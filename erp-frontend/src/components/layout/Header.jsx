import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiBell, FiLogOut } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import styles from './Header.module.css';

/**
 * GOLDEN SEED — SYSTEM STATUS HEADER
 * Optimized for performance and accurate role mapping.
 */
const Header = ({ onToggle }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [staleCount, setStaleCount] = useState(0);

    // Accurately map backend roles to clean display titles
    const displayRole = useMemo(() => {
        if (!user) return 'STAFF';
        if (user.isRoot) return 'FOUNDER';
        const roleMap = {
            'ROLE_ADMIN': 'ADMIN',
            'ROLE_DIRECTOR': 'DIRECTOR',
            'ROLE_MANAGER': 'MANAGER',
            'ROLE_SECRETARY': 'SECRETARY'
        };
        return roleMap[user.role] || 'STAFF';
    }, [user]);

    const initials = user?.username?.charAt(0).toUpperCase() || 'A';

    // Safely fetch the recovery bell count
    const fetchStaleCount = useCallback(async () => {
        try {
            const count = await recoveryService.getTaskCount();
            setStaleCount(count ?? 0);
        } catch {
            // Silently fail — badge just stays at 0 if API is unreachable
        }
    }, []);

    useEffect(() => {
        fetchStaleCount();
        const interval = setInterval(fetchStaleCount, 300000); // 5 minutes
        return () => clearInterval(interval);
    }, [fetchStaleCount]);

    const handleBellClick = useCallback(() => navigate('/recovery'), [navigate]);
    const handleLogout = useCallback(() => logout(), [logout]);

    return (
        <header className={styles.header}>
            <div className={styles.headerLeft}>
                <button
                    type="button"
                    className={styles.sidebarToggle}
                    onClick={onToggle}
                    aria-label="Toggle sidebar navigation"
                >
                    <FiMenu aria-hidden="true" />
                </button>

                <div className={styles.logoSection} aria-label="Golden Seed ERP">
                    <div className={styles.logoSmallPulse} aria-hidden="true">
                        <div className={styles.pulseInner}>🌱</div>
                        <div className={styles.pulseRing} />
                    </div>
                    <span className={styles.brandName}>GOLDEN SEED</span>
                </div>
            </div>

            <div className={styles.headerRight}>
                <button
                    type="button"
                    className={`${styles.notificationGroup} ${staleCount > 0 ? styles.activeSensor : ''}`}
                    onClick={handleBellClick}
                    aria-label={staleCount > 0
                        ? `${staleCount} recovery mission${staleCount > 1 ? 's' : ''} pending`
                        : 'Open recovery missions'
                    }
                >
                    <FiBell className={styles.bellIcon} aria-hidden="true" />
                    {staleCount > 0 && (
                        <span className={styles.badge} aria-hidden="true">
                            {staleCount > 99 ? '99+' : staleCount}
                        </span>
                    )}
                </button>

                <div className={styles.userCard} aria-label={`Logged in as ${user?.username}, ${displayRole}`}>
                    <div className={styles.avatar} aria-hidden="true">{initials}</div>
                    <div className={styles.userMeta}>
                        <span className={styles.userName}>{user?.username}</span>
                        <span className={styles.roleTag}>{displayRole}</span>
                    </div>
                </div>

                <button
                    type="button"
                    className={styles.logoutTrigger}
                    onClick={handleLogout}
                    aria-label="Sign out of session"
                >
                    <FiLogOut aria-hidden="true" />
                </button>
            </div>
        </header>
    );
};

export default Header;
