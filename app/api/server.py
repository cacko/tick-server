import logging
from pathlib import Path
from queue import LifoQueue
import bottle
from bottle import template, request
from app.api.auth import auth_required
from app.config import Config
from app.lametric.models import CONTENT_TYPE
from app.lametric import LaMetric
from app.core.events import EventManager
from paste.httpserver import WSGIThreadPoolServer, serve
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ServerConfigThreadOptions:
    spawn_if_under: int


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ServerConfig:
    host: str
    port: int
    daemon_threads: bool
    threadpool_workers: int
    threadpool_options: ServerConfigThreadOptions

app = bottle.default_app()

views = Path(__file__).parent / "views"

bottle.TEMPLATE_PATH = [views.as_posix()]

class ServerMeta(type):

    _instance: 'Server' = None
    _manager: LifoQueue = None
    _queue: LifoQueue = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = type.__call__(self, *args, **kwds)
        return self._instance

    def start(cls, mainQueue):
        cls().start_server(mainQueue)

    def nowplaying(cls, query):
        return cls().handle_nowplaying(query)

    def status(cls, query):
        return cls().handle_status(query)

    def subscription(cls, query):
        return cls().handle_subscription(query)

class Server(object, metaclass=ServerMeta):

    _mqinQueue = None
    server: WSGIThreadPoolServer = None

    @property
    def server_config(self) -> ServerConfig:
        api_config = Config.api
        return ServerConfig(
            host=api_config.host,
            port=api_config.port,
            daemon_threads=api_config.daemon_threads,
            threadpool_workers=api_config.nworkers,
            threadpool_options=ServerConfigThreadOptions(
                spawn_if_under=api_config.nworkers
            ),
        )


    def start_server(self, mainQueue):
        self._mqinQueue = mainQueue
        self.server = serve(app, **self.server_config.to_dict())

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
    events = [f"{k}={v}".lower() for k,v in request.query.items()]
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
