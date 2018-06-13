from collections import defaultdict
from typing import List, Iterator


class Cookie:

    options = {
        'samesite': ('same_site', lambda x: True),
        'httponly': ('http_only', lambda x: True),
        'expires': ('expires_at', lambda x: x[1]),
        'domain': ('domain', lambda x: x[1]),
        'path': ('path', lambda x: x[1]),
        'max-age': ('max_age', lambda x: int(x[1])),
        'secure': ('secure', lambda x: True)
    }
    __slots__ = ('name', 'value', 'same_site', 'http_only', 'expires_at',
                 'path', 'domain', 'max_age', 'secure')

    def __init__(self, name: str, value: str=None, same_site=False,
                 http_only=False, expires_at=None, path: str=None,
                 domain: str=None, max_age: int=None, secure: bool=None):
        self.name = name
        self.value = value if value is not None else ''
        self.same_site = same_site
        self.http_only = http_only
        self.expires_at = expires_at
        self.path = path
        self.domain = domain
        self.max_age = max_age
        self.secure = secure

    @property
    def header(self):
        header = f'Set-Cookie: {self.name}={self.value}; '
        if self.same_site:
            header += 'SameSite; '
        if self.http_only:
            header += 'HttpOnly; '
        if self.expires_at:
            header += f'Expires={self.expires_at}; '
        if self.domain:
            header += f'Domain={self.domain}; '
        if self.path:
            header += f'Path={self.path}; '
        return header.encode()

    @classmethod
    def from_header(cls, header: str):
        instance = cls(name='')
        first = True
        for piece in header.split(';'):
            sub_pieces = piece.split('=')
            if sub_pieces[0] == '':
                continue
            if first:
                instance.name = sub_pieces[0]
                if len(sub_pieces) == 2:
                    instance.value = sub_pieces[1]
                first = False
            else:
                try:
                    attribute_name, value = cls.options[sub_pieces[0].lower().strip()]
                except KeyError as error:
                    pass
                setattr(instance, attribute_name, value(sub_pieces))
        return instance


class CookiesJar:

    __slots__ = ('cookies', )

    def __init__(self):
        self.cookies = {}

    def add_cookie(self, cookie: Cookie):
        self.cookies[cookie.name] = cookie

    def get(self, name: str):
        return self.cookies.get(name)

    def __getitem__(self, item):
        return self.cookies[item]

    def __setitem__(self, key, value):
        if not isinstance(value, Cookie):
            raise Exception('Value must be a Cookie instance.')
        self.cookies[key] = value

    def __iter__(self):
        return self.cookies.values().__iter__()

    def merge(self, newest_jar):
        for cookie_name, cookie in newest_jar.cookies.items():
            self.cookies[cookie_name] = cookie

    def __bool__(self):
        return bool(self.cookies)

    def __str__(self):
        return '<CookiesJar(' + str([x for x in self.cookies.items()]) + ')>'


class SessionCookiesJar:

    __slots__ = ('_domains',)

    def __init__(self):
        self._domains = defaultdict(CookiesJar)

    def get(self, domain: str, strict: bool=False) -> CookiesJar:
        if not strict:
            unique_jar = CookiesJar()
            for key, jar in self._domains.items():
                if key.endswith(domain):
                    unique_jar.merge(jar)
            return unique_jar
        return self._domains.get(domain)

    def add_cookie(self, cookie: Cookie):
        self._domains[cookie.domain].add_cookie(cookie)

    @property
    def cookies(self) -> Iterator:
        for jar in self._domains.values():
            for cookie in jar.cookies.values():
                yield cookie

    def merge(self, jar: CookiesJar, domain: str):
        self._domains[domain].merge(jar)
