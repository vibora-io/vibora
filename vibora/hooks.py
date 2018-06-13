from inspect import iscoroutinefunction
from typing import get_type_hints


class Events:

    # After the fork but before the server is online receiving requests.
    BEFORE_SERVER_START = 1

    # After server fork and server online. Understand this is not deterministic, you could
    # theoretically be in the middle of a request while this function is running.
    AFTER_SERVER_START = 2

    # Before each endpoint, this is hook is very useful so you can halt requests,
    # authenticate stuff and many other common tasks in APIs.
    BEFORE_ENDPOINT = 3

    # After each endpoint is called, this is useful when you need to globally inject data into responses like headers.
    AFTER_ENDPOINT = 4

    # Called after each response is sent to the client, useful to cleaning and non-critical logging operations.
    AFTER_RESPONSE_SENT = 5

    # Called right before the server is stopped, you may have the chance to halt a stop request,
    # notify your clients and other useful stuff using this hook.
    BEFORE_SERVER_STOP = 6

    # Useful for debugging purposes.
    ALL = (BEFORE_SERVER_START, AFTER_SERVER_START, BEFORE_ENDPOINT, AFTER_ENDPOINT, AFTER_RESPONSE_SENT,
           BEFORE_SERVER_STOP)


class Hook:
    def __init__(self, event: int, handler, local=False):
        self.event_type = event
        self.handler = handler
        self.local = local
        self.async = iscoroutinefunction(handler)
        self.wanted_components = get_type_hints(self.handler)

    def call_handler(self, components):
        params = {}
        for name, required_type in self.wanted_components.items():
            params[name] = components.get(required_type)
        return self.handler(**params)
