from typing import List
from urllib.parse import urlparse, parse_qs, ParseResult
from asyncio import Event
from queue import deque
from ..multipart import DiskFile, MemoryFile, UploadedFile
from ..exceptions import InvalidJSON, StreamAlreadyConsumed
from ..sessions import Session
from ..utils import RequestParams
from ..utils import json

# noinspection PyUnresolvedReferences
from ..headers.headers cimport Headers
# noinspection PyUnresolvedReferences
from ..protocol.cprotocol cimport Connection
# noinspection PyUnresolvedReferences
from ..multipart.parser cimport MultipartParser


cdef class StreamQueue:

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

    cdef void put(self, bytes item):
        self.dirty = True
        self.items.append(item)
        if self.waiting is True:
            self.event.set()

    cdef void clear(self):
        if self.dirty:
            self.items.clear()
            self.event.clear()
            self.dirty = False
        self.finished = False

    cdef void end(self):
        if self.waiting:
            self.put(None)
        self.finished = True


cdef class Stream:

    def __init__(self, connection):
        self.consumed = False
        self.queue = StreamQueue()
        self.connection = connection

    async def read(self) -> bytearray:
        if self.consumed:
            raise StreamAlreadyConsumed()
        data = bytearray()
        async for chunk in self:
            data.extend(chunk)
        return data

    async def __aiter__(self):
        if self.consumed:
            raise StreamAlreadyConsumed()
        while True:
            self.connection.resume_reading()
            data = await self.queue.get()
            if not data:
                self.consumed = True
                break
            self.connection.pause_reading()
            yield data

    cdef void clear(self):
        """
        Resets the stream status.
        :return: None
        """
        self.queue.clear()
        self.consumed = False


cdef class Request:

    def __init__(self, bytes url, Headers headers, bytes method, Stream stream, Connection protocol):
        """

        :param url:
        :param headers:
        :param method:
        :param stream:
        :param protocol:
        """
        self.url = url
        self.protocol = protocol
        self.method = method
        self.headers = headers
        self.context = {}
        self.stream = stream
        self._cookies = None
        self._args = None
        self._parsed_url = None
        self._form = None
        self._session = None

    @property
    def app(self):
        return self.protocol.app

    cpdef str client_ip(self):
        return self.protocol.client_ip()

    @property
    def parsed_url(self) -> ParseResult:
        """

        :return:
        """
        if not self._parsed_url:
            self._parsed_url = urlparse(self.url)
        return self._parsed_url

    @property
    def args(self) -> RequestParams:
        """

        :return:
        """
        if not self._args:
            self._args = RequestParams(parse_qs(self.parsed_url.query))
        return self._args

    @property
    def cookies(self) -> dict:
        """

        :return:
        """
        if self._cookies is None:
            self._cookies = self.headers.parse_cookies()
        return self._cookies

    async def session(self) -> Session:
        """

        :return:
        """
        if not self._session:
            self._session = await self.app.session_engine.load(self.cookies)
        return self._session

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
        cdef str content_type
        content_type = self.headers.get('Content-Type')
        if 'multipart/form-data' in content_type:
            boundary = content_type[content_type.find('boundary=') + 9:]
            parser = MultipartParser(boundary.encode())
            async for chunk in self.stream:
                await parser.feed(chunk)
            self._form = parser.consume()
        else:
            self._form = {}

    async def files(self) -> List[UploadedFile]:
        """

        :return:
        """
        cdef list files = []
        if self._form is None:
            await self._load_form()
        for value in self._form.values():
            if isinstance(value, (DiskFile, MemoryFile)):
                files.append(value)
        return files

    async def form(self) -> dict:
        """

        :return:
        """
        if self._form is None:
            await self._load_form()
        return self._form

    cpdef session_pending_flush(self):
        """
        
        :return: 
        """
        if self._session and self._session.pending_flush:
            return self._session
