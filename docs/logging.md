### Logging

Vibora has a simple logging mechanism to avoid locking you into our library of choice.

You must provide a function that receives two parameters:  a msg and a logging level (that matches logging standard library for usability sake).

That's all.

It's up to you to choose what to do with logging messages.


```py
import logging
from vibora import Vibora, Response

app = Vibora()

@app.route('/')
def home():
    return Response(b'Hello World')

if __name__ == '__main__':
    def log_handler(msg, level):
        # Redirecting the msg and level to logging library.
        getattr(logging, level)(msg)
        print(f'Msg: {msg} / Level: {level}')

    app.run(logging=log_handler)
```
