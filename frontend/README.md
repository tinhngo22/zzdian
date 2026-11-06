# Hanzi frontend

React + TypeScript + Vite, styled with Tailwind CSS, data via TanStack Query, routing via React Router.
It consumes the FastAPI backend documented in [`data/README.md`](../data/README.md#api-routes).

## Run

```bash
# 1. backend on :8000 (from backend/)
uvicorn app.main:app --port 8000

# 2. frontend on :5173
cd frontend
cp .env.example .env      # optional, defaults are the same
npm install
npm run dev
```

Open http://localhost:5173. There is no sign-up screen: create an account with
`python -m scripts.create_user you@example.com` (run from `backend/`), then log in.

| Variable | Default | Meaning |
| -------- | ------- | ------- |
| `VITE_API_BASE_URL` | `/api` | Prefix the browser uses for API calls. |
| `VITE_API_PROXY_TARGET` | `http://localhost:8000` | Where the dev server forwards `/api/*`. |

By default the browser calls Vite on the same origin and Vite proxies `/api/*` to FastAPI
(stripping the `/api` prefix). To call the backend directly instead, set
`VITE_API_BASE_URL=http://localhost:8000`; the backend allows this origin through its
`CORS_ORIGINS` setting (default `http://localhost:5173,http://127.0.0.1:5173`).

Other scripts: `npm run build` (type-check + production build), `npm run typecheck`.

## How auth works

- `src/auth/tokenStorage.ts` is the only code that touches storage (localStorage today).
- `src/api/client.ts` adds `Authorization: Bearer <token>` to every request.
- `AuthProvider` (`src/auth`) validates a stored token with `GET /auth/me` on load and exposes
  `user`, `isLoading`, `login()`, and `logout()` through `useAuth()`.
- `RequireAuth` guards every route except `/login` and redirects back to the original page after login.
- Any `401` from an authenticated request clears the token and the query cache and sends the
  user to `/login`. Logging out does the same.

## Adding a tab

1. Build the page component under `src/features/<name>/` (it can define its own nested `<Routes>`,
   like `LibraryTab`).
2. Add one entry to `APP_TABS` in `src/routes/tabs.tsx`:

   ```tsx
   { id: "study", label: "Study", path: "/study", element: <StudyTab /> },
   ```

The top bar and the router are both driven by that array, and the tab automatically owns
every path under `path/*`. The first entry is the default landing page.

## Layout

```
src/
  api/          fetch client, endpoint functions, query keys, QueryClient
  auth/         token storage, AuthProvider/useAuth, RequireAuth
  components/   Button, Dialog, ConfirmDialog, TextInput/TextArea, Tabs, Card, Spinner/Skeleton, States, AppShell
  features/library/  Library tab: set list, set detail, dialogs, word modal, data hooks
  routes/       tab config, route table, login page
  types/        API response types
```

Styling is desktop-first: base classes target ≥1024px, and `max-lg:` / `max-md:` / `max-sm:`
variants adapt it for smaller screens. Chinese text uses the `font-cjk` family defined in
`src/index.css` (Noto Sans SC with system CJK fallbacks).
