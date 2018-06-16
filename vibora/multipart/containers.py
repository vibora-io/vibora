import inspect
import uuid
import os
from io import BytesIO


class BufferedIterable:
    def __init__(self, item):
        self.item = item
        self.cursor = self.item.__iter__()
        self.buffer = bytearray()

    def read(self, size):
        while len(self.buffer) < size:
            self.buffer.extend(self.cursor.__next__())
        temp = self.buffer[:size + 1]
        self.buffer = self.buffer[size + 1:]
        return temp


class FileUpload:
    def __init__(self, name: str=None, path: str=None, content: bytes=None, iterable=None,
                 f=None, headers: list=None):
        if not any([path, content, iterable, f]):
            raise Exception('You must supply either: path, content, iterable, f')
        self.name = name
        if f:
            self.f = f
        elif path:
            self.f = open(path, 'rb')
            if not self.name:
                self.name = os.path.basename(path)
        elif content:
            self.f = BytesIO(initial_bytes=content)
        elif iterable:
            self.f = BufferedIterable(iterable)
        if not self.name:
            self.name = str(uuid.uuid4())
        self.headers = headers
        self.is_async = inspect.iscoroutine(self.f.read)


class MultipartEncoder:

    def __init__(self, delimiter: bytes, params: dict, chunk_size: int=1*1024*1024,
                 loop=None, encoding: str='utf-8'):
        self.delimiter = b'--' + delimiter
        self.params = params
        self.chunk_size = chunk_size
        self.evaluated = False
        self.loop = loop
        self.encoding = encoding

    def create_headers(self, name: str, value) -> bytes:
        """

        :param name:
        :param value:
        :return:
        """
        if isinstance(value, FileUpload):
            return f'Content-Disposition: form-data; name="{name}"; filename="{value.name}"'.encode(self.encoding)
        else:
            return f'Content-Disposition: form-data; name="{name}"'.encode(self.encoding)

    def stream_value(self, value) -> bytes:
        """

        :param value:
        :return:
        """
        if isinstance(value, FileUpload):
            while True:
                if value.is_async:
                    chunk = self.loop.run_until_complete(value.f.read(self.chunk_size))
                else:
                    chunk = value.f.read(self.chunk_size)
                size = len(chunk)
                if size == 0:
                    break
                yield chunk
        else:
            if isinstance(value, int):
                yield str(value).encode()
            elif isinstance(value, str):
                yield value.encode(self.encoding)
            else:
                yield value

    def __iter__(self):
        """

        :return:
        """
        if self.evaluated:
            raise Exception('Streaming encoder cannot be evaluated twice.')
        for name, value in self.params.items():
            header = self.delimiter + b'\r\n' + self.create_headers(name, value) + b'\r\n\r\n'
            yield header
            for chunk in self.stream_value(value):
                yield chunk
            yield b'\r\n'
        yield self.delimiter + b'--'
        self.evaluated = True
