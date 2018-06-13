

class Headers:

    def __init__(self, raw=None):
        self.raw = raw or []
        self.values = None
        self.evaluated = False

    def get(self, key, default=None):
        if not self.evaluated:
            self.eval()
        return self.values.get(key.lower()) or default

    def eval(self):
        self.values = {}
        while self.raw:
            header = self.raw.pop()
            self.values[header[0].decode('utf-8').lower()] = header[1].decode('utf-8')
        self.evaluated = True

    def dump(self):
        if not self.evaluated:
            self.eval()
        return self.values

    def parse_cookies(self) -> dict:
        header = self.get('cookie')
        cookies = {}
        if header:
            for cookie in header.split(';'):
                first = cookie.find('=')
                name = cookie[:first].strip()
                value = cookie[first + 1:]
                cookies[name] = value
        return cookies

    def __getitem__(self, item: str):
        if not self.evaluated:
            self.eval()
        return self.values[item.lower()]

    def __setitem__(self, key: str, value: str):
        if not self.evaluated:
            self.eval()
        self.values[key.lower()] = value

    def __repr__(self):
        return f'<Headers {self.dump()}>'
