import HanziWriter from "hanzi-writer";

declare global {
  interface Window {
    activateHanziWriters: any;
  }
}

window.activateHanziWriters = function () {
  for (let quizEl of document.querySelectorAll<HTMLElement>(".hanzi-quiz")) {
    let character = quizEl.dataset.character;
    if (!character) {
      console.warn(
        "No character specified for .hanzi-quiz element, skipping",
        quizEl,
      );
      continue;
    }

    let graphicsJson = quizEl.dataset.graphics_json;
    if (!graphicsJson) {
      console.warn(
        "No character data present for .hanzi-quiz element, skipping",
        quizEl,
      );
      continue;
    }

    let graphics: any;
    try {
      graphics = JSON.parse(graphicsJson);
    } catch (e) {
      console.error(e);
      console.error("Full JSON", graphicsJson);
      continue;
    }

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
};
