

cdef class SmartFile:

    cdef:
        int in_memory_limit
        int pointer
        bint in_memory
        str filename
        str temp_dir
        object engine
        bytearray buffer

    cdef object consume(self)


cdef class MultipartParser:

    cdef:
        bytearray data
        bytes end_boundary
        bytes start_boundary
        dict values
        str temp_dir

        int in_memory_threshold
        int boundary_length
        int status

        SmartFile current_buffer

    cdef inline bytearray clean_value(self, bytearray v)
    cdef void parse_header(self, bytearray header)
    cdef dict consume(self)
