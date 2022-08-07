from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from typing import Optional
from enum import Enum
class CONTENT_TYPE(Enum):
    NOWPLAYING = 'nowplaying'
    YANKOSTATUS = 'yanko_status'

class APPNAME(Enum):
    CLOCK = 'clock'
    WEATHER = 'weather'
    YANKO = 'yanko'
    RM = 'rm'

class MUSIC_STATUS(Enum):
    PLAYING = 'playing'
    PAUSED = 'paused'
    STOPPED = 'stopped'
    LOADING = 'loadng'
    EXIT = 'exit'
    RESUMED = 'resumed'
    NEXT = 'next'
    PREVIOUS = 'previous'


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

