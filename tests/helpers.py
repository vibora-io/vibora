from vibora import Vibora
from vibora.tests import TestSuite
from vibora.responses import Response


class UrlForTestSuite(TestSuite):
    def setUp(self):
        self.app = Vibora()

        @self.app.route("/123")
        async def home():
            return Response(b"")

        self.app.initialize()

    def test_hello_world_situation(self):
        self.assertEqual(self.app.url_for("home"), "/123/")
