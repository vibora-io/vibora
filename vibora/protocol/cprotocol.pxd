#!python
#cython: language_level=3, boundscheck=False, wraparound=False

###############################################
# C IMPORTS
# noinspection PyUnresolvedReferences
from ..parsers.parser cimport HttpParser
# noinspection PyUnresolvedReferences
from ..router.router cimport Router, Route
# noinspection PyUnresolvedReferences
from ..request.request cimport Request, Stream, StreamQueue
# noinspection PyUnresolvedReferences
from ..headers.headers cimport Headers
# noinspection PyUnresolvedReferences
from ..responses.responses cimport Response, CachedResponse
# noinspection PyUnresolvedReferences
from ..components.components cimport ComponentsEngine
###############################################

cdef class Connection:
    cdef:
        public object app
        int status
        bint keep_alive
        bint closed
        bint _stopped
        int write_buffer
        object worker
        public object loop
        public object transport
        public bytes protocol
        bint writable
        bint readable
        object write_permission
        HttpParser parser
        Router router
        object log
        Stream stream
        StreamQueue queue
        object current_task
        object timeout_task
        ComponentsEngine components
        int last_task_time

        # Caching the existence of hooks.
        bint before_endpoint_hooks
        bint after_endpoint_hooks
        bint after_send_response_hooks
        bint any_hooks

        object request_class
        object call_hooks

    # Asyncio Callbacks (Network Flow)
    cpdef void connection_made(self, transport)
    cpdef void data_received(self, bytes data)
    cpdef void connection_lost(self, exc)
    cpdef void pause_writing(self)
    cpdef void resume_writing(self)

    # Custom protocol methods.
    cdef void handle_upgrade(self)
    cpdef void after_response(self, Response response)
    cpdef void resume_reading(self)
    cpdef void pause_reading(self)
    cpdef void cancel_request(self)
    cpdef void close(self)
    cpdef void stop(self)
    cpdef bint is_closed(self)
    cpdef str client_ip(self)

    # Reaper related.
    cpdef int get_status(self)
    cpdef int get_last_task_time(self)

    # HTTP parser callbacks.
    cdef void on_headers_complete(self, Headers headers, bytes url, bytes method, bint upgrade)
    cdef void on_body(self, bytes body)
    cdef void on_message_complete(self)
