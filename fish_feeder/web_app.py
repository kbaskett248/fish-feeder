from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates/")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("status.html", context={"request": request})


if __name__ == "__main__":
    uvicorn.run(app)
