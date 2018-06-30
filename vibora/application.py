from itertools import chain
from typing import Callable, Type, List, Optional
from .request import Request
from .blueprints import Blueprint
from .sessions import SessionEngine
from .router import Router, RouterStrategy, RouteLimits
from .protocol import Connection
from .responses import Response
from .components import ComponentsEngine
from .exceptions import ReverseNotFound, DuplicatedBlueprint
from .templates.engine import TemplateEngine
from .templates.extensions import ViboraNodes
from .static import StaticHandler
from .limits import ServerLimits


class Application(Blueprint):

    current_time: str = None

    def __init__(self, template_dirs: List[str] = None, router_strategy=RouterStrategy.CLONE,
                 sessions_engine: SessionEngine=None, server_name: str = None, url_scheme: str = 'http',
                 static: StaticHandler=None, log_handler: Callable=None, access_logs: bool=None,
                 server_limits: ServerLimits=None, route_limits: RouteLimits=None,
                 request_class: Type[Request]=Request):
        """

        :param template_dirs:
        :param router_strategy:
        :param sessions_engine:
        :param server_name:
        :param url_scheme:
        :param static:
        :param log_handler:
        :param server_limits:
        :param route_limits:
        """
        super().__init__(template_dirs=template_dirs, limits=route_limits)
        self.debug_mode = False
        self.test_mode = False
        self.server_name = server_name
        self.url_scheme = url_scheme
        self.handler = Connection
        self.router = Router(strategy=router_strategy)
        self.template_engine = TemplateEngine(extensions=[ViboraNodes(self)])
        self.static = static or StaticHandler([])
        self.connections = set()
        self.workers = []
        self.components = ComponentsEngine()
        self.loop = None
        self.access_logs = access_logs
        self.log_handler = log_handler
        self.initialized = False
        self.server_limits = server_limits or ServerLimits()
        self.running = False
        if not issubclass(request_class, Request):
            raise ValueError('class_obj must be a child of the Vibora Request class. '
                             '(from vibora.request import Request)')
        self.request_class = request_class
        self.session_engine = sessions_engine
        self._test_client = None

    def exists_hook(self, type_id: int) -> bool:
        """

        :param type_id:
        :return:
        """

        for blueprint in self.blueprints.keys():
            if bool(blueprint.hooks.get(type_id)):
                return True
            if bool(blueprint.async_hooks.get(type_id)):
                return True
        return bool(self.hooks.get(type_id) or self.async_hooks.get(type_id))

    async def call_hooks(self, type_id: int, components, route=None) -> Optional[Response]:
        """

        :param route:
        :param type_id:
        :param components:
        :return:
        """
        targets = (route.parent, self) if route and route.parent != self else (self, )
        for target in targets:
            for listener in target.hooks.get(type_id, ()):
                response = listener.call_handler(components)
                if response:
                    return response
            for listener in target.async_hooks.get(type_id, ()):
                response = await listener.call_handler(components)
                if response:
                    return response

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

        # Non-Local listeners are removed from the blueprint because they are actually global hooks.
        if blueprint != self:
            for collection, name in ((blueprint.hooks, 'hooks'), (blueprint.async_hooks, 'async_hooks')):
                local_listeners = {}
                for listener_type, listeners in collection.items():
                    for listener in listeners:
                        if not listener.local:
                            self.add_hook(listener)
                        else:
                            local_listeners.setdefault(listener.event_type, []).append(listener)
                setattr(blueprint, name, local_listeners)

    def clean_up(self):
        """

        :return:
        """
        for process in self.workers:
            process.terminate()
        self.running = False

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
