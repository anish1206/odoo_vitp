import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PublicOnlyRoute } from "./components/PublicOnlyRoute";
import { useAuth } from "./context/AuthContext";
import { DashboardPage } from "./pages/DashboardPage";
import { EmployeeClaimsPage } from "./pages/EmployeeClaimsPage";
import { EmployeeSubmitClaimPage } from "./pages/EmployeeSubmitClaimPage";
import { LoginPage } from "./pages/LoginPage";
import { ApprovalsInboxPage } from "./pages/ApprovalsInboxPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { SignupPage } from "./pages/SignupPage";

const RootRedirect = () => {
  const { isLoading, isAuthenticated, getDefaultRoute } = useAuth();

  if (isLoading) {
    return <div className="centered-page">Loading your workspace...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to={getDefaultRoute()} replace />;
};

function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
      </Route>

      <Route path="/" element={<RootRedirect />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/employee/dashboard" element={<DashboardPage />} />
          <Route path="/employee/claims" element={<EmployeeClaimsPage />} />
          <Route path="/employee/submit" element={<EmployeeSubmitClaimPage />} />
          <Route path="/approvals/inbox" element={<ApprovalsInboxPage />} />
          <Route
            path="/admin/settings"
            element={
              <PlaceholderPage
                title="Company Settings"
                description="Phase 5 adds admin management screens and controls."
              />
            }
          />
          <Route
            path="/admin/users"
            element={
              <PlaceholderPage
                title="User Management"
                description="Phase 5 will include user creation, updates, and deactivation."
              />
            }
          />
          <Route
            path="/admin/departments"
            element={
              <PlaceholderPage
                title="Department Management"
                description="Phase 5 will include department CRUD and assignments."
              />
            }
          />
          <Route
            path="/admin/categories"
            element={
              <PlaceholderPage
                title="Category Management"
                description="Phase 5 will include default category seed and CRUD workflows."
              />
            }
          />
          <Route
            path="/admin/rules"
            element={
              <PlaceholderPage
                title="Approval Rules"
                description="Phase 6 will implement sequential and min-approval rule configuration."
              />
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
