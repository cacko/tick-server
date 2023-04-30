import logging
from app.lametric.client import Client
from app.lametric.models import (
    Widget,
)
from typing import Any
from cachable.request import Method
from app.botyo.models import (
    MatchEvent,
    SubscriptionEvent,
    CancelJobEvent,
    ACTION
)


class WidgetMeta(type):

    _instances: dict[str, 'BaseWidget'] = {}
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
        cls.live_games_in_progress ^= value


class BaseWidget(object, metaclass=WidgetMeta):

    widget_id: str
    widget: Widget
    options: dict[str, Any]

    def __init__(self, widget_id: str, widget: Widget, **kwargs):
        self.widget_id = widget_id
        self.widget = widget
        self.options = kwargs

    @classmethod
    def validate(cls, v):
        return v

    def activate(self):
        ep = f"device/apps/{self.widget.package}/widgets"
        resp = self.__class__.client.api_call(
            method=Method.PUT,
            endpoint=f"{ep}/{self.widget_id}/activate"
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
        logging.info(f"on_event {payload}")
        if payload is None:
            return payload
        if isinstance(payload, list):
            if not len(payload):
                return payload
            payload, w_payload = self.filter_payload(payload)
            if w_payload:
                self.on_match_events(
                    [MatchEvent(**x) for x in w_payload]
                )
            return payload
        try:
            payload, w_payload = self.filter_payload(payload)
            action = ACTION(w_payload.get("action"))
            logging.info(f"ACTION {action}")
            match(action):
                case ACTION.CANCEL_JOB:
                    self.on_cancel_job_event(
                        CancelJobEvent(**w_payload))
                case ACTION.SUBSCRIBED:
                    self.on_subscribed_event(
                        SubscriptionEvent(**w_payload))
                case ACTION.UNSUBSUBSCRIBED:
                    self.on_unsubscribed_event(
                        SubscriptionEvent(**w_payload))
        except ValueError:
            pass
        finally:
            return payload

    def filter_payload(self, payload):
        return payload, None

    def on_match_events(self, events: list[MatchEvent]):
        raise NotImplementedError

    def on_cancel_job_event(self, event: CancelJobEvent):
        raise NotImplementedError

    def on_subscribed_event(self, event: SubscriptionEvent):
        raise NotImplementedError

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        raise NotImplementedError
