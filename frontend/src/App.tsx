import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./layouts/MainLayout";
import { HomePage } from "./pages/HomePage";
import { ResumePage } from "./pages/ResumePage";
import { JobMatchPage } from "./pages/JobMatchPage";
import { InterviewPage } from "./pages/InterviewPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ImprovementPage } from "./pages/ImprovementPage";
import { SettingsPage } from "./pages/SettingsPage";
import { LoginPage } from "./pages/LoginPage";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { LoadingState } from "./components/States";
import { type ReactNode } from "react";

/**
 * CareerPilot AI - Main Application Component
 */
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <LoadingState message="Loading..." />;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="login" element={<LoginPage />} />
            <Route
              path="resume"
              element={
                <ProtectedRoute>
                  <ResumePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="job-match"
              element={
                <ProtectedRoute>
                  <JobMatchPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="interview"
              element={
                <ProtectedRoute>
                  <InterviewPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="improve"
              element={
                <ProtectedRoute>
                  <ImprovementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
