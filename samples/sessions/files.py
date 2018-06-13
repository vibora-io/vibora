from vibora import Vibora
from vibora.request import Request
from vibora.responses import JsonResponse


app = Vibora()


@app.route('/', cache=False)
def home(request: Request):
    if 'requests_count' in request.session:
        request.session['requests_count'] += 1
    else:
        request.session['requests_count'] = 0
    return JsonResponse({'a': 1, 'session': request.session.dump()})


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
