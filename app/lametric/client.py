import logging
from app.core import clean_frame
from app.config import LametricConfig
import requests
from cachable.request import Method
from app.lametric.models import (
    Notification,
    Content
)


class Client(object):

    __config: LametricConfig = None

    def __init__(self, config: LametricConfig) -> None:
        self.__config = config

    def __make_request(self, method: Method, endpoint: str, **args):
        host = self.__config.host
        user = self.__config.user
        apikey = self.__config.apikey
        logging.debug(args)
        response = requests.request(
            method=method.value,
            auth=(user, apikey),
            url=f"{host}/api/v2/{endpoint}",
            **args
        )
        return response.json()

    def __widget_request(self, method: Method, **args):
        url = self.__config.widget_endpoint
        token = self.__config.widget_token
        logging.debug(args)
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

    def send_notification(self, notification: Notification):
        data = notification.to_dict()
        data["model"]["frames"] = list(map(clean_frame, data.get("model").get("frames", [])))
        return self.__make_request(
            Method.POST,
            "device/notifications",
            json=data
        )

    def send_model(self, model: Content):
        data = model.to_dict()
        data["frames"] = list(map(clean_frame, data.get("frames", [])))
        return self.__widget_request(
            Method.POST,
            json=data
        )
