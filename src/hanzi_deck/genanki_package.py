import contextlib
from pathlib import Path
from typing import Generator

import genanki
from genanki.package import tempfile

from .notes import HanziNote, build_hanzi_notes

# A little bit of extra data just in case other folks are also
# using the same mechanism for computing GUIDs.
GUID_SALT = "jfly/hanzi-deck"


def create_model() -> genanki.Model:
    return genanki.Model(
        1555250809,
        "Hanzi",
        fields=[{"name": field_name} for field_name in HanziNote.model_fields.keys()],
        templates=[
            {
                "name": template.name,
                "qfmt": template.question,
                "afmt": template.answer,
            }
            for template in HanziNote.templates()
        ],
        css=HanziNote.css(),
    )


def create_note(
    model: genanki.Model,
    hanzi_note: HanziNote,
) -> genanki.Note:
    return genanki.Note(
        model=model,
        fields=[
            getattr(hanzi_note, field_name)
            for field_name in HanziNote.model_fields.keys()
        ],
        guid=genanki.util.guid_for(GUID_SALT, hanzi_note.character),
    )


@contextlib.contextmanager
def generate_package() -> Generator[genanki.Package]:
    my_deck = genanki.Deck(1229323897, "Homemade Hanzi")

    model = create_model()

    hanzi_notes = build_hanzi_notes()
    for hanzi_note in hanzi_notes:
        my_deck.add_note(
            create_note(
                model=model,
                hanzi_note=hanzi_note,
            )
        )

    package = genanki.Package(my_deck)

    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)

        # We make a copy of every media file because it may have a timestamp
        # outside of the range of timestamps acceptable to zip (for example,
        # files in the nix store are timestamped 1970, but zip files cannot
        # support files after 1980).
        media_files: list[Path] = []
        for file in HanziNote.media():
            destination = tempdir / file.name
            file.copy(destination)
            media_files.append(destination)

        package.media_files = media_files
        yield package
