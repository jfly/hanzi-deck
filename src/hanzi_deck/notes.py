import base64
import hashlib
import json
import os
import tempfile
import textwrap
import zlib
from pathlib import Path
from typing import Generator

import cbor2
import pydantic

from . import hsk, npcr, subtlex, unihan


def strip_parentheticals(sentence: str) -> str:
    """
    Remove parentheticals (and up to 1 surround space) from the given sentence.

    Example:

    >>> strip_parentheticals("(same as 丘) hillock or mound")
    'hillock or mound'

    >>> strip_parentheticals("I love chocolate (especially dark (please no nuts, though)).")
    'I love chocolate.'

    >>> strip_parentheticals("Now we're (really)() being weird.")
    "Now we're being weird."

    >>> strip_parentheticals("I like 2 spaces.  After periods.")
    'I like 2 spaces.  After periods.'

    >>> strip_parentheticals("()")
    ''
    """

    pieces: list[str] = []
    just_exited_parenthetical = True
    depth = 0
    for ch in sentence:
        if ch == "(":
            depth += 1
            continue
        elif ch == ")":
            depth -= 1
            just_exited_parenthetical = True
            continue

        if depth == 0:
            if just_exited_parenthetical:
                pieces.append("")
                just_exited_parenthetical = False
            pieces[-1] += ch

    result: list[str] = []
    last_piece_ended_in_space = False
    for piece in pieces:
        if piece.startswith(" "):
            # Only remove spaces from the start of a piece
            # if the last piece did not end in a space.
            if not last_piece_ended_in_space:
                piece = piece[1:]

        if piece.endswith(" "):
            last_piece_ended_in_space = True
            piece = piece[:-1]
        else:
            last_piece_ended_in_space = False

        result.append(piece)

    return "".join(result)


class MmaHanziGraphics(pydantic.BaseModel):
    character: str
    strokes: list[str]
    medians: list[list[list[float]]]


class MmaHanziItem(pydantic.BaseModel):
    character: str
    definition: str | None = pydantic.Field(default=None)
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


_CA_MEDIA_TEMPDIR: tempfile.TemporaryDirectory | None = None


def get_content_addressed_media_dir() -> Path:
    """
    Given `HANZI_DECK_MEDIA`, produce a directory that contains the exact
    same filenames, but with the filenames uniquely named based on their
    content. This is a workaround for the fact that Anki won't update media
    files when re-importing a deck [0].

    [0]: https://forums.ankiweb.net/t/reimport-apkg-and-update-existing-media/69732
    """
    global _CA_MEDIA_TEMPDIR

    if _CA_MEDIA_TEMPDIR is not None:
        return Path(_CA_MEDIA_TEMPDIR.name)

    ca_media_tempdir = tempfile.TemporaryDirectory()
    ca_media_dir = Path(ca_media_tempdir.name)

    media_dir = Path(os.environ["HANZI_DECK_MEDIA"])
    for file in media_dir.iterdir():
        with file.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256")

        # Use the original filename, but insert the hex digest right before the file extension.
        ca_file = ca_media_dir / f"{file.stem}-{digest.hexdigest()}{file.suffix}"
        ca_file.symlink_to(file)

    _CA_MEDIA_TEMPDIR = ca_media_tempdir
    return ca_media_dir


class HanziNote(pydantic.BaseModel):
    character: str
    full_definition: str
    definition_without_parentheticals: str
    npcr_definition: str
    decomposition: str
    radical: str
    graphics_cbor_zlib_base64: str
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
        # HACK: Replace all references to media in templates with the content
        # addressed names instead. This is a workaround for the fact that Anki
        # won't update media on when reimporting a deck [0].
        #
        # [0]: https://forums.ankiweb.net/t/reimport-apkg-and-update-existing-media/69732
        media_to_ca_media_mappings = {
            f.readlink().name: f.name
            for f in get_content_addressed_media_dir().iterdir()
        }

        def replace_media_with_ca_media(input: str) -> str:
            for media, ca_media in media_to_ca_media_mappings.items():
                input = input.replace(media, ca_media)

            return input

        templates_dir = Path(os.environ["HANZI_DECK_TEMPLATES"])
        for template_dir in templates_dir.iterdir():
            yield Template(
                name=template_dir.name,
                question=replace_media_with_ca_media(
                    (template_dir / "question.html").read_text()
                ),
                answer=replace_media_with_ca_media(
                    (template_dir / "answer.html").read_text()
                ),
            )

    @staticmethod
    def media() -> Generator[Path]:
        media_dir = get_content_addressed_media_dir()
        for file in media_dir.iterdir():
            yield file


def build_hanzi_notes() -> list[HanziNote]:
    hanzi_notes: list[HanziNote] = []

    unihan_db = unihan.Unihan()
    mmahanzi_items = load_mmahanzi_items()
    frequency_data = subtlex.load()
    hsk_data = hsk.load()
    npcr_data = npcr.load()
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
        graphics_cbor_zlib_base64 = (
            base64.b64encode(
                zlib.compress(
                    cbor2.dumps(mmahanzi_item.graphics.model_dump()),
                    # Negative values give us "raw" compression, with no header
                    # or trailing checksum.
                    # This corresponds to CompressionFormat == "deflate-raw" in a web browser.
                    wbits=-15,
                )
            ).decode()
            if mmahanzi_item is not None
            else ""
        )

        hsk_datum = hsk_data.get(character)

        frequency_datum = frequency_data.get(character)

        def join_variants(variants: list[unihan.Codepoint]) -> str:
            return " ".join(map(chr, variants))

        npcr_datum = npcr_data.get(character)

        hanzi_notes.append(
            HanziNote(
                character=character,
                full_definition=definition,
                definition_without_parentheticals=strip_parentheticals(definition),
                npcr_definition=npcr_datum.definition if npcr_datum is not None else "",
                decomposition=decomposition,
                radical=radical,
                graphics_cbor_zlib_base64=graphics_cbor_zlib_base64,
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
