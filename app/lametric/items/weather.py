from curses.ascii import isupper
from pprint import pprint
from traceback import print_exc
from app.lametric.models import (
    WeatherFrame
)
from datetime import datetime, timedelta
from pyowm.owm import OWM
from pyowm.weatherapi25.weather_manager import WeatherManager
from pyowm.weatherapi25.observation import Observation
from pyowm.weatherapi25.weather import Weather as WeatherData
from app.config import Config
from enum import Enum

class WEATHER_ICON(Enum):
    THUNDERSTORM = 11428
    DRIZZLE = 72
    RAIN = 72
    SNOW = 2151
    MIST = 2154
    SMOKE = 2154
    HAZE = 2154
    DUST = 2154
    FOG = 2154
    SAND = 2154
    ASH = 2154
    SQUALL = 2154
    TORNADO = 2153
    CLEAR = 73
    CLOUDS = 2286

class WeatherMeta(type):

    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance

class Weather(object, metaclass=WeatherMeta):

    __last_called: datetime = None
    __omw: OWM = None
    __manager: WeatherManager = None
    __lifetime: timedelta = None
    __observation: Observation = None
    __icon: int = None

    def __init__(self) -> None:
        self.__lifetime = timedelta(seconds=Config.openweather.lifetime)
        self.__omw = OWM(Config.openweather.apikey)
        self.__manager = self.__omw.weather_manager()

    @property
    def observation(self) -> Observation:
        if self.isUpdated:
            self.__icon = None
            self.__observation = None
        if not self.__observation:
            self.__last_called = datetime.now()
            observation = self.__manager.weather_at_place(
                f"{Config.openweather.city},{Config.openweather.country}"
            )
            self.__observation = observation
        return self.__observation

    @property
    def icon(self):
        if not self.__icon:
            status = self.observation.weather.status
            try:
                icon = WEATHER_ICON[status.upper()]
                self.__icon = icon.value
            except ValueError as e:
                print_exc(e)
        return self.__icon

    def getFrames(self):
        observation = self.observation
        weather: WeatherData = observation.weather
        temp = int(weather.temperature('celsius').get("temp"))
        return [
            WeatherFrame(
                text=f"{temp}°",
                icon=self.icon,
                duration=5000
            )
        ]

    @property
    def isUpdated(self):
        if self.__last_called is None:
            return True
        return datetime.now() - self.__last_called > self.__lifetime
