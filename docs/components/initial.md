### Components

Every app has some hot objects that should be available almost
everywhere. Maybe they are database instances, maybe request objects.
Vibora call these objects `components`

For now you should pay close attention to the `Request` component:

This is the most important component and will be everywhere in your app.
It holds all information related to the current request and
also some useful references like the current application and route.

You can ask for components in your route by using type hints:

```py
from vibora import Vibora, Request, Response

app = Vibora()

@app.route('/')
async def home(request: Request):
    print(request.headers)
    return Response(b'123')
```

The request object has a special method that allows you to ask
for more components as you go.

```py
from vibora import Vibora, Request, Response
from vibora import Route

app = Vibora()

@app.route('/')
async def home(request: Request):
    current_route = request.get_component(Route)
    return Response(current_route.pattern.encode())
```

> By now you should have noticed that Vibora is smart enough
to know which components do you want in your routes so your routes
may not receive any parameters at all or ask as many components
do you wish.


### Adding custom components

Vibora was designed to avoid global magic (unlike Flask for example)
because it makes testing harder
and more prone to errors specially in async environments.

To help with this,
Vibora provides an API where you can register objects to later use.

This means they are correctly encapsulated into a single app object,
allowing many apps instances to work concurrently,
encouraging the use of type hints which brings many benefits
in the long-term and also make your routes much easier to test.

```py
from vibora import Vibora, Request, Response
from vibora import Route

# Config will be a new component.
class Config:
    def __init__(self):
        self.name = 'Vibora Component'

app = Vibora()

# Registering the config instance.
app.add_component(Config())

@app.route('/')
async def home(request: Request, config: Config):
    """
    Notice that if you specify a parameter of type "Config"
    Vibora will automatically provide the config instance registered previously.
    Instead of adding global variables you can now register new components,
    that are easily testable and accessible.
    """
    # You could also ask for the Config component at runtime.
    current_config = request.get_component(Config)
    assert current_config is config
    return Response(config.name)
```
