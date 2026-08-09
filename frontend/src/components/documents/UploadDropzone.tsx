import { useCallback, useRef, useState, type DragEvent, type ChangeEvent } from "react";
import { cn } from "@/utils/ui";

interface UploadDropzoneProps {
  // Single source of truth: the allowed extensions come from
  // backend/config.py (ALLOWED_EXTENSIONS = {.pdf, .docx}). We surface them
  // here so the UI matches what the server will accept.
  accept: string;
  hint?: string;
  disabled?: boolean;
  onSelect: (file: File) => void;
}

export const UploadDropzone = ({
  accept,
  hint,
  disabled,
  onSelect,
}: UploadDropzoneProps) => {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      onSelect(files[0]);
    },
    [onSelect],
  );

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDrag(false);
    if (disabled) return;
    handleFiles(e.dataTransfer.files);
  };

  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    // allow re-uploading the same file
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      aria-label="Upload a document. Drag and drop or press Enter to browse."
      aria-disabled={disabled || undefined}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed bg-bg-panel/60 px-6 py-10 text-center transition-colors",
        drag
          ? "border-accent bg-accent-subtle/10"
          : "border-border hover:border-border-strong",
        disabled && "pointer-events-none opacity-60",
      )}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-bg-card text-ink-muted">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-5 w-5"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </div>
      <p className="text-sm font-medium text-ink">
        Drag and drop a file here
      </p>
      <p className="text-xs text-ink-muted">or click to browse</p>
      {hint && <p className="mt-1 text-[11px] text-ink-subtle">{hint}</p>}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={onChange}
        className="hidden"
      />
    </div>
  );
};
