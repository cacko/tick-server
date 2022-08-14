import logging
import time
from app.lametric.widgets.base import BaseWidget
from app.config import LametricApp
from app.lametric.client import Client
from app.lametric.models import (
    CONTENT_TYPE,
    App,
    APPNAME,
    DeviceDisplay
)
from app.config import Config
from dataclasses import dataclass
from time import time
from dataclasses_json import dataclass_json, Undefined
from app.lametric.widgets import *


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DisplayItem:
    app: LametricApp
    widget: BaseWidget
    duration: int
    appname: APPNAME
    hidden: bool = False
    activated_at: float = None

    def activate(self):
        self.widget.activate()
        self.activated_at = time()
        self.widget.onShow()

    def deactivate(self):
        self.activated_at = None
        self.widget.onHide()

    @property
    def isExpired(self):
        return time() - self.activated_at > self.widget.duration(self.duration)

    @property
    def isActive(self):
        return self.activated_at is not None

    @property
    def isAllowed(self):
        return not(self.hidden or self.widget.isHidden)


class Display(object):

    _apps: dict[str, App] = {}
    _client: Client = None
    _items: list[DisplayItem] = []
    _current_idx: int = 0
    _widgets: dict[str, BaseWidget] = {}
    _device_display: DeviceDisplay = None

    def __init__(self, client: Client):
        self._client = client
        self._apps = client.get_apps()
        BaseWidget.register(self._client)
        self._device_display = self._client.get_display()
        self.__init()

    @property
    def is_screensaver_active(self):
        if not self._device_display.screensaver.enabled:
            return False
        if not self._device_display.screensaver.modes.time_based.enabled:
            return False
        return self._device_display.screensaver.modes.time_based.isActive

    def __init(self):
        lametricaps = Config.lametric.apps
        for name in Config.display:
            app: LametricApp = lametricaps.get(name)
            Widget: Widget = self.getWidget(APPNAME(name), app.package)
        self._items = [
            DisplayItem(
                app=lametricaps.get(name),
                widget=self.getWidget(APPNAME(name), app.package),
                duration=app.duration,
                hidden=False,
                appname=APPNAME(name)
            )
            for name in Config.display
        ]

    def on_response(self, content_type: CONTENT_TYPE, payload):
        match(content_type):
            case CONTENT_TYPE.NOWPLAYING:
                self._widgets.get(APPNAME.YANKO).nowplaying(payload)
            case CONTENT_TYPE.YANKOSTATUS:
                self._widgets.get(APPNAME.YANKO).yankostatus(payload)
            case CONTENT_TYPE.LIVESCOREEVENT:
                payload = self._widgets.get(APPNAME.RM).on_event(payload)
                self._widgets.get(APPNAME.LIVESCORES).on_event(payload)

    def get_next_idx(self):
        next_idx = self._current_idx + 1
        if len(self._items) > next_idx:
            self._current_idx = next_idx
        else:
            self._current_idx = 0

    def update(self):
        if self.is_screensaver_active:
            if self._current_idx != 0:
                self._current_idx = 0
                current = self._items[0]
                current.activate()
            return 0
        
        current = self._items[self._current_idx]

        if not current.isAllowed:
            return self.get_next_idx()
        if not current.isActive:
            return current.activate()
        if current.isExpired:
            current.deactivate()
            return self.get_next_idx()

    def getWidget(self, name: APPNAME, package_name):
        app_widgets = self._apps.get(package_name).widgets
        first_key = list(app_widgets.keys()).pop(0)
        widget_data = app_widgets.get(first_key)
        if name not in self._widgets:
            match(name):
                case APPNAME.CLOCK:
                    self._widgets[name] = ClockWidget(
                        first_key, widget_data)
                case APPNAME.WEATHER:
                    self._widgets[name] = WeatherWidget(
                        first_key, widget_data)
                case APPNAME.YANKO:
                    self._widgets[name] = YankoWidget(
                        first_key, widget_data)
                case APPNAME.RM:
                    self._widgets[name] = RMWidget(first_key, widget_data)
                case APPNAME.LIVESCORES:
                    self._widgets[name] = LivescoresWidget(
                        first_key, widget_data)
        return self._widgets.get(name)
