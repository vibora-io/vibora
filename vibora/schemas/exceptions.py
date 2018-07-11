from vibora.utils import json


class ValidationError(Exception):
    def __init__(self, msg=None, field=None, error_code: int = 0, **extra):
        self.msg = msg
        self.field = field
        self.extra = extra
        self.error_code = error_code
        super().__init__(str(msg))


class NestedValidationError(Exception):
    def __init__(self, context):
        self.context = context
        super().__init__()


class InvalidSchema(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__("Invalid schema: " + json.dumps(errors))
