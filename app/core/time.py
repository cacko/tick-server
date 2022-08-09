from app.config import Config
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

LOCAL_TIMEZONE = ZoneInfo(Config.lametric.timezone)


def to_local(d: datetime) -> datetime:
    return d.astimezone(tz=LOCAL_TIMEZONE)


def to_local_time(d: datetime, fmt="%H:%M") -> str:
    return to_local(d).strftime(fmt)


def is_today(d: datetime) -> bool:
    n = datetime.now(tz=LOCAL_TIMEZONE)
    fmt = "%m%d"
    return n.strftime(fmt) == to_local(d).strftime(fmt)
