### Routing

Routing is the core of any web framework because it allows the user
to map URL endpoints to functions.

```py
@app.route("/home", methods=['GET'])
async def home():
    return Response(b'123')
```

> In this example you are mapping every HTTP request with a `GET`
method and a path equals to `/home` to `async def home()`.

### Request Parameters

Often parts of an URL have a special meaning, for example,
specifying which product should be displayed.

```py
@app.route('/product/<product_id>')
async def show_product(product_id: int):
    return Response(f'Chosen product: {product_id}'.encode())
```

Not usually you'll need something more sophisticated.
Vibora allows regular expressions as route patterns.

```py
import re

@app.route(re.compile('/product/(?P<product_id>[0-9]+)'))
async def show_product(product_id: int):
    return Response(f'Chosen product: {product_id}'.encode())
```

### Virtual Hosts

Maybe you have different domains and you want to host them all
with a single Vibora application. So `http://docs.vibora.io/` and
`http://vibora.io/` would hit the same application but return different
responses based on the `HTTP host header`. Vibora makes it very easy
thanks to the `hosts` attribute.

```py
@app.route('/', hosts=['docs.vibora.io'])
async def docs():
    return Response(b'Docs')

@app.route('/', hosts=['vibora.io'])
async def home():
    return Response(b'Home')
```

To avoid repeating the `hosts` attribute for every route,
you can group routes using a Blueprint.

```py
from vibora.blueprints import Blueprint
from vibora.responses import Response


docs = Blueprint(hosts=['docs.vibora.io'])
main = Blueprint(hosts=['vibora.io'])


@docs.route('/')
async def docs():
    return Response(b'docs')


@main.route('/')
async def home():
    return Response(b'main')
```

### Router Strategies

A common source of headaches in URL routing are ending slashes.

Let's take the path `/home` and `/home/` for example.

In a web environment these are two completely different paths,
it's up to the server to interpret those as the same or not.

Vibora has three different strategies to deal with this problem:

    1. **Strict**. Does nothing. If you map your endpoints ending with
    slashes then if you try to access `/home` instead of `/home/`
    you'll get a 404 response.


    2. **Redirect (Default)**. If you map your route as `/home` then
    Vibora will return a 302 response if someone tries to access `/home/`
    and vice-versa.


    3. **Clone**. This one is similar to redirect but instead of a 302 it'll
    return the same response for both routes.

Configuration example:

```py
from vibora import Vibora
from vibora.router import RouterStrategy

app = Vibora(router_strategy=RouterStrategy.STRICT)
```

### Caching

Caching can be a tremendous ally when handling performance issues.
Imagine an API that does a read-only query being hit by 10k requests/sec,
this means that you are stressing your database at 10k queries/sec.

If you start caching the response for at least one second
you drop from 10k queries/sec to 1 query per second.
That's a huge improvement with almost no effort.

Vibora has some internal optimizations to speed-up cached APIs
so instead of handling it all by ourselves, you should use the `CacheEngine`.

```py
from vibora import Vibora, Response, Request
from vibora.cache import CacheEngine

app = Vibora()


class YourCacheEngine(CacheEngine):
    async def get(self, request: Request):
        return self.cache.get(request.url)

    async def store(self, request: Request, response):
        self.cache[request.url] = response


@app.route('/', cache=YourCacheEngine(skip_hooks=True))
def home():
    return Response(b'Hello World')
```

> Notice the "skip_hooks" parameter which makes cached responses to
  skip any listeners/hooks. Sometimes this is useful, often not,
  use wisely.

### Static Files

Vibora is fast enough to host static files and it tries hard to implement
the same features as some battle proven solutions like Nginx.

By default Vibora will seek for a directory called "static"
in the same parent directory related to the file that
created Vibora app instance.

You can configure the `StaticHandler` as bellow:

> All parameters are optional.

```py
from vibora.static import StaticHandler

app = Vibora(
    static=StaticHandler(
        paths=['/your_static_dir', '/second_static_dir'],
        host='static.vibora.io',
        url_prefix='/static',
        max_cache_size=1 * 1024 * 1024
    )
)
```

> **Host** parameter can be used to only serve static files when
  the Host header matches this specific host.

> **max_cache_size** specifies the amount of memory that Vibora
may invest into optimizations.
