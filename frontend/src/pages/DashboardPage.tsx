import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Card, SectionTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

import { Page } from "@/components/layout/AppShell";
import { useAuth } from "@/context/AuthContext";
import { useDocuments } from "@/hooks/useDocuments";
import { useConversations } from "@/hooks/useConversations";
import { health } from "@/services/api";

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { documents: docs } = useDocuments();
  const { list: convs } = useConversations();
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    health
      .live()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false));
  }, []);

  const stats = useMemo(() => {
    const indexed = docs.filter((d) => d.processing_status === "COMPLETED").length;
    const failed = docs.filter((d) => d.processing_status === "FAILED").length;
    return {
      totalDocs: docs.length,
      indexed,
      failed,
      conversations: convs.length,
    };
  }, [docs, convs]);

  return (
    <Page
      title={`Welcome${user?.email ? `, ${user.email.split("@")[0]}` : ""}`}
      description="Overview of your knowledge base and recent activity."
    >
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total documents" value={stats.totalDocs} />
        <StatCard label="Indexed" value={stats.indexed} tone="success" />
        <StatCard label="Failed" value={stats.failed} tone="warning" />
        <StatCard label="Conversations" value={stats.conversations} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <SectionTitle
            title="Knowledge Base"
            description="Upload PDFs or DOCX files to ground the assistant in your own content."
            action={
              <Button size="sm" onClick={() => navigate("/app/knowledge")}>
                Open
              </Button>
            }
          />
          <p className="mt-3 text-xs text-ink-muted">
            {stats.totalDocs === 0
              ? "You haven't uploaded any documents yet."
              : `${stats.totalDocs} document(s) • ${stats.indexed} indexed for retrieval.`}
          </p>
        </Card>

        <Card>
          <SectionTitle title="System" />
          <div className="mt-3 flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-ink-muted">Backend health</span>
              {backendOk === null ? (
                <Badge>Checking…</Badge>
              ) : backendOk ? (
                <Badge tone="success">
                  <span aria-hidden className="mr-1">●</span>
                  Online
                </Badge>
              ) : (
                <Badge tone="danger">
                  <span aria-hidden className="mr-1">●</span>
                  Unreachable
                </Badge>
              )}
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-ink-muted">RAG pipeline</span>
              <Badge tone="accent">
                <span aria-hidden className="mr-1">●</span>
                Active
              </Badge>
            </div>
          </div>
        </Card>
      </div>
    </Page>
  );
};

const StatCard = ({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "success" | "warning";
}) => (
  <Card>
    <p className="text-xs text-ink-muted">{label}</p>
    <p
      className={
        tone === "success"
          ? "mt-1 text-2xl font-semibold text-emerald-300"
          : tone === "warning"
            ? "mt-1 text-2xl font-semibold text-amber-300"
            : "mt-1 text-2xl font-semibold text-ink"
      }
    >
      {value}
    </p>
  </Card>
);
