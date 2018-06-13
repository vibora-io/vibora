import asyncio
import time
from vibora import Vibora
from vibora.responses import Response


app = Vibora()


@app.route('/', cache=False)
async def home():
    await asyncio.sleep(0)
    return Response(str(time.time()).encode())


if __name__ == '__main__':
    app.run(debug=False, port=8888)
