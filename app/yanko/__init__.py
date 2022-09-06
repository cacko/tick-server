from app.core import logger
from app.config import Config
from app.core.otp import OTP
from requests import request
from enum import Enum
from cachable.request import Method

from app.lametric.models import MUSIC_STATUS


class Endpoints(Enum):
    STATE = 'state'
    NEXT = 'command/next'
    TOGGLE = 'command/toggle'


class YankoMeta(type):

    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = type.__call__(self, *args, **kwds)
        return self._instance

    def state(cls):
        return cls().make_request(Method.GET, Endpoints.STATE)

    def next(cls):
        return cls().make_request(Method.GET, Endpoints.NEXT)

    def toggle(cls):
        return cls().make_request(Method.GET, Endpoints.TOGGLE)


class Yanko(object, metaclass=YankoMeta):

    __otp: OTP = None
    __host = None

    def __init__(self) -> None:
        self.__otp = OTP.yanko
        self.__host = Config.yanko.host

    def make_request(self, method: Method, endpoint: Endpoints, **kwags):
        try:
            resp = request(
                method=method.value,
                url=f"{self.__host}/{endpoint.value}",
                headers=self.__otp.headers,
                **kwags
            )
            return resp.json()
        except Exception as e:
            logger.debug(e)
            return {"status": MUSIC_STATUS.STOPPED}
