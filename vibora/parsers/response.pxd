#!python
#cython: language_level=3

from . cimport cparser
# noinspection PyUnresolvedReferences
from cpython cimport Py_buffer
# noinspection PyUnresolvedReferences
from ..headers.headers cimport Headers

__all__ = ('HttpResponseParser', )


cdef class HttpResponseParser:
    cdef:
        cparser.http_parser_settings* csettings
        cparser.http_parser* cparser

        bytes current_header_name
        bytes current_header_value
        object protocol

        _proto_on_url, _proto_on_status, _proto_on_body, \
        _proto_on_header, _proto_on_headers_complete, \
        _proto_on_message_complete, _proto_on_chunk_header, \
        _proto_on_chunk_complete, _proto_on_message_begin

        object last_error
        Headers headers
        bytes current_status

        Py_buffer py_buf

    cdef _maybe_call_on_header(self)
    cdef on_header_field(self, bytes field)
    cdef on_header_value(self, bytes val)
    cdef on_headers_complete(self)
    cdef on_chunk_header(self)
    cdef on_chunk_complete(self)
    cpdef feed(self, bytes data)
