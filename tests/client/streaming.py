import pytest
from typing import Tuple
from vibora import Vibora, Response
from vibora.responses import StreamingResponse

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def streaming_server():
    def generate_data():
        yield b"1" * (10 * 1024)
        yield b"2" * 1024

    app = Vibora()

    @app.route("/")
    async def home():
        return StreamingResponse(generate_data)

    yield app, b"".join(generate_data())

    app.clean_up()


@pytest.fixture()
async def static_server():
    data = b"123"
    app = Vibora()

    @app.route("/")
    async def home():
        return Response(data)

    yield app, data

    app.clean_up()


@pytest.fixture(params=["static_server", "streaming_server"], name="server")
def proxy_fixture(request):
    return request.getfuncargvalue(request.param)


async def test_streaming_client_reading_content__expects_successful(server: Tuple[Vibora, bytes]):
    app, expected_data = server
    async with app.test_client() as client:
        response = await client.get("/", stream=True)
        await response.read_content()
        assert response.content == expected_data


async def test_streaming_client_reading_stream__expects_successful(server: Tuple[Vibora, bytes]):
    app, expected_data = server
    async with app.test_client() as client:
        response = await client.get("/", stream=True)
        received_data = bytearray()
        async for chunk in response.stream():
            received_data.extend(chunk)
        assert received_data == expected_data


async def test_streaming_client_very_small_reads__expects_successful(server: Tuple[Vibora, bytes]):
    app, expected_data = server
    async with app.test_client() as client:
        response = await client.get("/", stream=True)
        received_data = bytearray()
        async for chunk in response.stream(chunk_size=1):
            assert len(chunk) == 1
            received_data.extend(chunk)
        assert received_data == expected_data
