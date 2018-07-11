from inspect import iscoroutinefunction
from ..responses.responses import CachedResponse, Response
from ..request.request import Request


class CacheEngine:
    def __init__(self, skip_hooks: bool = True):
        self.is_async = iscoroutinefunction(self.get) or iscoroutinefunction(self.store)
        self.skip_hooks = skip_hooks
        self.cache = {}

    def get(self, request: Request):
        raise NotImplementedError

    def store(self, request: Request, response: Response):
        raise NotImplementedError


class Static(CacheEngine):
    def get(self, request: Request) -> CachedResponse:
        return self.cache.get(1)

    def store(self, request: Request, response: Response):
        self.cache[1] = CachedResponse(
            response.content, headers=response.headers, cookies=response.cookies
        )
