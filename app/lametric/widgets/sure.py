import logging
from typing import Optional
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

    nextFrames: list[ContentFrame] = []
    
        
    def onShow(self):
        pass
        
    @property
    def isHidden(self):
        return len(self.nextFrames) == 0

    def onHide(self):
        pass

    def bestoffer(self, payload):
        try:
            data = BestOffer(**payload)
            self.nextFrames = [
                ContentFrame(
                    text=f"{data.total:.02f}",
                    icon=data.total_icon,
                    duration=10,
                    index=0,
                ),
                ContentFrame(
                    text=f"{data.per_night:.02f}",
                    icon=data.per_night_icon,
                    duration=10,
                    index=1,
                ),
            ]
            SureWidget.client.send_model_api2(APPNAME.SURE, Content(frames=self.nextFrames))
            return True
        except AssertionError as e:
            logging.exception(e)
            pass
