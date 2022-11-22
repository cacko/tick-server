from app.lametric.client import Client
from app.lametric.models import (
    Widget,
)
from typing import Any
from cachable.request import Method
from app.znayko.models import (
    MatchEvent,
    SubscriptionEvent,
    CancelJobEvent,
    ACTION
)
import logging


class WidgetMeta(type):

    _instances = {}
    client: Client
    live_games_in_progress = False

    def __call__(cls, widget_id: str, widget: Widget, *args, **kwds):
        if cls.__name__ not in cls._instances:
            cls._instances[cls.__name__] = type.__call__(
                cls, widget_id, widget, *args, **kwds)
        return cls._instances[cls.__name__]

    def register(cls, client: Client):
        cls.client = client

    @property
    def hasLivescoreGamesInProgress(cls):
        return cls.live_games_in_progress

    @hasLivescoreGamesInProgress.setter
    def hasLivescoreGamesInProgress(cls, value: bool):
        cls.live_games_in_progress ^= int(value)


class BaseWidget(object, metaclass=WidgetMeta):

    widget_id: str
    widget: Widget
    options: dict[str, Any]

    def __init__(self, widget_id: str, widget: Widget, *args, **kwargs):
        self.widget_id = widget_id
        self.widget = widget
        self.options = kwargs

    def activate(self):
        resp = __class__.client.api_call(
            method=Method.PUT,
            endpoint=f"device/apps/{self.widget.package}/widgets/{self.widget_id}/activate"
        )
        return resp
    
    @property
    def item_id(self) -> int:
        try:
            res = self.options.get("item_id")
            assert isinstance(res, int)
            return res
        except AssertionError:
            return 0

    def onShow(self):
        raise NotImplementedError

    def onHide(self):
        raise NotImplementedError

    def duration(self, duration: int):
        return duration

    @property
    def isHidden(self):
        return False

    @property
    def isSleeping(self):
        return False


class SubscriptionWidget(BaseWidget):

    def on_event(self, payload):
        if payload is None:
            return payload
        if isinstance(payload, list):
            if not len(payload):
                return payload
            self.on_match_events(
                MatchEvent.schema().load(payload, many=True)  # type: ignore
            )
            return self.filter_payload(payload)
        try:
            action = ACTION(payload.get("action"))
            match(action):
                case ACTION.CANCEL_JOB:
                    self.on_cancel_job_event(
                        CancelJobEvent.from_dict(payload))  # type: ignore
                case ACTION.SUBSCRIBED:
                    self.on_subscribed_event(
                        SubscriptionEvent.from_dict(payload))  # type: ignore
                case ACTION.UNSUBSUBSCRIBED:
                    self.on_unsubscribed_event(
                        SubscriptionEvent.from_dict(payload))  # type: ignore
        except ValueError:
            pass
        finally:
            return self.filter_payload(payload)

    def filter_payload(self, payload):
        return payload

    def on_match_events(self, events: list[MatchEvent]):
        raise NotImplementedError

    def on_cancel_job_event(self, event: CancelJobEvent):
        raise NotImplementedError

    def on_subscribed_event(self, event: SubscriptionEvent):
        raise NotImplementedError

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        raise NotImplementedError
