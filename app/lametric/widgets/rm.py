import logging
from re import L
from .base import BaseWidget, WidgetMeta
from app.znayko.models import (
    Game
)
from app.znayko.client import Client as ZnaykoClient
from cachable.storage import Storage
import pickle

TEAM_ID = 131
STORAGE_KEY = "real_madrid_schedule"


class Schedule(dict):

    def __init__(self, data: list[Game]):
        d = {f"{game.id}":game for game in data}
        logging.warning(d)
        super().__init__(d)

    def persist(self):
        d = {k:pickle.dumps(v) for k,v in self.items()}
        logging.warning(d)
        Storage.pipeline().hmset(STORAGE_KEY, d).persist(STORAGE_KEY).execute()

    @classmethod
    def load(cls) -> 'Schedule':
        data = Storage.hgetall(STORAGE_KEY)
        games = [pickle.loads(v) for v in data.values()]
        return cls(games)

class RMWidget(BaseWidget, metaclass=WidgetMeta):

    _schedule: Schedule = None

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.load()
        logging.warning(self._schedule)

    def onShow(self):
        pass

    def onHide(self):
        pass

    def load(self):
        if not Storage.exists(STORAGE_KEY):
            schedule = self.get_schedule()
            self._schedule = Schedule(schedule)
            self._schedule.persist()
        else:
            self._schedule = Schedule.load()


    def get_schedule(self):
        schedule = ZnaykoClient.team_schedule(TEAM_ID)
        logging.warning(schedule)
        return schedule


    # def on_event(self, payload):
    #     if isinstance(payload, list):
    #         try:
    #             self.on_match_events(
    #                 MatchEvent.schema().load(payload, many=True))
    #         except Exception as e:
    #             logging.error(e)
    #             logging.warning(payload)
    #     else:
    #         self.on_subscription_event(payload)

    # def on_match_events(self, events: list[MatchEvent]):
    #     for event in events:
    #         logging.warning(event)
    #         if not event.is_old_event:
    #             sub = next(filter(lambda x: x.event_id ==
    #                        event.event_id, self.subscriptions), None)
    #             frame = event.getContentFrame(
    #                 league_icon=sub.icon if sub else None)
    #             __class__.client.send_notification(Notification(
    #                 model=Content(
    #                     frames=[frame],
    #                     sound=event.getIcon()
    #                 ),
    #                 priority='critical'
    #             ))
    #         if event.score:
    #             self.scores[event.event_id] = event.score
    #     if self.scores.has_changes:
    #         self.update_frames()

    # def on_subscription_event(self, payload):
    #     action = ACTION(payload.get("action"))
    #     if action == ACTION.CANCEL_JOB:
    #         event = CancelJobEvent.from_dict(payload)
    #         sub = next(filter(lambda x: x.jobId ==
    #                    event.jobId, self.subscriptions), None)
    #         if sub:
    #             Storage.pipeline().hdel(STORAGE_KEY, f"{sub.event_id}").persist(STORAGE_KEY).execute()
    #     elif action == ACTION.SUBSCRIBED:
    #         event: SubscriptionEvent = SubscriptionEvent.from_dict(payload)
    #         logging.warning(event)
    #         Storage.pipline().hset(STORAGE_KEY, f"{event.event_id}", pickle.dumps(event)).persist(STORAGE_KEY).execute()
    #     else:
    #         event: SubscriptionEvent = SubscriptionEvent.from_dict(payload)
    #         Storage.pipline().hdel(STORAGE_KEY, f"{event.event_id}").persist(STORAGE_KEY).execute()
    #         logging.warning(f"DELETING {event.event_name}")
    #     self.load()
    #     self.update_frames()
