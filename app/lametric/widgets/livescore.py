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
from app.lametric.widgets.items.subscriptions import Subscriptions, Scores


class LivescoresWidget(SubscriptionWidget, metaclass=WidgetMeta):

    subscriptions: Subscriptions = None
    scores: Scores = {}
    __loaded = False

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.subscriptions = Subscriptions.livescores
        self.scores = Scores(())
        if self.subscriptions:
            self.update_frames()

    def cancel_sub(self, sub: SubscriptionEvent):
        ZnaykoClient.unsubscribe(sub)

    def onShow(self):
        do_update = False
        for sub in self.subscriptions.events:
            if sub.inProgress:
                do_update = True
                break
        if do_update:
            self.update_frames()

    def onHide(self):
        expired = []
        for k, sub in self.subscriptions.items():
            __class__.hasLivescoreGamesInProgress = sub.inProgress
            if sub.isExpired:
                expired.append[k]
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
        for idx, sub in enumerate(self.subscriptions.events):
            text = []
            text.append(sub.displayStatus)
            text.append(sub.event_name)
            score = self.scores.get(sub.event_id, "")
            if score:
                text.append(score)
            frame = ContentFrame(
                text=' '.join(text),
                index=idx,
                icon=sub.icon,
                duration=0
            )
            frames.append(frame)
        __class__.client.send_model(
            APPNAME.LIVESCORES, Content(frames=frames)
        )

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            if not event.is_old_event:
                sub: SubscriptionEvent = self.subscriptions.get(event.event_id)
                if not sub:
                    continue
                try:
                    act = ACTION(event.action)
                    if act == ACTION.HALF_TIME:
                        sub.status = 'HT'
                    elif act == ACTION.PROGRESS:
                        sub.status = f"{event.time}'"
                        self.subscriptions[event.event_id] = sub
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
                except ValueError:
                    pass
            if event.score:
                self.scores[event.event_id] = event.score
        self.update_frames()

    def on_cancel_job_event(self, event: CancelJobEvent):
        sub = next(filter(lambda x: x.jobId ==
                          event.jobId, self.subscriptions.events), None)
        if sub:
            del self.subscriptions[f"{sub.event_id}"]

    def on_subscribed_event(self, event: SubscriptionEvent):
        self.subscriptions[f"{event.event_id}"] = event
        self.update_frames()

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        del self.subscriptions[f"{event.event_id}"]
        logging.warning(f"DELETING {event.event_name}")
        self.update_frames()
