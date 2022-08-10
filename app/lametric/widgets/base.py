from app.lametric.client import Client
from app.lametric.models import (
    Widget,
)
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
    client: Client = None

    def __call__(cls, widget: Widget, *args, **kwds):
        if cls.__name__ not in cls._instances:
            cls._instances[cls.__name__] = type.__call__(
                cls, widget, *args, **kwds)
        return cls._instances[cls.__name__]

    def register(cls, client: Client):
        cls.client = client


class BaseWidget(object, metaclass=WidgetMeta):

    widget: Widget = None
    widget_id: str = None

    def __init__(self, widget_id: str, widget: Widget):
        self.widget = widget
        self.widget_id = widget_id

    def activate(self):
        resp = __class__.client.api_call(
            method=Method.PUT,
            endpoint=f"device/apps/{self.widget.package}/widgets/{self.widget_id}/activate"
        )
        return resp

    def onShow(self):
        raise NotImplementedError

    def onHide(self):
        raise NotImplementedError

    def duration(self, duration: int):
        return duration

    @property
    def isHidden(self):
        return False


class SubscriptionWidget(BaseWidget):

    def on_event(self, payload):
        if payload is None:
            return payload
        if isinstance(payload, list):
            if not len(payload):
                return payload
            try:
                self.on_match_events(
                    MatchEvent.schema().load(payload, many=True)
                )
            except Exception as e:
                logging.error(e)
                logging.warning(payload)
            finally:
                return self.filter_payload(payload)
        else:
            try:
                action = ACTION(payload.get("action"))
                match(action):
                    case ACTION.CANCEL_JOB:
                        self.on_cancel_job_event(CancelJobEvent.from_dict(payload))
                    case ACTION.SUBSCRIBED:
                        self.on_subscribed_event(SubscriptionEvent.fromt_dict(payload))
                    case ACTION.UNSUBSUBSCRIBED:
                        self.on_unsubscribed_event(SubscriptionEvent.from_dict(payload))
            except Exception as e:
                logging.error(e)
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

