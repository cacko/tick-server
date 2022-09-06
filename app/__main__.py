import sys
import signal
from app.core import logger
from app.core.app import App

try:
    App.start()

except KeyboardInterrupt:
    import sys
    sys.exit(0)
except Exception as e:
    logger.exception(e, exc_info=True)

def handler_stop_signals(signum, frame):
    logger.warning("Stopping app")
    App.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)