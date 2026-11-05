# Task: Build the frontend for a Chinese flashcard app (React + Tailwind)

## Goal
Build the UI for a Chinese flashcard app that consumes the existing backend API (documented in the backend README: read it first). Implement ONE main tab now (the "Library" tab) plus authentication, and structure the app so more tabs can be added later with minimal changes.

## Tech
- React (functional components + hooks), TypeScript, Vite
- React Router for navigation
- Tailwind CSS for all styling. Avoid custom CSS files except Tailwind's base import and font setup.
- A single API client module (fetch or axios) that attaches `Authorization: Bearer <token>` automatically
- TanStack Query for data fetching, caching, mutations, and invalidation
- Backend base URL from an `.env` variable (e.g. `VITE_API_BASE_URL`)
- Base all types on the real response shapes in the backend README. Do not invent endpoints or fields. If something needed is missing, list it in your final report instead of mocking silently.
- Suggested folders: `src/api`, `src/auth`, `src/components`, `src/features/library`, `src/routes`, `src/types`.

## Design approach: desktop first
- Design for desktop (≥1024px) first, then adapt downward using Tailwind's `max-lg:` / `max-md:` variants (or an equivalent desktop-first setup).
- Desktop: top navigation bar with tabs, multi-column card/tile grids, centered content with a max width.
- Tablet/mobile must remain fully usable (stacked layout, fewer grid columns, modal near full-width on small screens), but it is not the primary design target.
- Chinese text uses a suitable font stack (e.g. "Noto Sans SC", system CJK fonts) configured in the Tailwind theme.

## Authentication
### Backend routes used
| Route | Use |
| ----- | --- |
| `POST /auth/login` | Body `{ email, password }` → `{ access_token, token_type }`. `401` = bad credentials |
| `GET /auth/me` | Bearer. Returns `{ id, email, created_at }`. Use it to validate a stored token on app load and to show the user's email |

### Requirements
- **Login page** (`/login`): email + password form, submit button with loading state, inline error on `401` ("Invalid email or password") and on network errors. Basic client-side validation (valid email, password not empty).
- On success, store the access token (localStorage is acceptable; isolate it in `src/auth` so it can be swapped later), then redirect to `/library` (or the page the user originally tried to visit).
- **Auth provider/context** exposing `user`, `login()`, `logout()`, and `isLoading`. On app load, if a token exists, call `GET /auth/me` to confirm it is valid before rendering protected pages.
- **Protected routes**: all app routes except `/login` require auth; unauthenticated users are redirected to `/login`. A logged-in user visiting `/login` is redirected to `/library`.
- **Global 401 handling**: if any API call returns `401`, clear the token, clear the query cache, and redirect to `/login`.
- **Logout** control in the app shell (e.g. user email + "Log out" in the top bar). Logout clears the token and the query cache.
- Registration UI is out of scope; accounts are created directly via the API.

## App structure (extensible)
- App shell with a top tab bar driven by a config array, e.g.
  `{ id: 'library', label: 'Library', path: '/library', element: <LibraryTab/> }`
  Adding a tab = adding one entry to this array plus its page component.
- Only the Library tab is built. Do not add placeholder tabs.

## Library tab (all routes require auth)

### 1. Set list page (`/library`)
Backend: `GET /sets` → `[{ id, name, created_at, word_count }]`
- Render each set as a card: set name (primary) and "N words" below it (singular "1 word").
- Clicking a card navigates to `/library/:setId` (UUID).
- Each card has a menu/icons (stop click propagation) for **Rename** and **Delete**.
- A prominent **"New set"** button.
- States: loading (skeletons), empty ("No sets yet" + create button), error with retry.

### 2. Set management
| Action | Route | Notes |
| ------ | ----- | ----- |
| Create set | `POST /sets` body `{ name }` → `201 { id, name, created_at }` | Name 1–100 chars, trim whitespace, validate client-side and show an inline error |
| Rename set | `PATCH /sets/{set_id}` body `{ name }` | Same validation. Available from the set list card and the set detail header. `404` = set no longer exists: show an error and refresh the list |
| Delete set | `DELETE /sets/{set_id}` → `204` | Requires a confirmation dialog that names the set and warns its words will be removed. After deleting from the detail page, navigate back to `/library` |

- Create and rename use a small centered dialog with a single text input (Enter to submit, Escape to cancel, autofocus).
- After each mutation, invalidate the relevant queries (set list, set words) so the UI refreshes. Optimistic updates are optional.
- Set-scoped routes return `404` (not 403) if a set is missing or belongs to someone else. Handle it as "Set not found".

### 3. Set detail page (`/library/:setId`)
Backend: `GET /sets/{set_id}/words?limit=&offset=` → `{ total, items: [{ id, simplified, traditional, pinyin, definitions, added_at }] }`
- Header: back button to `/library`, set name, word total, **Rename** and **Delete set** actions.
- Grid of word tiles, each showing the glyph (`simplified`, large) with `pinyin` smaller directly below. Handle null/missing `pinyin` gracefully.
- The default `limit` is 200 and the max is 1000. Implement "Load more" (or infinite scroll) driven by `total` and `offset`; do not silently truncate large sets.
- An **"Add word"** button opens the add-word dialog (below).
- Clicking a tile opens the word modal.
- States: loading, empty ("This set has no words yet" + Add word button), error, and "Set not found" (404).

### 4. Add word to set
Backend: `POST /sets/{set_id}/words` → `201` word object. Body: `simplified` (required, non-empty), optional `traditional`, `pinyin`, `definitions`. All optional fields are plain strings (`definitions` is a TEXT column, not a list).
- Dialog with a required "Chinese word (simplified)" field and optional Traditional, Pinyin, and Definitions fields.
- Definitions is a multi-line `<textarea>` (3-4 rows). Send it as a single string; omit optional fields that are empty, or send null if the backend accepts it. Do not split it into an array.
- Inline validation (simplified cannot be empty, trim whitespace), submit loading state, and API error display.
- On success, close the dialog (or offer "Add another"), then invalidate the set's words and the set list (word_count).
- Note: the backend also writes explore rows for each character automatically; the frontend does nothing extra.

### 5. Delete word from set
Backend: `DELETE /sets/{set_id}/words/{word_id}` → `204`; `404` if not found in your set.
- Available in the word modal (a "Remove from set" button in the footer or Word Info tab) with a confirmation step.
- On success, close the modal, clear `?word=` from the URL, and invalidate the set's words and the set list.

### 6. Word modal (centered overlay)
- A centered modal/dialog (not a side drawer) with a dimmed backdrop; closes on backdrop click, Escape, and a close button. Trap focus; use proper ARIA dialog roles and return focus to the tile on close.
- Tab strip inside the modal:
    - **"Word Info"** (default open): all available word data from the set's word object (simplified, traditional, pinyin, definitions, added date). `definitions` is free-form text: render it as a string with `whitespace-pre-line` so any line breaks the user entered are preserved. Do not parse or split it. Hide a field's row when its value is null or empty.
  - **One tab per character**, in order, labeled with that character. Data comes from `GET /explore/characters?word=<simplified>` → `{ word, characters: [{ glyph, is_hanzi, character: { id, glyph, pinyin, meaning_en, stroke_count, main_radical_id } | null }] }`.
    - The backend returns unique glyphs in first-appearance order, so repeated characters collapse into one tab. This is expected.
    - Skip entries where `is_hanzi` is false (punctuation, Latin letters, etc.).
    - If `character` is null, show the glyph with "No dictionary data available".
    - Character tab content: large glyph, pinyin (an array; join/display all readings), English meaning, stroke count.
    - Fetch character data lazily when the modal opens, with its own loading/error state; the Word Info tab must work without waiting for it.
    - In character modal, show a Related word drop down. clicking will fetch words using `/explore/words/by-character`
  - Single-character words: show Word Info plus one character tab. Keep it simple and consistent.
- Modal state is reflected in the URL (`/library/:setId?word=<wordId>`) so refresh and the back button work. If the word ID is not in the loaded list, show "Word not found" or fetch more pages as needed.

## Non-goals (for now)
- No registration UI, no study/quiz mode, no other tabs, no editing of individual words (add and delete only).
- No use of  `/explore/words/by-radical`. These are reserved for a future tab.

## Quality bar
- Desktop-first, responsive down to mobile.
- Accessible: semantic elements, keyboard navigable, visible focus rings, labelled form inputs, dialogs with correct ARIA roles, error messages announced (`role="alert"`).
- Consistent loading, error, and empty states via shared components.
- Reusable components (Button, Dialog, ConfirmDialog, TextInput, Tabs, Card, Spinner/Skeleton); no giant files.
- Mutation buttons show a pending state and are disabled while pending to prevent double submits.

## Deliverables
1. Working app runnable with `npm install && npm run dev`, with `.env.example` documenting the backend URL variable.
2. Short README: how to run, how auth works, how to add a new tab.
3. Final report: endpoints used, assumptions made, and any gaps or inconsistencies found in the backend (e.g. CORS issues, missing endpoints, unclear nullability of optional word fields). suggestion for backend route future updates, for ex, changing input from using glyph to id, etc.