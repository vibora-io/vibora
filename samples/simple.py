import time
from vibora import Vibora, Response


app = Vibora()


@app.route('/', cache=False)
async def home():
    return Response(str(time.time()).encode())


if __name__ == '__main__':
    app.run(debug=False, port=8000)
