// useConversation — owns the messages for ONE active conversation.
//
// Why this hook:
// - Phase 10 turns the chat panel into a real RAG conversation. We need a
//   single place that (1) loads messages from GET /conversations/{id} on
//   mount or when the id changes, (2) drives the SSE stream against
//   POST /conversations/{id}/messages, and (3) surfaces sources, errors,
//   and the in-progress "Generating..." indicator.
//
// We keep the in-progress assistant message in local React state because
// it grows token-by-token. Once the stream emits `done` we refetch the
// conversation so the local state is replaced with the canonical row
// persisted by the backend (which guarantees the final assistant text
// matches what was actually written to PostgreSQL).

import { useCallback, useEffect, useRef, useState } from "react";

import { conversations } from "@/services/api";
import { streamMessage, StreamHttpError } from "@/services/streaming";
import type { ConversationDetail, Message, QuerySource } from "@/types/api";

interface PendingAssistant {
  // Local-only fields. `id` is negative so it never collides with real
  // server-issued ids. Sources are attached when the `sources` event fires.
  id: number;
  conversation_id: number;
  role: "assistant";
  content: string;
  sources: QuerySource[];
  hasRelevantContext: boolean;
  streaming: boolean;
  error: string | null;
}

interface UseConversationResult {
  conversation: ConversationDetail | null;
  messages: Message[];
  pending: PendingAssistant | null;
  loading: boolean;
  sending: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  send: (text: string) => Promise<void>;
  cancel: () => void;
}

let pendingIdSeq = -1;

export const useConversation = (
  conversationId: number | null,
): UseConversationResult => {
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [pending, setPending] = useState<PendingAssistant | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    if (conversationId == null) {
      setConversation(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const detail = await conversations.get(conversationId);
      setConversation(detail);
    } catch (err) {
      setError(messageFor(err, "Failed to load conversation."));
      setConversation(null);
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  // Reload when the active conversation changes. The dependency is the
  // primitive id (not the whole object) so a same-id refresh from the
  // caller still works.
  useEffect(() => {
    if (conversationId == null) {
      setConversation(null);
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    conversations
      .get(conversationId)
      .then((detail) => {
        if (active) setConversation(detail);
      })
      .catch((err) => {
        if (active) {
          setError(messageFor(err, "Failed to load conversation."));
          setConversation(null);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [conversationId]);

  // Cancel any in-flight stream on unmount or conversation switch.
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, [conversationId]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const send = useCallback(
    async (text: string) => {
      if (conversationId == null || sending) return;
      const content = text.trim();
      if (!content) return;

      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setSending(true);
      setError(null);

      // Optimistic: append the user message locally so the input clears
      // immediately and the chat scrolls. The server persists it inside
      // the route before streaming starts.
      const optimisticUser: Message = {
        id: pendingIdSeq--,
        conversation_id: conversationId,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };
      setConversation((prev) =>
        prev
          ? { ...prev, messages: [...prev.messages, optimisticUser] }
          : prev,
      );

      const placeholder: PendingAssistant = {
        id: pendingIdSeq--,
        conversation_id: conversationId,
        role: "assistant",
        content: "",
        sources: [],
        hasRelevantContext: true,
        streaming: true,
        error: null,
      };
      setPending(placeholder);

      try {
        await streamMessage(conversationId, content, ctrl.signal, {
          onToken: (delta) => {
            setPending((prev) =>
              prev
                ? { ...prev, content: prev.content + delta }
                : prev,
            );
          },
          onSources: (sources, hasRelevant) => {
            setPending((prev) =>
              prev
                ? {
                    ...prev,
                    sources,
                    hasRelevantContext: hasRelevant,
                  }
                : prev,
            );
          },
          onError: (msg) => {
            setPending((prev) =>
              prev ? { ...prev, error: msg, streaming: false } : prev,
            );
          },
          onDone: () => {
            setPending((prev) =>
              prev ? { ...prev, streaming: false } : prev,
            );
          },
        });
      } catch (err) {
        if ((err as DOMException)?.name === "AbortError") {
          // User cancelled — drop the placeholder without surfacing an error.
          setPending(null);
        } else {
          const msg = messageFor(err, "Failed to send message.");
          setPending((prev) =>
            prev ? { ...prev, error: msg, streaming: false } : prev,
          );
          setError(msg);
        }
      } finally {
        setSending(false);
        abortRef.current = null;
        // Always refetch after a send so the optimistic user row is
        // replaced by the server's persisted one (with its real id) and
        // the assistant message becomes canonical. If the stream errored
        // mid-way the backend may have still persisted the user message,
        // which we want reflected in the conversation list timestamp.
        try {
          const detail = await conversations.get(conversationId);
          setConversation(detail);
        } catch {
          /* error already surfaced above */
        }
        // Clear the streaming placeholder — the canonical assistant row
        // is now in `conversation.messages`.
        setPending(null);
      }
    },
    [conversationId, sending],
  );

  const messages = conversation?.messages ?? [];

  return {
    conversation,
    messages,
    pending,
    loading,
    sending,
    error,
    refresh,
    send,
    cancel,
  };
};

const messageFor = (err: unknown, fallback: string): string => {
  if (err instanceof StreamHttpError) return err.message;
  if (err instanceof Error) return err.message;
  return fallback;
};
