// PATH: erp-frontend/src/components/layout/Sidebar.jsx
import React, { useEffect, useRef } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
    FiGrid, FiPlusSquare, FiLayers, FiPhoneCall,
    FiSettings, FiBarChart2, FiShield
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import styles from './Sidebar.module.css';

/**
 * NYENZ INDUSTRIAL SIDEBAR (V4.5)
 *
 * Shell passes:  isCollapsed={isCollapsed}  onToggle={handleSidebarToggle}
 *
 * Mobile auto-close: when the route changes on a mobile screen and the
 * sidebar is currently open, call onToggle() to collapse it.
 * No internal state — Shell owns the single source of truth.
 */
const Sidebar = ({ isCollapsed, onToggle, onLockedClick }) => {
    const { user }  = useAuth();
    const navigate  = useNavigate();
    const location  = useLocation();

    // Refs keep latest values readable inside effects without adding
    // them as dependencies — prevents the effect re-firing on every render.
    const isCollapsedRef = useRef(isCollapsed);
    const onToggleRef    = useRef(onToggle);
    useEffect(() => { isCollapsedRef.current = isCollapsed; }, [isCollapsed]);
    useEffect(() => { onToggleRef.current    = onToggle;    }, [onToggle]);

    const isMobile = () => typeof window !== 'undefined' && window.innerWidth <= 768;

    // Track the previous path so the effect only fires on genuine
    // navigation — NOT on the initial mount or on re-renders.
    const prevPathRef = useRef(location.pathname);

    useEffect(() => {
        const currentPath = location.pathname;
        const prevPath    = prevPathRef.current;

        // Only auto-close when the path actually changed (not on mount)
        if (currentPath !== prevPath) {
            prevPathRef.current = currentPath;
            if (isMobile() && !isCollapsedRef.current && typeof onToggleRef.current === 'function') {
                onToggleRef.current();
            }
        }
    }, [location.pathname]); // onToggle intentionally excluded — read via ref

    const isLocked           = user?.mustChangePassword;
    const hasHighLevelAccess = user?.isRoot || user?.role === 'ROLE_ADMIN';

    const navItems = [
        { path: '/dashboard',     label: 'DASHBOARD', icon: <FiGrid       aria-hidden="true" />, access: true },
        { path: '/land/new',      label: 'INTAKE',    icon: <FiPlusSquare aria-hidden="true" />, access: true },
        { path: '/land/projects', label: 'LEDGER',    icon: <FiLayers     aria-hidden="true" />, access: true },
        { path: '/recovery',      label: 'RECOVERY',  icon: <FiPhoneCall  aria-hidden="true" />, access: true },
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
                <div
                    className={styles.sidebarBackdrop}
                    onClick={() => typeof onToggle === 'function' && onToggle()}
                    aria-hidden="true"
                />
            )}

            <aside
                className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}
                aria-label="System navigation"
            >
                <nav className={styles.sidebarNav} aria-label="Main menu">
                    <div className={styles.navSection}>
                        <p className={styles.navSectionTitle} aria-hidden="true">
                            {isCollapsed ? 'SYS' : 'SYSTEM MODULES'}
                        </p>

                        {navItems.map(item => {
                            if (!item.access) return null;
                            const locked = isLocked && item.path !== '/settings';

                            return (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    aria-label={isCollapsed ? item.label : undefined}
                                    aria-disabled={locked ? 'true' : undefined}
                                    className={({ isActive }) =>
                                        [
                                            styles.navItem,
                                            isActive ? styles.active : '',
                                            locked   ? styles.navItemLocked : '',
                                        ].filter(Boolean).join(' ')
                                    }
                                    onClick={locked ? (e) => handleLockedClick(e, item) : undefined}
                                >
                                    <span className={styles.navIcon}>{item.icon}</span>
                                    {!isCollapsed && (
                                        <span className={styles.navText}>{item.label}</span>
                                    )}
                                </NavLink>
                            );
                        })}
                    </div>
                </nav>

                <footer className={styles.sidebarFooter} aria-label="NYENZ branding">
                    <div className={styles.branding} aria-hidden="true">NYENZ</div>
                    {!isCollapsed && (
                        <div className={styles.version} aria-hidden="true">V.2.0.1-PROD</div>
                    )}
                </footer>
            </aside>
        </>
    );
};

export default Sidebar;