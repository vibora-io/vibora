### Configuration

Configuration handling in Vibora is simple thanks to components.

In your init script (usually called run.py) you can load environment
variables, config files or whatever and register a
config class as a new component and that's all.

This method is a little bit harder for beginners when compared to the
Django approach but it's way more flexible and allows you to build
whatever suits you better.

Here goes a practical example:

1) Create a file called config.py
```py
import aioredis


class Config:
    def __init__(self, config: dict):
        self.port = config['port']
        self.host = config['host']
        self.redis_host = config['redis']['host']
```

2) Create a file called api.py
```py
from vibora import Vibora
from vibora.blueprints import Blueprint
from vibora.hooks import Events
from aioredis import ConnectionsPool
from config import Config

api = Blueprint()


@api.route('/')
async def home(pool: ConnectionsPool):
    await pool.set('my_key', 'any_value')
    value = await pool.get('my_key')
    return Response(value.encode())


@api.handle(Events.BEFORE_SERVER_START)
async def initialize_db(app: Vibora, config: Config):

    # Creating a pool of connection to Redis.
    pool = await aioredis.create_pool(config.redis_host)

    # In this case we are registering the pool as a new component
    # but if you find yourself using too many components
    # feel free to wrap them all inside a single component
    # so you don't need to repeat yourself in every route.
    app.components.add(pool)
```

3) Now create a file called config.json
```js
{
    "host": "0.0.0.0",
    "port": 8000,
    "redis_host": "127.0.0.1"
}
```

4) Now create a file called run.py

```py
import json
from vibora import Vibora
from api import api
from config import Config


if __name__ == "__main__":
    # Creating a new app
    app = Vibora()

    # Registering our API
    app.add_blueprint(api, prefixes={'v1': '/v1'})

    # Opening the configuration file.
    with open('config.json') as f:

        # Parsing the JSON configs.
        config = Config(json.load(f))

        # Registering the config as a component so you can use it
        # later on (as we do in the "before_server_start" hook)
        app.components.add(config)

        # Running the server.
        app.run(host=config.host, port=config.port)
```

The previous example loads your configuration from JSON files, but
other approaches, such as environment variables, can be used.

Notice that we register the config instance as a component because
databases drivers, for example, often need to be instantiated
after the server is forked so you'll need the config after
the "run script".

Also, our config class in this example is a mere wrapper for our JSON
config but in a real app, you could be using the config class as
a components wrapper. You'll just need to add references to many
important components so you don't need to repeat yourself by
importing many different components in every route.
