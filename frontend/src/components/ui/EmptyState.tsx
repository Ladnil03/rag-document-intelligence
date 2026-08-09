import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export const EmptyState = ({ icon, title, description, action }: EmptyStateProps) => (
  <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-bg-panel/60 px-6 py-10 text-center">
    {icon && (
      <div className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-bg-card text-ink-muted">
        {icon}
      </div>
    )}
    <h3 className="text-sm font-semibold text-ink">{title}</h3>
    {description && (
      <p className="max-w-sm text-xs text-ink-muted">{description}</p>
    )}
    {action}
  </div>
);
