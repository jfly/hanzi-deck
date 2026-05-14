import HanziWriter from "hanzi-writer";
import * as cbor2 from "cbor2";

async function activateHanziWriters() {
  for (let quizEl of document.querySelectorAll<HTMLElement>(".hanzi-quiz")) {
    let character = quizEl.dataset.character;
    if (!character) {
      console.warn(
        "No character specified for .hanzi-quiz element, skipping",
        quizEl,
      );
      continue;
    }

    let graphicsCborZlibBase64 = quizEl.dataset.graphics_cbor_zlib_base64;
    if (!graphicsCborZlibBase64) {
      console.warn(
        "No character data present for .hanzi-quiz element (expected a data-graphics_cbor_zlib_base64 attribute). Skipping",
        quizEl,
      );
      continue;
    }

    let graphics: any;
    try {
      const graphicsCborZlib: Uint8Array<ArrayBuffer> = Uint8Array.fromBase64(
        graphicsCborZlibBase64,
      );
      const graphicsCbor = await decompress(graphicsCborZlib);
      graphics = cbor2.decode(graphicsCbor);
    } catch (e) {
      console.error(e);
      console.error("Raw graphics_cbor_zlib_base64", graphicsCborZlibBase64);
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
}

// Source - https://stackoverflow.com/a/76332760
// Posted by Alex
// Retrieved 2026-05-13, License - CC BY-SA 4.0
function mergeUint8Arrays(...arrays: Uint8Array[]): Uint8Array {
  const totalSize = arrays.reduce((acc, e) => acc + e.length, 0);
  const merged = new Uint8Array(totalSize);

  arrays.forEach((array, i, arrays) => {
    const offset = arrays.slice(0, i).reduce((acc, e) => acc + e.length, 0);
    merged.set(array, offset);
  });

  return merged;
}

async function decompress(
  compressed: Uint8Array<ArrayBuffer>,
): Promise<Uint8Array<ArrayBufferLike>> {
  const stream = new DecompressionStream("deflate-raw");
  const writer = stream.writable.getWriter();
  writer.write(compressed);
  writer.close();

  const decompressedChunks: Uint8Array[] = [];
  for await (const chunk of stream.readable) {
    decompressedChunks.push(chunk);
  }

  return mergeUint8Arrays(...decompressedChunks);
}

export { activateHanziWriters };
