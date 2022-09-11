from pathlib import Path
from queue import Queue
from app.api.auth import auth_required
from app.config import Config
from app.lametric.models import CONTENT_TYPE
from app.lametric import LaMetric
from app.core.events import EventManager
from butilka.server import request, template, Server as ButilkaServer
import logging

api_config = Config.api
views = Path(__file__).parent / "views"
srv = ButilkaServer(
    host=api_config.host, 
    port=api_config.port,
    template_path=views.as_posix()
)
app = srv.app
class ServerMeta(type):

    _instance: 'Server' = None
    _mainQueue: Queue = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = type.__call__(self, *args, **kwds)
        return self._instance

    def start(cls, mainQueue):
        cls._mainQueue = mainQueue
        cls().start_server()

    def nowplaying(cls, query):
        return cls().handle_nowplaying(query)

    def status(cls, query):
        return cls().handle_status(query)

    def subscription(cls, query):
        return cls().handle_subscription(query)


class Server(object, metaclass=ServerMeta):

    def start_server(self):
        srv.start()

    def handle_nowplaying(self, payload):
        LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, payload))

    def handle_status(self, payload):
        LaMetric.queue.put_nowait((CONTENT_TYPE.YANKOSTATUS, payload))

    def handle_subscription(self, payload):
        LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))
        return "OK"


@app.route('/api/nowplaying', method='POST')
@auth_required
def nowplaying():
    return Server.nowplaying(request.json)


@app.route('/api/status', method='POST')
@auth_required
def status():
    return Server.status(request.json)


@app.route('/api/button')
def on_button():
    events = [f"{k}={v}".lower() for k, v in request.query.items()]
    EventManager.on_trigger(events)


@app.route("/api/subscription", method="POST")
@auth_required
def on_subscription():
    data = request.json
    logging.debug(data)
    return Server.subscription(data)


@app.route('/privacy')
def privacy():
    return template('privacy')
