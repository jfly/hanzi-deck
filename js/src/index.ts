import HanziWriter from "hanzi-writer";

for (let quizEl of document.querySelectorAll<HTMLElement>(".hanzi-quiz")) {
  let character = quizEl.dataset.character;
  if (!character) {
    console.error(
      "No character specified for .hanzi-quiz element, skipping",
      quizEl,
    );
    continue;
  }

  let graphicsJson = quizEl.dataset.graphics_json;
  if (!graphicsJson) {
    console.error(
      "No character data present for .hanzi-quiz element, skipping",
      quizEl,
    );
    continue;
  }
  let graphics = JSON.parse(graphicsJson);

  let writer = HanziWriter.create(quizEl, character, {
    width: 300,
    height: 300,
    showCharacter: false,
    showOutline: true,
    showHintAfterMisses: 1,
    highlightOnComplete: false,
    padding: 5,
    charDataLoader: function () {
      return graphics;
    },
  });
  writer.quiz();
}
