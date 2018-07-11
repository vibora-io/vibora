from vibora import Vibora
from vibora.multipart import FileUpload
from vibora.request import Request
from vibora.responses import JsonResponse
from vibora.tests import TestSuite


class FormsTestCase(TestSuite):
    async def test_simple_form_expects_correctly_parsed(self):
        app = Vibora()

        @app.route("/", methods=["POST"])
        async def home(request: Request):
            form = await request.form()
            return JsonResponse(form)

        async with app.test_client() as client:
            response = await client.post("/", form={"a": 1, "b": 2})
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(response.json(), {"a": "1", "b": "2"})

    async def test_files_upload_expects_correctly_parsed(self):
        app = Vibora()

        @app.route("/", methods=["POST"])
        async def home(request: Request):
            form = await request.form()
            return JsonResponse(
                {
                    "a": (await form["a"].read()).decode(),
                    "b": (await form["b"].read()).decode(),
                    "c": (await form["c"].read()).decode(),
                    "d": form["d"],
                }
            )

        async with app.test_client() as client:
            response = await client.post(
                "/",
                form={
                    "a": FileUpload(content=b"a"),
                    "b": FileUpload(content=b"b"),
                    "c": FileUpload(content=b"c"),
                    "d": 1,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(response.json(), {"a": "a", "b": "b", "c": "c", "d": "1"})

    async def test_files_attribute_expects_correctly_parsed(self):
        app = Vibora()

        @app.route("/", methods=["POST"])
        async def home(request: Request):
            uploaded_files = {}
            for file in await request.files():
                uploaded_files[file.filename] = (await file.read()).decode()
            return JsonResponse(uploaded_files)

        async with app.test_client() as client:
            response = await client.post(
                "/",
                form={
                    "a": FileUpload(content=b"a", name="a"),
                    "b": FileUpload(content=b"b", name="b"),
                    "c": FileUpload(content=b"c", name="c"),
                    "d": 1,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(response.json(), {"a": "a", "b": "b", "c": "c"})
