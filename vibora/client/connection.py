import ssl
from asyncio import StreamWriter, StreamReader, BaseEventLoop, wait_for, TimeoutError
from typing import Coroutine


SECURE_CONTEXT = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
SECURE_CONTEXT.check_hostname = True

INSECURE_CONTEXT = ssl.SSLContext()
INSECURE_CONTEXT.check_hostname = False


class Connection:

    __slots__ = ('loop', 'reader', 'writer', 'pool')

    def __init__(self, loop: BaseEventLoop, reader: StreamReader, writer: StreamWriter, pool):
        self.loop = loop
        self.reader = reader
        self.writer = writer
        self.pool = pool

    def sendall(self, data: bytes) -> Coroutine:
        """

        :param data:
        :return:
        """
        self.writer.write(data)
        return self.writer.drain()

    def read_exactly(self, length) -> Coroutine:
        """

        :param length:
        :return:
        """
        return self.reader.readexactly(length)

    def read_until(self, delimiter: bytes) -> Coroutine:
        """

        :param delimiter:
        :return:
        """
        return self.reader.readuntil(delimiter)

    def close(self):
        """

        :return:
        """
        self.writer.close()

    async def is_dropped(self):
        """

        :return:
        """
        try:
            await wait_for(self.reader.readexactly(0), 0.001)
            return True
        except TimeoutError:
            return False

    def release(self, keep_alive: bool=False):
        """

        :param keep_alive:
        :return:
        """
        self.pool.release_connection(self, keep_alive)
