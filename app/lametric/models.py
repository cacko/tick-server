from pydantic import BaseModel, Field
from datetime import time, datetime, timezone, timedelta
from typing import Optional
from enum import Enum, IntEnum, StrEnum
from app.core.time import LOCAL_TIMEZONE


class DEVICE_MODE(StrEnum):
    MANUAL = "manual"
    AUTO = "auto"
    SCHEDULE = "schedule"
    KIOSK = "kiosk"


class CONTENT_TYPE(StrEnum):
    NOWPLAYING = "nowplaying"
    YANKOSTATUS = "yanko_status"
    LIVESCOREEVENT = "livescore_event"
    TERMO = "termo"
    SURE="sure"


class STORAGE_KEY(StrEnum):
    LIVESCORES = "subscriptions"
    WORLDCUP = "worldcup_subscriptions"
    PREMIER_LEAGUE = "premierleague_subscriptions"
    LA_LIGA = "laliga_subscriptions"
    REAL_MADRID = "real_madrid"


class APPNAME(StrEnum):
    CLOCK = "clock"
    WEATHER = "weather"
    DATETICKER = "dateticker"
    YANKO = "yanko"
    RM = "rm"
    LIVESCORES = "livescores"
    WORLDCUP = "worldcup"
    PREMIER_LEAGUE = "premierleague"
    LA_LIGA = "laliga"
    SYDNEY="sydney"
    TERMO="termo"
    SURE="sure"


class MUSIC_STATUS(StrEnum):
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    LOADING = "loadng"
    EXIT = "exit"
    RESUMED = "resumed"
    NEXT = "next"
    PREVIOUS = "previous"


class SOUNDS(StrEnum):
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
    
class ALERT_COLOR(Enum):
    GOAL_POSITIVE=['1BB94B', '34B0EE']
    GOAL_NEGATIVE=['FF8CFF', 'FFFF46']
    YELLOW_CARD=['FFFF46', 'FFFF00']
    RED_CARD=['FF0200', '850200']
    WIN=['13DB4B', '138BF7']
    LOSS=['CF00F7', '8C0089']
    DEFAULT=['FBF200', '0FF2FA']
        
class ALERT_DURATION(IntEnum):
    GOAL=2000
    YELLOW_CARD=1500
    RED_CARD=2000
    FULL_TIME=3000
    DEFAULT=1000

class ModeTimeBased(BaseModel):
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
        return all(
            [
                time.fromisoformat(self.local_start_time).replace(
                    tzinfo=LOCAL_TIMEZONE)
                < n,
                time.fromisoformat(self.local_end_time).replace(
                    tzinfo=LOCAL_TIMEZONE)
                > n,
            ]
        )


class ScreensaveModes(BaseModel):
    time_based: ModeTimeBased


class DisplayScreensave(BaseModel):
    enabled: bool
    modes: ScreensaveModes


class DeviceDisplay(BaseModel):
    brightness: int
    screensaver: DisplayScreensave
    updated_at: datetime

    @property
    def needs_update(self) -> bool:
        td = timedelta(minutes=5)
        return (datetime.now(tz=timezone.utc) - self.updated_at) > td


class Widget(BaseModel):
    index: int
    package: str
    settings: Optional[dict] = None


class App(BaseModel):
    package: str
    title: str
    vendor: str
    version: str
    version_code: str
    widgets: Optional[dict[str, Widget]] = None
    triggers: Optional[dict] = None
    
    
    def widget_id_by_idx(self, idx: int):
        try:
            assert self.widgets
            return next(filter(lambda k: self.widgets[k].index == idx, self.widgets.keys()), None)
        except AssertionError:
            return None

    def widget_data_by_id(self, idx):
        try:
            k = self.widget_id_by_idx(idx)
            assert k
            return self.widgets[k]
        except AssertionError:
            return None

class GoalData(BaseModel):
    start: int
    current: int
    end: int
    units: Optional[str] = ""


class ContentFrame(BaseModel):
    text: Optional[str] = None
    icon: Optional[str | int] = None
    index: Optional[int] = Field(default=0)
    duration: Optional[int] = None
    goalData: Optional[GoalData] = None


class TimeFrame(ContentFrame):
    index: Optional[int] = Field(default=0)


class DateFrame(ContentFrame):
    index: Optional[int] = Field(default=1)


class WeatherFrame(ContentFrame):
    index: Optional[int] = Field(default=2)


class NowPlayingFrame(ContentFrame):
    index: Optional[int] = Field(default=3)
    

class ContentSound(BaseModel):
    id: str
    category: str = Field(default="notifications")


class Content(BaseModel):
    frames: list[ContentFrame]
    sound: Optional[ContentSound] = None


class Notification(BaseModel):
    model: Content
    priority: str = Field(default="info")
    icon_type: str = Field(default="none")


class ContentLight(BaseModel):
    duration: int
    colors: list[str]