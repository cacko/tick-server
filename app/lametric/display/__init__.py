

from app.config import LametricApp
from app.lametric.client import Client
from app.lametric.models import (
    CONTENT_TYPE,
    App,
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


class WidgetMeta(type):

    _instances = {}
    client: Client = None

    def __call__(cls, widget: Widget, *args, **kwds):
        if cls not in cls._instances:
            cls._instances[cls] = type.__call__(cls, widget, *args, **kwds)
        return cls._instances[cls]

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


class ClockWidget(BaseWidget):

    def onShow(self):
        pass

    def onHide(self):
        pass


class WeatherWidget(BaseWidget):

    def onShow(self):
        pass

    def onShow(self):
        pass


class YankoWidget(BaseWidget):

    def onShow(self):
        pass

    def onHide(self):
        pass

    def nowplaying(self, payload):
        frame = NowPlayingFrame(**payload)
        __class__.client.send_notification(Notification(
            model=Content(frames=[frame]),
            priority='critical'
        ))
        __class__.client.send_model('yanko', Content(frames=[frame]))
        return True

    def yankostatus(self, payload):
        try:
            status = MUSIC_STATUS(payload.get("status"))
            if status == MUSIC_STATUS.EXIT:
                return True
        except ValueError:
            pass
        return False


class NowPlayingWidget(YankoWidget):
    pass


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DisplayItem:
    app: LametricApp
    widget: BaseWidget
    duration: int
    hidden: bool = False
    activated_at: Optional[datetime] = None


class Display(object):

    _apps: dict[str, App] = {}
    _client: Client = None
    _items: list[DisplayItem] = []
    _frames: list[DisplayItem] = []
    _current_frame: DisplayItem = None
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
              

    def update(self):
        if not len(self._frames):
            self._frames = self._items[:]
        if not self._current_frame:
            self._current_frame = self._frames.pop(0)
        if not self._current_frame.activated_at:
            self._current_frame.widget.activate()
            self._current_frame.activated_at = datetime.now()
            self._current_frame.widget.onShow()
            return
        td = datetime.now() - self._current_frame.activated_at
        if td > timedelta(milliseconds=self._current_frame.duration):
            self._current_frame.widget.onHide()
            self._current_frame = self._frames.pop(0)
            self._current_frame.widget.activate()
            self._current_frame.activated_at = datetime.now()
            self._current_frame.widget.onShow()

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
