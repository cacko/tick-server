import logging
from app.lametric.models import APPNAME, Content, ContentFrame, Notification, STORAGE_KEY
from .base import SubscriptionWidget, WidgetMeta
from app.znayko.models import (
    SubscriptionEvent,
    CancelJobEvent,
    MatchEvent,
    ACTION
)
from app.znayko.client import Client as ZnaykoClient
from app.lametric.widgets.items.subscriptions import Subscriptions
from app.core.events import EventManager, BUTTON_EVENTS


class LivescoresWidget(SubscriptionWidget, metaclass=WidgetMeta):

    subscriptions: Subscriptions = None

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.subscriptions = Subscriptions.livescores
        if self.subscriptions:
            self.update_frames()
        EventManager.listen(BUTTON_EVENTS.LIVESCORES_UNSUBSCRIBE, self.clear_all)
        EventManager.listen(BUTTON_EVENTS.LIVESCORES_CLEAN, self.clear_finished)


    def clear_all(self):
        logging.debug("TRIGGER CLEAR ALL")
        keys = [id for id in self.subscriptions.keys()]
        logging.debug(keys)

        logging.debug(keys)
        for id in keys:
            del self.subscriptions[id]   
        logging.debug(self.subscriptions)

    def clear_finished(self):
        keys = [id for id,ev in self.subscriptions.items() if ev.status == 'FT']
        for id in keys:
            del self.subscriptions[id]         

    def cancel_sub(self, sub: SubscriptionEvent):
        ZnaykoClient.unsubscribe(sub)

    def onHide(self):
        pass

    def onShow(self):
        expired = []
        for k, sub in self.subscriptions.items():
            __class__.hasLivescoreGamesInProgress = sub.inProgress
            if sub.isExpired:
                expired.append(k)
        if expired:
            for id in expired:
                del self.subscriptions[id]
            self.update_frames()

    def duration(self, duration: int):
        res = len(self.subscriptions) * duration
        return res

    @property
    def isHidden(self):
        return not len(self.subscriptions)

    def update_frames(self):
        frames = []
        logging.debug(f"UPDATE FRAMES")
        try:
            for idx, sub in enumerate(self.subscriptions.events):
                text = []
                text.append(sub.displayStatus)
                text.append(sub.event_name)
                if sub.score:
                    text.append(sub.score)
                frame = ContentFrame(
                    text=' '.join(text),
                    index=idx,
                    icon=sub.icon,
                    duration=0
                )
                frames.append(frame)
        except AttributeError as e:
            logging.error(e)
        __class__.client.send_model(
            APPNAME.LIVESCORES, Content(frames=frames)
        )

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            if event.is_old_event:
                continue
            sub: SubscriptionEvent = self.subscriptions.get(event.id)
            logging.debug(f"ON MATCH CALL {event}")
            if not sub:
                continue
            try:
                act = ACTION(event.action)
                if act == ACTION.HALF_TIME:
                    sub.status = 'HT'
                elif act == ACTION.PROGRESS:
                    sub.status = f"{event.time}'"
                else:
                    frame = event.getContentFrame(
                        league_icon=sub.icon if sub else None)
                    __class__.client.send_notification(Notification(
                        model=Content(
                            frames=[frame],
                            sound=event.getSound()
                        ),
                        priority='critical'
                    ))
                if event.score:
                    sub.score = event.score
                self.subscriptions[event.id] = sub
            except ValueError:
                pass
        self.update_frames()

    def on_cancel_job_event(self, event: CancelJobEvent):
        sub = next(filter(lambda x: x.jobId ==
                          event.jobId, self.subscriptions.events), None)
        if sub:
            del self.subscriptions[sub.id]

    def on_subscribed_event(self, event: SubscriptionEvent):
        self.subscriptions[event.id] = event
        self.update_frames()

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        del self.subscriptions[event.id]
        logging.warning(f"DELETING {event.event_name}")
        self.update_frames()
