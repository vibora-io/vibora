from inspect import isclass, iscoroutinefunction
from .cache import Static
from .optimizer import is_static
from .exceptions import ExceptionHandler, DuplicatedBlueprint, ConflictingPrefixes
from .router import Route, WebsocketRoute, websocket_handshake_handler
from .hooks import Hook, Events
from .responses import Response, StreamingResponse
from .limits import RouteLimits


class Blueprint:
    def __init__(self, template_dirs=None, hosts: list=None, limits: RouteLimits=None):
        self.default_routes = {}
        self.routes = []
        self.hooks = {}
        self.async_hooks = {}
        self.exception_handlers = {}
        self.template_dirs = template_dirs or []
        self.blueprints = {}
        self.hosts = hosts
        self.limits = limits or RouteLimits()

        # Initializing cached events.
        for key in Events.ALL:
            self.hooks[key] = []
            self.async_hooks[key] = []

        # Runtime Hacks.
        self.app = None
        self.parent = None

    def handle(self, value, local: bool = True):
        """
        Decorator to register a hook.
        :return: None
        """
        if value in (Events.BEFORE_SERVER_START, Events.AFTER_SERVER_START, Events.BEFORE_SERVER_STOP):
            local = False

        def wrapper(*args):
            handler = args[0]
            values = value if isinstance(value, (list, tuple)) else [value]
            for v in values:
                if v in Events.ALL:
                    self.add_hook(Hook(v, args[0], local=local))
                elif isinstance(v, Exception) or (isclass(v) and issubclass(v, Exception)):
                    self.exception_handlers[v] = ExceptionHandler(handler, v, local=local)
                else:
                    raise SyntaxError('{0} is not allowed at @handle.'.format(v))
        return wrapper

    def route(self, pattern, methods=None, cache=None, name=None, hosts: list=None, limits: RouteLimits=None):
        def register(handler):
            # Checking if handler is co-routine.
            if not iscoroutinefunction(handler):
                raise SyntaxError(f'Your route handler must be an async function. (Handler: {handler})')

            # If the route it's simple enough let the static cache kicks in.
            chosen_cache = cache
            if cache is None and is_static(handler):
                chosen_cache = Static()
            if cache is False:
                chosen_cache = None

            # Get the function name in case the user doesn't provide one.
            # Route names are used to create URLs (I.e: links inside templates)
            route_name = handler.__name__ if name is None else name

            # Patterns should be bytes.
            if isinstance(pattern, str):
                encoded_pattern = pattern.encode()
            else:
                encoded_pattern = pattern

            new_route = Route(encoded_pattern, handler, tuple(methods or (b'GET',)),
                              parent=self, name=route_name, cache=chosen_cache,
                              hosts=hosts or self.hosts, limits=limits or self.limits)
            self.add_route(new_route)
            return handler

        return register

    def websocket(self, pattern: str, name: str = None):
        def register(handler):
            # Get the function name in case the user doesn't provide one.
            # Route names are used to create URLs (I.e: links inside templates)
            route_name = handler.__name__ if name is None else name

            new_route = WebsocketRoute(pattern, websocket_handshake_handler, ['GET'],
                                       parent=self, name=route_name, websocket=True, websocket_handler=handler)
            self.routes.append(new_route)
            return handler

        return register

    async def process_exception(self, exception, components) -> Response:
        """

        :param components:
        :param exception:
        :return:
        """
        # Trying specific hooks first.
        exception_handler = self.exception_handlers.get(exception.__class__)
        if exception_handler:
            response = await exception_handler.call(components)
            if response:
                return response

        # Then we can start calling the more generic ones.
        for exception_type, exception_handler in self.exception_handlers.items():

            # This is a corner case where there is a specific handler but he doesn't return a response.
            if exception_type == exception.__class__:
                continue

            if isinstance(exception, exception_type) and exception != exception_type:
                response = await exception_handler.call(components)
                if response:
                    return response

        # Delegating this problem to our parent.
        if self.parent:
            return await self.parent.process_exception(exception, components)

    async def render(self, template_name: str, **template_vars):
        """

        :param template_name:
        :param template_vars:
        :return:
        """
        content = await self.app.template_engine.render(template_name, **template_vars)
        return Response(content.encode())

    async def render_streaming(self, template_name: str, **template_vars):
        """

        :param template_name:
        :param template_vars:
        :return:
        """
        content = await self.app.template_engine.render(template_name, streaming=True, **template_vars)
        return StreamingResponse(content)

    def add_blueprint(self, blueprint, prefixes: dict=None):
        """
        Add a nested blueprint.
        :param blueprint: Blueprint instance.
        :param prefixes: prefixes to prepend on route patterns. (I.e: {"/v1/": "v1"})
        :return: None
        """
        if not prefixes:
            prefixes = {'': ''}

        if blueprint.parent:
            raise DuplicatedBlueprint('You cannot add a blueprint twice. Use more prefixes or different hierarchy.')

        for key in prefixes.keys():
            for existent_prefix in self.blueprints.values():
                if key == existent_prefix:
                    raise ConflictingPrefixes(
                        f'Prefix "{key}" conflicts with an already existing prefix: {existent_prefix}')

        blueprint.parent = self
        self.blueprints[blueprint] = prefixes

    def add_hook(self, hook: Hook):
        """

        :param hook:
        :return:
        """
        collection = self.async_hooks if hook.is_async else self.hooks
        collection[hook.event_type].append(hook)

    def add_route(self, route: Route):
        """

        :param route:
        :return:
        """
        self.routes.append(route)

    def url_for(self, _name: str, _external=False, *args, **kwargs) -> str:
        """

        :param _external:
        :param _name:
        :param args:
        :param kwargs:
        :return:
        """
        return self.app.url_for(_name, _external=_external, *args, **kwargs)
