from app.config import Config
import requests
from cachable.request import Method
from app.lametric.models import (
    Notification,
    NotificationFrame,
    NotificationModel
)


class LaMetricMeta(type):

    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance

    def nowplaying(cls, payload):
        cls().do_notification(Notification(
            priority='info',
            model=NotificationModel(
                frames=[NotificationFrame(**payload)]
            )
        ))
        cls().do_widget_state(NotificationModel(
            frames=[
                NotificationFrame(**payload)
            ]
        ))

    def status(cls, payload):
        pass


class LaMetric(object, metaclass=LaMetricMeta):

    def __make_request(self, method: Method, endpoint: str, **args):
        host = Config.lametric.host
        user = Config.lametric.user
        apikey = Config.lametric.apikey
        response = requests.request(
            method=method.value,
            auth=(user, apikey),
            url=f"{host}/api/v2/{endpoint}",
            **args
        )
        return response.json()

    def __widget_request(self, method: Method, **args):
        url = Config.lametric.widget_endpoint
        token = Config.lametric.widget_token
        response = requests.request(
            method=method.value,
            headers={
                'x-access-token': token
            },
            url=f"{url}",
            **args
        )
        return response.status_code

    def do_notification(self, notification: Notification):
        return self.__make_request(
            Method.POST,
            "device/notifications",
            json=notification.to_dict()
        )

    def do_widget_state(self, model: NotificationModel):
        return self.__widget_request(
            Method.POST,
            json=model.to_dict()
        )
