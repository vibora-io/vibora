

class HTTPClientError(Exception):
    pass


class TooManyRedirects(HTTPClientError):
    pass


class StreamAlreadyConsumed(HTTPClientError):
    pass


class TooManyConnections(HTTPClientError):
    pass


class RequestTimeout(HTTPClientError):
    pass


class TooManyInvalidResponses(HTTPClientError):
    pass


class MissingSchema(HTTPClientError):
    pass
