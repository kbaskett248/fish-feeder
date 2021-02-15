from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

import api

app = FastAPI()
templates = Jinja2Templates(directory="templates/")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "status.html", context={"request": request, "feed_url": "/feed"}
    )


@app.get("/feed")
async def feed_fish_redirect(request: Request):
    api.feed_fish()
    return RedirectResponse("/")


@app.post("/api/feed")
async def feed_fish():
    api.feed_fish()


if __name__ == "__main__":
    uvicorn.run("web_app:app", reload=True)
