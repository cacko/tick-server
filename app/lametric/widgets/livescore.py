from enum import IntEnum, Enum
import logging

from app.lametric.models import Content, ContentFrame, Notification
from .base import BaseWidget, WidgetMeta
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Undefined
from marshmallow import fields
from enum import IntEnum, Enum

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
    event_id: int
    time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    action: str
    home_team:str
    home_team_id:int
    away_team: str
    away_team_id: int
    event_name:str

class EventIcon(IntEnum):

    GOAL = 8627


class Event(Enum):
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


class LivescoresWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass

    def on_event(self, payload):
        if isinstance(payload, list):
            self.on_match_events(MatchEvent.schema().load(payload, many=True))
        else:
            self.on_subscription_event(SubscriptionEvent.from_dict(payload))


    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            frame = ContentFrame(
                text=f"{event.get('action')} {event.get('time'):.0f}' {event.get('event_name')} {event.get('score')}"
            )
            __class__.client.send_notification(Notification(
                model=Content(
                    frames=[frame],
                ),
                priority='critical'
            ))

    def on_subscription_event(self, event: SubscriptionEvent):
        logging.warning(event)