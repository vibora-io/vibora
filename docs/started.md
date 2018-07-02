## Getting Started

Make sure you are using `Python 3.6+` because Vibora takes
advantage of some new Python features.

1. Install Vibora: `pip install vibora[fast]`

> It's highly recommended to install Vibora inside a virtualenv.

> If you have trouble with Vibora's dependencies try to install it without the extra libraries: `pip install vibora`


2. Create a file called `anything.py` with the following code:


```py
from vibora import Vibora, JsonResponse

app = Vibora()


@app.route('/')
async def home():
    return JsonResponse({'hello': 'world'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
```

3. Run the server: `python3 anything.py`


4. Open your browser and go to `http://127.0.0.1:8000`


### Creating a project

The previous example shows how quickly you can spin up a server, but
Vibora has an integrated command-line tool that makes getting a server
up and running even easier.

Using the command-line tool is the recommended way to start a new project,
try it out: `vibora new project_name`
