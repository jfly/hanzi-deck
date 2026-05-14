// Various workarounds for the old version of Chromium embedded in the
// old version of qt6 embedded in the Anki MacOS dmg.

// `Uint8Array.fromBase64` added in Chrome 140 (Release date: 2025-09-02)
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Uint8Array/fromBase64#browser_compatibility
import "core-js/proposals/array-buffer-base64";

// `[Symbol.asyncIterator]` added in Chrome 124 (Release date: 2024-04-16)
// https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream#browser_compatibility
if (
  typeof globalThis.ReadableStream?.prototype[Symbol.asyncIterator] !==
  "function"
) {
  // Polyfill copied from https://github.com/DefinitelyTyped/DefinitelyTyped/discussions/65542#discussioncomment-6071004
  ReadableStream.prototype[Symbol.asyncIterator] = async function* () {
    const reader = this.getReader();
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) return;
        yield value;
      }
    } finally {
      reader.releaseLock();
    }
  };
}
