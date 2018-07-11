from inspect import signature
from typing import Callable, get_type_hints


class ViboraException(Exception):
    pass


class RouteConfigurationError(ViboraException):
    pass


class MissingComponent(Exception):
    def __init__(self, msg, component=None, route=None):
        self.component = component
        self.route = route
        super().__init__(msg)


class TemplateNotFound(ViboraException):
    pass


class ReverseNotFound(ViboraException):
    def __init__(self, route_name):
        super().__init__("{0}\nCheck your function names.".format(route_name))


class InvalidJSON(ViboraException):
    pass


class DuplicatedBlueprint(ViboraException):
    pass


class ConflictingPrefixes(ViboraException):
    pass


class ExceptionHandler:
    def __init__(self, handler: Callable, exception, local: bool = True):
        self.handler = handler
        self.exception = exception
        self.local = local
        self.params = self.extract_params()

    def call(self, components):
        params = {}
        for key, class_type in self.params:
            params[key] = components.get(class_type)
        return self.handler(**params)

    def extract_params(self):
        hints = get_type_hints(self.handler)
        if not hints and len(signature(self.handler).parameters) > 0:
            raise Exception(
                f"Type hint your handler ({self.handler}) params so Vibora can optimize stuff."
            )
        return tuple(filter(lambda x: x[0] != "return", hints.items()))


class NotFound(ViboraException):
    pass


class StaticNotFound(ViboraException):
    pass


class MethodNotAllowed(ViboraException):
    def __init__(self, allowed_methods: list):
        self.allowed_methods = allowed_methods
        super().__init__()


class StreamAlreadyConsumed(ViboraException):
    def __init__(self):
        super().__init__("Stream already consumed")
