class URL:
    def __init__(
        self,
        schema: bytes,
        host: bytes,
        port,
        path: bytes,
        query: bytes,
        fragment: bytes,
        userinfo: bytes,
    ):
        self.schema = schema.decode("utf-8")
        self.host = host.decode("utf-8")
        self.port = port if port else 80
        self.path = path.decode("utf-8")
        self.query = query.decode("utf-8")
        self.fragment = fragment.decode("utf-8")
        self.userinfo = userinfo.decode("utf-8")
        self.netloc = self.schema + "://" + self.host + self.port

    def __repr__(self):
        return (
            "<URL schema: {!r}, host: {!r}, port: {!r}, path: {!r}, "
            "query: {!r}, fragment: {!r}, userinfo: {!r}>".format(
                self.schema,
                self.host,
                self.port,
                self.path,
                self.query,
                self.fragment,
                self.userinfo,
            )
        )
