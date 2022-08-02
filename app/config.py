
from os import environ
from dataclasses import dataclass
from pathlib import Path
from dataclasses_json import dataclass_json, Undefined
import toml

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class StorageConfig:
    storage: str
    redis_url: str
    attachments: str

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class YankoConfig:
    host: str
    secret: str

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
    widget_endpoint: str
    widget_token: str

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class OpenWeatherConfig:
    apikey: str
    city: str
    country: str
    lifetime: int

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ConfigStruct:
    storage: StorageConfig
    yanko: YankoConfig
    lametric: LametricConfig
    api: ApiConfig
    openweather: OpenWeatherConfig

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
    def lametric(cls) -> LametricConfig:
        return cls().struct.lametric

    @property
    def api(cls) -> ApiConfig:
        return cls().struct.api

    @property
    def openweather(cls) -> OpenWeatherConfig:
        return cls().struct.openweather

class Config(object, metaclass=ConfigMeta):

    truct: ConfigStruct = None

    def __init__(self):
        settings = Path(environ.get("SETTINGS_PATH", "app/settings.toml"))
        self.struct = ConfigStruct.from_dict(toml.loads(settings.read_text()))
