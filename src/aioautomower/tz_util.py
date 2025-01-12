"""Utils for Husqvarna Automower."""

import logging
from datetime import UTC, tzinfo
from functools import lru_cache

_LOGGER = logging.getLogger(__name__)

MOWER_TIME_ZONE: tzinfo = UTC


@lru_cache(maxsize=1)
def get_mower_time_zone() -> tzinfo:
    """Get the default time zone."""
    return MOWER_TIME_ZONE


def set_mower_time_zone(time_zone: tzinfo) -> None:
    """Set a default time zone to be used when none is specified.

    Async friendly.
    """
    # pylint: disable-next=global-statement
    global MOWER_TIME_ZONE  # noqa: PLW0603

    MOWER_TIME_ZONE = time_zone
    get_mower_time_zone.cache_clear()
