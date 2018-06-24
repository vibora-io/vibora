### Testing

Testing is the most important part of any project with considerably
size and yet of one of the most ignored steps.

Vibora has a builtin and fully featured async HTTP client and
a simple test framework to make it easier for you as in the example bellow:

```py
from vibora import Vibora, Response
from vibora.tests import TestSuite

app = Vibora()


@app.route('/')
async def home():
    return Response(b'Hello World')


class HomeTestCase(TestSuite):
    def setUp(self):
        self.client = app.test_client()

    async def test_home(self):
        response = await self.client.get('/')
        self.assertEqual(response.content, b'Hello World')
```
