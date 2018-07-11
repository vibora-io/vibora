import asyncio
from vibora import Vibora
from vibora.limits import RouteLimits
from vibora.tests import TestSuite
from vibora.responses import Response, StreamingResponse


class TimeoutsTestCase(TestSuite):
    async def test_simple_case_expects_timeout_response(self):
        app = Vibora()

        @app.route("/", limits=RouteLimits(timeout=2))
        async def home():
            await asyncio.sleep(10)
            return Response(b"Wrong. This request should timeout.")

        async with app.test_client() as client:
            response = await client.get("/", timeout=4)
            self.assertEqual(response.status_code, 500)

    async def test_non_timeout_case_expects_successful_response(self):

        app = Vibora()

        @app.route("/", limits=RouteLimits(timeout=1))
        async def home():
            return Response(b"Correct.")

        async with app.test_client() as client:
            response = await client.get("/", timeout=4)
            self.assertEqual(response.status_code, 200)

        # We wait to see if the server correctly removed the timeout watcher
        # otherwise an exception will raise.
        await asyncio.sleep(2)

    async def test_async_streaming_expects_successful(self):

        app = Vibora()

        async def generator():
            yield b"1"
            await asyncio.sleep(2)
            yield b"2"

        @app.route("/", limits=RouteLimits(timeout=1))
        async def home():
            return StreamingResponse(generator)

        async with app.test_client() as client:
            try:
                await client.get("/", timeout=10)
            except Exception as error:
                print(error)
                self.fail("Timeout should be canceled because it's a streaming response.")

    async def test_async_streaming_expects_successful_response(self):

        app = Vibora()

        async def generator():
            yield b"1"
            await asyncio.sleep(0)
            yield b"2"
            await asyncio.sleep(0)
            yield b"3"

        @app.route("/", limits=RouteLimits(timeout=5))
        async def home():
            return StreamingResponse(generator)

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.content, b"123")

    async def test_sync_iterator_expects_successful_response(self):

        app = Vibora()

        def generator():
            yield b"1"
            yield b"2"
            yield b"3"

        @app.route("/", limits=RouteLimits(timeout=5))
        async def home():
            return StreamingResponse(generator)

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.content, b"123")
