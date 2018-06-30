from ..exceptions import ValidationError, NestedValidationError
from ..messages import Messages
from .validator cimport Validator


cdef class Field:
    def __init__(self, bint required=True, object default=None, list validators=None,
                 bint strict=False, str load_from=None):
        self.validators = validators or []
        self.strict = strict
        self.is_async = False
        self.load_from = load_from
        self.load_into = None
        self.default = default
        self.required = required if default is None else False
        self.default_callable = callable(self.default)

    cdef load(self, value):
        return value

    async def pipeline(self, value, context: dict):
        """

        :param context:
        :param value:
        :return:
        """
        value = self.load(value)
        if self.validators:
            await self._call_validators(value, context)
        return value

    cdef sync_pipeline(self, value, dict context):
        """

        :param context:
        :param value:
        :return:
        """
        value = self.load(value)
        if self.validators:
            self._call_sync_validators(value, context)
        return value

    async def _call_validators(self, value, context: dict):
        """

        :param value:
        :param context:
        :return:
        """
        cdef Validator validator
        for validator in self.validators:
            if validator.is_async:
                await validator.validate(value, context)
            else:
                validator.validate(value, context)

    cdef _call_sync_validators(self, value, context: dict):
        """

        :param value:
        :param context:
        :return:
        """
        cdef Validator validator
        for validator in self.validators:
            validator.validate(value, context)


cdef class String(Field):

    cdef load(self, value):
        """

        :param value:
        :return:
        """
        if isinstance(value, str):
            return value
        elif self.strict and not isinstance(value, (int, float)):
            raise ValidationError(error_code=Messages.MUST_BE_STRING)
        return str(value)


cdef class Integer(Field):

    cdef load(self, value):
        """

        :param value:
        :return:
        """
        if isinstance(value, int):
            return value
        elif self.strict and not isinstance(value, (str, float)):
            raise ValidationError(error_code=Messages.MUST_BE_INTEGER, field=self.load_from)
        try:
            return int(value)
        except ValueError:
            raise ValidationError(error_code=Messages.MUST_BE_INTEGER, field=self.load_from)


cdef class Number(Field):

    cdef load(self, value):
        """

        :param value:
        :return:
        """
        if isinstance(value, int):
            return value
        elif self.strict:
            raise ValidationError(error_code=Messages.MUST_BE_NUMBER, field=self.load_from)
        try:
            return float(value)
        except ValueError:
            raise ValidationError(error_code=Messages.MUST_BE_NUMBER, field=self.load_from)


cdef class List(Field):

    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field

    async def pipeline(self, value, context):
        """

        :param value:
        :return:
        """
        if not isinstance(value, list):
            raise ValidationError(Messages.MUST_BE_LIST)
        processed_list = []
        for index, item in enumerate(value):
            try:
                if self.field.is_async:
                    processed_list.append(await self.field.async_pipeline(item))
                else:
                    processed_list.append(self.field.pipeline(item))
            except ValidationError as error:
                raise ValidationError(f'{index}º element: {error.msg}', field=self.load_from)
        value = processed_list
        if self.validators:
            await self._call_validators(value, context)
        return value


cdef class Nested(Field):

    def __init__(self, schema, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema

    async def pipeline(self, value, context: dict):
        """

        :param context:
        :param value:
        :return:
        """
        if not isinstance(value, dict):
            raise ValidationError(error_code=Messages.MUST_BE_DICT, field=self.load_from)
        nested_context = await self.schema.load(value, silent=True)
        if nested_context.errors:
            raise NestedValidationError(context=nested_context.context)
        value = nested_context.data
        if self.validators:
            await self._call_validators(value, context)
        return value

    cdef sync_pipeline(self, value, dict context):
        """

        :param context:
        :param value:
        :return:
        """
        if not isinstance(value, dict):
            raise ValidationError(error_code=Messages.MUST_BE_DICT, field=self.load_from)
        nested_context = self.schema.load(value, silent=True)
        if nested_context.errors:
            raise NestedValidationError(context=nested_context.context)
        value = nested_context.data
        if self.validators:
            self._call_validators(value, context)
        return value
