import logging
import structlog
from os import environ

logging.basicConfig(level=getattr(logging, environ.get("TICK_LOG_LEVEL", "DEBUG")), format=None)


logger = structlog.wrap_logger(
    logger=logging.getLogger("tick"),
      processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="TICK %m/%d|%H:%M.%S"),
        structlog.dev.ConsoleRenderer()
    ],  
)


def clean_frame(frame: dict):
    res = {}
    for k, v in frame.items():
        if v is not None:
            res[k] = v
    return res
