import logging
import sys
import traceback
from email.utils import formatdate
from signal import pause
from collections import OrderedDict, deque
from functools import partial
from multiprocessing import cpu_count
from vibora.__version__ import __version__
from .client import Session
from .workers.handler import RequestHandler
from .workers.necromancer import Necromancer
from .router import Route
from .request import Request
from .responses import Response
from .templates.loader import TemplateLoader
from .templates.compilers.cython import CythonTemplateCompiler
from .templates.engine import TemplateEngine
from .templates.cache import DiskCache, InMemoryCache
from .templates.extensions import ViboraNodes
from .exceptions import NotFound, MethodNotAllowed, MissingComponent
from .parsers.errors import BodyLimitError, HeadersLimitError
from .utils import wait_server_available, get_free_port, cprint
from .hooks import Hook, Events
from .application import Application


class Vibora(Application):

    current_time: str = formatdate(timeval=None, localtime=False, usegmt=True)

    def add_default_routes(self):
        """

        :return:
        """

        # 404 Not Found.
        async def not_found_handler():
            raise NotFound()

        route_404 = Route(b'', not_found_handler, parent=self, limits=self.limits)
        self.router.default_handlers[404] = route_404

        # 405 Method Not Allowed.
        async def method_not_allowed_handler(request: Request):
            raise MethodNotAllowed(request.context['allowed_methods'])

        route_405 = Route(b'', method_not_allowed_handler, parent=self, limits=self.limits)
        self.router.default_handlers[405] = route_405

        @self.handle(MissingComponent)
        async def handle_missing_component(app: Vibora, error: MissingComponent):
            if app.debug is True:
                # A hack to help users with component missing exceptions because they are generated
                # too deep in Cython and there aren't useful stack frames.
                try:
                    msg = f"{error.route.handler} needs {error.component} but there isn't any " \
                          f"component registered with this type."
                    raise MissingComponent(msg)
                except Exception as e:
                    traceback.print_exception(MissingComponent, e, e.__traceback__)
            return Response(b'Internal Server Error', status_code=500, headers={'Content-Type': 'text/html'})

        if BodyLimitError not in self.exception_handlers:
            @self.handle(BodyLimitError)
            async def handle_body_limit():
                return Response(b'HTTP request body is too big.', status_code=413)

        if HeadersLimitError not in self.exception_handlers:
            @self.handle(HeadersLimitError)
            async def handle_headers_limit():
                return Response(b'HTTP request headers are too big. '
                                b'Maybe there are too many, maybe just few big ones.', status_code=400)

        if Exception not in self.exception_handlers:
            @self.handle(Exception)
            async def handle_internal_error(app: Vibora, error: Exception):
                if app.debug and not app.testing:
                    traceback.print_exception(MissingComponent, error, error.__traceback__)
                return Response(b'Internal Server Error', status_code=500, headers={'Content-Type': 'text/html'})

    def configure_static_files(self):
        """

        :return:
        """
        if self.static:
            static_route = Route((self.static.url_prefix + '/.*').encode(), self.static.handle,
                                 methods=(b'GET', b'HEAD'), parent=self, limits=self.limits)
            self.router.add_route(static_route, {'': ''}, check_slashes=False)

    def check_integrity(self):
        """

        :return:
        """
        if self.session_engine and self.session_engine.is_async:
            for routes in self.router.routes.values():
                for route in routes:
                    if not route.is_coroutine:
                        raise Exception('You cannot use an asynchronous session handler with synchronous views.')
        self.router.check_integrity()

    def turn_on_debug_features(self):
        """

        :return:
        """
        self.static.max_cache_size = 0

        def default_log(msg, level: int = None):
            """

            :param msg:
            :param level:
            :return:
            """
            if level in (logging.INFO, logging.CRITICAL, logging.ERROR, logging.WARNING):
                print(f'[{self.current_time}] - {msg}', file=sys.stderr)

        if not self.testing:
            self.log = default_log

    def load_templates(self):
        """

        :return:
        """
        self.template_engine.extensions.append(ViboraNodes(app=self))
        dirs = list()
        for blueprint in self.blueprints:
            for path in blueprint.template_dirs:
                dirs.append(path)
        if self.debug:
            def start_template_loader(app: Vibora):
                tl = TemplateLoader(dirs, app.template_engine)
                tl.start()

                def stop_loader():
                    tl.has_to_run = False

                stop_hook = Hook(Events.BEFORE_SERVER_STOP, stop_loader)
                self.add_hook(stop_hook)

            new_hook = Hook(Events.AFTER_SERVER_START, start_template_loader)
            self.add_hook(new_hook)
        else:
            tl = TemplateLoader(dirs, self.template_engine)
            tl.load()
        self.template_engine.compile_templates()

    def add_default_error_handlers(self):
        """

        :return:
        """

        if Exception not in self.exception_handlers:
            @self.handle(Exception)
            async def internal_server_error():
                return Response(b'Internal Server Error', status_code=500)

        if NotFound not in self.exception_handlers:
            @self.handle(NotFound)
            async def internal_server_error():
                return Response(b'404 Not Found', status_code=404)

        if MethodNotAllowed not in self.exception_handlers:
            @self.handle(MethodNotAllowed)
            async def internal_server_error(request: Request):
                return Response(b'Method Not Allowed', status_code=405,
                                headers={'Allow': request.context['allowed_methods']})

        self.sort_error_handlers()

    def sort_error_handlers(self):
        """

        :return:
        """
        cache = []
        keys = deque(self.exception_handlers.keys())
        while keys:
            current_key = keys.pop()
            found = False
            for key in keys:
                if issubclass(current_key, key):
                    found = True
            if not found:
                cache.append(current_key)
            else:
                keys.appendleft(current_key)
        self.exception_handlers = OrderedDict([(x, self.exception_handlers[x]) for x in reversed(cache)])

    def test_client(self, headers: dict = None, follow_redirects: bool = True, max_redirects: int = 30,
                    stream: bool = False, decode: bool = True) -> Session:
        """

        :param headers:
        :param follow_redirects:
        :param max_redirects:
        :param stream:
        :param decode:
        :return:
        """
        if not self.running:
            sock, address, port = get_free_port()
            sock.close()
            if not self.initialized:
                self.testing = True
            self.run(host=address, port=port, block=False, verbose=False, necromancer=False, workers=1, debug=True)
            self._test_client = Session(prefix='http://' + address + ':' + str(port), headers=headers,
                                        follow_redirects=follow_redirects, max_redirects=max_redirects, stream=stream,
                                        decode=decode, keep_alive=False)
        return self._test_client

    def initialize(self, debug: bool=False):
        """

        :return:
        """
        self.debug = debug
        self.components.add(self)
        self.add_blueprint(self, prefixes={'': ''})
        if self.debug:
            self.turn_on_debug_features()
        self.add_default_routes()
        self.add_default_error_handlers()
        self.configure_static_files()
        self.check_integrity()
        self.initialized = True
        self.load_templates()

    def run(self, host='127.0.0.1', port=5000, workers=None, debug=True, block=True, verbose=True,
            necromancer: bool = False, sock=None):
        """

        :param host:
        :param port:
        :param workers:
        :param debug:
        :param block:
        :param verbose:
        :param necromancer:
        :param sock:
        :return:
        """
        if not self.initialized:
            self.initialize(debug)

        # Starting workers.
        spawn_function = partial(RequestHandler, self, host, port, sock)
        for _ in range(0, (workers or cpu_count() + 2)):
            worker = spawn_function()
            worker.start()
            self.workers.append(worker)

        # Watch out for dead workers and bring new ones to life as needed.
        if necromancer:
            necromancer = Necromancer(self.workers, spawn_function=spawn_function,
                                      interval=self.server_limits.worker_timeout)
            necromancer.start()

        wait_server_available(host, port)

        if verbose:
            cprint('# Vibora ({color_}' + __version__ + '{end_}) # http://' + str(host) + ':' + str(port),
                   mixed=True)

        self.running = True
        if block:
            try:
                pause()
                self.running = False
            except KeyboardInterrupt:
                self.clean_up()
