import logging
from app.config import Config
from enum import Enum
from requests import get, post
from app.znayko.models import (
    LivescoreEvent, 
    SubscriptionEvent,
    Game
)

class ENDPOINT(Enum):
    LIVESCORE = 'livescore'
    UNSUBSCRIBE = 'unsubscribe'
    TEAM_SCHEDULE = 'team_schedule'

class ClientMeta(type):

    _instance = None

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    def livescores(cls) -> list[LivescoreEvent]:
        try:
            data = cls().do_get(ENDPOINT.LIVESCORE.value)
            if data:
                return LivescoreEvent.schema().load(data, many=True)
        except Exception as e:
            logging.error(e)
        return []

    def unsubscribe(cls, sub: SubscriptionEvent):
        json = {
            "webhook": f"http://{Config.api.host}:{Config.api.port}/api/subscription",
            "group": Config.api.secret,
            "id": sub.job_id
        }
        return cls().do_post(ENDPOINT.UNSUBSCRIBE.value, json=json)

    def team_schedule(cls, team_id: int) -> list[Game]:
        try:
            data = cls().do_get(f"{ENDPOINT.TEAM_SCHEDULE.value}/{team_id}")
            if data:
                return Game.schema().load(data, many=True)
        except Exception as e:
            logging.error(e)
        return []


class Client(object, metaclass=ClientMeta):

    __host = None

    def __init__(self) -> None:
        self.__host = Config.znayko.host

    def do_get(self, endpoint: str, **kwargs):
        resp = get(f"{self.__host}/{endpoint}", **kwargs)
        return resp.json()

    def do_post(self, endpoint:str, **kwargs):
        resp = post(f"{self.__host}/{endpoint}", **kwargs)
        return resp.json()