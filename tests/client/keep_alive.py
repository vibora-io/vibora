from vibora.tests import TestSuite
from vibora import Vibora
from vibora.client import Session
from vibora.utils import wait_server_offline


class KeepAliveTestCase(TestSuite):

    async def test_connection_pool_recycling_connections(self):
        v = Vibora()
        address, port = '127.0.0.1', 65530
        async with Session(prefix=f'http://{address}:{port}', timeout=3, keep_alive=True) as client:
            v.run(host=address, port=port, block=False, necromancer=False, workers=1, debug=False,
                  startup_message=False)
            self.assertEqual((await client.get('/')).status_code, 404)
            v.clean_up()
            wait_server_offline(address, port, timeout=30)
            v.run(host=address, port=port, block=False, necromancer=False, workers=1, debug=False,
                  startup_message=False)
            self.assertEqual((await client.get('/')).status_code, 404)
