# noinspection PyUnresolvedReferences
from cpython cimport PyObject_GetBuffer, PyBuffer_Release, PyBUF_SIMPLE, \
                     Py_buffer, PyBytes_AsString
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from . cimport cparser
# noinspection PyUnresolvedReferences
from ..headers.headers cimport Headers
from .errors import (HttpParserError, HttpParserCallbackError, HttpParserInvalidStatusError,
                     HttpParserInvalidMethodError, HttpParserInvalidURLError)


__all__ = ('HttpResponseParser', )


# noinspection PyAttributeOutsideInit
cdef class HttpResponseParser:

    def __cinit__(self, object protocol):

        self.protocol = protocol

        # RAW C HttpParser
        self.cparser = <cparser.http_parser*> PyMem_Malloc(sizeof(cparser.http_parser))
        if self.cparser is NULL:
            raise MemoryError()

        # Creating callback Settings
        self.csettings = <cparser.http_parser_settings*> PyMem_Malloc(sizeof(cparser.http_parser_settings))
        if self.csettings is NULL:
            raise MemoryError()

        # Initializing the parser.
        cparser.http_parser_init(self.cparser, cparser.HTTP_RESPONSE)
        self.cparser.data = <void*>self

        # Binding callback settings.
        cparser.http_parser_settings_init(self.csettings)

        # Headers callbacks.
        self.current_header_name = None
        self.current_header_value = None
        self.csettings.on_header_field = cb_on_header_field
        self.csettings.on_header_value = cb_on_header_value
        self.csettings.on_headers_complete = cb_on_headers_complete

        # Chunked Headers
        self.csettings.on_chunk_header = cb_on_chunk_header
        self.csettings.on_chunk_complete = cb_on_chunk_complete

        # On Body Callback
        self._proto_on_body = protocol.on_body
        self.csettings.on_body = cb_on_body

        # On Body Fully Loaded
        self.csettings.on_message_complete = cb_on_message_complete

        self.headers = Headers()
        self.last_error = None
        self.current_status = b''

    def __dealloc__(self):
        PyMem_Free(self.cparser)
        PyMem_Free(self.csettings)

    cdef _maybe_call_on_header(self):
        if self.current_header_name is not None:
            # Storing current headers
            self.headers.raw.append((self.current_header_name, self.current_header_value))

            # Reset State.
            self.current_header_name = self.current_header_value = None

    cdef on_header_field(self, bytes field):
        self._maybe_call_on_header()
        self.current_header_name = field

    cdef on_header_value(self, bytes val):
        if self.current_header_value is None:
            self.current_header_value = val
        else:
            # This is unlikely, as mostly HTTP headers are one-line
            self.current_header_value += val

    cdef on_headers_complete(self):
        self._maybe_call_on_header()
        cdef cparser.http_parser* parser = self.cparser
        self.protocol.on_headers_complete(self.headers, self.cparser.status_code)
        self.headers = Headers()

    cdef on_chunk_header(self):
        if (self.current_header_value is not None or
            self.current_header_name is not None):
            raise HttpParserError('invalid headers state')

    cdef on_chunk_complete(self):
        self._maybe_call_on_header()
        self.protocol.chunk_complete()

    ### Public API ###

    def get_http_version(self):
        cdef cparser.http_parser* parser = self.cparser
        return '{}.{}'.format(parser.http_major, parser.http_minor)

    def should_keep_alive(self):
        return bool(cparser.http_should_keep_alive(self.cparser))

    cpdef feed(self, bytes data):

        cdef size_t data_length
        cdef size_t consumed_bytes

        # Getting the buffer size.
        PyObject_GetBuffer(data, &self.py_buf, PyBUF_SIMPLE)
        data_length = <size_t>self.py_buf.len

        # Calling the C http parser.
        consumed_bytes = cparser.http_parser_execute(self.cparser,
                                                     self.csettings, <char*>self.py_buf.buf, data_length)

        # Releasing the buffer.
        PyBuffer_Release(&self.py_buf)

        if self.cparser.http_errno != cparser.HPE_OK:
            ex =  parser_error_from_error_number(
                <cparser.http_errno> self.cparser.http_errno)
            if isinstance(ex, HttpParserCallbackError):
                if self.last_error is not None:
                    ex.__context__ = self.last_error
                    self.last_error = None
            raise ex

        if consumed_bytes != data_length:
            raise HttpParserError("HTTP parser din't consumed all the bytes.")


cdef int cb_on_header_field(cparser.http_parser* parser,
                            const char *at, size_t length) except -1:
    cdef HttpResponseParser p = <HttpResponseParser>parser.data
    try:
        p.on_header_field(at[:length])
    except BaseException as ex:
        p.last_error = ex
        return -1
    else:
        return 0


cdef int cb_on_header_value(cparser.http_parser* parser,
                            const char *at, size_t length) except -1:
    cdef HttpResponseParser p = <HttpResponseParser>parser.data
    try:
        p.on_header_value(at[:length])
    except BaseException as ex:
        p.last_error = ex
        return -1
    else:
        return 0


cdef int cb_on_headers_complete(cparser.http_parser* parser) except -1:
    cdef HttpResponseParser p = <HttpResponseParser>parser.data
    try:
        p.on_headers_complete()
    except BaseException as ex:
        p.last_error = ex
        return -1
    else:
        if p.cparser.upgrade:
            return 1
        else:
            return 0


cdef int cb_on_body(cparser.http_parser* parser,
                    const char *at, size_t length) except -1:
    cdef HttpResponseParser p = <HttpResponseParser>parser.data
    try:
        p.protocol.on_body(at[:length])
    except BaseException as ex:
        p.last_error = ex
        return -1
    else:
        return 0


cdef int cb_on_message_complete(cparser.http_parser* parser) except -1:
    cdef HttpResponseParser p = <HttpResponseParser>parser.data
    try:
        p.protocol.on_message_complete()
    except BaseException as ex:
        p.last_error = ex
        return -1
    else:
        return 0


cdef int cb_on_chunk_header(cparser.http_parser* parser) except -1:
    cdef HttpResponseParser p = <HttpResponseParser>parser.data
    try:
        p.on_chunk_header()
    except BaseException as ex:
        p.last_error = ex
        return -1
    else:
        return 0


cdef int cb_on_chunk_complete(cparser.http_parser* parser) except -1:
    cdef HttpResponseParser p = <HttpResponseParser>parser.data
    try:
        p.on_chunk_complete()
    except BaseException as ex:
        p.last_error = ex
        return -1
    else:
        return 0


cdef parser_error_from_error_number(cparser.http_errno error_number):
    cdef bytes desc = cparser.http_errno_description(error_number)

    if error_number in (cparser.HPE_CB_message_begin,
                        cparser.HPE_CB_url,
                        cparser.HPE_CB_header_field,
                        cparser.HPE_CB_header_value,
                        cparser.HPE_CB_headers_complete,
                        cparser.HPE_CB_body,
                        cparser.HPE_CB_message_complete,
                        cparser.HPE_CB_status,
                        cparser.HPE_CB_chunk_header,
                        cparser.HPE_CB_chunk_complete):
        cls = HttpParserCallbackError

    elif error_number == cparser.HPE_INVALID_STATUS:
        cls = HttpParserInvalidStatusError

    elif error_number == cparser.HPE_INVALID_METHOD:
        cls = HttpParserInvalidMethodError

    elif error_number == cparser.HPE_INVALID_URL:
        cls = HttpParserInvalidURLError

    else:
        cls = HttpParserError

    return cls(desc.decode('latin-1'))
