### Hooks (Listeners)

Hooks are functions that are called after an event.

Let's suppose you want to add a header to every response in your app.
Instead of manually editing every single route in your app you can just
register a listener to the event "BeforeResponse" and inject the desired headers.

Below is a fully working example:

```py
from vibora import Vibora, Response
from vibora.hooks import Events

app = Vibora()

@app.route('/')
async def home():
    return Response(b'Hello World')

@app.handle(Events.BEFORE_RESPONSE)
async def before_response(response: Response):
    response.headers['x-my-custom-header'] = 'Hello :)'

if __name__ == '__main__':
    app.run()
```

Hooks can halt a request and prevent a route from being called,
completely modify the response, handle app start/stop functionalities,
initialize components and do all kind of stuff.

> The golden rule is: If you don't want to modify the request flow (like halting requests)
you don't want to return anything in your function.
Of course that depends on which event you are listening to.
