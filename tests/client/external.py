from vibora import client
from vibora.tests import TestSuite


class HelloWorldCase(TestSuite):

    async def test_simple_get_google__expects_successful(self):
        response = await client.get('https://google.com/')
        self.assertEqual(response.status_code, 200)

    async def test_simple_get_google_https__expects_successful(self):
        response = await client.get('https://google.com/')
        self.assertEqual(response.status_code, 200)
