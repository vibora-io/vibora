from vibora import Vibora
from vibora.tests import TestSuite
from vibora.responses import StreamingResponse, Response


class ChunkedStreamingTestCase(TestSuite):

    def setUp(self):
        def generate_data():
            yield b'1' * (10 * 1024)
            yield b'2' * 1024
        self.data = b''.join(generate_data())
        self.server = Vibora()

        @self.server.route('/')
        async def home():
            return StreamingResponse(generate_data)

    async def test_streaming_client_reading_content__expects_successful(self):
        async with self.server.test_client() as client:
            response = await client.get('/', stream=True)
            await response.read_content()
            self.assertEqual(response.content, self.data)

    async def test_streaming_client_reading_stream__expects_successful(self):
        async with self.server.test_client() as client:
            response = await client.get('/', stream=True)
            received_data = bytearray()
            async for chunk in response.stream():
                received_data.extend(chunk)
            self.assertEqual(received_data, self.data)

    async def test_streaming_client_very_small_reads__expects_successful(self):
        client = self.server.test_client()
        response = await client.get('/', stream=True)
        received_data = bytearray()
        async for chunk in response.stream(chunk_size=1):
            self.assertTrue(len(chunk) == 1)
            received_data.extend(chunk)
        self.assertEqual(received_data, self.data)


class StreamingTestCase(TestSuite):

    def setUp(self):
        self.data = b'1' * (10 * 1024) + b'2' * 1024
        self.server = Vibora()

        @self.server.route('/')
        async def home():
            return Response(self.data)

    async def test_streaming_client_reading_content__expects_successful(self):
        client = self.server.test_client()
        response = await client.get('/', stream=True)
        await response.read_content()
        self.assertEqual(response.content, self.data)

    async def test_streaming_client_reading_stream__expects_successful(self):
        client = self.server.test_client()
        response = await client.get('/', stream=True)
        received_data = bytearray()
        async for chunk in response.stream():
            received_data.extend(chunk)
        self.assertEqual(received_data, self.data)

    async def test_streaming_client_very_small_reads__expects_successful(self):
        client = self.server.test_client()
        response = await client.get('/', stream=True)
        received_data = bytearray()
        async for chunk in response.stream(chunk_size=1):
            self.assertTrue(len(chunk) == 1)
            received_data.extend(chunk)
        self.assertEqual(received_data, self.data)
