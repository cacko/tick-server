from app.config import app_config
from app.core.otp import OTP
from requests import request
from enum import Enum
from cachable.request import Method
import logging

from app.lametric.models import MUSIC_STATUS


class Endpoints(Enum):
    STATE = "state"
    NEXT = "command/next"
    TOGGLE = "command/toggle"


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

    __otp: OTP
    __host: str

    def __init__(self) -> None:
        self.__otp = OTP.yanko
        self.__host = app_config.yanko.host

    def make_request(self, method: Method, endpoint: Endpoints, **kwags):
        try:
            resp = request(
                method=method.value,
                url=f"{self.__host}/{endpoint.value}",
                headers=self.__otp.headers,
                **kwags,
            )
            return resp.json()
        except Exception as e:
            return {"status": MUSIC_STATUS.STOPPED}
