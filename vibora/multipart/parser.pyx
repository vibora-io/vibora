"""
TODO: Asynchronous IO for files.
"""
import os
import shutil
import uuid
from tempfile import gettempdir


DEF EXPECTING_BOUNDARY = 1
DEF EXPECTING_CONTENT_HEADERS = 2
DEF EXPECTING_BUFFER = 3


cdef class UploadedFile:

    cdef public str filename

    def __init__(self, filename=None):
        self.filename = filename

    async def save(self, str destination):
        raise NotImplementedError

    async def read(self, int count=0):
        raise NotImplementedError

    async def write(self, data: bytes):
        raise NotImplementedError

    def seek(self, pos):
        raise NotImplementedError


cdef class MemoryFile(UploadedFile):

    cdef:
        bytearray f
        int pointer

    def __init__(self, filename=None, f=None):
        super().__init__(filename=filename)
        self.f = f or bytearray()
        self.pointer = 0

    async def write(self, bytes data):
        """

        :param data:
        :return:
        """
        self.f.extend(data)
        self.pointer += len(data)

    async def read(self, count=0) -> bytes:
        """

        :param count:
        :return:
        """
        if count:
            data = self.f[self.pointer:(self.pointer + count)]
            self.pointer += count
        else:
            data = self.f[self.pointer:]
            self.pointer = len(self.f)
        return bytes(data)

    async def save(self, str destination):
        """

        :param destination:
        :return:
        """
        with open(destination, 'wb') as f:
            f.write(self.f)

    def seek(self, pos):
        """

        :param pos:
        :return:
        """
        self.pointer = pos


cdef class DiskFile(UploadedFile):
    def __init__(self, filename=None, temporary_dir=None):
        super().__init__(filename=filename)
        self.temporary_path = os.path.join(temporary_dir or gettempdir(), str(uuid.uuid4()))
        self.pointer = 0
        self.delete_on_exit = True

    def seek(self, pos):
        """

        :param pos:
        :return:
        """
        self.pointer = pos

    async def write(self, bytes data):
        """

        :param data:
        :return:
        """
        with open(self.temporary_path, 'ab+') as f:
            f.write(data)
        self.pointer += len(data)

    async def read(self, int count=0):
        """

        :param count:
        :return:
        """
        with open(self.temporary_path, 'rb') as f:
            f.seek(self.pointer)
            data = f.read(count)
            self.pointer += count or 0
            return data

    async def save(self, str destination):
        """

        :param destination:
        :return:
        """
        shutil.move(self.temporary_path, destination)
        self.delete_on_exit = False

    def __del__(self):
        if self.delete_on_exit is True:
            try:
                os.remove(self.temporary_path)
            except FileNotFoundError:
                pass


cdef class SmartFile:

    def __init__(self, filename=None, in_memory_limit=10 * 1024 * 1024, temp_dir: str=None):
        self.buffer = bytearray()
        self.pointer = 0
        self.engine = None
        self.in_memory_limit = in_memory_limit
        self.in_memory = True
        self.filename = filename
        self.temp_dir = temp_dir

    async def write(self, bytearray data):
        """
        
        :param data: 
        :return: 
        """
        cdef int data_size = len(data)
        if self.in_memory:
            if len(self.buffer) + data_size > self.in_memory_limit:
                self.engine = DiskFile(filename=self.filename, temporary_dir=self.temp_dir)
                self.engine.write(self.buffer)
                self.in_memory = False
            else:
                self.buffer.extend(data)
                self.pointer += data_size
        else:
            self.engine.write(data)

    cdef object consume(self):
        """
        
        :return: 
        """
        if self.in_memory:
            if self.filename:
                return MemoryFile(filename=self.filename, f=self.buffer)
            return self.buffer.decode()
        self.engine.seek(0)
        return self.engine


cdef class MultipartParser:

    def __init__(self, bytes boundary, str temp_dir: str=None, int in_memory_threshold=1 * 1024 * 1024):
        self.data = bytearray()
        self.values = {}
        self.temp_dir = None
        self.in_memory_threshold = in_memory_threshold

        # State machine related
        self.start_boundary = b'--' + boundary
        self.boundary_length = len(self.start_boundary)
        self.end_boundary = b'--' + boundary + b'--' + b'\r\n'
        self.status = EXPECTING_BOUNDARY
        self.current_buffer = None

    cdef inline bytearray clean_value(self, bytearray v):
        """
        
        :param v: 
        :return: 
        """
        if v[0] == 37 or v[0] == 34:
            v = v[1:]
        if v[-1] == 37 or v[-1] == 34:
            v = v[:-1]
        return v

    cdef void parse_header(self, bytearray header):
        """

        :param header:
        :return:
        """
        cdef dict parsed_values = {}
        cdef bytearray value
        cdef list pieces
        pos = header.find(b'Content-Disposition: form-data;') + 31
        header = header[pos:]
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
            self.values[parsed_values['name'].decode()] = (parsed_values, self.current_buffer)

    async def feed(self, bytes data):
        """

        :param data:
        :return:
        """
        cdef:
            int pos
            bytearray pending_data = self.data
            int boundary_length = self.boundary_length

        pending_data.extend(data)

        while pending_data:

            if pending_data == self.end_boundary:
                return

            if self.status == EXPECTING_BOUNDARY:
                if len(pending_data) >= boundary_length:
                    pos = pending_data.find(self.start_boundary)
                    if pos != -1:
                        del pending_data[:(pos + len(self.start_boundary))]
                        self.status = EXPECTING_CONTENT_HEADERS
                    else:
                        raise ValueError('Missing boundaries.')
                else:
                    return

            if self.status == EXPECTING_CONTENT_HEADERS:
                pos = pending_data.find(b'\r\n\r\n')
                if pos != -1:
                    self.parse_header(pending_data[:pos])
                    del pending_data[:pos + 4]
                    self.status = EXPECTING_BUFFER
                else:
                    return

            if self.status == EXPECTING_BUFFER:
                pos = pending_data.find(self.start_boundary)
                if pos != -1:
                    await self.current_buffer.write(pending_data[:pos - 2])
                    del pending_data[:pos]
                    self.current_buffer = None
                    self.status = EXPECTING_BOUNDARY
                    continue
                elif len(pending_data) >= boundary_length * 40:
                    # We cannot flush the entire stream because maybe
                    # the boundary is sliced between two chunks.
                    await self.current_buffer.write(pending_data[:len(pending_data) - boundary_length])
                    del pending_data[:-boundary_length]
                return

    cdef dict consume(self):
        """

        :return:
        """
        cdef str key
        cdef tuple values
        cdef dict parsed_values = {}
        cdef SmartFile file
        for key, values in self.values.items():
            file = values[1]
            parsed_values[key] = file.consume()
        return parsed_values
