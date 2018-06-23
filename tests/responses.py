import ujson
from unittest import TestCase
from vibora import Vibora
from vibora.responses import JsonResponse, Response
from vibora.cookies import Cookie
from vibora.tests import TestSuite


class AttributesTestCase(TestCase):
    """
    It's important to be able to access common attributes
    like cookies, headers from Python
    """

    def test_json_response_attributes(self):
        headers = {'test': 'test'}
        cookies = [Cookie('server', 'Vibora')]
        status_code = 404
        content = {'a': 1}
        response = JsonResponse(content, headers=headers, cookies=cookies, status_code=status_code)
        self.assertEqual(response.cookies, cookies)
        self.assertEqual(response.headers['test'], headers['test'])
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.content, ujson.dumps(content).encode('utf-8'))

    def test_plain_response_attributes(self):
        headers = {'server': 'Vibora'}
        cookies = [Cookie('server', 'Vibora')]
        status_code = 404
        content = b'HelloWorld'
        response = Response(content, headers=headers, cookies=cookies, status_code=status_code)
        self.assertEqual(response.cookies, cookies)
        self.assertEqual(response.headers['server'], headers['server'])
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.content, content)


class IntegrationCookiesTestCase(TestSuite):

    async def test_cookies_encoding__expects_correctly_evaluated(self):
        app = Vibora()
        content = {"data": "all right"}

        @app.route("/")
        async def set_cookie():
            cookies = [Cookie('test', 'test_cookie')]
            return JsonResponse(content, cookies=cookies)

        client = app.test_client()
        response = await client.get('/')
        set_cookie_header = response.headers['set-cookie']

        self.assertEqual(response.json(), content)
        self.assertEqual(set_cookie_header, 'test=test_cookie;')
