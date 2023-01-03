from datetime import datetime, timedelta, timezone
from time import time
from .base import SubscriptionWidget, WidgetMeta
from app.znayko.models import (
    ACTION,
    EventStatus,
    Game,
    MatchEvent,
    CancelJobEvent,
    SubscriptionEvent,
    Status as MatchEventStatus,
)
from app.lametric.models import (
    Content,
    ContentFrame,
    APPNAME,
    Notification,
    Widget,
    STORAGE_KEY,
)
from app.znayko.client import Client as ZnaykoClient
from cachable.storage import Storage
from cachable.cacheable import TimeCacheable
from app.scheduler import Scheduler
from .livescore import BaseLivescoresWidget
import pickle
from app.core.time import to_local_time, is_today
import logging
from typing import Optional
from enum import Enum
from app.lametric.widgets.items.subscriptions import Subscriptions
from random import randint


class TeamSchedule(TimeCacheable):
    cachetime: timedelta = timedelta(seconds=30)
    __id: int

    def __init__(self, id) -> None:
        self.__id = id
        super().__init__()

    @property
    def content(self):
        logging.debug(f"TeamSchedule content {self.cachetime}")
        if not self.load():
            schedule = ZnaykoClient.team_schedule(self.__id)
            self._struct = self.tocache(schedule)
        return self._struct.struct

    @property
    def id(self):
        return self.__id


def cron_func(team_id: int, storage_key: str):
    try:
        games = TeamSchedule(team_id).content
        for game in games:
            if is_today(game.startTime):
                ZnaykoClient.subscribe(game.id)
        schedule_cron(team_id=team_id, storage_key=storage_key)
    except Exception as e:
        logging.error(e)
        n = datetime.now(timezone.utc)
        td = timedelta(minutes=30)
        Scheduler.add_job(
            id=f"{storage_key}_retry",
            name=f"{storage_key}_retry",
            func=cron_func,
            trigger="date",
            run_date=n + td,
            replace_existing=True,
            misfire_grace_time=180,
        )


def schedule_cron(team_id: int, storage_key: str):
    Scheduler.add_job(
        id=f"{storage_key}",
        name=f"{storage_key}",
        func=cron_func,
        trigger="cron",
        hour=7,
        minute=0 + randint(0, 55),
        kwargs={"team_id": team_id, "storage_key": storage_key},
        replace_existing=True,
        misfire_grace_time=180,
    )


class RMWidget(BaseLivescoresWidget, metaclass=WidgetMeta):
    @property
    def subscriptions(self) -> Subscriptions:
        return Subscriptions(STORAGE_KEY.REAL_MADRID.value)

    @property
    def app_name(self) -> APPNAME:
        return APPNAME.RM

    def post_init(self):
        schedule_cron(self.item_id, STORAGE_KEY.PREMIER_LEAGUE.value)
        cron_func(self.item_id, STORAGE_KEY.PREMIER_LEAGUE.value)

    # _schedule: Schedule
    # _sleep_start: datetime

    # def __init__(self, widget_id: str, widget: Widget, **kwargs):
    #     super().__init__(widget_id, widget, **kwargs)
    #     self.load()
    #     self.update_frames()
    #     schedule_cron(self.item_id)
    #     cron_func(self.item_id)

    # @property
    # def sleep_start(self):
    #     data = Storage.get(RMStorage.STORAGE_LAST_SLEEP_START.value)
    #     if data:
    #         return pickle.loads(data)
    #     return None

    # @sleep_start.setter
    # def sleep_start(self, value):
    #     Storage.pipeline().set(
    #         RMStorage.STORAGE_LAST_SLEEP_START.value, pickle.dumps(value)
    #     ).persist(RMStorage.STORAGE_LAST_SLEEP_START.value).execute()

    def filter_payload(self, payload):
        if isinstance(payload, list):
            return list(
                filter(
                    lambda x: self.item_id
                    not in [x.get("home_team_id"), x.get("away_team_id")],
                    payload,
                )
            )
        if self.item_id in [payload.get("home_team_id"), payload.get("away_team_id")]:
            return None
        return payload

    # @property
    # def isHidden(self):
    #     Schedule.load(self.item_id)
    #     logging.warning(f"on hidden schedule {self._schedule}")
    #     if not len(self._schedule.current):
    #         return True
    #     if self._schedule.in_progress:
    #         return False
    #     if __class__.hasLivescoreGamesInProgress:
    #         return False
    #     return False

    # def onShow(self):
    #     self.load()
    #     logging.warning(f"on show schedule {self._schedule}")
    #     if self._schedule.in_progress:
    #         ZnaykoClient.livescores()
    #     self.update_frames()

    # def onHide(self):
    #     pass

    # def duration(self, duration: int):
    #     multiplier = 30 if self._schedule.in_progress else duration
    #     res = len(self._schedule.current) * multiplier
    #     return max(res, duration)

    # def update_frames(self):
    #     logging.debug(f">>> UPDATE FRAMES {__class__}")
    #     frames = []
    #     for idx, game in enumerate(self._schedule.current):
    #         text = []
    #         if game.not_started:
    #             if not is_today(game.startTime):
    #                 text.append(to_local_time(game.startTime, fmt="%a %d / "))
    #             text.append(to_local_time(game.startTime))
    #         elif game.shortStatusText in [EventStatus.HT.value, EventStatus.FT.value]:
    #             text.append(game.shortStatusText)
    #         elif game.ended:
    #             text.append("FT")
    #         else:
    #             text.append(game.gameTimeDisplay)

    #         text.append(f"{game.homeCompetitor.name} / {game.awayCompetitor.name}")
    #         if not game.not_started:
    #             text.append(
    #                 f"{game.homeCompetitor.score:.0f}:{game.awayCompetitor.score:.0f}"
    #             )
    #         frame = ContentFrame(text=" ".join(text), index=idx, icon=game.icon)
    #         frames.append(frame)
    #     __class__.client.send_model(APPNAME.RM, Content(frames=frames))

    # def load(self):
    #     self._schedule = Schedule.load(self.item_id)

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            if event.is_old_event:
                continue
            try:
                logging.debug(event)
                sub = self.subscriptions[event.id]
                assert isinstance(sub, SubscriptionEvent)
                if sub.status == "FT":
                    continue
                act = ACTION(event.action)
                match act:
                    case ACTION.FULL_TIME:
                        sub.status = "FT"
                        sub.display_event_name = None
                        frame = event.getContentFrame(league_icon=icon)
                        __class__.client.send_notification(
                            Notification(
                                model=Content(
                                    frames=[frame],
                                    sound=event.getTeamSound(
                                        self.item_id, self.item_id == event.winner
                                    ),
                                ),
                                priority="critical",
                            )
                        )
                        self.cancel_sub(sub)
                    case ACTION.HALF_TIME:
                        sub.status = "HT"
                    case ACTION.PROGRESS:
                        if event.event_name:
                            sub.display_event_name = event.event_name.replace(
                                "/", " / "
                            )
                        logging.warning(f"STATUS {event.event_status}")
                        match event.event_status:
                            case MatchEventStatus.HALF_TIME:
                                sub.status = MatchEventStatus.HALF_TIME.value
                                self.subscriptions[event.id] = sub
                            case MatchEventStatus.FINAL:
                                sub.status = MatchEventStatus.FINAL.value
                                self.subscriptions[event.id] = sub
                            case _:
                                sub.status = f"{event.time}'"
                    case _:
                        icon = sub.icon
                        assert isinstance(icon, str)
                        frame = event.getContentFrame(league_icon=icon)
                        __class__.client.send_notification(
                            Notification(
                                model=Content(
                                    frames=[frame],
                                    sound=event.getTeamSound(
                                        self.item_id, self.item_id == event.winner
                                    ),
                                ),
                                priority="critical",
                            )
                        )
                if event.score:
                    sub.score = event.score
                self.subscriptions[event.id] = sub
            except ValueError as e:
                logging.exception(e)
            except KeyError as e:
                logging.debug(f">>>MISSING {event.id} {self.__class__}")
            except AssertionError as e:
                logging.exception(e)
        self.update_frames()

    # def on_match_events(self, events: list[MatchEvent]):
    #     for event in events:
    #         # if not self._schedule.isIn(event.id):
    #         #     continue
    #         if event.is_old_event:
    #             continue
    #         game = self._schedule.get(f"{event.event_id}")
    #         assert isinstance(game, Game)
    #         if game.shortStatusText == "FT":
    #             continue
    #         is_winner = None
    #         if not game:
    #             continue
    #         try:
    #             action = ACTION(event.action)
    #             match action:
    #                 case ACTION.HALF_TIME:
    #                     self._schedule[
    #                         f"{event.event_id}"
    #                     ].shortStatusText = EventStatus.HT.value
    #                     self._schedule.persist()
    #                 case ACTION.FULL_TIME:
    #                     self.load()
    #                     schedule_game = self._schedule.get(f"{event.event_id}")
    #                     assert isinstance(schedule_game, Game)
    #                     game = schedule_game
    #                     competitor = next(
    #                         filter(
    #                             lambda x: x.id == self.item_id,
    #                             [game.homeCompetitor, game.awayCompetitor],
    #                         ),
    #                         None,
    #                     )
    #                     assert competitor
    #                     is_winner = competitor.isWinner
    #                 case _:
    #                     break
    #         except ValueError:
    #             pass
    #         assert game.icon
    #         frame = event.getContentFrame(league_icon=game.icon)
    #         __class__.client.send_notification(
    #             Notification(
    #                 model=Content(
    #                     frames=[frame],
    #                     sound=event.getTeamSound(self.item_id, is_winner),
    #                 ),
    #                 priority="critical",
    #             )
    #         )

    # def on_cancel_job_event(self, event: CancelJobEvent):
    #     pass

    # def on_subscribed_event(self, event: SubscriptionEvent):
    #     pass

    # def on_unsubscribed_event(self, event: SubscriptionEvent):
    #     pass
