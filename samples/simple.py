from vibora import Vibora, Response

app = Vibora()


@app.route("/")
async def home():
    return Response(b"123")


if __name__ == "__main__":
    app.run(debug=True, port=8001)
