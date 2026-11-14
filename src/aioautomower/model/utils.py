"""Helper utils for Automower Connect API."""

from datetime import UTC, date, datetime

from aioautomower import tz_util

SERIAL_NUMBER_LENGTH = 9


def convert_timestamp_to_aware_datetime(timestamp: int) -> datetime | None:
    """Convert the timestamp to an aware datetime object.

    The Python datetime library expects timestamps to be anchored in UTC,
    however, the automower timestamps are anchored in local time. So we convert
    the timestamp to a datetime and replace the timezone with the local time.
    After that we convert the timezone to UTC.
    """
    if timestamp == 0:
        return None
    if timestamp > 32503680000:
        # This will break on January 1th 3000. If mankind still exists there
        # please fix it.
        return datetime.fromtimestamp(timestamp / 1000, tz=UTC).replace(
            tzinfo=tz_util.MOWER_TIME_ZONE
        )
    return datetime.fromtimestamp(timestamp, tz=UTC).replace(
        tzinfo=tz_util.MOWER_TIME_ZONE
    )


def decode_manufacture_date(serial_number: str | int) -> date | None:
    """Decode the manufacture date from a 9-digit YYWWNNNNN serial number.

    Only the year (YY) and ISO week (WW) are encoded, so the Monday of that ISO
    week is returned. The API delivers the serial number as an integer, so it is
    converted to a string first. Returns None if the serial number is not nine
    digits or the ISO week does not exist in that year (e.g. week 53 in 2021).
    """
    serial = str(serial_number)
    if len(serial) != SERIAL_NUMBER_LENGTH or not serial.isdigit():
        return None
    try:
        return date.fromisocalendar(2000 + int(serial[:2]), int(serial[2:4]), 1)
    except ValueError:
        return None
