# Utilities for parsing the [Unihan database].
#
# Expects a `UNIHAN` environment variable to be set pointing to an
# extracted version of [Unihan.zip].
#
# [Unihan database]: https://www.unicode.org/reports/tr38/
# [Unihan.zip]: https://www.unicode.org/Public/UCD/latest/ucd/

import os
import re
from pathlib import Path
from typing import Generator

import pydantic

Codepoint = int

UNIHAN_DIR = Path(os.environ["UNIHAN"])

CODEPOINT_RE = re.compile(r"U\+([A-Z0-9]+)")


def parse_codepoint_str(codepoint_str: str) -> Codepoint:
    """
    Unihan represents codepoints in string form like U+3401

    Example:

    >>> hex(parse_codepoint_str("U+3401"))
    '0x3401'
    """
    match = CODEPOINT_RE.fullmatch(codepoint_str)
    assert match is not None
    return int(match.group(1), 16)


def parse_kSemanticVariant(kSemanticVariant: str) -> Generator[Codepoint]:
    # https://www.unicode.org/reports/tr38/#kSemanticVariant
    for variant in kSemanticVariant.split():
        codepoint_str, *_additional_data = variant.split("<")
        yield parse_codepoint_str(codepoint_str)


def parse_kZVariant(kSemanticVariant: str) -> Generator[Codepoint]:
    # https://www.unicode.org/reports/tr38/#kZVariant
    # Looks like a simplified version of `kSemanticVariant`.
    # For our purposes, they're identical.
    for variant in kSemanticVariant.split():
        codepoint_str, *_additional_data = variant.split("<")
        yield parse_codepoint_str(codepoint_str)


class HanGrapheme(pydantic.BaseModel):
    codepoint: int
    properties: dict[str, str] = pydantic.Field(default_factory=dict)

    @property
    def character(self) -> str:
        return chr(self.codepoint)

    def definition(self) -> str | None:
        return self.properties.get("kDefinition")

    def pinyin(self) -> str | None:
        # This actually has some structure [0]. TODO: parse it!
        # [0]: https://www.unicode.org/reports/tr38/#kHanyuPinyin
        return self.properties.get("kHanyuPinyin")

    def compatibility_variant(self) -> Codepoint | None:
        # https://www.unicode.org/reports/tr38/index.html#kCompatibilityVariant
        variant_codepoint_str = self.properties.get("kCompatibilityVariant")
        return (
            None
            if variant_codepoint_str is None
            else parse_codepoint_str(variant_codepoint_str)
        )

    def simplified_variants(self) -> list[Codepoint]:
        # https://www.unicode.org/reports/tr38/#kSimplifiedVariant
        return [
            parse_codepoint_str(cp)
            for cp in self.properties.get("kSimplifiedVariant", "").split()
        ]

    def traditional_variants(self) -> list[Codepoint]:
        # https://www.unicode.org/reports/tr38/#kTraditionalVariant
        return [
            parse_codepoint_str(cp)
            for cp in self.properties.get("kTraditionalVariant", "").split()
        ]

    def semantic_variants(self) -> list[Codepoint]:
        # https://www.unicode.org/reports/tr38/#kSemanticVariant
        return list(parse_kSemanticVariant(self.properties.get("kSemanticVariant", "")))

    def specialized_semantic_variants(self) -> list[Codepoint]:
        # https://www.unicode.org/reports/tr38/#kSpecializedSemanticVariant
        # > The syntax is the same as for the kSemanticVariant property.
        return list(
            parse_kSemanticVariant(
                self.properties.get("kSpecializedSemanticVariant", "")
            )
        )

    def spoofing_variant(self) -> list[Codepoint]:
        # https://www.unicode.org/reports/tr38/#kSpoofingVariant
        return [
            parse_codepoint_str(cp)
            for cp in self.properties.get("kSpoofingVariant", "").split()
        ]

    def z_variants(self) -> list[Codepoint]:
        # https://www.unicode.org/reports/tr38/#kZVariant
        return list(parse_kZVariant(self.properties.get("kZVariant", "")))


class Unihan:
    def __init__(self, unihan_dir: Path | None = None):
        unihan_dir = Path(os.environ["UNIHAN"])

        self.grapheme_by_codepoint: dict[Codepoint, HanGrapheme] = {}

        # https://www.unicode.org/reports/tr38/#Unihan.zip
        # > One approach to parsing data for certain properties
        # > is to concatenate all of the `Unihan*.txt` files together
        for file in unihan_dir.glob("Unihan*.txt"):
            for line in file.read_text().splitlines():
                # > Blank lines may be ignored.
                # > Lines beginning with # are comment lines used
                # to provide the header and footer
                if line == "" or line.startswith("#"):
                    continue

                # > Each of the remaining lines is one entry, with three, tab-separated fields:
                # > - the Unicode Scalar Value,
                # > - the property name,
                # > - and the value for the property for the given Unicode Scalar Value
                codepoint_str, property_name, property_value = line.split("\t")
                codepoint = parse_codepoint_str(codepoint_str)

                if codepoint not in self.grapheme_by_codepoint:
                    self.grapheme_by_codepoint[codepoint] = HanGrapheme(
                        codepoint=codepoint
                    )

                self.grapheme_by_codepoint[codepoint].properties[property_name] = (
                    property_value
                )
