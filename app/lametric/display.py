import logging
from app.lametric.widgets.base import BaseWidget
from app.config import LametricApp
from app.lametric.client import Client
from app.lametric.models import CONTENT_TYPE, App, APPNAME, DeviceDisplay, Widget
from app.config import Config
from time import time
from app.lametric.widgets import (
    RMWidget,
    YankoWidget,
    ClockWidget,
    LivescoresWidget,
    WeatherWidget,
    DatetickerWidget,
    SydneyWidget,
)
from typing import Optional
from typing import Any
from pydantic import BaseModel, Extra, Field, validator
import json


class DisplayItem(BaseModel):
    app: LametricApp
    widget: BaseWidget
    duration: int
    appname: APPNAME
    hidden: bool = Field(default=False)
    activated_at: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.ignore

    @validator("widget")
    def widget_val(cls, v):
        return v

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
            duration = self.widget.duration(self.duration)
            return (time() - self.activated_at) > duration
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
                _ = self.getWidget(APPNAME(name), app.package, **app.model_dump())
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
        logging.warning(">>>> END INIT")

    def on_response(self, content_type: CONTENT_TYPE, payload):
        payload_struct = json.loads(payload) if isinstance(payload, str) else payload
        match (content_type):
            case CONTENT_TYPE.NOWPLAYING:
                self.invoke_widget(
                    name=APPNAME.YANKO, method="nowplaying", payload=payload_struct
                )
            case CONTENT_TYPE.YANKOSTATUS:
                self.invoke_widget(
                    name=APPNAME.YANKO, method="yankostatus", payload=payload_struct
                )
            case CONTENT_TYPE.LIVESCOREEVENT:
                payload_struct = self.invoke_widget(
                    name=APPNAME.RM, method="on_event", payload=payload_struct
                )
                # payload = self.invoke_widget(
                #     name=APPNAME.LA_LIGA, method="on_event", payload=payload
                # )
                # payload = self.invoke_widget(
                #     name=APPNAME.PREMIER_LEAGUE,
                # method="on_event",
                # payload=payload
                # )
                # payload = self.invoke_widget(
                #     name=APPNAME.WORLDCUP, method="on_event", payload=payload
                # )
                self.invoke_widget(
                    name=APPNAME.LIVESCORES, method="on_event", payload=payload_struct
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
        try:
            if self.is_screensaver_active:
                if self._current_idx != 0:
                    self._current_idx = 0
                    current = self._items[0]
                    current.activate()
                return 0
        except AssertionError:
            pass

        try:
            current = self._items[self._current_idx]
        except Exception as e:
            logging.exception(e)
            return self.get_next_idx()

        if not current.isAllowed:
            return self.get_next_idx()
        if not current.isActive:
            return current.activate()
        if current.isExpired:
            current.deactivate()
            return self.get_next_idx()

    def getWidget(self, name: APPNAME, package_name: str, **kwargs) -> BaseWidget:
        app = self._apps.get(package_name)
        widget_id = kwargs.get("widget_id", "")
        assert widget_id
        del kwargs["widget_id"]
        assert isinstance(app, App)
        app_widgets = app.widgets
        assert isinstance(app_widgets, dict)
        assert isinstance(widget_id, str)
        widget_data = app_widgets[widget_id]
        assert isinstance(widget_data, Widget)
        if name not in self._widgets:
            match (name):
                case APPNAME.CLOCK:
                    self._widgets[name.value] = ClockWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.SYDNEY:
                    self._widgets[name.value] = SydneyWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.WEATHER:
                    self._widgets[name.value] = WeatherWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.DATETICKER:
                    self._widgets[name.value] = DatetickerWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.YANKO:
                    self._widgets[name.value] = YankoWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.RM:
                    self._widgets[name.value] = RMWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.LIVESCORES:
                    self._widgets[name.value] = LivescoresWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                # case APPNAME.WORLDCUP:
                #     self._widgets[name.value] = WorldCupWidget(
                #         widget_id=widget_id, widget=widget_data, **kwargs
                #     )
                # case APPNAME.LA_LIGA:
                #     self._widgets[name.value] = LaLigaWidget(
                #         widget_id=widget_id, widget=widget_data, **kwargs
                #     )
                # case APPNAME.PREMIER_LEAGUE:
                #     self._widgets[name.value] = PremierLeagueWidget(
                #         widget_id=widget_id, widget=widget_data, **kwargs
                #     )
        res = self._widgets.get(name.value)
        assert isinstance(res, BaseWidget)
        return res
