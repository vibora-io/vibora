"""
|===== Warning ================================================================================|
| This is a stub file to provide type hints because this module is fully implemented in Cython |
|==============================================================================================|
"""
from typing import Callable
from inspect import isasyncgenfunction
from ..utils import json


class Response:

    def __init__(self, content: bytes, status_code: int = 200, headers: dict = None, cookies: list = None):
        self.status_code: int = status_code
        self.content: bytes = content
        self.headers: dict = headers or {}
        self.cookies: list = cookies or []


class CachedResponse(Response):

    def __init__(self, content: bytes, status_code: int = 200, headers: dict = None, cookies: list = None):
        super().__init__(content=content, status_code=status_code, headers=headers, cookies=cookies)
        self.content = content
        self.cache = None


class JsonResponse(Response):

    def __init__(self, content: object, status_code: int = 200, headers: dict = None, cookies: list = None):
        super().__init__(content=json.dumps(content).encode(), status_code=status_code,
                         headers=headers, cookies=cookies)


class RedirectResponse(Response):

    def __init__(self, location: str, status_code: int = 302, headers: dict = None, cookies: list = None):
        super().__init__(b'', status_code=status_code, headers=headers, cookies=cookies)


class StreamingResponse(Response):

    def __init__(self, stream: Callable, status_code: int = 200, headers: dict = None, cookies: list = None,
                 complete_timeout: int = 30, chunk_timeout: int = 10):
        super().__init__(b'', status_code=status_code, headers=headers, cookies=cookies)
        if not callable(stream):
            raise ValueError('StreamingResponse "stream" must be a callable.')
        self.stream = stream
        self.content = b''
        self.is_async = isasyncgenfunction(stream)
        if 'Content-Length' in self.headers:
            self.chunked = False
        else:
            self.chunked = True
            self.headers['Transfer-Encoding'] = 'chunked'
        self.complete_timeout = complete_timeout
        self.chunk_timeout = chunk_timeout
