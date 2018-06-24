from vibora import Vibora, JsonResponse, Request
from vibora.hooks import Events
from vibora.sessions.files import FilesSessionEngine


app = Vibora()


@app.handle(Events.BEFORE_SERVER_START)
async def set_up_sessions(current_app: Vibora):
    current_app.session_engine = FilesSessionEngine('/tmp/test')


@app.route('/')
async def home(request: Request):
    session = await request.session()
    if 'requests_count' in session:
        session['requests_count'] += 1
    else:
        session['requests_count'] = 0
    return JsonResponse({'a': 1, 'session': session.dump()})


if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0')
