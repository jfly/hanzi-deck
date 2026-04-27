from pathlib import Path
from typing import Annotated

import typer

from . import lib

app = typer.Typer()


@app.command()
def main(
    output: Annotated[Path, typer.Argument(dir_okay=False, metavar="[output.apkg]")],
):
    with lib.build_notes() as hanzi_notes:
        hanzi_notes.export_anki_package(output)

    print(f"Success! Generated {output}")


if __name__ == "__main__":
    app()  # pragma: no cover
