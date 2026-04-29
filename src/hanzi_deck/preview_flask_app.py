import random

from flask import Flask

from . import anki_collection
from .enter_for_process_lifetime import enter_for_process_lifetime

col = enter_for_process_lifetime(anki_collection.temp_collection())

app = Flask(__name__, static_url_path="", static_folder=col.media.dir())


@app.route("/")
def root():
    note_id = random.choice(col.find_notes(""))
    note = col.get_note(note_id)
    card = random.choice(note.cards())

    return f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
            </head>
            <body>
                <h1>Question</h1>
                <div class="card">
                    {card.question()}
                </div>

                <h1>Answer</h1>
                <div class="card">
                    {card.answer()}
                </div>
            </body>
        </html>
    """
