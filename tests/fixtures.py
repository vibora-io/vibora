import pytest
from vibora import Vibora

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="app")
async def create_app():

    _app = Vibora()

    yield _app

    _app.clean_up()
