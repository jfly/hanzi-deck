import os
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def main(
    host: Annotated[str, typer.Option()] = "localhost",
):
    from . import preview_flask_app

    preview_flask_app.app.run(
        host=host,
        debug=True,
        extra_files=list(Path(os.environ["HANZI_DECK_TEMPLATES"]).glob("**")),
    )


if __name__ == "__main__":
    app()
