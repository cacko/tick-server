from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from unicodedata import category
from dataclasses_json import dataclass_json, Undefined
from typing import Optional
from enum import Enum
from pixelme import Pixelate
from tempfile import gettempdir
from uuid import uuid4
from base64 import b64decode, b64encode

from app.config import LametricApp

class CONTENT_TYPE(Enum):
    NOWPLAYING = 'nowplaying'
    YANKOSTATUS = 'yanko_status'

class APP_NAME(Enum):
    CLOCK = 'clock'
    WEATHER = 'weather'
    YANKO = 'yanko'

class MUSIC_STATUS(Enum):
    PLAYING = 'playing'
    STOPPED = 'stopped'
    RESUMED = 'resumed'
    LOADING = 'loadng'
    EXIT = 'exit'


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

    def __post_init__(self):
        if self.icon:
            icon_path = Path(gettempdir()) / f"{uuid4().hex}.webp"
            icon_path.write_bytes(b64decode(self.icon))
            pix =Pixelate(
                icon_path,
                padding=200,
                block_size=25
            )
            pix.resize((8,8))
            self.icon = pix.base64


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

