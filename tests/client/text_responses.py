from vibora import Vibora
from unittest import TestCase
from vibora.responses import Response


class EncodingsTestCase(TestCase):

    def test_latin_1(self):
        server = Vibora()
        original = 'áéíóúç'
        value = original.encode('latin-1')

        @server.route('/')
        def home():
            return Response(value)

        client = server.test_client()
        response = client.get('/')
        self.assertEqual(response.content, value)
        self.assertEqual(response.text(), original)

    def test_utf_8(self):
        server = Vibora()
        original = 'áéíóúç'
        value = original.encode('utf-8')

        @server.route('/')
        def home():
            return Response(value)

        client = server.test_client()
        response = client.get('/')
        self.assertEqual(response.content, value)
        self.assertEqual(response.text(), original)
