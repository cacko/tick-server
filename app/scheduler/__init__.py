from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from urllib.parse import urlparse, parse_qs
from app.config import app_config

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
        self.scheduler = BackgroundScheduler()
        redis_url = urlparse(app_config.storage.redis_url)
        redis_url_options = parse_qs(redis_url.query)
        jobstores = None

        if redis_url.scheme == "redis":
            jobstores = {
                "default": RedisJobStore(
                    host=redis_url.hostname,
                    db=int(redis_url.path.strip("/")),
                )
            }
        elif redis_url.scheme == "unix":
            jobstores = {
                "default": RedisJobStore(
                    unix_socket_path=redis_url.path,
                    db=int(redis_url_options.get("db", [])[0]),
                )
            }
        else:
            raise RedisNotConfiguredException("not valid REDIS_URL")
        self.scheduler.configure(jobstores=jobstores)
