import logging
from app.api.server import Server
from app.config import Config
from app.core.thread import StoppableThread
from app.lametric import LaMetric
from app.scheduler import Scheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio


class AppMeta(type):

    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance

    def start(cls):
        cls().run()


class App(object, metaclass=AppMeta):

    scheduler: AsyncIOScheduler = None

    def __init__(self) -> None:
        self.eventLoop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()

    def run(self):

        lm = StoppableThread(target=LaMetric.start, args=[self.queue])
        lm.start()

        ts = StoppableThread(target=Server.start, args=[self.queue])
        ts.start()

        scheduler = AsyncIOScheduler(event_loop=self.eventLoop)
        self.scheduler = Scheduler(scheduler, Config.storage.redis_url)

        self.eventLoop.create_task(
            self._produce_consume_messages())
        self.scheduler.start()
        self.eventLoop.run_forever()

    async def _produce_consume_messages(self, consumers=3):
        producers = [
            asyncio.create_task(self.start_manager()),
        ]
        consumers = [
            asyncio.create_task(self._consume(n))
            for n in range(1, consumers + 1)
        ]
        await asyncio.gather(*producers)
        await self.queue.join()
        for c in consumers:
            c.cancel()

    async def start_manager(self):
        while True:
            await asyncio.sleep(0.5)

    async def _consume(self, name: int) -> None:
        while True:
            try:
                await self._consume_new_item(name)
            except Exception:
                continue

    async def _consume_new_item(self, name: int) -> None:
        command = await self.queue.get()
        logging.debug(f"CONSUME {name}: {command} done")
        self.queue.task_done()
