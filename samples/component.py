from vibora import Vibora
from vibora.request import Request
from vibora.responses import JsonResponse
from vibora.context import get_component


class Config:
    def __init__(self):
        self.port = 123


class Request2(Request):
    @property
    def config(self) -> Config:
        return get_component(Config)


app = Vibora()


@app.route("/", cache=False)
def home(request: Request2):
    return JsonResponse({"port": request.config.port}, headers={"1": "1"})


if __name__ == "__main__":
    config = Config()
    app.request_class = Request2
    app.run(debug=False, port=8000, host="0.0.0.0")
