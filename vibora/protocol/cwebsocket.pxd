

cdef class WebsocketConnection:

    cdef:
        object app
        object handler
        object loop
        object transport

    cpdef void data_received(self, bytes data)
    cpdef void connection_lost(self, exc)
