from vibora import Vibora, Response
from vibora.blueprints import Blueprint
from vibora.tests import TestSuite


class BlueprintsTestCase(TestSuite):
    def setUp(self):
        self.app = Vibora()

    async def test_simple_sub_domain_expects_match(self):
        b1 = Blueprint(hosts=[".*"])

        @b1.route("/")
        async def home():
            return Response(b"123")

        self.app.add_blueprint(b1)
        async with self.app.test_client() as client:
            response = await client.request("/")
            self.assertEqual(response.content, b"123")

    async def test_exact_match_sub_domain_expects_match(self):
        b1 = Blueprint(hosts=["test.vibora.io"])

        @b1.route("/")
        async def home():
            return Response(b"123")

        self.app.add_blueprint(b1)
        async with self.app.test_client() as client:
            response = await client.request("/", headers={"Host": "test.vibora.io"})
            self.assertEqual(response.content, b"123")

    async def test_different_sub_domain_expects_404(self):
        b1 = Blueprint(hosts=["test.vibora.io"])

        @b1.route("/")
        async def home():
            return Response(b"123")

        self.app.add_blueprint(b1)
        async with self.app.test_client() as client:
            response = await client.request("/", headers={"Host": "test2.vibora.io"})
            self.assertEqual(response.status_code, 404)

    async def test_sub_domain_working_with_non_hosts_based(self):
        b1 = Blueprint(hosts=["test.vibora.io"])
        b2 = Blueprint()

        @b1.route("/")
        async def home():
            return Response(b"123")

        @b2.route("/test")
        async def home2():
            return Response(b"123")

        self.app.add_blueprint(b1)
        self.app.add_blueprint(b2)
        async with self.app.test_client() as client:
            response = await client.request("/", headers={"Host": "test.vibora.io"})
            self.assertEqual(response.status_code, 200)
            response = await client.request("/", headers={"Host": "test2.vibora.io"})
            self.assertEqual(response.status_code, 404)
            response = await client.request("/test", headers={"Host": "anything.should.work"})
            self.assertEqual(response.status_code, 200)
            response = await client.request("/test2", headers={"Host": "anything.should.404"})
            self.assertEqual(response.status_code, 404)
