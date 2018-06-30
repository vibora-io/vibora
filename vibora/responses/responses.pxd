#cython: language_level=3, boundscheck=False, wraparound=False
import cython

# C IMPORTS
# noinspection PyUnresolvedReferences
from ..protocol.cprotocol cimport Connection
###############################################

cdef str current_time


@cython.freelist(409600)
cdef class Response:

    cdef:
        public int status_code
        public bytes content
        public dict headers
        public list cookies
        public bint skip_hooks

    cdef bytes encode(self)

    cdef void send(self, Connection protocol)


cdef class CachedResponse(Response):
    cdef tuple cache
    cdef void send(self, Connection protocol)


cdef class JsonResponse(Response):
    pass


cdef class WebsocketHandshakeResponse(Response):
    pass


cdef class RedirectResponse(Response):
    pass


cdef class StreamingResponse(Response):
    cdef:
        public bytes content_type
        public object stream
        public bint is_async
        public int complete_timeout
        public int chunk_timeout
        bint chunked

    cdef bytes encode(self)

    cdef void send(self, Connection protocol)
