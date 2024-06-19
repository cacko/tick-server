from enum import StrEnum
from app.lametric.models import APPNAME, Content, ContentFrame
from .base import BaseWidget, WidgetMeta
from pydantic import BaseModel


class SensorLocation(StrEnum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"


class NowData(BaseModel):
    temp: float
    humid: float
    location: SensorLocation

    @property
    def temp_icon(self):
        temp = self.temp
        match temp:
            case temp if temp > 25:
                return 5324
            case temp if temp > 10:
                return 5836
            case _:
                return 3425

    @property
    def humud_icon(self):
        humid = self.humid
        match humid:
            case humid if humid > 80:
                return 43363
            case humid if humid > 30:
                return 3359
            case _:
                return 32960


class TermoWidget(BaseWidget, metaclass=WidgetMeta):

    __nextFrames: list[ContentFrame] = []
    
    def activate(self):
        try:
            assert len(self.__nextFrames)
            frames, self.__nextFrames = self.__nextFrames, []
            TermoWidget.client.send_model_api2(APPNAME.TERMO, Content(frames=frames))
        except AssertionError:
            pass

    def onShow(self):
        pass

    def onHide(self):
        pass

    def nowdata(self, payload):
        try:
            data = NowData(**payload)
            assert data.location == SensorLocation.INDOOR
            self.__nextFrames = [
                ContentFrame(
                    text=f"{data.temp}°", icon=data.temp_icon, duration=10, index=0
                ),
                ContentFrame(
                    text=f"{data.humid}%", icon=data.humud_icon, duration=8, index=1
                ),
            ]
            return True
        except AssertionError:
            pass
