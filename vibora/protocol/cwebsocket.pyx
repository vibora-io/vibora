

cdef class WebsocketConnection:

    def __cinit__(self, object app, object handler, object loop, object transport):
        self.app = app
        self.handler = handler
        self.loop = loop
        self.transport = transport

    cpdef void data_received(self, bytes data):
        task = self.handler.feed(data)
        self.loop.create_task(task)

    cpdef void connection_lost(self, exc):
        self.app.connections.discard(self)
