import unittest
import asyncio
from inspect import iscoroutinefunction


def wrapper(f):
    def async_runner(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(f(*args, **kwargs))
        loop.run_until_complete(asyncio.sleep(0))
        loop.stop()
        loop.run_forever()

    return async_runner


class TestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for key, value in cls.__dict__.items():
            if key.startswith("test_") and iscoroutinefunction(value):
                setattr(cls, key, wrapper(value))

    @staticmethod
    async def _async_join(streaming):
        items = []
        async for chunk in streaming:
            items.append(chunk)
        try:
            if isinstance(items[0], bytes):
                return b"".join(items)
        except IndexError:
            return None
        return "".join(items)
