from datetime import datetime, timedelta, timezone
import logging
from .base import SubscriptionWidget, WidgetMeta
from app.znayko.models import (
    ACTION,
    Game,
    MatchEvent,
    CancelJobEvent,
    SubscriptionEvent
)
from app.lametric.models import (
    Content,
    ContentFrame,
    APPNAME,
    Notification
)
from app.znayko.client import Client as ZnaykoClient
from cachable.storage import Storage
from app.scheduler import Scheduler
import pickle
from app.core.time import to_local_time, is_today

TEAM_ID = 131
STORAGE_KEY = "real_madrid_schedule"


def cron_func():
    try:
        games = ZnaykoClient.team_schedule(TEAM_ID)
        for game in games:
            if is_today(game.startTime):
                res = ZnaykoClient.subscribe(game.id)
                logging.warn(res)
    except Exception as e:
        logging.error(e)
        n = datetime.now(timezone.utc)
        td = timedelta(minutes=30)
        Scheduler.add_job(
            id=f"{STORAGE_KEY}_retry",
            name=f"{STORAGE_KEY}_retry",
            func=cron_func,
            trigger="date",
            run_date=n+td,
            replace_existing=True,
            misfire_grace_time=180
        )


def schedule_cron():
    Scheduler.add_job(
        id=STORAGE_KEY,
        name=f"{STORAGE_KEY}",
        func=cron_func,
        trigger="cron",
        hour=0,
        minute=30,
        replace_existing=True,
        misfire_grace_time=180
    )


class Schedule(dict):

    def __init__(self, data: list[Game]):
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


class RMWidget(SubscriptionWidget, metaclass=WidgetMeta):

    _schedule: Schedule = None

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.load()
        if not self.isHidden:
            self.update_frames()
        schedule_cron()

    def filter_payload(self, payload):
        if isinstance(payload, list):
            return list(filter(lambda x: not self._schedule.isIn(x.get("event_id")), payload))
        event_id = payload.get("event_id")
        if event_id and self._schedule.isIn(event_id):
            return None
        return payload

    def onShow(self):
        for game in self._schedule.current:
            if game.in_progress:
                self.load()
                self.update_frames()
                ZnaykoClient.livescores()

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
                text.append(to_local_time(game.startTime))
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

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            if not self._schedule.isIn(event.event_id):
                continue
            logging.warning(event)
            if event.is_old_event:
                continue
            game: Game = self._schedule.get(f"{event.event_id}")
            is_winner = None
            if not game:
                return
            frame = event.getContentFrame(league_icon=game.icon)
            try:
                action = ACTION(event.action)
                if action == ACTION.FULL_TIME:
                    self.load()
                    game = self._schedule.get(f"{event.event_id}")
                    for competitor in [game.homeCompetitor, game.awayCompetitor]:
                        if competitor.id == TEAM_ID:
                            match(competitor.isWinner):
                                case True:
                                    is_winner = True
                                case False:
                                    is_winner = False
                            break
            except:
                pass
            __class__.client.send_notification(Notification(
                model=Content(
                    frames=[frame],
                    sound=event.getTeamSound(TEAM_ID, is_winner)
                ),
                priority='critical'
            ))

    def on_cancel_job_event(self, event: CancelJobEvent):
        pass

    def on_subscribed_event(self, event: SubscriptionEvent):
        pass

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        pass
