from app.lametric.widgets.base import BaseWidget
from app.config import LametricApp
from app.lametric.client import Client
from app.lametric.models import CONTENT_TYPE, App, APPNAME, DeviceDisplay, Widget
from app.config import Config
from dataclasses import dataclass
from time import time
from dataclasses_json import dataclass_json, Undefined
from app.lametric.widgets import *
from typing import Optional
from typing import Any
import logging


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DisplayItem:
    app: LametricApp
    widget: BaseWidget
    duration: int
    appname: APPNAME
    hidden: bool = False
    activated_at: Optional[float] = None

    def activate(self):
        self.widget.activate()
        self.activated_at = time()
        self.widget.onShow()

    def deactivate(self):
        self.activated_at = None
        self.widget.onHide()

    @property
    def isExpired(self):
        try:
            assert self.activated_at
            return time() - self.activated_at > self.widget.duration(self.duration)
        except AssertionError:
            return False

    @property
    def isActive(self):
        return self.activated_at is not None

    @property
    def isAllowed(self):
        return not (self.hidden or self.widget.isHidden)


class Display(object):

    _apps: dict[str, App] = {}
    _client: Client
    _items: list[DisplayItem] = []
    _current_idx: int = 0
    _widgets: dict[str, BaseWidget] = {}
    _device_display: DeviceDisplay

    def __init__(self, client: Client):
        self._client = client
        self._apps = client.get_apps()
        BaseWidget.register(self._client)
        self._device_display = self._client.get_display()
        self.__init()

    @property
    def is_screensaver_active(self):
        if self._device_display.needs_update:
            self._device_display = self._client.get_display()
        if not self._device_display.screensaver.enabled:
            return False
        if not self._device_display.screensaver.modes.time_based.enabled:
            return False
        return self._device_display.screensaver.modes.time_based.isActive

    def __init(self):
        lametricaps = Config.lametric.apps
        for name in Config.display:
            try:
                app = lametricaps.get(name)
                assert isinstance(app, LametricApp)
                Widget = self.getWidget(APPNAME(name), app.package, **app.to_dict())  # type: ignore
            except AssertionError:
                pass

        items = []
        for name in Config.display:
            try:
                app = lametricaps.get(name)
                assert isinstance(app, LametricApp)
                assert isinstance(app.duration, int)
                items.append(
                    DisplayItem(
                        app=app,
                        widget=self.getWidget(APPNAME(name), app.package),
                        duration=app.duration,
                        hidden=False,
                        appname=APPNAME(name),
                    )
                )
            except AssertionError:
                pass
        self._items = items[:]

    def on_response(self, content_type: CONTENT_TYPE, payload):
        match (content_type):
            case CONTENT_TYPE.NOWPLAYING:  # type: ignore
                self.invoke_widget(
                    name=APPNAME.YANKO, method="nowplaying", payload=payload
                )
            case CONTENT_TYPE.YANKOSTATUS:
                self.invoke_widget(
                    name=APPNAME.YANKO, method="yankostatus", payload=payload
                )
            case CONTENT_TYPE.LIVESCOREEVENT:
                payload = self.invoke_widget(
                    name=APPNAME.RM, method="on_event", payload=payload
                )
                payload = self.invoke_widget(
                    name=APPNAME.LA_LIGA, method="on_event", payload=payload
                )
                payload = self.invoke_widget(
                    name=APPNAME.PREMIER_LEAGUE, method="on_event", payload=payload
                )
                payload = self.invoke_widget(
                    name=APPNAME.WORLDCUP, method="on_event", payload=payload
                )
                self.invoke_widget(
                    name=APPNAME.LIVESCORES, method="on_event", payload=payload
                )

    def invoke_widget(self, name: APPNAME, method: str, payload: Any):
        try:
            wdg = self._widgets.get(name.value)
            assert isinstance(wdg, BaseWidget)
            assert hasattr(wdg, method)
            assert callable(getattr(wdg, method))
            return getattr(wdg, method)(payload)
        except AssertionError:
            return payload

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

    def getWidget(self, name: APPNAME, package_name: str, **kwargs) -> BaseWidget:
        app = self._apps.get(package_name)
        assert isinstance(app, App)
        app_widgets = app.widgets
        assert isinstance(app_widgets, dict)
        first_key = list(app_widgets.keys()).pop(0)
        assert isinstance(first_key, str)
        widget_data = app_widgets.get(first_key)
        assert isinstance(widget_data, Widget)
        if name not in self._widgets:
            match (name):
                case APPNAME.CLOCK:
                    self._widgets[name.value] = ClockWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
                case APPNAME.WEATHER:
                    self._widgets[name.value] = WeatherWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
                case APPNAME.YANKO:
                    self._widgets[name.value] = YankoWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
                case APPNAME.RM:
                    self._widgets[name.value] = RMWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
                case APPNAME.LIVESCORES:
                    self._widgets[name.value] = LivescoresWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
                case APPNAME.WORLDCUP:
                    self._widgets[name.value] = WorldCupWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
                case APPNAME.LA_LIGA:
                    self._widgets[name.value] = LaLigaWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
                case APPNAME.PREMIER_LEAGUE:
                    self._widgets[name.value] = PremierLeagueWidget(
                        widget_id=first_key, widget=widget_data, **kwargs
                    )
        res = self._widgets.get(name.value)
        assert isinstance(res, BaseWidget)
        return res
