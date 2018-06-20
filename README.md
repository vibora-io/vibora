<p align="center">
  <a href="https://vibora.io"><img src="https://raw.githubusercontent.com/vibora-io/vibora/master/docs/logo.png"></a>
  <a href="https://circleci.com/gh/vibora-io/vibora"><img src="https://circleci.com/gh/vibora-io/vibora.svg?style=shield"></a>
</p>

-----------------------------------------------------------
> [Vibora](https://vibora.io) is a **sexy and fast** async Python 3.6+ http client/server framework. (Alpha stage)


Server Features
---------------
* Performance (https://github.com/vibora-io/benchmarks).
* Schemas Engine. (50x faster than marshmallow, Async Enabled)
* Nested Blueprints / Domain Based Routes / Components
* Connection Reaper / Self-Healing Workers
* Sessions Engine (easily extended to any backend)
* Streaming
* Websockets (under development)
* Caching tools
* Async Template Engine (hot-reloading, deep inheritance)
* Complete flow customization
* Static Files (Smart Cache, Range, LastModified, ETags)
* Complete Test Framework
* Type hints, type hints, type hints everywhere.


Client Features
---------------
* Streaming MultipartForms (Inspired by: https://github.com/requests/requests/issues/1584)
* Rate Limiting / Retries mechanisms
* Websockets (under development)
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
| Frameworks    | Requests/Sec  | Version |
| ------------- |:-------------:|:-------:|
| Tornado       | 14,249         | 5.02    |
| Django        | 22,727         | 2.0.6   |
| Flask         | 37,139         | 1.0.2   |
| Aiohttp       | 40,986         | 3.3.2   |
| Sanic         | 116,195        | 0.7.0   |
| Vibora        | 361,685        | 0.0.6   |
> More benchmarks and info at https://github.com/vibora-io/benchmarks
-----
Goals
-----
* **Be the fastest Python http client/server framework.**.
* Windows / Linux / MacOS.
* Enjoyable and up to date development features/trends.


Coming Soon
-----------
* Server Rate Limiting
* Cluster-Wide publish/subscribe events API.
* Auto Reloading
* JIT optimizer for user routes.
* HTTP2 Support
* Brotli Decompression
* OCSP SSL.
* Cython compiled templates.
* Async ORM
