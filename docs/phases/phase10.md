# Phase 10 — RAG Workspace

## Goal

Turn the Phase 9 frontend foundation into a fully functional RAG
workspace: real document upload + status polling, persistent conversation
management, and a streaming chat panel with Markdown rendering, source
citations, and follow-up messages that belong to the selected conversation.

The Groq API key remains backend-only; the frontend speaks only HTTP to
FastAPI.

---

## Features Implemented

### Document Knowledge Base
- Drag-and-drop + click-to-browse upload (`UploadDropzone`)
- Live validation mirroring `backend/config.ALLOWED_EXTENSIONS` and
  `MAX_FILE_SIZE` (`.pdf`, `.docx`, 10 MB)
- Optimistic insert of the new row before the next status poll
- Status polling: `useDocuments` polls `GET /documents` every 2s while
  any row is `UPLOADED` or `PROCESSING`. The interval tears down the
  moment every row reaches a terminal state.
- Client-side search by name + status filter + type filter
- Delete with browser `confirm()` + `DELETE /documents/{id}`
- Empty state for zero documents

### Conversations
- List `GET /conversations` on mount
- Create `POST /conversations` from the **+ New chat** button (Chat page
  + Conversations page)
- Delete `DELETE /conversations/{id}` with confirm
- Active id persisted to `localStorage` under `rag_selected_conversation`
- Auto-select the most recent conversation when the chat page loads
- Stale-selection self-heal: if the persisted id is no longer in the
  list, drop it silently on first load

### Chat
- Send a question to the selected conversation
- The user message is appended optimistically; the server persists it
  inside the route before streaming begins
- Real SSE stream against `POST /conversations/{id}/messages`
- `Generating…` indicator while tokens arrive
- Stop button replaces Send while streaming; aborts the underlying fetch
- Markdown rendering via `react-markdown` (headings, lists, bold,
  inline code, code blocks — no raw HTML)
- Source citations appear once the `sources` event fires; `page_number`
  shown only when the backend provided one
- After `done` (or `error`), the conversation is refetched so the local
  state matches the canonical rows persisted by the backend
- Refresh-safe: the selected conversation + its messages are restored
  on browser reload from `localStorage` + `GET /conversations/{id}`

### Dashboard / System
- Dashboard stats read live counts (`Total / Indexed / Failed / Conversations`)
- Health badge pings `GET /health/liveness`

---

## API Endpoints Used

| Method | Endpoint | Used by |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | LoginPage, RegisterPage |
| GET | `/documents` | DashboardPage, KnowledgeBasePage, DocumentsPage (with polling) |
| POST | `/documents/upload` | KnowledgeBasePage (via `useDocuments.upload`) |
| DELETE | `/documents/{id}` | KnowledgeBasePage, DocumentsPage |
| GET | `/conversations` | DashboardPage, ChatPage, ConversationsPage |
| POST | `/conversations` | ChatPage `+ New chat`, ConversationsPage |
| DELETE | `/conversations/{id}` | ChatPage, ConversationsPage |
| GET | `/conversations/{id}` | useConversation (loads messages) |
| POST | `/conversations/{id}/messages` | useConversation.send (SSE stream) |
| GET | `/health/liveness` | DashboardPage |

No new endpoints were invented. The `POST /conversations/{id}/messages`
SSE wire format (`event: token|sources|done|error`) matches the
existing backend exactly (see `conversation_routes._sse`).

---

## Components Created / Updated

| File | Status | Purpose |
|---|---|---|
| `src/services/streaming.ts` | Created | fetch + ReadableStream SSE parser |
| `src/hooks/useConversation.ts` | Created | Loads messages, drives the SSE stream, exposes `pending` |
| `src/hooks/useConversations.ts` | Updated | + create/remove + selection persistence |
| `src/hooks/useDocuments.ts` | Updated | + status polling + upload/remove |
| `src/components/chat/Message.tsx` | Updated | + `PendingAssistantMessage` with sources + streaming indicator |
| `src/components/chat/ChatInput.tsx` | Updated | + Stop button during streaming |
| `src/pages/ChatPage.tsx` | Rewritten | Real RAG chat with conversation rail |
| `src/pages/ConversationsPage.tsx` | Rewritten | Real list/create/delete/select |
| `src/pages/KnowledgeBasePage.tsx` | Updated | Real upload via `useDocuments`, client-side validation |
| `src/pages/DocumentsPage.tsx` | Updated | Delete button + processing badge |
| `docs/understanding.md` | Updated | Phase 10 concept entries |
| `docs/system_architecture.md` | Updated | Frontend layer + Phase 10 status |
| `docs/workflow.md` | Updated | Upload / RAG chat / streaming / sources / conversation workflows |
| `docs/phases/phase10.md` | Created | This document |

---

## Streaming Implementation

`services/streaming.ts` implements a small SSE parser because the
browser's `EventSource` cannot POST or attach a custom `Authorization`
header. The flow:

1. `fetch(POST /conversations/{id}/messages, headers: {Authorization: Bearer, Accept: text/event-stream})`
2. On non-OK response → throw `StreamHttpError(status, detail)` (uses
   the backend's sanitised JSON `detail`)
3. On OK → grab `res.body.getReader()` and read chunks
4. Decode each chunk, split on `\n`, accumulate `event:` and `data:`
   fields until a blank line signals a complete frame
5. Dispatch by event name to typed callbacks
6. `AbortController` lets the UI cancel the request

The `onToken` handler appends to the in-progress assistant bubble.
`onSources` attaches the citation block. `onError` replaces the
streaming content with a friendly message. `onDone` marks the bubble
as no longer streaming and triggers the post-stream refetch.

---

## Source / Citation Implementation

`QuerySource` (mirrors `backend/schemas.QuerySource`) is rendered in a
`Sources` block below the assistant bubble:

```text
Sources
[1] rag-guide.pdf                    Page 3
[2] machine-learning.pdf
```

Only chunks the LLM actually saw are shown — the backend filters
`sources` to the same set used for prompt construction. `page_number`
is rendered only when the backend provides one; it is never invented.

---

## Conversation Implementation

- `useConversations` keeps the list in React state and persists the
  selected id to `localStorage`. Stale ids are cleared silently on first
  load (404 / not-in-list).
- `useConversation(id)` fetches `GET /conversations/{id}` and replaces
  the local message list with the canonical one after every send /
  receive cycle. This guarantees a refresh restores the same state.
- The chat composer is disabled when no conversation is selected.
- The rail collapses to a hamburger drawer on mobile.

---

## Error Handling

| Source | Handling |
|---|---|
| 401 / 403 from any API | `HttpError` propagates to the page; the user is bounced to `/login` next render (the existing `ProtectedRoute` reads `localStorage` token on every navigation) |
| 404 on conversation delete | Treated as success; the row is already gone |
| 413 / 415 / 422 from upload | Surfaced as a friendly red banner under the dropzone |
| 503 / 502 from streaming | `StreamHttpError` message is shown in the assistant bubble |
| In-stream `event: error` | Rendered inside the assistant bubble as red text |
| Network failure mid-stream | Native fetch error bubbles to `pending.error` |
| Browser cancels the stream | `AbortError` drops the placeholder without surfacing an error |

Stack traces, internal paths, and API keys are never shown to the user —
all messages come from the backend's sanitised `detail` strings.

---

## Loading States

- Documents: skeleton text + the existing `Spinner` style ("Loading documents…")
- Conversations: "Loading conversations…"
- Upload: "Uploading & indexing…" under the dropzone + a `processing`
  badge in the page header while any row is in-flight
- Chat: per-message `<ChatWindow>` keeps the previous messages visible;
  the `PendingAssistantMessage` shows a three-dot pulse → growing
  Markdown → "Generating…" line
- Refresh / refetch: `refresh()` is exposed on both list hooks for the
  Conversations and Documents pages

---

## Empty States

- **No documents**: `EmptyState` with title "No documents match your filters"
- **No conversations**: `EmptyState` on the list page + a "No conversation
  selected" state on the chat panel
- **No messages**: centred muted text inside the chat panel
- **Backend unreachable**: Dashboard "Backend health: Unreachable"

All empty states match the Phase 9 dark theme.

---

## Responsive Design

- Desktop (>= md): three-column shell — sidebar + centre page + (on Chat
  page) conversation rail + chat
- Tablet: same shell with narrower conversation rail
- Mobile (< md): the conversation rail becomes a hamburger drawer inside
  the chat page; the app sidebar is the existing Phase 9 drawer

---

## Known Limitations

- No optimistic UI for conversation **create** — the page shows a tiny
  button-loading state via `Button.loading`. The new conversation is
  added to the list as soon as the POST resolves.
- `useConversation` refetches the conversation after `done`, so the
  streamed assistant message is briefly visible locally and then
  replaced with the canonical row. There is no perceptible flicker,
  but it is the deliberate design.
- Streaming cancellation drops the optimistic user message that the
  backend has already persisted; the next refetch brings it back. This
  matches the backend behaviour where the user message is created
  before the LLM starts.
- No retry/backoff on streaming failure — the user clicks Send again.
- The SSE parser assumes the backend always sends valid UTF-8 and JSON
  payloads. If the backend ever sends non-JSON `data:` lines, they are
  dropped silently.
- `QuerySource.similarity` is exposed by the backend but not displayed
  in the UI — it is metadata, not a quality signal, and showing it would
  imply a precision the platform doesn't promise.

---

## Manual Testing Checklist

Pre-reqs:
- Backend running on `http://localhost:8000`
- `frontend/.env.local` with `VITE_API_URL=http://localhost:8000`
- `npm run dev` → open `http://localhost:5173`

1. **Auth** — register or log in; verify redirect to `/app`.
2. **Upload** — on `/app/knowledge`, drop a `.pdf` or `.docx` (≤10 MB).
   The row appears with status `UPLOADED` (or `PROCESSING`) and the
   "N processing" badge in the page header flips on. Within seconds it
   transitions to `COMPLETED` and the badge disappears.
3. **Upload validation** — try a 12 MB file or an `.exe`; the UI shows
   a red banner without hitting the server.
4. **Document list** — change the status filter to `Failed`; nothing
   shows unless a real failure exists. Reset to `All`.
5. **Delete** — click `Delete` on any row; confirm; the row disappears.
6. **Conversations** — open `/app/conversations`; click `+ New chat`;
   the new row appears at the top.
7. **Chat** — open `/app/chat`; the conversation rail shows on the
   left; select a conversation (or auto-select the most recent); type
   "What is RAG?" → press Enter; the assistant bubble grows token by
   token; sources appear below.
8. **Stop** — during streaming, click `Stop`; the bubble is removed.
9. **Follow-up** — ask a second question; verify both questions and
   answers belong to the same conversation. Reload the page — the
   conversation + both Q/A pairs are still there.
10. **Markdown** — ask a question that returns a numbered list or a
    code snippet; verify the rendered output.
11. **Sources** — verify the `Sources` block lists real filenames (not
    invented) and `Page N` only when the backend provided it.
12. **Isolation** — open a second browser profile (or log out + register
    a second user) and verify the first user cannot see the second
    user's documents or conversations. (Backend enforces this; the
    frontend just displays what the API returns.)
13. **Errors** — point `VITE_API_URL` at an unreachable host, send a
    message — the assistant bubble shows a friendly error.
14. **Mobile** — resize the window below `md`; the conversation rail
    becomes a hamburger drawer; the chat remains usable.
15. **Logout** — click `Logout` in the sidebar; the chat panel returns
    to `/login` on next navigation.

---

## Files Changed

| File | Action | Description |
|---|---|---|
| `frontend/src/services/streaming.ts` | Created | SSE fetch + ReadableStream parser |
| `frontend/src/hooks/useConversation.ts` | Created | Active conversation lifecycle |
| `frontend/src/hooks/useConversations.ts` | Updated | + create/remove + selection persistence |
| `frontend/src/hooks/useDocuments.ts` | Updated | + status polling + upload/remove |
| `frontend/src/components/chat/Message.tsx` | Updated | + `PendingAssistantMessage` with sources + streaming indicator |
| `frontend/src/components/chat/ChatInput.tsx` | Updated | + Stop button while sending |
| `frontend/src/pages/ChatPage.tsx` | Rewritten | Real RAG chat |
| `frontend/src/pages/ConversationsPage.tsx` | Rewritten | Real list/create/delete/select |
| `frontend/src/pages/KnowledgeBasePage.tsx` | Updated | Real upload + delete + status badge |
| `frontend/src/pages/DocumentsPage.tsx` | Updated | Delete + processing badge |
| `docs/understanding.md` | Updated | Phase 10 concept entries |
| `docs/system_architecture.md` | Updated | Frontend layer + Phase 10 status |
| `docs/workflow.md` | Updated | Upload / RAG chat / streaming / sources / conversation workflows |
| `docs/phases/phase10.md` | Created | This document |
