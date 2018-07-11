from unittest.mock import Mock, MagicMock
from vibora.schemas import Schema, fields
from vibora.schemas.exceptions import ValidationError, InvalidSchema
from vibora.schemas.messages import Messages, EnglishLanguage
from vibora.schemas.validators import Length
from vibora.tests import TestSuite


class SchemasTestCase(TestSuite):
    async def test_basic_schema_loads(self):
        class TestSchema(Schema):
            field1: str
            field2: str

        values = {"field1": "Test", "field2": "123"}
        data = await TestSchema.load(values)
        self.assertTrue(data.field1, values["field1"])
        self.assertTrue(data.field2, values["field2"])

    async def test_schema_missing_fields(self):
        class TestSchema(Schema):
            field1: str
            field2: str

        try:
            await TestSchema.load({"anything": "else"})
        except InvalidSchema as error:
            self.assertTrue(len(error.errors), 2)

    def test_schema_correctly_identifying_fields(self):
        class TestSchema(Schema):
            field1: str
            field2: str

        self.assertIsInstance(TestSchema._fields[0], fields.String)
        self.assertIsInstance(TestSchema._fields[1], fields.String)

    async def test_schema_after_load_hook(self):
        mock = Mock()

        class TestSchema(Schema):
            field1: str = fields.String(default="1")

            # noinspection PyMethodMayBeStatic
            async def after_load(self):
                mock()

        await TestSchema.load({})
        self.assertTrue(mock.called)

    async def test_schema_calling_validators(self):
        mock, mock2 = MagicMock(), MagicMock()

        class TestSchema(Schema):
            field1: str = fields.String(validators=[lambda x: mock(x), lambda x: mock2(x)])

        value = "test_value"
        await TestSchema.load({"field1": value})
        self.assertEqual(mock.call_args[0][0], value)
        self.assertEqual(mock2.call_args[0][0], value)
        self.assertTrue(mock.called)
        self.assertTrue(mock2.called)

    async def test_schema_handling_validators_exception(self):
        def validator(*args):
            assert args is not None
            raise ValidationError("Test")

        class TestSchema(Schema):
            field1: str = fields.String(validators=[validator])

        try:
            await TestSchema.load({"field1": "123"})
            self.fail("Load() must a raise a function with invalid values.")
        except InvalidSchema as error:
            self.assertEqual(error.errors, {"field1": [{"msg": "Test", "error_code": 0}]})

    async def test_empty_schema(self):
        class TestSchema(Schema):
            pass

        try:
            await TestSchema.load({})
        except Exception as error:
            print(error)
            self.fail("An empty schema should be valid although rarely useful.")

    async def test_load_from_with_two_fields(self):
        class TestSchema(Schema):
            field1: str = fields.String(load_from="special_field")
            field2: str = fields.String(load_from="special_field_2")

        values = {"special_field": "test", "special_field_2": "test2"}
        schema = await TestSchema.load(values)
        self.assertEqual(schema.field1, values["special_field"])
        self.assertEqual(schema.field2, values["special_field_2"])

    async def test_load_from_same_field(self):
        class TestSchema(Schema):
            field1: str = fields.String(load_from="special_field")
            field2: str = fields.String(load_from="special_field")

        values = {"special_field": "test"}
        schema = await TestSchema.load(values)
        self.assertEqual(schema.field1, values["special_field"])
        self.assertEqual(schema.field2, values["special_field"])

    async def test_context_errors_properly_populated(self):
        class TestSchema(Schema):
            field1: str
            field2: str = fields.String(required=False)
            field3: str

        try:
            await TestSchema.load({"field2": "test"})
        except InvalidSchema as error:
            self.assertDictEqual(
                error.errors,
                {
                    "field1": [
                        {
                            "error_code": Messages.MISSING_REQUIRED_FIELD,
                            "msg": EnglishLanguage[Messages.MISSING_REQUIRED_FIELD],
                        }
                    ],
                    "field3": [
                        {
                            "error_code": Messages.MISSING_REQUIRED_FIELD,
                            "msg": EnglishLanguage[Messages.MISSING_REQUIRED_FIELD],
                        }
                    ],
                },
            )

    async def test_custom_language_with_new_error_code(self):
        class NewMessages(Messages):
            TEST = 100

        new_language = EnglishLanguage.copy()

        def new_message(context: dict):
            return "{}".format(str(context["custom_attribute"]))

        new_language[NewMessages.TEST] = new_message

        def validator():
            raise ValidationError(NewMessages.TEST, custom_attribute="Something custom.")

        class TestSchema(Schema):
            field1: str = fields.String(validators=[validator])

        try:
            await TestSchema.load({"field1": "test"}, language=new_language)
        except InvalidSchema as error:
            self.assertDictEqual(error.errors, {"field1": [{"error_code": 100, "msg": "Something custom."}]})

    async def test_schema_calling_builtin_validator(self):
        class TestSchema(Schema):
            field1: str = fields.String(validators=[Length(min=1)])

        try:
            await TestSchema.load({"field1": ""})
            self.fail("Schema failed to call length validator.")
        except InvalidSchema:
            pass
