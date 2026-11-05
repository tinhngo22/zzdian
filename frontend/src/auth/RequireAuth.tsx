import { Navigate, Outlet, useLocation } from "react-router";
import { ErrorState, PageSpinner } from "../components/States";
import { useAuth } from "./AuthContext";

export function RequireAuth() {
  const { user, isLoading, bootError, retryBoot } = useAuth();
  const location = useLocation();

  if (isLoading) return <PageSpinner label="Checking your session" />;
  if (bootError) {
    return (
      <div className="mx-auto max-w-lg px-6 py-24">
        <ErrorState message={bootError.message} onRetry={retryBoot} />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  return <Outlet />;
}
