from asyncio.transports import Transport


class ConnectionStatus:
    PENDING = 1
    PROCESSING_REQUEST = 2
    WEBSOCKET = 3


class Connection:
    def __init__(self, app, loop):
        pass

    def connection_made(self, transport: Transport):
        pass

    def data_received(self, data):
        pass

    def write_response(self, response):
        pass

    async def call_async_hooks(self, type_id: int, **kwargs) -> bool:
        pass

    async def process_async_request(self, route, request, stream):
        pass

    def connection_lost(self, exc):
        pass

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # HTTP PARSER CALLBACKS

    def on_headers_complete(self, headers: dict, url: bytes, method: bytes):
        pass

    def on_body(self, body):
        pass

    def on_message_complete(self):
        pass


def update_current_time() -> None:
    pass
