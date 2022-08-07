import logging
from pathlib import Path
from queue import LifoQueue
import bottle
from bottle import Bottle, run, template, request
from app.api.auth import auth_required
from app.config import Config
from app.lametric.models import CONTENT_TYPE
from app.lametric import LaMetric
from app.yanko import Yanko

app = Bottle()

views = Path(__file__).parent / "views"

bottle.TEMPLATE_PATH = [views.as_posix()]

class ServerMeta(type):

    _instance: 'Server' = None
    _manager: LifoQueue = None
    _queue: LifoQueue = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance

    def start(cls, mainQueue):
        cls().start_server(mainQueue)

    def nowplaying(cls, query):
        return cls().handle_nowplaying(query)

    def status(cls, query):
        return cls().handle_status(query)


class Server(object, metaclass=ServerMeta):

    _mqinQueue = None

    def start_server(self, mainQueue):
        self._mqinQueue = mainQueue
        conf = Config.api.to_dict()
        run(app, **conf)

    def handle_nowplaying(self, payload):
        print(payload)
        LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, payload))

    def handle_status(self, payload):
        LaMetric.queue.put_nowait((CONTENT_TYPE.YANKOSTATUS, payload))


@app.route('/api/nowplaying', method='POST')
@auth_required
def nowplaying():
    print(request.json)
    return Server.nowplaying(request.json)


@app.route('/api/status', method='POST')
@auth_required
def status():
    return Server.status(request.json)


@app.route('/api/button')
def on_button():
    logging.debug(
        [f"{h}: {request.get_header(h)}" for h in request.headers.keys()])
    logging.debug(
        [f"{h}: {request.query.get(h)}" for h in request.query.keys()])
    Yanko.toggle()

@app.route("/api/subscription", method="POST")
@auth_required
def on_subscription():
    logging.info(request.json)

@app.route('/privacy')
def privacy():
    return template('privacy')
