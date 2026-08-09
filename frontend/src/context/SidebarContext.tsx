import { createContext, useContext, type ReactNode } from "react";

interface SidebarContextValue {
  openSidebar: () => void;
}

const SidebarContext = createContext<SidebarContextValue | undefined>(undefined);

export const SidebarProvider = ({
  value,
  children,
}: {
  value: SidebarContextValue;
  children: ReactNode;
}) => <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;

export const useSidebar = (): SidebarContextValue => {
  const ctx = useContext(SidebarContext);
  if (!ctx) {
    // Safe default: no-op. Lets components that may render outside the
    // shell (e.g. error states) still call openSidebar() without crashing.
    return { openSidebar: () => {} };
  }
  return ctx;
};
