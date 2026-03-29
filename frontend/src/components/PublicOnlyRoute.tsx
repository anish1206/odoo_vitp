import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export const PublicOnlyRoute = () => {
  const { isLoading, isAuthenticated, getDefaultRoute } = useAuth();

  if (isLoading) {
    return <div className="centered-page">Loading your workspace...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to={getDefaultRoute()} replace />;
  }

  return <Outlet />;
};
