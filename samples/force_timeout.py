import time
from vibora import Vibora
from vibora.responses import Response
from vibora.utils import Timeouts


app = Vibora()


@app.route('/')
def home():
    time.sleep(10)
    return Response(b'123')


if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0', workers=1, timeouts=Timeouts(
        worker=5,
        keep_alive=10
    ))
