from app.znayko.models import SubscriptionEvent
from cachable.storage import Storage
import logging
import pickle
from app.znayko.client import Client as ZnaykoClient
from app.lametric.models import STORAGE_KEY

class Scores(dict):

    __has_changes = False

    def __setitem__(self, __k, __v) -> None:
        if self.get(__k, "") != __v:
            self.__has_changes = True
        return super().__setitem__(__k, __v)

    def __delitem__(self, __v) -> None:
        return super().__delitem__(__v)

    @property
    def has_changes(self):
        res = self.__has_changes
        self.__has_changes = False
        return res


class SubscriptionsMeta(type):

    __instances = {}

    def __call__(cls, storage_key, *args, **kwds):
        if storage_key not in cls.__instances:
            cls.__instances[storage_key] = type.__call__(
                cls, storage_key, *args, **kwds)
        return cls.__instances[storage_key]

    @property
    def livescores(cls) -> 'Subscriptions':
        return cls(STORAGE_KEY.LIVESCORES.value)

    def _load(cls, storage_key) -> dict[str, SubscriptionEvent]:
        data = Storage.hgetall(storage_key)
        if not data:
            logging.debug("no data")
            return []
        items = {k: pickle.loads(v) for k, v in data.items()}
        return items


class Subscriptions(dict, metaclass=SubscriptionsMeta):

    __storage_key = None
    __scores: Scores = None

    def __init__(self, storage_key, *args, **kwds):
        self.__storage_key = storage_key
        self.__scores = Scores({})
        items = __class__._load(storage_key)
        super().__init__(items, *args, **kwds)

    def __setitem__(self, __k, __v) -> None:
        Storage.pipeline().hset(self.__storage_key, __k, pickle.dumps(
            __v)).persist(self.__storage_key).execute()
        if __v.score:
            self.__scores[__k] = __v.score
        return super().__setitem__(__k, __v)

    def __delitem__(self, __v) -> None:
        Storage.pipeline().hdel(self.__storage_key, __v).persist(
            self.__storage_key).execute()
        return super().__delitem__(__v)

    def __load_scores(self):
        data = ZnaykoClient.livescores()
        ids = [x.id for x in self.events]
        events = list(filter(lambda x: x.id in ids, data))
        if not len(events):
            return
        store = Storage.pipeline()
        for event in events:
            text = event.displayScore
            sub = next(filter(lambda x: x.id ==
                       event.id, self.subscriptions), None)
            if not sub:
                return
            sub.status = event.displayStatus
            store.hset(self.__storage_key,
                       sub.id, pickle.dumps(sub))
            self.__scores[event.id] = text
        store.persist(self.__storage_key).execute()

    @property
    def events(self) -> list[SubscriptionEvent]:
        print(list(super().values()))
        return list(super().values())

    @property
    def scores(self) -> Scores:
        self.__load_scores()
        return self.__scores
