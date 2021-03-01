from functools import lru_cache
from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from . import abstract
from .api import API


class Scheduler(abstract.Scheduler):
    apscheduler: AsyncIOScheduler

    def __init__(self) -> None:
        super().__init__()
        self.apscheduler = AsyncIOScheduler()

    def load_schedules(
        self, db: abstract.Database, api: API, get_db_callback: Callable
    ):
        self._load_scheduled_feedings(db, api, get_db_callback)

    def _load_scheduled_feedings(
        self, db: abstract.Database, api: API, get_db_callback: Callable
    ):
        def feed_fish():
            db_ = get_db_callback()
            api.feed_fish(db_)

        for feeding_schedule in db.list_schedules():
            await self._add_feeding_job(feeding_schedule, feed_fish)

    async def _add_feeding_job(
        self, feeding_schedule: abstract.Schedule, callback: Callable
    ):
        kwargs = {
            "trigger": "cron",
            "id": feeding_schedule.id,
            "name": "Scheduled Feeding",
            "misfire_grace_time": 3600,
            "coalesce": True,
            "max_instances": 1,
        }
        cron_args = feeding_schedule.get_cron_args()
        kwargs.update(cron_args)
        job = self.apscheduler.add_job(callback, **kwargs)
        logger.info("Added scheduled feeding: {}", job)


@lru_cache()
def get_scheduler() -> Scheduler:
    return Scheduler()
