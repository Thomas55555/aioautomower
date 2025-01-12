"""Helper utils for Automower Connect API."""

from datetime import UTC, datetime

from aioautomower import tz_util


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
