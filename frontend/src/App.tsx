import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/context/AuthContext";
import { AuthUnauthorizedToastBridge, ToastProvider } from "@/context/ToastContext";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { ErrorBoundary } from "@/components/layout/ErrorBoundary";

import { LoginPage, RegisterPage } from "@/pages/AuthPages";
import { DashboardPage } from "@/pages/DashboardPage";
import { KnowledgeBasePage } from "@/pages/KnowledgeBasePage";
import { DocumentsPage } from "@/pages/DocumentsPage";
import { ConversationsPage } from "@/pages/ConversationsPage";
import { ChatPage } from "@/pages/ChatPage";
import { SettingsPage } from "@/pages/SettingsPage";

export const App = () => (
  <ErrorBoundary>
    <ToastProvider>
      <BrowserRouter>
        <AuthProvider>
          <AuthUnauthorizedToastBridge />
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected app */}
            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="knowledge" element={<KnowledgeBasePage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="conversations" element={<ConversationsPage />} />
              <Route path="chat" element={<ChatPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            <Route path="/" element={<Navigate to="/app" replace />} />
            <Route path="*" element={<Navigate to="/app" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ToastProvider>
  </ErrorBoundary>
);
