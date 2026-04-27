import os
from functools import cache
from pathlib import Path
from typing import Annotated

import genanki
import pydantic
import typer

app = typer.Typer()


class MmaHanziItem(pydantic.BaseModel):
    character: str
    definition: str | None = pydantic.Field(default=None)
    pinyin: list[str]
    decomposition: str
    radical: str


def load_mmahanzi_items() -> list[MmaHanziItem]:
    makemeahanzi = Path(os.environ["MAKEMEAHANZI"])
    dictionary = makemeahanzi / "dictionary.txt"

    items: list[MmaHanziItem] = []
    for line in dictionary.read_text().splitlines():
        items.append(MmaHanziItem.model_validate_json(line))

    return items


class AnkiHanzi(pydantic.BaseModel):
    character: str
    definition: str
    pinyin: str
    decomposition: str
    radical: str

    def to_anki_note(self) -> genanki.Note:
        anki_model = self.__class__.to_anki_model()
        return genanki.Note(
            model=anki_model,
            fields=[
                getattr(self, field_name)
                for field_name in self.__class__.model_fields.keys()
            ],
        )

    @classmethod
    @cache
    def to_anki_model(cls) -> genanki.Model:
        templates_dir = Path("./templates")
        return genanki.Model(
            1197179238,
            "Hanzi",
            fields=[{"name": field_name} for field_name in cls.model_fields.keys()],
            templates=[
                {
                    "name": "Character",
                    "qfmt": (template_dir / "question.html").read_text(),
                    "afmt": (template_dir / "answer.html").read_text(),
                }
                for template_dir in templates_dir.iterdir()
            ],
            css="""
@font-face {
  font-family: SerifFont;
  src: url("character.js");
}
            """,
        )


@app.command()
def main(
    output: Annotated[
        Path | None, typer.Argument(dir_okay=False, metavar="[output.apkg]")
    ],
):
    mmahanzi_items = load_mmahanzi_items()
    hanzi_deck = genanki.Deck(1092097767, "Hanzi")

    for mmahanzi_item in mmahanzi_items:
        pinyin = ", ".join(mmahanzi_item.pinyin)
        definition = mmahanzi_item.definition or ""

        anki_hanzi = AnkiHanzi(
            character=mmahanzi_item.character,
            definition=definition,
            pinyin=pinyin,
            decomposition=mmahanzi_item.decomposition,
            radical=mmahanzi_item.radical,
        )
        hanzi_deck.add_note(anki_hanzi.to_anki_note())

    genanki.Package(
        hanzi_deck, media_files=[Path("templates/character/_character.js")]
    ).write_to_file(output)


if __name__ == "__main__":
    app()  # pragma: no cover
