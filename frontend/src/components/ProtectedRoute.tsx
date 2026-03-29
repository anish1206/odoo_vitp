import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export const ProtectedRoute = () => {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <div className="centered-page">Loading your workspace...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
