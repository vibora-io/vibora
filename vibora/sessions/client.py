import ujson
from .base import SessionEngine, Session
from cryptography.fernet import Fernet


class EncryptedCookiesEngine(SessionEngine):
    def __init__(self, cookie_name='vibora', secret_key=None):
        super().__init__()
        self.cookie_name = cookie_name
        self.cipher = Fernet(secret_key or Fernet.generate_key())

    def load_cookie(self, request):
        cookie = request.cookies.get(self.cookie_name)
        if cookie:
            try:
                return self.cipher.decrypt(cookie.encode())
            except (AttributeError, ValueError):
                pass

    def load(self, request):
        cookie = self.load_cookie(request)
        if cookie:
            try:
                return Session(ujson.loads(cookie))
            except ValueError:
                # In this case, the user has an invalid session.
                # Probably a malicious user or app update.
                return Session(needs_update=True)
        return Session()

    def save(self, request, response):
        value = self.cipher.encrypt(request.session.dumps().encode())
        cookie = f'{self.cookie_name}={value.decode()}; SameSite=Lax'
        response.headers['Set-Cookie'] = cookie
