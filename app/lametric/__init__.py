from queue import LifoQueue

from app.lametric.client import Client
from app.config import Config
from app.lametric.items.clock import Clock
from app.lametric.items.weather import Weather
from app.lametric.models import (
    CONTENT_TYPE,
    YANKO_STATUS,
    Content,
    Notification,
    Display,
    YankoFrame,

)
import time

from app.yanko import Yanko


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
    _clock: Clock = None
    _display: Display = None
    _weather: Weather = None
    _mainQueue = None

    def __init__(self) -> None:
        self._client = Client(Config.lametric)
        self._clock = Clock()
        self._weather = Weather()
        self._clock.icon = self._weather.icon
        self._display = Display(
            clock=self._clock.getFrames(),
            weather=self._weather.getFrames()
        )

    def run(self, mainQueue):
        self._mainQueue = mainQueue
        queue = __class__.queue
        display = self._display
        clock: Clock = self._clock
        weather = self._weather
        self._client.send_model(display.getContent())
        if not Yanko.state():
            self._display.yanko = None

        while True:
            isUpdated = False

            if clock.isUpdated:
                isUpdated = True
                display.clock = clock.getFrames()

            if weather.isUpdated:
                isUpdated = True
                display.weather = weather.getFrames()
                clock.icon = weather.icon
                display.clock = clock.getFrames()

            if queue.empty():
                time.sleep(0.1)
            else:
                cmd, payload = queue.get_nowait()
                match(cmd):
                    case CONTENT_TYPE.NOWPLAYING:
                        isUpdated |= self.__nowplaying(payload)
                    case CONTENT_TYPE.YANKOSTATUS:
                        isUpdated |= self.__yankostatus(payload)
            if isUpdated:
                self._client.send_model(display.getContent())

    def __nowplaying(self, payload):
        frame = YankoFrame(**payload)
        self._client.send_notification(Notification(
            model=Content(frames=[frame]),
            priority='critical'
        ))
        self._display.yanko = [frame]
        return True

    def __yankostatus(self, payload):
        try:
            status = YANKO_STATUS(payload.get("status"))
            if status == YANKO_STATUS.EXIT:
                self._display.yanko = None
                return True
        except ValueError:
            pass
        return False
