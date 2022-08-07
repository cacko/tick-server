from dataclasses import dataclass
import logging
from app.core import clean_frame
from app.config import LametricConfig, LametricApp
import requests
from requests import ConnectionError
from cachable.request import Method
from app.lametric.models import (
    APPNAME,
    App,
    Notification,
    Content,
)


class Client(object):

    __config: LametricConfig = None

    def __init__(self, config: LametricConfig) -> None:
        self.__config = config

    def api_call(self, method: Method, endpoint: str, **args):
        host = self.__config.host
        user = self.__config.user
        apikey = self.__config.apikey
        logging.debug(args)
        try:
            response = requests.request(
                method=method.value,
                auth=(user, apikey),
                url=f"{host}/api/v2/{endpoint}",
                **args
            )
            return response.json()
        except ConnectionError:
            pass

    def widget_call(self, config_name: APPNAME, method: Method, **args):
        app: LametricApp = self.__config.apps.get(config_name.value)
        url = app.endpoint
        token = app.token
        logging.debug(args)
        try:
            response = requests.request(
                method=method.value,
                headers={
                    'X-Access-Token': token,
                    'Cache-Control': 'no-cache',
                    'Accept': 'application/json'
                },
                url=f"{url}",
                **args
            )
            return response.status_code
        except ConnectionError:
            pass

    def send_notification(self, notification: Notification):
        data = notification.to_dict()
        data["model"]["frames"] = list(
            map(clean_frame, data.get("model").get("frames", [])))
        data["model"] = clean_frame(data.get("model"))
        return self.api_call(
            Method.POST,
            "device/notifications",
            json=data
        )

    def get_apps(self) -> dict[str, App]:
        res = self.api_call(
            Method.GET,
            "device/apps"
        )
        return {k: App.from_dict(v) for k, v in res.items()}

    def send_model(self, config_name: APPNAME, model: Content):
        data = model.to_dict()
        data["frames"] = list(map(clean_frame, data.get("frames", [])))
        return self.widget_call(
            config_name,
            Method.POST,
            json=data
        )
