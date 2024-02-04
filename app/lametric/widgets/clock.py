
from .base import BaseWidget, WidgetMeta


class ClockWidget(BaseWidget, metaclass=WidgetMeta):

    def onShow(self):
        pass

    def onHide(self):
        pass

class SydneyWidget(ClockWidget):
    pass