

class RetryStrategy:

    __slots__ = ('network_failures', 'responses')

    def __init__(self, network_failures: dict = None, responses: dict = None):
        """

        :param network_failures:
        :param responses:
        """
        # Although retry an operation after an connection reset is the default behavior of browsers
        # this is dangerous with non idempotent requests because it could duplicate charges/anything
        # in a poorly implemented API.
        # This issue is not rare when using connection pooling and the server does not tell us
        # about the keep alive timeout. There is no way to guarantee that a socket is still alive so
        # you write in it and hope for the best. In case the connection is reset after your next socket read
        # you never know if the server actually received it or not.
        self.network_failures = network_failures or {'GET': 1}

        # Retry after an specific status_code is found.
        self.responses = responses or {}

    def clone(self) -> 'RetryStrategy':
        return RetryStrategy(network_failures=self.network_failures.copy(), responses=self.responses.copy())
