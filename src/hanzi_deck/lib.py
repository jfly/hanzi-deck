import contextlib
import html
import json
import os
import tempfile
from functools import cache
from pathlib import Path
from typing import Generator

import anki.collection
import anki.decks
import anki.models
import anki.notes
import pydantic


class MmaHanziGraphics(pydantic.BaseModel):
    character: str
    strokes: list[str]
    medians: list[list[list[float]]]


class MmaHanziItem(pydantic.BaseModel):
    character: str
    definition: str | None = pydantic.Field(default=None)
    pinyin: list[str]
    decomposition: str
    radical: str
    graphics: MmaHanziGraphics


def load_mmahanzi_items() -> list[MmaHanziItem]:
    makemeahanzi = Path(os.environ["MAKEMEAHANZI"])
    dictionary = makemeahanzi / "dictionary.txt"
    graphics = makemeahanzi / "graphics.txt"

    graphics_by_character: dict[str, MmaHanziGraphics] = {}
    for line in graphics.read_text().splitlines():
        mmagraphics = MmaHanziGraphics.model_validate_json(line)
        graphics_by_character[mmagraphics.character] = mmagraphics

    items: list[MmaHanziItem] = []
    for line in dictionary.read_text().splitlines():
        raw_item = json.loads(line)
        character = raw_item["character"]
        graphics = graphics_by_character[character]
        items.append(MmaHanziItem.model_validate({**raw_item, "graphics": graphics}))

    return items


class AnkiHanzi(pydantic.BaseModel):
    character: str
    definition: str
    pinyin: str
    decomposition: str
    radical: str
    graphics_json_escaped_for_html_attribute: str

    def to_anki_note(self, col: anki.collection.Collection) -> anki.notes.Note:
        note = col.new_note(self.__class__.to_anki_model(col))
        for field_name in self.__class__.model_fields.keys():
            note[field_name] = getattr(self, field_name)

        return note

    @classmethod
    @cache
    def to_anki_model(cls, col: anki.collection.Collection) -> anki.models.NotetypeDict:
        model = col.models.new("Hanzi")
        model["css"] = """
.card {
    font-family: arial;
    font-size: 20px;
    line-height: 1.5;
    text-align: center;
    color: black;
    background-color: white;
}

.character {
    font-size: 80px;
}
"""

        # Add fields.
        for field_name in cls.model_fields.keys():
            field = col.models.new_field(field_name)
            col.models.add_field(model, field)

        # Add templates.
        templates_dir = Path(os.environ["HANZI_DECK_TEMPLATES"])
        for template_dir in templates_dir.iterdir():
            tmpl = col.models.new_template(template_dir.name)
            tmpl["qfmt"] = (template_dir / "question.html").read_text()
            tmpl["afmt"] = (template_dir / "answer.html").read_text()
            col.models.add_template(model, tmpl)

        # Add media.
        media_dir = Path(os.environ["HANZI_DECK_MEDIA"])
        for file in media_dir.iterdir():
            col.media.add_file(str(file))

        col.models.add(model)

        return model


class HanziNotes:
    def __init__(self, col: anki.collection.Collection) -> None:
        self._col = col
        self.notes: list[anki.notes.Note] = []

        # TODO: <<< figure out why notes aren't getting added to this deck. They're landing in the default deck instead >>>
        deck = col.decks.new_deck()
        deck.name = "Homemade Hanzi"
        col.decks.add_deck(deck)
        self._deck_id = anki.decks.DeckId(deck.id)

        mmahanzi_items = load_mmahanzi_items()
        for mmahanzi_item in mmahanzi_items:
            pinyin = ", ".join(mmahanzi_item.pinyin)
            definition = mmahanzi_item.definition or ""

            anki_hanzi = AnkiHanzi(
                character=mmahanzi_item.character,
                definition=definition,
                pinyin=pinyin,
                decomposition=mmahanzi_item.decomposition,
                radical=mmahanzi_item.radical,
                graphics_json_escaped_for_html_attribute=html.escape(
                    mmahanzi_item.graphics.model_dump_json()
                ),
            )

            self.notes.append(anki_hanzi.to_anki_note(self._col))

        # >>> add_notes allows for one time iterables, but it assumes it can iterate over in inpute multiple times: https://github.com/ankitects/anki/blob/25.09.2/pylib/anki/collection.py#L537-L551 <<<
        col.add_notes(
            [anki.collection.AddNoteRequest(note, self._deck_id) for note in self.notes]
        )

    def export_anki_package(self, output: Path):
        self._col.export_anki_package(
            # <<< # this crashes here:
            # <<< # - https://github.com/ankitects/anki/blob/25.09.2/rslib/src/import_export/package/apkg/export.rs#L64
            # <<< # - https://github.com/ankitects/anki/blob/25.09.2/rslib/io/src/lib.rs#L266
            # <<< out_path="yoo.apkg",
            out_path=str(output.absolute()),
            options=anki.collection.ExportAnkiPackageOptions(with_media=True),
            limit=None,  # <<<
            # <<< limit=anki.collection.DeckIdLimit(self._deck_id),
        )


@contextlib.contextmanager
def temp_collection() -> Generator[anki.collection.Collection, None, None]:
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        yield anki.collection.Collection(str(tempdir / "temp.anki2"))


@contextlib.contextmanager
def build_notes() -> Generator[HanziNotes, None, None]:
    with temp_collection() as col:
        yield HanziNotes(col)
