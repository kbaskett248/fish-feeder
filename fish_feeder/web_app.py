from functools import lru_cache

import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.params import Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from . import api as api_
from .settings import Settings, get_settings

app = FastAPI()
templates = Jinja2Templates(directory="templates/")


def get_api(
    bg: BackgroundTasks, settings: Settings = Depends(get_settings)
) -> api_.API:
    return api_.get_api(settings.simulate, bg, settings)


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "status.html", context={"request": request, "feed_url": "/feed"}
    )


@app.get("/feed")
async def feed_fish_redirect(api: api_.API = Depends(get_api)):
    api.feed_fish()
    return RedirectResponse("/")


@app.post("/api/feed")
async def feed_fish(api: api_.API = Depends(get_api)):
    api.feed_fish()


if __name__ == "__main__":
    uvicorn.run("web_app:app", reload=True)
