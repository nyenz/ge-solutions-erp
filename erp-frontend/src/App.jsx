// PATH: erp-frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthProvider';
import { useAuth } from './hooks/useAuth';

import CircuitBackground from './components/layout/CircuitBackground';
import Shell from './components/layout/Shell';

import LoginPage     from './pages/login/LoginPage';
import Dashboard     from './pages/Dashboard/Dashboard';
import IntakePage    from './pages/Intake/IntakePage';
import LedgerPage    from './pages/Ledger/LedgerPage';
import FolderPage    from './pages/DigitalFolder/FolderPage';
import RecoveryPortal from './pages/Recovery/RecoveryPortal';
import PaymentsPage  from './pages/Payments/PaymentsPage';
import ReportHub     from './pages/Reports/ReportHub';
import AuditPage     from './pages/Audit/AuditPage';
import SettingsPage  from './pages/settings/SettingsPage';

const ProtectedRoute = ({ children, adminOnly = false }) => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    if (adminOnly && !(user.isRoot || user.role === 'ROLE_ADMIN')) return <Navigate to="/dashboard" replace />;
    return children;
};

const AppRoutes = () => {
    const { user, token } = useAuth();

    if (user && user.mustChangePassword) {
        return (
            <Routes>
                <Route path="/settings" element={<Shell><SettingsPage /></Shell>} />
                <Route path="*" element={<Navigate to="/settings" replace />} />
            </Routes>
        );
    }

    return (
        <Routes>
            <Route path="/login" element={!token ? <LoginPage /> : <Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<ProtectedRoute><Shell><Dashboard /></Shell></ProtectedRoute>} />
            <Route path="/land/new" element={<ProtectedRoute><Shell><IntakePage /></Shell></ProtectedRoute>} />
            <Route path="/land/projects" element={<ProtectedRoute><Shell><LedgerPage /></Shell></ProtectedRoute>} />
            <Route path="/folder/:id" element={<ProtectedRoute><Shell><FolderPage /></Shell></ProtectedRoute>} />
            <Route path="/recovery" element={<ProtectedRoute><Shell><RecoveryPortal /></Shell></ProtectedRoute>} />
            <Route path="/payments" element={<ProtectedRoute adminOnly><Shell><PaymentsPage /></Shell></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Shell><SettingsPage /></Shell></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute adminOnly><Shell><ReportHub /></Shell></ProtectedRoute>} />
            <Route path="/audit" element={<ProtectedRoute adminOnly><Shell><AuditPage /></Shell></ProtectedRoute>} />
            <Route path="*" element={<Navigate to={token ? "/dashboard" : "/login"} replace />} />
        </Routes>
    );
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <CircuitBackground />
                <AppRoutes />
            </Router>
        </AuthProvider>
    );
}

export default App;