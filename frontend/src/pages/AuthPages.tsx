import { useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { friendlyError } from "@/utils/errors";

export const LoginPage = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const from = (location.state as { from?: string } | null)?.from ?? "/app";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const emailRef = useRef<HTMLInputElement>(null);

  if (isAuthenticated) return <Navigate to={from} replace />;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      toast.success("Welcome back.");
      navigate(from, { replace: true });
    } catch (err) {
      setError(friendlyError(err, "Sign-in failed."));
    } finally {
      setSubmitting(false);
      emailRef.current?.focus();
    }
  };

  return (
    <AuthShell title="Sign in" subtitle="Welcome back. Sign in to your RAG workspace.">
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <Input
          ref={emailRef}
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com"
        />
        <Input
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
        {error && (
          <p
            role="alert"
            className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300"
          >
            {error}
          </p>
        )}
        <Button type="submit" block loading={submitting}>
          Sign in
        </Button>
      </form>
      <p className="mt-4 text-center text-xs text-ink-muted">
        Don't have an account?{" "}
        <Link to="/register" className="text-accent hover:underline">
          Create one
        </Link>
      </p>
    </AuthShell>
  );
};

export const RegisterPage = () => {
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isAuthenticated) return <Navigate to="/app" replace />;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await register(email, password);
      toast.success("Account created.");
      navigate("/app", { replace: true });
    } catch (err) {
      setError(friendlyError(err, "Sign-up failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell title="Create account" subtitle="Start building your document knowledge base.">
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <Input
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com"
        />
        <Input
          label="Password"
          type="password"
          name="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          hint="Minimum 8 characters."
          placeholder="••••••••"
        />
        {error && (
          <p
            role="alert"
            className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300"
          >
            {error}
          </p>
        )}
        <Button type="submit" block loading={submitting}>
          Create account
        </Button>
      </form>
      <p className="mt-4 text-center text-xs text-ink-muted">
        Already have an account?{" "}
        <Link to="/login" className="text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
};

const AuthShell = ({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) => (
  <main className="flex min-h-screen items-center justify-center bg-bg px-4">
    <div className="w-full max-w-sm rounded-2xl border border-border bg-bg-card p-6 shadow-card">
      <div className="mb-6 flex items-center gap-2">
        <div
          aria-hidden
          className="flex h-8 w-8 items-center justify-center rounded-md bg-accent/15 text-accent"
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
        <div>
          <p className="text-sm font-semibold text-ink">RAG Intelligence</p>
          <p className="text-[11px] text-ink-muted">AI Document Assistant</p>
        </div>
      </div>
      <h1 className="text-lg font-semibold text-ink">{title}</h1>
      <p className="mt-1 text-xs text-ink-muted">{subtitle}</p>
      <div className="mt-5">{children}</div>
    </div>
  </main>
);
