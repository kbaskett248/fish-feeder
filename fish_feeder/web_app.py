from functools import lru_cache
from typing import Tuple

from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.params import Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


@app.get("/")
async def status(request: Request, db: database.Database = Depends(get_db)):
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
    return RedirectResponse(request.url_for("status"))


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
        },
    )


@app.post("/api/feed")
async def feed_fish(
    bg: BackgroundTasks,
    api: api_.API = Depends(get_api),
    db: database.Database = Depends(get_db),
):
    api.feed_fish(db, bg)
