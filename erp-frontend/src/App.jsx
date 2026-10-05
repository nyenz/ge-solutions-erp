// PATH: erp-frontend/src/App.jsx
import { roleFlags, landingPathFor } from './utils/roles';
import React, { Suspense, useEffect } from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthProvider';
import { useAuth } from './hooks/useAuth';

import CircuitBackground from './components/layout/CircuitBackground';
import Shell from './components/layout/Shell';
import RouteErrorScreen from './components/common/RouteErrorScreen';
import { LoadingState } from './components/common/LoadingState';
import { readPrefsFor } from './context/prefsStore';

import LoginPage      from './pages/login/LoginPage';

/* fix182 (speed): every page is its own file, downloaded when it is first opened, so the first screen no longer waits
   for the whole app (1.2 MB). After sign-in the other pages are fetched quietly in the background, so moving between
   them stays instant. A page file that no longer exists (the site was updated while this tab was open) reloads the tab
   once instead of showing the fault screen. */
const RELOAD_KEY = 'gs_chunk_reload_at';
function lazyPage(load) {
    const safeLoad = () => load().catch((err) => {
        let last = 0;
        try { last = Number(sessionStorage.getItem(RELOAD_KEY)) || 0; } catch { /* storage blocked */ }
        if (Date.now() - last > 15000) {
            try { sessionStorage.setItem(RELOAD_KEY, String(Date.now())); } catch { /* storage blocked */ }
            window.location.reload();
            return new Promise(() => {});
        }
        throw err;
    });
    const Page = React.lazy(safeLoad);
    Page.preload = safeLoad;
    return Page;
}

const Dashboard           = lazyPage(() => import('./pages/Dashboard/Dashboard'));
const IntakePage          = lazyPage(() => import('./pages/Intake/IntakePage'));
const LedgerPage          = lazyPage(() => import('./pages/Ledger/LedgerPage'));
const FolderPage          = lazyPage(() => import('./pages/DigitalFolder/FolderPage'));
const RecoveryPortal      = lazyPage(() => import('./pages/Recovery/RecoveryPortal'));
const ClientLedgerPage    = lazyPage(() => import('./pages/Clients/ClientLedgerPage'));
const ClientPortfolioPage = lazyPage(() => import('./pages/Clients/ClientPortfolioPage'));
const PaymentsPage        = lazyPage(() => import('./pages/Payments/PaymentsPage'));
const ExpensesPage        = lazyPage(() => import('./pages/Financials/ExpensesPage'));
const ReportHub           = lazyPage(() => import('./pages/Reports/ReportHub'));
const AuditPage           = lazyPage(() => import('./pages/Audit/AuditPage'));
const SettingsPage        = lazyPage(() => import('./pages/settings/SettingsPage'));
const MyEntriesPage       = lazyPage(() => import('./pages/Pending/MyEntriesPage'));
const PendingViewPage     = lazyPage(() => import('./pages/Pending/PendingViewPage'));
const ALL_PAGES = [Dashboard, LedgerPage, FolderPage, IntakePage, RecoveryPortal, ClientLedgerPage, ClientPortfolioPage,
    PaymentsPage, ExpensesPage, SettingsPage, ReportHub, AuditPage, MyEntriesPage, PendingViewPage];

/** fix182: ONE frame (header, bell, sidebar) for every signed-in page. It stays mounted while you move between pages,
    so the bell and sidebar are not rebuilt and re-fetched on every click; only the page inside changes. */
const ShellLayout = () => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    return (
        <Shell><Suspense fallback={<LoadingState label="OPENING..." size="page" />}><Outlet /></Suspense></Shell>
    );
};

/** Fetches the other page files once the browser is idle after sign-in (one at a time, never during real work). */
function usePrefetchPages(signedIn) {
    useEffect(() => {
        if (!signedIn) return undefined;
        let cancelled = false;
        const idle = window.requestIdleCallback || ((fn) => setTimeout(fn, 1200));
        const queue = ALL_PAGES.slice();
        const next = () => {
            if (cancelled || queue.length === 0) return;
            const P = queue.shift();
            P.preload().catch(() => {}).finally(() => idle(next));
        };
        const t = setTimeout(() => idle(next), 1500);
        return () => { cancelled = true; clearTimeout(t); };
    }, [signedIn]);
}

const ProtectedRoute = ({ children, adminOnly = false, managerPlus = false, isSettings = false, employeeOk = false }) => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    if (user.mustChangePassword && !isSettings) return <Navigate to="/settings" replace />;
    const f = roleFlags(user);   // fix181: one rank helper for every page
    // fix181 (8.7b, 14.0a): the Employee may open only New Project, My Entries, their Pending view and Settings;
    // everything else sends them to New Project (sending them to /dashboard made a redirect loop)
    if (f.isEmployee && !employeeOk && !isSettings) return <Navigate to="/land/new" replace />;
    if (adminOnly && !f.isOwnerLevel) return <Navigate to="/dashboard" replace />;
    if (managerPlus && !f.isManager) return <Navigate to="/dashboard" replace />;
    return children;
};

/* fix181 (14.0a, 15.1i): WHERE SIGNING IN DROPS YOU. The Start page choice is kept per person on the device and is
   checked against the CURRENT person's rank (devices are shared); the Employee always starts at New Project.
   readPrefsFor() is a plain localStorage read, not a hook, because these are route elements. */
const landingPath = (user) => {
    try { return landingPathFor(user, readPrefsFor(user?.username).landing); }
    catch { return landingPathFor(user, null); }
};

const LoginRoute = () => {
    const { user, token } = useAuth();
    if (token && user) {
        // The password handbrake outranks the preference: an account that has
        // to change its key goes to Settings wherever it would rather start.
        if (user.mustChangePassword) return <Navigate to="/settings" replace />;
        return <Navigate to={landingPath(user)} replace />;
    }
    return <LoginPage />;
};

const FallbackRoute = () => {
    const { user, token } = useAuth();
    if (!token || !user) return <Navigate to="/login" replace />;
    if (user.mustChangePassword) return <Navigate to="/settings" replace />;
    return <Navigate to={landingPath(user)} replace />;
};

const AppLayout = () => {
    const { user, token } = useAuth();
    usePrefetchPages(!!(user && token));
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
            {
                element: <ShellLayout />,
                children: [
                    { path: "dashboard", element: <ProtectedRoute><Dashboard /></ProtectedRoute> },
                    { path: "land/new", element: <ProtectedRoute employeeOk><IntakePage /></ProtectedRoute> },
                    { path: "my-entries", element: <ProtectedRoute employeeOk><MyEntriesPage /></ProtectedRoute> },
                    { path: "pending/:id", element: <ProtectedRoute employeeOk><PendingViewPage /></ProtectedRoute> },
                    { path: "land/projects", element: <ProtectedRoute><LedgerPage /></ProtectedRoute> },
                    { path: "folder/:id", element: <ProtectedRoute><FolderPage /></ProtectedRoute> },
                    { path: "recovery", element: <ProtectedRoute><RecoveryPortal /></ProtectedRoute> },
                    { path: "clients", element: <ProtectedRoute><ClientLedgerPage /></ProtectedRoute> },
                    { path: "client/:id", element: <ProtectedRoute><ClientPortfolioPage /></ProtectedRoute> },
                    { path: "payments", element: <ProtectedRoute adminOnly><PaymentsPage /></ProtectedRoute> },
                    { path: "financials", element: <ProtectedRoute managerPlus><ExpensesPage /></ProtectedRoute> },
                    { path: "reports", element: <ProtectedRoute adminOnly><ReportHub /></ProtectedRoute> },
                    { path: "audit", element: <ProtectedRoute adminOnly><AuditPage /></ProtectedRoute> },
                    { path: "settings", element: <ProtectedRoute isSettings><SettingsPage /></ProtectedRoute> },
                ]
            },
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
