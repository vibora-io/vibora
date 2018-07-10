import base64
import hashlib
import re
import uuid
from collections import deque
from typing import get_type_hints
from inspect import iscoroutinefunction, isbuiltin, signature
from .parser import PatternParser
from ..limits import RouteLimits
from ..utils import clean_route_name, clean_methods
from ..exceptions import ReverseNotFound, NotFound, MethodNotAllowed, MissingComponent
from ..cache.cache import CacheEngine

############################################
# C IMPORTS
# noinspection PyUnresolvedReferences
from ..request.request cimport Request
# noinspection PyUnresolvedReferences
from ..cache.cache cimport CacheEngine
# noinspection PyUnresolvedReferences
from ..responses.responses cimport Response, RedirectResponse, WebsocketHandshakeResponse
# noinspection PyUnresolvedReferences
from ..components.components cimport ComponentsEngine
############################################


class RouterStrategy:
    STRICT = 1
    REDIRECT = 2
    CLONE = 3


cdef inline bytes clean_url(bytes url):
    cdef bytes char
    cdef int count = 0
    for char in url:
        if char == b'?' or char == b'#':
            return url[:count]
        count += 1
    return url


cdef class RouterCache:

    def __init__(self, max_size: int=256):
        self.values = {}
        self.queue = deque()
        self.max_size = max_size
        self.current_size = 0

    cdef set(self, tuple key, Route route):
        if self.current_size > self.max_size:
            key = self.queue.pop()
            del self.values[key]
        else:
            self.current_size += 1
        self.queue.appendleft(key)
        self.values[key] = route


cdef class Router:
    def __init__(self, strategy: int):
        self.strategy = strategy
        self.reverse_index = {}
        self.routes = {}
        self.dynamic_routes = {}
        self.default_handlers = {}
        self.cache = RouterCache(max_size=1024)
        self.hosts = {}
        self.check_host = False

    def _add_route_to_cache(self, route: 'Route'):
        """

        :param route:
        :return:
        """
        if not route.is_dynamic and not route.hosts:
            for method in route.methods:
                self.routes.setdefault(method, {})[route.pattern] = route
        elif route.hosts:
            self.check_host = True
            for host in route.hosts:
                host = re.compile(host)
                routes = self.hosts.setdefault(host, {})
                for method in route.methods:
                    routes.setdefault(method, []).append(route)
        elif route.is_dynamic:
            for method in route.methods:
                self.dynamic_routes.setdefault(method, []).append(route)
        self.reverse_index[route.name] = route

    def add_route(self, route: 'Route', prefixes: dict = None, check_slashes: bool = True):
        """

        :param route:
        :param prefixes:
        :param check_slashes:
        :return:
        """
        if prefixes is None:
            prefixes = {'': ''}

        for name_prefix, pattern_prefix in prefixes.items():
            clone = route.clone(pattern=pattern_prefix.encode() + route.pattern,
                                name=clean_route_name(name_prefix, route.name))
            self._add_route_to_cache(clone)

            # Handling slashes strategy.
            conditions = [
                not clone.is_dynamic,
                check_slashes is True,
                b'GET' in clone.methods
            ]

            if all(conditions):
                if self.strategy == RouterStrategy.CLONE:
                    pattern = clone.pattern[:-1] if clone.pattern.endswith(b'/') else clone.pattern + b'/'
                    self.add_route(clone.clone(pattern), check_slashes=False, prefixes={'': ''})

                elif self.strategy == RouterStrategy.REDIRECT:
                    async def redirect_handler():
                        return RedirectResponse(clone.pattern.decode(), status_code=301)
                    redirect_route = clone.clone(
                        handler=redirect_handler, methods=('GET', ),
                        dynamic=False,
                        pattern=clone.pattern[:-1] if clone.pattern.endswith(b'/') else clone.pattern + b'/'
                    )
                    self.add_route(redirect_route, check_slashes=False, prefixes={'': ''})

    def build_url(self, _name: str, *args, **kwargs):
        try:
            route = self.reverse_index[_name]
            return route.build_url(*args, **kwargs)
        except KeyError:
            raise ReverseNotFound('Failed to build url for {0}'.format(_name))

    cdef bint check_not_allowed_method(self, bytes url, bytes method) except -1:
        """

        :param url:
        :param method:
        :return:
        """

        allowed_methods = []

        for current_method in self.routes:
            # We can skip the actual method because we already checked it before.
            if current_method == method:
                continue
            if url in self.routes[current_method]:
                allowed_methods.append(allowed_methods)

        for current_method, routes in self.dynamic_routes.items():
            # We can skip the actual method because we already checked it before.
            if current_method == method:
                continue
            for route in routes:
                if route.regex.fullmatch(url):
                    allowed_methods.append(current_method)

        if allowed_methods:
            raise MethodNotAllowed(allowed_methods=allowed_methods)

    cdef Route _find_route_by_host(self, bytes url, bytes method, str host):
        """

        :param url:
        :param method:
        :param host:
        :return:
        """
        key = (url, method, host)
        route = self.cache.values.get(key)
        if route is not None:
            return route

        # Static routes for this given host are priority.
        for pattern, routes in self.hosts.items():
            if pattern.fullmatch(host):

                # Checking if there is a match.
                for route in routes.get(method, []):
                    if not route.is_dynamic and route.pattern == url:
                        self.cache.set(key, route)
                        return route
                    elif route.is_dynamic and route.regex.fullmatch(url):
                        self.cache.set(key, route)
                        return route

                # Checking the "not allowed" case.
                allowed_methods = []
                for method_name in self.hosts[host]:

                    # We do skip the correct method because we already checked it.
                    if method_name == method:
                        continue

                    for route in self.hosts[host][method_name]:
                        if not route.is_dynamic and route.pattern == url:
                            allowed_methods.append(method_name)
                        elif route.is_dynamic and route.regex.fullmatch(url):
                            allowed_methods.append(method_name)

                if allowed_methods:
                    raise MethodNotAllowed(allowed_methods=allowed_methods)

        return self._find_route(url, method)

    cdef Route _find_route(self, bytes url, bytes method):
        """

        :param url:
        :param method:
        :return:
        """
        url = clean_url(url)
        cdef tuple key = (url, method)
        try:
            return self.cache.values[key]
        except KeyError:
            pass

        try:
            route = self.routes[method][url]
            self.cache.set(key, route)
            return route
        except KeyError:
            pass

        try:
            for route in self.dynamic_routes[method]:
                if route.regex.fullmatch(url):
                    self.cache.set(key, route)
                    return route
        except KeyError:
            pass

        self.check_not_allowed_method(url, method)

        raise NotFound()

    cdef Route get_route(self, request: Request):
        try:
            if not self.check_host:
                return self._find_route(request.url, request.method)
            return self._find_route_by_host(request.url, request.method, request.headers.get('host'))
        except MethodNotAllowed as error:
            request.context['allowed_methods'] = error.allowed_methods
            return self.default_handlers[405]
        except NotFound:
            return self.default_handlers[404]

    def check_integrity(self):
        for http_code in [404, 405]:
            if self.default_handlers.get(http_code) is None:
                raise NotImplementedError(f'Please implement the default {http_code} route.')


cdef class Route:

    def __init__(self, pattern, handler, methods=None,
                 parent=None, app=None, dynamic=None, str name = None,
                 cache: CacheEngine = None, websocket=False, hosts=None, limits: RouteLimits=None):
        self.name = name or str(uuid.uuid4())
        self.handler = handler
        self.app = app
        self.parent = parent
        self.pattern = pattern
        self.components = self.extract_components(self.handler)
        self.receive_params = len(self.components)
        self.is_coroutine = iscoroutinefunction(handler)
        self.methods = clean_methods(methods)
        self.websocket = websocket
        self.regex, self.params_book, self.simplified_pattern = PatternParser.extract_params(pattern)
        self.hosts = hosts
        if dynamic is None:
            self.is_dynamic = PatternParser.is_dynamic_pattern(self.regex.pattern)
        else:
            self.is_dynamic = dynamic
        self.cache = cache
        self.limits = limits

    def extract_components(self, handler):
        if isbuiltin(handler):
            try:
                return native_signatures[handler]
            except KeyError:
                raise Exception('Native handler not registered in native signatures module.')
        else:
            hints = get_type_hints(handler)
            if not hints and len(signature(handler).parameters) > 0:
                raise Exception(f'Type hint your route ({self.name}) params so Vibora can optimize stuff.')
            return tuple(filter(lambda x: x[0] != 'return', hints.items()))

    cdef call_handler(self, Request request, ComponentsEngine components):
        cdef str name
        cdef dict function_params = {}
        if not self.receive_params:
            return self.handler()
        else:
            try:
                if self.params_book:
                    match = self.regex.match(request.url)
                    for name, type_ in self.components:
                        if name in self.params_book:
                            function_params[name] = PatternParser.CAST[type_](match.group(name))
                        else:
                            function_params[name] = components.get(type_)
                else:
                    for name, type_ in self.components:
                        function_params[name] = components.get(type_)
            except MissingComponent as error:
                    error.route = self
                    raise error
            return self.handler(**function_params)

    def build_url(self, **kwargs):
        if not self.is_dynamic:
            return self.pattern
        else:
            url = self.simplified_pattern
            for key, value in kwargs.items():
                url = url.replace('$' + key, str(value))
            return url

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all([
                other.pattern == self.pattern,
                other.handler == self.handler,
                other.methods == self.methods
            ])
        return False

    def __str__(self):
        return '<Route ("{0}", methods={1})>'.format(self.pattern, self.methods)

    def clone(self, pattern=None, name=None, handler=None, methods=None, dynamic=None):
        return Route(pattern=pattern or self.pattern, handler=handler or self.handler,
                     methods=methods or self.methods,
                     parent=self.parent, app=self.app, limits=self.limits, hosts=self.hosts,
                     dynamic=dynamic or self.is_dynamic, name=name or self.name, cache=self.cache)


class WebsocketRoute(Route):
    def __init__(self, *args, **kwargs):
        key = 'websocket_handler'
        if key in kwargs:
            self.websocket_handler = kwargs[key]
            del kwargs[key]
        else:
            raise SyntaxError(f'WebsocketRoute needs a "{key} " parameter.')
        super().__init__(*args, **kwargs)

    def clone(self, pattern=None, name=None):
        return WebsocketRoute(pattern=pattern or self.pattern, handler=self.handler, methods=self.methods,
                              parent=self.parent, app=self.app, cache=self.cache,
                              dynamic=self.is_dynamic, name=name or self.name, websocket_handler=self.websocket_handler)


def websocket_handshake_handler(request: Request = None):
    header_name = b'Sec-WebSocket-Key'
    key = request.headers.get(header_name.decode('utf-8'))
    if key:
        key += '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        key = base64.b64encode(hashlib.sha1(key.encode('utf-8')).digest())
        return WebsocketHandshakeResponse(key)
    else:
        return Response(b'', status_code=400)


native_signatures = {
    websocket_handshake_handler: (('request', Request),)
}
