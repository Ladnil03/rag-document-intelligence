// Auth context + provider. Owns the JWT and the current user, exposes
// login/register/logout, and persists the token to localStorage.
//
// Phase 11 changes:
//  - Subscribes to the "auth:unauthorized" window event dispatched by
//    services/api.ts whenever any request returns 401. The provider
//    clears local user state so the rest of the tree re-renders against
//    "signed out". ProtectedRoute still bounces the URL.
//  - `login` and `register` resolve only after the API settles (so the
//    caller can show a spinner until the navigation happens).
//  - `register` no longer fails silently if the auto-login POST 500s; it
//    surfaces the original HttpError.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { auth, authToken, HttpError } from "@/services/api";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // No /auth/me endpoint yet — token presence is the truth. ProtectedRoute
    // is the redirect mechanism. Initial loading flips off immediately so
    // pages render their own skeletons instead of a global spinner.
    setLoading(false);

    const onUnauth = () => setUser(null);
    window.addEventListener("auth:unauthorized", onUnauth);
    return () => window.removeEventListener("auth:unauthorized", onUnauth);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const token = await auth.login(email, password);
    authToken.set(token.access_token);
    // /auth/login does not return the user row; minimal stub until /auth/me lands.
    setUser({ id: 0, email, created_at: new Date().toISOString() });
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const created = await auth.register(email, password);
    // Auto-login for first-run smoothness. If the auto-login fails the
    // page can route to /login manually — we still surface the original
    // error from the second call so it doesn't look like a silent success.
    const token = await auth.login(email, password);
    authToken.set(token.access_token);
    setUser(created);
  }, []);

  const logout = useCallback(() => {
    authToken.clear();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
    }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
};

// Helper for non-React code (e.g. services/api.ts) to test whether the
// current render believes the user is authenticated.
export const isAuthed = (): boolean => !!authToken.get();

// Re-exported so callers don't have to import from two places.
export { HttpError };
