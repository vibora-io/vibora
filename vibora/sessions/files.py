import uuid
import os
from .base import Session, SessionEngine
from ..utils import json


class FilesSessionEngine(SessionEngine):
    def __init__(self, storage_path: str, cookie_name: str = "SESSION_ID"):
        super().__init__(cookie_name=cookie_name)
        self.storage_path = storage_path
        try:
            os.mkdir(self.storage_path)
        except FileExistsError:
            pass
        self.cookie_name = cookie_name

    async def load(self, cookies) -> Session:
        """

        :param cookies:
        :return:
        """
        session_id = cookies.get(self.cookie_name)
        if session_id:
            try:
                with open(os.path.join(self.storage_path, session_id)) as f:
                    values = json.loads(f.read())
                    return Session(values, unique_id=session_id)
            except FileNotFoundError:
                pass
        return Session(unique_id=str(uuid.uuid4()))

    async def save(self, session: Session, response):
        """

        :param session:
        :param response:
        :return:
        """
        with open(os.path.join(self.storage_path, session.uuid), "w") as f:
            f.write(session.dumps())
        cookie = f"{self.cookie_name}={session.uuid}; SameSite=Lax"
        response.headers["Set-Cookie"] = cookie
