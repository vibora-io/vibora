from unittest import TestCase
from vibora.responses import JsonResponse, Response
from vibora.cookies import Cookie
from vibora.utils import json


class AttributesTestCase(TestCase):
    """
    It's important to be able to access common attributes
    like cookies, headers from Python
    """

    def test_json_response_attributes(self):
        headers = {"test": "test"}
        cookies = [Cookie("server", "Vibora")]
        status_code = 404
        content = {"a": 1}
        response = JsonResponse(content, headers=headers, cookies=cookies, status_code=status_code)
        self.assertEqual(response.cookies, cookies)
        self.assertEqual(response.headers["test"], headers["test"])
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.content, json.dumps(content).encode("utf-8"))

    def test_plain_response_attributes(self):
        headers = {"server": "Vibora"}
        cookies = [Cookie("server", "Vibora")]
        status_code = 404
        content = b"HelloWorld"
        response = Response(content, headers=headers, cookies=cookies, status_code=status_code)
        self.assertEqual(response.cookies, cookies)
        self.assertEqual(response.headers["server"], headers["server"])
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.content, content)
