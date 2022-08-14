
from os import environ
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from yaml import load, Loader


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class StorageConfig:
    storage: str
    redis_url: str
    attachments: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LametricApp:
    package: str
    duration: Optional[int] = None
    endpoint: Optional[str] = None
    token: Optional[str] = None
    sleep_minutes: Optional[int] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class YankoConfig:
    host: str
    secret: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZnaykoConfig:
    host: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ApiConfig:
    host: str
    port: int
    secret: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LametricConfig:
    host: str
    user: str
    apikey: str
    apps: dict[str, LametricApp]
    timezone: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ConfigStruct:
    storage: StorageConfig
    yanko: YankoConfig
    lametric: LametricConfig
    api: ApiConfig
    znayko: ZnaykoConfig
    display: list[str]


class ConfigMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    @property
    def storage(cls) -> StorageConfig:
        return cls().struct.storage

    @property
    def yanko(cls) -> YankoConfig:
        return cls().struct.yanko

    @property
    def znayko(cls) -> ZnaykoConfig:
        return cls().struct.znayko

    @property
    def lametric(cls) -> LametricConfig:
        return cls().struct.lametric

    @property
    def api(cls) -> ApiConfig:
        return cls().struct.api

    @property
    def display(cls) -> list[str]:
        return cls().struct.display


class Config(object, metaclass=ConfigMeta):

    truct: ConfigStruct = None

    def __init__(self):
        settings = Path(environ.get("SETTINGS_PATH", "app/settings.yaml"))
        data = load(settings.read_text(), Loader=Loader)
        self.struct = ConfigStruct.from_dict(data)
