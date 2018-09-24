from vibora import Vibora
from vibora.responses import Response


app = Vibora()


@app.route('/')
async def home():
    return Response(b'123')


if __name__ == '__main__':
    app.run(debug=False, port=8000)
