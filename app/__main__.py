

import logging
from app.core.app import App
from os import environ

logging.basicConfig(
    level=getattr(logging, environ.get("TICK_LOG_LEVEL", "INFO")),
    format="%(filename)s %(message)s",
    datefmt="%H:%M:%S",
)


try:
    App.start()
except KeyboardInterrupt:
    import sys
    sys.exit(0)
except Exception as e:
    logging.exception(e, exc_info=True)
