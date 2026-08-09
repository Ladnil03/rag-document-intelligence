import { useNavigate } from "react-router-dom";

import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { selectedConversation } from "@/hooks/useConversations";

export const UserFooter = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = () => {
    logout();
    // Clear the persisted "active conversation" so a different person on
    // the same browser doesn't inherit it after re-login.
    selectedConversation.set(null);
    navigate("/login", { replace: true });
  };

  return (
    <div className="border-t border-border px-4 py-4">
      <div className="mb-3 px-1">
        <p className="text-xs font-medium text-ink-muted">Signed in as</p>
        <p className="truncate text-sm text-ink">{user?.email ?? "—"}</p>
      </div>
      <Button variant="secondary" size="sm" block onClick={onLogout}>
        Log out
      </Button>
    </div>
  );
};
