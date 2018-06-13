import ujson
import uuid
from .base import Session, SessionEngine


class AsyncRedis(SessionEngine):
    def __init__(self, cookie_name='riven', connection=None):
        super().__init__()
        self.connection = connection
        self.cookie_name = cookie_name

    async def load(self, request) -> Session:
        session_id = request.cookies.get(self.cookie_name)
        if session_id:
            values = await self.connection.get(session_id)
            if values:
                return Session(ujson.loads(values), unique_id=session_id)
        return Session(unique_id=str(uuid.uuid4()))

    async def save(self, request, response):
        await self.connection.set(request.session.uuid, request.session.dumps())
        cookie = f'{self.cookie_name}={request.session.uuid}; SameSite=Lax'
        response.headers['Set-Cookie'] = cookie


class Redis(SessionEngine):
    def __init__(self, cookie_name='vibora', connection=None):
        super().__init__()
        self.connection = connection
        self.cookie_name = cookie_name

    def load(self, request) -> Session:
        session_id = request.cookies.get(self.cookie_name)
        if session_id:
            values = self.connection.get(session_id)
            if values:
                return Session(ujson.loads(values), unique_id=session_id)
        return Session(unique_id=str(uuid.uuid4()))

    def save(self, request, response):
        self.connection.set(request.session.uuid, request.session.dumps())
        cookie = f'{self.cookie_name}={request.session.uuid}; SameSite=Lax'
        response.headers['Set-Cookie'] = cookie
