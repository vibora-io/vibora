import uuid
import os
from tempfile import TemporaryDirectory
from .base import Session, SessionEngine
from ..utils import json


class FilesSessionEngine(SessionEngine):
    def __init__(self, cookie_name='vibora', storage_path=None):
        super().__init__()
        if storage_path is None:
            self.temporary_directory = TemporaryDirectory()
            self.storage_path = self.temporary_directory.name
        else:
            self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            try:
                os.mkdir(self.storage_path)
            except FileExistsError:
                pass
        self.cookie_name = cookie_name

    def load(self, request) -> Session:
        session_id = request.cookies.get(self.cookie_name)
        if session_id:
            try:
                with open(os.path.join(self.storage_path, session_id)) as f:
                    values = json.loads(f.read())
                    return Session(values, unique_id=session_id)
            except FileNotFoundError:
                pass
        return Session(unique_id=str(uuid.uuid4()))

    def save(self, request, response):
        with open(os.path.join(self.storage_path, request.session.uuid), 'w') as f:
            f.write(request.session.dumps())
        cookie = f'{self.cookie_name}={request.session.uuid}; SameSite=Lax'
        response.headers['Set-Cookie'] = cookie

    def clean_up(self):
        self.temporary_directory.cleanup()
