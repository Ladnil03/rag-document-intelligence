import { useEffect, useRef, useState } from "react";

import { Page } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ChatInput } from "@/components/chat/ChatInput";
import {
  ChatWindow,
  PendingAssistantMessage,
} from "@/components/chat/Message";
import { useConversations } from "@/hooks/useConversations";
import { useConversation } from "@/hooks/useConversation";
import { useToast } from "@/context/ToastContext";
import { friendlyError } from "@/utils/errors";
import { formatRelative } from "@/utils/ui";

// ChatPage — the real RAG workspace.
//
// Three logical regions inside the page card:
//  1. Conversations list (left rail)
//  2. Active conversation messages (center)
//  3. Composer at the bottom (sticky)
//
// On mobile the conversation list collapses to a top toggle so the chat
// area stays usable.

export const ChatPage = () => {
  const {
    list,
    loading: listLoading,
    error: listError,
    selectedId,
    setSelectedId,
    create,
    remove,
  } = useConversations();

  const {
    messages,
    pending,
    loading: convoLoading,
    sending,
    error: convoError,
    send,
    cancel,
  } = useConversation(selectedId);

  const toast = useToast();
  const [showSidebar, setShowSidebar] = useState(false);

  // Auto-select the most recent conversation once the list loads.
  const didAutoSelectRef = useRef(false);
  useEffect(() => {
    if (didAutoSelectRef.current) return;
    if (listLoading) return;
    if (selectedId != null) {
      didAutoSelectRef.current = true;
      return;
    }
    if (list.length > 0) {
      didAutoSelectRef.current = true;
      setSelectedId(list[0].id);
    }
  }, [listLoading, list, selectedId, setSelectedId]);

  const onNewChat = async () => {
    try {
      const created = await create();
      setSelectedId(created.id);
      toast.success("New chat started.");
    } catch (err) {
      toast.error(friendlyError(err, "Could not start a chat."));
    }
  };

  const onDelete = async (id: number) => {
    const target = list.find((c) => c.id === id);
    if (!window.confirm(`Delete "${target?.title ?? "this chat"}"? This removes all its messages.`))
      return;
    try {
      await remove(id);
      toast.success("Chat deleted.");
    } catch (err) {
      toast.error(friendlyError(err, "Delete failed."));
    }
  };

  return (
    <Page
      title="AI Assistant"
      description="Grounded answers from your uploaded documents."
      actions={
        <>
          <Badge tone="success">
            <span aria-hidden className="mr-1">●</span>
            RAG Active
          </Badge>
          <Button variant="secondary" size="sm" onClick={onNewChat}>
            + New chat
          </Button>
        </>
      }
    >
      <div className="flex h-[calc(100vh-8rem)] min-h-[520px] gap-4">
        {/* Conversation rail — visible on desktop, drawer on mobile */}
        <aside
          aria-label="Conversations"
          className={
            "flex w-72 shrink-0 flex-col overflow-hidden rounded-2xl border border-border bg-bg-card " +
            (showSidebar ? "flex" : "hidden") +
            " md:flex md:bg-transparent md:border-0"
          }
        >
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-subtle">
              Conversations
            </p>
            <button
              type="button"
              onClick={() => setShowSidebar(false)}
              className="text-xs text-ink-muted hover:text-ink md:hidden"
            >
              Close
            </button>
          </div>
          <ConversationList
            list={list}
            loading={listLoading}
            error={listError}
            selectedId={selectedId}
            onSelect={(id) => {
              setSelectedId(id);
              setShowSidebar(false);
            }}
            onDelete={onDelete}
          />
        </aside>

        {/* Active conversation */}
        <section className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-bg-card">
          <div className="flex items-center justify-between border-b border-border px-4 py-2">
            <div className="flex min-w-0 items-center gap-2">
              <button
                type="button"
                onClick={() => setShowSidebar((v) => !v)}
                className="rounded-md border border-border bg-bg-card p-1.5 text-ink-muted hover:text-ink md:hidden"
                aria-label={showSidebar ? "Hide conversations" : "Show conversations"}
                aria-expanded={showSidebar}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4"
                  aria-hidden
                >
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
              </button>
              <h2 className="truncate text-sm font-semibold text-ink">
                {selectedId != null
                  ? list.find((c) => c.id === selectedId)?.title ??
                    "Conversation"
                  : "New chat"}
              </h2>
            </div>
            <Badge tone="accent">
              <span aria-hidden className="mr-1">●</span>
              Grounded
            </Badge>
          </div>

          <div className="min-h-0 flex-1">
            {selectedId == null ? (
              <EmptyState
                title="No conversation selected"
                description="Start a new chat to ask questions grounded in your documents."
                action={
                  <Button size="sm" onClick={onNewChat}>
                    + New chat
                  </Button>
                }
              />
            ) : convoLoading ? (
              <div className="flex h-full flex-col gap-3 px-4 py-4" aria-label="Loading messages">
                <Skeleton width="60%" height={28} />
                <Skeleton width="80%" height={28} />
                <Skeleton width="40%" height={28} />
              </div>
            ) : (
              <ChatWindow
                messages={messages}
                emptyState="No messages yet. Ask a question to get started."
                pending={
                  pending ? (
                    <PendingAssistantMessage
                      content={pending.content}
                      sources={pending.sources}
                      hasRelevantContext={pending.hasRelevantContext}
                      streaming={pending.streaming}
                      error={pending.error}
                    />
                  ) : null
                }
              />
            )}
          </div>

          {convoError && (
            <p
              role="alert"
              className="border-t border-red-500/30 bg-red-500/10 px-4 py-2 text-xs text-red-300"
            >
              {convoError}
            </p>
          )}

          <ChatInput
            onSend={(text) => {
              send(text).catch(() => {
                /* error already in convoError / pending.error */
              });
            }}
            onCancel={cancel}
            sending={sending}
            disabled={selectedId == null}
            placeholder={
              selectedId == null
                ? "Start or select a conversation first…"
                : "Ask a question about your documents..."
            }
          />
        </section>
      </div>
    </Page>
  );
};

interface ConversationListProps {
  list: { id: number; title: string; updated_at: string }[];
  loading: boolean;
  error: string | null;
  selectedId: number | null;
  onSelect: (id: number) => void;
  onDelete: (id: number) => Promise<void>;
}

const ConversationList = ({
  list,
  loading,
  error,
  selectedId,
  onSelect,
  onDelete,
}: ConversationListProps) => {
  if (loading) {
    return (
      <ul className="space-y-1.5 px-2 py-2" aria-label="Loading conversations">
        {Array.from({ length: 4 }).map((_, i) => (
          <li key={i} className="rounded-md border border-transparent px-2 py-2">
            <Skeleton width="70%" height={12} />
            <div className="mt-1.5">
              <Skeleton width="30%" height={9} />
            </div>
          </li>
        ))}
      </ul>
    );
  }
  if (error) {
    return (
      <p
        role="alert"
        className="m-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300"
      >
        {error}
      </p>
    );
  }
  if (list.length === 0) {
    return (
      <p className="px-4 py-6 text-center text-xs text-ink-muted">
        No conversations yet. Click <span className="font-medium text-ink">+ New chat</span> to start.
      </p>
    );
  }
  return (
    <ul className="flex-1 overflow-y-auto px-2 py-2">
      {list.map((c) => {
        const isActive = selectedId === c.id;
        return (
          <li
            key={c.id}
            className={
              "group mb-1 flex items-center justify-between gap-2 rounded-md border px-2 py-2 text-sm transition-colors " +
              (isActive
                ? "border-accent/40 bg-accent-subtle/20 text-ink"
                : "border-transparent text-ink-muted hover:border-border hover:bg-bg-hover hover:text-ink")
            }
          >
            <button
              type="button"
              onClick={() => onSelect(c.id)}
              aria-current={isActive ? "true" : undefined}
              className="min-w-0 flex-1 text-left"
            >
              <p className="truncate text-sm font-medium">{c.title}</p>
              <p className="text-[10px] text-ink-subtle">
                {formatRelative(c.updated_at)}
              </p>
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
              className="rounded p-1 text-ink-subtle opacity-0 transition-opacity hover:bg-bg-card hover:text-red-400 group-hover:opacity-100 focus-visible:opacity-100"
              aria-label={`Delete ${c.title}`}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-3.5 w-3.5"
                aria-hidden
              >
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                <path d="M10 11v6M14 11v6" />
              </svg>
            </button>
          </li>
        );
      })}
    </ul>
  );
};
