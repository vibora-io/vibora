class ServerLimits:

    __slots__ = (
        "worker_timeout",
        "keep_alive_timeout",
        "response_timeout",
        "max_body_size",
        "max_headers_size",
        "write_buffer",
    )

    def __init__(
        self,
        worker_timeout: int = 60,
        keep_alive_timeout: int = 30,
        max_headers_size: int = 1024 * 10,
        write_buffer: int = 419430,
    ):
        """

        :param worker_timeout:
        :param keep_alive_timeout:
        :param max_headers_size:
        """
        self.worker_timeout = worker_timeout
        self.keep_alive_timeout = keep_alive_timeout
        self.max_headers_size = max_headers_size
        self.write_buffer = write_buffer


class RouteLimits:

    __slots__ = ("timeout", "max_body_size", "in_memory_threshold")

    def __init__(
        self,
        max_body_size: int = 1 * 1024 * 1024,
        timeout: int = 30,
        in_memory_threshold: int = 1 * 1024 * 1024,
    ):
        """

        :param max_body_size:
        :param timeout:
        """
        self.max_body_size = max_body_size
        self.timeout = timeout
        self.in_memory_threshold = in_memory_threshold
