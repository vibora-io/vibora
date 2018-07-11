from vibora import Vibora
from vibora.websockets import WebsocketHandler

app = Vibora()


@app.websocket("/")
class ConnectedClient(WebsocketHandler):
    async def on_message(self, msg):
        print(msg)
        await self.send(msg)

    async def on_connect(self):
        print("Client connected")


if __name__ == "__main__":
    app.run()
