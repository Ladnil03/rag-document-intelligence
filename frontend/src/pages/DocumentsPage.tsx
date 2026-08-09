import { Page } from "@/components/layout/AppShell";
import { DocumentList } from "@/components/documents/DocumentList";
import { Card, SectionTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { useDocuments } from "@/hooks/useDocuments";
import { useToast } from "@/context/ToastContext";
import { friendlyError } from "@/utils/errors";
import type { Document } from "@/types/api";

export const DocumentsPage = () => {
  const {
    documents: list,
    loading,
    error,
    remove,
    refresh,
  } = useDocuments();
  const toast = useToast();

  const onDelete = async (doc: Document) => {
    if (!window.confirm(`Delete "${doc.name}"? This removes its vectors too.`))
      return;
    try {
      await remove(doc.id);
      toast.success(`Deleted "${doc.name}".`);
    } catch (err) {
      toast.error(friendlyError(err, "Delete failed."));
    }
  };

  const processing = list.filter(
    (d) => d.processing_status === "UPLOADED" || d.processing_status === "PROCESSING",
  ).length;

  return (
    <Page
      title="Documents"
      description="All documents you have uploaded to your knowledge base."
      actions={
        <>
          {processing > 0 && <Badge tone="warning">{processing} processing</Badge>}
          <Button variant="secondary" size="sm" onClick={() => refresh()}>
            Refresh
          </Button>
        </>
      }
    >
      <Card>
        <SectionTitle
          title="Library"
          description="Manage, search, and inspect every file you own."
        />
        <div className="mt-4">
          {loading ? (
            <div className="space-y-2" aria-label="Loading documents">
              <Skeleton width="60%" height={14} />
              <Skeleton width="80%" height={14} />
              <Skeleton width="40%" height={14} />
            </div>
          ) : error ? (
            <p
              role="alert"
              className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300"
            >
              {error}
            </p>
          ) : list.length === 0 ? (
            <EmptyState
              title="No documents yet"
              description="Head to Knowledge Base to upload your first PDF or DOCX."
            />
          ) : (
            <DocumentList
              documents={list}
              query=""
              statusFilter="all"
              typeFilter="all"
              onDelete={onDelete}
            />
          )}
        </div>
      </Card>
    </Page>
  );
};
