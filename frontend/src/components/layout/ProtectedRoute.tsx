import { useEffect, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { authToken } from "@/services/api";

// ProtectedRoute — gates the app behind a stored JWT.
//
// Phase 11 changes:
//  - Subscribes to the global "auth:unauthorized" window event so an
//    expired token mid-session bounces the user back to /login with the
//    requested path preserved. Without this the UI would keep showing
//    data that fails on every request.
//  - Uses a state flag instead of `authToken.get()` directly so a token
//    cleared mid-render still triggers a re-render and the redirect.

export const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const location = useLocation();
  const [token, setToken] = useState<string | null>(() => authToken.get());

  useEffect(() => {
    const onUnauth = () => setToken(null);
    window.addEventListener("auth:unauthorized", onUnauth);
    return () => window.removeEventListener("auth:unauthorized", onUnauth);
  }, []);

  if (!token) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
};
