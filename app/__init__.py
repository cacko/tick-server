import logging
from os import environ

logging.basicConfig(
    level=getattr(logging, environ.get("TICK_LOG_LEVEL", "DEBUG")),
    format="%(filename)s %(message)s",
    datefmt="%H:%M:%S",
)