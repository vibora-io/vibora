import ujson
from typing import Optional
from .base import SessionEngine, Session

try:
    from cryptography.fernet import Fernet
except ImportError:
    raise ImportError(
        "To use encrypted sessions you need to install the cryptography library or implement your own "
        "engine by extending the SessionEngine class."
    )


class EncryptedCookiesEngine(SessionEngine):
    def __init__(self, cookie_name="vibora", secret_key=None):
        super().__init__(cookie_name=cookie_name)
        self.cipher = Fernet(secret_key)

    def load_cookie(self, request) -> Optional[str]:
        """

        :param request:
        :return:
        """
        cookie = request.cookies.get(self.cookie_name)
        if cookie:
            try:
                return self.cipher.decrypt(cookie.encode())
            except (AttributeError, ValueError):
                pass

    async def load(self, request) -> Session:
        """

        :param request:
        :return:
        """
        cookie = self.load_cookie(request)
        if cookie:
            try:
                return Session(ujson.loads(cookie))
            except ValueError:
                # In this case, the user has an invalid session.
                # Probably a malicious user or secret key update.
                return Session(pending_flush=True)
        return Session()

    async def save(self, request, response) -> None:
        """
        Inject headers in the response object so the user will receive
        an encrypted cookie with session values.
        :param request: current Request object
        :param response: current Response object where headers will be inject.
        :return:
        """
        value = self.cipher.encrypt(request.session.dumps().encode())
        cookie = f"{self.cookie_name}={value.decode()}; SameSite=Lax"
        response.headers["Set-Cookie"] = cookie
