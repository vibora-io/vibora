import os
import hashlib
from functools import lru_cache, partial
from mimetypes import MimeTypes
from .request import Request
from .utils import RangeFile
from .responses import StreamingResponse, Response, CachedResponse
from .exceptions import StaticNotFound


def streaming_file(path: str, chunk_size: int=1 * 1024 * 1024):
    with open(path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


class CacheEntry:

    mime = MimeTypes()

    def __init__(self, path: str, available_cache_size: int=0):
        self.path = path
        self.content_type = self.mime.guess_type(path)
        self.etag = self.get_hash(path)
        self.last_modified = os.path.getmtime(path)
        self.content_length = os.path.getsize(path)
        self.headers = {
            'Last-Modified': str(self.last_modified),
            'ETag': self.etag,
            'Content-Type': self.content_type[0],
            'Content-Length': str(self.content_length),
            'Accept-Ranges': 'bytes'
        }
        if available_cache_size > self.content_length:
            with open(path, 'rb') as f:
                self.response = CachedResponse(f.read(), headers=self.headers)
        else:
            self.response = StreamingResponse(partial(streaming_file, path), headers=self.headers)

    @property
    def needs_update(self):
        return os.path.getmtime(self.path) != self.last_modified

    @staticmethod
    def get_hash(path: str, chunk_size=1 * 1024 * 1024):
        md5 = hashlib.md5()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5.update(chunk)
        return md5.hexdigest()


class StaticHandler:
    def __init__(self, paths: list, host=None, url_prefix='/static', max_cache_size=10 * 1024 * 1024,
                 default_responses: dict=None):
        self.paths = paths
        self.host = host
        self.url_prefix = url_prefix
        self.cache = {}
        self.max_cache_size = max_cache_size
        self.current_cache_size = 0
        self.default_responses = default_responses or {}
        self.default_responses.update({
            304: Response(b'', status_code=304)
        })

    @property
    def available_cache_size(self):
        return self.max_cache_size - self.current_cache_size

    def extract_path(self, request: Request):
        url = request.url.decode('utf-8')
        path = url.replace(self.url_prefix, '')
        return path.split('?')[0].split('#')[0]

    @lru_cache(maxsize=128 * 128)
    def exists(self, path: str):
        return os.path.isfile(path)

    @staticmethod
    def get_last_modified_header(request):
        last_modified_client = request.headers.get('If-Modified-Since')
        if last_modified_client:
            try:
                return float(last_modified_client)
            except ValueError:
                return None

    def parse_response(self, request: Request, cache: CacheEntry):
        # Handling Last Modified
        last_modified_client = self.get_last_modified_header(request)
        if last_modified_client:
            if cache.last_modified <= last_modified_client:
                return self.default_responses[304]

        # Handling etags
        etag_client = request.headers.get('If-None-Match')
        if etag_client and cache.etag in etag_client:
            return self.default_responses[304]

        # Handling Range-Requests
        range_header = request.headers.get('Range')
        if range_header:
            pieces = self.get_range_pieces(range_header)
            if len(pieces) == 2:
                start, end = int(pieces[0]), int(pieces[1])
                headers = {
                    'Content-Range': 'bytes {0}-{1}/{2}'.format(start, end, cache.content_length),
                    'Content-Length': str((end - start)),
                    'Accept-Ranges': 'bytes'
                }
                if request.method == 'HEAD':
                    return Response(b'', headers=headers, status_code=206)
                else:
                    return StreamingResponse(RangeFile(cache.path, start, end).stream,
                                             headers=headers, status_code=206)

        # Handling HEAD requests
        if request.method == 'HEAD':
            return Response(b'', headers=cache.headers)

        return cache.response

    @staticmethod
    def get_range_pieces(header: str) -> list:
        header = header[header.find('=')+1:]
        values = header.strip().split('-')
        return values

    async def handle(self, request: Request):
        path = self.extract_path(request)
        if '../' in path:
            raise StaticNotFound()
        if path not in self.cache or self.cache[path].needs_update:
            for root_path in self.paths:
                real_path = root_path + path
                if self.exists(real_path):
                    cached = CacheEntry(real_path, self.available_cache_size)
                    if isinstance(cached.response, CachedResponse):
                        self.current_cache_size += cached.content_length
                    self.cache[path] = cached
                    return self.parse_response(request, cached)
            raise StaticNotFound()
        return self.parse_response(request, self.cache[path])

    def url_for(self, path: str):
        if not path.startswith('/'):
            path = '/' + path
        return self.url_prefix + path
