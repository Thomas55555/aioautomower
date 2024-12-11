"""Test automower session."""

import zoneinfo
from unittest.mock import AsyncMock, patch

import pytest
from aioresponses import aioresponses

from aioautomower.const import API_BASE_URL, AUTH_HEADER_FMT, WS_URL
from aioautomower.exceptions import (
    ApiBadRequestException,
    ApiForbiddenException,
    ApiUnauthorizedException,
)
from aioautomower.session import AutomowerEndpoint, AutomowerSession

from . import load_fixture_json, setup_connection
from .const import MOWER_ID, STAY_OUT_ZONE_ID_SPRING_FLOWERS


async def test_get_status_400(
    responses: aioresponses,
    automower_client: AutomowerSession,
):
    """Test get status with error."""
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=400,
        payload=load_fixture_json("error.json"),
    )
    with pytest.raises(
        ApiBadRequestException,
        match="Unable to send request with API: 400, message='Bad Request', url='https://api.amc.husqvarna.dev/v1/mowers/'",
    ):
        await automower_client.get_status()


async def test_get_status_401(
    responses: aioresponses,
    automower_client: AutomowerSession,
):
    """Test get status with error."""
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=401,
        payload=load_fixture_json("error.json"),
    )
    with pytest.raises(
        ApiUnauthorizedException,
        match="Unable to authenticate with API: 401, message='Unauthorized', url='https://api.amc.husqvarna.dev/v1/mowers/'",
    ):
        await automower_client.get_status()


async def test_get_status_402(
    responses: aioresponses,
    automower_client: AutomowerSession,
):
    """Test get status with error."""
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=403,
        payload=load_fixture_json("error.json"),
    )
    with pytest.raises(
        ApiForbiddenException,
        match="Forbidden response from API: 403, message='Forbidden', url='https://api.amc.husqvarna.dev/v1/mowers/'",
    ):
        await automower_client.get_status()


async def test_patch_request_success(
    responses: aioresponses,
    automower_client: AutomowerSession,
    control_response,
    mower_data,
    mower_tz: zoneinfo.ZoneInfo,
):
    """Test patch request success."""
    await setup_connection(responses, automower_client, mower_data, mower_tz)
    endpoint = AutomowerEndpoint.stay_out_zones.format(
        mower_id=MOWER_ID, stay_out_id=STAY_OUT_ZONE_ID_SPRING_FLOWERS
    )
    url = f"{API_BASE_URL}/{endpoint}"
    responses.patch(
        url=url,
        status=200,
        payload=control_response,
    )
    assert (
        await automower_client.commands.switch_stay_out_zone(
            MOWER_ID, STAY_OUT_ZONE_ID_SPRING_FLOWERS, True
        )
        is None
    )


async def test_post_request_success(
    responses: aioresponses,
    automower_client: AutomowerSession,
    control_response,
    mower_data,
    mower_tz: zoneinfo.ZoneInfo,
):
    """Test get status."""
    await setup_connection(responses, automower_client, mower_data, mower_tz)
    endpoint = AutomowerEndpoint.actions.format(mower_id=MOWER_ID)
    url = f"{API_BASE_URL}/{endpoint}"
    responses.post(
        url=url,
        status=200,
        payload=control_response,
    )
    assert await automower_client.commands.resume_schedule(MOWER_ID) is None


@pytest.mark.asyncio
async def test_websocket_connect(automower_client: AutomowerSession, jwt_token: str):
    """Test websocket connection."""
    with patch(
        "aiohttp.ClientSession.ws_connect", new_callable=AsyncMock
    ) as mock_ws_connect:
        mock_ws = AsyncMock()
        mock_ws_connect.return_value = mock_ws

        await automower_client.auth.websocket_connect()

        mock_ws_connect.assert_called_once_with(
            url=WS_URL,
            headers={"Authorization": AUTH_HEADER_FMT.format(jwt_token)},
            heartbeat=60,
        )
        assert automower_client.auth.ws == mock_ws
