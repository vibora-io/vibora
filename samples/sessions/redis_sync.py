import redis
from vibora import Vibora
from vibora.request import Request
from vibora.hooks import Events
from vibora.sessions import Redis
from vibora.responses import JsonResponse


app = Vibora(sessions=Redis())


@app.route('/')
def home(request: Request):
    if request.session.get('count') is None:
        request.session['count'] = 0
    request.session['count'] += 1
    return JsonResponse({'a': 1, 'session': request.session.dump()})


@app.route('/asd')
def home(request: Request):
    return JsonResponse({'a': 1, 'session': request.session.dump()})


@app.handle(Events.AFTER_SERVER_START)
def open_connections():
    app.session_engine.connection = redis.StrictRedis(host="localhost", port=6379, db=0)


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
