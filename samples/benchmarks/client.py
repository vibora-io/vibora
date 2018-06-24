import time
import uvloop
import requests
from vibora.client import Session, RetryStrategy
from vibora.client.limits import RequestRate
from aiohttp import ClientSession


max = 20
url = 'http://127.0.0.1:8000/'


async def vibora():
    t1 = time.time()
    with Session(keep_alive=True) as client:
        for _ in range(0, max):
            await client.get(url)
    print('Vibora: ', time.time() - t1)


async def aiohttp():
    t1 = time.time()
    async with ClientSession() as session:
        for _ in range(0, max):
            await session.get(url)
    print('Aiohttp: ', time.time() - t1)


async def requests2():
    t1 = time.time()
    with requests.Session() as session:
        for _ in range(0, max):
            session.get(url)
    print('Requests: ', time.time() - t1)


if __name__ == '__main__':
    loop = uvloop.new_event_loop()
    loop.run_until_complete(vibora())
    loop.run_until_complete(aiohttp())
    loop.run_until_complete(requests2())
