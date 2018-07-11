import asyncio
from asyncio import futures
from vibora import Vibora
from vibora.limits import ServerLimits
from vibora.responses import StreamingResponse
from vibora.tests import TestSuite


class StreamingTestSuite(TestSuite):
    async def test_simple_streaming_expects_successful(self):

        app = Vibora()

        async def stream():
            for _ in range(0, 100):
                await asyncio.sleep(0.05)
                yield b"1"

        @app.route("/")
        async def home():
            return StreamingResponse(stream)

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"1" * 100)

    async def test_streaming_with_timeout__expects_timeout(self):

        app = Vibora()

        async def stream():
            for _ in range(0, 100):
                await asyncio.sleep(2)
                yield b"1"

        @app.route("/")
        async def home():
            return StreamingResponse(stream, complete_timeout=1)

        async with app.test_client() as client:
            try:
                await client.get("/", timeout=3)
                self.fail("Vibora should have closed the connection because a streaming timeout is not recoverable.")
            except asyncio.IncompleteReadError:
                pass
            except futures.TimeoutError:
                pass

    async def test_simple_streaming_with_chunk_timeout(self):

        app = Vibora(server_limits=ServerLimits(write_buffer=1))

        async def stream():
            for _ in range(0, 5):
                await asyncio.sleep(0)
                yield b"1" * 1024 * 1024 * 100

        @app.route("/")
        async def home():
            return StreamingResponse(stream, chunk_timeout=3, complete_timeout=999)

        async with app.test_client() as client:
            response = await client.get("/", stream=True)
            try:
                first = True
                chunk_size = 1 * 1024 * 1024
                async for chunk in response.stream(chunk_size=chunk_size):
                    if first:
                        await asyncio.sleep(5)
                        first = False
                    self.assertTrue(len(chunk) <= chunk_size)
                self.fail("Vibora should have closed the connection because of a chunk timeout.")
            except asyncio.IncompleteReadError:
                pass
