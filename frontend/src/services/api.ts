// Thin API client. Only knows about fetch, the base URL, and the Bearer token.
// No business logic lives here — pages and hooks compose these calls.
//
// The base URL is read from import.meta.env.VITE_API_URL (see .env.example).
// The Groq API key never enters this layer; the backend owns it.
//
// Phase 11 adds a 401 side-effect: when an authenticated request returns
// 401 we (a) clear the stored token, (b) dispatch a window event so the
// AuthContext and the ToastBridge can react. Pages themselves never have
// to handle 401 — they just call API functions and read the thrown error.

import type {
  ApiError,
  Conversation,
  ConversationDetail,
  Document,
  QueryResponse,
  TokenResponse,
  User,
} from "@/types/api";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "rag_auth_token";

export const authToken = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class HttpError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "HttpError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = authToken.get();
  if (init.auth !== false && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch (err) {
    // fetch() rejects on DNS failure, offline, CORS rejection. Surface as
    // a TypeError-friendly network error; pages wrap with friendlyError().
    throw err;
  }

  if (res.status === 401 && init.auth !== false) {
    // Single source of truth for "session is dead". Clear the token so
    // ProtectedRoute bounces on next navigation, and let other layers
    // (AuthContext, ToastBridge) react via the window event.
    authToken.clear();
    window.dispatchEvent(new CustomEvent("auth:unauthorized"));
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as ApiError;
      if (body?.detail) detail = body.detail;
    } catch {
      // body wasn't JSON; keep statusText
    }
    throw new HttpError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---------- Auth ----------

export const auth = {
  register: (email: string, password: string) =>
    request<User>("/auth/register", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password }),
    }),
};

// ---------- Documents ----------

export const documents = {
  list: () => request<Document[]>("/documents"),
  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<Document>("/documents/upload", {
      method: "POST",
      body: fd,
    });
  },
  remove: (id: number) =>
    request<{ message: string; id: number }>(`/documents/${id}`, {
      method: "DELETE",
    }),
};

// ---------- Conversations ----------

export const conversations = {
  list: () => request<Conversation[]>("/conversations"),
  get: (id: number) => request<ConversationDetail>(`/conversations/${id}`),
  create: (title?: string) =>
    request<Conversation>("/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  remove: (id: number) =>
    request<{ message: string; id: number }>(`/conversations/${id}`, {
      method: "DELETE",
    }),
};

// ---------- Direct RAG query ----------

export const query = {
  ask: (question: string) =>
    request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};

// ---------- Health ----------

export const health = {
  live: () => request<{ status: string }>("/health/liveness", { auth: false }),
};
