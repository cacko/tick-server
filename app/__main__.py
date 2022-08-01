from queue import LifoQueue
from app.znayko.client import Client
from app.api.server import Server
from app import log
from botyo_client.core.config import Config as BotyoConfig
from botyo_client.app import App
from app.config import Config
from app.core.thread import StoppableThread
from app.lametric import LaMetric


threads = []

try:
    lm = StoppableThread(target=LaMetric.start)
    lm.start()

    ts = StoppableThread(target=Server.start)
    ts.start()

    client = Client()
    app = App(
        BotyoConfig.from_dict(Config.botyo.to_dict()),
        client
    )
    app.start()
except KeyboardInterrupt:
    import sys
    sys.exit(0)
except Exception as e:
    log.exception(e, exc_info=True)
