import contextlib
import tempfile
from pathlib import Path
from typing import Generator

import anki.collection
import anki.models
import anki.notes
import genanki.util

from .notes import HanziNote, build_hanzi_notes


def create_note(
    model: anki.models.NotetypeDict,
    col: anki.collection.Collection,
    hanzi_note: HanziNote,
) -> anki.notes.Note:
    note = col.new_note(model)
    note.guid = genanki.util.guid_for(hanzi_note.character)
    for field_name in HanziNote.model_fields.keys():
        note[field_name] = getattr(hanzi_note, field_name)

    return note


def create_model(col: anki.collection.Collection) -> anki.models.NotetypeDict:
    model = col.models.new("Hanzi")
    model["css"] = HanziNote.css()

    # Add fields.
    for field_name in HanziNote.model_fields.keys():
        field = col.models.new_field(field_name)
        col.models.add_field(model, field)

    # Add templates.
    for template in HanziNote.templates():
        tmpl = col.models.new_template(template.name)
        tmpl["qfmt"] = template.question
        tmpl["afmt"] = template.answer
        col.models.add_template(model, tmpl)

    # Add media.
    for file in HanziNote.media():
        col.media.add_file(str(file))

    col.models.add(model)

    return model


@contextlib.contextmanager
def temp_collection() -> Generator[anki.collection.Collection]:
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        col = anki.collection.Collection(str(tempdir / "temp.anki2"))

        model = create_model(col)

        deck_id = col.decks.id(name="Homemade Hanzi")
        assert deck_id is not None

        notes: list[anki.notes.Note] = []
        hanzi_notes = build_hanzi_notes()
        for hanzi_note in hanzi_notes:
            notes.append(
                create_note(
                    col=col,
                    model=model,
                    hanzi_note=hanzi_note,
                )
            )

        col.add_notes([anki.collection.AddNoteRequest(note, deck_id) for note in notes])
        yield col
