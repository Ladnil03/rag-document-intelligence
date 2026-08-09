# Phase 11 — Production-Quality Frontend

## Goal

Turn the Phase 10 RAG workspace into a production-quality web app:
premium polish, accessibility, error UX, loading UX, notifications,
security audit, and a real production Docker image — all without
modifying backend logic.

---

## UI / UX Improvements

- **Toasts** for success / error feedback (upload, delete, auth,
  creation events) via a single global `ToastProvider`. Polite screen-reader
  announcements, auto-dismiss, manual dismiss.
- **Skeleton loaders** for the document list, conversation list, and chat
  messages. The layout doesn't jump when data arrives.
- **Empty states** rewritten for all four pages with consistent dark
  styling, descriptive copy, and contextual action buttons.
- **Error Boundary** wrapping `<App />`: any render-time exception shows
  a friendly recovery screen instead of a blank page.
- **Friendly error mapping** (`utils/errors.ts`) turns `HttpError` /
  `StreamHttpError` status codes into short user-meaningful copy.
- **401 auto-logout**: any authenticated request that returns 401 clears
  the token, dispatches a window event, and the `AuthProvider`,
  `ProtectedRoute`, and `ToastProvider` all react in parallel.
- **Logout** navigates to `/login` immediately and clears the persisted
  active conversation id.
- **Status badges** now show both a colour tone and a glyph + label
  ("✓ Indexed", "… Processing", "• Uploaded", "! Failed") so colour-blind
  users and screen readers can tell status apart.
- **Source cards** render as bordered pill-rows with a numeric badge,
  filename, and `Page N` (only when the backend supplies it).
- **Chat** got timestamps on every message, a "Copy" button on assistant
  replies, and smart auto-scroll that stops yanking the viewport when
  the user has scrolled up.

## Responsive Design

- Desktop (≥ md): three-column shell — fixed sidebar + scrollable
  page + (on `/app/chat`) conversation rail + chat surface.
- Tablet: same shell, narrower conversation rail, smaller padding.
- Mobile (< md):
  - App sidebar collapses into a drawer (Phase 9 behaviour).
  - Chat page conversation rail collapses into a top-toggle drawer.
  - Tables wrap in `overflow-x-auto` to prevent horizontal page scroll.
  - TopBar and Page paddings shrink; action buttons wrap to a new row.
- Reduced-motion users (`prefers-reduced-motion: reduce`) get a CSS
  override that collapses all animation/transition durations to ~0.

## Accessibility

- Global `:focus-visible` accent ring in `index.css` — invisible to mouse
  users, visible to keyboard users.
- All interactive icons carry `aria-label`s (mobile menu, delete row,
  dismiss toast, copy response).
- Tables use `<th scope="col">`; lists use `<ul>/<li>`; landmarks use
  `<header role="banner">`, `<aside aria-label="...">`, `<main>`.
- The chat log is `role="log"` + `aria-live="polite"` + `aria-relevant="additions"`
  so screen readers announce new assistant content.
- Status never conveyed by colour alone — every badge has both a label
  and a glyph.
- The upload dropzone has `role="button"`, `aria-label`, and
  `aria-disabled`; it accepts Enter / Space.
- The toast viewport is `aria-live="polite"` so announcements don't
  interrupt the user's current task.
- Filter `<select>`s in Knowledge Base have explicit `aria-label`s.

## Error Handling

| Source | Handling |
|---|---|
| 401 from any API | `HttpError` → API client clears the token + dispatches `auth:unauthorized` → AuthProvider, ProtectedRoute, and toast bridge react in parallel |
| 403 | friendlyError → "You don't have access to this resource." |
| 404 | friendlyError → "We couldn't find what you were looking for." |
| 413 / 415 | friendlyError → size / type message; the dropzone also blocks bad files client-side |
| 422 | friendlyError → "The request was invalid." |
| 429 | friendlyError → "Too many requests. Please slow down." |
| 5xx | friendlyError → "Our server hit a problem. Please try again." |
| Network failure (TypeError) | friendlyError → "Can't reach the server. Check your connection." |
| Stream HTTP failure | `StreamHttpError` mapped by friendlyError |
| In-stream `event: error` | Rendered inside the assistant bubble |
| Render-time exception | Caught by `ErrorBoundary` → recovery screen |
| Pre-stream abort (user clicked Stop) | Drop the placeholder silently |

No raw exception text or stack traces are shown to the user.

## Loading States

- Documents: skeleton table with header row + 4 body rows + a pulsing
  upload indicator.
- Conversations: skeleton list with 4 placeholder rows.
- Chat messages: three placeholder bars sized like the largest
  expected bubble.
- Upload: pulsing dot + "Uploading & indexing…" line under the dropzone.
- Page-level processing badge in the header.
- Dashboard stats: appear immediately from cached hook state; no extra
  loading spinner needed.

## Chat UX

- Markdown via `react-markdown` rendered through a custom `.md` CSS
  class for full theme control (no extra `typography` plugin needed).
- Code blocks render in a bordered `bg-bg-panel` container with monospace.
- Inline code uses a small `bg-bg-panel` chip.
- Copy button on assistant text (`navigator.clipboard.writeText`) with a
  1.5s "Copied" confirmation.
- "Generating…" indicator appears below the bubble only when there is
  already some content, so the first frame isn't a misleading "still
  typing" pill on an empty bubble.
- Smart auto-scroll: tracks the user's scroll position and only jumps
  to bottom when they are within 32px of the bottom.
- Stream cancel: the Stop button aborts the fetch and the pending
  placeholder is dropped without surfacing an error.

## Security

- The Groq API key, JWT signing key, and DB credentials never enter the
  frontend. `services/api.ts` only reads `VITE_API_URL`; no other
  variables prefixed `VITE_` exist.
- `frontend/.env.example` documents the only environment variable the
  browser sees; `.gitignore` excludes `.env.local`.
- The login / register / chat pages never store anything more sensitive
  than the JWT itself. The JWT is in `localStorage` under a single key
  (`rag_auth_token`); a stolen token is the only attack surface.
- The 401 path clears the token and surfaces a toast — a token that
  fails server-side never lingers client-side.
- Stack traces are logged to the console only in dev builds.
- Verified: no occurrences of `GROQ_API_KEY`, `JWT_SECRET`, or
  hardcoded passwords anywhere under `frontend/src/`.

## Environment Configuration

- `frontend/.env.example` is updated to document `VITE_API_URL` with
  two scenarios:
  - Local dev (`vite` on `:5173`, FastAPI on `:8000`): `VITE_API_URL=http://localhost:8000`
  - Production docker stack (nginx on `:80`, FastAPI proxied at `/api`):
    `VITE_API_URL=/api`
- The value is baked into the bundle at build time by Vite.
- No other env vars are read in the browser.

## Production Build

```text
npm run build
   → tsc -b (typecheck)
   → vite build (tree-shake, minify, hashed chunks)
   → dist/index.html + dist/assets/index-*.{js,css}
```

Verified: 338 kB JS / 21 kB CSS (105 kB / 4.9 kB gzip). No build errors.

## Docker

- New `frontend/Dockerfile` (multi-stage):
  - Stage 1: `node:20-alpine` — `npm ci` then `npm run build` with
    `VITE_API_URL=/api`.
  - Stage 2: `nginx:alpine` — serves `dist/` on port 80.
- New `frontend/nginx.conf`:
  - Long-cache `/assets/*` (Vite-emitted hash filenames).
  - No-cache `/index.html` (deploys are picked up immediately).
  - SPA fallback: unknown paths serve `index.html` so React Router
    takes over on refresh.
  - Reverse-proxy `/api/*` → `http://web:8000/` (FastAPI service).
  - SSE-friendly: `proxy_buffering off`, `proxy_read_timeout 1h`.
- New `frontend/.dockerignore` excludes `node_modules`, `dist`,
  `.env*`.
- `docker-compose.yml` updated:
  - New `frontend` service depends on `web`.
  - `web` no longer exposes `8000` publicly — it's only reachable from
    the docker network via nginx.
  - `ALLOWED_ORIGINS` still keeps the dev ports for local
    non-docker runs.
- The browser now talks to a single origin (`http://localhost:8080`),
  eliminating the dev-only CORS dance in production.

## Files Changed

| File | Action | Description |
|---|---|---|
| `frontend/src/context/ToastContext.tsx` | Created | Global toast provider + viewport + 401 bridge |
| `frontend/src/utils/errors.ts` | Created | `friendlyError(err, fallback)` HTTP mapper |
| `frontend/src/components/ui/Skeleton.tsx` | Created | Skeleton primitive |
| `frontend/src/components/layout/ErrorBoundary.tsx` | Created | Render-error recovery |
| `frontend/src/services/api.ts` | Updated | 401 → clear token + dispatch event |
| `frontend/src/context/AuthContext.tsx` | Updated | Listens to `auth:unauthorized` |
| `frontend/src/components/layout/ProtectedRoute.tsx` | Updated | Listens to `auth:unauthorized`, redirects |
| `frontend/src/components/layout/UserFooter.tsx` | Updated | Logout navigates to `/login` + clears selection |
| `frontend/src/components/layout/AppShell.tsx` | Updated | Cleanup, mobile drawer aria |
| `frontend/src/components/layout/Sidebar.tsx` | Updated | aria-label on landmarks |
| `frontend/src/components/layout/TopBar.tsx` | Updated | Banner landmark + mobile menu aria-label |
| `frontend/src/components/ui/Button.tsx` | Updated | `aria-busy`, default `type="button"` |
| `frontend/src/components/chat/Message.tsx` | Updated | Timestamps, smart auto-scroll, copy, error icon |
| `frontend/src/components/chat/ChatInput.tsx` | Updated | `aria-label`, focus restoration |
| `frontend/src/components/documents/DocumentList.tsx` | Updated | Status glyph + label, overflow scroll, aria-labels |
| `frontend/src/components/documents/UploadDropzone.tsx` | Updated | aria-label, aria-disabled |
| `frontend/src/pages/AuthPages.tsx` | Updated | `friendlyError`, success toast, role="alert" |
| `frontend/src/pages/ChatPage.tsx` | Updated | Skeletons, toasts, better empty states, `aria-current` |
| `frontend/src/pages/ConversationsPage.tsx` | Updated | Skeletons, toasts, better empty states |
| `frontend/src/pages/DocumentsPage.tsx` | Updated | Skeletons, toasts |
| `frontend/src/pages/KnowledgeBasePage.tsx` | Updated | Skeletons, toasts, `role="alert"` errors |
| `frontend/src/pages/DashboardPage.tsx` | Updated | `useNavigate` instead of `window.location` |
| `frontend/src/pages/SettingsPage.tsx` | Updated | Removed fake "User ID: 0", build-mode line |
| `frontend/src/index.css` | Updated | Focus ring, reduced-motion, `.md` Markdown styles |
| `frontend/src/App.tsx` | Updated | Wraps in ToastProvider + ErrorBoundary + bridge |
| `frontend/.env.example` | Updated | Documents local vs docker `VITE_API_URL` |
| `frontend/Dockerfile` | Created | Multi-stage Node → nginx |
| `frontend/.dockerignore` | Created | Excludes `node_modules`, `dist`, `.env*` |
| `frontend/nginx.conf` | Created | Static SPA + `/api/*` reverse proxy |
| `docker-compose.yml` | Updated | New `frontend` service, internal `web` port |
| `docs/understanding.md` | Updated | Phase 11 concept entries |
| `docs/system_architecture.md` | Updated | nginx in the diagram, status line, Frontend Layer |
| `docs/workflow.md` | Updated | Toast / 401 / ErrorBoundary / Production Build / Docker workflows |
| `docs/decisions.md` | Updated | Phase 11 ADRs |
| `README.md` | Updated | Phase 11 references and frontend service in docker-compose |

---

## Known Limitations

- No tests are added (Vitest, Testing Library, Playwright). The
  production-quality bar is "manual QA + typecheck + build" — Phase 12
  should add a test suite.
- The `User.id` shown in the Settings page is always `0` because
  `/auth/login` does not return the user row and no `/auth/me` endpoint
  exists yet. We deliberately hide the field rather than show a
  misleading `0`.
- The chat composer is disabled when no conversation is selected; the
  UX is "click a chat or + New chat to start typing" which some users
  find slightly slower than always-enabled. We accept that trade-off to
  keep the URL/state contract clean.
- The 401 path is "fire-and-forget" — three listeners react to the
  event independently. There is no test harness that verifies all three
  fire; if one of them is removed in the future, the toast would just
  not appear.
- The Docker image is ~50 MB (nginx:alpine + dist). Smaller base images
  (e.g. `nginx:alpine-slim`) exist but aren't worth the compatibility
  risk for a Phase 11 deliverable.

---

## Manual Testing Checklist

Pre-reqs:
- Backend running on `http://localhost:8000` OR the full docker stack
  running on `http://localhost:8080`.

Local dev path:
1. `cd frontend && npm install`
2. `cp .env.example .env.local` (default points at `localhost:8000`)
3. `npm run build` — confirm no errors, check `dist/`.
4. `npm run dev` → `http://localhost:5173` → redirected to `/login`.

UI / polish:
5. Sign in → "Welcome back." toast appears top-right; auto-dismisses.
6. Wrong password → friendly red banner under the form (no raw
   exception text).
7. Resize below `md` → hamburger menu appears; sidebar slides in.
8. Settings page → no "User ID: 0" line; API URL row is monospace.
9. Focus the email input, press Tab → focus ring visible on password.
10. Toggle `prefers-reduced-motion` (DevTools → Rendering) →
    animations collapse.

Knowledge Base:
11. Drop a `.pdf` → row appears with `UPLOADED` / `PROCESSING` /
    `COMPLETED` badges cycling; the "N processing" badge in the header
    tracks count; "Uploaded …" toast fires on success.
12. Drop a `.txt` → red banner under the dropzone (client-side gate),
    no server round-trip.
13. Drop a 12 MB file → red banner, no upload.
14. Filter by Status → `Indexed`; rows update; empty state if none.
15. Delete a row → confirm dialog → toast confirms.

Conversations:
16. Open `/app/conversations` → skeleton rows briefly; then list.
17. Create new chat → toast "New chat started"; row appears at top.
18. Delete a chat → toast "Chat deleted".

Chat:
19. Open `/app/chat` → most recent conversation auto-selected.
20. Send a question → streaming bubble grows token by token.
21. While streaming, scroll up → bubble does NOT yank you back.
22. Scroll back to bottom → next token auto-scrolls.
23. Copy response → "Copied" confirmation appears.
24. Click Stop → bubble disappears; the user message (already persisted
    by the backend) reappears after the next refetch.
25. Reload the page → conversation + messages restored.
26. Force a 401 (e.g. clear `localStorage.rag_auth_token` in DevTools
    then trigger an action) → "Your session expired" toast + redirect
    to `/login`.

Error boundary:
27. In DevTools, throw an error inside a component (e.g. via React
    DevTools) → recovery screen appears with "Try again" / "Reload
    page". Console shows the stack (dev only).

Docker:
28. `docker-compose up --build` → three containers up; `http://localhost:8080`
    serves the SPA.
29. Browser network tab: every API call is to `/api/...` (single
    origin). Login, upload, chat all work.
30. `docker-compose down` → volumes persist.
