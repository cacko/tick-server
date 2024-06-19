import logging
from queue import Queue
import sys
from xml.etree.ElementTree import QName

import rich
from app.lametric.widgets.base import BaseWidget
from app.config import LametricApp
from app.lametric.client import Client
from app.lametric.models import CONTENT_TYPE, App, APPNAME, DeviceDisplay, Widget
from app.config import app_config
from time import time
from app.lametric.widgets import (
    RMWidget,
    YankoWidget,
    ClockWidget,
    LivescoresWidget,
    WorldCupWidget,
    WeatherWidget,
    DatetickerWidget,
    SydneyWidget,
)
from typing import List, Optional
from typing import Any
from pydantic import BaseModel, Extra, Field, validator
import json

from app.lametric.widgets.sure import SureWidget
from app.lametric.widgets.termo import TermoWidget


class DisplayItem(BaseModel, arbitrary_types_allowed=True):
    app: LametricApp
    widget: BaseWidget
    duration: int
    appname: APPNAME
    hidden: bool = Field(default=False)
    activated_at: Optional[float] = None

    class app_config:
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
        try:
            assert self.isActive
            self.activated_at = None
            self.widget.onHide()
        except AssertionError:
            pass

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


class RepeatingItems(list):

    def drop(self) -> DisplayItem:
        res = super().pop(0)
        self.append(res)
        return res


class Display(object):
    _apps: dict[str, App] = {}
    _client: Client
    _current: DisplayItem = None
    _widgets: dict[str, BaseWidget] = {}
    _device_display: DeviceDisplay

    def __init__(self, client: Client):
        self._client = client
        self._apps = client.get_apps()
        BaseWidget.register(self._client)
        self._device_display = self._client.get_display()
        self._items: RepeatingItems[DisplayItem] = RepeatingItems([])
        self._saveritems: RepeatingItems[DisplayItem] = RepeatingItems([])
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
        lametricaps = app_config.lametric.apps
        # for name in app_config.display:
        #     try:
        #         app = lametricaps.get(name)
        #         assert isinstance(app, LametricApp)
        #         _ = self.getWidget(APPNAME(name), app.package, **app.model_dump())
        #     except AssertionError:
        #         pass

        for name in app_config.display:
            try:
                app = lametricaps.get(name)
                assert isinstance(app, LametricApp)
                assert isinstance(app.duration, int)
                self._items.append(
                    DisplayItem(
                        app=app,
                        widget=self.getWidget(APPNAME(name), app.package, **app.model_dump()),
                        duration=app.duration,
                        hidden=False,
                        appname=APPNAME(name),
                    )
                )
            except AssertionError as e:
                pass

        for name in app_config.display:
            try:
                app = lametricaps.get(name)
                assert isinstance(app, LametricApp)
                assert isinstance(app.duration, int)
                self._saveritems.append(
                    DisplayItem(
                        app=app,
                        widget=self.getWidget(APPNAME(name), app.package),
                        duration=app.duration,
                        hidden=False,
                        appname=APPNAME(name),
                    )
                )
            except AssertionError as e:
                pass

    def on_response(self, content_type: CONTENT_TYPE, payload):
        payload_struct = json.loads(payload) if isinstance(payload, str) else payload
        match (content_type):
            case CONTENT_TYPE.NOWPLAYING:
                self.invoke_widget(
                    name=APPNAME.YANKO, method="nowplaying", payload=payload_struct
                )
            case CONTENT_TYPE.SURE:
                self.invoke_widget(
                    name=APPNAME.SURE, method="bestoffer", payload=payload_struct
                )
            case CONTENT_TYPE.TERMO:
                self.invoke_widget(
                    name=APPNAME.TERMO, method="nowdata", payload=payload_struct
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
                payload = self.invoke_widget(
                    name=APPNAME.WORLDCUP, method="on_event", payload=payload
                )
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

    def update(self):
        try:
            assert self._current
            assert self._current.isAllowed
        except AssertionError:
            self._current = (
                self._saveritems.drop()
                if self.is_screensaver_active
                else self._items.drop()
            )
            logging.info(f"new item {self._current}")
        try:
            assert self._current.isAllowed
            assert not self._current.isExpired
            if not self._current.isActive:
                self._current.activate()
        except AssertionError:
            self._current.deactivate()
            self._current = None


    def getWidget(self, name: APPNAME, package_name: str, **kwargs) -> BaseWidget:
        if name not in self._widgets:
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
            match (name):
                case APPNAME.CLOCK:
                    self._widgets[name.value] = ClockWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.SYDNEY:
                    self._widgets[name.value] = SydneyWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.TERMO:
                    self._widgets[name.value] = TermoWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                case APPNAME.SURE:
                    self._widgets[name.value] = SureWidget(
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
                case APPNAME.WORLDCUP:
                    self._widgets[name.value] = WorldCupWidget(
                        widget_id=widget_id, widget=widget_data, **kwargs
                    )
                # case APPNAME.LA_LIGA:
                #     self._widgets[name.value] = LaLigaWidget(
                #         widget_id=widget_id, widget=widget_data, **kwargs
                #     )
                # case APPNAME.PREMIER_LEAGUE:
                #     self._widgets[name.value] = PremierLeagueWidget(
                #         widget_id=widget_id, widget=widget_data, **kwargs
                #     )
        res = self._widgets.get(name.value)
        logging.info(res)
        assert isinstance(res, BaseWidget)
        return res
