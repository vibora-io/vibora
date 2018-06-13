from vibora import client
from vibora.client.exceptions import MissingSchema
from vibora.tests import TestSuite


class ClientInterfaceTestCase(TestSuite):

    async def test_form_and_body_combined__expects_exception(self):
        try:
            await client.post('http://google.com', form={}, body=b'')
            self.fail('Failed to prevent the user from doing wrong params combination.')
        except ValueError:
            pass

    async def test_form_and_json_combined__expects_exception(self):
        try:
            await client.post('http://google.com', form={}, json={})
            self.fail('Failed to prevent the user from doing wrong params combination.')
        except ValueError:
            pass

    async def test_body_and_json_combined__expects_exception(self):
        try:
            await client.post('http://google.com', body=b'', json={})
            self.fail('Failed to prevent the user from doing wrong params combination.')
        except ValueError:
            pass

    async def test_missing_schema_url__expects_missing_schema_exception(self):
        try:
            await client.get('google.com')
            self.fail('Missing schema exception not raised.')
        except MissingSchema:
            pass
