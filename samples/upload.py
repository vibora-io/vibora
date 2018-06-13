from vibora import Vibora
from vibora.responses import Response
from vibora.request import Request


app = Vibora()


@app.route('/', methods=['POST'])
def home(request: Request):
    print(request.form)
    return Response(b'asd')


if __name__ == '__main__':
    app.run(debug=False, port=8000, host='localhost')
