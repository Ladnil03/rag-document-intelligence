// useDocuments — lists the authenticated user's documents and polls for
// status updates while any document is still being processed.
//
// Phase 10 adds:
//  - status polling (every 2s) while at least one row is in UPLOADED or
//    PROCESSING. The poll stops when every row reaches COMPLETED or
//    FAILED, so a stable library doesn't waste requests.
//  - upload() that POSTs to /documents/upload and inserts the new row at
//    the top of the list optimistically; the next poll reconciles its
//    status from UPLOADED -> PROCESSING -> COMPLETED.
//  - remove() that calls DELETE /documents/{id} with a confirm step
//    owned by the caller (the hook never pops a browser dialog).

import { useCallback, useEffect, useRef, useState } from "react";

import { documents } from "@/services/api";
import type { Document } from "@/types/api";

const POLL_INTERVAL_MS = 2000;

interface UseDocumentsResult {
  documents: Document[];
  loading: boolean;
  uploading: boolean;
  uploadError: string | null;
  error: string | null;
  refresh: () => Promise<void>;
  upload: (file: File) => Promise<Document>;
  remove: (id: number) => Promise<void>;
}

const isPending = (d: Document) =>
  d.processing_status === "UPLOADED" || d.processing_status === "PROCESSING";

export const useDocuments = (): UseDocumentsResult => {
  const [list, setList] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);

  const refresh = useCallback(async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    setError(null);
    try {
      const data = await documents.list();
      setList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents.");
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while anything is still in flight. We stop polling the moment
  // every row reaches a terminal state to avoid wasting requests.
  useEffect(() => {
    if (!list.some(isPending)) return;
    const id = window.setInterval(refresh, POLL_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [list, refresh]);

  const upload = useCallback(
    async (file: File): Promise<Document> => {
      setUploading(true);
      setUploadError(null);
      try {
        const created = await documents.upload(file);
        // Insert immediately so the row appears even before the next poll.
        setList((prev) => {
          if (prev.some((d) => d.id === created.id)) return prev;
          return [created, ...prev];
        });
        return created;
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Upload failed.";
        setUploadError(msg);
        throw err;
      } finally {
        setUploading(false);
      }
    },
    [],
  );

  const remove = useCallback(async (id: number) => {
    await documents.remove(id);
    setList((prev) => prev.filter((d) => d.id !== id));
  }, []);

  return {
    documents: list,
    loading,
    uploading,
    uploadError,
    error,
    refresh,
    upload,
    remove,
  };
};
