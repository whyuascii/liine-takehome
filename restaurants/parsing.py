import re
from datetime import time


def parse_time(time_str):
    """Parse a time string like '11:30 am' into a datetime.time object.

    Returns datetime.time.

    Note: '12 am' returns time(0, 0) (midnight).
    """
    match = re.match(r"(\d+)(?::(\d+))?\s*(am|pm)", time_str.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid time format: {time_str!r}")

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3).lower()

    if period == "am":
        if hour == 12:
            hour = 0
    else:
        if hour != 12:
            hour += 12

    return time(hour, minute)


DAY_MAP = {
    "mon": 0,
    "tues": 1,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

ORDERED_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _day_to_int(day_str):
    """Convert a day abbreviation to an integer (0=Mon, 6=Sun)."""
    key = day_str.strip().lower()
    if key not in DAY_MAP:
        raise ValueError(f"Unknown day abbreviation: {day_str!r}")
    return DAY_MAP[key]


def parse_day_specifiers(day_str):
    """Parse day specifiers like 'Mon-Thu, Sun' into a sorted list of day ints.

    Returns sorted list of ints where 0=Monday, 6=Sunday.
    """
    days = []
    parts = [p.strip() for p in day_str.split(",")]
    for part in parts:
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = _day_to_int(start_str)
            end = _day_to_int(end_str)
            if start <= end:
                days.extend(range(start, end + 1))
            else:
                # Wrap around: e.g., Sat-Mon
                days.extend(range(start, 7))
                days.extend(range(0, end + 1))
        else:
            days.append(_day_to_int(part))
    return sorted(set(days))


def parse_hours_string(hours_str):
    """Parse a full hours string into a list of (day_of_week, open_time, close_time) tuples.

    Handles multiple schedule blocks separated by ' / ', overnight hour splitting,
    and various day specifier formats.

    Returns a list of tuples: (day_of_week, open_time, close_time)
    where close_time > open_time always holds.
    """
    results = []
    blocks = [b.strip() for b in hours_str.split("/")]

    for block in blocks:
        time_match = re.search(r"\d", block)
        if not time_match:
            continue

        day_part = block[: time_match.start()].strip().rstrip(",").strip()
        time_part = block[time_match.start() :].strip()

        days = parse_day_specifiers(day_part)

        time_range_match = re.match(
            r"(\d+(?::\d+)?\s*[ap]m)\s*-\s*(\d+(?::\d+)?\s*[ap]m)",
            time_part,
            re.IGNORECASE,
        )
        if not time_range_match:
            raise ValueError(f"Invalid time range format: {time_part!r}")

        open_time = parse_time(time_range_match.group(1))
        close_time = parse_time(time_range_match.group(2))

        if close_time == time(0, 0):
            close_time = time.max

        for day in days:
            if close_time <= open_time:
                results.append((day, open_time, time.max))
                next_day = (day + 1) % 7
                results.append((next_day, time.min, close_time))
            else:
                results.append((day, open_time, close_time))

    return results
