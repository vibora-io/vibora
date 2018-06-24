from cryptography.fernet import Fernet
from vibora import Vibora, JsonResponse, Request
from vibora.hooks import Events
from vibora.sessions.client import EncryptedCookiesEngine


app = Vibora()


@app.handle(Events.BEFORE_SERVER_START)
async def set_up_sessions(current_app: Vibora):
    # In this example every time the server is restart a new key will be generated, which means
    # you lose all your sessions... you may want to have a fixed key instead.
    current_app.session_engine = EncryptedCookiesEngine(
        'cookie_name', secret_key=Fernet.generate_key()
    )


@app.route('/')
async def home(request: Request):
    session = await request.session()
    if 'requests_count' in session:
        session['requests_count'] += 1
    else:
        session['requests_count'] = 0
    return JsonResponse({'a': 1, 'session': session.dump()})


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
