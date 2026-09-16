// PATH: erp-frontend/src/components/layout/Sidebar.jsx
import React, { useEffect, useRef } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
FiGrid, FiPlusSquare, FiLayers, FiPhoneCall,
    FiSettings, FiBarChart2, FiShield, FiDollarSign, FiTrendingDown, FiUsers
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { Tooltip } from '../common/Tooltip';
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
    const hasHighLevelAccess = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';
    const hasManagerAccess   = hasHighLevelAccess || user?.role === 'ROLE_MANAGER';

    const navItems = [
        { path: '/dashboard',     label: 'DASHBOARD',   icon: <FiGrid         aria-hidden="true" />, access: true,                hint: 'Company-wide numbers at a glance' },
        { path: '/land/new',      label: 'NEW PROJECT', icon: <FiPlusSquare   aria-hidden="true" />, access: true,                hint: 'Start a new folder, title, or legacy title' },
        { path: '/land/projects', label: 'LEDGER',      icon: <FiLayers       aria-hidden="true" />, access: true,                hint: 'Every project, searchable by stage, client and debt' },
        { path: '/recovery',      label: 'RECOVERY',    icon: <FiPhoneCall    aria-hidden="true" />, access: true,                hint: 'Who to call about money owed, and who is due today' },
        { path: '/clients',       label: 'CLIENTS',     icon: <FiUsers        aria-hidden="true" />, access: true,                hint: 'Client register and full dossiers' },
        { path: '/payments',      label: 'PAYMENTS',    icon: <FiDollarSign   aria-hidden="true" />, access: hasHighLevelAccess,  hint: 'Every payment received, across all projects' },
        { path: '/financials',    label: 'EXPENSES',    icon: <FiTrendingDown aria-hidden="true" />, access: hasManagerAccess,    hint: "The company's own costs -- not project costs" },
        { path: '/reports',       label: 'REPORTS',     icon: <FiBarChart2    aria-hidden="true" />, access: hasHighLevelAccess,  hint: 'Exportable reports across the whole company' },
        { path: '/audit',         label: 'AUDIT',       icon: <FiShield       aria-hidden="true" />, access: hasHighLevelAccess,  hint: 'Who did what, and when' },
        { path: '/settings',      label: 'SETTINGS',    icon: <FiSettings     aria-hidden="true" />, access: true,                hint: 'Your password, staff accounts, deleted plots' },
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
                            // Collapsed, these are nine unlabelled icons. Expanded, the
                            // label is already on screen, so the tooltip explains what
                            // the module is FOR instead of just repeating the name.
                            const tip = locked
                                ? item.label + ' -- locked until you change your password'
                                : (isCollapsed ? item.label : item.hint);
                            return (
                                <Tooltip key={item.path} label={tip} placement="bottom" block>
                                    <NavLink to={item.path}
                                        aria-label={isCollapsed ? item.label : undefined}
                                        aria-disabled={locked ? 'true' : undefined}
                                        className={({ isActive }) =>
                                            [styles.navItem, isActive ? styles.active : '', locked ? styles.navItemLocked : ''].filter(Boolean).join(' ')
                                        }
                                        onClick={locked ? (e) => handleLockedClick(e, item) : undefined}>
                                        <span className={styles.navIcon}>{item.icon}</span>
                                        {!isCollapsed && <span className={styles.navText}>{item.label}</span>}
                                    </NavLink>
                                </Tooltip>
                            );
                        })}
                    </div>
                </nav>
                <footer className={styles.sidebarFooter} aria-label="Golden Seed branding">
                    <div className={styles.branding} aria-hidden="true">GOLDEN SEED</div>
                    {!isCollapsed && <div className={styles.version} aria-hidden="true">V.2.0.1-PROD</div>}
                </footer>
            </aside>
        </>
    );
};

export default Sidebar;