from datetime import time
from fish_feeder import abstract
from functools import lru_cache
from typing import Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, FastAPI, Form, Request, status
from fastapi.params import Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from . import api as api_
from . import database
from .settings import Settings, get_settings

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")


def get_api(settings: Settings = Depends(get_settings)) -> api_.API:
    return api_.get_api(settings.simulate, settings)


def get_db(settings: Settings = Depends(get_settings)):
    return database.get_database_factory(settings.db_url())()


@lru_cache()
def get_scheduler() -> AsyncIOScheduler:
    logger.info("Creating scheduler")
    return AsyncIOScheduler()


@app.on_event("startup")
async def create_schedules():
    scheduler = get_scheduler()
    settings = get_settings()
    api = get_api(settings)
    db = get_db(settings)
    scheduler.add_job(
        api.feed_fish,
        trigger="cron",
        minute="*/1",
        kwargs={"db": db},
        id="feeding",
        name="Scheduled Feeding",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Started scheduler")


@app.get("/")
async def feeder_status(request: Request, db: database.Database = Depends(get_db)):
    return templates.TemplateResponse(
        "status.html",
        context={
            "request": request,
            "log_items": db.list_feedings(),
        },
    )


@app.get("/feed")
async def feed_fish_redirect(
    request: Request,
    bg: BackgroundTasks,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
):
    api.feed_fish(db, bg)
    return RedirectResponse(request.url_for("feeder_status"))


@app.get("/settings")
async def settings_get(
    request: Request,
    db: database.Database = Depends(get_db),
):
    return templates.TemplateResponse(
        "settings.html",
        context={
            "request": request,
            "feed_angle": db.get_feed_angle(),
            "schedules": db.list_schedules(),
        },
    )


@app.post("/settings")
async def settings_post(
    request: Request,
    db: database.Database = Depends(get_db),
    feed_angle: float = Form(...),
):
    db.set_feed_angle(feed_angle)
    return templates.TemplateResponse(
        "settings.html",
        context={
            "request": request,
            "feed_angle": db.get_feed_angle(),
            "schedules": db.list_schedules(),
        },
    )


@app.get("/settings/new-daily-schedule")
async def new_daily_schedule(request: Request):
    return templates.TemplateResponse(
        "edit-daily-schedule.html", context={"request": request}
    )


@app.post("/settings/new-daily-schedule")
async def new_daily_schedule_post(
    request: Request,
    db: database.Database = Depends(get_db),
    scheduled_time: time = Form(...),
):
    db.add_schedule(schedule_type=abstract.ScheduleMode.DAILY, time_=scheduled_time)
    return RedirectResponse(
        request.url_for("settings_get"), status_code=status.HTTP_303_SEE_OTHER
    )


@app.post("/api/feed")
async def feed_fish(
    bg: BackgroundTasks,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
):
    api.feed_fish(db, bg)
