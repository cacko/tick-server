import logging
from queue import Queue
import uvicorn
from app.config import app_config
from typing import Optional
from fastapi import FastAPI
from app.api.routers.rest import router as rest_router


class ServerMeta(type):

    _instance: Optional["Server"] = None
    _mainQueue: Optional[Queue] = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = type.__call__(self, *args, **kwds)
        return self._instance

    def start(cls, mainQueue):
        cls._mainQueue = mainQueue
        cls().start_server()



class Server(object, metaclass=ServerMeta):
    
    server: Optional[uvicorn.Server]

    def __init__(self, *args, **kwargs):
        self.app = FastAPI()
        self.app.include_router(rest_router)
        super().__init__(*args, **kwargs)
    
    def start_server(self):
        config = app_config.api
        server_config = uvicorn.Config(
            app=self.app,
            host=config.host,
            port=config.port,
            use_colors=True,
            loop="uvloop",
            log_level=logging.root.level
        )
        self.server = uvicorn.Server(server_config)
        self.server.run()
