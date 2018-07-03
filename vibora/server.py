import logging
import sys
import traceback
from email.utils import formatdate
from collections import OrderedDict, deque
from functools import partial
from multiprocessing import cpu_count
from .__version__ import __version__
from .client import Session
from .workers.handler import RequestHandler
from .workers.necromancer import Necromancer
from .router import Route
from .request import Request
from .responses import Response
from .sessions import SessionEngine
from .templates.loader import TemplateLoader
from .templates.extensions import ViboraNodes
from .exceptions import NotFound, MethodNotAllowed, MissingComponent
from .parsers.errors import BodyLimitError, HeadersLimitError
from .utils import wait_server_available, get_free_port, cprint, pause, format_access_log
from .hooks import Hook, Events
from .application import Application


class Vibora(Application):

    current_time: str = formatdate(timeval=None, localtime=False, usegmt=True)

    def _add_default_routes(self):
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
            if app.debug_mode is True:
                # A hack to help users with component missing exceptions because they are generated
                # too deep in Cython and there aren't useful stack frames.
                try:
                    msg = f"{error.route.handler if error.route else 'A hook'} needs " \
                          f"{error.component} but there isn't any " \
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
                if app.debug_mode and not app.test_mode:
                    traceback.print_exception(MissingComponent, error, error.__traceback__)
                return Response(b'Internal Server Error', status_code=500, headers={'Content-Type': 'text/html'})

    def _configure_static_files(self):
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
        self.router.check_integrity()

    def _turn_on_debug_features(self):
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

        if not self.test_mode:
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
        if self.debug_mode:
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
            loader = TemplateLoader(dirs, self.template_engine)
            loader.load()
        self.template_engine.compile_templates()

    def _add_default_error_handlers(self):
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
                self.test_mode = True
            self.run(host=address, port=port, block=False, necromancer=False, workers=1, debug=True,
                     startup_message=False)
            self._test_client = Session(prefix='http://' + address + ':' + str(port), headers=headers,
                                        follow_redirects=follow_redirects, max_redirects=max_redirects, stream=stream,
                                        decode=decode, keep_alive=False)
        return self._test_client

    def _configure_sessions(self) -> None:
        """
        Register the flush_session hook to enable the session engine to work correctly.
        :return: None
        """
        # You cannot check for the session_engine presence right now
        # because the user may set it using the before_server_start hook to be able to make async calls.
        @self.handle(Events.BEFORE_SERVER_START)
        async def register_session_hook(app: Vibora):

            # In case the user didn't configured a session engine we skip the hook for performance.
            if app.session_engine:

                app.components.add(app.session_engine)

                @app.handle(Events.AFTER_ENDPOINT)
                async def flush_session(request: Request, response: Response, sessions: SessionEngine):
                    pending_session = request.session_pending_flush()
                    if pending_session:
                        await sessions.save(pending_session, response)

    def _configure_logging(self):
        """

        :return:
        """
        if (self.access_logs is None and self.debug_mode) or self.access_logs is True:

            @self.handle(Events.BEFORE_SERVER_START)
            async def register_session_hook(app: Vibora):

                @app.handle(Events.AFTER_ENDPOINT)
                async def access_logs(request: Request, response: Response):
                    print(format_access_log(request, response), file=sys.stderr)

    def initialize(self):
        """

        :return:
        """
        self.components.add(self)
        self.add_blueprint(self, prefixes={'': ''})
        if self.debug_mode:
            self._turn_on_debug_features()
        self._add_default_routes()
        self._add_default_error_handlers()
        self._configure_static_files()
        self._configure_sessions()
        self.check_integrity()
        self.load_templates()
        self.initialized = True

    def run(self, host: str='127.0.0.1', port: int=5000, workers: int=None, debug: bool=True,
            block: bool=True, necromancer: bool=False, sock=None, startup_message: bool=True):
        """

        :param startup_message:
        :param host:
        :param port:
        :param workers:
        :param debug:
        :param block:
        :param necromancer:
        :param sock:
        :return:
        """
        self.debug_mode = debug

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

        # Wait the server start accepting new connections.
        if not sock:
            wait_server_available(host, port)

        if startup_message:
            cprint('# Vibora ({color_}' + __version__ + '{end_}) # http://' + str(host) + ':' + str(port),
                   custom=True)

        self.running = True
        if block:
            try:
                pause()
                self.running = False
            except KeyboardInterrupt:
                self.clean_up()
