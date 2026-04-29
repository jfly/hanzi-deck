import contextlib
import os
import tempfile
from pathlib import Path
from typing import Generator

import anki.collection
import anki.models
import anki.notes
import genanki.util

from hanzi_deck.notes import HanziNote, build_hanzi_notes


def create_anki_note(
    model: anki.models.NotetypeDict,
    col: anki.collection.Collection,
    hanzi_note: HanziNote,
) -> anki.notes.Note:
    note = col.new_note(model)
    note.guid = genanki.util.guid_for(hanzi_note.character)
    for field_name in HanziNote.model_fields.keys():
        note[field_name] = getattr(hanzi_note, field_name)

    return note


def create_anki_model(col: anki.collection.Collection) -> anki.models.NotetypeDict:
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
    for field_name in HanziNote.model_fields.keys():
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


@contextlib.contextmanager
def temp_collection() -> Generator[anki.collection.Collection, None, None]:
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        col = anki.collection.Collection(str(tempdir / "temp.anki2"))

        model = create_anki_model(col)

        deck_id = col.decks.id(name="Homemade Hanzi")
        assert deck_id is not None

        notes: list[anki.notes.Note] = []
        hanzi_notes = build_hanzi_notes()
        for hanzi_note in hanzi_notes:
            notes.append(
                create_anki_note(
                    col=col,
                    model=model,
                    hanzi_note=hanzi_note,
                )
            )

        col.add_notes([anki.collection.AddNoteRequest(note, deck_id) for note in notes])
        print("Note", notes[0].id, notes[0].guid)  # <<<
        print("Note", notes[1].id, notes[1].guid)  # <<<

        yield col
