from typing import Coroutine, Any
from .session import Session
from .response import Response
from .retries import RetryStrategy

__default_session = Session(keep_alive=False)


async def get(url: str = '', stream: bool = False, follow_redirects: bool = True, max_redirects: int = 30,
              decode: bool = True, ssl=None, timeout=None, retries: Session = None,
              headers: dict = None, query: dict = None,
              ignore_prefix: bool = False) -> Response:
    return await __default_session.request(url=url, stream=stream, follow_redirects=follow_redirects,
                                           max_redirects=max_redirects, decode=decode, ssl=ssl,
                                           retries=retries, headers=headers, timeout=timeout, method='GET', query=query,
                                           ignore_prefix=ignore_prefix)


async def post(url: str = '', stream: bool = False, follow_redirects: bool = True, max_redirects: int = 30,
               decode: bool = True, validate_ssl=None, timeout=None, retries: RetryStrategy = None,
               headers: dict = None, query: dict = None, body=None, form=None, json=None,
               ignore_prefix: bool = False) -> Response:
    return await __default_session.request(url=url, stream=stream, follow_redirects=follow_redirects,
                                           max_redirects=max_redirects, decode=decode, ssl=validate_ssl,
                                           retries=retries, headers=headers, timeout=timeout, method='POST',
                                           query=query,
                                           ignore_prefix=ignore_prefix, body=body, form=form, json=json)
