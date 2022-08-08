from enum import IntEnum, Enum

from app.lametric.models import Content, ContentFrame, Notification
from .base import BaseWidget, WidgetMeta


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


class LivescoresWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass

    def on_event(self, event):
        frame = ContentFrame(
            text=f"{event.action} {event.time:.0f}' {event.event_name} {event.score}"
        )
        __class__.client.send_notification(Notification(
            model=Content(
                frames=[frame],
            ),
            priority='critical'
        ))