import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PublicOnlyRoute } from "./components/PublicOnlyRoute";
import { useAuth } from "./context/AuthContext";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
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
          <Route
            path="/employee/claims"
            element={
              <PlaceholderPage
                title="My Claims"
                description="Phase 3 will deliver claim list, status filters, and detail views."
              />
            }
          />
          <Route
            path="/employee/submit"
            element={
              <PlaceholderPage
                title="Submit Expense"
                description="Phase 3 will add draft and submit claim workflows."
              />
            }
          />
          <Route
            path="/approvals/inbox"
            element={
              <PlaceholderPage
                title="Approvals Inbox"
                description="Phase 4 will add pending approvals queue and approve/reject actions."
              />
            }
          />
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
