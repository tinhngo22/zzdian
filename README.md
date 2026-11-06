
## API routes

Auth: routes marked **Bearer** need `Authorization: Bearer <access_token>` from `POST /auth/login`. Set-scoped routes return **404** (not 403) if the set is missing or belongs to someone else.


### Health

| Method | Path | Input | Returns | Permission |
| ------ | ---- | ----- | ------- | ---------- |
| `GET` | `/health` | — | `{ "status": "ok" }` | public |
| `GET` | `/health/db` | — | `{ "db": 1 }` | public |


### Auth (`/auth`)

| Method | Path | Input | Returns | Permission |
| ------ | ---- | ----- | ------- | ---------- |
| `POST` | `/auth/login` | JSON body: `email`, `password` | `{ "access_token": "...", "token_type": "bearer" }` · `401` on bad credentials | public |
| `GET` | `/auth/me` | — | `{ "id", "email", "created_at" }` · `401` if token invalid or user gone | Bearer |


### Dictionary

Cached with `Cache-Control: public, max-age=3600`. `character_id` is the Unicode code point (e.g. 好 → `22909`).

| Method | Path | Input | Returns | Permission |
| ------ | ---- | ----- | ------- | ---------- |
| `GET` | `/characters/{character_id}` | path: `character_id` (int) | Character detail (below) · `404` if missing | public |
| `GET` | `/characters/glyph/{glyph}` | path: `glyph` (exactly one character) | Same as above · `400` if not one char · `404` if missing | public |

Character detail shape:

```json
{
  "id": 22909,
  "glyph": "好",
  "pinyin": ["hǎo"],
  "meaning_en": "...",
  "stroke_count": 6,
  "main_radical": { "id", "glyph", "pinyin", "meaning_en", "stroke_count" } | null,
  "components": [
    { "position", "role", "id", "glyph", "pinyin", "meaning_en" }
  ]
}
```


### Sets (`/sets`)

All routes require Bearer. Sets and words are scoped to the authenticated user.

| Method | Path | Input | Returns | Permission |
| ------ | ---- | ----- | ------- | ---------- |
| `POST` | `/sets` | JSON body: `name` (1–100 chars, trimmed) | `201` `{ "id", "name", "created_at" }` | Bearer |
| `GET` | `/sets` | — | `[{ "id", "name", "created_at", "word_count" }, ...]` | Bearer |
| `PATCH` | `/sets/{set_id}` | path: `set_id` (UUID); JSON body: `name` | `{ "id", "name", "created_at" }` · `404` if not found / not yours | Bearer |
| `DELETE` | `/sets/{set_id}` | path: `set_id` (UUID) | `204` empty · `404` if not found / not yours | Bearer |
| `GET` | `/sets/{set_id}/words` | path: `set_id`; query: `limit` (1–1000, default 200), `offset` (≥0, default 0) | `{ "total": N, "items": [{ "id", "simplified", "traditional", "pinyin", "definitions", "added_at" }, ...] }` · `404` if set not yours | Bearer |
| `POST` | `/sets/{set_id}/words` | path: `set_id`; JSON body: `simplified` (required, non-empty), optional `traditional`, `pinyin`, `definitions` | `201` `{ "id", "simplified", "traditional", "pinyin", "definitions", "added_at" }` · also writes `explore` rows for each character · `404` if set not yours | Bearer |
| `POST` | `/sets/{set_id}/words/bulk` | path: `set_id`; JSON body: `words`, 1–500 objects shaped like the single-word body | `201` `{ "items": [<word>, ...] }` in the given order · all or nothing (`422` if any word is invalid) · `404` if set not yours | Bearer |
| `DELETE` | `/sets/{set_id}/words/{word_id}` | path: `set_id`, `word_id` (UUIDs) | `204` empty · `404` if set/word not found in your set | Bearer |


### Explore (`/explore`)

| Method | Path | Input | Returns | Permission |
| ------ | ---- | ----- | ------- | ---------- |
| `GET` | `/explore/characters` | query: `character_id` repeated, 1–50 values, each 0–0x10FFFF (e.g. `?character_id=20320&character_id=22909` for 你好) | `{ "character_ids": [...], "characters": [{ "id", "glyph", "is_hanzi", "character": { "id", "glyph", "pinyin", "meaning_en", "stroke_count", "main_radical_id", "components": [{ "position", "role", "id", "glyph", "pinyin", "meaning_en" }] } \| null }] }` — unique ids in first-appearance order; `components` is empty for characters that do not decompose | public |
| `GET` | `/explore/words/by-character` | query: `character_id` (int, 0–0x10FFFF, Unicode code point) | `{ "character_id": N, "words": [{ "id", "simplified", "traditional", "pinyin", "definitions", "added_at" }, ...] }` — your saved words containing that character (distinct `simplified`) | Bearer |
| `GET` | `/explore/words/by-component` | query: `component_id` (int, 0–0x10FFFF, a `characters.id`) | `{ "component_id": N, "words": [...] }` (same word shape) — your saved words containing a character built from that component, or the component itself (distinct `simplified`) | Bearer |

All ids are `characters.id`, i.e. the Unicode code point (好 → `22909`). CORS allows the origins in `CORS_ORIGINS` (default `http://localhost:5173,http://127.0.0.1:5173`).


