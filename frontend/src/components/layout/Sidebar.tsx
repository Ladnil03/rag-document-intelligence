import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";
import { cn } from "@/utils/ui";

export interface NavItem {
  to: string;
  label: string;
  icon?: ReactNode;
}

interface NavSectionProps {
  label: string;
  items: NavItem[];
}

const NavSection = ({ label, items }: NavSectionProps) => (
  <div className="px-3 py-2">
    <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-ink-subtle">
      {label}
    </p>
    <ul className="space-y-0.5">
      {items.map((item) => (
        <li key={item.to}>
          <NavLink
            to={item.to}
            end={item.to === "/app"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors",
                isActive
                  ? "bg-bg-hover text-ink"
                  : "text-ink-muted hover:bg-bg-hover hover:text-ink",
              )
            }
          >
            {item.icon && (
              <span aria-hidden className="text-ink-subtle">
                {item.icon}
              </span>
            )}
            {item.label}
          </NavLink>
        </li>
      ))}
    </ul>
  </div>
);

export const Sidebar = ({
  workspace,
  management,
  system,
}: {
  workspace: NavItem[];
  management: NavItem[];
  system: NavItem[];
}) => (
  <aside
    aria-label="Primary"
    className="flex h-full w-60 flex-col border-r border-border bg-bg-panel"
  >
    <div className="px-5 py-5">
      <div className="flex items-center gap-2">
        <div
          aria-hidden
          className="flex h-7 w-7 items-center justify-center rounded-md bg-accent/15 text-accent"
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
          >
            <path d="M4 4h12l4 4v12a2 2 0 0 1-2 2H4z" />
            <path d="M14 4v4h4" />
            <path d="M8 13h8M8 17h5" />
          </svg>
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-ink">RAG Intelligence</p>
          <p className="text-[11px] text-ink-muted">AI Document Assistant</p>
        </div>
      </div>
    </div>

    <nav className="flex-1 overflow-y-auto" aria-label="Sections">
      <NavSection label="Workspace" items={workspace} />
      <NavSection label="Management" items={management} />
      <NavSection label="System" items={system} />
    </nav>
  </aside>
);
