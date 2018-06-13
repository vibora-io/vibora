from vibora import Vibora
from vibora.responses import JsonResponse
from samples.blueprints.v1.routes import v1
from samples.blueprints.v2.routes import v2


app = Vibora()


@app.route('/')
def home():
    return JsonResponse({'a': 1})


@app.handle(404)
def handle_anything():
    app.url_for('')
    return JsonResponse({'global': 'handler'})


if __name__ == '__main__':
    v1.add_blueprint(v2, prefixes={'v2': '/v2'})
    app.add_blueprint(v1, prefixes={'v1': '/v1', '': '/'})
    app.add_blueprint(v2, prefixes={'v2': '/v2'})
    app.run(debug=True, port=8000, host='0.0.0.0', workers=1)
