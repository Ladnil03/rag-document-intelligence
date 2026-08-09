# Phase 9 — Frontend Foundation

## Goal

Build the frontend foundation that talks to the existing Phase 1–8 FastAPI
backend: a React + TypeScript + Vite + Tailwind application with a premium
dark-theme three-column layout, reusable components, real authentication
foundation, and environment-driven API access.

This phase is **visual + structural**. The interactive document workflow,
streaming chat, and citation rendering belong to Phase 10.

---

## What Was Implemented

### Frontend Stack
- **React 18** + **TypeScript** (strict mode, path alias `@/`)
- **Vite 5** as the dev server and bundler
- **Tailwind CSS 3** with a custom dark theme (bg / panel / card / border
  / ink / accent tokens) — no other CSS frameworks
- **react-router-dom 6** for routing and protected routes
- **react-markdown** for assistant message rendering (Phase 10 will
  receive Markdown-formatted LLM answers)

No state management library, no UI kit, no test framework — Phase 9 keeps
dependencies minimal and intentional.

### Folder Structure
```text
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── .env.example
├── .gitignore
└── src/
    ├── main.tsx                 # React root + StrictMode
    ├── App.tsx                  # Routes + providers
    ├── index.css                # Tailwind layers + base resets
    ├── vite-env.d.ts            # Vite import.meta.env typing
    ├── types/
    │   └── api.ts               # Mirror of backend Pydantic schemas
    ├── services/
    │   └── api.ts               # Fetch wrapper + endpoint functions
    ├── context/
    │   ├── AuthContext.tsx      # JWT + user state
    │   └── SidebarContext.tsx   # Mobile drawer trigger
    ├── hooks/
    │   ├── useDocuments.ts      # /documents list fetcher
    │   └── useConversations.ts  # /conversations list fetcher
    ├── components/
    │   ├── layout/
    │   │   ├── AppShell.tsx     # 3-column shell + Page wrapper
    │   │   ├── Sidebar.tsx      # Three-section nav (Workspace/Management/System)
    │   │   ├── TopBar.tsx       # Page header + mobile menu button
    │   │   ├── UserFooter.tsx   # Signed-in email + Logout
    │   │   └── ProtectedRoute.tsx
    │   ├── ui/
    │   │   ├── Button.tsx
    │   │   ├── Input.tsx        # Input + Textarea
    │   │   ├── Card.tsx         # Card + SectionTitle
    │   │   ├── Badge.tsx
    │   │   └── EmptyState.tsx
    │   ├── documents/
    │   │   ├── UploadDropzone.tsx
    │   │   └── DocumentList.tsx
    │   └── chat/
    │       ├── Message.tsx      # ChatWindow + ChatMessage (Markdown)
    │       └── ChatInput.tsx
    └── pages/
        ├── AuthPages.tsx        # Login + Register + shared shell
        ├── DashboardPage.tsx
        ├── KnowledgeBasePage.tsx
        ├── DocumentsPage.tsx
        ├── ConversationsPage.tsx
        ├── ChatPage.tsx         # Placeholder UI; Phase 10 wires streams
        └── SettingsPage.tsx
```

### Three-Column Layout

| Column | Width | Purpose |
|---|---|---|
| Left sidebar | `w-60` (fixed on desktop) | RAG Intelligence branding + 3-section nav + signed-in user footer |
| Center | `flex-1 min-w-0` | Page header + main content area (Knowledge Base, Documents, etc.) |
| Right | embedded in pages | AI Assistant chat panel (Chat page) |

On viewports `<md` the sidebar collapses into a slide-out drawer triggered
by a hamburger button on the TopBar. The state is hoisted into a
`SidebarContext` so any page header can open the drawer.

### Reusable Components

| Component | Purpose |
|---|---|
| `Button` | Variants: `primary`, `secondary`, `ghost`, `danger`; sizes `sm/md/lg`; loading spinner |
| `Input`, `Textarea` | Labelled, themed, optional hint/error |
| `Card`, `SectionTitle` | Bordered dark cards with header + optional action slot |
| `Badge` | Coloured tone (`neutral/accent/success/warning/danger`) |
| `EmptyState` | Centred icon + title + description + action |
| `Sidebar` | Three-section nav built from a `NavItem[]` shape |
| `TopBar` | Page title + description + actions; mobile menu slot |
| `AppShell` | The three-column responsive shell |
| `UserFooter` | Email + Logout (calls `useAuth().logout`) |
| `ProtectedRoute` | Redirects to `/login` when no JWT in `localStorage` |
| `UploadDropzone` | Drag/drop + click-to-browse, accepts `.pdf,.docx` (mirrors `backend/config.ALLOWED_EXTENSIONS`) |
| `DocumentList` | Sortable table with status + type filters, client-side search, delete button |
| `ChatMessage`, `ChatWindow` | User bubbles (plain) + assistant bubbles (Markdown via `react-markdown`) |
| `ChatInput` | Auto-growing textarea, Enter-to-send (Shift+Enter newline) |

### Authentication Foundation

Implemented end-to-end against the **existing** backend endpoints
(`/auth/register`, `/auth/login`):

- `services/api.ts` exposes typed `auth.register()` and `auth.login()`.
- `AuthContext` stores the JWT in `localStorage` (key `rag_auth_token`)
  and exposes `login`, `register`, `logout`, `user`, `isAuthenticated`.
- `ProtectedRoute` checks the stored token and redirects to `/login`,
  remembering the requested path in router state.
- `UserFooter` renders the signed-in email and a Logout button that
  clears the token + state.

The Groq API key never enters the frontend. It lives only in
`backend/.env`. The only env var the browser sees is
`VITE_API_URL` (see below).

### Routes

| Path | Component | Auth |
|---|---|---|
| `/login` | `LoginPage` | Public |
| `/register` | `RegisterPage` | Public |
| `/app` | `DashboardPage` | Protected |
| `/app/knowledge` | `KnowledgeBasePage` | Protected |
| `/app/documents` | `DocumentsPage` | Protected |
| `/app/conversations` | `ConversationsPage` | Protected |
| `/app/chat` | `ChatPage` (placeholder) | Protected |
| `/app/settings` | `SettingsPage` | Protected |
| `/` | Redirect → `/app` | — |
| `*` | Redirect → `/app` | — |

### Environment Configuration

`frontend/.env.example`:

```text
# Base URL of the FastAPI backend (no trailing slash).
VITE_API_URL=http://localhost:8000
```

`services/api.ts` reads `import.meta.env.VITE_API_URL ?? "http://localhost:8000"`.
No URL is hardcoded in component code.

---

## Backend APIs Consumed

| Endpoint | Method | Used by |
|---|---|---|
| `/auth/register` | POST | RegisterPage |
| `/auth/login` | POST | LoginPage |
| `/documents` | GET | DashboardPage stats, KnowledgeBasePage list, DocumentsPage |
| `/documents/upload` | POST | KnowledgeBasePage (Phase 9 wires the live endpoint — upload + refresh already functional) |
| `/documents/{id}` | DELETE | KnowledgeBasePage (with confirm dialog) |
| `/conversations` | GET | DashboardPage stats, ConversationsPage |
| `/health/liveness` | GET | DashboardPage "Backend health" badge |

All other endpoints (`/conversations/{id}/messages` SSE, `/query`,
`PATCH /documents/{id}`) are not consumed yet — they will be wired in
Phase 10. No new backend routes were invented.

---

## What Is NOT Implemented Yet (Phase 10+)

- **Streaming chat**: `ChatPage` shows a UI shell with a static placeholder
  assistant reply. SSE consumption of `POST /conversations/{id}/messages`
  arrives in Phase 10.
- **Source citation chips** in assistant messages (the `sources` event).
- **Conversation switching UI**: the list page renders, but clicking a
  conversation does not yet load its messages into the chat panel.
- **Search on the backend**: `/documents` currently has no `q` filter; the
  KnowledgeBase page uses client-side filtering only.
- **Settings editing**: no backend endpoint to update user profile yet.
- **Tests / ESLint configuration**: Phase 9 keeps dependencies minimal.
  Phase 10 should add Vitest + Testing Library when behaviour grows.

---

## Manual Testing Checklist

After `npm install` and starting the backend on `http://localhost:8000`:

1. `npm run dev` — open `http://localhost:5173`
2. You should be redirected to `/login`.
3. Click **Create one**, register a new account, verify the dashboard
   loads at `/app`.
4. Navigate to **Knowledge Base**: drop a PDF in the dropzone; verify
   the row appears in the document table with status `PROCESSING` and
   then `COMPLETED`.
5. Use the Status and Type filters — they hide/show rows.
6. Click **Delete** — confirm the row disappears.
7. Navigate to **Chat**: type a question and press Enter. The UI shows a
   placeholder assistant reply (no streaming yet).
8. Navigate to **Documents** — the same table is visible without upload UI.
9. Navigate to **Conversations** — an empty state is shown until a real
   conversation exists.
10. Navigate to **Settings** — verify the email + API URL render correctly.
11. Click **Log out** in the sidebar footer — you return to `/login`.
12. Resize the browser to mobile width — the sidebar collapses into a
    drawer; the hamburger button opens it.

---

## Files Changed

| File | Action | Description |
|---|---|---|
| `frontend/package.json` | Created | Minimal dependency set |
| `frontend/tsconfig.json` | Created | Strict TypeScript config |
| `frontend/vite.config.ts` | Created | Vite + React + path alias |
| `frontend/tailwind.config.js` | Created | Custom dark theme tokens |
| `frontend/postcss.config.js` | Created | Tailwind + autoprefixer |
| `frontend/index.html` | Created | Vite entry |
| `frontend/.env.example` | Created | Documents `VITE_API_URL` |
| `frontend/.gitignore` | Created | Ignores `node_modules`, `dist`, `.env*` |
| `frontend/src/main.tsx` | Created | React root |
| `frontend/src/App.tsx` | Created | Router + providers |
| `frontend/src/index.css` | Created | Tailwind layers |
| `frontend/src/vite-env.d.ts` | Created | Vite env typing |
| `frontend/src/types/api.ts` | Created | TS types mirroring `backend/schemas.py` |
| `frontend/src/services/api.ts` | Created | Typed fetch client + endpoint wrappers |
| `frontend/src/context/AuthContext.tsx` | Created | JWT state + login/register/logout |
| `frontend/src/context/SidebarContext.tsx` | Created | Mobile drawer trigger |
| `frontend/src/hooks/useDocuments.ts` | Created | Documents fetcher |
| `frontend/src/hooks/useConversations.ts` | Created | Conversations fetcher |
| `frontend/src/components/layout/AppShell.tsx` | Created | Shell + `Page` wrapper |
| `frontend/src/components/layout/Sidebar.tsx` | Created | Three-section nav |
| `frontend/src/components/layout/TopBar.tsx` | Created | Page header + mobile menu |
| `frontend/src/components/layout/UserFooter.tsx` | Created | Signed-in user + logout |
| `frontend/src/components/layout/ProtectedRoute.tsx` | Created | Auth gate |
| `frontend/src/components/ui/Button.tsx` | Created | Variants/sizes/loading |
| `frontend/src/components/ui/Input.tsx` | Created | Input + Textarea |
| `frontend/src/components/ui/Card.tsx` | Created | Card + SectionTitle |
| `frontend/src/components/ui/Badge.tsx` | Created | Toned pill |
| `frontend/src/components/ui/EmptyState.tsx` | Created | Centred placeholder |
| `frontend/src/components/documents/UploadDropzone.tsx` | Created | Drag/drop + click |
| `frontend/src/components/documents/DocumentList.tsx` | Created | Table + filters |
| `frontend/src/components/chat/Message.tsx` | Created | ChatWindow + Markdown message |
| `frontend/src/components/chat/ChatInput.tsx` | Created | Enter-to-send textarea |
| `frontend/src/pages/AuthPages.tsx` | Created | Login + Register |
| `frontend/src/pages/DashboardPage.tsx` | Created | Stats + system status |
| `frontend/src/pages/KnowledgeBasePage.tsx` | Created | Upload + list + filters |
| `frontend/src/pages/DocumentsPage.tsx` | Created | Read-only library |
| `frontend/src/pages/ConversationsPage.tsx` | Created | Read-only history |
| `frontend/src/pages/ChatPage.tsx` | Created | Placeholder chat UI |
| `frontend/src/pages/SettingsPage.tsx` | Created | Account + runtime info |
| `docs/understanding.md` | Modified | Added Phase 9 concept entries |
| `docs/system_architecture.md` | Modified | Added React Frontend + API Client layer |
| `docs/workflow.md` | Modified | Added frontend auth/protected-route/logout workflows |
| `docs/phases/phase9.md` | Created | This document |
