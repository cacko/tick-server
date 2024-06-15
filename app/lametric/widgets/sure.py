from enum import StrEnum
from app.lametric.models import APPNAME, Content, ContentFrame
from .base import BaseWidget, WidgetMeta
from pydantic import BaseModel


class BestOffer(BaseModel):
    total: float
    per_night: float

    @property
    def total_icon(self):
        return 10329

    @property
    def per_night_icon(self):
        per_night = self.per_night
        match per_night:
            case per_night if per_night > 70:
                return 10773
            case humid if humid > 60:
                return 10772
            case _:
                return 10329


class SureWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass

    def bestoffer(self, payload):
        try:
            data = BestOffer(**payload)
            frames = [
                ContentFrame(
                    text=f"{data.total:.02f}°",
                    icon=data.total_icon,
                    duration=5,
                    index=0,
                ),
                ContentFrame(
                    text=f"{data.per_night}%",
                    icon=data.per_night_icon,
                    duration=10,
                    index=1,
                ),
            ]
            SureWidget.client.send_model_api2(APPNAME.SURE, Content(frames=frames))
            return True
        except AssertionError:
            pass
