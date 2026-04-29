import html
import json
import os
import random
from pathlib import Path

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


class HanziNote(pydantic.BaseModel):
    character: str
    definition: str
    pinyin: str
    decomposition: str
    radical: str
    graphics_json_escaped_for_html_attribute: str
    random_number: str  # <<<


def build_hanzi_notes() -> list[HanziNote]:
    hanzi_notes: list[HanziNote] = []

    mmahanzi_items = load_mmahanzi_items()
    for mmahanzi_item in mmahanzi_items:
        pinyin = ", ".join(mmahanzi_item.pinyin)
        definition = mmahanzi_item.definition or ""

        hanzi_notes.append(
            HanziNote(
                character=mmahanzi_item.character,
                definition=definition,
                pinyin=pinyin,
                decomposition=mmahanzi_item.decomposition,
                radical=mmahanzi_item.radical,
                graphics_json_escaped_for_html_attribute=html.escape(
                    mmahanzi_item.graphics.model_dump_json()
                ),
                random_number=f"Have a random number: {random.randint(0, 100)}",  # <<<
            )
        )

    return hanzi_notes
