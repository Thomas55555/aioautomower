"""Utils for Husqvarna Automower."""

import logging
from datetime import UTC, tzinfo
from functools import lru_cache

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIME_ZONE: tzinfo = UTC


@lru_cache(maxsize=1)
def get_default_time_zone() -> tzinfo:
    """Get the default time zone."""
    return DEFAULT_TIME_ZONE


def set_default_time_zone(time_zone: tzinfo) -> None:
    """Set a default time zone to be used when none is specified.

    Async friendly.
    """
    # pylint: disable-next=global-statement
    global DEFAULT_TIME_ZONE  # noqa: PLW0603

    # assert isinstance(time_zone, datetime.tzinfo)

    DEFAULT_TIME_ZONE = time_zone
    get_default_time_zone.cache_clear()
