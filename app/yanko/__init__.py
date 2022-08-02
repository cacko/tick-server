from app.config import Config
from app.core.otp import OTP
from requests import request
from enum import Enum
from cachable.request import Method


class Endpoints(Enum):
    STATE = 'state'
    NEXT = 'command/next'


class YankoMeta(type):

    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance

    def state(cls):
        return cls().make_request(Method.GET, Endpoints.STATE)

    def next(cls):
        return cls().make_request(Method.GET, Endpoints.NEXT)


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
            return resp.status_code > 399
        except Exception as e:
            return False
