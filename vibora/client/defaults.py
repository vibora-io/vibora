from .retries import RetryStrategy


class ClientDefaults:
    TIMEOUT = 30
    HEADERS = {
        "User-Agent": "Vibora",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate",
    }
    RETRY_STRATEGY = RetryStrategy()
