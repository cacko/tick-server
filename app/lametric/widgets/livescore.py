from app.lametric.models import (
    APPNAME,
    Content,
    ContentFrame,
    Notification,
    STORAGE_KEY,
    Widget,
)
from .base import SubscriptionWidget, WidgetMeta
from app.znayko.models import SubscriptionEvent, CancelJobEvent, MatchEvent, ACTION
from app.znayko.client import Client as ZnaykoClient
from app.lametric.widgets.items.subscriptions import Subscriptions
from app.core.events import EventManager, BUTTON_EVENTS
import logging
from app.scheduler import Scheduler
from app.core.time import is_today
from cachable.cacheable import TimeCacheable
from datetime import datetime, timedelta, timezone

class BaseLivescoresWidget(SubscriptionWidget):

    def __init__(self, widget_id: str, widget: Widget, **kwargs):
        super().__init__(widget_id, widget, **kwargs)
        self.post_init()
        self.update_frames()
            
    @property
    def subscriptions(self) -> Subscriptions:
        raise NotImplementedError

    def post_init(self):
        raise NotImplementedError

    def clear_all(self):
        logging.debug("TRIGGER CLEAR ALL")
        keys = [id for id in self.subscriptions.keys()]
        logging.debug(keys)

        for id in keys:
            del self.subscriptions[id]
        logging.debug(self.subscriptions)

    def clear_finished(self):
        keys = [id for id, ev in self.subscriptions.items() if ev.status == "FT"]
        for id in keys:
            del self.subscriptions[id]

    def cancel_sub(self, sub: SubscriptionEvent):
        ZnaykoClient.unsubscribe(sub)

    def onHide(self):
        pass

    def onShow(self):
        expired = []
        for k, sub in self.subscriptions.items():
            __class__.hasLivescoreGamesInProgress = sub.inProgress
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
        logging.debug(f"UPDATE FRAMES")
        try:
            for idx, sub in enumerate(self.subscriptions.events):
                text = []
                text.append(sub.displayStatus)
                text.append(sub.event_name)
                if sub.score:
                    text.append(sub.score)
                frame = ContentFrame(
                    text=" ".join(text), index=idx, icon=sub.display_icon, duration=0
                )
                frames.append(frame)
        except AttributeError as e:
            logging.error(e)
        __class__.client.send_model(APPNAME.LIVESCORES, Content(frames=frames))

    def on_match_events(self, events: list[MatchEvent]):
        for event in events:
            if event.is_old_event:
                continue
            try:
                sub = self.subscriptions.get(event.id)
                assert isinstance(sub, SubscriptionEvent)
                act = ACTION(event.action)
                if act == ACTION.HALF_TIME:
                    sub.status = "HT"
                elif act == ACTION.PROGRESS:
                    sub.status = f"{event.time}'"
                else:
                    icon = sub.icon
                    assert isinstance(icon, str)
                    frame = event.getContentFrame(league_icon=icon)
                    __class__.client.send_notification(
                        Notification(
                            model=Content(frames=[frame], sound=event.getSound()),
                            priority="critical",
                        )
                    )
                if event.score:
                    sub.score = event.score
                self.subscriptions[event.id] = sub
            except ValueError:
                pass
            except AssertionError:
                pass
        self.update_frames()

    def on_cancel_job_event(self, event: CancelJobEvent):
        sub = next(
            filter(lambda x: x.jobId == event.jobId, self.subscriptions.events), None
        )
        if sub:
            del self.subscriptions[sub.id]

    def on_subscribed_event(self, event: SubscriptionEvent):
        logging.warning(f"{self.__class__.__name__} on_subscribed_event")
        logging.debug(event)
        self.subscriptions[event.id] = event
        logging.debug(self.subscriptions)
        self.update_frames()

    def on_unsubscribed_event(self, event: SubscriptionEvent):
        del self.subscriptions[event.id]
        logging.debug(f"DELETING {event.event_name}")
        self.update_frames()


def cron_func(competition_id: int):
    try:
        games = LeagueSchedule(competition_id).content
        for game in games:
            if is_today(game.startTime):
                ZnaykoClient.subscribe(game.id)
    except Exception as e:
        logging.error(e)
        n = datetime.now(timezone.utc)
        td = timedelta(minutes=30)
        Scheduler.add_job(
            id=f"{STORAGE_KEY.WORLDCUP}_retry",
            name=f"{STORAGE_KEY.WORLDCUP}_retry",
            func=cron_func,
            trigger="date",
            run_date=n + td,
            replace_existing=True,
            misfire_grace_time=180,
        )


def schedule_cron(competition_id: int):
    Scheduler.add_job(
        id=f"{STORAGE_KEY.WORLDCUP}",
        name=f"{STORAGE_KEY.WORLDCUP}",
        func=cron_func,
        trigger="cron",
        hour=4,
        minute=40,
        kwargs={"competition_id": competition_id},
        replace_existing=True,
        misfire_grace_time=180,
    )


class LeagueSchedule(TimeCacheable):
    cachetime: timedelta = timedelta(hours=10)
    __id: int

    def __init__(self, id: int):
        self.__id = id
        super().__init__()

    @property
    def content(self):
        if not self.load():
            schedule = ZnaykoClient.league_schedule(self.__id)
            self._struct = self.tocache(schedule)
        return self._struct.struct

    @property
    def id(self):
        return self.__id


class WorldCupWidget(BaseLivescoresWidget, metaclass=WidgetMeta):
    
    @property
    def subscriptions(self) -> Subscriptions:
        return Subscriptions(STORAGE_KEY.WORLDCUP.value)
    
    def post_init(self):
        schedule_cron(self.item_id)
        cron_func(self.item_id)

    def filter_payload(self, payload):
        logging.warning(payload)
        if isinstance(payload, list):
            return list(
                filter(
                    lambda x: x.get("competitionId", 0) != self.item_id,
                    payload,
                )
            )
        league_id = payload.get("league_id", 0)
        if league_id == self.item_id:
            return None
        return payload


class LivescoresWidget(BaseLivescoresWidget, metaclass=WidgetMeta):

    @property
    def subscriptions(self) -> Subscriptions:
        return Subscriptions(STORAGE_KEY.LIVESCORES.value)
    
    def post_init(self):
        EventManager.listen(BUTTON_EVENTS.LIVESCORES_UNSUBSCRIBE, self.clear_all)
        EventManager.listen(BUTTON_EVENTS.LIVESCORES_CLEAN, self.clear_finished)
