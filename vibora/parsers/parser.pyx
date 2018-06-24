#!python
#cython: language_level=3
########################################################################
########################################################################
# Portions Copyright (c) 2015-present MagicStack Inc.
# https://github.com/MagicStack/httptools
########################################################################
########################################################################
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from cpython cimport PyObject_GetBuffer, PyBuffer_Release, PyBUF_SIMPLE, Py_buffer
from .errors import HttpParserError, HttpParserCallbackError, HttpParserInvalidStatusError, \
    HttpParserInvalidMethodError, HttpParserInvalidURLError, BodyLimitError, HeadersLimitError
cimport cython
from . cimport cparser
from ..protocol.cprotocol cimport Connection
from ..headers.headers cimport Headers

__all__ = ('parse_url', 'HttpParser', 'HttpResponseParser')

cdef class HttpParser:
    def __init__(self, Connection protocol, max_headers_size: int, max_body_size: int):

        self.protocol = protocol

        # RAW C HttpParser
        self._cparser = <cparser.http_parser*> PyMem_Malloc(sizeof(cparser.http_parser))
        if self._cparser is NULL:
            raise MemoryError()

        # Creating callback Settings
        self._csettings = <cparser.http_parser_settings*> PyMem_Malloc(sizeof(cparser.http_parser_settings))
        if self._csettings is NULL:
            raise MemoryError()

        # Initializing the parser.
        cparser.http_parser_init(self._cparser, cparser.HTTP_REQUEST)
        self._cparser.data = <void*> self

        # Binding callback settings.
        cparser.http_parser_settings_init(self._csettings)

        # Headers callbacks.
        self._current_header_name = None
        self._current_header_value = None
        self._csettings.on_header_field = cb_on_header_field
        self._csettings.on_header_value = cb_on_header_value
        self._csettings.on_headers_complete = cb_on_headers_complete

        # Chunked Headers
        self._csettings.on_chunk_header = cb_on_chunk_header
        self._csettings.on_chunk_complete = cb_on_chunk_complete

        # On Body Callback
        self._proto_on_body = protocol.on_body
        self._csettings.on_body = cb_on_body

        # On Body Fully Loaded
        self._csettings.on_message_complete = cb_on_message_complete

        # On parsed URL
        self._proto_on_url = getattr(protocol, 'on_url', None)
        self._csettings.on_url = cb_on_url

        self._headers = []
        self._last_error = None

        # Security Limits
        self.headers_limit = max_headers_size
        self.body_limit = max_body_size
        self.max_headers_size = max_headers_size
        self.max_body_size = max_body_size
        self.current_headers_size = 0
        self.current_body_size = 0

    def __dealloc__(self):
        PyMem_Free(self._cparser)
        PyMem_Free(self._csettings)

    cdef _maybe_call_on_header(self):
        if self._current_header_name:
            # Storing current headers
            self._headers.append((self._current_header_name, self._current_header_value))

            # Reset State.
            self._current_header_name = self._current_header_value = None

    cdef _on_header_field(self, bytes field):
        self._maybe_call_on_header()
        self._current_header_name = field

    cdef _on_header_value(self, bytes val):
        if not self._current_header_value:
            self._current_header_value = val
        else:
            # This is unlikely, as mostly HTTP headers are one-line
            self._current_header_value += val

    cdef _on_headers_complete(self):
        self._maybe_call_on_header()
        cdef cparser.http_parser*parser = self._cparser
        method = cparser.http_method_str(<cparser.http_method> parser.method)
        self.protocol.on_headers_complete(Headers(self._headers), self._url, method, parser.upgrade)
        self._headers = []

    cdef _on_chunk_header(self):
        if (self._current_header_value is not None or
                self._current_header_name is not None):
            raise HttpParserError('invalid headers state')

    cdef _on_chunk_complete(self):
        self._maybe_call_on_header()

    ### Public API ###

    def get_http_version(self):
        cdef cparser.http_parser*parser = self._cparser
        return '{}.{}'.format(parser.http_major, parser.http_minor)

    def should_keep_alive(self):
        return bool(cparser.http_should_keep_alive(self._cparser))

    cdef int feed_data(self, bytes data) except -1:

        cdef size_t data_length
        cdef size_t consumed_bytes

        # Getting the buffer size.
        PyObject_GetBuffer(data, &self.py_buf, PyBUF_SIMPLE)
        data_length = <size_t> self.py_buf.len

        # Calling the C http parser.
        consumed_bytes = cparser.http_parser_execute(self._cparser,
                                                     self._csettings, <char*> self.py_buf.buf, data_length)

        # Releasing the buffer.
        PyBuffer_Release(&self.py_buf)

        if self._cparser.http_errno != cparser.HPE_OK:
            ex = parser_error_from_errno(
                <cparser.http_errno> self._cparser.http_errno)
            if isinstance(ex, HttpParserCallbackError):
                if self._last_error is not None:
                    ex = self._last_error
                    self._last_error = None
            raise ex

        if consumed_bytes != data_length:
            raise HttpParserError("HTTP parser din't consumed all the bytes.")


cdef int cb_on_url(cparser.http_parser*parser, const char *at, size_t length) except -1:
    cdef HttpParser wrapper = <HttpParser> parser.data

    # Dealing with max headers size.
    wrapper.current_headers_size += length
    if wrapper.current_headers_size > wrapper.max_headers_size > 0:
        wrapper._last_error = HeadersLimitError()
        return -1

    try:
        wrapper._url = at[:length]
    except BaseException as ex:
        wrapper._last_error = ex
        return -1
    else:
        return 0


cdef int cb_on_header_field(cparser.http_parser*parser, const char *at, size_t length) except -1:
    cdef HttpParser wrapper = <HttpParser> parser.data

    # Dealing with max headers size.
    wrapper.current_headers_size += length
    if wrapper.current_headers_size > wrapper.max_headers_size > 0:
        wrapper._last_error = HeadersLimitError()
        return -1

    try:
        wrapper._on_header_field(at[:length])
    except BaseException as ex:
        wrapper._last_error = ex
        return -1
    else:
        return 0

cdef int cb_on_header_value(cparser.http_parser*parser,
                            const char *at, size_t length) except -1:
    cdef HttpParser wrapper = <HttpParser> parser.data

    # Dealing with max headers size.
    wrapper.current_headers_size += length
    if wrapper.current_headers_size > wrapper.max_headers_size > 0:
        wrapper._last_error = HeadersLimitError()
        return -1

    try:
        wrapper._on_header_value(at[:length])
    except BaseException as ex:
        wrapper._last_error = ex
        return -1
    else:
        return 0

cdef int cb_on_headers_complete(cparser.http_parser*parser) except -1:
    cdef HttpParser pyparser = <HttpParser> parser.data
    try:
        pyparser._on_headers_complete()
    except BaseException as ex:
        pyparser._last_error = ex
        return -1
    else:
        if pyparser._cparser.upgrade:
            return 1
        else:
            return 0

cdef int cb_on_body(cparser.http_parser*parser,
                    const char *at, size_t length) except -1:
    cdef HttpParser wrapper = <HttpParser> parser.data
    if wrapper.max_body_size > 0:
        wrapper.current_body_size += length
        if wrapper.current_body_size > wrapper.max_body_size:
            wrapper._last_error = BodyLimitError()
            return -1
    try:
        wrapper.protocol.on_body(at[:length])
    except BaseException as ex:
        wrapper._last_error = ex
        return -1
    else:
        return 0

cdef int cb_on_message_complete(cparser.http_parser*parser) except -1:
    cdef HttpParser wrapper = <HttpParser> parser.data
    # Resetting security limits.
    wrapper.current_body_size = 0
    wrapper.current_headers_size = 0
    wrapper.max_body_size = wrapper.body_limit
    wrapper.max_headers_size = wrapper.headers_limit
    try:
        wrapper.protocol.on_message_complete()
    except BaseException as ex:
        wrapper._last_error = ex
        return -1
    else:
        return 0

cdef int cb_on_chunk_header(cparser.http_parser*parser) except -1:
    cdef HttpParser pyparser = <HttpParser> parser.data
    try:
        pyparser._on_chunk_header()
    except BaseException as ex:
        pyparser._last_error = ex
        return -1
    else:
        return 0

cdef int cb_on_chunk_complete(cparser.http_parser*parser) except -1:
    cdef HttpParser pyparser = <HttpParser> parser.data
    try:
        pyparser._on_chunk_complete()
    except BaseException as ex:
        pyparser._last_error = ex
        return -1
    else:
        return 0

cdef parser_error_from_errno(cparser.http_errno errno):
    cdef bytes desc = cparser.http_errno_description(errno)

    if errno in (cparser.HPE_CB_message_begin,
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

    elif errno == cparser.HPE_INVALID_STATUS:
        cls = HttpParserInvalidStatusError

    elif errno == cparser.HPE_INVALID_METHOD:
        cls = HttpParserInvalidMethodError

    elif errno == cparser.HPE_INVALID_URL:
        cls = HttpParserInvalidURLError

    else:
        cls = HttpParserError

    return cls(desc.decode('latin-1'))

@cython.freelist(250)
cdef class URL:
    cdef readonly str schema
    cdef readonly str host
    cdef readonly int port
    cdef readonly str path
    cdef readonly str query
    cdef readonly str fragment
    cdef readonly str userinfo
    cdef readonly str netloc

    def __cinit__(self, bytes schema, bytes host, object port, bytes path,
                  bytes query, bytes fragment, bytes userinfo):

        self.schema = schema.decode('utf-8')
        self.host = host.decode('utf-8')
        if port and port != 0:
            self.port = port
        else:
            if schema == b'https':
                self.port = 443
            else:
                self.port = 80
        self.path = path.decode('utf-8') if path else ''
        self.query = query.decode('utf-8') if query else None
        self.fragment = fragment.decode('utf-8') if fragment else None
        self.userinfo = userinfo.decode('utf-8') if userinfo else None
        self.netloc = self.schema + '://' + self.host + ':' + str(self.port)

    @property
    def raw(self):
        return self.netloc + (self.path or '') + (self.query or '') + (self.fragment or '')

    def __repr__(self):
        return ('<URL schema: {!r}, host: {!r}, port: {!r}, path: {!r}, '
                'query: {!r}, fragment: {!r}, userinfo: {!r}>'
                .format(self.schema, self.host, self.port, self.path,
                        self.query, self.fragment, self.userinfo))

def parse_url(url):
    cdef:
        Py_buffer py_buf
        char*buf_data
        cparser.http_parser_url*parsed
        int res
        bytes schema = None
        bytes host = None
        object port = None
        bytes path = None
        bytes query = None
        bytes fragment = None
        bytes userinfo = None
        object result = None
        int off
        int ln

    parsed = <cparser.http_parser_url*> \
        PyMem_Malloc(sizeof(cparser.http_parser_url))
    cparser.http_parser_url_init(parsed)

    PyObject_GetBuffer(url, &py_buf, PyBUF_SIMPLE)
    try:
        buf_data = <char*> py_buf.buf
        res = cparser.http_parser_parse_url(buf_data, py_buf.len, 0, parsed)

        if res == 0:
            if parsed.field_set & (1 << cparser.UF_SCHEMA):
                off = parsed.field_data[<int> cparser.UF_SCHEMA].off
                ln = parsed.field_data[<int> cparser.UF_SCHEMA].len
                schema = buf_data[off:off + ln]

            if parsed.field_set & (1 << cparser.UF_HOST):
                off = parsed.field_data[<int> cparser.UF_HOST].off
                ln = parsed.field_data[<int> cparser.UF_HOST].len
                host = buf_data[off:off + ln]

            if parsed.field_set & (1 << cparser.UF_PORT):
                port = parsed.port

            if parsed.field_set & (1 << cparser.UF_PATH):
                off = parsed.field_data[<int> cparser.UF_PATH].off
                ln = parsed.field_data[<int> cparser.UF_PATH].len
                path = buf_data[off:off + ln]

            if parsed.field_set & (1 << cparser.UF_QUERY):
                off = parsed.field_data[<int> cparser.UF_QUERY].off
                ln = parsed.field_data[<int> cparser.UF_QUERY].len
                query = buf_data[off:off + ln]

            if parsed.field_set & (1 << cparser.UF_FRAGMENT):
                off = parsed.field_data[<int> cparser.UF_FRAGMENT].off
                ln = parsed.field_data[<int> cparser.UF_FRAGMENT].len
                fragment = buf_data[off:off + ln]

            if parsed.field_set & (1 << cparser.UF_USERINFO):
                off = parsed.field_data[<int> cparser.UF_USERINFO].off
                ln = parsed.field_data[<int> cparser.UF_USERINFO].len
                userinfo = buf_data[off:off + ln]

            return URL(schema, host, port, path, query, fragment, userinfo)
        else:
            raise HttpParserInvalidURLError("invalid url {!r}".format(url))
    finally:
        PyBuffer_Release(&py_buf)
        PyMem_Free(parsed)
