from vibora import Vibora, Events, Request
from vibora.responses import JsonResponse


app = Vibora()


@app.route('/', cache=False)
async def home():
    return JsonResponse({'1': 1})


@app.handle(Events.BEFORE_ENDPOINT)
async def before_endpoint(request: Request):
    request.context['1'] = 1


@app.handle(Events.AFTER_ENDPOINT)
async def after_endpoint():
    pass


if __name__ == '__main__':
    app.run(debug=False, port=8888, host='localhost')
