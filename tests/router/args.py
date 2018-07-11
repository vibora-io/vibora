import pytest
from vibora.responses import Response
from ..fixtures import create_app  # noqa

pytestmark = pytest.mark.asyncio


async def test_route_with_args__expects_found(app):
    @app.route("/test")
    async def home():
        return Response(b"test")

    async with app.test_client() as client:
        response = await client.get("/test", query={"a": 1, "b": 2, "c": 3})
        assert response.content == b"test"


async def test_empty_route_with_args__expects_found(app):
    @app.route("")
    async def home():
        return Response(b"test")

    async with app.test_client() as client:
        response = await client.get("/", query={"a": 1, "b": 2, "c": 3})
        assert response.content == b"test"


async def test_route_with_fragment__expects_found(app):
    @app.route("/")
    async def home():
        return Response(b"test")

    async with app.test_client() as client:
        response = await client.get("/#test")
        assert response.content == b"test"


async def test_route_with_query_and_fragment__expects_found(app):
    @app.route("/")
    async def home():
        return Response(b"test")

    async with app.test_client() as client:
        response = await client.get("/?test=1#test")
        assert response.content == b"test"


async def test_bytes_query_parameter_expects_correctly_parsed(app):
    @app.route("/<name>")
    async def home(name: bytes):
        return Response(name)

    async with app.test_client() as client:
        response = await client.get("/test?test=bytes#c")
        assert response.content == b"test"


async def test_string_query_parameter_expects_correctly_parsed(app):
    @app.route("/<name>")
    async def home(name: str):
        return Response(name.encode())

    async with app.test_client() as client:
        response = await client.get("/test?test=123#a")
        assert response.content == b"test"


async def test_int_query_parameter_expects_correctly_parsed(app):
    @app.route("/<count>")
    async def home(count: int):
        return Response(str(count + 1).encode())

    async with app.test_client() as client:
        response = await client.get("/123?test=123#b")
        assert response.content == b"124"
