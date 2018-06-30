#!python
#cython: language_level=3, boundscheck=False, wraparound=False
from time import time
from asyncio import Transport, Event, sleep, Task, CancelledError
from ..parsers.errors import HttpParserError

############################################
# C IMPORTS
# noinspection PyUnresolvedReferences
from ..cache.cache cimport CacheEngine
# noinspection PyUnresolvedReferences
from ..request.request cimport Request, Stream
# noinspection PyUnresolvedReferences
from ..parsers.parser cimport HttpParser
# noinspection PyUnresolvedReferences
from ..headers.headers cimport Headers
# noinspection PyUnresolvedReferences
from ..router.router import Route
# noinspection PyUnresolvedReferences
from ..responses.responses cimport Response, CachedResponse
# noinspection PyUnresolvedReferences
from .cwebsocket cimport WebsocketConnection
############################################

cdef int current_time = time()

DEF PENDING_STATUS = 1
DEF RECEIVING_STATUS = 2
DEF PROCESSING_STATUS = 3
DEF EVENTS_BEFORE_ENDPOINT = 3
DEF EVENTS_AFTER_ENDPOINT  = 4
DEF EVENTS_AFTER_RESPONSE_SENT  = 5


cdef class Connection:

    def __init__(self, app: object, loop: object, worker):

        ############################
        ## Constants
        self.app = app
        self.loop = loop
        self.protocol = b'1.1'
        self.components = app.components.clone()
        self.components.index[Connection] = self
        self.parser = HttpParser(self, app.server_limits.max_headers_size, app.limits.max_body_size)
        self.stream = Stream(self)

        ###########################
        ## State Machine
        self.transport = None  # type: Transport
        self.status = PENDING_STATUS
        self.writable = True
        self.readable = True
        self.write_permission = Event()
        self.current_task = None
        self.timeout_task = None
        self.closed = False
        self.last_task_time = time()
        self._stopped = False

        ##################################
        ## Early bindings for performance.
        self.keep_alive = app.server_limits.keep_alive_timeout > 0
        self.request_class = self.app.request_class
        self.router = self.app.router
        self.log = self.app.log_handler
        self.queue = self.stream.queue
        self.write_buffer = app.server_limits.write_buffer

        ##################################
        ## Caching the existence of hooks.
        self.before_endpoint_hooks = self.app.exists_hook(EVENTS_BEFORE_ENDPOINT)
        self.after_endpoint_hooks = self.app.exists_hook(EVENTS_AFTER_ENDPOINT)
        self.after_send_response_hooks = self.app.exists_hook(EVENTS_AFTER_RESPONSE_SENT)
        self.any_hooks = self.before_endpoint_hooks or self.after_endpoint_hooks or self.after_send_response_hooks

    cdef void handle_upgrade(self):
        """
        
        :return: 
        """
        websocket = self.route.websocket_handler(self.transport)
        self.loop.create_task(websocket.on_connect())
        self.transport.set_protocol(
            WebsocketConnection(
                app=self.app,
                handler=websocket,
                loop=self.loop,
                transport=self.transport
            )
        )

    cpdef void after_response(self, Response response):
        """
        Handle network flow after a response is sent. Must be called after each response.
        :return: None.
        """
        self.status = PENDING_STATUS
        if not self.keep_alive:
            self.close()
        elif self._stopped:
            self.loop.create_task(self.scheduled_close(timeout=30))
        else:
            self.resume_reading()

        # Resetting the stream status.
        self.stream.clear()

        # Handling timeouts.
        if self.timeout_task:
            self.timeout_task.cancel()
            self.timeout_task = None

        # Components like request and route objects are tied to the request flow so
        # after the response they are removed from this component engine.
        self.components.reset()

    async def write(self, bytes data):
        """

        :param data:
        :return:
        """
        # The data is already at our hand, already in-memory, there is no reason
        # to wait before adding to the buffer.
        self.transport.write(data)

        # Paused writes means the client is not consuming the content so we should wait
        # before proceeding to prevent the buffer from growing beyond the limits.
        if not self.writable:
            await self.write_permission.wait()

    async def handle_request(self, Request request, Route route):
        """

        :return:
        """
        cdef Response response = None
        cdef CacheEngine cache_engine = route.cache

        try:
            if not self.any_hooks and not cache_engine:
                response = await route.call_handler(request, self.components)
                return response.send(self)

            # Fast lane for async requests.
            if cache_engine and cache_engine.skip_hooks and cache_engine.is_async:
                response = await cache_engine.get(request)
                if response:
                    response.send(self)
                    return

            # Before endpoint hooks can halt the request (and prevent more hooks from being called)
            if self.before_endpoint_hooks:
                response = await self.app.call_hooks(EVENTS_BEFORE_ENDPOINT, self.components, route=route)
                if response:
                    response.send(self)
                    return

            # Trying to fetch the response from route cache
            if cache_engine:
                if cache_engine.is_async:
                    response = await cache_engine.get(request)
                else:
                    response = cache_engine.get(request)

            # In case the response is not cached, let's finally call the user route.
            if not response:
                response = await route.call_handler(request, self.components)

                # Updating the cache.
                if cache_engine:
                    maybe_coroutine = cache_engine.store(request, response)
                    if cache_engine.is_async:
                        await maybe_coroutine

            if self.after_endpoint_hooks:
                self.components.ephemeral_index[response.__class__] = response
                new_response = await self.app.call_hooks(EVENTS_AFTER_ENDPOINT, self.components, route=route)
                if new_response:
                    response = new_response
                    self.components.ephemeral_index[response.__class__] = response

            response.send(self)

            if self.after_send_response_hooks:
                await self.app.call_hooks(EVENTS_AFTER_RESPONSE_SENT, self.components, route=route)
        except CancelledError as error:
            # In case the task is cancelled (probably a timeout)
            # we do nothing.
            pass
        except Exception as error:
            self.components.ephemeral_index[type(error)] = error
            task = self.handle_exception(error, self.components, route=route)
            self.loop.create_task(task)

    #######################################################################
    # HTTP PARSER CALLBACKS
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    cdef void on_headers_complete(self, Headers headers, bytes url, bytes method, bint upgrade):
        """

        :param headers:
        :param url:
        :param method:
        :param upgrade:
        :return:
        """
        cdef Response response
        cdef CacheEngine cache_engine
        cdef dict ephemeral_components = self.components.ephemeral_index

        # Building the Route & Request objects.
        cdef Request request = self.request_class(url, headers, method, self.stream, self)
        cdef Route route = self.router.get_route(request)

        # Registering them as components to later use.
        ephemeral_components[self.request_class] = request
        ephemeral_components[Route] = route

        # # Updating HTTP parser security limits.
        limits = route.limits
        if limits:
            self.parser.max_body_size = limits.max_body_size

        # Checking for protocol upgrades (I.e: Websocket connections, HTTP2)
        if not upgrade:

            # Updating last request time.
            self.last_task_time = current_time

            # Optimized path that skips the creation of a async task because
            # the response is already in memory so we can do some neat optimizations.
            cache_engine = route.cache
            if cache_engine and cache_engine.skip_hooks is True and not cache_engine.is_async:
                response = cache_engine.get(request)
                if response:
                    response.send(self)
                    return

            self.current_task = Task(self.handle_request(request, route), loop=self.loop)
            self.current_task.components = self.components

            # Creating the timeout watcher.
            self.timeout_task = self.loop.call_later(route.limits.timeout, self.cancel_request)
        else:
            self.handle_upgrade()

    cdef void on_body(self, bytes body):
        """
        
        :param body: 
        :return: 
        """
        self.queue.put(body)

        # Stop reading from the socket while processing the response.
        # We only start reading again if the user explicitly tries to consume the stream.
        # This helps to prevent DoS and give the user a chance to choose what's
        # best for him in this situation.
        self.pause_reading()

    cdef void on_message_complete(self):
        """
        
        :return: 
        """
        # This is a signal to show the Stream consumer that the stream ended.
        self.queue.end()

        # Updating the status so the watcher thread can monitor this process and
        # kill the process itself if it gets stuck.
        self.status = PROCESSING_STATUS

    #######################################################################
    # Network Flow Callbacks
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    cpdef void connection_made(self, transport: Transport):
        """
        
        :param transport: 
        :return: 
        """
        transport.set_write_buffer_limits(self.write_buffer)
        self.transport = transport # type: Transport
        self.app.connections.add(self)

    cpdef void data_received(self, bytes data):
        """
        
        :param data: 
        :return: 
        """
        self.status = RECEIVING_STATUS
        try:
            self.parser.feed_data(data)
        except HttpParserError as error:
            self.pause_reading()
            self.components.ephemeral_index[type(error)] = error
            task = self.handle_exception(error, self.components)
            self.loop.create_task(task)
            # self.close()

    cpdef void connection_lost(self, exc):
        """
        
        :param exc: 
        :return: 
        """
        self.close()

    cpdef void pause_reading(self):
        """
        
        :return: 
        """
        if self.readable:
            self.transport.pause_reading()
            self.readable = False

    cpdef void resume_reading(self):
        """
        
        :return: 
        """
        if not self.readable:
            self.transport.resume_reading()
            self.readable = True

    cpdef void pause_writing(self):
        """
        
        :return: 
        """
        self.writable = False

    cpdef void resume_writing(self):
        """
         
        :return: 
        """
        if not self.writable:
            self.writable = True
            self.write_permission.set()

    cpdef void close(self):
        """
        
        :return: 
        """
        if not self.closed:
            self.transport.close()
            self.app.connections.discard(self)
            self.closed = True

    cpdef void cancel_request(self):
        """

        :return:
        """
        self.current_task.cancel()
        error = TimeoutError()
        self.components.ephemeral_index[TimeoutError] = error
        task = self.handle_exception(error, self.components)
        self.loop.create_task(task)

    cpdef void stop(self):
        """
        
        :return: 
        """
        self._stopped = True
        if self.status == PENDING_STATUS:
            self.close()

    cpdef bint is_closed(self):
        """
        
        :return: 
        """
        return self.closed

    cpdef int get_status(self):
        """
        
        :return: 
        """
        return self.status

    cpdef int get_last_task_time(self):
        """
        
        :return: 
        """
        return self.last_task_time

    def eof_received(self, *args):
        """

        :param args:
        :return:
        """
        pass

    cpdef str client_ip(self):
        """
        
        :return: 
        """
        return self.transport.get_extra_info('peername')[0]

    async def scheduled_close(self, int timeout=30):
        """

        :param timeout:
        :return:
        """
        buffer_size = self.transport.get_write_buffer_size
        while buffer_size() > 0:
            await sleep(0.5)
        self.close()

    async def handle_exception(self, object exception, object components, Route route = None):
        """

        :param exception:
        :param components:
        :param route:
        :return:
        """
        cdef Response response = None
        if route:
            response = await route.parent.process_exception(exception, components)
        if response is None:
            response = await self.app.process_exception(exception, components)
        response.send(self)


def update_current_time() -> None:
    """
    current_time cannot be access from outside this module so we call this function periodically to update this.
    :return: None
    """
    global current_time
    current_time = time()
