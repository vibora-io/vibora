__all__ = ('HttpParserError',
           'HttpParserCallbackError',
           'HttpParserInvalidStatusError',
           'HttpParserInvalidMethodError',
           'HttpParserInvalidURLError',
           'HttpParserUpgrade',
           'BodyLimitError',
           'HeadersLimitError')


class HttpParserError(Exception):
    pass


class HttpParserCallbackError(HttpParserError):
    pass


class HttpParserInvalidStatusError(HttpParserError):
    pass


class HttpParserInvalidMethodError(HttpParserError):
    pass


class HttpParserInvalidURLError(HttpParserError):
    pass


class BodyLimitError(HttpParserError):
    pass


class HeadersLimitError(HttpParserError):
    pass


class HttpParserUpgrade(Exception):
    pass
