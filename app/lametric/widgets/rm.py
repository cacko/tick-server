from datetime import datetime, timezone
import logging
from .base import BaseWidget, WidgetMeta
from app.znayko.models import (
    Game,
)
from app.lametric.models import (
    Content,
    ContentFrame,
    APPNAME
)
from zoneinfo import ZoneInfo
from app.znayko.client import Client as ZnaykoClient
from cachable.storage import Storage
from app.scheduler import Scheduler
import pickle

TEAM_ID = 131
STORAGE_KEY = "real_madrid_schedule"


def cron_func():
    games = ZnaykoClient.team_schedule(TEAM_ID)
    td = datetime.now(tz=timezone.utc).strftime('%m-%d')
    for game in games:
        gd = game.startTime.strftime('%m-%d')
        if td == gd:
            res = ZnaykoClient.subscribe(game.id)
            logging.warn(res)


def schedule_cron():
    Scheduler.add_job(
        id=STORAGE_KEY,
        name=f"{STORAGE_KEY}",
        func=cron_func,
        trigger="cron",
        hour=2,
        minutes=20,
        replace_existing=True,
        misfire_grace_time=180
    )


class Schedule(dict):

    def __init__(self, data: list[Game]):
        schedule_cron()
        d = {f"{game.id}": game for game in data}
        super().__init__(d)

    def persist(self):
        d = {k: pickle.dumps(v) for k, v in self.items()}
        Storage.pipeline().hmset(STORAGE_KEY, d).persist(STORAGE_KEY).execute()

    @classmethod
    def load(cls) -> 'Schedule':
        data = Storage.hgetall(STORAGE_KEY)
        games = [pickle.loads(v) for v in data.values()]
        return cls(games)

    def isIn(self, event_id: int):
        return f"{event_id}" in self

    @property
    def current(self) -> list[Game]:
        n = datetime.now(tz=timezone.utc)
        events = list(filter(lambda g: abs(
            (n - g.startTime).days) < 2, self.values()))
        return events


class RMWidget(BaseWidget, metaclass=WidgetMeta):

    _schedule: Schedule = None

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.load()
        if not self.isHidden:
            self.update_frames()

    def onShow(self):
        pass

    def onHide(self):
        pass

    def duration(self, duration: int):
        res = len(self._schedule.current) * 8000
        return res

    def update_frames(self):
        frames = []
        for idx, game in enumerate(self._schedule.current):
            text = []
            if game.not_started:
                text.append(game.startTime.astimezone(
                    ZoneInfo('Europe/London')).strftime('%H:%M'))
            else:
                text.append(game.shortStatusText)
            text.append(
                f"{game.homeCompetitor.name} / {game.awayCompetitor.name}")
            if not game.not_started:
                text.append(
                    f"{game.homeCompetitor.score:.0f}:{game.awayCompetitor.score:.9f}")
            frame = ContentFrame(
                text=' '.join(text),
                index=idx,
                icon=game.icon
            )
            frames.append(frame)
        __class__.client.send_model(
            APPNAME.RM, Content(frames=frames)
        )

    @property
    def isHidden(self):
        return len(self._schedule.current) == 0

    def load(self):
        schedule = self.get_schedule()
        self._schedule = Schedule(schedule)
        self._schedule.persist()

    def get_schedule(self):
        schedule = ZnaykoClient.team_schedule(TEAM_ID)
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
