"""Test automower session."""

import re
import zoneinfo
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError, WSServerHandshakeError
from aiointercept import aiointercept

from aioautomower.const import API_BASE_URL, AUTH_HEADER_FMT, WS_URL
from aioautomower.exceptions import (
    ApiBadRequestError,
    ApiError,
    ApiForbiddenError,
    ApiUnauthorizedError,
    AuthError,
    HusqvarnaWSClientError,
    HusqvarnaWSServerHandshakeError,
)
from aioautomower.model_input import MowerDataResponse
from aioautomower.session import AutomowerEndpoint, AutomowerSession

from . import load_fixture_json, setup_connection
from .const import MOWER_ID, STAY_OUT_ZONE_ID_SPRING_FLOWERS


async def test_get_status_400(
    responses: aiointercept,
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
        match=re.escape(
            "400, message='Bad Request', url='https://api.amc.husqvarna.dev/v1/mowers/'"
        ),
    ):
        await aio_client.get_status()


async def test_get_status_401(
    responses: aiointercept,
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
        match=re.escape(
            "401, message='Unauthorized', url='https://api.amc.husqvarna.dev/v1/mowers/'",
        ),
    ):
        await aio_client.get_status()


async def test_get_status_402(
    responses: aiointercept,
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
        match=re.escape(
            "403, message='Forbidden', url='https://api.amc.husqvarna.dev/v1/mowers/'",
        ),
    ):
        await aio_client.get_status()


async def test_get_status_with_error_handling(
    responses: aiointercept,
    aio_client: AutomowerSession,
) -> None:
    """Test get status with error handling code covered."""
    # aiointercept models response errors as HTTP responses.
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=500,
        payload={"error": {"status": "500", "message": "Internal Server Error"}},
    )

    with pytest.raises(ApiError, match="Internal Server Error"):
        await aio_client.get_status()

    # aiointercept uses a dropped connection to raise ClientConnectionError.
    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        exception=True,
    )
    with pytest.raises(ApiError, match="Server disconnected"):
        await aio_client.get_status()


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_get_json_functional(
    aio_client: AutomowerSession,
    high_feature_mower_data: dict,
) -> None:
    """Test get json functional."""
    url = f"{API_BASE_URL}/{AutomowerEndpoint.mowers}"

    async with aiointercept(mock_external_urls=True) as mocked:
        mocked.get(url, payload=high_feature_mower_data)

        result = await aio_client.auth.get_json(url)

    assert isinstance(result, dict)
    assert "data" in result


async def test_patch_request_success(
    responses: aiointercept,
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
    responses: aiointercept,
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


async def test_process_json_response_errors(aio_client: AutomowerSession) -> None:
    """Test JSON-response parsing errors."""
    invalid_json = MagicMock()
    invalid_json.read = AsyncMock(return_value=b"not json")
    with pytest.raises(ApiError):
        await aio_client.auth._process_json_response(invalid_json)

    non_object = MagicMock()
    non_object.read = AsyncMock(return_value=b"[]")
    with pytest.raises(ApiError):
        await aio_client.auth._process_json_response(non_object)

    failed_read = MagicMock()
    failed_read.read = AsyncMock(side_effect=ClientError("read failed"))
    with pytest.raises(ApiError, match="read failed"):
        await aio_client.auth._process_json_response(failed_read)


@pytest.mark.parametrize("method", ["post", "patch"])
async def test_request_errors_are_wrapped(
    aio_client: AutomowerSession, method: str
) -> None:
    """Test that request errors are wrapped by all HTTP helpers."""
    with (
        patch.object(
            aio_client.auth,
            "request",
            new_callable=AsyncMock,
            side_effect=ClientError("request failed"),
        ),
        pytest.raises(ApiError, match="request failed"),
    ):
        await getattr(aio_client.auth, method)("endpoint")


async def test_access_token_error_is_wrapped(aio_client: AutomowerSession) -> None:
    """Test access-token request errors."""
    with (
        patch.object(
            aio_client.auth,
            "async_get_access_token",
            new_callable=AsyncMock,
            side_effect=ClientError("token failed"),
        ),
        pytest.raises(AuthError, match="token failed"),
    ):
        await aio_client.auth._async_get_access_token()


async def test_error_detail_handles_client_error(aio_client: AutomowerSession) -> None:
    """Test error-detail parsing failures."""
    response = MagicMock(status=500)
    response.json = AsyncMock(side_effect=ClientError("invalid response"))

    assert await aio_client.auth._error_detail(response) == []


async def test_raise_for_status_wraps_client_error(
    aio_client: AutomowerSession,
) -> None:
    """Test generic client errors from response status handling."""
    response = MagicMock(status=200)
    response.raise_for_status.side_effect = ClientError("status failed")

    with pytest.raises(ApiError, match="status failed"):
        await aio_client.auth._raise_for_status(response)


async def test_websocket_connect_errors(aio_client: AutomowerSession) -> None:
    """Test websocket connection errors."""
    with (
        patch.object(
            aio_client.auth._websession,
            "ws_connect",
            new_callable=AsyncMock,
            side_effect=WSServerHandshakeError(None, (), status=401, message="denied"),
        ),
        pytest.raises(HusqvarnaWSServerHandshakeError),
    ):
        await aio_client.auth.websocket_connect()

    with (
        patch.object(
            aio_client.auth._websession,
            "ws_connect",
            new_callable=AsyncMock,
            side_effect=ClientError("connection failed"),
        ),
        pytest.raises(HusqvarnaWSClientError, match="connection failed"),
    ):
        await aio_client.auth.websocket_connect()


async def test_websocket_close(aio_client: AutomowerSession) -> None:
    """Test successful and failed websocket closure."""
    aio_client.auth.ws = AsyncMock()
    await aio_client.auth.websocket_close()
    assert aio_client.auth.ws is None

    failed_ws = AsyncMock()
    failed_ws.close.side_effect = ClientError("close failed")
    aio_client.auth.ws = failed_ws
    with pytest.raises(HusqvarnaWSClientError, match="close failed"):
        await aio_client.auth.websocket_close()
    assert aio_client.auth.ws is None
