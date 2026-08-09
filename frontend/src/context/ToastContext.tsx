// Toast notification system.
//
// Why: Phase 11 replaces ad-hoc inline banners for transient feedback
// (upload success, delete confirm, auth errors) with a single global
// notification surface. One provider, one queue, keyboard-dismissable,
// screen-reader friendly (aria-live polite).
//
// Why no library: the platform's existing UI is hand-built on Tailwind;
// adding react-hot-toast or sonner would be the largest new dependency
// in Phase 11. ~70 LOC does the same job.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { cn } from "@/utils/ui";

export type ToastTone = "success" | "error" | "info";

export interface ToastInput {
  message: string;
  tone?: ToastTone;
  // Auto-dismiss after this many ms. 0 disables.
  duration?: number;
}

interface Toast extends Required<Pick<ToastInput, "tone" | "duration">> {
  id: number;
  message: string;
}

interface ToastContextValue {
  toast: (input: ToastInput) => number;
  dismiss: (id: number) => void;
  success: (message: string, opts?: { duration?: number }) => number;
  error: (message: string, opts?: { duration?: number }) => number;
  info: (message: string, opts?: { duration?: number }) => number;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const DEFAULT_DURATION = 4000;

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(1);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (input: ToastInput): number => {
      const id = idRef.current++;
      const tone = input.tone ?? "info";
      const duration = input.duration ?? DEFAULT_DURATION;
      setToasts((prev) => [
        ...prev,
        { id, message: input.message, tone, duration },
      ]);
      if (duration > 0) {
        window.setTimeout(() => dismiss(id), duration);
      }
      return id;
    },
    [dismiss],
  );

  const value = useMemo<ToastContextValue>(
    () => ({
      toast,
      dismiss,
      success: (message, opts) =>
        toast({ message, tone: "success", duration: opts?.duration }),
      error: (message, opts) =>
        toast({ message, tone: "error", duration: opts?.duration ?? 6000 }),
      info: (message, opts) => toast({ message, tone: "info", duration: opts?.duration }),
    }),
    [toast, dismiss],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextValue => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a ToastProvider");
  return ctx;
};

// Listens for the "auth:unauthorized" window event (dispatched by the API
// client on a 401) and surfaces a single toast. Mounted once at the root
// so the rest of the app stays unaware of the cross-cutting concern.
export const AuthUnauthorizedToastBridge = () => {
  const { error } = useToast();
  useEffect(() => {
    const handler = () => {
      error("Your session expired. Please sign in again.");
    };
    window.addEventListener("auth:unauthorized", handler);
    return () => window.removeEventListener("auth:unauthorized", handler);
  }, [error]);
  return null;
};

interface ToastViewportProps {
  toasts: Toast[];
  onDismiss: (id: number) => void;
}

const TONE_STYLES: Record<ToastTone, string> = {
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  error: "border-red-500/30 bg-red-500/10 text-red-200",
  info: "border-border bg-bg-card text-ink",
};

const TONE_ICONS: Record<ToastTone, string> = {
  success: "M5 12l5 5L20 7",
  error: "M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z",
  info: "M12 8v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z",
};

const ToastViewport = ({ toasts, onDismiss }: ToastViewportProps) => (
  <div
    aria-live="polite"
    aria-atomic="true"
    className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
  >
    {toasts.map((t) => (
      <div
        key={t.id}
        role="status"
        className={cn(
          "pointer-events-auto flex items-start gap-2 rounded-lg border px-3 py-2 text-sm shadow-card",
          TONE_STYLES[t.tone],
        )}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="mt-0.5 h-4 w-4 shrink-0"
          aria-hidden
        >
          <path d={TONE_ICONS[t.tone]} />
        </svg>
        <p className="flex-1 leading-snug">{t.message}</p>
        <button
          type="button"
          onClick={() => onDismiss(t.id)}
          aria-label="Dismiss notification"
          className="rounded p-0.5 text-current opacity-70 hover:opacity-100"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3.5 w-3.5"
            aria-hidden
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    ))}
  </div>
);
