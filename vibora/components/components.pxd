

cdef class ComponentsEngine:

    cdef dict index
    cdef dict ephemeral_index
    cdef object request_class
    cdef void reset(self)

    cpdef ComponentsEngine clone(self)
