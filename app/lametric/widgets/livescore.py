import logging
from app.lametric.models import APPNAME, Content, ContentFrame, Notification, STORAGE_KEY
from .base import SubscriptionWidget, WidgetMeta
from cachable.storage import Storage
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
        # self.load()
        if self.subscriptions:
            # self.load_scores()
            self.update_frames()

    def cancel_sub(self, sub: SubscriptionEvent):
        ZnaykoClient.unsubscribe(sub)

    def onShow(self):
        do_update = False
        for sub in self.subscriptions:
            if sub.inProgress:
                do_update = True
                break
        if do_update:
            # self.load_scores()
            self.update_frames()

    def onHide(self):
        pipe = Storage.pipeline()
        has_changes = False
        for sub in self.subscriptions:
            __class__.hasLivescoreGamesInProgress = sub.inProgress
            if sub.isExpired:
                pipe.hdel(STORAGE_KEY, f"{sub.event_id}")
                has_changes = True
        if has_changes:
            pipe.persist(STORAGE_KEY).execute()
            # self.load()
            self.update_frames()

    def duration(self, duration: int):
        res = len(self.subscriptions) * duration
        return res

    @property
    def isHidden(self):
        # if not self.__loaded:
        #     self.load()
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
                sub = self.subscriptions.get(event.event_id)
                if not sub:
                    continue
                try:
                    act = ACTION(event.action)
                    if act == ACTION.HALF_TIME:
                        sub.status = 'HT'
                except ValueError:
                    pass
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
                self.scores[event.event_id] = event.score
        self.update_frames()

    def on_cancel_job_event(self, event: CancelJobEvent):
        sub = next(filter(lambda x: x.jobId ==
                          event.jobId, self.subscriptions), None)
        if sub:
            Storage.pipeline().hdel(STORAGE_KEY.LIVESCORES.value, f"{sub.event_id}").persist(
                STORAGE_KEY.LIVESCORES.value).execute()

    def on_subscribed_event(self, event: SubscriptionEvent):
        self.subscriptions[f"{event.event_id}"] = event
        self.update_frames()

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        del self.subscriptions[f"{event.event_id}"]
        logging.warning(f"DELETING {event.event_name}")
        self.update_frames()
