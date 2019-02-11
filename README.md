> **Warning: This project is being completely re-written. If you're curious about the progress, reach me on Slack.**

<p align="center">
  <a href="https://vibora.io"><img src="https://raw.githubusercontent.com/vibora-io/vibora/master/docs/logo.png"></a>
</p>

<p align="center">
  <a href="https://circleci.com/gh/vibora-io/vibora"><img src="https://circleci.com/gh/vibora-io/vibora.svg?style=shield"></a>
  <a href="https://github.com/vibora-io/vibora/blob/master/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://pypi.org/project/vibora/"><img alt="PyPI" src="https://img.shields.io/pypi/v/vibora.svg"></a>
  <a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
  <a target="_blank" href="https://join.slack.com/t/vibora-io/shared_invite/enQtNDAxMTQ4NDc5NDYzLTA2YTdmNmM0YmY4ZTY0Y2JjZjc0ODgwMmJjY2I0MmVkODFiYzc4YjM0NGMyOTkxMjZlNTliZDU1ZmFhYWZmNjU"><img alt="Join Slack" src="https://img.shields.io/badge/join-slack-E02462.svg"></a>
</p>

-----------------------------------------------------------
> [Vibora](https://vibora.io) is a **fast, asynchronous and elegant** Python 3.6+ http client/server framework. (Alpha stage)

> Before you ask, Vibora means Viper in Portuguese :)


Server Features
---------------
* Performance (https://github.com/vibora-io/benchmarks).
* Schemas Engine.
* Nested Blueprints / Domain Based Routes / Components
* Connection Reaper / Self-Healing Workers
* Sessions Engine
* Streaming
* Websockets
* Caching tools
* Async Template Engine (hot-reloading, deep inheritance)
* Complete flow customization
* Static Files (Smart Cache, Range, LastModified, ETags)
* Testing Framework
* Type hints, type hints, type hints everywhere.


Client Features
---------------
* Streaming MultipartForms (Inspired by: https://github.com/requests/requests/issues/1584)
* Rate Limiting / Retries mechanisms
* Websockets
* Keep-Alive & Connection Pooling
* Sessions with cookies persistence
* Basic/digest Authentication
* Transparent Content Decoding

Server Example
--------------
```python
from vibora import Vibora, Request
from vibora.responses import JsonResponse

app = Vibora()


@app.route('/')
async def home(request: Request):
    return JsonResponse({'hello': 'world'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
```

Client Example
--------------

```python
import asyncio
from vibora import client


async def hello_world():
    response = await client.get('https://google.com/')
    print(f'Content: {response.content}')
    print(f'Status code: {response.status_code}')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(hello_world())
```

Documentation
-------------
[Check it out at Vibora docs website](https://docs.vibora.io).

Performance (Infamous Hello World benchmark)
-----------
| Frameworks    | Requests/Sec  | Version  |
| ------------- |:-------------:|:--------:|
| Tornado       | 14,197         | 5.0.2   |
| Django        | 22,823         | 2.0.6   |
| Flask         | 37,487         | 1.0.2   |
| Aiohttp       | 61,252         | 3.3.2   |
| Sanic         | 119,764        | 0.7.0   |
| Vibora        | 368,456        | 0.0.6   |
> More benchmarks and info at https://github.com/vibora-io/benchmarks
----
Goals
-----
* **Be the fastest Python http client/server framework.**.
* Windows / Linux / MacOS.
* Enjoyable and up to date development features/trends.

Coming Soon
-----------
* Auto Reloading
* HTTP2 Support
* Brotli support (Server/Client)
* Cython compiled templates.
* Cython compiled user-routes.
