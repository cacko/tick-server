

import logging
from app.config import LametricApp
from app.lametric.client import Client
from app.lametric.models import (
    CONTENT_TYPE,
    App,
    ContentSound,
    Widget,
    NowPlayingFrame,
    Notification,
    Content,
    MUSIC_STATUS,
    APP_NAME
)
from cachable.request import Method
from app.config import Config
from dataclasses import dataclass
from datetime import datetime, timedelta
from dataclasses_json import dataclass_json, Undefined
from typing import Optional

from app.yanko import Yanko


class WidgetMeta(type):

    _instances = {}
    client: Client = None

    def __call__(cls, widget: Widget, *args, **kwds):
        if cls.__name__ not in cls._instances:
            cls._instances[cls.__name__] = type.__call__(cls, widget, *args, **kwds)
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


class ClockWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass


class WeatherWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass


class YankoWidget(BaseWidget, metaclass=WidgetMeta):

    status: MUSIC_STATUS = None

    def __init__(self, widget_id: str, widget: Widget):
        super().__init__(widget_id, widget)
        self.status = MUSIC_STATUS.STOPPED
        if not Yanko.state():
            self.status = MUSIC_STATUS.STOPPED

    def onShow(self):
        pass

    def onHide(self):
        pass

    @property
    def isHidden(self):
        return (self.status in [MUSIC_STATUS.STOPPED, MUSIC_STATUS.EXIT])

    def nowplaying(self, payload):
        frame = NowPlayingFrame(**payload)
        __class__.client.send_notification(Notification(
            model=Content(
                frames=[frame],
            ),
            priority='critical'
        ))
        __class__.client.send_model('yanko', Content(frames=[frame]))
        return True

    def yankostatus(self, payload):
        try:
            self.status = MUSIC_STATUS(payload.get("status"))
        except ValueError:
            self.status = MUSIC_STATUS.STOPPED

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DisplayItem:
    app: LametricApp
    widget: BaseWidget
    duration: int
    hidden: bool = False
    activated_at: Optional[datetime] = None

    def activate(self):
        self.widget.activate()
        self.activated_at = datetime.now()
        self.widget.onShow()

    def deactivate(self):
        self.activated_at = None
        self.widget.onHide()

    @property
    def isExpired(self):
        td = datetime.now() - self.activated_at
        return td > timedelta(milliseconds=self.duration)

    @property
    def isActive(self):
        return self.activated_at is not None

    @property
    def isAllowed(self):
        return all([not self.hidden, not self.widget.isHidden])


class Display(object):

    _apps: dict[str, App] = {}
    _client: Client = None
    _items: list[DisplayItem] = []
    _current_idx: int = 0
    _widgets: dict[str, BaseWidget] = {}

    def __init__(self, client: Client):
        self._client = client
        self._apps = client.get_apps()
        BaseWidget.register(self._client)
        self.__init()

    def __init(self):
        lametricaps = Config.lametric.apps
        for name in Config.display:
            app: LametricApp = lametricaps.get(name)
            Widget: Widget = self.getWidget(name, app.package)
        self._items = [
            DisplayItem(
                app=lametricaps.get(name),
                widget=self.getWidget(name, app.package),
                duration=app.duration,
                hidden=False
            )
            for name in Config.display
        ]

    def load(self, content_type: CONTENT_TYPE, payload):
        match(content_type):
            case CONTENT_TYPE.NOWPLAYING:
                self._widgets.get("yanko").nowplaying(payload)
            case CONTENT_TYPE.YANKOSTATUS:
                self._widgets.get("yanko").yankostatus(payload)

    def get_next_idx(self):
        next_idx = self._current_idx + 1
        if len(self._items) > next_idx:
            self._current_idx = next_idx
        else:
            self._current_idx = 0

    def update(self):
        current = self._items[self._current_idx]
        if not current.isAllowed:
            return self.get_next_idx()
        if not current.isActive:
            return current.activate()
        if current.isExpired:
            current.deactivate()
            return self.get_next_idx()

    def getWidget(self, name, package_name):
        app_widgets = self._apps.get(package_name).widgets
        first_key = list(app_widgets.keys()).pop(0)
        widget_data = app_widgets.get(first_key)
        if name not in self._widgets:
            match(name):
                case 'clock':
                    self._widgets['clock'] = ClockWidget(
                        first_key, widget_data)
                case 'weather':
                    self._widgets['weather'] = WeatherWidget(
                        first_key, widget_data)
                case 'yanko':
                    self._widgets['yanko'] = YankoWidget(
                        first_key, widget_data)
        return self._widgets.get(name)
