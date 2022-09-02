import logging
from app.api.server import Server
from app.config import Config
from app.core.thread import StoppableThread
from app.lametric import LaMetric
from app.scheduler import Scheduler
from cachable.storage import Storage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio


class AppMeta(type):

    _instance = None
    threads: list[StoppableThread] = []


    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = type.__call__(self, *args, **kwds)
        return self._instance

    def start(cls):
        Storage.register(Config.storage.redis_url)
        cls().run()

    def terminate(cls):
        Scheduler.stop()
        for th in cls.threads:
            th.stop()
        cls().eventLoop.stop()


class App(object, metaclass=AppMeta):

    scheduler: AsyncIOScheduler = None
    event_loop = None

    def __init__(self) -> None:
        self.eventLoop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()

    def run(self):

        lm = StoppableThread(target=LaMetric.start, args=[self.queue])
        lm.start()
        __class__.threads.append(lm)

        ts = StoppableThread(target=Server.start, args=[self.queue])
        ts.start()
        __class__.threads.append(ts)

        scheduler = AsyncIOScheduler(event_loop=self.eventLoop)
        self.scheduler = Scheduler(scheduler, Config.storage.redis_url)
        
        Scheduler.start()
        self.eventLoop.run_forever()
