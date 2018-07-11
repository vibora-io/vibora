import pytest
from vibora import Vibora, Request
from vibora.responses import JsonResponse
from vibora.multipart import FileUpload

pytestmark = pytest.mark.asyncio


async def test_simple_post__expects_correctly_interpreted():
    app = Vibora()

    @app.route("/", methods=["POST"])
    async def home(request: Request):
        return JsonResponse((await request.form()))

    async with app.test_client() as client:
        response = await client.post("/", form={"a": 1, "b": 2})
    assert response.json() == {"a": "1", "b": "2"}


async def test_file_upload_with_another_values():
    app = Vibora()

    @app.route("/", methods=["POST"])
    async def home(request: Request):
        form = await request.form()
        return JsonResponse({"a": form["a"], "b": (await form["b"].read()).decode()})

    async with app.test_client() as client:
        response = await client.post("/", form={"a": 1, "b": FileUpload(content=b"uploaded_file")})
        assert response.json() == {"a": "1", "b": "uploaded_file"}
