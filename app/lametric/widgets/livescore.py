from app.lametric.models import (
    APPNAME,
    Content,
    ContentFrame,
    Notification,
    STORAGE_KEY,
    Widget,
)
from .base import SubscriptionWidget, WidgetMeta
from app.botyo.models import (
    SubscriptionEvent,
    CancelJobEvent,
    MatchEvent,
    ACTION,
    Status as MatchEventStatus,
)
from app.botyo.client import Client as BotyoClient
from app.lametric.widgets.items.subscriptions import Subscriptions
from app.core.events import EventManager, BUTTON_EVENTS
import logging
from app.scheduler import Scheduler
from app.core.time import is_today
from cachable.cacheable import TimeCacheable
from datetime import datetime, timedelta, timezone
from random import randint
from cachable.storage.redis import RedisStorage


class BaseLivescoresWidget(SubscriptionWidget):
    def __init__(self, widget_id: str, widget: Widget, **kwargs):
        super().__init__(widget_id, widget, **kwargs)
        self.post_init()
        self.update_frames()

    @property
    def subscriptions(self) -> Subscriptions:
        raise NotImplementedError

    @property
    def app_name(self) -> APPNAME:
        raise NotImplementedError

    def post_init(self):
        raise NotImplementedError

    def clear_all(self):
        logging.debug("TRIGGER CLEAR ALL")
        for sub in list(self.subscriptions.values()):
            self.cancel_sub(sub)
            del self.subscriptions[sub.id]

    def clear_finished(self):
        for sub in self.subscriptions.values():
            self.cancel_sub(sub)

    def cancel_sub(self, sub: SubscriptionEvent):
        BotyoClient.unsubscribe(sub)

    def onHide(self):
        pass

    def onShow(self):
        expired = []
        for k, sub in self.subscriptions.items():
            self.__class__.hasLivescoreGamesInProgress = sub.inProgress
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
        logging.debug(f">>> UPDATE FRAMES {self.__class__}")
        try:
            for idx, sub in enumerate(self.subscriptions.events):
                text = []
                text.append(sub.displayStatus)
                text.append(sub.displayEventName)
                if sub.score:
                    text.append(sub.score)
                frame = ContentFrame(
                    text=" ".join(text), index=idx, icon=sub.display_icon, duration=0
                )
                frames.append(frame)
        except AttributeError as e:
            logging.error(e)
        logging.debug(frames)
        self.__class__.client.send_model(self.app_name, Content(frames=frames))

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
                        self.cancel_sub(sub)
                    case ACTION.HALF_TIME:
                        sub.status = "HT"
                    case ACTION.PROGRESS:
                        if event.event_name:
                            sub.display_event_name = event.event_name.replace(
                                "/", " / "
                            )
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
                        self.__class__.client.send_notification(
                            Notification(
                                model=Content(frames=[frame], sound=event.sound),
                                priority="critical",
                            )
                        )
                if event.score:
                    sub.score = event.score
                self.subscriptions[event.id] = sub
            except ValueError as e:
                logging.exception(e)
            except KeyError:
                logging.warn(f">>>MISSING {event.id} {self.__class__}")
            except AssertionError as e:
                logging.exception(e)
        self.update_frames()

    def on_cancel_job_event(self, event: CancelJobEvent):
        sub = next(
            filter(lambda x: x.jobId == event.jobId, self.subscriptions.events), None
        )
        if sub:
            del self.subscriptions[sub.id]

    def on_subscribed_event(self, event: SubscriptionEvent):
        self.subscriptions[event.id] = event
        self.update_frames()

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        del self.subscriptions[event.id]
        self.update_frames()


def cron_func(competition_id: int, storage_key: str):
    try:
        games = LeagueSchedule(competition_id).content
        for game in games:
            if is_today(game.startTime):
                BotyoClient.subscribe(game.id)
        schedule_cron(competition_id=competition_id, storage_key=storage_key)
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


def schedule_cron(competition_id: int, storage_key: str):
    Scheduler.add_job(
        id=f"{storage_key}",
        name=f"{storage_key}",
        func=cron_func,
        trigger="cron",
        hour=7,
        minute=0 + randint(0, 55),
        kwargs={"competition_id": competition_id, "storage_key": storage_key},
        replace_existing=True,
        misfire_grace_time=180,
    )


class LeagueSchedule(TimeCacheable):
    cachetime: timedelta = timedelta(hours=5)
    __id: int

    def __init__(self, id: int):
        self.__id = id
        super().__init__()

    @property
    def storage(self):
        return RedisStorage

    @property
    def content(self):
        if not self.load():
            schedule = BotyoClient.league_schedule(self.__id)
            self._struct = self.tocache(schedule)
        return self._struct.struct

    @property
    def id(self):
        return self.__id


class WorldCupWidget(BaseLivescoresWidget, metaclass=WidgetMeta):
    @property
    def subscriptions(self) -> Subscriptions:
        return Subscriptions(STORAGE_KEY.WORLDCUP.value)

    @property
    def app_name(self) -> APPNAME:
        return APPNAME.WORLDCUP

    def post_init(self):
        cron_func(self.item_id, STORAGE_KEY.WORLDCUP.value)
        schedule_cron(self.item_id, STORAGE_KEY.WORLDCUP.value)

    def filter_payload(self, payload):

        if isinstance(payload, list):
            return list(
                filter(
                    lambda x: x.get("league_id", 0) == self.item_id,
                    payload,
                )
            )
        league_id = payload.get("league_id", 0)
        if league_id == self.item_id:
            return payload
        return None


class PremierLeagueWidget(BaseLivescoresWidget, metaclass=WidgetMeta):
    @property
    def subscriptions(self) -> Subscriptions:
        return Subscriptions(STORAGE_KEY.PREMIER_LEAGUE.value)

    @property
    def app_name(self) -> APPNAME:
        return APPNAME.PREMIER_LEAGUE

    def post_init(self):
        schedule_cron(self.item_id, STORAGE_KEY.PREMIER_LEAGUE.value)
        cron_func(self.item_id, STORAGE_KEY.PREMIER_LEAGUE.value)

    def filter_payload(self, payload):
        if isinstance(payload, list):
            return list(
                filter(
                    lambda x: x.get("league_id", 0) == self.item_id,
                    payload,
                )
            )
        league_id = payload.get("league_id", 0)
        if league_id == self.item_id:
            return payload
        return None


class LaLigaWidget(BaseLivescoresWidget, metaclass=WidgetMeta):
    @property
    def subscriptions(self) -> Subscriptions:
        return Subscriptions(STORAGE_KEY.LA_LIGA.value)

    @property
    def app_name(self) -> APPNAME:
        return APPNAME.LA_LIGA

    def post_init(self):
        schedule_cron(self.item_id, STORAGE_KEY.LA_LIGA.value)
        cron_func(self.item_id, STORAGE_KEY.LA_LIGA.value)

    def filter_payload(self, payload):
        if isinstance(payload, list):
            return  list(
                filter(
                    lambda x: x.get("league_id", 0) == self.item_id,
                    payload,
                )
            )
        league_id = payload.get("league_id", 0)
        if league_id == self.item_id:
            return payload
        return None


class LivescoresWidget(BaseLivescoresWidget, metaclass=WidgetMeta):
    @property
    def subscriptions(self) -> Subscriptions:
        return Subscriptions(STORAGE_KEY.LIVESCORES.value)

    @property
    def app_name(self) -> APPNAME:
        return APPNAME.LIVESCORES

    def post_init(self):
        EventManager.listen(BUTTON_EVENTS.LIVESCORES_UNSUBSCRIBE, self.clear_all)
        EventManager.listen(BUTTON_EVENTS.LIVESCORES_CLEAN, self.clear_finished)
