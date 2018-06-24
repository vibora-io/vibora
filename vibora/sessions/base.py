from ..utils import json


class SessionEngine:

    def __init__(self, cookie_name: str=None):
        self.cookie_name = cookie_name or 'SESSION_ID'

    async def load(self, request):
        raise NotImplementedError

    async def save(self, request, response):
        raise NotImplementedError

    async def clean_up(self):
        pass


class Session:
    __slots__ = ('values', 'pending_flush', 'uuid')

    def __init__(self, values: dict = None, pending_flush: bool=False, unique_id: str=None):
        self.uuid = unique_id
        self.values = values or {}
        self.pending_flush = pending_flush

    def __setitem__(self, key, value):
        self.values[key] = value
        self.pending_flush = True

    def __getitem__(self, item):
        return self.values[item]

    def get(self, item, default=None):
        try:
            return self.values[item]
        except KeyError:
            return default

    def __delitem__(self, key):
        del self.values[key]
        self.pending_flush = True

    def dump(self):
        return self.values

    def dumps(self):
        return json.dumps(self.values)

    def load(self, values: dict):
        self.values.update(values)
        self.pending_flush = True

    def clear(self):
        self.values.clear()
        self.pending_flush = True

    def __contains__(self, item):
        return item in self.values
