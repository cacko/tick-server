from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler


class RedisNotConfiguredException(Exception):
    pass


class SchedulerMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    def start(cls):
        cls().scheduler.start()

    def stop(cls):
        try:
            cls().scheduler.shutdown()
        except Exception:
            pass

    def add_job(cls, *args, **kwargs):
        return cls().scheduler.add_job(*args, **kwargs)

    def get_job(cls, id, jobstore=None):
        return cls().scheduler.get_job(id, jobstore)

    def cancel_jobs(cls, id, jobstore=None):
        return cls().scheduler.remove_job(id, jobstore)

    def remove_all_jobs(cls, jobstore=None):
        return cls().scheduler.remove_all_jobs(jobstore)

    def get_jobs(cls, jobstore=None, pending=None):
        return cls().scheduler.get_jobs(jobstore, pending)


class Scheduler(object, metaclass=SchedulerMeta):

    scheduler: BackgroundScheduler

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(
            jobstores=dict(default=MemoryJobStore())
        )
