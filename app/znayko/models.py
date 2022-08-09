from enum import IntEnum, Enum
import logging
from app.lametric.models import ContentFrame, ContentSound, SOUNDS
from typing import Optional
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Undefined
from marshmallow import fields
from enum import IntEnum, Enum
from string import punctuation
import re
from stringcase import constcase


class EventIcon(IntEnum):
    GOAL = 8627
    SUBSTITUTION = 31567
    YELLOW__CARD = 43845
    RED__CARD = 43844
    GOAL__DISALLOWED = 10723
    FULL__TIME = 2541
    GAME__START = 2541


class ACTION(Enum):
    SUBSTITUTION = "Substitution"
    GOAL = "Goal"
    YELLOW_CARD = "Yellow Card"
    RED_CARD = "Red Card"
    WOODWORK = "Woodwork"
    PENALTY_MISS = "Penalty Miss"
    GOAL_DISALLOWED = "Goal Disallowed"
    FULL_TIME = "Full Time"
    GAME_START = "Game Start"
    SUBSCRIBED = "Subscribed"
    UNSUBSUBSCRIBED = "Unsubscribed"
    CANCEL_JOB = "Cancel Job"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MatchEvent:
    event_id: int
    time: int
    action: str
    order: int
    is_old_event: bool
    team: Optional[str] = None
    player: Optional[str] = None
    score: Optional[str] = None
    team_id: Optional[int] = None
    event_name: Optional[str] = None

    def getContentFrame(self, league_icon: str = None) -> ContentFrame:
        parts = []
        if self.time:
            parts.append(f"{self.time}'")
        if self.action:
            parts.append(f"{self.action}")
        if self.player:
            parts.append(f"{self.player}")
        if self.event_name:
            parts.append(f"{self.event_name}")
        if self.score:
            parts.append(f"{self.score}")

        res = ContentFrame(text=' '.join(parts))

        if league_icon:
            res.icon = league_icon

        try:
            icon = EventIcon[constcase(self.action)]
            res.icon = icon.value
        except:
            pass

        return res

    def getIcon(self):
        try:
            action = ACTION(self.action)
            if action in [ACTION.GOAL, ACTION.FULL_TIME]:
                return ContentSound(
                    id=SOUNDS.BICYCLE.value
                )
        except:
            pass
        return None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SubscriptionEvent:
    start_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    action: str
    league: str
    league_id: int
    home_team: str
    home_team_id: int
    away_team: str
    away_team_id: int
    event_id: int
    event_name: str
    job_id: str
    icon: str
    status: str = ""

    @property
    def jobId(self):
        if ':' in self.job_id:
            return self.job_id.split(':')[0]
        return self.job_id

    @property
    def isExpired(self):
        n = datetime.now(tz=timezone.utc)
        limit = timedelta(hours=5)
        if self.start_time > n:
            return False
        return (n - self.start_time) > limit

    @property
    def inProgress(self) -> bool:
        logging.warning(f"{self.event_name} {self.status}")
        return re.match(r"^\d+", self.status)

STATUS_MAP = {
    "Post.": "PPD",
    "Ended": "FT",
    "Canc.": "CNL",
    "Sched.": "NS",
    "Just Ended": "FT",
    "After ET": "AET",
    "After Pen": "AET",
}


class GameStatus(Enum):
    FT = "Ended"
    JE = "Just Ended"
    SUS = "Susp"
    ABD = "Aband."
    AET = "After Pen"
    UNKNOWN = ""
    NS = "NS"
    FN = "Final"


class OrderWeight(Enum):
    INPLAY = 1
    HT = pow(2, 1)
    LIVE = pow(2, 1)
    FT = pow(2, 2)
    EAT = pow(2, 3)
    ET = pow(2, 3)
    NS = pow(2, 3)
    PPD = pow(2, 4)
    JUNK = pow(2, 5)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LivescoreEvent:
    id: str
    idEvent: int
    strSport: str
    idLeague: int
    strLeague: str
    idHomeTeam: int
    idAwayTeam: int
    strHomeTeam: str
    strAwayTeam: str
    strStatus: str
    startTime: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso", tzinfo=timezone.utc),
        )
    )
    intHomeScore: Optional[int] = -1
    intAwayScore: Optional[int] = -1
    sort: int = 0
    details: Optional[str] = None
    displayScore: Optional[str] = ""
    displayStatus: Optional[str] = ""
    source: Optional[str] = ""
    strWinDescription: Optional[str] = ""

    def __post_init__(self):
        if self.strStatus in STATUS_MAP:
            self.strStatus = STATUS_MAP[self.strStatus]

        delta = (datetime.now(timezone.utc) -
                 self.startTime).total_seconds() / 60
        try:
            self.displayStatus = GameStatus(self.strStatus)
            if delta < 0 and self.displayStatus in [
                    GameStatus.UNKNOWN, GameStatus.NS]:
                self.displayStatus = self.startTime.astimezone(
                    ZoneInfo("Europe/London")).strftime("%H:%M")
            else:
                self.displayStatus = self.displayStatus.name
        except Exception:
            self.displayStatus = self.strStatus
        try:
            if re.match(r"^\d+$", self.strStatus):
                self.sort = OrderWeight.INPLAY.value * int(self.strStatus)
                self.displayStatus = f"{self.strStatus}\""
            else:
                self.sort = OrderWeight[
                    self.strStatus.translate(punctuation).upper()
                ].value * abs(delta)
        except KeyError:
            self.sort = OrderWeight.JUNK.value * abs(delta)
        if any([self.intAwayScore == -1, self.intHomeScore == -1]):
            self.displayScore = ""
        else:
            self.displayScore = ":".join([
                f"{self.intHomeScore:.0f}",
                f"{self.intAwayScore:.0f}"
            ])

    @property
    def inProgress(self) -> bool:
        return re.match(r"^\d+$", self.strStatus)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CancelJobEvent:
    job_id: str
    action: str

    @property
    def jobId(self):
        if ':' in self.job_id:
            return self.job_id.split(':')[0]
        return self.job_id
