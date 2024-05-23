from app.lametric.models import APPNAME, Content, ContentFrame
from .base import BaseWidget, WidgetMeta
from pydantic import BaseModel


class NowData(BaseModel):
    temp: float
    humid: float


class TermoWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass

    def nowdata(self, payload):
        data = NowData(**payload)
        frames = [
            ContentFrame(text=f"{data.temp}", icon=2369, duration=6),
            ContentFrame(text=f"{data.humid}%", icon=2369, duration=4),
        ]
        TermoWidget.client.send_model_api2(APPNAME.TERMO, Content(frames=frames))
        return True
