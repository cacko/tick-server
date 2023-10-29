from pydantic import BaseModel, Field
from datetime import time, datetime, timezone, timedelta
from typing import Optional
from enum import StrEnum
from app.core.time import LOCAL_TIMEZONE


class CONTENT_TYPE(StrEnum):
    NOWPLAYING = "nowplaying"
    YANKOSTATUS = "yanko_status"
    LIVESCOREEVENT = "livescore_event"


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
