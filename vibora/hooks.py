from inspect import iscoroutinefunction
from typing import get_type_hints


class Events:

    # After the fork but before the server is online receiving requests.
    BEFORE_SERVER_START = 1

    # After server fork and server online. Understand that you could
    # theoretically be in the middle of a request while this function is running.
    # If you need to ensure something runs before the first request arrives "BEFORE_SERVER_START" is what you need.
    AFTER_SERVER_START = 2

    # Before each endpoint, you can halt requests, authorize users and many other common tasks
    # that are shared with many routes.
    BEFORE_ENDPOINT = 3

    # After each endpoint is called, this is useful when you need to globally inject data into responses
    # like headers.
    AFTER_ENDPOINT = 4

    # Called after each response is sent to the client, useful to cleaning and non-critical logging operations.
    AFTER_RESPONSE_SENT = 5

    # Called right before the server is stopped, you have the chance to cancel a stop request,
    # notify your clients and other useful stuff using this hook.
    BEFORE_SERVER_STOP = 6

    # Useful for debugging purposes.
    ALL = (
        BEFORE_SERVER_START,
        AFTER_SERVER_START,
        BEFORE_ENDPOINT,
        AFTER_ENDPOINT,
        AFTER_RESPONSE_SENT,
        BEFORE_SERVER_STOP,
    )


class Hook:

    __slots__ = ("event_type", "handler", "local", "is_async", "wanted_components")

    def __init__(self, event: int, handler, local=False):
        self.event_type = event
        self.handler = handler
        self.local = local
        self.is_async = iscoroutinefunction(handler)
        self.wanted_components = get_type_hints(self.handler)

    def call_handler(self, components):
        params = {}
        for name, required_type in self.wanted_components.items():
            params[name] = components.get(required_type)
        return self.handler(**params)
