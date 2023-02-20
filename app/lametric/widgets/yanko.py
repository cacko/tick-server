from app.lametric.models import (
    Widget,
    NowPlayingFrame,
    Notification,
    Content,
    MUSIC_STATUS,
    APPNAME
)
from app.yanko import Yanko
from .base import BaseWidget, WidgetMeta
from app.core.events import EventManager, BUTTON_EVENTS
import logging


class YankoWidget(BaseWidget, metaclass=WidgetMeta):

    status: MUSIC_STATUS

    def __init__(self, widget_id: str, widget: Widget, **kwargs):
        super().__init__(widget_id, widget, **kwargs)
        EventManager.listen(BUTTON_EVENTS.YANKO_PLAY_PAUSE, Yanko.toggle)
        EventManager.listen(BUTTON_EVENTS.YANKO_NEXT, Yanko.next)
        self.yankostatus(Yanko.state())

    def onShow(self):
        pass

    def onHide(self):
        pass

    @property
    def isHidden(self):
        return (self.status in [MUSIC_STATUS.STOPPED, MUSIC_STATUS.EXIT])

    def nowplaying(self, payload):
        frame = NowPlayingFrame(**payload)
        self.status = MUSIC_STATUS.PLAYING
        YankoWidget.client.send_notification(Notification(
            model=Content(
                frames=[frame],
            ),
            priority='critical'
        ))
        YankoWidget.client.send_model(APPNAME.YANKO, Content(frames=[frame]))
        return True

    def yankostatus(self, payload):
        logging.debug(payload)
        try:
            self.status = MUSIC_STATUS(payload.get("status"))
        except ValueError:
            self.status = MUSIC_STATUS.STOPPED
