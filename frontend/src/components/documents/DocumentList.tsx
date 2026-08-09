import { useMemo } from "react";

import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import type { Document } from "@/types/api";
import { formatBytes, formatRelative } from "@/utils/ui";

interface DocumentListProps {
  documents: Document[];
  query: string;
  statusFilter: "all" | Document["processing_status"];
  typeFilter: "all" | "pdf" | "docx";
  onDelete?: (doc: Document) => void;
}

const STATUS_META: Record<
  Document["processing_status"],
  { tone: "success" | "warning" | "neutral" | "danger"; label: string; glyph: string }
> = {
  COMPLETED: { tone: "success", label: "Indexed", glyph: "✓" },
  PROCESSING: { tone: "warning", label: "Processing", glyph: "…" },
  UPLOADED: { tone: "neutral", label: "Uploaded", glyph: "•" },
  FAILED: { tone: "danger", label: "Failed", glyph: "!" },
};

export const DocumentList = ({
  documents,
  query,
  statusFilter,
  typeFilter,
  onDelete,
}: DocumentListProps) => {
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return documents.filter((d) => {
      if (statusFilter !== "all" && d.processing_status !== statusFilter) return false;
      if (typeFilter !== "all" && d.file_type !== typeFilter) return false;
      if (q && !d.name.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [documents, query, statusFilter, typeFilter]);

  if (filtered.length === 0) {
    return (
      <EmptyState
        title="No documents match your filters"
        description="Upload a PDF or DOCX file above to start building your knowledge base."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-bg-card">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-sm">
          <thead className="bg-bg-panel text-left text-[11px] uppercase tracking-wider text-ink-subtle">
            <tr>
              <th scope="col" className="px-4 py-2.5 font-medium">Name</th>
              <th scope="col" className="px-4 py-2.5 font-medium">Type</th>
              <th scope="col" className="px-4 py-2.5 font-medium">Size</th>
              <th scope="col" className="px-4 py-2.5 font-medium">Status</th>
              <th scope="col" className="px-4 py-2.5 font-medium">Uploaded</th>
              {onDelete && (
                <th scope="col" className="px-4 py-2.5 text-right font-medium">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.map((doc) => {
              const meta = STATUS_META[doc.processing_status];
              return (
                <tr key={doc.id} className="text-ink">
                  <td className="max-w-[40ch] truncate px-4 py-2.5 font-medium">
                    {doc.name}
                  </td>
                  <td className="px-4 py-2.5 uppercase text-ink-muted">
                    {doc.file_type ?? "—"}
                  </td>
                  <td className="px-4 py-2.5 text-ink-muted">
                    {formatBytes(doc.file_size)}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge tone={meta.tone}>
                      <span aria-hidden className="mr-1">{meta.glyph}</span>
                      {meta.label}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-ink-muted">
                    {formatRelative(doc.created_at)}
                  </td>
                  {onDelete && (
                    <td className="px-4 py-2.5 text-right">
                      <button
                        type="button"
                        onClick={() => onDelete(doc)}
                        aria-label={`Delete ${doc.name}`}
                        className="text-xs text-ink-muted hover:text-red-400"
                      >
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
