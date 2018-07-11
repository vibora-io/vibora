class Messages:
    MISSING_REQUIRED_FIELD = 1
    MUST_BE_STRING = 2
    MUST_BE_INTEGER = 3
    MUST_BE_NUMBER = 4
    MUST_BE_LIST = 5
    MUST_BE_DICT = 6
    MINIMUM_LENGTH = 7
    MAXIMUM_LENGTH = 8


EnglishLanguage = {
    Messages.MISSING_REQUIRED_FIELD: "Missing required field",
    Messages.MUST_BE_STRING: "Must be a string",
    Messages.MUST_BE_INTEGER: "Must be a valid integer",
    Messages.MUST_BE_NUMBER: "Must be a valid number",
    Messages.MUST_BE_LIST: "Must be a list",
    Messages.MUST_BE_DICT: "Must be a map",
    Messages.MINIMUM_LENGTH: "At least {minimum_value} character(s).",
    Messages.MAXIMUM_LENGTH: "Maximum of {maximum_value} of character(s).",
}
