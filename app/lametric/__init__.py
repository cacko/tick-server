import logging
from queue import Empty, Queue

from app.lametric.client import Client
from app.config import Config
from app.lametric.models import (
    CONTENT_TYPE,
    DEVICE_MODE,
)
from app.lametric.display import Display
import time


class LaMetricMeta(type):

    _instance = None
    _queue: Queue

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._queue = Queue()
            self._instance = type.__call__(self, *args, **kwds)
        return self._instance

    def start(cls, mainQueue):
        cls().run(mainQueue)

    @property
    def queue(cls):
        return cls._queue


class LaMetric(object, metaclass=LaMetricMeta):

    _client: Client
    _display: Display
    _mainQueue = None

    def __init__(self) -> None:
        self._client = Client(Config.lametric)
        self._display = Display(client=self._client)
        self._client.set_device_mode(DEVICE_MODE.MANUAL)

    def run(self, mainQueue):
        self._mainQueue = mainQueue
        queue = LaMetric.queue
        logging.info(">>>> LAMETRUIC QUEUE START")
        while True:
            try:
                cmd, payload = queue.get_nowait()
                match(cmd):
                    case CONTENT_TYPE.NOWPLAYING:
                        self._display.on_response(cmd, payload)
                    case CONTENT_TYPE.YANKOSTATUS:
                        self._display.on_response(cmd, payload)
                    case CONTENT_TYPE.LIVESCOREEVENT:
                        self._display.on_response(cmd, payload)
                    case CONTENT_TYPE.TERMO:
                        self._display.on_response(cmd, payload)
                    case CONTENT_TYPE.SURE:
                        self._display.on_response(cmd, payload)
                queue.task_done()
            except Empty:
                time.sleep(0.2)
            self._display.update()
