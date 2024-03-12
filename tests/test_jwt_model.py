"""Tests for asynchronous Python client for aioautomower."""

from dataclasses import fields
import json

from aioautomower.utils import structure_token
from tests import load_fixture

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_decode_token() -> None:
    """Test converting a low feature mower."""
    token_fixture = load_fixture("jwt.json")
    token_python = json.loads(token_fixture)
    token_structered = structure_token(token_python["data"])
    assert token_structered.scope == "iam:read amc:api"
    assert token_structered.client_id == "433e5fdf-5129-452c-xxxx-fadce3213042"
    assert token_structered.user.first_name == "Erika"
    assert token_structered.user.last_name == "Mustermann"


async def test_jwt_snapshot(snapshot):
    """Testing a snapshot of a JWT."""
    token_fixture = load_fixture("jwt.json")
    token_python = json.loads(token_fixture)
    token_structered = structure_token(token_python["data"])
    for field in fields(token_structered):
        field_name = field.name
        field_value = getattr(token_structered, field_name)
        assert field_value == snapshot(name=f"{field_name}")
