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
        """
        :param data:
        :return:
        """
        pass

    def write_response(self, response):
        """
        :param response:
        :return:
        """
        pass

    async def call_async_hooks(self, type_id: int, **kwargs) -> bool:
        """
        :param type_id:
        :param kwargs:
        :return:
        """
        pass

    async def process_async_request(self, route, request, stream):
        pass

    def connection_lost(self, exc):
        """
        :param exc:
        :return:
        """
        pass

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # HTTP PARSER CALLBACKS

    def on_headers_complete(self, headers: dict, url: bytes, method: bytes):
        """
        :param headers:
        :param url:
        :param method:
        :return:
        """
        pass

    def on_body(self, body):
        """

        :param body:
        :return:
        """
        pass

    def on_message_complete(self):
        """
        :return:
        """
        pass


def update_current_time() -> None:
    pass
