import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

import { Badge } from "@/components/ui/Badge";
import type { Message, QuerySource } from "@/types/api";
import { cn } from "@/utils/ui";

interface ChatMessageProps {
  message: Message;
}

// Single persisted message bubble.
export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === "user";
  const time = formatClock(message.created_at);
  return (
    <div
      className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}
    >
      <div
        className={cn(
          "group max-w-[85%] rounded-2xl border px-4 py-2.5 text-sm leading-relaxed shadow-card",
          isUser
            ? "border-accent/40 bg-accent text-white"
            : "border-border bg-bg-card text-ink",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="md">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        <p
          className={cn(
            "mt-1.5 text-right text-[10px]",
            isUser ? "text-white/70" : "text-ink-subtle",
          )}
        >
          {time}
        </p>
      </div>
    </div>
  );
};

interface PendingAssistantProps {
  content: string;
  sources: QuerySource[];
  hasRelevantContext: boolean;
  streaming: boolean;
  error: string | null;
}

// In-progress assistant message: grows as SSE tokens arrive, shows a
// "Generating…" pill while streaming, and a Sources block once the
// `sources` event fires.
export const PendingAssistantMessage = ({
  content,
  sources,
  hasRelevantContext,
  streaming,
  error,
}: PendingAssistantProps) => {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard may be blocked; non-fatal */
    }
  };

  return (
    <div className="flex w-full justify-start">
      <div className="max-w-[85%] rounded-2xl border border-border bg-bg-card px-4 py-2.5 text-sm leading-relaxed shadow-card">
        {error ? (
          <div className="flex items-start gap-2 text-red-300">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="mt-0.5 h-4 w-4 shrink-0"
              aria-hidden
            >
              <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            </svg>
            <span>{error}</span>
          </div>
        ) : content ? (
          <>
            <div className="md">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
            <div className="mt-1.5 flex items-center justify-between text-[10px] text-ink-subtle">
              <span>
                {streaming && (
                  <span className="inline-flex items-center gap-1 text-accent">
                    <span className="inline-block h-1 w-1 animate-pulse rounded-full bg-accent" />
                    Generating…
                  </span>
                )}
              </span>
              <button
                type="button"
                onClick={onCopy}
                aria-label={copied ? "Copied" : "Copy response"}
                className="rounded px-1.5 py-0.5 text-[10px] text-ink-subtle hover:bg-bg-hover hover:text-ink"
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </>
        ) : (
          <span
            className="inline-flex items-center gap-1.5 text-ink-muted"
            aria-label="Assistant is generating a response"
          >
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted" />
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted [animation-delay:120ms]" />
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted [animation-delay:240ms]" />
          </span>
        )}

        {sources.length > 0 && (
          <SourcesBlock sources={sources} />
        )}

        {!hasRelevantContext && !streaming && !error && (
          <p className="mt-2 text-[11px] italic text-ink-subtle">
            No relevant context in your documents.
          </p>
        )}
      </div>
    </div>
  );
};

const SourcesBlock = ({ sources }: { sources: QuerySource[] }) => (
  <div className="mt-3 border-t border-border pt-2.5">
    <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-subtle">
      Sources
    </p>
    <ul className="flex flex-col gap-1">
      {sources.map((s, i) => (
        <li
          key={`${s.document_id}-${s.chunk_index}-${i}`}
          className="flex items-center gap-2 rounded-md border border-border bg-bg-panel/60 px-2 py-1.5 text-xs"
        >
          <Badge tone="accent">{i + 1}</Badge>
          <span className="truncate font-medium text-ink">{s.filename}</span>
          {s.page_number != null && (
            <span className="text-[10px] text-ink-subtle">
              Page {s.page_number}
            </span>
          )}
        </li>
      ))}
    </ul>
  </div>
);

interface ChatWindowProps {
  messages: Message[];
  pending?: React.ReactNode;
  emptyState?: React.ReactNode;
}

export const ChatWindow = ({ messages, pending, emptyState }: ChatWindowProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  // Track whether the user is "at the bottom" of the scroll container so
  // we only auto-scroll on new content when they want it. Otherwise we
  // yank the page away from messages they're reading.
  const stickToBottomRef = useRef(true);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      // 32px tolerance so "close enough" counts as bottom.
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
      stickToBottomRef.current = distance < 32;
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!stickToBottomRef.current) return;
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, pending]);

  if (messages.length === 0 && !pending) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-center text-sm text-ink-muted">
        {emptyState ?? "No messages yet. Ask a question to get started."}
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      role="log"
      aria-live="polite"
      aria-relevant="additions"
      className="flex h-full flex-col gap-3 overflow-y-auto px-4 py-4"
    >
      {messages.map((m) => (
        <ChatMessage key={m.id} message={m} />
      ))}
      {pending}
    </div>
  );
};

const formatClock = (iso: string): string =>
  new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
