from datetime import datetime, timedelta, timezone
from .base import WidgetMeta
from app.botyo.models import (
    ACTION,
    MatchEvent,
    SubscriptionEvent,
    Status as MatchEventStatus,
)
from app.lametric.models import (
    Content,
    APPNAME,
    Notification,
    STORAGE_KEY,
)
from app.botyo.client import Client as BotyoClient
from cachable.cacheable import TimeCacheable
from app.scheduler import Scheduler
from .livescore import BaseLivescoresWidget
from app.core.time import is_today
import logging
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
            schedule = BotyoClient.team_schedule(self.__id)
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
                BotyoClient.subscribe(game.id)
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
            kwargs={"team_id": team_id, "storage_key": storage_key},
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
    
    @property
    def isHidden(self):
        return False

    def post_init(self):
        logging.warning(self.item_id)
        logging.warning(STORAGE_KEY.REAL_MADRID.value)
        schedule_cron(self.item_id, STORAGE_KEY.REAL_MADRID.value)
        cron_func(self.item_id, STORAGE_KEY.REAL_MADRID.value)

    def filter_payload(self, payload):
        logging.warning(payload)
        if isinstance(payload, list):
            return list(
                filter(
                    lambda x: self.item_id
                    not in [x.get("home_team_id"), x.get("away_team_id")],
                    payload,
                )
            )
        if self.item_id in [
            payload.get("home_team_id"),
            payload.get("away_team_id")
        ]:
            return None
        return payload

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
                        frame = event.getContentFrame(league_icon=sub.icon)
                        RMWidget.client.send_notification(
                            Notification(
                                model=Content(
                                    frames=[frame],
                                    sound=event.getTeamSound(
                                        self.item_id,
                                        self.item_id == event.winner
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
                        RMWidget.client.send_notification(
                            Notification(
                                model=Content(
                                    frames=[frame],
                                    sound=event.getTeamSound(
                                        self.item_id,
                                        self.item_id == event.winner
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
            except KeyError:
                logging.debug(f">>>MISSING {event.id} {self.__class__}")
            except AssertionError as e:
                logging.exception(e)
        self.update_frames()
