import datetime
from collections import Counter
from .parser import get_messages


def messages_by_day(data: dict) -> list[tuple[str, int]]:
    days = Counter()
    for m in get_messages(data):
        ts = m.get("inserted_at")
        if not ts:
            continue
        try:
            d = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            days[d] += 1
        except Exception:
            pass
    return sorted(days.items())


def messages_by_hour(data: dict) -> list[tuple[str, int]]:
    hours = Counter()
    for m in get_messages(data):
        ts = m.get("inserted_at")
        if not ts:
            continue
        try:
            h = datetime.datetime.fromtimestamp(ts).strftime("%H:00")
            hours[h] += 1
        except Exception:
            pass
    return sorted(hours.items())


def duration(data: dict) -> dict:
    times = [m.get("inserted_at") for m in get_messages(data) if m.get("inserted_at")]
    if not times:
        return {}
    start = min(times)
    end = max(times)
    secs = end - start
    return {
        "start": datetime.datetime.fromtimestamp(start).strftime("%Y-%m-%d %H:%M"),
        "end": datetime.datetime.fromtimestamp(end).strftime("%Y-%m-%d %H:%M"),
        "duration_min": int(secs / 60),
        "duration_hours": round(secs / 3600, 1),
    }
