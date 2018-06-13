# cython: language_level=3, boundscheck=False, wraparound=False, annotation_typing=False
import cython
# noinspection PyUnresolvedReferences
from ..headers.headers cimport Headers
# noinspection PyUnresolvedReferences
from ..protocol.cprotocol cimport Connection


cdef class StreamQueue:

    cdef:
        readonly object items
        object event
        bint waiting
        bint dirty
        bint finished

    cdef void put(self, bytes item)
    cdef void clear(self)
    cdef void end(self)


cdef class Stream:

    cdef:
        bint consumed
        StreamQueue queue
        Connection connection

    cdef clear(self)


@cython.freelist(409600)
cdef class Request:

    cdef:
        readonly bytes url
        readonly bytes method
        readonly object parent
        readonly object protocol
        readonly bytearray body
        readonly Headers headers
        readonly dict context
        readonly Stream stream
        object __cookies
        object __parsed_url
        object __args
        dict __form

    cpdef str client_ip(self)
