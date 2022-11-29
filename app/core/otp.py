from typing import Dict
from app.config import Config
import pyotp


class OTPMeta(type):

    _instances = {}

    def __call__(self, secret: str, *args, **kwds):
        if secret not in self._instances:
            self._instances[secret] = super().__call__(secret, *args, **kwds)
        return self._instances[secret]

    @property
    def api(cls) -> "OTP":
        return cls(Config.api.secret)

    @property
    def yanko(cls) -> "OTP":
        return cls(Config.yanko.secret)


class OTP(object, metaclass=OTPMeta):
    def __init__(self, secret) -> None:
        self.__totp = pyotp.TOTP(secret)

    def verify(self, code: str) -> bool:
        return self.__totp.verify(code)

    @property
    def now(self) -> str:
        return self.__totp.now()

    @property
    def headers(self) -> Dict[str, str]:
        return {"Cache-Control": "no-cache", "X-TOTP": self.now}
