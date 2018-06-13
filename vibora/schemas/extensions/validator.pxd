

cdef class Validator:
    cdef:
        object f
        bint is_async
        int params_count

    cdef validate(self, object value, dict context)
