"""Helper for Husqvarna Automower."""

# As I can't import Calendar and Event directly in HomeAssistant,
# because it's making tests fail I import it here. Be aware of the LICENSE:
# https://github.com/allenporter/ical/blob/64380cefb6942f75e76d725d1cf01ee39fe63b43/LICENSE
# Source code can be found here: https://github.com/allenporter/ical/

from ical.calendar import Calendar
from ical.event import Event
from ical.types.recur import Recur


class AutomowerCalendar(Calendar):
    """Copy of ical.calendar."""


class AutomowerEvent(Event):
    """Copy of ical.event."""


class AutomowerRecur(Recur):
    """Copy of ical.types.recur."""
