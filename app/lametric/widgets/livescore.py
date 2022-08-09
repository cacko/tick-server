from enum import IntEnum, Enum
from app.lametric.models import APPNAME, Content, ContentFrame, Notification
from .base import BaseWidget, WidgetMeta
from typing import Optional
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Undefined
from marshmallow import fields
from enum import IntEnum, Enum
from cachable.storage import Storage
import requests
import pickle
from app.config import Config


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MatchEvent:
    event_id: int
    time: str
    action: str
    order: int
    is_old_event: bool
    team: Optional[str] = None
    player: Optional[str] = None
    score: Optional[str] = None
    team_id: Optional[int] = None
    event_name: Optional[str] = None


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

    @property
    def jobId(self):
        if ':' in self.job_id:
            return self.job_id.split(':')[0]
        return self.job_id


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


class EventIcon(IntEnum):
    GOAL = 8627


class ACTION(Enum):
    SUBSTITUTION = "Subsctitution"
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


STORAGE_KEY = "subscriptions"
TIMEZONE = ZoneInfo("Europe/London")


class LivescoresWidget(BaseWidget, metaclass=WidgetMeta):

    subsriptions: list[SubscriptionEvent] = []
    scores = {}

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.load()
        if self.subsriptions:
            self.load_scores()

    def load(self):
        data = Storage.hgetall(STORAGE_KEY)
        if not data:
            self.subsriptions = []
        self.subsriptions = [pickle.loads(v) for v in data.values()]
        self.update_frames()

    def load_scores(self):
        url = f"{Config.znayko.host}/livescore"
        res = requests.get(url)
        data = res.json()
        ids = [x.event_id for x in self.subsriptions]
        scores = list(filter(lambda x: x.get("idEvent") in ids, data))
        for score in scores:
            id = score.get("idEvent")
            text = f"{score.get('intHomeScore')}:{score.get('intAwayScore')}"
            self.scores[id] = text

    def onShow(self):
        pass

    def onHide(self):
        pass

    def duration(self, duration: int):
        res = len(self.subsriptions) * 8000
        return res

    @property
    def isHidden(self):
        return len(self.subsriptions) == 0

    def update_frames(self):
        frames = []
        n = datetime.now(tz=timezone.utc)
        for idx, sub in enumerate(self.subsriptions):
            text = sub.event_name
            if sub.start_time > n:
                text = f"{sub.start_time.astimezone(TIMEZONE).strftime('%H:%M')} {text}"
            else:
                score = self.scores.get(sub.event_id, "")
                text = f"{text} {score}"
            frame = ContentFrame(
                text=text,
                index=idx,
                icon=sub.icon
            )
            frames.append(frame)
        __class__.client.send_model(
            APPNAME.LIVESCORES, Content(frames=frames)
        )

    def on_event(self, payload):
        if isinstance(payload, list):
            self.on_match_events(MatchEvent.schema().load(payload, many=True))
        else:
            self.on_subscription_event(payload)

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            if event.score:
                self.scores[event.event_id] = event.score
            frame = ContentFrame(
                text=f"{event.get('action')} {event.get('time'):.0f}' {event.get('event_name')} {event.get('score')}"
            )
            __class__.client.send_notification(Notification(
                model=Content(
                    frames=[frame],
                ),
                priority='critical'
            ))

    def on_subscription_event(self, payload):
        action = ACTION(payload.get("action"))
        if action == ACTION.CANCEL_JOB:
            event = CancelJobEvent.from_dict(payload)
            sub = next(filter(lambda x: x.jobId ==
                       event.jobId, self.subsriptions), None)
            if sub:
                Storage.hdel(STORAGE_KEY, f"{sub.event_id}")
                Storage.persist(STORAGE_KEY)
        elif action == ACTION.SUBSCRIBED:
            event: SubscriptionEvent = SubscriptionEvent.from_dict(payload)
            Storage.hset(STORAGE_KEY, f"{event.event_id}", pickle.dumps(event))
            Storage.persist(STORAGE_KEY)
        else:
            event: SubscriptionEvent = SubscriptionEvent.from_dict(payload)
            Storage.hdel(STORAGE_KEY, f"{event.event_id}")
            Storage.persist(STORAGE_KEY)
        self.load()
