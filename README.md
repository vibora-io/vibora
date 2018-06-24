<p align="center">
  <a href="https://vibora.io"><img src="https://raw.githubusercontent.com/vibora-io/vibora/master/docs/logo.png"></a>
  <a href="https://circleci.com/gh/vibora-io/vibora"><img src="https://circleci.com/gh/vibora-io/vibora.svg?style=shield"></a>
</p>

-----------------------------------------------------------
> [Vibora](https://vibora.io) is a **fast, asynchronous and efficient** Python 3.6+ http client/server framework. (Alpha stage)

> Before you ask, Vibora means Viper in Portuguese :)

> **Disclaimer: Still at an early stage of development. Rapidly evolving APIs.**


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
[Check it out at Vibora docs website](https://docs.vibora.io/docs).

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
