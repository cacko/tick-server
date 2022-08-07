from queue import LifoQueue

from app.lametric.client import Client
from app.config import Config
from app.lametric.models import (
    CONTENT_TYPE
)
from app.lametric.display import Display
import time


class LaMetricMeta(type):

    _instance = None
    _queue: LifoQueue = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._queue = LifoQueue()
            self._instance = super().__call__(*args, **kwds)
        return self._instance

    def start(cls, mainQueue):
        cls().run(mainQueue)

    @property
    def queue(cls):
        return cls._queue


class LaMetric(object, metaclass=LaMetricMeta):

    _client: Client = None
    _display: Display = None
    _mainQueue = None

    def __init__(self) -> None:
        self._client = Client(Config.lametric)
        self._display = Display(client=self._client)

    def run(self, mainQueue):
        self._mainQueue = mainQueue
        queue = __class__.queue
        while True:
            if queue.empty():
                time.sleep(0.1)
                self._display.update()
                continue
            cmd, payload = queue.get_nowait()
            queue.task_done()
            match(cmd):
                case CONTENT_TYPE.NOWPLAYING:
                    self._display.load(cmd, payload)
                case CONTENT_TYPE.YANKOSTATUS:
                    self._display.load(cmd, payload)
            self._display.update()
