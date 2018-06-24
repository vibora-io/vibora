import asyncio_redis
from vibora import Vibora
from vibora.hooks import Events
from vibora.sessions import AsyncRedis
from vibora.responses import Response


app = Vibora(
    sessions=AsyncRedis()
)


@app.route('/', cache=False)
async def home(request):
    print(request.session.dump())
    await request.load_session()
    if request.session.get('count') is None:
        request.session['count'] = 0
    request.session['count'] += 1
    return Response(str(request.session['count']).encode())


@app.handle(Events.BEFORE_SERVER_START)
async def open_connections(loop):
    pool = await asyncio_redis.Pool.create(host='localhost', port=6379, poolsize=10)
    app.session_engine.connection = pool


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0', workers=6)
