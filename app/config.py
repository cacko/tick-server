from os import environ
from pathlib import Path
from typing import Optional
from yaml import load, Loader
from pydantic import BaseModel, Extra


class StorageConfig(BaseModel):
    storage: str
    redis_url: str
    attachments: str


class LametricApp(BaseModel):
    package: str
    index: Optional[int] = None
    duration: Optional[int] = None
    endpoint: Optional[str] = None
    token: Optional[str] = None
    sleep_minutes: Optional[int] = None
    item_id: Optional[int] = None


class YankoConfig(BaseModel):
    host: str
    secret: str


class BotyoConfig(BaseModel):
    host: str


class ApiConfig(BaseModel):
    host: str
    port: int
    secret: str
    daemon_threads: bool
    nworkers: int
    device: list[str]


class LametricConfig(BaseModel):
    host: str
    user: str
    apikey: str
    apps: dict[str, LametricApp]
    timezone: str


class ConfigStruct(BaseModel):
    storage: StorageConfig
    yanko: YankoConfig
    lametric: LametricConfig
    api: ApiConfig
    botyo: BotyoConfig
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
    def botyo(cls) -> BotyoConfig:
        return cls().struct.botyo

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

    struct: ConfigStruct

    def __init__(self):
        settings = Path(environ.get("SETTINGS_PATH", "app/settings.yaml"))
        data = load(settings.read_text(), Loader=Loader)
        self.struct = ConfigStruct(**data)
