from enum import IntEnum
from .base import BaseWidget, WidgetMeta


class EventIcon(IntEnum):

    GOAL = 8627


class LivescoresWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass
