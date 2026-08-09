import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";

interface TopBarProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  sidebarToggle?: ReactNode;
}

export const TopBar = ({ title, description, actions, sidebarToggle }: TopBarProps) => (
  <header
    role="banner"
    className="flex items-start justify-between gap-4 border-b border-border bg-bg-panel/80 px-4 py-3 backdrop-blur md:px-6 md:py-4"
  >
    <div className="flex items-start gap-3">
      {sidebarToggle}
      <div>
        <h1 className="text-base font-semibold text-ink md:text-lg">{title}</h1>
        {description && (
          <p className="mt-0.5 text-xs text-ink-muted">{description}</p>
        )}
      </div>
    </div>
    {actions && (
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        {actions}
      </div>
    )}
  </header>
);

export const MobileMenuButton = ({ onClick }: { onClick: () => void }) => (
  <button
    type="button"
    onClick={onClick}
    aria-label="Open navigation menu"
    className="rounded-md border border-border bg-bg-card p-2 text-ink-muted hover:text-ink md:hidden"
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
);

export const SidebarOpenButton = ({
  open,
  onClick,
}: {
  open: boolean;
  onClick: () => void;
}) => (
  <Button variant="ghost" size="sm" onClick={onClick} aria-expanded={open}>
    {open ? "Hide menu" : "Show menu"}
  </Button>
);

export const useMobileSidebar = () => useState<boolean>(false);
