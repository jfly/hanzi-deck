# Utilities for parsing [complete-hsk-vocabulary].
#
# Expects a `COMPLETE_HSK_VOCABULARY` environment variable to be set pointing to [complete.json].
#
# [complete-hsk-vocabulary]: https://github.com/drkameleon/complete-hsk-vocabulary
# [complete.json]: https://github.com/drkameleon/complete-hsk-vocabulary/raw/refs/heads/main/complete.json

import enum
import json
import os
from pathlib import Path

import pydantic


class HskVersion(enum.Enum):
    TWO_2010 = "two-2010"
    THREE_2021 = "three-2021"
    THREE_2026 = "three-2026"


class HskLevel(enum.Enum):
    OLD_1 = "old-1"
    OLD_2 = "old-2"
    OLD_3 = "old-3"
    OLD_4 = "old-4"
    OLD_5 = "old-5"
    OLD_6 = "old-6"

    NEW_1 = "new-1"
    NEW_2 = "new-2"
    NEW_3 = "new-3"
    NEW_4 = "new-4"
    NEW_5 = "new-5"
    NEW_6 = "new-6"
    NEW_7 = "new-7"

    NEWEST_1 = "newest-1"
    NEWEST_2 = "newest-2"
    NEWEST_3 = "newest-3"
    NEWEST_4 = "newest-4"
    NEWEST_5 = "newest-5"
    NEWEST_6 = "newest-6"
    NEWEST_7 = "newest-7"

    def parse(self) -> tuple[HskVersion, int]:
        version_str, level = self.value.split("-")
        # Upstream made some unfortunate naming decisions for the levels, lol.
        version = {
            "old": HskVersion.TWO_2010,
            "new": HskVersion.THREE_2021,
            "newest": HskVersion.THREE_2026,
        }[version_str]
        return version, int(level)


class HskWordData(pydantic.BaseModel):
    # https://github.com/drkameleon/complete-hsk-vocabulary/tree/main#schema
    simplified: str
    levels: list[HskLevel] = pydantic.Field(alias="level")

    def hsk_2026_level(self) -> int | None:
        for level in self.levels:
            version, level_int = level.parse()
            if version == HskVersion.THREE_2026:
                return level_int


def load() -> dict[str, HskWordData]:
    complete_json_file = Path(os.environ["COMPLETE_HSK_VOCABULARY"])

    data_dict: dict[str, HskWordData] = {}
    for raw_data in json.loads(complete_json_file.read_text()):
        data = HskWordData.model_validate(raw_data)
        data_dict[data.simplified] = data

    return data_dict
