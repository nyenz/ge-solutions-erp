// PATH: erp-frontend/src/App.jsx
import { roleFlags } from './utils/roles';
import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthProvider';
import { useAuth } from './hooks/useAuth';

import CircuitBackground from './components/layout/CircuitBackground';
import Shell from './components/layout/Shell';
import RouteErrorScreen from './components/common/RouteErrorScreen';
import { readPrefs } from './context/PreferencesProvider';

import LoginPage      from './pages/login/LoginPage';
import Dashboard      from './pages/Dashboard/Dashboard';
import IntakePage     from './pages/Intake/IntakePage';
import LedgerPage     from './pages/Ledger/LedgerPage';
import FolderPage     from './pages/DigitalFolder/FolderPage';
import RecoveryPortal from './pages/Recovery/RecoveryPortal';
import ClientLedgerPage from './pages/Clients/ClientLedgerPage';
import ClientPortfolioPage from './pages/Clients/ClientPortfolioPage';
import PaymentsPage   from './pages/Payments/PaymentsPage';
import ExpensesPage    from './pages/Financials/ExpensesPage';
import ReportHub      from './pages/Reports/ReportHub';
import AuditPage      from './pages/Audit/AuditPage';
import SettingsPage   from './pages/settings/SettingsPage';

const ProtectedRoute = ({ children, adminOnly = false, managerPlus = false, isSettings = false }) => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    if (user.mustChangePassword && !isSettings) return <Navigate to="/settings" replace />;
    const f = roleFlags(user);   // fix181: one rank helper for every page
    if (adminOnly && !f.isOwnerLevel) return <Navigate to="/dashboard" replace />;
    if (managerPlus && !f.isManager) return <Navigate to="/dashboard" replace />;
    return children;
};

/* fix71 -- WHERE SIGNING IN DROPS YOU.
   Settings -> Data & Start. Only pages with no role gate are offered, so this
   can never land somebody on a route their rank would bounce them out of:
   Payments and Reports are adminOnly and are deliberately not in the list.
   readPrefs() is a plain localStorage read, not a hook, because these two are
   route elements that render before any provider below them. */
const LANDING = {
    dashboard: '/dashboard',
    ledger:    '/land/projects',
    recovery:  '/recovery',
    clients:   '/clients',
};

const landingPath = () => {
    try { return LANDING[readPrefs().landing] || '/dashboard'; }
    catch { return '/dashboard'; }
};

const LoginRoute = () => {
    const { user, token } = useAuth();
    if (token && user) {
        // The password handbrake outranks the preference: an account that has
        // to change its key goes to Settings wherever it would rather start.
        if (user.mustChangePassword) return <Navigate to="/settings" replace />;
        return <Navigate to={landingPath()} replace />;
    }
    return <LoginPage />;
};

const FallbackRoute = () => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    if (user.mustChangePassword) return <Navigate to="/settings" replace />;
    return <Navigate to={landingPath()} replace />;
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
        errorElement: <RouteErrorScreen />,
        children: [
            { index: true, element: <FallbackRoute /> },
            { path: "login", element: <LoginRoute /> },
            { path: "dashboard", element: <ProtectedRoute><Shell><Dashboard /></Shell></ProtectedRoute> },
            { path: "land/new", element: <ProtectedRoute><Shell><IntakePage /></Shell></ProtectedRoute> },
            { path: "land/projects", element: <ProtectedRoute><Shell><LedgerPage /></Shell></ProtectedRoute> },
            { path: "folder/:id", element: <ProtectedRoute><Shell><FolderPage /></Shell></ProtectedRoute> },
            { path: "recovery", element: <ProtectedRoute><Shell><RecoveryPortal /></Shell></ProtectedRoute> },
            { path: "clients", element: <ProtectedRoute><Shell><ClientLedgerPage /></Shell></ProtectedRoute> },
            { path: "client/:id", element: <ProtectedRoute><Shell><ClientPortfolioPage /></Shell></ProtectedRoute> },
            { path: "payments", element: <ProtectedRoute adminOnly><Shell><PaymentsPage /></Shell></ProtectedRoute> },
            { path: "financials", element: <ProtectedRoute managerPlus><Shell><ExpensesPage /></Shell></ProtectedRoute> },
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
