import asyncio
import time
import uuid
from vibora import Vibora, Response, Request, MissingComponent
from vibora.responses import StreamingResponse
from vibora.hooks import Events
from vibora.tests import TestSuite


class HooksTestSuite(TestSuite):

    def setUp(self):
        self.app = Vibora()

    async def test_simple_before_request_with_component(self):
        @self.app.handle(Events.BEFORE_ENDPOINT)
        def before_endpoint(request: Request):
            request.context['status_code'] = 200

        @self.app.route('/')
        async def home(request: Request):
            return Response(b'', status_code=request.context.get('status_code', 500))

        with self.app.test_client() as client:
            response = await client.get('/')
            self.assertEqual(response.status_code, 200)

    async def test_before_request_halting(self):
        @self.app.handle(Events.BEFORE_ENDPOINT)
        def before_endpoint():
            return Response(b'', status_code=200)

        @self.app.route('/')
        async def home():
            return Response(b'', status_code=500)

        with self.app.test_client() as client:
            response = await client.get('/')
            self.assertEqual(response.status_code, 200)

    async def test_before_request_propagation(self):
        @self.app.handle(Events.BEFORE_ENDPOINT)
        def before_endpoint_1(request: Request):
            request.context['counter'] = 1

        @self.app.handle(Events.BEFORE_ENDPOINT)
        def before_endpoint_2(request: Request):
            request.context['counter'] += 1

        @self.app.route('/')
        async def home(request: Request):
            return Response(str(request.context['counter']).encode(), status_code=500)

        with self.app.test_client() as client:
            response = await client.get('/')
            self.assertEqual(response.content, b'2')

    async def test_before_server_start(self):
        secret = uuid.uuid4().hex.encode()

        class RuntimeConfig:
            def __init__(self):
                self.secret = secret

        @self.app.handle(Events.BEFORE_SERVER_START)
        def before_server_start(app: Vibora):
            app.components.add(RuntimeConfig())

        @self.app.route('/')
        async def home(request: Request):
            return Response(request.app.components.get(RuntimeConfig).secret, status_code=200)

        with self.app.test_client() as client:
            response = await client.get('/')
            self.assertEqual(secret, response.content)

    async def test_after_server_start(self):
        secret = uuid.uuid4().hex.encode()

        class RuntimeConfig:
            def __init__(self):
                self.secret = secret

        @self.app.route('/')
        async def home(request: Request):
            try:
                return Response(request.app.components.get(RuntimeConfig).secret, status_code=200)
            except MissingComponent:
                return Response(b'', status_code=500)

        @self.app.handle(Events.AFTER_SERVER_START)
        async def before_server_start(app: Vibora):
            await asyncio.sleep(1)
            app.components.add(RuntimeConfig())

        with self.app.test_client() as client:
            # This must return an internal server error because the component is not registered yet
            # and the server is already online.
            response = await client.get('/')
            self.assertEqual(response.status_code, 500)

        # We wait a little to let the after_server_start hook finish his job.
        await asyncio.sleep(1)

        with self.app.test_client() as client:
            response = await client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(secret, response.content)

    async def test_after_endpoint_modify_response(self):

        @self.app.route('/')
        async def home():
            return Response(b'', status_code=500)

        @self.app.handle(Events.AFTER_ENDPOINT)
        async def after_response(r: Response):
            r.status_code = 200

        with self.app.test_client() as client:
            response = await client.get('/')
            self.assertEqual(response.status_code, 200)

    async def test_after_response_sent(self):

        class Mock:
            def __init__(self):
                self.test = 'test'

        @self.app.route('/')
        async def home(request: Request):
            try:
                request.app.components.get(Mock)
                return Response(b'Second')
            except Exception as error:
                return Response(str(error).encode(), status_code=500)

        @self.app.handle(Events.AFTER_RESPONSE_SENT)
        async def after_response_sent(app: Vibora):
            try:
                app.components.add(Mock())
            except ValueError:
                pass

        with self.app.test_client() as client:
            response = await client.get('/')
            self.assertEqual(response.status_code, 500)
            await asyncio.sleep(1)
            response = await client.get('/')
            self.assertEqual(response.status_code, 200)

    async def test_before_server_stop_expects_polite_shutdown(self):
        """
        This test tries to ensure that the server will respect current streaming connections and
        give it some time before closing them so requests are closed abruptly.
        :return:
        """

        @self.app.route('/')
        async def home():
            async def slow_streaming():
                for _ in range(0, 5):
                    yield b'123'
                    await asyncio.sleep(1)
            return StreamingResponse(slow_streaming)

        with self.app.test_client() as client:
            response = await client.get('/', stream=True)
            # This sends a kill signal to all workers, pretty much like someone is trying to stop the server.
            # Our HTTP client already sent the request but didn't consumed the response yet, the server must
            # respectfully wait for us.
            time.sleep(1)
            self.app.clean_up()
            await response.read_content()
            self.assertEqual(response.content, b'123' * 5)
