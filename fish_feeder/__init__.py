__version__ = "0.1.0"


def run():
    import uvicorn

    uvicorn.run("fish_feeder.web_app:app", reload=True)
