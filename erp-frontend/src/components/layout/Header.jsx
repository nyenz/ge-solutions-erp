// PATH: erp-frontend/src/components/layout/Header.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiBell, FiLogOut } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import styles from './Header.module.css';

/**
 * GOLDEN SEED — SYSTEM STATUS HEADER
 * ERP Standard compliant:
 * - clamp() on all fluid sizes
 * - DM Sans 900 / Space Mono 700-900 / Cinzel 700+ — no system fonts
 * - All icon-only buttons have aria-label
 * - All icons aria-hidden="true"
 * - notificationGroup is <button> not <div>
 * - activeSensor class defined
 * - try/catch on recoveryService
 * - focus-visible on all interactive elements
 */
const Header = ({ onToggle }) => {
    const { user, logout } = useAuth();
    const navigate         = useNavigate();
    const [staleCount, setStaleCount] = useState(0);

    const isRoot      = user?.isRoot;
    const displayRole = isRoot ? 'ROOT OWNER' : 'SYSTEM MANAGER';
    const initials    = user?.username?.charAt(0).toUpperCase() || 'A';

    useEffect(() => {
        const updateSensor = async () => {
            try {
                const count = await recoveryService.getTaskCount();
                setStaleCount(count ?? 0);
            } catch {
                // Non-fatal — badge simply stays at 0
            }
        };
        updateSensor();
        const interval = setInterval(updateSensor, 300000);
        return () => clearInterval(interval);
    }, []);

    return (
        <header className={styles.header}>
            <div className={styles.headerLeft}>
                <button
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
                {/* Recovery mission sensor — navigates to /recovery */}
                <button
                    className={`${styles.notificationGroup} ${staleCount > 0 ? styles.activeSensor : ''}`}
                    onClick={() => navigate('/recovery')}
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
                    className={styles.logoutTrigger}
                    onClick={logout}
                    aria-label="Sign out of session"
                >
                    <FiLogOut aria-hidden="true" />
                </button>
            </div>
        </header>
    );
};

export default Header;