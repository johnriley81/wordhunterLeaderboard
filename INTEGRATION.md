# Wordhunter game client ↔ API alignment (handoff)

This document is the **integration contract** between the **Wordhunter** game client and this leaderboard service. The **game repo behavior described here is source of truth** unless you intentionally keep legacy behavior on the server.

## Relationship: game changes ↔ API changes

| Game behavior | Why the API must care |
|---------------|------------------------|
| Word scoring uses tile weights × word length (see [§1 Scoring](#1-scoring-canonical)) | `validate_score_payload` recomputes scores with the same formula as `wordhunter_cert` or submissions fail when validation is on. |
| Daily puzzle id = **local** day index since **2026-05-19**; puzzle row = that id **mod pool size** | Path `/leaderboard/<puzzle>` must use that index for DB partition. |
| `POST` includes `scoreValidation` | `leaderboard_ops.validate_score_payload` must match the client payload: full starting letter pool plus ordered `wordsPlayed`, with **trophy** present in the run. |
| **API Gateway** still wraps JSON in a string `body`; **Flask** returns parsed JSON | The client should branch on `typeof data.body` (see [§4](#4-get--post-response-shape)). |

---

## 1. Scoring (canonical)

**Game implementation:** `wordTotal = letterSum * length`, where `letterSum` is the sum of per-tile weights (`qu` is one tile), and `length` is the **tile** count along the path (revisits count).

| Location | Role |
|----------|------|
| Game | `js/board-logic.js` — `getLiveWordScoreBreakdownFromLabels` |
| Parity tooling | `tools/wordhunter_cert` — `word_breakdown` / `score_word_as_tiles` |

**This repo**

- `wordhunter_scoring.py` — `iter_tiles()` (left-to-right, `qu` grouped) then `letterSum * length`.
- **`tile_weights.json`** — bundled default map (`a`–`z`, `qu`). **Replace with an export from `wordhunter_cert` if any value differs** (defaults are US-Scrabble-style + `qu`: 11 for convenience).
- **`WORDHUNTER_TILE_WEIGHTS_JSON`** — optional absolute path to override the bundled file (Lambda or local).

There is **no** legacy length-only fallback; validation requires valid weights for every tile in every submitted word.

---

## 2. Puzzle id (canonical)

| Constant | Value |
|----------|--------|
| `PUZZLE_ROTATION_EPOCH` | **2026-05-19** (local calendar; client defines timezone boundary) |
| Path `<puzzle>` | **Day index** since that epoch (epoch day = **0**). |
| Template / pool row | **`puzzle % pool_size`** — implemented as `puzzle_calendar.template_row_index`. |

Python helpers live in **`puzzle_calendar.py`** (`day_index_since_rotation`, `template_row_index`). The client should send the same integer it uses for the daily board / `puzzles.txt` row.

**Source of truth (game repo):** `js/puzzle-calendar.js` — `PUZZLE_ROTATION_EPOCH = new Date(2026, 4, 19)` (May 19, 2026).

---

## 3. `POST` body

**Always required:** valid JSON, `player` (non-empty, no profanity), `score`, `trophy`, and **`scoreValidation`** — object with:

- `gameLetters`: flat letter pool at puzzle start (row-major starting grid + padded `next_letters`)
- `wordsPlayed`: ordered list of submitted words (lowercase)

**trophy** must appear in `wordsPlayed`. The server recomputes score by consuming tiles from `gameLetters` in order; submitted `score` must match.

Duplicate submissions with the same `(puzzle, player, score, trophy)` return `This record already exists.` without inserting again.

---

## 4. `GET` / `POST` response shape

| Surface | Response |
|---------|----------|
| **Flask** (`wordhunter_leaderboard.py`) | **Plain JSON** in the HTTP body: `GET` → array of rows; `POST` → `{ "message", "top_10" }`. |
| **Lambda** (`handler.py` + API Gateway proxy) | API Gateway envelope: `{ "statusCode", "headers", "body" }` where **`body` is a JSON string**. Headers include **`Content-Type: application/json`**. |

**Client helper**

```javascript
const data = await response.json();
const payload = typeof data.body === "string" ? JSON.parse(data.body) : data;
```

**GET success:** JSON array, up to 10 rows, each `[player, score, trophy]`.

**POST success (200):** `{ "message": string, "top_10": [ ... ] }` for business outcomes (reject name, invalid trace, duplicate, success). **400** for bad JSON or missing required fields. **429** for rate limit. **500** for DB connection errors.

---

## 5. CORS and origin

Game is served at **https://wordhunter.io**. Successful Flask responses set `Access-Control-Allow-Origin` accordingly; Lambda uses the same header in `CORS_HEADERS`.

---

## 6. Security / ops

- Prefer **parameterized SQL** for `player`, `trophy`, and numeric fields (current code uses string interpolation).
- **Secrets Manager** secret id should follow environment (not only `test/wordhunterLeaderboard` in code).
- **Rate limit:** one request per IP per minute (`rate_limit.py`).

---

## 7. Checklist for API repo maintainers

- [ ] `tile_weights.json` matches `wordhunter_cert` / board logic.
- [ ] `PUZZLE_ROTATION_EPOCH` matches `js/puzzle-calendar.js`.
- [ ] `validate_score_payload` matches live game rules.
- [ ] Flask and Lambda share **`leaderboard_ops`**, **`wordhunter_scoring`**, **`puzzle_calendar`**, **`rate_limit`**.
- [ ] Deployment packages **`tile_weights.json`** next to the scoring module (and optional custom weights path via env).

---

## 8. Game repo changes (context for API authors)

- Always emit **`scoreValidation`** on leaderboard `POST`.
- Use **one** puzzle id: local day index since **2026-05-19**, for leaderboard URL and puzzle row.
- Parse responses with the Gateway vs Flask helper above.
- Point **`leaderboardLink`** at production when shipping.

---

## Appendix: modules in this repo

| File | Role |
|------|------|
| `handler.py` | Lambda entry; Secrets Manager; JSON string `body` + CORS |
| `wordhunter_leaderboard.py` | Flask; plain JSON responses |
| `leaderboard_ops.py` | `validate_score_payload`, `validate_player_name`, `try_insert_leaderboard` |
| `wordhunter_scoring.py` | Tile segmentation + `letterSum * length` |
| `puzzle_calendar.py` | Rotation epoch + `template_row_index` |
| `rate_limit.py` | Per-IP request throttling |
| `tile_weights.json` | Default tile weights (sync from cert if needed) |
