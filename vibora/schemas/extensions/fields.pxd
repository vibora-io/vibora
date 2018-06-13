

cdef class Field:
    cdef:
        readonly list validators
        public bint strict
        public bint is_async
        public str load_from
        public str load_into
        object default
        public bint required
        bint default_callable


    cdef load(self, value)
    cdef sync_pipeline(self, object value, dict context)
    cdef _call_sync_validators(self, object value, dict context)


cdef class Integer(Field):
    pass


cdef class Number(Field):
    pass


cdef class String(Field):
    pass


cdef class List(Field):
    pass


cdef class Nested(Field):
    pass