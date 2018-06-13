import re
import asyncio
from time import time


class RequestRate:

    __slots__ = ('_count', '_period', '_actual_usage', '_next_flush', 'pattern', 'optimistic')

    def __init__(self, count: int, period: int, pattern=None, optimistic: bool=False):
        """

        :param count: How many requests per period are allowed.
                      If the request rate is 10 requests per minute than count=10 with period=60.
        :param period: How many seconds between each cycle.
                       If the request rate is 10 requests per minute than the period is 60.
        :param pattern: A pattern to match against URLs and skip the rate for those that don't match the pattern.
        :param optimistic: Request rate is complicated because you never know how __exactly__ the server is measuring
        the throughput... By default Vibora is optimistic and assumes that the server will honor the rate/period
        accurately.
        """
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        else:
            self.pattern = pattern
        self.optimistic = optimistic
        self._count = count
        self._period = period
        self._actual_usage = 0
        self._next_flush = None

    async def notify(self):
        """

        :return:
        """
        now = time()
        if self._next_flush is None:
            self._next_flush = now + self._period
        elif now > self._next_flush:
            self._next_flush = now + self._period
            self._actual_usage = 0
        elif now < self._next_flush and self._actual_usage >= self._count:
            if self.optimistic:
                wait_time = (self._next_flush - now) or 0
            else:
                wait_time = self._period
            await asyncio.sleep(wait_time)
            self._actual_usage = 0
        self._actual_usage += 1
