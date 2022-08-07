from app.lametric.client import Client
from app.lametric.models import (
    Widget,
)
from cachable.request import Method



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

    @property
    def isHidden(self):
        return False
