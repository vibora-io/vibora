import asyncio
from functools import partial
from typing import Any, Coroutine
from vibora.parsers.response import HttpResponseParser
from vibora.websockets import FrameParser
from .request import WebsocketRequest


# https://websocket.org/echo.html


class WebsocketProtocol(asyncio.Protocol):

    def __init__(self, transport, loop):
        self.loop = loop
        self.transport = transport
        self.parser = FrameParser(self)

    async def write(self, data):
        self.transport.write(data)

    def data_received(self, data):
        self.loop.create_task(self.parser.feed(data))
        print(f'WebsData received: {data}')

    async def on_message(self, data):
        print(f'Data {data}')


class WebsocketHandshake(asyncio.Protocol):

    def __init__(self, client, loop):
        self.client = client
        self.loop = loop
        self.transport: asyncio.Transport = None
        self.parser = HttpResponseParser(self)
        self.current_status = None
        self.current_headers = None

    def connection_made(self, transport):
        """

        :param transport:
        :return:
        """
        wr = WebsocketRequest(self.client.host, path=self.client.path, origin=self.client.origin)
        transport.write(wr.encode())
        self.transport = transport
        print('connected')

    def data_received(self, data):
        self.parser.feed(data)
        print(f'Data received: {data}')

    def connection_lost(self, exc):
        print('The server closed the connection')
        print('Stop the event loop')

    # Parser Callbacks
    def on_body(self): pass

    def on_headers_complete(self, headers, status_code):
        self.current_status = status_code
        self.current_headers = headers

    def on_message_complete(self):
        self.transport.set_protocol(WebsocketProtocol(self.transport, self.loop))


class WebsocketClient:

    def __init__(self, host: str, port: int, path: str = '/', loop=None, origin: str = None):
        self.host = host
        self.port = port
        self.path = path
        self.connected = False
        self.origin = origin
        self.loop = loop or asyncio.get_event_loop()
        self.buffer = bytearray()

    async def connect(self):
        factory = partial(WebsocketHandshake, self, self.loop)
        await self.loop.create_connection(factory, host=self.host, port=self.port, ssl=True)

    async def send(self, msg):
        if not self.connected:
            await self.connect()
        pass

    async def receive(self, max_size: int = 1 * 1024 * 1024, stream: bool = False):
        pass
