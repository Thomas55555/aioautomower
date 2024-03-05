"""Utils for Husqvarna Automower."""

import logging
import time
from urllib.parse import quote_plus, urlencode
import datetime
from dataclasses import fields
import aiohttp
import jwt
from .const import AUTH_API_REVOKE_URL, AUTH_API_TOKEN_URL, AUTH_HEADERS
from .exceptions import ApiException
from .model import JWT, MowerAttributes, MowerList, Tasks, Calendar, CalendarEvent


_LOGGER = logging.getLogger(__name__)

WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


WEEKDAYS_TO_RFC5545 = {
    "monday": "MO",
    "tuesday": "TU",
    "wednesday": "WE",
    "thursday": "TH",
    "friday": "FR",
    "saturday": "SA",
    "sunday": "SU",
}


class ConvertScheduleToCalendar:
    """Convert the Husqvarna task to an CalendarEvent"""

    def __init__(self, task: Calendar) -> None:
        """Initialize the schedule to calendar converter"""
        self.task = task
        self.now = datetime.datetime.now().astimezone()
        self.begin_of_current_day = self.now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.current_day = self.now.weekday()

    # pylint: disable=inconsistent-return-statements
    def next_weekday_with_schedule(self) -> datetime.datetime:
        """Find the next weekday with a schedule entry."""
        # pylint: disable=too-many-nested-blocks
        for days in range(8):
            time_to_check = self.now + datetime.timedelta(days=days)
            time_to_check_begin_of_day = time_to_check.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_to_check = time_to_check.weekday()
            print("today:%s", self.now)
            print("day_to_check:%s", day_to_check)
            day_to_check_as_string = WEEKDAYS[day_to_check]
            print("today_as_string:%s", day_to_check_as_string)
            for field in fields(self.task):
                field_name = field.name
                field_value = getattr(self.task, field_name)
                if field_value is True:
                    if field_name is day_to_check_as_string:
                        print("field_name:%s", field_name)
                        end_task = (
                            time_to_check_begin_of_day
                            + datetime.timedelta(minutes=self.task.start)
                            + datetime.timedelta(minutes=self.task.duration)
                        )
                        print("time_to_check", time_to_check)
                        print("end_task", end_task)
                        print("HIER")
                        print("compare", time_to_check < end_task)
                        print("Days", days)
                        if self.begin_of_current_day == time_to_check_begin_of_day:
                            print("GLEICHER TAG")
                            if end_task < self.now:
                                break
                        return self.now + datetime.timedelta(days)
        # return datetime.datetime.today() + datetime.timedelta(days_ahead)

    def make_daylist(self) -> str:
        """Generate a RFC5545 daylist from a task."""
        day_list = ""
        for field in fields(self.task):
            field_name = field.name
            field_value = getattr(self.task, field_name)
            if field_value is True:
                today_rfc = WEEKDAYS_TO_RFC5545[field_name]
                if day_list == "":
                    day_list = today_rfc
                else:
                    day_list += "," + str(today_rfc)
        return day_list

    def make_event(self) -> CalendarEvent:
        """Generate a CalendarEvent from a task."""
        daylist = self.make_daylist()
        next_wd_with_schedule = self.next_weekday_with_schedule()
        print("next_wd_with_schedule:%s", next_wd_with_schedule)
        begin_of_day_with_schedule = next_wd_with_schedule.replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone()
        event = CalendarEvent(
            start=begin_of_day_with_schedule
            + datetime.timedelta(minutes=self.task.start),
            end=begin_of_day_with_schedule
            + datetime.timedelta(minutes=self.task.start)
            + datetime.timedelta(minutes=self.task.duration),
            rrule=f"FREQ=WEEKLY;BYDAY={daylist}",
            uid="fs",
            recurrence_id=f"Recure{1}",
        )
        if event.end < self.now:
            print("Uhrzeit schon vorbei")
        print(event)
        return event


async def async_structure_token(access_token) -> JWT:
    """Decode JWT and convert to dataclass."""
    token_decoded = jwt.decode(access_token, options={"verify_signature": False})
    return JWT.from_dict(token_decoded)


async def async_get_access_token(client_id, client_secret) -> dict:
    """Get an access token from the Authentication API with client credentials.

    This grant type is intended only for you. If you want other
    users to use your application, then they should login using Authorization
    Code Grant.
    """
    auth_data = urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        quote_via=quote_plus,
    )
    async with (
        aiohttp.ClientSession(headers=AUTH_HEADERS) as session,
        session.post(AUTH_API_TOKEN_URL, data=auth_data) as resp,
    ):
        result = await resp.json(encoding="UTF-8")
        _LOGGER.debug("Resp.status get access token: %s", result)
        if resp.status == 200:
            result = await resp.json(encoding="UTF-8")
            result["expires_at"] = result["expires_in"] + time.time()
        if resp.status >= 400:
            raise ApiException(
                f"""The token is invalid, response from
                    Husqvarna Automower API: {result}"""
            )
    result["status"] = resp.status
    return result


async def async_invalidate_access_token(
    valid_access_token, access_token_to_invalidate
) -> dict:
    """Invalidate the token.

    :param str valid_access_token: A working access token to authorize this request.
    :param str access_token_to_delete: An access token to invalidate,
    can be th same like the first argument.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {valid_access_token}",
        "Accept": "*/*",
    }
    async with (
        aiohttp.ClientSession(headers=headers) as session,
        session.post(
            AUTH_API_REVOKE_URL, data=(f"token={access_token_to_invalidate}")
        ) as resp,
    ):
        result = await resp.json(encoding="UTF-8")
        _LOGGER.debug("Resp.status delete token: %s", resp.status)
        if resp.status >= 400:
            resp.raise_for_status()
            _LOGGER.error("Response body delete token: %s", result)
    return result


def mower_list_to_dictionary_dataclass(mower_list) -> dict[str, MowerAttributes]:
    """Convert mower data to a dictionary DataClass."""
    mowers_list = MowerList.from_dict(mower_list)
    mowers_dict = {}
    for mower in mowers_list.data:
        mowers_dict[mower.id] = mower.attributes
    return mowers_dict


def husqvarna_schedule_to_calendar(calendar: Tasks) -> dict[str, MowerAttributes]:
    """Convert mower data to a dictionary DataClass."""
    for task in calendar.tasks:
        event = ConvertScheduleToCalendar(task)
        event.make_event()
