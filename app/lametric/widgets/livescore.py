from enum import IntEnum, Enum
import logging
from app.lametric.models import APPNAME, Content, ContentFrame, ContentSound, Notification, SOUNDS
from .base import BaseWidget, WidgetMeta
from typing import Optional
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Undefined
from marshmallow import fields
from enum import IntEnum, Enum
from cachable.storage import Storage
import requests
import pickle
from app.config import Config
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


STORAGE_KEY = "subscriptions"
TIMEZONE = ZoneInfo("Europe/London")


class Scores(dict):

    __has_changes = False

    def __setitem__(self, __k, __v) -> None:
        if self.get(__k, "") != __v:
            self.__has_changes = True
        return super().__setitem__(__k, __v)

    def __delitem__(self, __v) -> None:
        return super().__delitem__(__v)

    @property
    def has_changes(self):
        res = self.__has_changes
        self.__has_changes = False
        return res


class LivescoresWidget(BaseWidget, metaclass=WidgetMeta):

    subscriptions: list[SubscriptionEvent] = []
    scores: Scores = {}

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.scores = Scores(())
        self.load()
        if self.subscriptions:
            for sub in self.subscriptions:
                if sub.isExpired:
                    self.cancel_sub(sub)
            self.load_scores()
            self.update_frames()

    def load(self):
        data = Storage.hgetall(STORAGE_KEY)
        if not data:
            self.subscriptions = []
        self.subscriptions = [pickle.loads(v) for v in data.values()]

    def load_scores(self):
        url = f"{Config.znayko.host}/livescore"
        res = requests.get(url)
        data = res.json()
        ids = [x.event_id for x in self.subscriptions]

        scores = list(filter(lambda x: x.get("idEvent") in ids, data))
        if not len(scores):
            return
        events: list[LivescoreEvent] = LivescoreEvent.schema().load(
            scores, many=True)
        store = Storage.pipeline()
        for event in events:
            text = event.displayScore
            sub = next(filter(lambda x: x.event_id ==
                       event.idEvent, self.subscriptions), None)
            if not sub:
                return
            sub.status = event.displayStatus
            logging.warning(sub)
            store.hset(STORAGE_KEY, f"{sub.event_id}", pickle.dumps(sub))
            self.scores[event.idEvent] = text
        store.persist(STORAGE_KEY).execute()

    def cancel_sub(self, sub: SubscriptionEvent):
        url = f"{Config.znayko.host}/unsubscribe"
        res = requests.post(url, {
            "webhook": f"http://{Config.api.host}:{Config.api.port}/api/subscription",
            "group": Config.api.secret,
            "id": sub.job_id
        })
        logging.warning(res.content)

    def onShow(self):
        pass

    def onHide(self):
        pass

    def duration(self, duration: int):
        res = len(self.subscriptions) * 8000
        return res

    @property
    def isHidden(self):
        return len(self.subscriptions) == 0

    def update_frames(self):
        frames = []
        for idx, sub in enumerate(self.subscriptions):
            text = []
            text.append(sub.status)
            text.append(sub.event_name)
            score = self.scores.get(sub.event_id, "")
            if score:
                text.append(score)
            frame = ContentFrame(
                text=' '.join(text),
                index=idx,
                icon=sub.icon
            )
            frames.append(frame)
        __class__.client.send_model(
            APPNAME.LIVESCORES, Content(frames=frames)
        )

    def on_event(self, payload):
        if isinstance(payload, list):
            try:
                self.on_match_events(
                    MatchEvent.schema().load(payload, many=True))
            except Exception as e:
                logging.error(e)
                logging.warning(payload)
        else:
            self.on_subscription_event(payload)

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            logging.warning(event)
            if not event.is_old_event:
                sub = next(filter(lambda x: x.event_id ==
                           event.event_id, self.subscriptions), None)
                frame = event.getContentFrame(
                    league_icon=sub.icon if sub else None)
                __class__.client.send_notification(Notification(
                    model=Content(
                        frames=[frame],
                        sound=event.getIcon()
                    ),
                    priority='critical'
                ))
            if event.score:
                self.scores[event.event_id] = event.score
        if self.scores.has_changes:
            self.update_frames()

    def on_subscription_event(self, payload):
        action = ACTION(payload.get("action"))
        if action == ACTION.CANCEL_JOB:
            event = CancelJobEvent.from_dict(payload)
            sub = next(filter(lambda x: x.jobId ==
                       event.jobId, self.subscriptions), None)
            if sub:
                Storage.hdel(STORAGE_KEY, f"{sub.event_id}")
                Storage.persist(STORAGE_KEY)
        elif action == ACTION.SUBSCRIBED:
            event: SubscriptionEvent = SubscriptionEvent.from_dict(payload)
            logging.warning(event)
            Storage.hset(STORAGE_KEY, f"{event.event_id}", pickle.dumps(event))
            Storage.persist(STORAGE_KEY)
        else:
            event: SubscriptionEvent = SubscriptionEvent.from_dict(payload)
            Storage.hdel(STORAGE_KEY, f"{event.event_id}")
            Storage.persist(STORAGE_KEY)
        self.load()
        self.update_frames()
