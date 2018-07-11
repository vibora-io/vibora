import pytest
from vibora import client
from vibora.client.exceptions import MissingSchema

pytestmark = pytest.mark.asyncio


async def test_form_and_body_combined__expects_exception():
    try:
        await client.post("http://google.com", form={}, body=b"")
        raise Exception("Failed to prevent the user from doing wrong params combination.")
    except ValueError:
        pass


async def test_form_and_json_combined__expects_exception():
    try:
        await client.post("http://google.com", form={}, json={})
        raise Exception("Failed to prevent the user from doing wrong params combination.")
    except ValueError:
        pass


async def test_body_and_json_combined__expects_exception():
    try:
        await client.post("http://google.com", body=b"", json={})
        raise Exception("Failed to prevent the user from doing wrong params combination.")
    except ValueError:
        pass


async def test_missing_schema_url__expects_missing_schema_exception():
    try:
        await client.get("google.com")
        raise Exception("Missing schema exception not raised.")
    except MissingSchema:
        pass
