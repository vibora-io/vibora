from vibora import Vibora
from vibora.request import Request
from vibora.responses import JsonResponse

app = Vibora()


@app.route("/", methods=["POST"])
async def home(request: Request):
    await request.form()
    return JsonResponse({"hello": "world"})


if __name__ == "__main__":
    app.run(debug=False, port=8000, host="0.0.0.0")
