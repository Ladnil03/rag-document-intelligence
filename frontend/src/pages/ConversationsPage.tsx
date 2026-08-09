import { Link } from "react-router-dom";

import { Page } from "@/components/layout/AppShell";
import { Card, SectionTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { useConversations } from "@/hooks/useConversations";
import { useToast } from "@/context/ToastContext";
import { friendlyError } from "@/utils/errors";
import { formatRelative } from "@/utils/ui";

export const ConversationsPage = () => {
  const {
    list,
    loading,
    error,
    selectedId,
    setSelectedId,
    create,
    remove,
    refresh,
  } = useConversations();
  const toast = useToast();

  const onDelete = async (id: number, title: string) => {
    if (!window.confirm(`Delete "${title}"? This removes all its messages.`))
      return;
    try {
      await remove(id);
      toast.success(`Deleted "${title}".`);
    } catch (err) {
      toast.error(friendlyError(err, "Delete failed."));
    }
  };

  const onCreate = async () => {
    try {
      const c = await create();
      setSelectedId(c.id);
      toast.success("New chat started.");
    } catch (err) {
      toast.error(friendlyError(err, "Could not start a chat."));
    }
  };

  return (
    <Page
      title="Conversations"
      description="Persistent chat sessions stored against your account."
      actions={
        <>
          <Button variant="secondary" size="sm" onClick={() => refresh()}>
            Refresh
          </Button>
          <Button size="sm" onClick={onCreate}>
            + New chat
          </Button>
        </>
      }
    >
      <Card>
        <SectionTitle title="History" description="Newest first." />
        <div className="mt-4">
          {loading ? (
            <ul className="space-y-2" aria-label="Loading conversations">
              {Array.from({ length: 4 }).map((_, i) => (
                <li key={i} className="flex items-center gap-3 rounded-md border border-border bg-bg-card px-4 py-3">
                  <div className="flex-1 space-y-2">
                    <Skeleton width="40%" height={14} />
                    <Skeleton width="25%" height={10} />
                  </div>
                </li>
              ))}
            </ul>
          ) : error ? (
            <p
              role="alert"
              className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300"
            >
              {error}
            </p>
          ) : list.length === 0 ? (
            <EmptyState
              title="No conversations yet"
              description="Start a chat to see it listed here."
              action={
                <Button size="sm" onClick={onCreate}>
                  + New chat
                </Button>
              }
            />
          ) : (
            <ul className="divide-y divide-border rounded-xl border border-border bg-bg-card">
              {list.map((c) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <Link
                    to="/app/chat"
                    onClick={() => setSelectedId(c.id)}
                    className="min-w-0 flex-1"
                  >
                    <p className="truncate text-sm font-medium text-ink hover:text-accent">
                      {c.title}
                    </p>
                    <p className="text-xs text-ink-muted">
                      Updated {formatRelative(c.updated_at)}
                    </p>
                  </Link>
                  <div className="flex items-center gap-2">
                    {selectedId === c.id && <Badge tone="accent">Active</Badge>}
                    <Link to="/app/chat" onClick={() => setSelectedId(c.id)}>
                      <Button variant="ghost" size="sm">
                        Open
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(c.id, c.title)}
                    >
                      Delete
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Card>
    </Page>
  );
};
