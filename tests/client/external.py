import pytest
from vibora import client

pytestmark = pytest.mark.asyncio


async def test_simple_get_google__expects_successful():
    response = await client.get("https://google.com/")
    assert response.status_code == 200


async def test_simple_get_google_https__expects_successful():
    response = await client.get("https://google.com/")
    assert response.status_code == 200
