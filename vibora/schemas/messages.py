

class Messages:
    MISSING_REQUIRED_FIELD = 1
    MUST_BE_STRING = 2
    MUST_BE_INTEGER = 3
    MUST_BE_NUMBER = 4
    MUST_BE_LIST = 5
    MUST_BE_DICT = 6


EnglishLanguage = {
    Messages.MISSING_REQUIRED_FIELD: lambda x: 'Missing required field',
    Messages.MUST_BE_STRING: lambda x: 'Must be a string',
    Messages.MUST_BE_INTEGER: lambda x: 'Must be a valid integer',
    Messages.MUST_BE_NUMBER: lambda x: 'Must be a valid number',
    Messages.MUST_BE_LIST: lambda x: 'Must be a list',
    Messages.MUST_BE_DICT: lambda x: 'Must be a map'
}
