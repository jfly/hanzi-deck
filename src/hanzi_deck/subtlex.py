# Utilities for parsing [SUBTLEX-CH].
#
# Expects a `SUBTLEX_CH` environment variable to be set pointing to an
# extracted version of [pone.0010729.s002.zip]
#
# [SUBTLEX-CH]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0010729
# [pone.0010729.s002.zip]: https://doi.org/10.1371/journal.pone.0010729.s002

import csv
import os
from pathlib import Path

import pydantic


class CharacterData(pydantic.BaseModel):
    # https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0010729#pone-0010729-g001
    character: str = pydantic.Field(alias="Character")
    character_count: int = pydantic.Field(alias="CHRCount")
    character_count_per_million: float = pydantic.Field(alias="CHR/million")
    film_count: float = pydantic.Field(alias="CHR-CD")
    film_percentage: float = pydantic.Field(alias="CHR-CD%")


def load() -> dict[str, CharacterData]:
    subtlex_character_data = Path(os.environ["SUBTLEX_CH"]) / "SUBTLEX-CH-CHR"
    # AFAICT, these files are underspecified in the original document.
    # They're TSVs, with some quirks:
    # - They're encoded in the [GBK] encoding, rather than utf-8.
    # - They start with 1 or 2 quoted strings before the TSV data begins
    #
    # [GBK]: https://en.wikipedia.org/wiki/GBK_(character_encoding)
    lines = subtlex_character_data.read_text(encoding="gbk").splitlines()
    assert (line := lines.pop(0)).startswith('"'), f"Unexpected line {line}"
    assert (line := lines.pop(0)).startswith('"'), f"Unexpected line {line}"

    data_by_char: dict[str, CharacterData] = {}
    reader = csv.DictReader(lines, dialect=csv.excel_tab)
    for row in reader:
        data = CharacterData.model_validate(row)
        data_by_char[data.character] = data

    return data_by_char
