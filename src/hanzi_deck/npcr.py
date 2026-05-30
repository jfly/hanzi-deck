# Utilities for parsing data from the "New Practical Chinese Reader",
# provided by [HSKFlashCards].
#
# Expects a `NPCR_XLS` environment variable to be set pointing to a
# download of [npcr.xls].
#
# [HSKFlashCards]: https://www.hskflashcards.com
# [npcr.xls]: https://www.hskflashcards.com/d/npcr.xls

import os
from pathlib import Path

import pydantic
import xlrd


class Datum(pydantic.BaseModel):
    # https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0010729#pone-0010729-g001
    chapter: int

    number: int = pydantic.Field(alias="A")
    traditional: str = pydantic.Field(alias="B")
    simplified: str = pydantic.Field(alias="C")
    pinyin: str = pydantic.Field(alias="D")
    definition: str = pydantic.Field(alias="E")
    part_of_speech: str = pydantic.Field(alias="F")

    @property
    def variants(self) -> set[str]:
        return {self.traditional, self.simplified}


# Incomplete. Add more as needed.
EXCEL_COLUMN_NAMES = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
]


def load() -> dict[str, Datum]:
    npcr_xls = Path(os.environ["NPCR_XLS"])
    npcr = xlrd.open_workbook(str(npcr_xls))

    data: dict[str, Datum] = {}
    for sheet_idx in range(npcr.nsheets):
        sheet = npcr.sheet_by_index(sheet_idx)
        for rx in range(sheet.nrows):
            row = sheet.row(rx)
            named_data = {
                "chapter": int(sheet.name),
                **dict(zip(EXCEL_COLUMN_NAMES, [r.value for r in row])),
            }
            datum = Datum.model_validate(named_data)
            for variant in datum.variants:
                data[variant] = datum

    return data
