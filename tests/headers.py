import unittest
import uuid
import json
from vibora import Vibora
from vibora.headers import Headers
from vibora.responses import JsonResponse
from vibora.request import Request
from vibora.tests import TestSuite


class HeadersTestCase(unittest.TestCase):
    def test_headers_obj(self):
        headers = Headers()
        headers["test"] = "1"
        headers["test"] = "2"
        headers["a"] = "3"
        self.assertEqual({"test": "2", "a": "3"}, headers.dump())


class IntegrationHeadersTestCase(TestSuite):
    async def test_extra_headers__expects_correctly_evaluated(self):
        app = Vibora()

        @app.route("/")
        async def get_headers(request: Request):
            return JsonResponse(request.headers.dump())

        client = app.test_client()
        token = str(uuid.uuid4())
        response = await client.get("/", headers={"x-access-token": token})
        response = json.loads(response.content)
        self.assertEqual(response.get("x-access-token"), token)
