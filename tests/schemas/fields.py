from unittest import TestCase
from vibora.schemas.fields import String
from vibora.schemas.exceptions import ValidationError


class StringTestCase(TestCase):

    def test_default__expects_successful(self):
        field = String()
        self.assertEqual('Test', field.load('Test'))

    def test_default_with_integer__expects_casting(self):
        field = String()
        self.assertEqual('1', field.load('1'))

    def test_strict_true__expects_failure_with_integer(self):
        field = String(strict=True)
        try:
            field.load(1)
            self.fail('Missing exception')
        except ValidationError:
            pass

    def test_strict_true__expects_successful(self):
        field = String(strict=True)
        self.assertEqual('TestString', field.load('TestString'))

    def test_default__expects_default_instead_of_none(self):
        default = 'Test'
        field = String(default=default)
        self.assertEqual(field.load(None), default)

    def test_default_with_empty_string__expects_default(self):
        default = 'Test'
        field = String(default=default)
        self.assertEqual(field.load(''), default)

    def test_default_with_non_empty_string__expects_ignored(self):
        default = 'Test'
        field = String(default=default)
        self.assertEqual(field.load('A'), 'A')
