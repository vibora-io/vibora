from vibora import Vibora


app = Vibora()

t = [x for x in range(0, 5)]


@app.route('/')
async def home():
    return await app.render('index.html', teste=t)


if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0', workers=6)
