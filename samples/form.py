from vibora import Vibora
from vibora.request import Request
from vibora.responses import JsonResponse
from vibora.static import StaticHandler


app = Vibora(
    static=StaticHandler(['/tmp'], url_prefix='/static')
)


@app.route('/', methods=['POST'])
async def home(request: Request):
    print(await request.form())
    return JsonResponse({'hello': 'world', 'form': str(request.form)})


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
