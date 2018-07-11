import time
from multiprocessing import Manager
from vibora import Vibora, Request
from vibora.hooks import Events, Hook
from vibora.cache import Static, CacheEngine
from vibora.responses import JsonResponse
from vibora.tests import TestSuite


class CacheTestCase(TestSuite):
    async def test_async_cache_engine_skipping_hooks(self):
        class AsyncEngine(CacheEngine):
            async def get(self, request: Request):
                request.client_ip()
                return self.cache.get(request.url)

            async def store(self, request: Request, response):
                self.cache[request.url] = response

        app = Vibora()
        manager = Manager()
        calls = manager.list()

        def before_end():
            calls.append("called_before_endpoint")

        app.add_hook(Hook(Events.BEFORE_ENDPOINT, before_end))

        @app.route("/", cache=AsyncEngine(skip_hooks=True))
        async def home():
            return JsonResponse({"now": time.time()})

        async with app.test_client() as client:
            response1 = await client.get("/")
            response2 = await client.get("/")

        self.assertEqual(len(calls), 1)
        self.assertEqual(response1.content, response2.content)

    async def test_async_cache_engine_not_skipping_hooks(self):
        class AsyncEngine(CacheEngine):
            async def get(self, request: Request):
                return self.cache.get(request.url)

            async def store(self, request: Request, response):
                self.cache[request.url] = response

        app = Vibora()
        manager = Manager()
        calls = manager.list()

        def before_end():
            calls.append("called_before_endpoint")

        app.add_hook(Hook(Events.BEFORE_ENDPOINT, before_end))

        @app.route("/", cache=AsyncEngine(skip_hooks=False))
        async def home():
            return JsonResponse({"now": time.time()})

        client = app.test_client()
        response1 = await client.get("/")
        response2 = await client.get("/")

        self.assertEqual(len(calls), 2)
        self.assertEqual(response1.content, response2.content)

        client.close()

    async def test_custom_cache_engine_not_skipping_hooks(self):
        class AsyncEngine(CacheEngine):
            def get(self, request: Request):
                return self.cache.get(request.url)

            def store(self, request: Request, response):
                self.cache[request.url] = response

        app = Vibora()
        manager = Manager()
        calls = manager.list()

        def before_end():
            calls.append("called_before_endpoint")

        app.add_hook(Hook(Events.BEFORE_ENDPOINT, before_end))

        @app.route("/", cache=AsyncEngine(skip_hooks=False))
        async def home():
            return JsonResponse({"now": time.time()})

        client = app.test_client()
        response1 = await client.get("/")
        response2 = await client.get("/")

        self.assertEqual(len(calls), 2)
        self.assertEqual(response1.content, response2.content)

        client.close()

    async def test_custom_cache_engine_skipping_hooks(self):
        class AsyncEngine(CacheEngine):
            def get(self, request: Request):
                return self.cache.get(request.url)

            def store(self, request: Request, response):
                self.cache[request.url] = response

        app = Vibora()
        manager = Manager()
        calls = manager.list()

        def before_end():
            calls.append("called_before_endpoint")

        app.add_hook(Hook(Events.BEFORE_ENDPOINT, before_end))

        @app.route("/", cache=AsyncEngine(skip_hooks=True))
        async def home():
            return JsonResponse({"now": time.time()})

        client = app.test_client()
        response1 = await client.get("/")
        response2 = await client.get("/")

        self.assertEqual(len(calls), 1)
        self.assertEqual(response1.content, response2.content)

        client.close()

    async def test_static_cache_skipping_hooks(self):
        app = Vibora()

        @app.route("/", cache=Static(skip_hooks=True))
        async def home():
            return JsonResponse({"now": time.time()})

        client = app.test_client()
        response1 = await client.get("/")
        response2 = await client.get("/")

        self.assertEqual(response1.content, response2.content)

        client.close()

    async def test_static_cache_not_skipping_hooks(self):
        app = Vibora()

        @app.route("/", cache=Static(skip_hooks=False))
        async def home():
            return JsonResponse({"now": time.time()})

        client = app.test_client()
        response1 = await client.get("/")
        response2 = await client.get("/")

        self.assertEqual(response1.content, response2.content)

        client.close()

    async def test_default_expects_static_cache(self):
        app = Vibora()

        @app.route("/", cache=False)
        async def home():
            return JsonResponse({"now": time.time()})

        async with app.test_client() as client:
            response1 = await client.get("/")
            response2 = await client.get("/")

        self.assertNotEqual(response1.content, response2.content)
