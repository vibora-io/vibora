import os
from tempfile import gettempdir
from typing import Callable, Type
from collections import defaultdict
from inspect import stack
from .request import Request
from .blueprints import Blueprint
from .router import Router, Route, RouterStrategy, RouteLimits
from .protocol import Connection
from .components import ComponentsEngine
from .exceptions import ReverseNotFound, DuplicatedBlueprint
from .templates.engine import TemplateEngine
from .templates.extensions import ViboraNodes
from .static import StaticHandler
from .limits import ServerLimits


class Application(Blueprint):

    current_time = None

    def __init__(self, template_dirs: list = None, router_strategy=RouterStrategy.CLONE, sessions=None,
                 server_name: str = None, url_scheme: str = 'http', static=None,
                 log: Callable = None, server_limits: ServerLimits=None, route_limits: RouteLimits=None,
                 temporary_dir: str=None):
        """

        :param template_dirs:
        :param router_strategy:
        :param sessions:
        :param server_name:
        :param url_scheme:
        :param static:
        :param log:
        :param server_limits:
        :param route_limits:
        :param temporary_dir:
        """
        super().__init__(template_dirs=template_dirs or self._get_template_dirs_based_on_stack(),
                         limits=route_limits)
        self.debug = False
        self.testing = False
        self.server_name = server_name
        self.url_scheme = url_scheme
        self.handler = Connection
        self.router = Router(strategy=router_strategy)
        self.template_engine = TemplateEngine(extensions=[ViboraNodes(self)])
        self.static = static or StaticHandler(self._get_static_dirs_based_on_stack())
        self.connections = set()
        self.logger = None
        self.workers = []
        # self.session_engine = sessions or FilesSessionEngine()
        self.session_engine = sessions
        self.components = ComponentsEngine()
        self.loop = None
        self.log = log
        self.initialized = False
        self.request_class = Request
        self.server_limits = server_limits or ServerLimits()
        self.temporary_dir = temporary_dir or gettempdir()
        self.running = False
        self._test_client = None

    def override_request(self, class_obj: Type):
        """

        :param class_obj:
        :return:
        """
        if not issubclass(class_obj, Request):
            raise ValueError('You must subclass the Request class to override it.')
        self.request_class = class_obj

    def exists_hook(self, type_id: int) -> bool:
        """

        :param type_id:
        :return:
        """
        return bool(self.hooks.get(type_id) or self.async_hooks.get(type_id))

    async def call_hooks(self, type_id: int, components):
        """

        :param type_id:
        :param components:
        :return:
        """
        for listener in self.hooks[type_id]:
            response = listener.call_handler(components)
            if response:
                return response
        for listener in self.async_hooks[type_id]:
            response = await listener.call_handler(components)
            if response:
                return response

    @staticmethod
    def _get_template_dirs_based_on_stack():
        chosen_stack = None
        template_dirs = []
        for s in reversed(stack()):
            if s.code_context:
                for context in s.code_context:
                    if 'vibora' in context.lower():
                        chosen_stack = s
        if chosen_stack:
            parent_dir = os.path.dirname(chosen_stack.filename)
            for root, dirs, files in os.walk(parent_dir):
                for directory_name in dirs:
                    if directory_name == 'templates':
                        template_dirs.append(os.path.join(root, directory_name))
        return template_dirs

    @staticmethod
    def _get_static_dirs_based_on_stack():
        chosen_stack = None
        template_dirs = []
        for s in reversed(stack()):
            if s.code_context:
                for context in s.code_context:
                    if 'vibora' in context.lower():
                        chosen_stack = s
        if chosen_stack:
            parent_dir = os.path.dirname(chosen_stack.filename)
            for root, dirs, files in os.walk(parent_dir):
                for directory_name in dirs:
                    if directory_name == 'static':
                        template_dirs.append(os.path.join(root, directory_name))
        return template_dirs

    def __register_blueprint_routes(self, blueprint: Blueprint, prefixes: dict = None):
        """

        :param blueprint:
        :param prefixes:
        :return:
        """
        for name, pattern in prefixes.items():
            for nested_blueprint, nested_prefixes in blueprint.blueprints.items():
                for nested_name, nested_pattern in nested_prefixes.items():
                    if name and nested_name:
                        merged_prefixes = {name + ':' + nested_name: pattern + nested_pattern}
                    else:
                        merged_prefixes = {name or nested_name: pattern + nested_pattern}
                    self.__register_blueprint_routes(nested_blueprint, prefixes=merged_prefixes)
        blueprint.app = self
        for route in blueprint.routes:
            route.app = self.app
            route.limits = route.limits or self.limits
            self.router.add_route(route, prefixes=prefixes)

    def add_blueprint(self, blueprint, prefixes: dict = None):
        """

        :param blueprint:
        :param prefixes:
        :return:
        """
        if blueprint.parent:
            raise DuplicatedBlueprint('You cannot add blueprint twice. Use more prefixes or a different hierarchy.')

        if blueprint != self:
            blueprint.parent = self

        if prefixes is None:
            prefixes = {'': ''}

        self.__register_blueprint_routes(blueprint, prefixes)

        self.blueprints[blueprint] = prefixes

        # Non-Local listeners are removed from the blueprint.
        if blueprint != self:
            local_listeners = defaultdict(list)
            for listener_type, listeners in blueprint.hooks.items():
                for listener in listeners:
                    if not listener.local:
                        self.add_hook(listener)
                    else:
                        local_listeners[listener_type].append(listener)

            blueprint.hooks = local_listeners

    def clean_up(self):
        # self.session_engine.clean_up()
        for process in self.workers:
            process.terminate()
        self.running = False

    async def handle_exception(self, connection, exception, components, route: Route = None):
        """

        :param components:
        :param connection:
        :param exception:
        :param route:
        :return:
        """
        response = None
        if route:
            response = await route.parent.process_exception(exception, components)
        if response is None:
            response = await self.process_exception(exception, components)
        response.send(connection)

    def url_for(self, _name: str, _external=False, *args, **kwargs) -> str:
        """

        :param _name:
        :param _external:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.initialized:
            raise ValueError('Routes are not registered yet. Please run Vibora or call app.initialize().')
        route = self.router.reverse_index.get(_name)
        if not route:
            raise ReverseNotFound(_name)
        root = ''
        if _external:
            if not self.server_name or not self.url_scheme:
                raise Exception('Please configure the server_name and url_scheme to use external urls.')
            root = self.url_scheme + '://' + self.server_name
        return root + route.build_url(*args, **kwargs).decode()

    def __del__(self):
        self.clean_up()
