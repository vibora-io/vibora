from vibora import Vibora
from vibora.responses import Response
from vibora.request import Request
from vibora.tests import TestSuite
from vibora.limits import ServerLimits, RouteLimits


class LimitTestCase(TestSuite):
    async def test_body_smaller_than_limit_expects_200(self):
        app = Vibora(route_limits=RouteLimits(max_body_size=2))

        @app.route("/", methods=["POST"])
        async def home(request: Request):
            await request.stream.read()
            return Response(b"Correct. Request should not be blocked.")

        async with app.test_client() as client:
            response = await client.post("/", body=b"1")
            self.assertEqual(response.status_code, 200)

    async def test_body_bigger_than_expected_expects_rejected(self):
        app = Vibora(route_limits=RouteLimits(max_body_size=1))

        @app.route("/", methods=["POST"])
        async def home(request: Request):
            await request.stream.read()
            return Response(b"Wrong. Request should halted earlier.")

        async with app.test_client() as client:
            response = await client.post("/", body=b"12")
            self.assertEqual(response.status_code, 413)

    async def test_headers_bigger_than_expected_expects_rejected_request(self):
        app = Vibora(server_limits=ServerLimits(max_headers_size=1))

        @app.route("/", methods=["GET"])
        async def home():
            return Response(b"Wrong. Request should halted earlier.")

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.status_code, 400)

    async def test_headers_smaller_than_limit_expects_200(self):
        app = Vibora(server_limits=ServerLimits(max_headers_size=1 * 1024 * 1024))

        @app.route("/", methods=["GET"])
        async def home():
            return Response(b"Correct. Request should pass without problems.")

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.status_code, 200)

    async def test_custom_body_limit_per_route_expects_successful(self):
        app = Vibora(route_limits=RouteLimits(max_body_size=1))

        @app.route("/", methods=["POST"], limits=RouteLimits(max_body_size=2))
        async def home(request: Request):
            await request.stream.read()
            return Response(b"Correct. Request should pass without problems.")

        async with app.test_client() as client:
            response = await client.post("/", body=b"11")
            self.assertEqual(response.status_code, 200)

    async def test_custom_body_limit_more_restrictive_per_route_expects_successful(self):
        app = Vibora(route_limits=RouteLimits(max_body_size=100))

        @app.route("/", methods=["POST"], limits=RouteLimits(max_body_size=1))
        async def home(request: Request):
            await request.stream.read()
            return Response(b"Wrong. Request must be blocked because this route is more restrictive.")

        async with app.test_client() as client:
            response = await client.post("/", body=b"11")
            self.assertEqual(response.status_code, 413)
