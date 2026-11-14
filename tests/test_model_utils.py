"""Tests for the Automower model utils."""

from datetime import date

import pytest

from aioautomower.model.model_system import System
from aioautomower.model.utils import decode_manufacture_date


@pytest.mark.parametrize(
    ("serial_number", "expected_result"),
    [
        pytest.param("184800801", date(2018, 11, 26), id="string_serial"),
        pytest.param(184800801, date(2018, 11, 26), id="integer_serial"),
        pytest.param("205300801", date(2020, 12, 28), id="week_53_exists"),
        pytest.param("215300801", None, id="week_53_missing"),
        pytest.param("180000801", None, id="week_zero"),
        pytest.param("185400801", None, id="week_above_53"),
        pytest.param("123", None, id="too_short_string"),
        pytest.param(123, None, id="too_short_integer"),
        pytest.param("18AB00801", None, id="non_digit_characters"),
    ],
)
def test_decode_manufacture_date(
    serial_number: str | int, expected_result: date | None
) -> None:
    """Test decoding the manufacture date from a serial number."""
    # Act
    result = decode_manufacture_date(serial_number)

    # Assert
    assert result == expected_result


def test_system_manufacture_date_from_serial_number() -> None:
    """Test the system model derives the manufacture date from the serial number."""
    # Arrange
    payload = {
        "name": "Test Mower 1",
        "model": "450XH-TEST",
        "serialNumber": 184800801,
    }

    # Act
    result = System.from_dict(payload)

    # Assert
    assert result.serial_number == "184800801"
    assert result.manufacture_date == date(2018, 11, 26)
    assert result.to_dict()["manufacture_date"] == "2018-11-26"
