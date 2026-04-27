import random
from pathlib import Path

from flask import Flask

from . import lib
from .enter_for_process_lifetime import enter_for_process_lifetime

hanzi_notes = enter_for_process_lifetime(lib.build_notes())

app = Flask(__name__, static_url_path="", static_folder=hanzi_notes._col.media.dir())


@app.route("/")
def show_card():
    note = random.choice(hanzi_notes.notes)
    card = random.choice(note.cards())
    return f"""
        <h1>Question</h1>
        <div class="card">
            {card.question()}
        </div>

        <h1>Answer</h1>
        <div class="card">
            {card.answer()}
        </div>
    """


def main():
    app.run(
        debug=True,
        extra_files=list(Path("templates/").glob("**")),
    )


if __name__ == "__main__":
    main()
