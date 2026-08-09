import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";

interface State {
  error: Error | null;
}

// Lightweight error boundary. Phase 11 wants production-quality error
// handling: a thrown render exception should not produce a blank page.
// The boundary catches it and offers a "Try again" reset.

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Server-side logging would go here. We deliberately do NOT include
    // the stack trace in the UI; it leaks implementation details and is
    // overwhelming for non-technical users.
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error("UI exception:", error, info.componentStack);
    }
  }

  reset = () => {
    this.setState({ error: null });
  };

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-bg px-4">
          <div className="w-full max-w-md rounded-2xl border border-border bg-bg-card p-6 shadow-card">
            <h1 className="text-base font-semibold text-ink">
              Something went wrong
            </h1>
            <p className="mt-1 text-sm text-ink-muted">
              The interface hit an unexpected error. Reloading usually fixes it.
              Your data is safe.
            </p>
            <div className="mt-4 flex gap-2">
              <Button onClick={this.reset}>Try again</Button>
              <Button variant="secondary" onClick={() => window.location.reload()}>
                Reload page
              </Button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
