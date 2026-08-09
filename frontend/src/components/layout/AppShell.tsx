import type { ReactNode } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar, type NavItem } from "@/components/layout/Sidebar";
import { TopBar, MobileMenuButton, useMobileSidebar } from "@/components/layout/TopBar";
import { UserFooter } from "@/components/layout/UserFooter";
import { SidebarProvider, useSidebar } from "@/context/SidebarContext";

const workspace: NavItem[] = [
  { to: "/app", label: "Dashboard" },
  { to: "/app/knowledge", label: "Knowledge Base" },
  { to: "/app/chat", label: "Chat" },
];

const management: NavItem[] = [
  { to: "/app/documents", label: "Documents" },
  { to: "/app/conversations", label: "Conversations" },
];

const system: NavItem[] = [{ to: "/app/settings", label: "Settings" }];

// Single source of truth for the app shell: a fixed left sidebar on desktop
// that becomes a slide-out drawer on small screens, and a scrollable
// content area on the right.
export const AppShell = () => {
  const [open, setOpen] = useMobileSidebar();

  const shell = (
    <div className="flex h-full w-60 flex-col">
      <Sidebar workspace={workspace} management={management} system={system} />
      <div className="mt-auto">
        <UserFooter />
      </div>
    </div>
  );

  return (
    <SidebarProvider value={{ openSidebar: () => setOpen(true) }}>
      <div className="flex h-screen w-full overflow-hidden bg-bg text-ink">
        {/* Desktop sidebar */}
        <div className="hidden md:block">{shell}</div>

        {/* Mobile drawer */}
        {open && (
          <div
            className="fixed inset-0 z-40 md:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="Navigation menu"
          >
            <div
              className="absolute inset-0 bg-black/60"
              onClick={() => setOpen(false)}
              aria-hidden
            />
            <div className="relative z-50 h-full w-64 border-r border-border bg-bg-panel">
              {shell}
            </div>
          </div>
        )}

        <main className="flex min-w-0 flex-1 flex-col">
          <Outlet />
        </main>
      </div>
    </SidebarProvider>
  );
};

interface PageProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  sidebarToggle?: ReactNode;
  children: ReactNode;
}

export const Page = ({ title, description, actions, sidebarToggle, children }: PageProps) => {
  const { openSidebar } = useSidebar();
  return (
    <div className="flex h-full min-h-0 flex-col">
      <TopBar
        title={title}
        description={description}
        actions={actions}
        sidebarToggle={sidebarToggle ?? <MobileMenuButton onClick={openSidebar} />}
      />
      <div className="min-h-0 flex-1 overflow-y-auto p-4 md:p-6">{children}</div>
    </div>
  );
};
