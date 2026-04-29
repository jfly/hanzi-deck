from pathlib import Path
from typing import Annotated

import anki.collection
import typer

from . import anki_collection

app = typer.Typer()


@app.command()
def main(
    output: Annotated[Path, typer.Argument(dir_okay=False, metavar="[output.apkg]")],
):
    with anki_collection.temp_collection() as col:
        col.export_anki_package(
            # Calling `absolute` is a workaround for the fact that Anki crashes if you try to export to a relative path with one component:
            # <https://forums.ankiweb.net/t/anki-collection-collection-export-anki-package-crashes-if-given-a-relative-path-with-one-component/69562>
            out_path=str(output.absolute()),
            options=anki.collection.ExportAnkiPackageOptions(with_media=True),
            limit=None,
        )

    print(f"Success! Generated {output}")


if __name__ == "__main__":
    app()  # pragma: no cover
