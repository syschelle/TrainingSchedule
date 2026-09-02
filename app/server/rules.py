from __future__ import annotations

from datetime import date, datetime, time, timedelta

DISPLAY_WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
WEEKDAYS = DISPLAY_WEEKDAYS[:4]


def parse_time(value: str) -> int:
    hour, minute = value.strip().split(":")
    return int(hour) * 60 + int(minute)


def format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"




def snap_minutes_to_quarter(minutes: int, mode: str = "nearest") -> int:
    """Snap a minute value to a 15-minute boundary.

    ``ceil`` is used by the planner so a new block never starts before a
    previous block has ended. ``nearest`` is used for user-entered values.
    """
    step = 15
    if mode == "ceil":
        return ((minutes + step - 1) // step) * step
    return ((minutes + step // 2) // step) * step


def snap_time_to_quarter(value: str, mode: str = "nearest") -> str:
    return format_time(snap_minutes_to_quarter(parse_time(value), mode))

def minutes_between(start: str, end: str) -> int:
    return parse_time(end) - parse_time(start)


def add_minutes(start: str, minutes: int) -> str:
    return format_time(parse_time(start) + minutes)


def training_dates(start: date | None) -> list[date | None]:
    if start is None:
        return [None, None, None, None, None]
    monday = start
    while monday.weekday() != 0:
        monday = monday - timedelta(days=1)
    return [monday + timedelta(days=i) for i in range(5)]


def german_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%d.%m.%Y")


def is_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return parse_time(a_start) < parse_time(b_end) and parse_time(b_start) < parse_time(a_end)
