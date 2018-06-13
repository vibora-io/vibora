import socket
import sys
import time
import os
from typing import Tuple


if os.environ.get('VIBORA_UJSON', 1) == '0':
    # noinspection PyUnresolvedReferences
    import json
else:
    try:
        import ujson as json
    except ImportError:
        import json


if os.environ.get('VIBORA_UVLOOP', 1) == '0':
    # noinspection PyUnresolvedReferences
    import asyncio as asynclib
else:
    try:
        import uvloop as asynclib
    except ImportError:
        import asyncio as asynclib


class RequestParams:
    def __init__(self, values: dict):
        self.values = values

    def get(self, item):
        v = self.values.get(item)
        return v[0] if v else None

    def get_list(self, item, default=None):
        return self.values.get(item, default or [])

    def __getitem__(self, item):
        return self.values[item]

    def __getattr__(self, item):
        return getattr(self.values, item)


class RangeFile:
    def __init__(self, path: str, start: int, end: int, chunk_size=1 * 1024 * 1024):
        self.path = path
        self.current_pointer = start
        self.start = start
        self.end = end
        self.chunk_size = chunk_size
        self._file = open(self.path, 'rb')
        self._file.seek(self.current_pointer)

    def __iter__(self):
        while True:
            current_pointer = self._file.tell()
            if (current_pointer + self.chunk_size) < self.end:
                data = self._file.read(self.chunk_size)
            else:
                data = self._file.read(self.end - current_pointer)
            if data == b'':
                break
            yield data

    def read(self, count: int):
        if self.current_pointer == self.end:
            return None
        if (self.current_pointer + count) > self.end:
            count = self.end
        with open(self.path, 'rb') as f:
            f.seek(self.current_pointer)
            return f.read(count)

    def __del__(self):
        self._file.close()

    def stream(self):
        for chunk in self:
            yield chunk


def clean_route_name(prefix: str, name: str):
    if prefix:
        if prefix[0] == ':':
            prefix = prefix[1:]
        if len(prefix) > 0:
            if prefix[len(prefix)-1] == ':':
                prefix = prefix[:len(prefix) - 1]
        if len(prefix) > 0:
            return prefix + '.' + name
    return name


def clean_methods(methods) -> Tuple[bytes]:
    if methods:
        parsed_methods = []
        for method in methods:
            if isinstance(method, str):
                parsed_methods.append(method.upper().encode())
            elif isinstance(method, bytes):
                parsed_methods.append(method.upper())
            else:
                raise Exception('Methods should be str or bytes.')
        return tuple(parsed_methods)
    return b'GET',


def get_free_port(address='127.0.0.1') -> tuple:
    """
    The reference of the socket is returned, otherwise the port could
    theoretically (highly unlikely) be used be someone else.
    :return: (socket instance, port)
    """
    sock = socket.socket()
    sock.bind((address, 0))
    return sock, address, sock.getsockname()[1]


def wait_server_available(host, port, timeout: int=10):
    """
    Wait until the server is available by trying to connect to the same.
    :param timeout:
    :param host:
    :param port:
    :return:
    """
    sock = socket.socket()
    sock.settimeout(timeout)
    while timeout > 0:
        start_time = time.time()
        try:
            sock.connect((host, port))
            sock.close()
            return
        except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError):
            time.sleep(0.001)
            timeout -= time.time() - start_time
    sock.close()
    raise SystemError(f'Server is taking too long to get online.')


def wait_server_offline(host, port, timeout: int=10):
    """
    Wait until the server is offline.
    :param timeout:
    :param host:
    :param port:
    :return:
    """
    while timeout > 0:
        try:
            start_time = time.time()
            sock = socket.socket()
            sock.settimeout(1)
            sock.connect((host, port))
            time.sleep(1)
            timeout -= time.time() - start_time
        except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError):
            return
        finally:
            sock.close()
    raise SystemError(f'Server is still running after the timeout threshold.')


def cprint(message: str, color='\033[35m', mixed: bool=False):
    if sys.stdout.isatty() or os.environ.get('PYCHARM_HOSTED'):
        if mixed:
            print(message.format(color_=color, end_='\033[0m'))
        else:
            print(color + message + '\033[0m')
    else:
        print(message)
