from typing import List
from urllib.parse import urlparse, parse_qs, ParseResult
from asyncio import Event
from queue import deque
from ..multipart import MultipartParser, DiskFile, MemoryFile, UploadedFile
from ..exceptions import InvalidJSON
from ..sessions import Session
from ..utils import RequestParams
from ..headers.headers import Headers
from ..utils import json


class StreamQueue:

    def __init__(self):
        self.items = deque()
        self.event = Event()
        self.waiting = False
        self.dirty = False
        self.finished = False

    async def get(self) -> bytes:
        try:
            return self.items.popleft()
        except IndexError:
            if self.finished is True:
                return b''
            else:
                self.event.clear()
                self.waiting = True
                await self.event.wait()
                self.event.clear()
                self.waiting = False
                return self.items.popleft()

    def put(self, item):
        self.dirty = True
        self.items.append(item)
        if self.waiting is True:
            self.event.set()

    def clear(self):
        if self.dirty:
            self.items.clear()
            self.event.clear()
            self.dirty = False
        self.finished = False

    def end(self):
        if self.waiting:
            self.put(None)
        self.finished = True


class Stream:

    def __init__(self, connection):
        self.consumed = False
        self.queue = StreamQueue()
        self.connection = connection

    async def read(self) -> bytearray:
        data = bytearray()
        if self.consumed:
            raise Exception('Stream already consumed.')
        async for chunk in self:
            data.extend(chunk)
        return data

    async def __aiter__(self):
        while True:
            self.connection.resume_reading()
            data = await self.queue.get()
            if not data:
                self.consumed = True
                break
            self.connection.pause_reading()
            yield data

    def clear(self):
        """
        Resets the stream status.
        :return: None
        """
        self.queue.clear()
        self.consumed = False


class Request:

    def __init__(self, url: bytes, headers: Headers, method: bytes, stream: Stream, protocol):

        self.url = url
        self.protocol = protocol
        self.method = method
        self.headers = headers
        self.context = {}
        self.stream = stream
        self.__cookies = None
        self.__args = None
        self.__parsed_url = None
        self.__form = None

    @property
    def app(self):
        return self.protocol.app

    def client_ip(self) -> str:
        return self.protocol.client_ip()

    @property
    def parsed_url(self) -> ParseResult:
        """

        :return:
        """
        if not self.__parsed_url:
            self.__parsed_url = urlparse(self.url)
        return self.__parsed_url

    @property
    def args(self) -> RequestParams:
        """

        :return:
        """
        if not self.__args:
            self.__args = RequestParams(parse_qs(self.parsed_url.query))
        return self.__args

    @property
    def cookies(self) -> dict:
        """

        :return:
        """
        if self.__cookies is None:
            self.__cookies = self.headers.parse_cookies()
        return self.__cookies

    async def session(self) -> Session:
        """

        :return:
        """
        return self.app.session_engine.load(self)

    async def json(self, loads=None, strict: bool=False) -> dict:
        """

        :param loads:
        :param strict:
        :return:
        """
        if strict:
            ct = self.headers.get('Content-Type')
            conditions = (
                ct == 'application/json',
                ct.startswith('application/') and ct.endswith('+json')
            )
            if not any(conditions):
                raise InvalidJSON('JSON strict mode is enabled '
                                  'and HTTP header does not match the required format.')
        loads = loads or json.loads
        try:
            return loads((await self.stream.read()).decode())
        except ValueError:
            raise InvalidJSON('HTTP request body is not a valid JSON.', 400)

    async def _load_form(self):
        """

        :return:
        """
        content_type = self.headers.get('Content-Type')
        if 'multipart/form-data' in content_type:
            boundary = content_type[content_type.find('boundary=') + 9:]
            parser = MultipartParser(boundary.encode(), temp_dir=self.app.temporary_dir)
            async for chunk in self.stream:
                parser.feed_data(chunk)
            self.__form = parser.consume()
        else:
            self.__form = {}

    async def files(self) -> List[UploadedFile]:
        """

        :return:
        """
        if self.__form is None:
            await self._load_form()
        files = []
        for key, value in self.__form.items():
            if isinstance(value, (DiskFile, MemoryFile)):
                files.append(value)
        return files

    async def form(self) -> dict:
        """

        :return:
        """
        if self.__form is None:
            await self._load_form()
        return self.__form
