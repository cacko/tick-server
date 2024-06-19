import sys
import signal
from app.core.app import App
import logging


try:
    App.start()
except KeyboardInterrupt:
    sys.exit(0)
except Exception as e:
    logging.exception(e, exc_info=True)


def handler_stop_signals(signum, frame):
    logging.warn("Stopping app")
    App.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)
