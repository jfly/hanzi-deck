import os
import time
from pathlib import Path
from typing import Annotated

import typer

from .genanki_package import generate_package

app = typer.Typer()


@app.command()
def main(
    output: Annotated[Path, typer.Argument(dir_okay=False, metavar="[output.apkg]")],
):
    timestamp = int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))

    with generate_package() as package:
        package.write_to_file(output, timestamp=timestamp)

    print(f"Success! Generated {output}")


if __name__ == "__main__":
    app()  # pragma: no cover
