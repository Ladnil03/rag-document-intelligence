// useConversations — owns the user's conversation list.
//
// Phase 10 needs four operations on the list:
//  1. Load all conversations on mount.
//  2. Create a new conversation (returns it so the caller can navigate).
//  3. Delete a conversation.
//  4. Track the selected conversation id (persisted to localStorage so a
//     refresh restores the user's view).
//
// The selected id is intentionally separate from this hook so the
// ChatPage can also clear it on delete without us coupling the two.

import { useCallback, useEffect, useRef, useState } from "react";

import { conversations, HttpError } from "@/services/api";
import type { Conversation } from "@/types/api";

const SELECTED_KEY = "rag_selected_conversation";

export const selectedConversation = {
  get: (): number | null => {
    const raw = localStorage.getItem(SELECTED_KEY);
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  },
  set: (id: number | null) => {
    if (id == null) localStorage.removeItem(SELECTED_KEY);
    else localStorage.setItem(SELECTED_KEY, String(id));
  },
};

interface UseConversationsResult {
  list: Conversation[];
  loading: boolean;
  error: string | null;
  selectedId: number | null;
  setSelectedId: (id: number | null) => void;
  refresh: () => Promise<void>;
  create: () => Promise<Conversation>;
  remove: (id: number) => Promise<void>;
}

export const useConversations = (): UseConversationsResult => {
  const [list, setList] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedIdState] = useState<number | null>(() =>
    selectedConversation.get(),
  );

  // If the persisted selection points to a conversation that has since
  // been deleted (e.g. after a 404), drop it silently on first list load.
  const initialSelectionResolved = useRef(false);

  const setSelectedId = useCallback((id: number | null) => {
    setSelectedIdState(id);
    selectedConversation.set(id);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await conversations.list();
      setList(data);
      if (!initialSelectionResolved.current) {
        initialSelectionResolved.current = true;
        const persisted = selectedConversation.get();
        if (persisted != null && !data.some((c) => c.id === persisted)) {
          setSelectedIdState(null);
          selectedConversation.set(null);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load conversations.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const create = useCallback(async (): Promise<Conversation> => {
    const created = await conversations.create(undefined);
    setList((prev) => [created, ...prev]);
    setSelectedId(created.id);
    return created;
  }, [setSelectedId]);

  const remove = useCallback(
    async (id: number) => {
      try {
        await conversations.remove(id);
      } catch (err) {
        // 404 on delete is benign — the row is already gone.
        if (!(err instanceof HttpError) || err.status !== 404) throw err;
      }
      setList((prev) => prev.filter((c) => c.id !== id));
      if (selectedId === id) setSelectedId(null);
    },
    [selectedId, setSelectedId],
  );

  return {
    list,
    loading,
    error,
    selectedId,
    setSelectedId,
    refresh,
    create,
    remove,
  };
};
