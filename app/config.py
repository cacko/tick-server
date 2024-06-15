from os import environ
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel


class LamboConfig(BaseModel):
    username: str
    clientkey: str
    hostname: str


class StorageConfig(BaseModel):
    storage: str
    redis_url: str
    attachments: str


class LametricApp(BaseModel):
    package: str
    widget_id: str
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


class _config(BaseModel):
    storage: StorageConfig
    yanko: YankoConfig
    botyo: BotyoConfig
    lametric: LamboConfig
    api: ApiConfig
    display: list[str]
    saver: list[str]


settings = Path(environ.get("SETTINGS_PATH", "app/settings.yaml"))
data = yaml.full_load(settings.read_text())
app_config = _config(**data)
