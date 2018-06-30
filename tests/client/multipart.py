from vibora import Vibora, Request
from vibora.tests import TestSuite
from vibora.responses import JsonResponse
from vibora.multipart import FileUpload


class FormsTestCase(TestSuite):

    async def test_simple_post__expects_correctly_interpreted(self):
        app = Vibora()

        @app.route('/', methods=['POST'])
        async def home(request: Request):
            return JsonResponse((await request.form()))

        async with app.test_client() as client:
            response = await client.post('/', form={'a': 1, 'b': 2})

        self.assertDictEqual(response.json(), {'a': '1', 'b': '2'})

    async def test_file_upload_with_another_values(self):
        app = Vibora()

        @app.route('/', methods=['POST'])
        async def home(request: Request):
            form = await request.form()
            return JsonResponse({'a': form['a'], 'b': (await form['b'].read()).decode()})

        async with app.test_client() as client:
            response = await client.post('/', form={'a': 1, 'b': FileUpload(content=b'uploaded_file')})
            self.assertDictEqual(response.json(), {'a': '1', 'b': 'uploaded_file'})
