import type { ReactNode } from "react";
import { cn } from "@/utils/ui";

interface CardProps {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}

export const Card = ({ children, className, padded = true }: CardProps) => (
  <div
    className={cn(
      "rounded-xl border border-border bg-bg-card shadow-card",
      padded && "p-5",
      className,
    )}
  >
    {children}
  </div>
);

export const SectionTitle = ({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) => (
  <div className={cn("flex items-start justify-between gap-3", className)}>
    <div>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {description && (
        <p className="mt-0.5 text-xs text-ink-muted">{description}</p>
      )}
    </div>
    {action}
  </div>
);
