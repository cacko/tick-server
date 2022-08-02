from dataclasses import dataclass
from lib2to3.pgen2.token import OP
from statistics import mode
from dataclasses_json import dataclass_json, Undefined
from typing import Optional
from enum import Enum
from datetime import datetime


class CONTENT_TYPE(Enum):
    NOWPLAYING = 'nowplaying'
    YANKOSTATUS = 'yanko_status'



class YANKO_STATUS(Enum):
    PLAYING = 'playing'
    STOPPED = 'stopped'
    LOADING = 'loadng'
    EXIT = 'exit'

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
class YankoFrame(ContentFrame):
    index: Optional[int] = 3


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Content:
    frames: list[ContentFrame]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Notification:
    model: Content
    priority: str = "info"
    icon_type: str = "none"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Display:
    clock: list[ContentFrame]
    weather: Optional[list[WeatherFrame]] = None
    yanko: Optional[list[YankoFrame]] = None

    def getContent(self):
        res = [*self.clock]
        if self.weather:
            res += self.weather
        if self.yanko:
            res += self.yanko
        return Content(
            frames=res
        )
