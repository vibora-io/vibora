#!python
#cython: language_level=3

from __future__ import print_function
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from cpython cimport PyObject_GetBuffer, PyBuffer_Release, PyBUF_SIMPLE, \
                     Py_buffer, PyBytes_AsString

from .errors import (HttpParserError,
                     HttpParserCallbackError,
                     HttpParserInvalidStatusError,
                     HttpParserInvalidMethodError,
                     HttpParserInvalidURLError,
                     HttpParserUpgrade)
cimport cython
from ..parsers cimport cparser
from ..protocol.cprotocol cimport Connection
from ..headers.headers cimport Headers

__all__ = ('parse_url', 'HttpParser')


cdef class HttpParser:
    cdef:
        cparser.http_parser* _cparser
        cparser.http_parser_settings* _csettings

        bytes _current_header_name
        bytes _current_header_value
        Connection protocol

        _proto_on_url, _proto_on_status, _proto_on_body, \
        _proto_on_header, _proto_on_headers_complete, \
        _proto_on_message_complete, _proto_on_chunk_header, \
        _proto_on_chunk_complete, _proto_on_message_begin

        object _last_error
        list _headers
        bytes _url

        Py_buffer py_buf

        # Security Limits
        int headers_limit
        int body_limit
        int max_headers_size
        int max_body_size
        int current_headers_size
        int current_body_size

    cdef _maybe_call_on_header(self)
    cdef _on_header_field(self, bytes field)
    cdef _on_header_value(self, bytes val)
    cdef _on_headers_complete(self)
    cdef _on_chunk_header(self)
    cdef _on_chunk_complete(self)
    cdef int feed_data(self, bytes data) except -1
