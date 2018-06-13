from vibora import Vibora
from vibora.request import Request
from vibora.responses import JsonResponse


app = Vibora()


@app.route('/')
async def home(request: Request):
    request.session['123'] = 123
    return JsonResponse({'a': 1, 'session': request.session.dump()})


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
