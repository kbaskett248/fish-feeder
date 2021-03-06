from datetime import datetime, time
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, Form, Request, status
from fastapi.params import Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

from . import api as api_
from . import database, scheduler
from .settings import Settings, get_settings
from . import __version__ as PACKAGE_VERSION

API_VERSION = "0.1.0"

BASEDIR = Path(__file__).resolve(strict=True).parent
STATIC_PATH = BASEDIR / "static"
TEMPLATE_PATH = BASEDIR / "templates"

app = FastAPI(title="Fish Feeder 5000", version=API_VERSION)
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
templates = Jinja2Templates(directory=TEMPLATE_PATH)

logger.info("Package version: {}", PACKAGE_VERSION)


def get_api(settings: Settings = Depends(get_settings)) -> api_.API:
    return api_.get_api(
        database.get_database_factory(settings.db_url()), settings.simulate, settings
    )


def get_db(settings: Settings = Depends(get_settings)) -> database.Database:
    return database.get_database_factory(settings.db_url())()


def get_scheduler() -> scheduler.Scheduler:
    return scheduler.get_scheduler()


def schedule_job_id(schedule: database.Schedule) -> str:
    return str(hash(schedule))


@app.on_event("startup")
async def create_schedules():
    scheduler = get_scheduler()
    settings = get_settings()
    api = get_api(settings)
    db = get_db(settings)
    api.load_scheduled_feedings(db, scheduler)


@app.get("/", include_in_schema=False)
async def feeder_status(
    request: Request,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
    scheduler: scheduler.Scheduler = Depends(get_scheduler),
):
    scheduled_feedings = api.next_feeding_times(scheduler)
    try:
        next_feeding = f"{scheduled_feedings[0]:%Y-%m-%d %H:%M}"
    except IndexError:
        next_feeding = "No feedings scheduled"
    return templates.TemplateResponse(
        "status.html",
        context={
            "request": request,
            "log_items": db.list_feedings(),
            "next_feeding": next_feeding,
        },
    )


@app.get("/feed", include_in_schema=False)
async def feed_fish_redirect(
    request: Request,
    bg: BackgroundTasks,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
):
    api.feed_fish(db, bg)
    return RedirectResponse(request.url_for("feeder_status"))


@app.get("/settings", include_in_schema=False)
async def settings_get(
    request: Request,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
    scheduler: scheduler.Scheduler = Depends(get_scheduler),
):
    schedules = [
        {
            "schedule": str(schedule),
            "next_feeding": f"{next_feeding:%Y-%m-%d %H:%M}" if next_feeding else "",
            "id": schedule.id,
        }
        for schedule, next_feeding in api.list_schedules_with_runtimes(db, scheduler)
    ]

    return templates.TemplateResponse(
        "settings.html",
        context={
            "request": request,
            "feed_angle": db.get_feed_angle(),
            "schedules": schedules,
        },
    )


@app.post("/settings", include_in_schema=False)
async def settings_post(
    request: Request,
    db: database.Database = Depends(get_db),
    feed_angle: float = Form(...),
):
    db.set_feed_angle(feed_angle)
    return RedirectResponse(
        request.url_for("settings_get"), status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/settings/new-daily-schedule", include_in_schema=False)
async def new_daily_schedule(request: Request):
    return templates.TemplateResponse(
        "edit-daily-schedule.html", context={"request": request}
    )


@app.post("/settings/new-daily-schedule", include_in_schema=False)
async def new_daily_schedule_post(
    request: Request,
    db: database.Database = Depends(get_db),
    scheduler: scheduler.Scheduler = Depends(get_scheduler),
    api: api_.API = Depends(get_api),
    scheduled_time: time = Form(...),
):
    api.add_scheduled_feeding(db, scheduler, scheduled_time)
    return RedirectResponse(
        request.url_for("settings_get"), status_code=status.HTTP_303_SEE_OTHER
    )


@app.post("/settings/remove-schedule/{item_id}", include_in_schema=False)
async def remove_schedule(
    item_id: int,
    request: Request,
    db: database.Database = Depends(get_db),
    scheduler: scheduler.Scheduler = Depends(get_scheduler),
    api: api_.API = Depends(get_api),
):
    api.remove_scheduled_feeding(db, scheduler, item_id)
    return RedirectResponse(
        request.url_for("settings_get"), status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(
        "/static/favicon.ico", status_code=status.HTTP_301_MOVED_PERMANENTLY
    )


class Feeding(BaseModel):
    time_requested: datetime
    time_fed: Optional[datetime]

    class Config:
        orm_mode = True


@app.post("/api/feedings", response_model=Feeding)
async def feed_fish(
    bg: BackgroundTasks,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
):
    """Schedule the fish to be fed."""
    return api.feed_fish(db, bg)


@app.get("/api/feedings", response_model=List[Feeding])
async def feed_fish(
    limit=20,
    date_limit: Optional[datetime] = None,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
):
    """Return the times that the fish was fed."""
    return api.list_feedings(db, limit, date_limit)


class ScheduledFeeding(BaseModel):
    scheduled_time: datetime


@app.get("/api/scheduled_feedings", response_model=List[ScheduledFeeding])
async def next_feedings(
    bg: BackgroundTasks,
    api: api_.API = Depends(get_api),
    scheduler: scheduler.Scheduler = Depends(get_scheduler),
):
    """Return the upcoming feeding times."""
    return [{"scheduled_time": t} for t in api.next_feeding_times(scheduler)]
