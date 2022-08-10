import logging
from app.lametric.models import APPNAME, Content, ContentFrame, Notification
from .base import SubscriptionWidget, WidgetMeta
from cachable.storage import Storage
import pickle
from app.znayko.models import (
    SubscriptionEvent,
    CancelJobEvent,
    MatchEvent,
)
from app.znayko.client import Client as ZnaykoClient


STORAGE_KEY = "subscriptions"


class Scores(dict):

    __has_changes = False

    def __setitem__(self, __k, __v) -> None:
        if self.get(__k, "") != __v:
            self.__has_changes = True
        return super().__setitem__(__k, __v)

    def __delitem__(self, __v) -> None:
        return super().__delitem__(__v)

    @property
    def has_changes(self):
        res = self.__has_changes
        self.__has_changes = False
        return res


class LivescoresWidget(SubscriptionWidget, metaclass=WidgetMeta):

    subscriptions: list[SubscriptionEvent] = []
    scores: Scores = {}

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.scores = Scores(())
        self.load()
        if self.subscriptions:
            # for sub in self.subscriptions:
            #     if sub.isExpired:
            #         self.cancel_sub(sub)
            self.load_scores()
            self.update_frames()

    def load(self):
        data = Storage.hgetall(STORAGE_KEY)
        if not data:
            self.subscriptions = []
        self.subscriptions = [pickle.loads(v) for v in data.values()]

    def load_scores(self):
        data = ZnaykoClient.livescores()
        ids = [x.event_id for x in self.subscriptions]
        events = list(filter(lambda x: x.idEvent in ids, data))
        if not len(events):
            return
        store = Storage.pipeline()
        for event in events:
            text = event.displayScore
            sub = next(filter(lambda x: x.event_id ==
                       event.idEvent, self.subscriptions), None)
            if not sub:
                return
            sub.status = event.displayStatus
            store.hset(STORAGE_KEY, f"{sub.event_id}", pickle.dumps(sub))
            self.scores[event.idEvent] = text
        store.persist(STORAGE_KEY).execute()

    def cancel_sub(self, sub: SubscriptionEvent):
        ZnaykoClient.unsubscribe(sub)

    def onShow(self):
        do_update = False
        for sub in self.subscriptions:
            if sub.inProgress:
                do_update = True
                break
        if do_update:
            self.load_scores()
            self.update_frames()

    def onHide(self):
        pipe = Storage.pipeline()
        has_changes = False
        for sub in self.subscriptions:
            if sub.isExpired:
                pipe.hdel(STORAGE_KEY, f"{sub.event_id}")
                has_changes = True
        if has_changes:
            pipe.persist(STORAGE_KEY).execute()
            self.load()
            self.update_frames()

    def duration(self, duration: int):
        res = len(self.subscriptions) * 8000
        return res

    @property
    def isHidden(self):
        return len(self.subscriptions) == 0

    def update_frames(self):
        frames = []
        for idx, sub in enumerate(self.subscriptions):
            text = []
            text.append(sub.status)
            text.append(sub.event_name)
            score = self.scores.get(sub.event_id, "")
            if score:
                text.append(score)
            frame = ContentFrame(
                text=' '.join(text),
                index=idx,
                icon=sub.icon
            )
            frames.append(frame)
        __class__.client.send_model(
            APPNAME.LIVESCORES, Content(frames=frames)
        )

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            logging.warning(event)
            if not event.is_old_event:
                sub = next(filter(lambda x: x.event_id ==
                           event.event_id, self.subscriptions), None)
                frame = event.getContentFrame(
                    league_icon=sub.icon if sub else None)
                __class__.client.send_notification(Notification(
                    model=Content(
                        frames=[frame],
                        sound=event.getIcon()
                    ),
                    priority='critical'
                ))
            if event.score:
                self.scores[event.event_id] = event.score
        if self.scores.has_changes:
            self.update_frames()

    def on_cancel_job_event(self, event: CancelJobEvent):
        sub = next(filter(lambda x: x.jobId ==
                          event.jobId, self.subscriptions), None)
        if sub:
            Storage.pipeline().hdel(STORAGE_KEY, f"{sub.event_id}").persist(
                STORAGE_KEY).execute()

    def on_subscribed_event(self, event: SubscriptionEvent):
        logging.warning(event)
        Storage.pipline().hset(STORAGE_KEY, f"{event.event_id}", pickle.dumps(
            event)).persist(STORAGE_KEY).execute()
        self.load()
        self.update_frames()

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        Storage.pipline().hdel(STORAGE_KEY, f"{event.event_id}").persist(
            STORAGE_KEY).execute()
        logging.warning(f"DELETING {event.event_name}")
        self.load()
        self.update_frames()
