"""Test automower session."""

import zoneinfo
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError, ClientResponseError, RequestInfo
from aioresponses import aioresponses
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from aioautomower.const import API_BASE_URL, AUTH_HEADER_FMT, WS_URL
from aioautomower.exceptions import (
    ApiBadRequestError,
    ApiError,
    ApiForbiddenError,
    ApiUnauthorizedError,
)
from aioautomower.model_input import MowerDataResponse
from aioautomower.session import AutomowerEndpoint, AutomowerSession

from . import load_fixture_json, setup_connection
from .const import MOWER_ID, STAY_OUT_ZONE_ID_SPRING_FLOWERS


async def test_get_status_400(
    responses: aioresponses,
    aio_client: AutomowerSession,
) -> None:
    """Test get status with error."""
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=400,
        payload=load_fixture_json("error.json"),
    )
    with pytest.raises(
        ApiBadRequestError,
        match="400, message='Bad Request', url='https://api.amc.husqvarna.dev/v1/mowers/'",
    ):
        await aio_client.get_status()


async def test_get_status_401(
    responses: aioresponses,
    aio_client: AutomowerSession,
) -> None:
    """Test get status with error."""
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=401,
        payload=load_fixture_json("error.json"),
    )
    with pytest.raises(
        ApiUnauthorizedError,
        match="401, message='Unauthorized', url='https://api.amc.husqvarna.dev/v1/mowers/'",
    ):
        await aio_client.get_status()


async def test_get_status_402(
    responses: aioresponses,
    aio_client: AutomowerSession,
) -> None:
    """Test get status with error."""
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=403,
        payload=load_fixture_json("error.json"),
    )
    with pytest.raises(
        ApiForbiddenError,
        match="403, message='Forbidden', url='https://api.amc.husqvarna.dev/v1/mowers/'",
    ):
        await aio_client.get_status()


async def test_get_status_with_error_handling(
    responses: aioresponses,
    aio_client: AutomowerSession,
    jwt_token: str,
) -> None:
    """Test get status with error handling code covered."""
    request_info = RequestInfo(
        url=URL(f"{API_BASE_URL}/{AutomowerEndpoint.mowers}"),
        method="GET",
        headers=CIMultiDictProxy(
            CIMultiDict(
                {
                    "Authorization": f"Bearer {jwt_token}",
                    "Authorization-Provider": "husqvarna",
                    "Content-Type": "application/vnd.api+json",
                    "X-Api-Key": "433e5fdf-5129-452c-xxxx-fadce3213042",
                }
            )
        ),
        real_url=URL(f"{API_BASE_URL}/{AutomowerEndpoint.mowers}"),
    )

    # Simuliere ClientResponseError mit einer Nachricht
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        exception=ClientResponseError(
            request_info=request_info,
            history=(),
            status=400,
            message="Bad Request",
        ),
    )

    # Test, ob ApiError geworfen wird, wenn der Fehler in detail gespeichert wird
    with pytest.raises(ApiError, match="Bad Request"):
        await aio_client.get_status()

    # Simuliere ClientError, um den ClientError Block abzudecken
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        exception=ClientError("Client error occurred"),
    )
    with pytest.raises(ApiError, match="Client error occurred"):
        await aio_client.get_status()


async def test_patch_request_success(
    responses: aioresponses,
    aio_client: AutomowerSession,
    control_response: dict,
    mower_data: MowerDataResponse,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test patch request success."""
    await setup_connection(responses, aio_client, mower_data, mower_tz)
    endpoint = AutomowerEndpoint.stay_out_zones.format(
        mower_id=MOWER_ID, stay_out_id=STAY_OUT_ZONE_ID_SPRING_FLOWERS
    )
    url = f"{API_BASE_URL}/{endpoint}"
    responses.patch(
        url=url,
        status=200,
        payload=control_response,
    )
    await aio_client.commands.switch_stay_out_zone(
        MOWER_ID, STAY_OUT_ZONE_ID_SPRING_FLOWERS, switch=True
    )
    assert len(responses.requests) > 0


async def test_post_request_success(
    responses: aioresponses,
    aio_client: AutomowerSession,
    control_response: dict,
    mower_data: MowerDataResponse,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test get status."""
    await setup_connection(responses, aio_client, mower_data, mower_tz)
    endpoint = AutomowerEndpoint.actions.format(mower_id=MOWER_ID)
    url = f"{API_BASE_URL}/{endpoint}"
    responses.post(
        url=url,
        status=200,
        payload=control_response,
    )
    await aio_client.commands.resume_schedule(MOWER_ID)
    assert len(responses.requests) > 0


@pytest.mark.asyncio
async def test_websocket_connect(aio_client: AutomowerSession, jwt_token: str) -> None:
    """Test websocket connection."""
    with patch(
        "aiohttp.ClientSession.ws_connect", new_callable=AsyncMock
    ) as mock_ws_connect:
        mock_ws = AsyncMock()
        mock_ws_connect.return_value = mock_ws

        await aio_client.auth.websocket_connect()

        mock_ws_connect.assert_called_once_with(
            url=WS_URL,
            headers={"Authorization": AUTH_HEADER_FMT.format(jwt_token)},
            heartbeat=60,
        )
        assert aio_client.auth.ws == mock_ws
