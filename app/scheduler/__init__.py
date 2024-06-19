from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional


class SchedulerMeta(type):
    _instance: Optional['Scheduler'] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    def start(cls):
        cls()._scheduler.start()

    def stop(cls):
        cls()._scheduler.shutdown()

    def add_job(cls, *args, **kwargs):
        return cls()._scheduler.add_job(*args, **kwargs)

    def get_job(cls, id, jobstore=None):
        return cls()._scheduler.get_job(id, jobstore)

    def cancel_jobs(cls, id, jobstore=None):
        return cls()._scheduler.remove_job(id, jobstore)

    def remove_all_jobs(cls, jobstore=None):
        return cls()._scheduler.remove_all_jobs(jobstore)

    def get_jobs(cls, jobstore=None, pending=None):
        return cls()._scheduler.get_jobs(jobstore, pending)


class Scheduler(object, metaclass=SchedulerMeta):

    _scheduler: BackgroundScheduler = None
    _instance = None

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(
            jobstores=dict(default=MemoryJobStore())
        )
