from inspect import iscoroutinefunction
from ..utils import json


class SessionEngine:
    def __init__(self):
        self.is_async = iscoroutinefunction(self.load)

    def load(self, request):
        raise NotImplementedError

    def save(self, request, response):
        raise NotImplementedError

    def clean_up(self):
        pass


class Session:
    __slots__ = ('values', 'needs_update', 'uuid')

    def __init__(self, values: dict = None, needs_update=False, unique_id=None):
        self.uuid = unique_id
        self.values = values or {}
        self.needs_update = needs_update

    def __setitem__(self, key, value):
        self.values[key] = value
        self.needs_update = True

    def __getitem__(self, item):
        return self.values[item]

    def get(self, item, default=None):
        try:
            return self.values[item]
        except KeyError:
            return default

    def __delitem__(self, key):
        del self.values[key]
        self.needs_update = True

    def dump(self):
        return self.values

    def dumps(self):
        return json.dumps(self.values)

    def load(self, values: dict):
        self.values.update(values)
        self.needs_update = True

    def clear(self):
        self.values.clear()
        self.needs_update = True

    def __contains__(self, item):
        return item in self.values
