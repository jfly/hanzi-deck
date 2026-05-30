# hanzi-deck

## Build deck

```console
nix build github:jfly/hanzi-deck
```

## Hacking

See [HACKING.md](./HACKING.md).

## License

The code in this repository is licensed under the [MIT license](./LICENSE),
however, it incorporates data from various sources:

- [Unihan](https://www.unicode.org/reports/tr38/): grapheme data.
  [Unicode License v3](https://github.com/unicode-org/unihan-database/blob/main/LICENSE).
- [SUBTLEX-CH](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0010729): frequency data. Creative Commons Attribution License.
- [Make Me a Hanzi](https://github.com/skishore/makemeahanzi): stroke data.
  [Complicated licensing](https://github.com/skishore/makemeahanzi/blob/master/COPYING).
- [Hanzi Writer](https://github.com/chanind/hanzi-writer): javascript widget
  for practicing strokes. [MIT License](https://github.com/chanind/hanzi-writer#license).
- [Complete HSK Vocabulary](https://github.com/drkameleon/complete-hsk-vocabulary): for mapping
  characters/"words" to HSK level. [MIT License](https://github.com/drkameleon/complete-hsk-vocabulary/blob/main/LICENSE).
- [HSKFlashCards](https://www.hskflashcards.com/): alternate source of
  definitions that are more "practical" than those in the Unihan database. [GPL
  License](https://www.hskflashcards.com/downloads/#licensing-and-permission),
  but it's unclear how this is compatible with the "All rights reserved" clause
  at the start of the "New Practical Chinese Reader".
