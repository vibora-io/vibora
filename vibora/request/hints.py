####################################################################################################
# === Warning ===
# This is a file stub to provide type hints to the Request object because it's a pure cython module.
####################################################################################################
from ..headers import Headers
from ..multipart import UploadedFile
from ..sessions import Session
from typing import List, Callable


class Request:

    def __init__(self, url: bytes, headers: Headers, method: bytes, stream, protocol):
        self.url = url
        self.headers = headers
        self.method = method
        self.stream = stream
        self.protocol = protocol
        self.cookies: dict = {}
        self.args: dict = {}
        self.context: dict = {}

    def client_ip(self) -> str:
        """

        :return:
        """
        pass

    def session_pending_flush(self) -> bool:
        """

        :return:
        """
        pass

    async def form(self) -> dict:
        """

        :return:
        """
        pass

    async def files(self) -> List[UploadedFile]:
        """

        :return:
        """
        pass

    async def _load_form(self) -> None:
        """

        :return:
        """
        pass

    async def json(self, loads: Callable=None, strict: bool = False) -> dict:
        """

        :param loads:
        :param strict:
        :return:
        """
        pass

    async def session(self) -> Session:
        """

        :return:
        """
        pass
