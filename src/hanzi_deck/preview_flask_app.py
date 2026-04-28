import random

import typer
from flask import Flask

from . import lib
from .enter_for_process_lifetime import enter_for_process_lifetime

app = typer.Typer()


hanzi_notes = enter_for_process_lifetime(lib.build_notes())

app = Flask(__name__, static_url_path="", static_folder=hanzi_notes._col.media.dir())


@app.route("/")
def root():
    note = random.choice(hanzi_notes.notes)
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
