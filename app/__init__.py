import logging
from os import environ

logging.basicConfig(
    level=getattr(logging, environ.get("LAMETRIC_LOG_LEVEL", "INFO")),
    format="%(filename)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("LAMETRIC")
