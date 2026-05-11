// PATH: erp-frontend/src/App.jsx
import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthProvider';
import { useAuth } from './hooks/useAuth';

import CircuitBackground from './components/layout/CircuitBackground';
import Shell from './components/layout/Shell';

import LoginPage      from './pages/login/LoginPage';
import Dashboard      from './pages/Dashboard/Dashboard';
import IntakePage     from './pages/Intake/IntakePage';
import LedgerPage     from './pages/Ledger/LedgerPage';
import FolderPage     from './pages/DigitalFolder/FolderPage';
import RecoveryPortal from './pages/Recovery/RecoveryPortal';
import PaymentsPage   from './pages/Payments/PaymentsPage';
import ReportHub      from './pages/Reports/ReportHub';
import AuditPage      from './pages/Audit/AuditPage';
import SettingsPage   from './pages/settings/SettingsPage';

const ProtectedRoute = ({ children, adminOnly = false, isSettings = false }) => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    if (user.mustChangePassword && !isSettings) return <Navigate to="/settings" replace />;
    if (adminOnly && !(user.isRoot || user.role === 'ROLE_ADMIN')) return <Navigate to="/dashboard" replace />;
    return children;
};

const LoginRoute = () => {
    const { user, token } = useAuth();
    if (token && user) {
        if (user.mustChangePassword) return <Navigate to="/settings" replace />;
        return <Navigate to="/dashboard" replace />;
    }
    return <LoginPage />;
};

const FallbackRoute = () => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    if (user.mustChangePassword) return <Navigate to="/settings" replace />;
    return <Navigate to="/dashboard" replace />;
};

const AppLayout = () => {
    return (
        <>
            <CircuitBackground />
            <Outlet />
        </>
    );
};

// using createBrowserRouter enables data router hooks like useBlocker
const router = createBrowserRouter([
    {
        path: "/",
        element: <AppLayout />,
        children: [
            { index: true, element: <FallbackRoute /> },
            { path: "login", element: <LoginRoute /> },
            { path: "dashboard", element: <ProtectedRoute><Shell><Dashboard /></Shell></ProtectedRoute> },
            { path: "land/new", element: <ProtectedRoute><Shell><IntakePage /></Shell></ProtectedRoute> },
            { path: "land/projects", element: <ProtectedRoute><Shell><LedgerPage /></Shell></ProtectedRoute> },
            { path: "folder/:id", element: <ProtectedRoute><Shell><FolderPage /></Shell></ProtectedRoute> },
            { path: "recovery", element: <ProtectedRoute><Shell><RecoveryPortal /></Shell></ProtectedRoute> },
            { path: "payments", element: <ProtectedRoute adminOnly><Shell><PaymentsPage /></Shell></ProtectedRoute> },
            { path: "reports", element: <ProtectedRoute adminOnly><Shell><ReportHub /></Shell></ProtectedRoute> },
            { path: "audit", element: <ProtectedRoute adminOnly><Shell><AuditPage /></Shell></ProtectedRoute> },
            { path: "settings", element: <ProtectedRoute isSettings><Shell><SettingsPage /></Shell></ProtectedRoute> },
            { path: "*", element: <FallbackRoute /> }
        ]
    }
]);

function App() {
    return (
        <AuthProvider>
            <RouterProvider router={router} />
        </AuthProvider>
    );
}

export default App;
