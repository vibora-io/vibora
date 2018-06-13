import inspect
import shutil
import uuid
import os
from io import BytesIO
from tempfile import gettempdir


class UploadedFile:
    def __init__(self, filename=None):
        self.filename = filename

    def save(self, destination: str):
        raise NotImplementedError

    def read(self, count=None):
        raise NotImplementedError

    def seek(self, pos):
        raise NotImplementedError

    def write(self, data: bytes):
        raise NotImplementedError


class MemoryFile(UploadedFile):

    def __init__(self, filename=None):
        super().__init__(filename=filename)
        self.f = BytesIO()

    def write(self, data: bytes):
        return self.f.write(data)

    def read(self, count=None):
        return self.f.read(count)

    def seek(self, pos):
        return self.f.seek(pos)

    def save(self, destination: str):
        with open(destination, 'wb') as f:
            self.f.seek(0)
            f.write(self.f.read())


class DiskFile(UploadedFile):
    def __init__(self, filename=None, temporary_dir=None):
        super().__init__(filename=filename)
        self.temporary_path = os.path.join(temporary_dir or gettempdir(), str(uuid.uuid4()))
        self.pointer = 0
        self.delete_on_exit = True

    def seek(self, pos):
        self.pointer = pos

    def write(self, data: bytes):
        with open(self.temporary_path, 'ab+') as f:
            f.write(data)
        self.pointer += len(data)

    def read(self, count=None):
        with open(self.temporary_path, 'rb') as f:
            f.seek(self.pointer)
            data = f.read(count)
            self.pointer += count or 0
            return data

    def save(self, destination: str):
        shutil.move(self.temporary_path, destination)
        self.delete_on_exit = False

    def __del__(self):
        if self.delete_on_exit is True:
            try:
                os.remove(self.temporary_path)
            except FileNotFoundError:
                pass


class SmartFile:
    def __init__(self, filename=None, in_memory_size=10 * 1024 * 1024, temp_dir: str=None):
        self.engine = BytesIO()
        self.length = 0
        self.in_memory_size = in_memory_size
        self.in_memory = True
        self.filename = filename
        self.temp_dir = temp_dir

    def seek(self, pos):
        self.engine.seek(pos)

    def write(self, data: bytes):
        if self.in_memory is True:
            if len(data) + self.length > self.in_memory_size:
                self.engine.seek(0)
                new_engine = DiskFile(filename=self.filename, temporary_dir=self.temp_dir)
                new_engine.write(self.engine.read())
                self.engine = new_engine
                self.engine.write(data)
                self.in_memory = False
                return
        self.length += len(data)
        self.engine.write(data)

    def consume(self):
        self.engine.seek(0)
        if self.in_memory is True and not self.filename:
            return self.engine.read().decode('UTF-8')
        elif self.in_memory is True:
            mf = MemoryFile(filename=self.filename)
            mf.f = self.engine
            return mf
        return self.engine


class MultipartParser:
    def __init__(self, boundary: bytes, temp_dir: str=None, in_memory_threshold: int=1 * 1024 * 1024):
        self.data = bytearray()
        self.values = {}
        self.temp_dir = temp_dir or gettempdir()
        self.in_memory_threshold = in_memory_threshold

        # State machine related
        self.start_boundary = b'--' + boundary
        self.boundary_length = len(self.start_boundary)
        self.end_boundary = b'--' + boundary + b'--' + b'\r\n'
        self.expecting_boundary = True
        self.expecting_content_headers = False
        self.expecting_buffer = False
        self.current_buffer = None

    @staticmethod
    def clean_value(v: bytes):
        if v[0] == 37 or v[0] == 34:
            v = v[1:]
        if v[-1] == 37 or v[-1] == 34:
            v = v[:-1]
        return v

    def parse_header(self, header: bytearray):
        """

        :param header:
        :return:
        """
        search_for = b'Content-Disposition: form-data;'
        pos = header.find(search_for) + len(search_for)
        header = header[pos:]
        parsed_values = {}
        values = header.strip().split(b';')
        for value in values:
            value = value.strip()
            pieces = value.split(b'=')
            if len(pieces) == 2:
                parsed_values[pieces[0].decode()] = self.clean_value(pieces[1])
        if 'name' in parsed_values:
            filename = parsed_values.get('filename')
            self.current_buffer = SmartFile(filename=filename.decode('utf-8') if filename else None,
                                            temp_dir=self.temp_dir)
            self.values[parsed_values['name'].decode()] = {
                "values": parsed_values,
                "buffer": self.current_buffer
            }

    def feed_data(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.data.extend(data)

        while len(self.data) > 0:

            if self.data == self.end_boundary:
                return

            if self.expecting_boundary is True:
                if len(self.data) >= self.boundary_length:
                    pos = self.data.find(self.start_boundary)
                    if pos != -1:
                        del self.data[:(pos + len(self.start_boundary))]
                        self.expecting_content_headers = True
                        self.expecting_boundary = False
                    else:
                        raise ValueError('Missing boundaries.')
                else:
                    return

            if self.expecting_content_headers:
                pos = self.data.find(b'\r\n\r\n')
                if pos != -1:
                    self.parse_header(self.data[:pos])
                    del self.data[:pos + 4]
                    # self.data = self.data[pos + 2:]
                    self.expecting_content_headers = False
                    self.expecting_buffer = True
                else:
                    return

            if self.expecting_buffer:
                pos = self.data.find(self.start_boundary)
                if pos != -1:
                    self.current_buffer.write(memoryview(self.data)[:pos - 2])
                    del self.data[:pos]
                    self.current_buffer = None
                    self.expecting_boundary = True
                    self.expecting_buffer = False
                    continue
                elif len(self.data) >= self.boundary_length * 40:
                    # We cannot flush the entire stream because maybe
                    # the boundary is sliced between two chunks.
                    mem = memoryview(self.data)
                    self.current_buffer.write(mem[:len(self.data) - self.boundary_length])
                    self.data = self.data[len(self.data) - self.boundary_length:]
                return

    def consume(self):
        """

        :return:
        """
        parsed_values = {}
        for key, values in self.values.items():
            parsed_values[key] = values['buffer'].consume()
        return parsed_values


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
