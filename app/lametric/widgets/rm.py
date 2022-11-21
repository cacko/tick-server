from datetime import datetime, timedelta, timezone
from time import time
from .base import SubscriptionWidget, WidgetMeta
from app.znayko.models import (
    ACTION,
    EventStatus,
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
from cachable.cacheable import TimeCacheable
from app.scheduler import Scheduler
import pickle
from app.core.time import to_local_time, is_today
import logging
from typing import Optional

TEAM_ID = 131
STORAGE_KEY = "real_madrid_schedule"
STORAGE_LAST_UPDATE = "real_madrid_last_update"
STORAGE_LAST_SLEEP_START = "real_madrid_sleep_start"


class TeamSchedule(TimeCacheable):
    cachetime: timedelta = timedelta(seconds=30)
    __id = None

    def __init__(self, id) -> None:
        self.__id = id
        super().__init__()

    @property
    def content(self):
        if not self.load():
            schedule = ZnaykoClient.team_schedule(TEAM_ID)
            self._struct = self.tocache(schedule)
        return self._struct.struct

    @property
    def id(self):
        return self.__id


def cron_func():
    try:
        games = TeamSchedule(TEAM_ID).content
        for game in games:
            if is_today(game.startTime):
                res = ZnaykoClient.subscribe(game.id)
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
        hour=4,
        minute=30,
        replace_existing=True,
        misfire_grace_time=180
    )


class ScheduleMeta(type):

    __instance = None

    def __call__(cls, data, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, data, *args, **kwargs)
        return cls.__instance

    def load(cls) -> 'Schedule':
        if not cls.__instance:
            data = Storage.hgetall(STORAGE_KEY)
            assert isinstance(data, dict)
            games = [pickle.loads(v) for v in data.values()]
            return cls(games)
        if cls.needsUpdate():
            schedule = TeamSchedule(TEAM_ID).content
            cls.__instance.reload(schedule)
            return cls.__instance
        return cls.__instance

    def needsUpdate(cls) -> bool:
        return True
        if cls.__instance and cls.__instance.in_progress:
            print("needs update in progress")
            return True
        if not Storage.exists(STORAGE_KEY):
            return True
        if not Storage.exists(STORAGE_LAST_UPDATE):
            return True
        last_update = float(Storage.get(STORAGE_LAST_UPDATE))
        return time() - last_update > (60 * 60)


class Schedule(dict, metaclass=ScheduleMeta):
    def __init__(self, data: list[Game]):
        d = {f"{game.id}": game for game in data}
        super().__init__(d)

    def persist(self):
        try:
            d = {k: pickle.dumps(v) for k, v in self.items()}
            Storage.pipeline().hset(name=STORAGE_KEY, mapping=d).persist(STORAGE_KEY).set(
                STORAGE_LAST_UPDATE, time()).persist(STORAGE_LAST_UPDATE).execute()
        except Exception as e:
            logging.error(e)
            logging.warning(f"failed pesistance")

    def isIn(self, id: str):
        ids = [x.subscriptionId for x in self.values()]
        logging.debug(ids)
        return id in ids

    def reload(self, data: list[Game], *args, **kwargs):
        self.clear()
        d = {f"{game.id}": game for game in data}
        self.update(d, *args, **kwargs)
        self.persist()


    @property
    def current(self) -> list[Game]:
        if game := self.in_progress:
            return [game]
        n = datetime.now(tz=timezone.utc)
        games = sorted(self.values(), key=lambda g: g.startTime)
        past = list(filter(lambda g: n > g.startTime, games))
        try:
            next_game = games[len(past)]
            if is_today(next_game.startTime):
                return [next_game]
            return [past[-1], next_game]
        except IndexError:
            logging.warning(f"getting index failed")
            return []

    @property
    def in_progress(self) -> Optional[Game]:
        return next(filter(lambda g: g.in_progress, self.values()), None)

    @property
    def next_game(self) -> Game:
        if self.in_progress:
            return self.current[0]
        return self.current[-1]


class RMWidget(SubscriptionWidget, metaclass=WidgetMeta):

    _schedule: Schedule
    _sleep_start: datetime

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.load()
        self.update_frames()
        schedule_cron()
        cron_func()

    @property
    def sleep_start(self):
        data = Storage.get(STORAGE_LAST_SLEEP_START)
        if data:
            return pickle.loads(data)
        return None

    @sleep_start.setter
    def sleep_start(self, value):
        Storage.pipeline().set(STORAGE_LAST_SLEEP_START, pickle.dumps(value)
                               ).persist(STORAGE_LAST_SLEEP_START).execute()

    def filter_payload(self, payload):
        if isinstance(payload, list):
            return list(
                filter(
                    lambda x: not self._schedule.isIn(x.get("id")),
                    payload
                )
            )
        subid = payload.get("id")
        if subid and self._schedule.isIn(subid):
            return None
        return payload

    @property
    def isHidden(self):
        Schedule.load()
        if not len(self._schedule.current):
            return True
        if self._schedule.in_progress:
            return False
        if __class__.hasLivescoreGamesInProgress:
            return False
        return False

    def onShow(self):
        self.load()
        if self._schedule.in_progress:
            ZnaykoClient.livescores()
        self.update_frames()

    def onHide(self):
        pass

    def duration(self, duration: int):
        multiplier = 30 if self._schedule.in_progress else duration
        res = len(self._schedule.current) * multiplier
        return max(res, duration)

    def update_frames(self):
        frames = []
        for idx, game in enumerate(self._schedule.current):
            text = []
            if game.not_started:
                if not is_today(game.startTime):
                    text.append(to_local_time(game.startTime, fmt="%a %d / "))
                text.append(to_local_time(game.startTime))
            elif game.shortStatusText in [EventStatus.HT.value, EventStatus.FT.value]:
                text.append(game.shortStatusText)
            elif game.ended:
                text.append("FT")
            else:
                text.append(game.gameTimeDisplay)

            text.append(
                f"{game.homeCompetitor.name} / {game.awayCompetitor.name}")
            if not game.not_started:
                text.append(
                    f"{game.homeCompetitor.score:.0f}:{game.awayCompetitor.score:.0f}")
            frame = ContentFrame(
                text=' '.join(text),
                index=idx,
                icon=game.icon
            )
            frames.append(frame)
        __class__.client.send_model(
            APPNAME.RM, Content(frames=frames)
        )

    def load(self):
        self._schedule = Schedule.load()

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            if not self._schedule.isIn(event.id):
                continue
            if event.is_old_event:
                continue
            game: Game = self._schedule.get(f"{event.event_id}")
            is_winner = None
            if not game:
                return
            try:
                action = ACTION(event.action)
                if action == ACTION.PROGRESS:
                    continue
                if action == ACTION.FULL_TIME:
                    self.load()
                    game = self._schedule.get(f"{event.event_id}")
                    is_winner = next(filter(lambda x: x.id == TEAM_ID, [
                                     game.homeCompetitor, game.awayCompetitor]), None).isWinner
            except ValueError:
                pass
            frame = event.getContentFrame(league_icon=game.icon)
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
