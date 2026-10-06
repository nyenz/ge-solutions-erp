// PATH: erp-frontend/src/components/layout/Sidebar.jsx
import { roleFlags } from '../../utils/roles';
import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
FiGrid, FiPlusSquare, FiLayers, FiPhoneCall,
    FiSettings, FiBarChart2, FiShield, FiDollarSign, FiTrendingDown, FiUsers, FiInbox
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { Tooltip } from '../common/Tooltip';
import styles from './Sidebar.module.css';

const Sidebar = ({ isCollapsed, onToggle, onLockedClick }) => {
    const { user }  = useAuth();
    const navigate  = useNavigate();

    const isMobile = () => typeof window !== 'undefined' && window.innerWidth <= 768;

    const isLocked           = user?.mustChangePassword;
    const flags              = roleFlags(user);   // fix181
    const hasHighLevelAccess = flags.isOwnerLevel;
    const hasManagerAccess   = flags.isManager;

    const navItems = [
        // fix181 (8.7c): the Employee sees only NEW PROJECT, MY ENTRIES and SETTINGS
        { path: '/dashboard',     label: 'DASHBOARD',   icon: <FiGrid         aria-hidden="true" />, access: flags.isStaff,       hint: 'Company-wide numbers at a glance' },
        { path: '/land/new',      label: 'NEW PROJECT', icon: <FiPlusSquare   aria-hidden="true" />, access: true,                hint: 'Start a new folder, title, or legacy title' },
        { path: '/my-entries',    label: 'MY ENTRIES',  icon: <FiInbox        aria-hidden="true" />, access: flags.isEmployee,    hint: 'The projects you entered, and what the office did with them' },
        { path: '/land/projects', label: 'LEDGER',      icon: <FiLayers       aria-hidden="true" />, access: flags.isStaff,       hint: 'Every project, searchable by stage, client and debt' },
        { path: '/recovery',      label: 'RECOVERY',    icon: <FiPhoneCall    aria-hidden="true" />, access: flags.isStaff,       hint: 'Who to call about money owed, and who is due today' },
        { path: '/clients',       label: 'CLIENTS',     icon: <FiUsers        aria-hidden="true" />, access: flags.isStaff,       hint: 'Client register and full dossiers' },
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

    /* Collapsing here, on the nav link's own click, used to make the panel
       vanish before the new page had even rendered. That auto-collapse now
       lives in Shell instead, keyed off the first click INSIDE the page
       content -- so picking a link still shows you where you landed with
       the panel open, and it only gets out of the way once you start
       actually working the page. */
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
                {/* fix183: the maker's mark. Same word open and collapsed, so nothing jumps when the panel moves. */}
                <footer className={styles.sidebarFooter} aria-label="Built by nyenz">
                    <div className={styles.branding} aria-hidden="true">nyenz</div>
                </footer>
            </aside>
        </>
    );
};

export default Sidebar;