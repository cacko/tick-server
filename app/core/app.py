from pathlib import Path
from app.api.server import Server
from app.config import Config
from app.core.thread import StoppableThread
from app.lametric import LaMetric
from app.scheduler import Scheduler
from cachable.storage.redis import RedisStorage
from cachable.storage.file import FileStorage
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio


class AppMeta(type):

    _instance = None
    threads: list[StoppableThread] = []

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = type.__call__(self, *args, **kwds)
        return self._instance

    def start(cls):
        RedisStorage.register(Config.storage.redis_url)
        FileStorage.register(Path(Config.storage.storage))
        cls().run()

    def terminate(cls):
        Scheduler.stop()
        for th in cls.threads:
            th.stop()
        cls().eventLoop.stop()


class App(object, metaclass=AppMeta):

    def __init__(self) -> None:
        self.eventLoop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()

    def run(self):

        lm = StoppableThread(target=LaMetric.start, args=[self.queue])
        lm.start()
        App.threads.append(lm)

        ts = StoppableThread(target=Server.start, args=[self.queue])
        ts.start()
        App.threads.append(ts)

        scheduler = BackgroundScheduler()
        self.scheduler = Scheduler(scheduler, Config.storage.redis_url)

        Scheduler.start()
        self.eventLoop.run_forever()
