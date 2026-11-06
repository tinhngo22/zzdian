
## CC-CEDICT → `words`


| Dataset field                   | App table.column                          | Transformation                          |
| ------------------------------- | ----------------------------------------- | --------------------------------------- |
| Traditional (1st token on line) | `words.traditional`                       | none                                    |
| Simplified (2nd token on line)  | `words.simplified`                        | none                                    |
| Pinyin in `[...]`               | `words.pinyin_numbered`                   | stored as-is, case kept (`Zhong1 guo2`) |
| Pinyin in `[...]`               | `words.pinyin`                            | `numbered_to_marked` → `Zhōng guó`      |
| Pinyin in `[...]`               | `words.pinyin_plain`                      | `numbered_to_plain` → `zhong guo`       |
| Definitions between `/.../`     | `words.definitions` (JSONB)               | split on `/` into an array of strings   |
| *(not in dataset)*              | `words.hsk_level`, `words.frequency_rank` | empty for now, filled in Phase 7        |
| *(not in dataset)*              | `words.is_custom`, `words.created_by`     | defaults: `false` and `NULL`            |




## Unihan → `characters` and `radicals`


| Dataset field                            | App table.column             | Transformation                                                       |
| ---------------------------------------- | ---------------------------- | -------------------------------------------------------------------- |
| `kRSUnicode`                             | `characters.main_radical_id` | take the number before the dot (`149'.7` → `149`)                    |
| `kTotalStrokes`                          | `characters.stroke_count`    | first number if several (`10 9` → `10`)                              |
| `kMandarin`                              | `characters.pinyin`          | split on spaces into an array, used only if Make Me a Hanzi has none |
| `kDefinition`                            | `characters.meaning_en`      | used only if Make Me a Hanzi has none                                |
| `kMandarin` (of the radical's glyph)     | `radicals.pinyin`            | first reading                                                        |
| `kTotalStrokes` (of the radical's glyph) | `radicals.stroke_count`      | first number                                                         |
| Code point (`U+597D`)                    | `characters.id`              | hex to int (`22909`)                                                 |




## Make Me a Hanzi → `characters` and `character_components`


| Dataset field                               | App table.column                    | Transformation                                                         |
| ------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------- |
| `character`                                 | `characters.glyph`                  | none                                                                   |
| `character`                                 | `characters.id`                     | `ord(glyph)` (the Unicode code point)                                  |
| `pinyin` (list)                             | `characters.pinyin`                 | none, preferred over Unihan                                            |
| `definition`                                | `characters.meaning_en`             | none, preferred over Unihan                                            |
| `decomposition`                             | `character_components.component_id` | drop layout symbols (`⿰`, `⿱`, ...) and `？`, then `ord()` of each part |
| `decomposition` (order of parts)            | `character_components.position`     | index of the part, starting at 0                                       |
| `etymology.semantic` / `etymology.phonetic` | `character_components.role`         | matching part → `semantic` / `phonetic`, otherwise `component`         |
| `radical`                                   | *(not used)*                        | main radical comes from Unihan instead                                 |
| `matches`, strokes data                     | *(not used)*                        | reserved for stroke-order work in Phase 7                              |




## Unicode built-in data (`unicodedata`) → `radicals`


| Source                                  | App table.column      | Transformation                       |
| --------------------------------------- | --------------------- | ------------------------------------ |
| Code point in U+2F00 to U+2FD5          | `radicals.id`         | `code_point - 0x2F00 + 1` (1 to 214) |
| Character in the Kangxi block           | `radicals.glyph`      | `NFKC` normalize (⼥ → 女)             |
| Character name (`KANGXI RADICAL WOMAN`) | `radicals.meaning_en` | remove prefix, title-case (`Woman`)  |




## Derived tables (no dataset field of their own)


| App table.column               | Built from                                          |
| ------------------------------ | --------------------------------------------------- |
| `word_characters.word_id`      | `words.id`                                          |
| `word_characters.position`     | index of each character in `words.simplified`       |
| `word_characters.character_id` | `ord(char)` of each character in `words.simplified` |




## Source priority when two datasets overlap


| App column              | 1st choice                   | Fallback             |
| ----------------------- | ---------------------------- | -------------------- |
| `characters.pinyin`     | Make Me a Hanzi `pinyin`     | Unihan `kMandarin`   |
| `characters.meaning_en` | Make Me a Hanzi `definition` | Unihan `kDefinition` |

