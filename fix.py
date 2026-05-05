import os

files = {}

# ── 1. SIDEBAR — add Payments page ──────────────────────────────────
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

# ── 2. APP.JSX — add /payments route ────────────────────────────────
files["erp-frontend/src/App.jsx"] = """\
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
"""

# ── 3. NEW PAYMENTS PAGE ─────────────────────────────────────────────
os.makedirs("erp-frontend/src/pages/Payments", exist_ok=True)

files["erp-frontend/src/pages/Payments/PaymentsPage.jsx"] = """\
// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDollarSign, FiSearch, FiX, FiFilter,
    FiChevronRight, FiAlertOctagon, FiClock, FiUser
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
    const [payments,    setPayments]    = useState([]);
    const [loading,     setLoading]     = useState(true);
    const [searchTerm,  setSearchTerm]  = useState('');
    const [typeFilter,  setTypeFilter]  = useState('ALL');
    const [sortDir,     setSortDir]     = useState('desc');

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

    const titlePayments   = filtered.filter(p => p.paymentType !== 'BACKLOG_PARTIAL');
    const storagePayments = filtered.filter(p => p.paymentType === 'BACKLOG_PARTIAL');

    const titleTotal   = titlePayments.reduce((s, p) => s + Number(p.amountPaid || 0), 0);
    const storageTotal = storagePayments.reduce((s, p) => s + Number(p.amountPaid || 0), 0);

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div>
                    <h1 className={styles.title}>PAYMENTS</h1>
                    <p className={styles.subtitle}>All payment records — title payments and storage fee collections</p>
                </div>
            </header>

            {/* SUMMARY CARDS */}
            <div className={styles.summaryRow}>
                <div className={styles.sumCard}>
                    <label>TOTAL SHOWN</label>
                    <strong>UGX {fmt(totalCollected)}</strong>
                    <span>{filtered.length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#22c55e' }}>
                    <label style={{ color: '#22c55e' }}>TITLE PAYMENTS</label>
                    <strong style={{ color: '#22c55e' }}>UGX {fmt(titleTotal)}</strong>
                    <span>{titlePayments.length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#ef4444' }}>
                    <label style={{ color: '#ef4444' }}>STORAGE FEE COLLECTIONS</label>
                    <strong style={{ color: '#ef4444' }}>UGX {fmt(storageTotal)}</strong>
                    <span>{storagePayments.length} records</span>
                </div>
            </div>

            {/* CONTROLS */}
            <div className={styles.controls}>
                <div className={styles.searchWrap}>
                    <FiSearch className={styles.searchIcon} />
                    <input type="search" className={styles.searchInput}
                        placeholder="Search plot, owner, recorded by..."
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                    {searchTerm && (
                        <button className={styles.clearBtn} onClick={() => setSearchTerm('')}>
                            <FiX />
                        </button>
                    )}
                </div>
                <div className={styles.filterRow}>
                    {['ALL','STANDARD','INITIAL_DEPOSIT','BACKLOG_PARTIAL'].map(t => (
                        <button key={t}
                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}
                            onClick={() => setTypeFilter(t)}>
                            {t === 'ALL' ? 'ALL' : TYPE_LABELS[t] || t}
                        </button>
                    ))}
                    <button className={styles.filterBtn} onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
                        DATE {sortDir === 'desc' ? '\u2193' : '\u2191'}
                    </button>
                </div>
            </div>

            {/* TABLE */}
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
                                <th>AMOUNT</th>
                                <th>BALANCE AFTER</th>
                                <th>RECORDED BY</th>
                                <th>NOTES</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((pay, i) => (
                                <tr key={pay.id || i} className={styles.row}>
                                    <td className={styles.dateCell}>
                                        {new Date(pay.timestamp).toLocaleDateString()}
                                        <span className={styles.time}>
                                            {new Date(pay.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </td>
                                    <td className={styles.plotCell}>
                                        <strong>{pay.plotNumber || '---'}</strong>
                                    </td>
                                    <td>{pay.ownerName || '---'}</td>
                                    <td>
                                        <span className={styles.typeBadge} style={{
                                            background: `${TYPE_COLORS[pay.paymentType]}22`,
                                            color: TYPE_COLORS[pay.paymentType],
                                            border: `1px solid ${TYPE_COLORS[pay.paymentType]}44`
                                        }}>
                                            {pay.paymentType === 'BACKLOG_PARTIAL' && <FiAlertOctagon size={10} />}
                                            {TYPE_LABELS[pay.paymentType] || pay.paymentType}
                                        </span>
                                    </td>
                                    <td className={styles.amountCell}>
                                        <strong style={{ color: TYPE_COLORS[pay.paymentType] }}>
                                            UGX {fmt(pay.amountPaid)}
                                        </strong>
                                    </td>
                                    <td className={styles.balanceCell}>
                                        {pay.balanceAfter != null ? `UGX ${fmt(pay.balanceAfter)}` : '---'}
                                    </td>
                                    <td>
                                        <span className={styles.recorder}>
                                            <FiUser size={11} /> {pay.recordedBy}
                                        </span>
                                    </td>
                                    <td className={styles.notesCell}>
                                        {pay.notes || '---'}
                                    </td>
                                    <td>
                                        {pay.projectId && (
                                            <button className={styles.goBtn}
                                                onClick={() => navigate(`/folder/${pay.projectId}`)}>
                                                <FiChevronRight size={14} />
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

files["erp-frontend/src/pages/Payments/PaymentsPage.module.css"] = """\
/* PATH: erp-frontend/src/pages/Payments/PaymentsPage.module.css */
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(12px, 2vw, 24px);
    color: #fff;
    font-family: 'DM Sans', sans-serif;
}

.header {
    border-left: 4px solid #EE8C3A;
    padding: clamp(10px, 1.5vw, 16px) clamp(14px, 2vw, 24px);
    background: rgba(255,255,255,0.55);
    border-radius: 0 10px 10px 0;
    backdrop-filter: blur(15px);
    margin-bottom: clamp(14px, 2vw, 24px);
}

.title {
    font-family: 'Cinzel', serif;
    color: #1a2e30;
    font-size: clamp(16px, 2.4vw, 24px);
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

.summaryRow {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: clamp(10px, 1.5vw, 16px);
    margin-bottom: clamp(14px, 2vw, 20px);
}

.sumCard {
    background: linear-gradient(160deg, #1c3335, #213E40);
    border: 1.5px solid rgba(238,140,58,0.25);
    border-radius: 10px;
    padding: clamp(12px, 1.6vw, 18px);
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.sumCard label {
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 900;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.sumCard strong {
    font-family: 'Space Mono', monospace;
    font-size: clamp(14px, 1.8vw, 20px);
    color: #fff;
    font-weight: 700;
}

.sumCard span {
    font-size: clamp(9px, 0.9vw, 11px);
    color: rgba(255,255,255,0.35);
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
    height: clamp(38px, 4.5vw, 44px);
    max-width: 500px;
    transition: border-color 0.2s;
}

.searchWrap:focus-within {
    border-color: #EE8C3A;
    box-shadow: 0 0 0 3px rgba(238,140,58,0.15);
}

.searchIcon {
    position: absolute;
    left: 12px;
    color: #EE8C3A;
    font-size: 16px;
    pointer-events: none;
}

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
    transition: color 0.15s;
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
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}

.filterBtn:hover { border-color: #EE8C3A; color: #EE8C3A; }

.filterActive {
    background: #EE8C3A;
    border-color: #EE8C3A;
    color: #1a2e30;
}

.tableWrap {
    overflow-x: auto;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
    background: linear-gradient(160deg, #1c3335, #213E40);
}

.table {
    width: 100%;
    border-collapse: collapse;
    font-size: clamp(10px, 1.1vw, 13px);
    min-width: 700px;
}

.table thead tr {
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

.table th {
    padding: clamp(10px, 1.3vw, 14px) clamp(12px, 1.5vw, 16px);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.85vw, 10px);
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
    text-align: left;
    white-space: nowrap;
}

.row {
    border-bottom: 1px solid rgba(255,255,255,0.04);
    transition: background 0.15s;
    cursor: default;
}

.row:hover { background: rgba(255,255,255,0.03); }

.table td {
    padding: clamp(10px, 1.3vw, 14px) clamp(12px, 1.5vw, 16px);
    color: rgba(255,255,255,0.85);
    vertical-align: middle;
}

.dateCell {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-weight: 700;
    white-space: nowrap;
}

.time {
    font-size: 10px;
    opacity: 0.5;
}

.plotCell strong {
    font-family: 'Space Mono', monospace;
    color: #EE8C3A;
    font-size: clamp(10px, 1.1vw, 13px);
}

.typeBadge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 800;
    text-transform: uppercase;
    white-space: nowrap;
}

.amountCell strong {
    font-family: 'Space Mono', monospace;
    font-size: clamp(11px, 1.2vw, 14px);
    font-weight: 700;
}

.balanceCell {
    font-family: 'Space Mono', monospace;
    font-size: clamp(10px, 1vw, 12px);
    opacity: 0.6;
}

.recorder {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: clamp(9px, 0.9vw, 11px);
    opacity: 0.7;
}

.notesCell {
    font-style: italic;
    opacity: 0.6;
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: clamp(9px, 0.9vw, 11px);
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

.goBtn:hover {
    background: #EE8C3A;
    color: #1a2e30;
}

.loading, .empty {
    text-align: center;
    padding: 60px 20px;
    color: rgba(255,255,255,0.4);
    font-weight: 700;
    font-size: clamp(12px, 1.3vw, 15px);
    text-transform: uppercase;
    letter-spacing: 1px;
}

@media (max-width: 768px) {
    .summaryRow { grid-template-columns: 1fr; }
    .filterRow { gap: 6px; }
    .filterBtn { padding: 5px 10px; font-size: 9px; }
}
"""

# ── 4. BACKEND — payments endpoint ──────────────────────────────────
files["erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PaymentController.java"] = """\
// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PaymentController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.*;

@RestController
@RequestMapping("/api/v1/recovery/payments")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN')")
public class PaymentController {

    private final PaymentRecordRepository paymentRecordRepository;
    private final LandProjectRepository projectRepository;

    @GetMapping("/all")
    public ResponseEntity<List<Map<String, Object>>> getAllPayments(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "200") int size) {

        List<PaymentRecord> records = paymentRecordRepository.findAll(
                PageRequest.of(page, size, Sort.by("timestamp").descending())
        ).getContent();

        List<Map<String, Object>> result = new ArrayList<>();

        for (PaymentRecord pay : records) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id",          pay.getId());
            row.put("projectId",   pay.getProjectId());
            row.put("amountPaid",  pay.getAmountPaid());
            row.put("paymentType", pay.getPaymentType());
            row.put("recordedBy",  pay.getRecordedBy());
            row.put("notes",       pay.getNotes());
            row.put("balanceAfter",pay.getBalanceAfter());
            row.put("timestamp",   pay.getTimestamp());

            // Enrich with plot and owner info
            try {
                LandProject project = projectRepository.findById(pay.getProjectId()).orElse(null);
                if (project != null) {
                    row.put("plotNumber", project.getLandTitle().getPlotNumber());
                    String ownerName = project.getProprietors().stream()
                            .findFirst()
                            .map(c -> c.getFullName())
                            .orElse("---");
                    row.put("ownerName", ownerName);
                }
            } catch (Exception e) {
                row.put("plotNumber", "---");
                row.put("ownerName", "---");
            }

            result.add(row);
        }

        return ResponseEntity.ok(result);
    }
}
"""

# ── 5. SCHEDULER FIX — 30 days from backlog start, not 1st of month ─
files["erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerService.java"] = """\
// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BacklogSchedulerService {

    private final LandProjectRepository projectRepository;
    private final AuditService auditService;

    private static final BigDecimal MONTHLY_STORAGE_FEE = new BigDecimal("50000");

    // Runs every day at midnight
    // Adds 50,000 UGX to every backlog plot that is due for a monthly fee
    // "Due" means: 30 days have passed since backlogStartDate (or last fee was applied)
    // This replaces the old 1st-of-month scheduler
    @Scheduled(cron = "0 0 0 * * *")
    @Transactional
    public void applyMonthlyStorageFees() {
        List<LandProject> backlogPlots = projectRepository.findAllBacklogPlots();
        LocalDateTime now = LocalDateTime.now();

        for (LandProject plot : backlogPlots) {
            if (plot.getBacklogStartDate() == null) continue;

            // How many 30-day periods have passed since backlog started?
            long daysSinceBacklog = ChronoUnit.DAYS.between(plot.getBacklogStartDate(), now);
            long periodsOwed = daysSinceBacklog / 30;

            if (periodsOwed <= 0) continue;

            // How many fees have already been applied?
            // We calculate this from storageFeesAccumulated / 50000
            BigDecimal currentFees = plot.getStorageFeesAccumulated() != null
                    ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;
            long feesAlreadyApplied = currentFees.divide(MONTHLY_STORAGE_FEE, 0, java.math.RoundingMode.DOWN).longValue();

            if (feesAlreadyApplied >= periodsOwed) continue;

            // Apply the missing fee periods
            long feesMissing = periodsOwed - feesAlreadyApplied;
            BigDecimal toAdd = MONTHLY_STORAGE_FEE.multiply(BigDecimal.valueOf(feesMissing));

            plot.setStorageFeesAccumulated(currentFees.add(toAdd));
            projectRepository.save(plot);

            auditService.logAction("STORAGE_FEE_APPLIED",
                "SYSTEM: Added UGX " + toAdd + " storage fee to backlog plot: "
                + plot.getLandTitle().getPlotNumber()
                + " (" + feesMissing + " month(s) at UGX 50,000)"
                + " | Total fees now: UGX " + plot.getStorageFeesAccumulated());
        }
    }

    // Runs every day at 6:00 AM
    // Auto-flags plots with no payment for 365+ days as backlog
    @Scheduled(cron = "0 0 6 * * *")
    @Transactional
    public void autoFlagStaleAsBacklog() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(365);
        List<LandProject> candidates = projectRepository.findAutoBacklogCandidates(cutoff);

        for (LandProject plot : candidates) {
            BigDecimal outstanding = plot.getTotalCost().subtract(plot.getAmountPaid());
            if (outstanding.compareTo(BigDecimal.ZERO) <= 0) continue;

            plot.setBacklog(true);
            plot.setBacklogStartDate(LocalDateTime.now());
            plot.setOriginalDebt(outstanding);
            plot.setStorageFeesAccumulated(BigDecimal.ZERO);
            plot.setStatus("BACKLOG");
            projectRepository.save(plot);

            auditService.logAction("AUTO_BACKLOG",
                "SYSTEM: Plot " + plot.getLandTitle().getPlotNumber()
                + " auto-flagged as BACKLOG after 365 days of no payment. "
                + "Original debt frozen at: UGX " + outstanding);
        }
    }
}
"""

# ── 6. RECOVERY PORTAL CSS — compact cards, contrast fixes ──────────
files["erp-frontend/src/pages/Recovery/RecoveryPortal.module.css"] = """\
/* PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --red:           #ef4444;
    --emerald:       #10b981;
    --cyan:          #06b6d4;
    --gap-xl:    clamp(12px, 1.8vw, 20px);
    --gap-lg:    clamp(8px,  1.2vw, 14px);
    --gap-md:    clamp(6px,  0.9vw, 11px);
    --pad-card:  clamp(12px, 1.6vw, 18px);
    --radius:    10px;
    --radius-sm: 7px;
    --fs-h1:     clamp(16px, 2.2vw, 22px);
    --fs-label:  clamp(8px,  0.82vw, 10px);
    --fs-meta:   clamp(9px,  0.9vw, 11px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-phone:  clamp(11px, 1.15vw, 13px);
    --fs-owner:  clamp(13px, 1.5vw, 17px);
    --fs-demand: clamp(13px, 1.6vw, 18px);
    --fs-badge:  clamp(7px,  0.75vw, 9px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);
    --fs-note:   clamp(10px, 1vw, 12px);
    max-width: 1600px;
    margin: 0 auto;
    padding: clamp(8px, 1.5vw, 16px) clamp(8px, 1.5vw, 16px) clamp(24px, 4vw, 48px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
}

/* TOAST */
.toastContainer { position: fixed; bottom: clamp(16px, 2.5vh, 28px); right: clamp(12px, 1.8vw, 22px); z-index: 99999; display: flex; flex-direction: column-reverse; gap: 8px; max-width: clamp(260px, 88vw, 380px); pointer-events: none; }
.toast { display: flex; align-items: flex-start; gap: 10px; padding: 12px 14px; border-radius: 8px; box-shadow: 0 6px 22px rgba(0,0,0,0.5); pointer-events: all; }
.toast_success { background: rgba(16,185,129,0.95); border-left: 4px solid #059669; color: #fff; }
.toast_error   { background: rgba(239,68,68,0.95);  border-left: 4px solid #b91c1c; color: #fff; }
.toast_warn    { background: rgba(245,158,11,0.95); border-left: 4px solid #b45309; color: #fff; }
.toast_info    { background: rgba(6,182,212,0.95);  border-left: 4px solid #0369a1; color: #fff; }
.toastIcon  { font-size: 15px; flex-shrink: 0; margin-top: 1px; }
.toastMsg   { font-family: 'Space Mono', monospace; font-size: 10px; font-weight: 700; line-height: 1.4; flex: 1; min-width: 0; word-break: break-word; }
.toastClose { background: transparent; border: none; color: inherit; opacity: 0.6; cursor: pointer; padding: 2px; font-size: 13px; flex-shrink: 0; }
.toastClose:hover { opacity: 1; }

/* BOOT */
.bootScreen  { height: 60vh; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; }
.bootSpinner { width: 36px; height: 36px; border: 3px solid rgba(238,140,58,0.15); border-top-color: #EE8C3A; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.bootLabel   { font-family: 'Cinzel', serif; font-size: 11px; font-weight: 700; letter-spacing: 4px; color: #EE8C3A; text-transform: uppercase; }

/* HEADER */
.header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--gap-md); margin-bottom: var(--gap-xl); border-left: 4px solid var(--orange); padding: clamp(10px, 1.3vw, 14px) clamp(14px, 2vw, 22px); background: rgba(255,255,255,0.55); border-radius: 0 var(--radius) var(--radius) 0; backdrop-filter: blur(15px); }
.titleBlock { display: flex; flex-direction: column; gap: 8px; }
.title { font-family: 'Cinzel', serif; color: var(--navy); font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0; }
.modeSwitch { display: inline-flex; background: var(--navy); padding: 4px; border-radius: var(--radius-sm); border: 1px solid var(--orange-border); gap: 3px; }
.modeActive   { background: var(--orange); color: var(--navy); border: none; padding: 7px 16px; border-radius: 5px; font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: var(--fs-btn); letter-spacing: 1px; text-transform: uppercase; cursor: pointer; display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.modeInactive { background: transparent; color: rgba(255,255,255,0.5); border: none; padding: 7px 16px; border-radius: 5px; font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: var(--fs-btn); letter-spacing: 1px; text-transform: uppercase; cursor: pointer; display: flex; align-items: center; gap: 6px; white-space: nowrap; transition: background 0.2s, color 0.2s; }
.modeInactive:hover { background: rgba(255,255,255,0.06); color: #fff; }
.hudStats { display: flex; gap: var(--gap-md); }
.statBox { background: var(--navy); padding: 8px 18px; border-radius: var(--radius-sm); border: 1px solid var(--orange-border); text-align: center; }
.statBox label { display: block; font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.4); font-size: var(--fs-label); font-weight: 900; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 1px; }
.statBox strong { font-family: 'Space Mono', monospace; font-size: clamp(15px, 1.8vw, 20px); color: #fff; line-height: 1; }

/* SEARCH */
.filterBar { margin-bottom: var(--gap-xl); }
.searchInner { position: relative; display: flex; align-items: center; background: #fff; border: 1.5px solid #c8d6d7; border-radius: var(--radius-sm); width: 100%; max-width: clamp(300px, 42vw, 520px); height: clamp(36px, 4vw, 42px); transition: border-color 0.2s; }
.searchInner:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238,140,58,0.15); }
.searchIcon { position: absolute; left: 12px; color: var(--orange); font-size: 16px; pointer-events: none; }
.searchInput { width: 100%; border: none; outline: none; background: transparent; color: var(--navy); padding: 0 34px 0 38px; font-family: 'DM Sans', sans-serif; font-weight: 800; font-size: clamp(11px, 1.1vw, 13px); }
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.searchClear { position: absolute; right: 8px; background: transparent; border: none; cursor: pointer; color: rgba(26,46,48,0.4); display: flex; align-items: center; padding: 3px; border-radius: 4px; }
.searchClear:hover { color: var(--navy); }

/* SECTION GROUPS */
.sectionGroup { margin-bottom: var(--gap-xl); }
.sectionHeader { font-family: 'DM Sans', sans-serif; font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 2px; margin-bottom: var(--gap-lg); display: flex; align-items: center; gap: 8px; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
.sectionHeaderBacklog { color: #fca5a5; border-bottom-color: rgba(239,68,68,0.2); }

/* MISSION GRID */
.missionGrid { display: flex; flex-direction: column; gap: var(--gap-md); }

/* MISSION CARD */
.missionCard {
    background: var(--panel-bg);
    border: 1.5px solid rgba(238,140,58,0.2);
    border-radius: var(--radius);
    box-shadow: 0 4px 14px rgba(0,0,0,0.2);
    transition: border-color 0.2s, box-shadow 0.2s;
    overflow: hidden;
    outline: none;
    width: 100%;
}
.missionCard:hover { border-color: rgba(238,140,58,0.4); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.missionCard:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.cardLocked  { opacity: 0.75; filter: grayscale(0.5); border-style: dashed; }
.cardBacklog { border-color: rgba(239,68,68,0.3); }
.cardBacklog:hover { border-color: rgba(239,68,68,0.55); }

/* STATUS BADGE */
.statusBadge { display: flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 0 0 0 6px; font-family: 'DM Sans', sans-serif; font-size: var(--fs-badge); font-weight: 900; letter-spacing: 1px; text-transform: uppercase; float: right; margin-bottom: -1px; }
.statusRed   { background: #7f1d1d; color: #fca5a5; }
.statusBlue  { background: #0c4a6e; color: #67e8f9; }
.statusGrey  { background: #27272a; color: #94a3b8; }
.statusDefault { background: rgba(0,0,0,0.4); color: rgba(255,255,255,0.5); }
.backlogTag  { background: rgba(239,68,68,0.2); color: #fca5a5; border-radius: 3px; padding: 1px 5px; font-size: 8px; margin-left: 4px; }

/* CARD HEADER */
.cardHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(10px, 1.2vw, 14px) var(--pad-card);
    cursor: pointer;
    user-select: none;
    clear: both;
}
.identity { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
.ownerName { font-family: 'Cinzel', serif; color: #fff; font-size: var(--fs-owner); font-weight: 700; margin: 0; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.phoneNum  { font-family: 'Space Mono', monospace; color: var(--orange); font-weight: 900; font-size: var(--fs-phone); letter-spacing: 0.5px; }
.totalDemandRow { display: flex; align-items: center; gap: 8px; }
.demandLabel { font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; }
.demandValue { font-family: 'Space Mono', monospace; font-size: var(--fs-demand); color: #fff; font-weight: 700; }
.feesRow { display: flex; align-items: center; gap: 5px; font-size: var(--fs-label); color: #fca5a5; font-weight: 800; }
.expandIcon { color: rgba(255,255,255,0.35); font-size: 18px; transition: color 0.2s; flex-shrink: 0; margin-left: 12px; }
.missionCard:hover .expandIcon { color: var(--orange); }

/* CARD BODY */
.cardBody { padding: 0 var(--pad-card) var(--pad-card); }
.divider  { height: 1px; background: linear-gradient(90deg, var(--orange), transparent); margin: 10px 0; opacity: 0.15; }

.timingRow { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; font-size: var(--fs-meta); color: rgba(255,255,255,0.7); font-weight: 700; margin-bottom: 10px; background: rgba(0,0,0,0.2); padding: 8px 10px; border-radius: 6px; }
.timingRow strong { color: #fff; }

/* PLOTS LIST */
.plotsList { display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
.plotsHeader { font-family: 'DM Sans', sans-serif; font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px; }
.plotRow { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px 12px; border-left: 3px solid rgba(238,140,58,0.3); }
.plotRowBacklog { border-left-color: rgba(239,68,68,0.5); background: rgba(239,68,68,0.05); }
.plotRowLeft { display: flex; align-items: flex-start; gap: 8px; flex: 1; min-width: 0; }
.plotInfo { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
.plotNumber { font-family: 'Space Mono', monospace; color: var(--orange); font-size: clamp(11px, 1.1vw, 13px); font-weight: 700; }
.plotBox    { font-size: var(--fs-meta); color: rgba(255,255,255,0.5); font-weight: 700; }
.backlogBreakdown { display: flex; flex-direction: column; gap: 2px; }
.backlogPlotTag { display: inline-flex; align-items: center; gap: 4px; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); border-radius: 4px; padding: 2px 6px; font-size: 9px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; width: fit-content; }
.debtLine   { font-size: var(--fs-meta); color: rgba(255,255,255,0.75); font-weight: 700; }
.debtLine strong { color: #fff; }
.activePlotFinance { font-size: var(--fs-meta); color: rgba(255,255,255,0.75); font-weight: 700; }
.activePlotFinance strong { color: #fff; }
.lastNote { display: flex; align-items: flex-start; gap: 5px; font-size: var(--fs-label); color: rgba(255,255,255,0.4); font-style: italic; margin-top: 4px; font-weight: 600; }
.plotRowActions { display: flex; flex-direction: column; gap: 5px; flex-shrink: 0; }

/* CARD ACTIONS */
.cardActions { display: flex; gap: var(--gap-md); margin-top: 10px; }
.logCallBtn { flex: 1; background: var(--orange); color: var(--navy); font-family: 'DM Sans', sans-serif; font-weight: 900; border-radius: var(--radius-sm); font-size: var(--fs-btn); text-transform: uppercase; letter-spacing: 1px; padding: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 7px; border: 2px solid var(--orange); transition: background 0.2s; }
.logCallBtn:hover:not(:disabled) { background: #d4732a; border-color: #d4732a; }
.logCallBtn:disabled { background: transparent; color: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.1); cursor: not-allowed; }
.folderBtn { background: rgba(255,255,255,0.06); border: 1.5px solid rgba(255,255,255,0.15); color: #fff; font-family: 'DM Sans', sans-serif; font-weight: 900; border-radius: var(--radius-sm); font-size: var(--fs-btn); padding: 7px 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px; transition: all 0.2s; white-space: nowrap; }
.folderBtn:hover { border-color: var(--orange); color: var(--orange); }
.payBtn { background: rgba(34,197,94,0.1); border: 1.5px solid rgba(34,197,94,0.3); color: #22c55e; font-family: 'DM Sans', sans-serif; font-weight: 900; border-radius: var(--radius-sm); font-size: var(--fs-btn); padding: 7px 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px; transition: all 0.2s; white-space: nowrap; }
.payBtn:hover { background: #22c55e; color: #1a2e30; }

/* EMPTY */
.emptyGate  { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; padding: 60px 20px; text-align: center; }
.emptyIcon  { font-size: 50px; color: var(--emerald); opacity: 0.25; }
.emptyTitle { font-family: 'Cinzel', serif; font-size: clamp(13px, 1.6vw, 18px); font-weight: 700; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 1.5px; margin: 0; }

/* MODAL */
.modalBody      { padding-top: 10px; }
.historyStream  { max-height: 180px; overflow-y: auto; background: #fff; border-radius: 8px; padding: 12px; margin-bottom: 14px; scrollbar-width: thin; }
.historyTitle   { font-family: 'DM Sans', sans-serif; font-size: 9px; font-weight: 900; color: #94a3b8; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
.historyItem    { border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 8px; }
.historyItem:last-child { border-bottom: none; margin-bottom: 0; }
.historyMeta    { display: flex; justify-content: space-between; align-items: center; font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 800; color: #EE8C3A; margin-bottom: 4px; }
.historyItem p  { font-family: 'DM Sans', sans-serif; font-size: 12px; color: #1a2e30; line-height: 1.5; font-weight: 600; margin: 0; }
.emptyHistory   { font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 700; color: rgba(26,46,48,0.4); text-align: center; padding: 20px 0; }
.notebookArea   { width: 100%; min-height: 90px; background: #fff; border-radius: 8px; border: 1.5px solid rgba(238,140,58,0.5); padding: 10px 12px; color: #1a2e30; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600; resize: vertical; box-sizing: border-box; display: block; outline: none; transition: box-shadow 0.2s; }
.notebookArea:focus { box-shadow: 0 0 0 3px rgba(238,140,58,0.2); }
.notebookArea::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.modalFooter    { margin-top: 12px; display: flex; justify-content: flex-end; }

.backlogPayInfo  { display: flex; align-items: flex-start; gap: 12px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 14px; margin-bottom: 14px; font-size: 13px; color: rgba(255,255,255,0.85); }
.activePayInfo   { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.25); border-radius: 8px; padding: 12px; margin-bottom: 14px; font-size: 13px; color: rgba(255,255,255,0.85); }

/* RESPONSIVE */
@media (max-width: 768px) {
    .header { flex-direction: column; align-items: flex-start; }
    .hudStats { width: 100%; }
    .modeSwitch { width: 100%; }
    .modeActive, .modeInactive { flex: 1; justify-content: center; }
    .plotRow { flex-direction: column; }
    .plotRowActions { flex-direction: row; }
    .cardActions { flex-direction: column; }
}

@media (max-width: 480px) {
    .statusBadge { font-size: 7px; padding: 2px 7px; }
    .cardHeader  { padding: 9px 11px; }
    .cardBody    { padding: 0 11px 11px; }
    .ownerName   { font-size: 13px; }
    .demandValue { font-size: 13px; }
    .historyStream { max-height: 110px; }
}
"""

# ── WRITE ALL FILES ──────────────────────────────────────────────────
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("All done.")