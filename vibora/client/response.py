import asyncio
import time
from asyncio import wait_for
from vibora.parsers.response import HttpResponseParser
from enum import Enum
from .connection import Connection
from .exceptions import StreamAlreadyConsumed
from .request import Request
from .decoders import GzipDecoder
from ..cookies import CookiesJar, Cookie
from ..utils import json


class ResponseStatus(Enum):
    PENDING_HEADERS = 1
    PENDING_BODY = 2
    CHUNKED_TRANSFER = 3
    DECODING = 4
    COMPLETE = 5
    ERROR = 6


class Response:

    __slots__ = ('_connection', '_headers', '_content', '_parser', '_parser_status', '_cookies',
                 '_status_code', '_decode', '_chunk_size', '_decoder', '_encoding',
                 'request', 'url')

    def __init__(self, url: str, connection: Connection,
                 request: Request, chunk_size: int= 1 * 1024 * 1024, decode: bool=True):
        self._connection = connection
        self._headers = {}
        self._content = bytearray()
        # noinspection PyArgumentList
        self._parser = HttpResponseParser(self)
        self._parser_status = ResponseStatus.PENDING_HEADERS
        self._cookies = None
        self._status_code = None
        self._chunk_size = chunk_size
        self._decode = decode
        self._decoder = None
        self._encoding = None
        self.request = request
        self.url = url

    @property
    def encoding(self):
        return 'utf-8'

    def json(self, *args, loads=None, **kwargs):
        if not loads:
            loads = json.loads
        return loads(self.content.decode(self.encoding), *args, **kwargs)

    def text(self, encoding: str=None) -> str:
        return self.content.decode(encoding=encoding or self.encoding)

    @property
    def status_code(self):
        """

        :return:
        """
        if self._parser_status == ResponseStatus.PENDING_HEADERS:
            raise Exception('Status code not loaded yet. '
                            'In streaming mode you should manually call load_headers().')
        return self._status_code

    @property
    def headers(self):
        """

        :return:
        """
        if self._parser_status == ResponseStatus.PENDING_HEADERS:
            raise Exception('Headers not loaded yet. '
                            'In streaming mode you should manually call load_headers().')
        return self._headers

    @property
    def content(self):
        """

        :return:
        """
        if self._parser_status == ResponseStatus.PENDING_BODY:
            raise Exception('You need to call read_content() '
                            'before using this in streaming mode.')
        return self._content

    @property
    async def cookies(self):
        """

        :return:
        """
        if self._parser_status == ResponseStatus.PENDING_HEADERS:
            await self.receive_headers()
        if self._cookies is None:
            self._cookies = CookiesJar()
            if self._headers.get('set-cookie'):
                self._cookies.add_cookie(Cookie.from_header(self._headers['set-cookie']))
        return self._cookies

    async def read_content(self):
        """

        :return:
        """
        await self.receive_headers()
        if self._parser_status != ResponseStatus.PENDING_BODY:
            return
        try:
            length = int(self._headers['Content-Length'])
            if not self._decoder:
                # Skipping the HTTP parser for performance.
                self._content.extend(await self._connection.read_exactly(length))
                self.on_message_complete()
            else:
                self._parser.feed(await self._connection.read_exactly(length))
        except KeyError:
            if self._headers.get('Transfer-Encoding') == 'chunked':
                await self._handle_chunked_encoding()
            else:
                raise Exception('Invalid response.')
            return self._content
        except ValueError:
            raise Exception('Invalid content-length header.')

    async def _handle_chunked_encoding(self):
        """

        :return:
        """
        self._parser_status = ResponseStatus.CHUNKED_TRANSFER
        while self._parser_status == ResponseStatus.CHUNKED_TRANSFER:
            self._parser.feed(await self._connection.read_until(b'\r\n'))

    async def receive_headers(self):
        """

        :return:
        """
        if self._parser_status != ResponseStatus.PENDING_HEADERS:
            return
        try:
            self._parser.feed(await self._connection.read_until(b'\r\n\r\n'))
            if self._headers.get('content-encoding') == 'gzip':
                self._decoder = GzipDecoder()
            self._parser_status = ResponseStatus.PENDING_BODY
        except OSError as error:
            # In case any network error occurs we should discard this connection.
            self._parser_status = ResponseStatus.ERROR
            self._connection.close()
            raise error

    async def _release_connection(self):
        """

        :return:
        """
        await self._connection.pool.release_connection(self._connection, self._parser.should_keep_alive())

    async def stream(self, chunk_size: int=1*1024*1024, chunk_timeout: int=10,
                     complete_timeout: int=300):
        """

        :param complete_timeout:
        :param chunk_timeout:
        :param chunk_size:
        :return:
        """
        if self._parser_status not in (ResponseStatus.PENDING_HEADERS, ResponseStatus.PENDING_BODY):
            raise StreamAlreadyConsumed
        if self._parser_status == ResponseStatus.PENDING_HEADERS:
            await wait_for(self.receive_headers(), chunk_timeout)

        try:
            length = int(self.headers['Content-Length'])
            remaining = length
            while remaining:
                bytes_to_read = min(remaining, chunk_size)
                task = self._connection.read_exactly(bytes_to_read)
                start_time = time.time()
                self._parser.feed(await wait_for(task, min(chunk_timeout, complete_timeout)))
                complete_timeout -= time.time() - start_time
                remaining -= bytes_to_read
                yield bytes(self._content)
                self._content = bytearray()
        except KeyError:
            if self._headers.get('Transfer-Encoding') == 'chunked':
                self._parser_status = ResponseStatus.CHUNKED_TRANSFER
                while self._parser_status == ResponseStatus.CHUNKED_TRANSFER:
                    task = self._connection.read_until(b'\r\n')
                    start_time = time.time()
                    try:
                        self._parser.feed(await wait_for(task, min(chunk_timeout, complete_timeout)))
                    except asyncio.LimitOverrunError as error:
                        self._parser.feed(await self._connection.read_exactly(error.consumed))
                    complete_timeout -= time.time() - start_time
                    while len(self._content) >= chunk_size:
                        yield self._content[:chunk_size]
                        self._content = self._content[chunk_size:]
                while len(self._content) > 0:
                    yield self._content[:chunk_size]
                    self._content = self._content[chunk_size:]
            else:
                raise Exception('Invalid response.')
        except ValueError:
            raise Exception('Invalid content-length header.')

    def is_redirect(self):
        return self.headers.get('location') is not None

    #############
    # # #  Http Parser Callbacks
    ######################################

    def on_headers_complete(self, headers, status_code):
        """

        :param headers:
        :param status_code:
        :return:
        """
        self._headers = headers
        self._status_code = status_code

    def on_body(self, data: bytes):
        """

        :param data:
        :return:
        """
        if self._decoder is not None:
            self._content.extend(self._decoder.decompress(data))
        else:
            self._content.extend(data)

    def on_message_complete(self):
        """

        :return:
        """
        self._parser_status = ResponseStatus.COMPLETE
        try:
            self._connection.loop.create_task(self._release_connection())
        except Exception as error:
            print(error)

    def chunk_complete(self): pass

    def __repr__(self):
        if 400 > self.status_code >= 300:
            if len(self.url) > 30:
                url = self.url[:30] + '...'
            else:
                url = self.url
            return f'<Response [{self.status_code} => "{url}"]>'
        else:
            return f'<Response [{self.status_code}]>'


class BodyStream:
    def __init__(self, response: Response):
        self.response = response

    async def __aiter__(self):
        return self

    async def __anext__(self):
        pass
