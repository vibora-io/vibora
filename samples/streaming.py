from vibora import Vibora
from vibora.responses import StreamingResponse

app = Vibora()


@app.route("/", methods=["GET"])
async def home():
    return StreamingResponse(b"123")


if __name__ == "__main__":
    app.run(debug=False, port=8888, host="localhost")
