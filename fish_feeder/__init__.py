__version__ = "0.1.0"

import typer


def run_server(
    dev: bool = typer.Option(False, help="Use --dev to run in development mode")
):
    """
    Run the server for the Fish Feeder.

    The --dev option will automatically reload when changes are detected.

    """
    import uvicorn

    if dev:
        uvicorn.run("fish_feeder.web_app:app", reload=True)
    else:
        uvicorn.run("fish_feeder.web_app:app", host="0.0.0.0")


def run():
    typer.run(run_server)
