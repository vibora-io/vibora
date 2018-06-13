import asyncio
from asyncio import BaseEventLoop
from collections import deque
from .connection import Connection, SECURE_CONTEXT, INSECURE_CONTEXT


class ConnectionPool:

    __slots__ = ('loop', 'host', 'port', 'protocol', 'max_connections', 'connections', 'available_connections',
                 'keep_alive', 'wait_connection_available')

    def __init__(self, loop: BaseEventLoop, host: str, port: int, protocol: str, keep_alive: bool=True):
        self.loop = loop
        self.host = host
        self.port = port
        self.protocol = protocol
        self.available_connections = deque()
        self.connections = set()
        self.keep_alive = keep_alive

    async def create_connection(self, ssl=None) -> Connection:
        """

        :param ssl:
        :return:
        """
        args = {'host': self.host, 'port': self.port, 'loop': self.loop}
        if self.protocol == 'https':
            if ssl is False:
                args['ssl'] = INSECURE_CONTEXT
            elif ssl is None:
                args['ssl'] = SECURE_CONTEXT
            else:
                args['ssl'] = ssl
        reader, writer = await asyncio.open_connection(**args)
        connection = Connection(self.loop, reader, writer, self)
        self.connections.add(connection)
        return connection

    async def get_connection(self, ssl) -> Connection:
        """

        :param ssl:
        :return:
        """
        try:
            connection = self.available_connections.pop()
            if not await connection.is_dropped():
                return connection
            else:
                await self.release_connection(connection, keep_alive=False)
                return await self.create_connection(ssl)
        except IndexError:
            return await self.create_connection(ssl)

    async def release_connection(self, connection: Connection, keep_alive=True):
        """

        :param connection:
        :param keep_alive:
        :return:
        """
        if keep_alive and self.keep_alive:
            self.available_connections.appendleft(connection)
        else:
            connection.close()
            self.connections.discard(connection)

    def close(self):
        """

        :return:
        """
        for connection in self.connections:
            connection.close()
