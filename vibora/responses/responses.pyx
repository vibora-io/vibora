#######################################################
# This is a very sensitive file.
# The whole framework performance is highly impacted by the implementations here.
# There are a lot of "bad practices" here, super calls avoided, duplicated code, early bindings everywhere.
# Tests should help us stay calm and maintain this.
# Raw ** performance ** is our ** main goal ** here.
#######################################################
import asyncio
from typing import Callable
from inspect import isasyncgenfunction
from email.utils import formatdate
from functools import partial
from concurrent.futures import TimeoutError
from .. import constants
from ..utils import json

# C IMPORTS
# noinspection PyUnresolvedReferences
from ..protocol.cprotocol cimport Connection
###############################################

cdef str current_time = formatdate(timeval=None, localtime=False, usegmt=True)
cdef dict ALL_STATUS_CODES = constants.ALL_STATUS_CODES


async def stream_response(response: 'StreamingResponse', protocol, chunk_timeout):
    """

    :param chunk_timeout:
    :param response:
    :param protocol:
    :return:
    """
    try:
        write = protocol.write
        await write(response.encode())
        if not response.is_async:
            for chunk in response.stream():
                await asyncio.wait_for(write(chunk), chunk_timeout)
        else:
            async for chunk in response.stream():
                await asyncio.wait_for(write(chunk), chunk_timeout)
        protocol.after_response(response)
    except TimeoutError:
        protocol.close()


async def stream_chunked_response(response: 'StreamingResponse', protocol, chunk_timeout):
    """

    :param chunk_timeout:
    :param response:
    :param protocol:
    :return:
    """
    try:
        write = protocol.write
        await write(response.encode())
        if not response.is_async:
            for chunk in response.stream():
                content = b''.join([('%X\r\n' % len(chunk)).encode(), chunk, b'\r\n'])
                await asyncio.wait_for(write(content), chunk_timeout)
        else:
            async for chunk in response.stream():
                await asyncio.wait_for(write(b''.join([('%X\r\n' % len(chunk)).encode(), chunk, b'\r\n'])),
                                       chunk_timeout)
        await write(b'0\r\n\r\n')
        protocol.after_response(response)
    except TimeoutError:
        protocol.close()


async def wait_client_consume(response, protocol):
    """

    :param response:
    :param protocol:
    :return:
    """
    if not protocol.writable:
        await protocol.write_premission()
    protocol.after_response(response)


def cancel_streaming_task(task, protocol):
    task.cancel()
    protocol.close()


cdef class Response:

    def __init__(self, content: bytes, status_code: int = 200, headers: dict = None, cookies: list = None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.cookies = cookies or []

    cdef bytes encode(self):
        headers = self.headers
        headers['Content-Length'] = len(self.content)
        headers['Date'] = current_time
        content = f'HTTP/1.1 {self.status_code} {ALL_STATUS_CODES[self.status_code]}\r\n'
        for header, value in headers.items():
            content += f'{header}: {value}\r\n'
        if self.cookies:
            for cookie in self.cookies:
                content += cookie.header + '\r\n'
        content += '\r\n'
        return content.encode()

    def clone(self, **kwargs):
        params = {
            'content': self.content,
            'status_code': self.status_code,
            'headers': self.headers,
            'cookies': self.cookies
        }
        params.update(kwargs)
        return self.__class__(**params)

    cdef void send(self, Connection protocol):
        # We check if the protocol is writable because we wanna make sure we aren't making the write buffer
        # surpass the high-mark. To actually process the next response we need to call after_response()
        # but if we don't know yet if the client consumed the response we could be generating responses too fast
        # and blow up the server memory... that's why we schedule the after_response() call.
        # Since the content of this response is already in memory, we take a shortcut
        # and add it to the buffers anyway. At this moment, protocol is not reading the socket until the write buffer
        # is consumed by the client.
        if self.headers or self.cookies:
            protocol.transport.write(self.encode() + self.content)
        else:
            protocol.transport.write(
                f'HTTP/1.1 {self.status_code} {ALL_STATUS_CODES[self.status_code]}\r\n'
                f'Content-Length: {len(self.content)}\r\nDate: {current_time}\r\n\r\n'.encode() + self.content
            )
        if protocol.writable is False:
            protocol.loop.create_task(wait_client_consume(self, protocol))
        else:
            protocol.after_response(self)


cdef class CachedResponse(Response):

    def __init__(self, content: bytes, status_code: int = 200, headers: dict = None, cookies: list = None):
        # Super is skipped on purpose.
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        if 'Content-Length' not in self.headers:
            self.headers['Content-Length'] = str(len(self.content))
        self.headers['Date'] = '$date'
        self.cookies = cookies or []
        self.cache = None

    cdef bytes encode(self):
        headers = self.headers
        headers['Content-Length'] = len(self.content)
        headers['Date'] = '$date'
        content = f'HTTP/1.1 {self.status_code} {ALL_STATUS_CODES[self.status_code]}\r\n'
        for header, value in headers.items():
            content += f'{header}: {value}\r\n'
        if self.cookies:
            for cookie in self.cookies:
                content += cookie.header + '\r\n'
        content += '\r\n'
        return content.encode()

    cdef void send(self, Connection protocol):
        if self.cache is None:
            headers = self.encode()
            self.cache = (
                headers[:headers.find(b'$date')],
                headers[headers.find(b'$date') + 5:]
            )
        cache = self.cache
        protocol.transport.write(cache[0] + current_time.encode() + cache[1] + self.content)
        if protocol.writable:
            protocol.after_response(self)
        else:
            protocol.loop.create_task(wait_client_consume(self, protocol))


cdef class JsonResponse(Response):

    def __init__(self, content: object, status_code: int = 200, headers: dict = None, cookies: list = None):
        self.status_code = status_code
        self.content = json.dumps(content).encode()
        self.headers = headers or {}
        self.headers['Content-Type'] = 'application/json'
        self.cookies = cookies or []


cdef class RedirectResponse(Response):

    def __init__(self, location, status_code: int = 302, headers: dict = None, cookies: list = None):
        self.status_code = status_code
        self.content = b''
        self.headers = headers or {}
        self.headers.update({
            'Location': location,
            'Content-Length': '0',
        })
        self.cookies = cookies or []


cdef class StreamingResponse(Response):

    def __init__(self, stream: Callable, status_code: int = 200, headers: dict = None, cookies: list = None,
                 complete_timeout: int = 30, chunk_timeout: int = 10):
        if not callable(stream):
            raise ValueError('StreamingResponse "stream" must be a callable.')
        self.stream = stream
        self.content = b''
        self.status_code = status_code
        self.is_async = isasyncgenfunction(stream)
        self.headers = headers or {}
        if 'Content-Length' in self.headers:
            self.chunked = False
        else:
            self.chunked = True
            self.headers['Transfer-Encoding'] = 'chunked'
        self.cookies = cookies or []
        self.complete_timeout = complete_timeout
        self.chunk_timeout = chunk_timeout

    cdef bytes encode(self):
        content = f'HTTP/1.1 {self.status_code} {ALL_STATUS_CODES[self.status_code]}\r\n'
        for header, value in self.headers.items():
            content += f'{header}: {value}\r\n'
        if self.cookies:
            for cookie in self.cookies:
                content += cookie.header + '\r\n'
        content += '\r\n'
        return content.encode()

    cdef void send(self, Connection protocol):
        # Streaming responses make use of a custom timeout function because
        # we don't to send a response in case a timeout.
        # The client could handle the timeout response as part of the stream and a luck enough
        # guy could even match the remaining byte count.
        protocol.timeout_task.cancel()

        # Creating the streaming task.
        f = stream_chunked_response if self.chunked else stream_response
        task = partial(f, response=self, protocol=protocol, chunk_timeout=self.chunk_timeout)
        streaming_task = protocol.loop.create_task(task())

        # Creating the timeout task and setting it in the protocol so after_response()
        # can correctly cancel it if needed.
        if self.complete_timeout > 0:
            protocol.timeout_task = protocol.loop.call_later(
                self.complete_timeout, partial(cancel_streaming_task, streaming_task, protocol)
            )


cdef class WebsocketHandshakeResponse(Response):
    def __init__(self, key: bytes):
        self.status_code = 101
        self.content = b''
        self.cookies = []
        self.headers = {
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-Websocket-Accept': key.decode('utf-8')
        }


def update_current_time(value):
    global current_time
    current_time = value
