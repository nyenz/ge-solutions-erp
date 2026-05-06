import os

files = {}

# ── App.jsx — add /payments route ────────────────────────────────────
files["erp-frontend/src/App.jsx"] = """\
// PATH: erp-frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
            <Route path="/reports" element={<ProtectedRoute adminOnly><Shell><ReportHub /></Shell></ProtectedRoute>} />
            <Route path="/audit" element={<ProtectedRoute adminOnly><Shell><AuditPage /></Shell></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Shell><SettingsPage /></Shell></ProtectedRoute>} />
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
"""

# ── Sidebar — add Payments link ───────────────────────────────────────
files["erp-frontend/src/components/layout/Sidebar.jsx"] = """\
// PATH: erp-frontend/src/components/layout/Sidebar.jsx
import React, { useEffect, useRef } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
    FiGrid, FiPlusSquare, FiLayers, FiPhoneCall,
    FiSettings, FiBarChart2, FiShield, FiDollarSign
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import styles from './Sidebar.module.css';

const Sidebar = ({ isCollapsed, onToggle, onLockedClick }) => {
    const { user }  = useAuth();
    const navigate  = useNavigate();
    const location  = useLocation();

    const isCollapsedRef = useRef(isCollapsed);
    const onToggleRef    = useRef(onToggle);
    useEffect(() => { isCollapsedRef.current = isCollapsed; }, [isCollapsed]);
    useEffect(() => { onToggleRef.current    = onToggle;    }, [onToggle]);

    const isMobile = () => typeof window !== 'undefined' && window.innerWidth <= 768;
    const prevPathRef = useRef(location.pathname);

    useEffect(() => {
        const currentPath = location.pathname;
        const prevPath    = prevPathRef.current;
        if (currentPath !== prevPath) {
            prevPathRef.current = currentPath;
            if (isMobile() && !isCollapsedRef.current && typeof onToggleRef.current === 'function') {
                onToggleRef.current();
            }
        }
    }, [location.pathname]);

    const isLocked           = user?.mustChangePassword;
    const hasHighLevelAccess = user?.isRoot || user?.role === 'ROLE_ADMIN';

    const navItems = [
        { path: '/dashboard',     label: 'DASHBOARD', icon: <FiGrid       aria-hidden="true" />, access: true },
        { path: '/land/new',      label: 'INTAKE',    icon: <FiPlusSquare aria-hidden="true" />, access: true },
        { path: '/land/projects', label: 'LEDGER',    icon: <FiLayers     aria-hidden="true" />, access: true },
        { path: '/recovery',      label: 'RECOVERY',  icon: <FiPhoneCall  aria-hidden="true" />, access: true },
        { path: '/payments',      label: 'PAYMENTS',  icon: <FiDollarSign aria-hidden="true" />, access: hasHighLevelAccess },
        { path: '/reports',       label: 'REPORTS',   icon: <FiBarChart2  aria-hidden="true" />, access: hasHighLevelAccess },
        { path: '/audit',         label: 'AUDIT',     icon: <FiShield     aria-hidden="true" />, access: hasHighLevelAccess },
        { path: '/settings',      label: 'SETTINGS',  icon: <FiSettings   aria-hidden="true" />, access: true },
    ];

    const handleLockedClick = (e, item) => {
        e.preventDefault();
        if (typeof onLockedClick === 'function') onLockedClick(item.label);
        navigate('/settings');
    };

    const showBackdrop = isMobile() && !isCollapsed;

    return (
        <>
            {showBackdrop && (
                <div className={styles.sidebarBackdrop}
                    onClick={() => typeof onToggle === 'function' && onToggle()}
                    aria-hidden="true" />
            )}
            <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}
                aria-label="System navigation">
                <nav className={styles.sidebarNav} aria-label="Main menu">
                    <div className={styles.navSection}>
                        <p className={styles.navSectionTitle} aria-hidden="true">
                            {isCollapsed ? 'SYS' : 'SYSTEM MODULES'}
                        </p>
                        {navItems.map(item => {
                            if (!item.access) return null;
                            const locked = isLocked && item.path !== '/settings';
                            return (
                                <NavLink key={item.path} to={item.path}
                                    aria-label={isCollapsed ? item.label : undefined}
                                    aria-disabled={locked ? 'true' : undefined}
                                    className={({ isActive }) =>
                                        [styles.navItem, isActive ? styles.active : '', locked ? styles.navItemLocked : ''].filter(Boolean).join(' ')
                                    }
                                    onClick={locked ? (e) => handleLockedClick(e, item) : undefined}>
                                    <span className={styles.navIcon}>{item.icon}</span>
                                    {!isCollapsed && <span className={styles.navText}>{item.label}</span>}
                                </NavLink>
                            );
                        })}
                    </div>
                </nav>
                <footer className={styles.sidebarFooter} aria-label="NYENZ branding">
                    <div className={styles.branding} aria-hidden="true">NYENZ</div>
                    {!isCollapsed && <div className={styles.version} aria-hidden="true">V.2.0.1-PROD</div>}
                </footer>
            </aside>
        </>
    );
};

export default Sidebar;
"""

# ── New Payments page JSX ─────────────────────────────────────────────
os.makedirs("erp-frontend/src/pages/Payments", exist_ok=True)

files["erp-frontend/src/pages/Payments/PaymentsPage.jsx"] = """\
// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDollarSign, FiSearch, FiX,
    FiChevronRight, FiAlertOctagon, FiUser, FiRefreshCw
} from 'react-icons/fi';
import api from '../../api/axios';
import styles from './PaymentsPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const TYPE_LABELS = {
    STANDARD:        'Title Payment',
    INITIAL_DEPOSIT: 'Initial Deposit',
    BACKLOG_PARTIAL: 'Backlog Payment',
};

const TYPE_COLORS = {
    STANDARD:        '#22c55e',
    INITIAL_DEPOSIT: '#06b6d4',
    BACKLOG_PARTIAL: '#ef4444',
};

const PaymentsPage = () => {
    const navigate = useNavigate();
    const [payments,   setPayments]   = useState([]);
    const [loading,    setLoading]    = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [typeFilter, setTypeFilter] = useState('ALL');
    const [sortDir,    setSortDir]    = useState('desc');

    const loadPayments = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.get('/recovery/payments/all');
            setPayments(res.data || []);
        } catch {
            setPayments([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadPayments(); }, [loadPayments]);

    const filtered = useMemo(() => {
        let list = [...payments];
        if (typeFilter !== 'ALL') list = list.filter(p => p.paymentType === typeFilter);
        if (searchTerm.trim()) {
            const t = searchTerm.toLowerCase();
            list = list.filter(p =>
                p.plotNumber?.toLowerCase().includes(t) ||
                p.ownerName?.toLowerCase().includes(t) ||
                p.recordedBy?.toLowerCase().includes(t) ||
                p.notes?.toLowerCase().includes(t)
            );
        }
        list.sort((a, b) => {
            const da = new Date(a.timestamp), db = new Date(b.timestamp);
            return sortDir === 'desc' ? db - da : da - db;
        });
        return list;
    }, [payments, typeFilter, searchTerm, sortDir]);

    const totalCollected = useMemo(() =>
        filtered.reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    const titleTotal = useMemo(() =>
        filtered.filter(p => p.paymentType !== 'BACKLOG_PARTIAL')
                .reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    const storageTotal = useMemo(() =>
        filtered.filter(p => p.paymentType === 'BACKLOG_PARTIAL')
                .reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div>
                    <h1 className={styles.title}>PAYMENTS</h1>
                    <p className={styles.subtitle}>All payment records — title payments and storage fee collections</p>
                </div>
                <button className={styles.refreshBtn} onClick={loadPayments} aria-label="Refresh">
                    <FiRefreshCw size={16} />
                </button>
            </header>

            <div className={styles.summaryRow}>
                <div className={styles.sumCard}>
                    <label>TOTAL SHOWN</label>
                    <strong>UGX {fmt(totalCollected)}</strong>
                    <span>{filtered.length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#22c55e' }}>
                    <label style={{ color: '#22c55e' }}>TITLE PAYMENTS</label>
                    <strong style={{ color: '#22c55e' }}>UGX {fmt(titleTotal)}</strong>
                    <span>{filtered.filter(p => p.paymentType !== 'BACKLOG_PARTIAL').length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#ef4444' }}>
                    <label style={{ color: '#ef4444' }}>BACKLOG PAYMENTS</label>
                    <strong style={{ color: '#ef4444' }}>UGX {fmt(storageTotal)}</strong>
                    <span>{filtered.filter(p => p.paymentType === 'BACKLOG_PARTIAL').length} records</span>
                </div>
            </div>

            <div className={styles.controls}>
                <div className={styles.searchWrap}>
                    <FiSearch className={styles.searchIcon} />
                    <input type="search" className={styles.searchInput}
                        placeholder="Search plot ID, owner name, recorded by..."
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                    {searchTerm && (
                        <button className={styles.clearBtn} onClick={() => setSearchTerm('')}>
                            <FiX size={14} />
                        </button>
                    )}
                </div>
                <div className={styles.filterRow}>
                    {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL'].map(t => (
                        <button key={t}
                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}
                            onClick={() => setTypeFilter(t)}>
                            {t === 'ALL' ? 'ALL TYPES' : TYPE_LABELS[t]}
                        </button>
                    ))}
                    <button className={styles.filterBtn}
                        onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
                        DATE {sortDir === 'desc' ? '↓ NEWEST' : '↑ OLDEST'}
                    </button>
                </div>
            </div>

            {loading ? (
                <div className={styles.loading}>Loading payments...</div>
            ) : filtered.length === 0 ? (
                <div className={styles.empty}>No payment records found.</div>
            ) : (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>DATE</th>
                                <th>PLOT</th>
                                <th>OWNER</th>
                                <th>TYPE</th>
                                <th>AMOUNT PAID</th>
                                <th>BALANCE AFTER</th>
                                <th>RECORDED BY</th>
                                <th>NOTES</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((pay, i) => (
                                <tr key={pay.id || i} className={styles.row}>
                                    <td>
                                        <div className={styles.dateCell}>
                                            <span>{new Date(pay.timestamp).toLocaleDateString()}</span>
                                            <span className={styles.time}>
                                                {new Date(pay.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                    </td>
                                    <td>
                                        <strong className={styles.plotNum}>{pay.plotNumber || '---'}</strong>
                                    </td>
                                    <td className={styles.ownerCell}>{pay.ownerName || '---'}</td>
                                    <td>
                                        <span className={styles.typeBadge} style={{
                                            background: `${TYPE_COLORS[pay.paymentType] || '#888'}22`,
                                            color: TYPE_COLORS[pay.paymentType] || '#888',
                                            border: `1px solid ${TYPE_COLORS[pay.paymentType] || '#888'}44`
                                        }}>
                                            {pay.paymentType === 'BACKLOG_PARTIAL' && <FiAlertOctagon size={9} />}
                                            {TYPE_LABELS[pay.paymentType] || pay.paymentType}
                                        </span>
                                    </td>
                                    <td>
                                        <strong className={styles.amount} style={{ color: TYPE_COLORS[pay.paymentType] || '#fff' }}>
                                            UGX {fmt(pay.amountPaid)}
                                        </strong>
                                    </td>
                                    <td className={styles.balance}>
                                        {pay.balanceAfter != null ? `UGX ${fmt(pay.balanceAfter)}` : '---'}
                                    </td>
                                    <td>
                                        <span className={styles.recorder}>
                                            <FiUser size={10} /> {pay.recordedBy}
                                        </span>
                                    </td>
                                    <td className={styles.notesCell}>{pay.notes || '---'}</td>
                                    <td>
                                        {pay.projectId && (
                                            <button className={styles.goBtn}
                                                onClick={() => navigate(`/folder/${pay.projectId}`)}>
                                                <FiChevronRight size={13} />
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default PaymentsPage;
"""

# ── New Payments page CSS ─────────────────────────────────────────────
files["erp-frontend/src/pages/Payments/PaymentsPage.module.css"] = """\
/* PATH: erp-frontend/src/pages/Payments/PaymentsPage.module.css */
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(12px, 2vw, 24px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-left: 4px solid #EE8C3A;
    padding: clamp(10px, 1.4vw, 16px) clamp(14px, 2vw, 24px);
    background: rgba(255,255,255,0.55);
    border-radius: 0 10px 10px 0;
    backdrop-filter: blur(15px);
    margin-bottom: clamp(14px, 2vw, 22px);
}

.title {
    font-family: 'Cinzel', serif;
    color: #1a2e30;
    font-size: clamp(16px, 2.2vw, 22px);
    font-weight: 700;
    margin: 0;
    letter-spacing: 2px;
}

.subtitle {
    color: rgba(26,46,48,0.6);
    font-size: clamp(10px, 1.1vw, 13px);
    font-weight: 600;
    margin: 4px 0 0;
}

.refreshBtn {
    background: rgba(26,46,48,0.08);
    border: 1px solid rgba(26,46,48,0.15);
    color: #1a2e30;
    border-radius: 8px;
    padding: 8px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    transition: all 0.2s;
}
.refreshBtn:hover { background: #EE8C3A; color: #fff; border-color: #EE8C3A; }

.summaryRow {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 20px);
}

.sumCard {
    background: linear-gradient(160deg, #1c3335, #213E40);
    border: 1.5px solid rgba(238,140,58,0.25);
    border-radius: 10px;
    padding: clamp(12px, 1.5vw, 18px);
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.sumCard label {
    font-size: clamp(8px, 0.82vw, 10px);
    font-weight: 900;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.sumCard strong {
    font-family: 'Space Mono', monospace;
    font-size: clamp(13px, 1.6vw, 19px);
    color: #fff;
    font-weight: 700;
}

.sumCard span {
    font-size: clamp(9px, 0.88vw, 11px);
    color: rgba(255,255,255,0.3);
}

.controls {
    display: flex;
    flex-direction: column;
    gap: clamp(8px, 1vw, 12px);
    margin-bottom: clamp(14px, 2vw, 20px);
}

.searchWrap {
    position: relative;
    display: flex;
    align-items: center;
    background: #fff;
    border: 1.5px solid #c8d6d7;
    border-radius: 8px;
    height: clamp(38px, 4.2vw, 44px);
    max-width: clamp(280px, 45vw, 520px);
    transition: border-color 0.2s;
}
.searchWrap:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }

.searchIcon { position: absolute; left: 12px; color: #EE8C3A; font-size: 16px; pointer-events: none; }

.searchInput {
    width: 100%;
    border: none;
    outline: none;
    background: transparent;
    color: #1a2e30;
    padding: 0 36px 0 38px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 700;
    font-size: clamp(11px, 1.1vw, 13px);
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }

.clearBtn {
    position: absolute;
    right: 8px;
    background: transparent;
    border: none;
    cursor: pointer;
    color: rgba(26,46,48,0.4);
    display: flex;
    align-items: center;
    padding: 4px;
    border-radius: 4px;
}
.clearBtn:hover { color: #1a2e30; }

.filterRow {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.filterBtn {
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.7);
    border-radius: 6px;
    padding: 6px 14px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 800;
    font-size: clamp(9px, 0.88vw, 11px);
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}
.filterBtn:hover { border-color: #EE8C3A; color: #EE8C3A; }
.filterActive { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }

.tableWrap {
    overflow-x: auto;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
    background: linear-gradient(160deg, #1c3335, #213E40);
}

.table {
    width: 100%;
    border-collapse: collapse;
    font-size: clamp(10px, 1.05vw, 13px);
    min-width: 680px;
}

.table thead tr { border-bottom: 1px solid rgba(255,255,255,0.08); }

.table th {
    padding: clamp(10px, 1.2vw, 14px) clamp(10px, 1.3vw, 14px);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.82vw, 10px);
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
    text-align: left;
    white-space: nowrap;
}

.row { border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.15s; }
.row:hover { background: rgba(255,255,255,0.03); }

.table td {
    padding: clamp(10px, 1.2vw, 14px) clamp(10px, 1.3vw, 14px);
    color: rgba(255,255,255,0.85);
    vertical-align: middle;
}

.dateCell { display: flex; flex-direction: column; gap: 2px; white-space: nowrap; font-weight: 700; }
.time { font-size: 10px; opacity: 0.45; }

.plotNum { font-family: 'Space Mono', monospace; color: #EE8C3A; font-size: clamp(10px, 1.05vw, 12px); }

.ownerCell { font-weight: 700; }

.typeBadge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: clamp(8px, 0.82vw, 10px);
    font-weight: 800;
    text-transform: uppercase;
    white-space: nowrap;
}

.amount { font-family: 'Space Mono', monospace; font-size: clamp(10px, 1.1vw, 13px); font-weight: 700; }

.balance { font-family: 'Space Mono', monospace; font-size: clamp(9px, 0.95vw, 11px); opacity: 0.55; }

.recorder { display: inline-flex; align-items: center; gap: 5px; font-size: clamp(9px, 0.88vw, 11px); opacity: 0.65; }

.notesCell {
    font-style: italic;
    opacity: 0.55;
    max-width: 160px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: clamp(9px, 0.88vw, 11px);
}

.goBtn {
    background: rgba(238,140,58,0.1);
    border: 1px solid rgba(238,140,58,0.3);
    color: #EE8C3A;
    border-radius: 6px;
    padding: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    transition: all 0.2s;
}
.goBtn:hover { background: #EE8C3A; color: #1a2e30; }

.loading, .empty {
    text-align: center;
    padding: 60px 20px;
    color: rgba(255,255,255,0.35);
    font-weight: 700;
    font-size: clamp(12px, 1.3vw, 15px);
    text-transform: uppercase;
    letter-spacing: 1px;
}

@media (max-width: 768px) {
    .summaryRow { grid-template-columns: 1fr; }
    .filterRow { gap: 6px; }
    .filterBtn { padding: 5px 10px; font-size: 9px; }
    .searchWrap { max-width: 100%; }
}
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("All done.")