import uuid
from vibora import Vibora, TestSuite
from vibora.router import RouterStrategy
from vibora.responses import Response


class RedirectStrategyTestCase(TestSuite):
    def setUp(self):
        self.app = Vibora(router_strategy=RouterStrategy.REDIRECT)

    async def test_missing_slash_expects_redirect(self):
        @self.app.route("/asd", methods=["GET"])
        async def home():
            return Response(b"123")

        client = self.app.test_client(follow_redirects=False)
        self.assertEqual((await client.request("/asd/")).status_code, 301)

    async def test_missing_slash_with_default_post_route_expects_not_found(self):
        @self.app.route("/asd", methods=["POST"])
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual((await client.request("/asd/")).status_code, 404)

    async def test_wrong_method_expects_405_response(self):
        @self.app.route("/asd/", methods=["GET"])
        async def home():
            return Response(b"")

        client = self.app.test_client()
        self.assertEqual((await client.request("/asd", method="POST")).status_code, 405)

    async def test_additional_slash_expects_redirected(self):
        @self.app.route("/asd/", methods=["GET"])
        async def home():
            return Response(b"")

        client = self.app.test_client(follow_redirects=False)
        response = await client.request("/asd", method="GET")
        self.assertEqual(response.status_code, 301)
        self.assertEqual("/asd/", response.headers["location"])


class StrictStrategyTestCase(TestSuite):
    def setUp(self):
        self.app = Vibora(router_strategy=RouterStrategy.STRICT)

    async def test_simple_get_route_expects_found(self):
        path = "/" + uuid.uuid4().hex

        @self.app.route(path)
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(200, (await client.request(path)).status_code)

    async def test_simple_get_route_expects_404(self):
        @self.app.route("/test")
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(404, (await client.request("/wrong-path")).status_code)

    async def test_route_missing_slash_expects_404(self):
        @self.app.route("/test/")
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(404, (await client.request("/test")).status_code)

    async def test_route_correct_slash_but_different_method_expects_not_allowed(self):
        @self.app.route("/test/", methods=["POST"])
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(405, (await client.request("/test/")).status_code)

    async def test_route_with_params_expect_found(self):
        @self.app.route("/<name>/")
        async def home(name: int):
            self.assertEqual(name, 123)
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(200, (await client.request("/123/")).status_code)

    async def test_route_with_params_expects_not_found(self):
        @self.app.route("/<name>")
        async def home(name: str):
            return Response(name.encode())

        client = self.app.test_client()
        self.assertEqual(404, (await client.request("/123/")).status_code)

    async def test_dynamic_route_expect_found(self):
        @self.app.route("/<anything>/a")
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(200, (await client.request("/123/a")).status_code)

    async def test_dynamic_route_expects_not_found(self):
        @self.app.route("/.*/a")
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(404, (await client.request("/123/")).status_code)


class CloneStrategyTestCase(TestSuite):
    def setUp(self):
        self.app = Vibora(router_strategy=RouterStrategy.CLONE)

    async def test_simple_get_route_expects_found(self):
        @self.app.route("/test")
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(200, (await client.request("/test")).status_code)

    async def test_simple_get_route_wrong_method_expects_not_allowed(self):
        @self.app.route("/test", methods=["POST"])
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(405, (await client.request("/test")).status_code)

    async def test_simple_get_route_wrong_path_expects_not_found(self):
        @self.app.route("/test", methods=["POST"])
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(404, (await client.request("/asd")).status_code)

    async def test_missing_slash_expects_found(self):
        @self.app.route("/test/", methods=["GET"])
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(200, (await client.request("/test")).status_code)

    async def test_additional_slash_expects_found(self):
        @self.app.route("/test", methods=["GET"])
        async def home():
            return Response(b"123")

        client = self.app.test_client()
        self.assertEqual(200, (await client.request("/test/")).status_code)
