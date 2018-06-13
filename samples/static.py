from vibora import Vibora
from vibora.responses import Response
from vibora.static import StaticHandler


app = Vibora(
    static=StaticHandler(paths=['/your_static_dir', '/second_static_dir'])
)


@app.route('/')
async def home():
    return Response(b'123')


if __name__ == '__main__':
    app.run(debug=False, port=8888)
