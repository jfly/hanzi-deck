import html
import json
import os
import textwrap
from pathlib import Path
from typing import Generator

import pydantic

from . import hsk, subtlex, unihan


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


def load_mmahanzi_items() -> dict[str, MmaHanziItem]:
    makemeahanzi = Path(os.environ["MAKEMEAHANZI"])
    dictionary = makemeahanzi / "dictionary.txt"
    graphics = makemeahanzi / "graphics.txt"

    graphics_by_character: dict[str, MmaHanziGraphics] = {}
    for line in graphics.read_text().splitlines():
        mmagraphics = MmaHanziGraphics.model_validate_json(line)
        graphics_by_character[mmagraphics.character] = mmagraphics

    items: dict[str, MmaHanziItem] = {}
    for line in dictionary.read_text().splitlines():
        raw_item = json.loads(line)
        character = raw_item["character"]
        graphics = graphics_by_character[character]
        items[character] = MmaHanziItem.model_validate(
            {**raw_item, "graphics": graphics}
        )

    return items


class Template(pydantic.BaseModel):
    name: str
    question: str
    answer: str


class HanziNote(pydantic.BaseModel):
    character: str
    definition: str
    pinyin: str
    decomposition: str
    radical: str
    graphics_json_escaped_for_html_attribute: str
    character_count_per_million: str
    simplified_variants: str
    traditional_variants: str
    semantic_variants: str
    specialized_semantic_variants: str
    spoofing_variant: str
    z_variants: str
    hsk_2026_level: str

    @staticmethod
    def css() -> str:
        return textwrap.dedent("""\
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
        """)

    @staticmethod
    def templates() -> Generator[Template]:
        templates_dir = Path(os.environ["HANZI_DECK_TEMPLATES"])
        for template_dir in templates_dir.iterdir():
            yield Template(
                name=template_dir.name,
                question=(template_dir / "question.html").read_text(),
                answer=(template_dir / "answer.html").read_text(),
            )

    @staticmethod
    def media() -> Generator[Path]:
        media_dir = Path(os.environ["HANZI_DECK_MEDIA"])
        for file in media_dir.iterdir():
            yield file


def build_hanzi_notes() -> list[HanziNote]:
    hanzi_notes: list[HanziNote] = []

    unihan_db = unihan.Unihan()
    mmahanzi_items = load_mmahanzi_items()
    frequency_data = subtlex.load()
    hsk_data = hsk.load()
    for grapheme in unihan_db.grapheme_by_codepoint.values():
        character = grapheme.character

        definition = grapheme.definition()
        if definition is None:
            continue

        # Need to read more on compatibility variants, but
        # characters with compatibility variants don't seem
        # to have any interesting data that isn't captured
        # in the variant.
        if grapheme.compatibility_variant() is not None:
            continue

        mmahanzi_item = mmahanzi_items.get(character)
        decomposition = mmahanzi_item.decomposition if mmahanzi_item is not None else ""
        radical = mmahanzi_item.radical if mmahanzi_item is not None else ""
        graphics_json_escaped_for_html_attribute = (
            html.escape(mmahanzi_item.graphics.model_dump_json())
            if mmahanzi_item is not None
            else ""
        )

        hsk_datum = hsk_data.get(character)

        frequency_datum = frequency_data.get(character)

        def join_variants(variants: list[unihan.Codepoint]) -> str:
            return " ".join(map(chr, variants))

        hanzi_notes.append(
            HanziNote(
                character=character,
                definition=definition,
                pinyin=grapheme.pinyin() or "",
                decomposition=decomposition,
                radical=radical,
                graphics_json_escaped_for_html_attribute=graphics_json_escaped_for_html_attribute,
                character_count_per_million=(
                    str(frequency_datum.character_count_per_million)
                    if frequency_datum is not None
                    else ""
                ),
                hsk_2026_level=(
                    str(hsk_datum.hsk_2026_level() or "")
                    if hsk_datum is not None
                    else ""
                ),
                simplified_variants=join_variants(grapheme.simplified_variants()),
                traditional_variants=join_variants(grapheme.traditional_variants()),
                semantic_variants=join_variants(grapheme.semantic_variants()),
                specialized_semantic_variants=join_variants(
                    grapheme.specialized_semantic_variants()
                ),
                spoofing_variant=join_variants(grapheme.spoofing_variant()),
                z_variants=join_variants(grapheme.z_variants()),
            )
        )

    return hanzi_notes
