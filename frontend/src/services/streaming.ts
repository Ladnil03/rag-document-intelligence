// Server-Sent Events streaming client. We cannot use the browser's
// EventSource because (a) it only supports GET and (b) it cannot attach a
// custom Authorization header. The backend uses POST + Bearer JWT +
// media-type text/event-stream, so we hand-roll a streaming parser on top
// of fetch + ReadableStream.
//
// Wire format from backend (conversation_routes._sse):
//   event: token\ndata: {"text":"..."}\n\n
//   event: sources\ndata: {"sources":[...],"has_relevant_context":bool}\n\n
//   event: done\ndata: {}\n\n
//   event: error\ndata: {"message":"..."}\n\n
//
// All four event names are documented in docs/understanding.md (Phase 6).

import { authToken } from "@/services/api";
import type { QuerySource } from "@/types/api";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface StreamHandlers {
  onToken?: (text: string) => void;
  onSources?: (sources: QuerySource[], hasRelevantContext: boolean) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

export class StreamHttpError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// POSTs the message and yields parsed SSE events until the stream ends
// (done) or fails (error / network / HTTP).
export async function streamMessage(
  conversationId: number,
  content: string,
  signal: AbortSignal,
  handlers: StreamHandlers,
): Promise<void> {
  const token = authToken.get();
  if (!token) {
    throw new StreamHttpError(401, "You are signed out.");
  }

  const res = await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ content }),
    signal,
  });

  if (!res.ok || !res.body) {
    // Try to parse a JSON error body. The FastAPI default error responses
    // are JSON; SSE errors come AFTER headers so we already have them here.
    let detail = res.statusText || "Request failed.";
    try {
      const body = (await res.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      /* body wasn't JSON */
    }
    throw new StreamHttpError(res.status, detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");

  // The parser holds an in-progress event block. SSE frames are separated
  // by a blank line ("\n\n"); multi-line `data:` fields are concatenated
  // with "\n" per the spec.
  let buffer = "";
  let eventName = "";
  let dataLines: string[] = [];

  const flush = () => {
    if (!eventName && dataLines.length === 0) return;
    const event = eventName || "message";
    const data = dataLines.join("\n");
    eventName = "";
    dataLines = [];
    if (!data) return;
    handleEvent(event, data, handlers);
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Split into lines and process complete frames.
      let idx: number;
      while ((idx = buffer.indexOf("\n")) !== -1) {
        let line = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 1);
        // Drop a trailing CR (SSE lines end with \r\n per spec).
        if (line.endsWith("\r")) line = line.slice(0, -1);

        if (line === "") {
          flush();
          continue;
        }
        if (line.startsWith(":")) {
          // Comment line — ignore.
          continue;
        }
        const colon = line.indexOf(":");
        const field = colon === -1 ? line : line.slice(0, colon);
        let valuePart = colon === -1 ? "" : line.slice(colon + 1);
        if (valuePart.startsWith(" ")) valuePart = valuePart.slice(1);

        if (field === "event") eventName = valuePart;
        else if (field === "data") dataLines.push(valuePart);
        // `id:` and `retry:` are not used by the backend; skip.
      }
    }
    // Final partial frame, if any.
    if (buffer.length) {
      let line = buffer;
      if (line.endsWith("\r")) line = line.slice(0, -1);
      if (line.startsWith(":")) {
        /* comment */
      } else {
        const colon = line.indexOf(":");
        const field = colon === -1 ? line : line.slice(0, colon);
        let valuePart = colon === -1 ? "" : line.slice(colon + 1);
        if (valuePart.startsWith(" ")) valuePart = valuePart.slice(1);
        if (field === "event") eventName = valuePart;
        else if (field === "data") dataLines.push(valuePart);
      }
      buffer = "";
      flush();
    }
  } catch (err) {
    if ((err as DOMException)?.name === "AbortError") {
      // Caller cancelled; surface as a clean abort, not a network error.
      throw err;
    }
    throw err;
  }
}

function handleEvent(event: string, data: string, handlers: StreamHandlers): void {
  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    // Non-JSON payload — log and drop; backend should always send JSON.
    return;
  }
  switch (event) {
    case "token": {
      const obj = parsed as { text?: unknown };
      if (typeof obj.text === "string") handlers.onToken?.(obj.text);
      break;
    }
    case "sources": {
      const obj = parsed as {
        sources?: QuerySource[];
        has_relevant_context?: boolean;
      };
      handlers.onSources?.(obj.sources ?? [], Boolean(obj.has_relevant_context));
      break;
    }
    case "done":
      handlers.onDone?.();
      break;
    case "error": {
      const obj = parsed as { message?: unknown };
      const msg = typeof obj.message === "string" ? obj.message : "Assistant response failed.";
      handlers.onError?.(msg);
      break;
    }
    default:
      break;
  }
}
