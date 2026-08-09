import { Page } from "@/components/layout/AppShell";
import { Card, SectionTitle } from "@/components/ui/Card";
import { useAuth } from "@/context/AuthContext";

// Settings page — read-only summary. Account editing endpoints are not
// part of the backend yet; the page reserves space and explains what
// would live here.

export const SettingsPage = () => {
  const { user } = useAuth();
  const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  return (
    <Page
      title="Settings"
      description="Account and application preferences."
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle title="Account" description="The account you're signed in with." />
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-ink-muted">Email</dt>
              <dd className="text-ink">{user?.email ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Member since</dt>
              <dd className="text-ink">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : "—"}
              </dd>
            </div>
          </dl>
        </Card>

        <Card>
          <SectionTitle
            title="Application"
            description="Runtime information exposed to the frontend."
          />
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between gap-2">
              <dt className="text-ink-muted">API URL</dt>
              <dd className="truncate font-mono text-ink">{apiUrl}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">LLM provider</dt>
              <dd className="text-ink">Server-side only</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-muted">Build</dt>
              <dd className="text-ink">
                {import.meta.env.MODE === "production" ? "Production" : "Development"}
              </dd>
            </div>
          </dl>
          <p className="mt-4 text-[11px] text-ink-subtle">
            API keys (e.g. the LLM provider key) are never shipped to the
            browser. They live in <span className="font-mono">backend/.env</span> only.
          </p>
        </Card>
      </div>
    </Page>
  );
};
