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
        { path: '/land/new',      label: 'NEW PLOT',  icon: <FiPlusSquare aria-hidden="true" />, access: true },
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