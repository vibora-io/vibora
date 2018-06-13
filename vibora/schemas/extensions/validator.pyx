from inspect import signature, iscoroutinefunction
from typing import Callable


cdef class Validator:

    def __init__(self, f: Callable=None):
        self.f = f
        self.is_async = iscoroutinefunction(f)
        try:
            self.params_count = len(signature(f).parameters) if f else 0
        except TypeError:
            self.params_count = len(signature(f.__func__).parameters) if f else 0

    cdef validate(self, value, dict context):
        if self.params_count == 1:
            return self.f(value)
        elif self.params_count == 2:
            return self.f(value, context)
