import { useState } from "react";

import { Page } from "@/components/layout/AppShell";
import { Card, SectionTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentList } from "@/components/documents/DocumentList";
import { EmptyState } from "@/components/ui/EmptyState";
import { useDocuments } from "@/hooks/useDocuments";
import { useToast } from "@/context/ToastContext";
import { friendlyError } from "@/utils/errors";
import type { Document } from "@/types/api";

// .pdf and .docx — mirrors backend/config.py ALLOWED_EXTENSIONS.
const ACCEPT = ".pdf,.docx";
const MAX_SIZE = 10 * 1024 * 1024;

export const KnowledgeBasePage = () => {
  const {
    documents: list,
    loading,
    uploading,
    uploadError,
    error,
    upload,
    remove,
  } = useDocuments();
  const toast = useToast();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | Document["processing_status"]>("all");
  const [type, setType] = useState<"all" | "pdf" | "docx">("all");
  const [localError, setLocalError] = useState<string | null>(null);

  const onUpload = async (file: File) => {
    setLocalError(null);
    if (file.size === 0) {
      setLocalError("Uploaded file is empty (0 bytes).");
      return;
    }
    if (file.size > MAX_SIZE) {
      setLocalError("File exceeds the 10 MB limit.");
      return;
    }
    const ext = file.name.toLowerCase().split(".").pop() ?? "";
    if (ext !== "pdf" && ext !== "docx") {
      setLocalError("Unsupported file type. Only PDF and DOCX are allowed.");
      return;
    }
    try {
      const created = await upload(file);
      toast.success(`Uploaded "${created.name}". Indexing in the background.`);
    } catch (err) {
      toast.error(friendlyError(err, "Upload failed."));
    }
  };

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
      title="Knowledge Base"
      description="Manage your documents and knowledge sources."
      actions={
        <>
          {processing > 0 && <Badge tone="warning">{processing} processing</Badge>}
          <Button>+ Upload Document</Button>
        </>
      }
    >
      <Card>
        <UploadDropzone
          accept={ACCEPT}
          hint="Supported: PDF, DOCX — max 10 MB."
          disabled={uploading}
          onSelect={onUpload}
        />
        {uploading && (
          <div className="mt-2 flex items-center gap-2 text-xs text-ink-muted" aria-live="polite">
            <Skeleton width={12} height={12} rounded />
            Uploading &amp; indexing…
          </div>
        )}
        {(localError || uploadError) && (
          <p
            role="alert"
            className="mt-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300"
          >
            {localError ?? uploadError}
          </p>
        )}
      </Card>

      <div className="mt-6">
        <Card>
          <SectionTitle
            title="Your documents"
            description="Search and filter your indexed files. Status updates automatically while documents process."
          />
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <div className="min-w-[14rem] flex-1">
              <Input
                label="Search documents"
                placeholder="Search by name…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <FilterSelect
              label="Status"
              value={status}
              onChange={(v) => setStatus(v as typeof status)}
              options={[
                { value: "all", label: "All" },
                { value: "COMPLETED", label: "Indexed" },
                { value: "PROCESSING", label: "Processing" },
                { value: "UPLOADED", label: "Uploaded" },
                { value: "FAILED", label: "Failed" },
              ]}
            />
            <FilterSelect
              label="Type"
              value={type}
              onChange={(v) => setType(v as typeof type)}
              options={[
                { value: "all", label: "All" },
                { value: "pdf", label: "PDF" },
                { value: "docx", label: "DOCX" },
              ]}
            />
            <Badge>{list.length} total</Badge>
          </div>

          <div className="mt-4">
            {loading ? (
              <DocumentListSkeleton />
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
                description="Drop a PDF or DOCX above to start building your knowledge base."
              />
            ) : (
              <DocumentList
                documents={list}
                query={query}
                statusFilter={status}
                typeFilter={type}
                onDelete={onDelete}
              />
            )}
          </div>
        </Card>
      </div>
    </Page>
  );
};

const DocumentListSkeleton = () => (
  <div className="overflow-hidden rounded-xl border border-border bg-bg-card">
    <div className="flex gap-3 border-b border-border bg-bg-panel px-4 py-2.5 text-[11px] uppercase tracking-wider text-ink-subtle">
      <Skeleton width={120} height={10} />
      <Skeleton width={40} height={10} />
      <Skeleton width={50} height={10} />
      <Skeleton width={70} height={10} />
    </div>
    {Array.from({ length: 4 }).map((_, i) => (
      <div
        key={i}
        className="flex items-center gap-4 border-b border-border px-4 py-3 last:border-b-0"
      >
        <Skeleton width={180} height={12} />
        <Skeleton width={36} height={12} />
        <Skeleton width={50} height={12} />
        <Skeleton width={70} height={18} rounded />
        <Skeleton width={70} height={10} />
      </div>
    ))}
  </div>
);

interface FilterSelectProps<T extends string> {
  label: string;
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string }[];
}

const FilterSelect = <T extends string>({
  label,
  value,
  onChange,
  options,
}: FilterSelectProps<T>) => (
  <label className="block">
    <span className="mb-1 block text-xs font-medium text-ink-muted">{label}</span>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      aria-label={label}
      className="rounded-md border border-border bg-bg-panel px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/40"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  </label>
);
