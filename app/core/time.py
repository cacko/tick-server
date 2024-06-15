from app.config import app_config
from zoneinfo import ZoneInfo
from datetime import datetime

LOCAL_TIMEZONE = ZoneInfo(app_config.lametric.timezone)


def to_local(d: datetime) -> datetime:
    return d.astimezone(tz=LOCAL_TIMEZONE)


def to_local_time(d: datetime, fmt="%H:%M") -> str:
    return to_local(d).strftime(fmt)


def is_today(d: datetime) -> bool:
    n = datetime.now(tz=LOCAL_TIMEZONE)
    fmt = "%m%d"
    return n.strftime(fmt) == to_local(d).strftime(fmt)
