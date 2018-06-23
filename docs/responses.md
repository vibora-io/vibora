### Responses

Each route must return a Response object,
the protocol will use these objects to encode the HTTP response and
send through the socket.

There are many different response types but they all inherit from
the base Response class.

Bellow there are the most important ones:

### JSON Response

Automatically dumps Python objects and adds the correct headers to match the JSON format.

```py
from vibora import Vibora
from vibora.responses import JsonResponse

app = Vibora()

@app.route('/')
async def home():
    return JsonResponse({'hello': 'world})
```

### Streaming Response

Whenever you don't have the response already completely ready,
be it because you don't want to waste memory by buffering,
be it because you want the client to start receiving the response as soon as possible,
a StreamingResponse will be more appropriate.

**A StreamingResponse receives a coroutine that yield bytes.**

Differently from simple responses, streaming ones have more timeout options
because they are often long running tasks.
Usually a route timeout works until the client consumes the entire response
but with streaming responses this is not true.
After the route return a StreamingResponse two new timeouts options take its place.

> **complete_timeout: int**: How many seconds the client have to consume the **entire** response.
So if you set it to 30 seconds the client will have 30 seconds to consume the entire response,
in case not, the connection will be closed abruptly to avoid DOS attacks.
You may set it to zero and completely disable this timeout,
when chunk_timeout is properly configured this is a reasonable choice.

> **chunk_timeout: int**: How many seconds the client have to consume each response chunk.
Lets say your function produces 30 bytes per yield and the chunk_timeout is 10 seconds.
The client will have 10 seconds to consume the 30 bytes, in case not, the connection will be closed abruptly to avoid DOS attacks.

```py
import asyncio
from vibora import Vibora, StreamingResponse

app = Vibora()

@app.route('/')
async def home():
    async def stream_builder():
        for x in range(0, 5):
            yield str(x).encode()
            await asyncio.sleep(1)

    return StreamingResponse(
           stream_builder, chunk_timeout=10, complete_timeout=30
    )
```

### Response

A raw Response object would fit whenever you need a more
customized response.

```py
from vibora import Vibora, Response

app = Vibora()

@app.route('/')
async def home():
    return Response(b'Hello World', headers={'content-type': 'html'})
```
