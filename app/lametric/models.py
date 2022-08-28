from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from datetime import time, datetime, timezone, timedelta
from typing import Optional
from enum import Enum
from app.core.time import LOCAL_TIMEZONE


class CONTENT_TYPE(Enum):
    NOWPLAYING = 'nowplaying'
    YANKOSTATUS = 'yanko_status'
    LIVESCOREEVENT = 'livescore_event'


class APPNAME(Enum):
    CLOCK = 'clock'
    WEATHER = 'weather'
    YANKO = 'yanko'
    RM = 'rm'
    LIVESCORES = 'livescores'


class MUSIC_STATUS(Enum):
    PLAYING = 'playing'
    PAUSED = 'paused'
    STOPPED = 'stopped'
    LOADING = 'loadng'
    EXIT = 'exit'
    RESUMED = 'resumed'
    NEXT = 'next'
    PREVIOUS = 'previous'


class SOUNDS(Enum):
    BICYCLE = "bicycle"
    CAR = "car"
    CASH = "cash"
    CAT = "cat"
    DOG = "dog"
    DOG2 = "dog2"
    ENERGY = "energy"
    KNOCK = "knock-knock"
    EMAIL = "letter_email"
    LOSE1 = "lose1"
    LOSE2 = "lose2"
    NEGATIVE1 = "negative1"
    NEGATIVE2 = "negative2"
    NEGATIVE3 = "negative3"
    NEGATIVE4 = "negative4"
    NEGATIVE5 = "negative5"
    NOTIFICATION = "notification"
    NOTIFICATION2 = "notification2"
    NOTIFICATION3 = "notification3"
    NOTIFICATION4 = "notification4"
    OPEN_DOOR = "open_door"
    POSITIVE1 = "positive1"
    POSITIVE2 = "positive2"
    POSITIVE3 = "positive3"
    POSITIVE4 = "positive4"
    POSITIVE5 = "positive5"
    POSITIVE6 = "positive6"
    STATISIC = "statistic"
    THUNDER = "thunder"
    WATER = "water1"
    WATER2 = "water2"
    WIN = "win"
    WIN2 = "win2"
    WIND = "wind"
    WIND_SHORT = "wind_short"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ModeTimeBased:
    enabled: bool
    end_time: str
    start_time: str
    local_end_time: str
    local_start_time: str

    @property
    def isActive(self):
        if not self.enabled:
            return False
        n = datetime.now(tz=LOCAL_TIMEZONE).time()
        return all([
            time.fromisoformat(self.local_start_time).replace(
                tzinfo=LOCAL_TIMEZONE) < n,
            time.fromisoformat(self.local_end_time).replace(
                tzinfo=LOCAL_TIMEZONE) > n
        ])


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ScreensaveModes:
    time_based: ModeTimeBased


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DisplayScreensave:
    enabled: bool
    modes: ScreensaveModes


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DeviceDisplay:
    brightness: int
    screensaver: DisplayScreensave
    updated_at: Optional[datetime] = None

    @property
    def needs_update(self) -> bool:
        return (datetime.now(tz=timezone.utc) - self.updated_at) > timedelta(minutes=5)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Widget:
    index: int
    package: str
    settings: Optional[dict] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class App:
    package: str
    title: str
    vendor: str
    version: str
    version_code: str
    widgets: Optional[dict[str, Widget]] = None
    triggers: Optional[dict] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GoalData:
    start: int
    current: int
    end: int
    units: Optional[str] = ""


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ContentFrame:
    text: Optional[str] = None
    icon: Optional[str | int] = None
    index: Optional[int] = 0
    duration: Optional[int] = None
    goalData: Optional[GoalData] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TimeFrame(ContentFrame):
    index: Optional[int] = 0


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DateFrame(ContentFrame):
    index: Optional[int] = 1


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class WeatherFrame(ContentFrame):
    index: Optional[int] = 2


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class NowPlayingFrame(ContentFrame):
    index: Optional[int] = 3


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ContentSound:
    id: str
    category: str = "notifications"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Content:
    frames: list[ContentFrame]
    sound: Optional[ContentSound] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Notification:
    model: Content
    priority: str = "info"
    icon_type: str = "none"

