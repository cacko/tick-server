import corelog
import os


corelog.register(os.environ.get("TICK_LOG_LEVEL", "INFO"), corelog.Handlers.RICH)
