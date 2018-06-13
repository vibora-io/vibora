from vibora import Vibora
from vibora.request import Request
from vibora.responses import Response, JsonResponse


class Config:
    def __init__(self):
        self.port = 123


class Request2(Request):
    def __init__(self, c: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = c


app = Vibora()


@app.route('/', cache=False)
def home(request: Request2):
    return JsonResponse({'a': 1}, headers={'1': '1'})


if __name__ == '__main__':
    config = Config()

    def create_request(*args, **kwargs) -> 'Request2':
        return Request2(config, *args, **kwargs)
    app.override_request(create_request)
    app.run(debug=False, port=8000, host='0.0.0.0')
