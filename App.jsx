import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import AssetDetails from './pages/AssetDetails';
import Missions from './pages/Missions';
import AssetRequests from './pages/AssetRequests';
import Approvals from './pages/Approvals';
import Inventory from './pages/Inventory';
import Maintenance from './pages/Maintenance';
import Notifications from './pages/Notifications';
import Reports from './pages/Reports';
import AuditLogs from './pages/AuditLogs';
import Users from './pages/Users';
import Settings from './pages/Settings';
import Profile from './pages/Profile';

// Protected Route Wrapper
const ProtectedRoute = ({ children, roles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-slate-400 text-sm font-mono">AUTHENTICATING...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// App Router
const AppRouter = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />

      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="assets" element={<Assets />} />
        <Route path="assets/:id" element={<AssetDetails />} />
        <Route path="missions" element={<Missions />} />
        <Route path="requests" element={<AssetRequests />} />
        <Route path="approvals" element={
          <ProtectedRoute roles={['Admin', 'Commander']}>
            <Approvals />
          </ProtectedRoute>
        } />
        <Route path="inventory" element={
          <ProtectedRoute roles={['Admin', 'Logistics Officer']}>
            <Inventory />
          </ProtectedRoute>
        } />
        <Route path="maintenance" element={<Maintenance />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="reports" element={
          <ProtectedRoute roles={['Admin', 'Commander', 'Logistics Officer']}>
            <Reports />
          </ProtectedRoute>
        } />
        <Route path="audit-logs" element={
          <ProtectedRoute roles={['Admin']}>
            <AuditLogs />
          </ProtectedRoute>
        } />
        <Route path="users" element={
          <ProtectedRoute roles={['Admin']}>
            <Users />
          </ProtectedRoute>
        } />
        <Route path="settings" element={<Settings />} />
        <Route path="profile" element={<Profile />} />
      </Route>

      {/* 404 fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

const App = () => (
  <BrowserRouter>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </BrowserRouter>
);

export default App;
