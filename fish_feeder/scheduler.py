from datetime import time
from functools import lru_cache
from typing import Callable, List, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from . import abstract
from .api import API


class Scheduler(abstract.Scheduler):
    apscheduler: AsyncIOScheduler

    def __init__(self) -> None:
        super().__init__()
        self.apscheduler = AsyncIOScheduler()
        self.apscheduler.start()
        logger.info("Started scheduler")

    def add_scheduled_feeding(
        self, feeding_schedule: abstract.Schedule, feeding_callback: Callable
    ):
        kwargs = {
            "trigger": "cron",
            "id": feeding_schedule.get_id(),
            "name": "Scheduled Feeding",
            "misfire_grace_time": 3600,
            "coalesce": True,
            "max_instances": 1,
        }
        cron_args = feeding_schedule.get_cron_args()
        kwargs.update(cron_args)
        job = self.apscheduler.add_job(feeding_callback, **kwargs)
        logger.info("Added scheduled feeding: {}", job)

    def remove_scheduled_feeding(self, feeding_schedule: abstract.Schedule):
        job = self.apscheduler.get_job(feeding_schedule.get_id())
        logger.info("Removing scheduled job: {}", job)
        if job:
            job.remove()

    def list_scheduled_feedings(self) -> List[Tuple[str, time]]:
        return [(job.id, job.next_run_time) for job in self.apscheduler.get_jobs()]


@lru_cache()
def get_scheduler() -> Scheduler:
    return Scheduler()
