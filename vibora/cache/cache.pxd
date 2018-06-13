# cython: language_level=3, boundscheck=False, wraparound=False, annotation_typing=False

###################################################
# C IMPORTS
# noinspection PyUnresolvedReferences
from ..responses.responses cimport CachedResponse, Response
# noinspection PyUnresolvedReferences
from ..request.request cimport Request
###################################################


cdef class CacheEngine:
    cdef:
        bint skip_hooks
        bint is_async
        readonly dict cache

    cpdef get(self, Request request)
    cpdef store(self, Request request, response)



cdef class Static(CacheEngine):
    cpdef CachedResponse get(self, Request request)
