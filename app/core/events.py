from enum import Enum
import logging
from threading import Event
from typing import Callable


class BUTTON_EVENTS(Enum):
    LIVESCORES_UNSUBSCRIBE = "action.livescores=unsubscribe"
    LIVESCORES_CLEAN = "action.livescores=clean"
    YANKO_PLAY_PAUSE = "action.yanko=play/pause"
    YANKO_NEXT = "action.yanko=next"
    YANKO_ARTIST = "action.yanko=artist"
    YANKO_ALBUM = "action.yanko=artist"


class EventManagerMeta(type):

    __instance = None
    __listeners: dict[BUTTON_EVENTS, list[Callable]] = {}

    def __call__(cls, *args, **kwds):
        if not cls.__instance:
            cls.__instance = type.__call__(cls, {}, *args, **kwds)
        return cls.__instance

    def on_trigger(cls, payload: list[str]):
        for event_name in payload:
            try:
                ev = BUTTON_EVENTS(event_name)
                cls()[ev] = True
                if ev in cls.__listeners:
                    for cb in cls.__listeners[ev]:
                        cb()
            except ValueError:
                logging.error(f"{event_name} is not registered event")
                pass

    def listen(cls, bev: BUTTON_EVENTS, callback: Callable) -> Event:
        ev = cls().get(bev)
        if ev not in cls.__listeners:
            cls.__listeners[bev] = []
        cls.__listeners[bev].append(callback)
        return ev


class EventManager(dict[BUTTON_EVENTS, Event], metaclass=EventManagerMeta):
    def __getitem__(self, __k) -> Event:
        if __k not in self.keys():
            super().__setitem__(__k, Event())
        return super().__getitem__(__k)

    def __setitem__(self, __k, __v):
        ev: Event = self.__getitem__(__k)
        if __v:
            ev.set()
        else:
            ev.clear()
        return super().__setitem__(__k, ev)
