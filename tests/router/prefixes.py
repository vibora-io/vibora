from vibora import Vibora, TestSuite
from vibora.blueprints import Blueprint
from vibora.responses import JsonResponse


class RouterPrefixesTestCase(TestSuite):
    async def test_root_route_expect_registered(self):
        data = {"hello": "world"}
        app = Vibora()

        @app.route("/test", methods=["GET"])
        async def home():
            return JsonResponse(data)

        response = await app.test_client().request("/test/")
        self.assertEqual(response.json(), data)

    async def test_root_route_expect_not_found(self):
        app = Vibora()
        response = await app.test_client().request("/test")
        self.assertEqual(response.status_code, 404)

    async def test_add_blueprint_with_one_prefix(self):
        data, app = {"hello": "world"}, Vibora()
        bp = Blueprint()

        @bp.route("/")
        async def home():
            return JsonResponse(data)

        app.add_blueprint(bp, prefixes={"test": "/test"})
        response = await app.test_client().request("/test")
        self.assertEqual(response.json(), data)

    async def test_prefix_with_dynamic_route(self):
        app = Vibora()
        bp = Blueprint()

        @bp.route("/<name>")
        async def home(name: str):
            return JsonResponse({"name": name})

        app.add_blueprint(bp, prefixes={"test": "/test"})
        response = await app.test_client().request("/test/test")
        self.assertEqual(response.json(), {"name": "test"})
