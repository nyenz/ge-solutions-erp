// PATH: erp-frontend/src/components/layout/Header.jsx
/**
 * GOLDEN SEED -- HEADER / NOTIFICATION CENTRE
 *
 * WHAT CHANGED AND WHY (fix71)
 *
 * The bell used to render every signal as the same grey row with a coloured
 * dot and no timestamp, cap the list at twelve with nothing to say there were
 * more, and navigate everything that was not a PROJECT to /recovery. So the
 * two questions you actually ask a notification list -- "what kind of thing is
 * this" and "when did it happen" -- were both unanswerable, and half the rows
 * went to the wrong page.
 *
 * Now: every row carries its type's own icon and label from the notification
 * catalog, a relative timestamp, and a destination chosen from its entityType.
 * The list can be filtered to unread or to one group, which is the difference
 * between a bell you check and a bell you turn off.
 *
 * POLLING is the user's choice (Settings -> Behaviour). Five minutes is the
 * default; a phone on mobile data can drop to fifteen, and MANUAL stops the
 * timer entirely and leaves the refresh button. The old build hard-coded five
 * minutes with no way to change it.
 */
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiBell, FiLogOut, FiCheck, FiRefreshCw, FiPhoneCall } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { usePreferences } from '../../context/usePreferences';
import recoveryService from '../../services/recoveryService';
import { describe, routeFor, relativeTime, SEVERITY_COLOR, FILTERS } from '../common/notificationCatalog';
import styles from './Header.module.css';

const VISIBLE_LIMIT = 40;

const Header = ({ onToggle }) => {
    const { user, logout } = useAuth();
    const { prefs } = usePreferences();
    const navigate = useNavigate();

    const [staleCount, setStaleCount] = useState(0);
    const [notifOpen, setNotifOpen] = useState(false);
    const [notifs, setNotifs] = useState([]);
    const [unread, setUnread] = useState(0);
    const [filter, setFilter] = useState('ALL');
    const [loading, setLoading] = useState(false);
    const dropRef = useRef(null);

    const isRoot = user?.isRoot;
    const roleMap = { ROLE_ADMIN: 'ADMIN', ROLE_DIRECTOR: 'DIRECTOR', ROLE_MANAGER: 'MANAGER', ROLE_SECRETARY: 'SECRETARY' };
    const displayRole = isRoot ? 'ROOT OWNER' : (roleMap[user?.role] || 'STAFF');
    const initials = user?.username?.charAt(0).toUpperCase() || 'A';

    const sync = useCallback(async () => {
        try { setStaleCount((await recoveryService.getTaskCount()) ?? 0); } catch { /* offline */ }
        try { setUnread((await recoveryService.getUnreadCount()) ?? 0); } catch { /* offline */ }
    }, []);

    const pullList = useCallback(async () => {
        setLoading(true);
        try { setNotifs(await recoveryService.getNotifications()); }
        catch { setNotifs([]); }
        finally { setLoading(false); }
    }, []);

    /* Poll interval comes from the user's own setting. 0 means manual only:
       the timer is never created, so a phone on metered data can opt out. */
    useEffect(() => {
        sync();
        const secs = Number(prefs?.notifPoll ?? 300);
        if (!Number.isFinite(secs) || secs <= 0) return undefined;
        const iv = setInterval(sync, secs * 1000);
        return () => clearInterval(iv);
    }, [sync, prefs?.notifPoll]);

    useEffect(() => {
        const h = (e) => { if (dropRef.current && !dropRef.current.contains(e.target)) setNotifOpen(false); };
        const esc = (e) => { if (e.key === 'Escape') setNotifOpen(false); };
        document.addEventListener('mousedown', h);
        document.addEventListener('keydown', esc);
        return () => {
            document.removeEventListener('mousedown', h);
            document.removeEventListener('keydown', esc);
        };
    }, []);

    const openDrop = async () => {
        const next = !notifOpen;
        setNotifOpen(next);
        if (next) await pullList();
    };

    const go = (n) => {
        setNotifOpen(false);
        navigate(routeFor(n));
        /* Mark read optimistically so the row dims immediately rather than
           waiting on a round trip the user has already navigated away from. */
        setNotifs(list => list.map(x => (x.id === n.id ? { ...x, read: true } : x)));
        setUnread(u => Math.max(0, u - (n.read ? 0 : 1)));
        recoveryService.markRead(n.id).then(sync).catch(() => {});
    };

    const readAll = async () => {
        setNotifs(list => list.map(x => ({ ...x, read: true })));
        setUnread(0);
        try { await recoveryService.markAllRead(); } catch { /* retried on next sync */ }
        sync();
        pullList();
    };

    const shown = useMemo(() => {
        const list = notifs.filter(n => {
            if (filter === 'ALL') return true;
            if (filter === 'UNREAD') return !n.read;
            return describe(n).group === filter;
        });
        return list.slice(0, VISIBLE_LIMIT);
    }, [notifs, filter]);

    const badge = unread + (staleCount > 0 ? staleCount : 0);

    return (
        <header className={styles.header}>
            <div className={styles.headerLeft}>
                <button type="button" className={styles.sidebarToggle} onClick={onToggle} aria-label="Toggle sidebar navigation">
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
                <div className={styles.notifWrap} ref={dropRef}>
                    <button
                        type="button"
                        className={`${styles.notificationGroup} ${badge > 0 ? styles.activeSensor : ''}`}
                        onClick={openDrop}
                        aria-label={badge > 0 ? badge + ' signals pending' : 'Open notifications'}
                        aria-expanded={notifOpen}
                    >
                        <FiBell className={styles.bellIcon} aria-hidden="true" />
                        {badge > 0 && <span className={styles.badge}>{badge > 99 ? '99+' : badge}</span>}
                    </button>

                    {notifOpen && (
                        <div className={styles.notifDrop} role="dialog" aria-label="Notifications">
                            <div className={styles.notifHead}>
                                <span>SIGNALS</span>
                                <span className={styles.notifHeadBtns}>
                                    <button type="button" className={styles.notifReadAll} onClick={pullList} aria-label="Refresh notifications">
                                        <FiRefreshCw aria-hidden="true" /> REFRESH
                                    </button>
                                    <button type="button" className={styles.notifReadAll} onClick={readAll}>
                                        <FiCheck aria-hidden="true" /> READ ALL
                                    </button>
                                </span>
                            </div>

                            <div className={styles.notifFilters}>
                                {FILTERS.map(f => (
                                    <button
                                        key={f.key}
                                        type="button"
                                        className={filter === f.key ? styles.notifChipActive : styles.notifChip}
                                        onClick={() => setFilter(f.key)}
                                    >
                                        {f.label}
                                        {f.key === 'UNREAD' && unread > 0 ? ` (${unread})` : ''}
                                    </button>
                                ))}
                            </div>

                            <div className={styles.notifList}>
                                {/* The recovery queue is computed, not stored, so it is not a
                                    row in the notifications table -- but it is the most
                                    actionable thing the bell knows, so it pins to the top. */}
                                {staleCount > 0 && (filter === 'ALL' || filter === 'RECOVERY') && (
                                    <button type="button" className={styles.notifRowPinned}
                                        onClick={() => { setNotifOpen(false); navigate('/recovery'); }}>
                                        <span className={styles.notifIcon} style={{ color: 'var(--warn)' }}>
                                            <FiPhoneCall aria-hidden="true" />
                                        </span>
                                        <span className={styles.notifBody}>
                                            <span className={styles.notifType}>RECOVERY QUEUE</span>
                                            <span className={styles.notifMsg}>
                                                {staleCount} mission{staleCount > 1 ? 's' : ''} due now
                                            </span>
                                        </span>
                                    </button>
                                )}

                                {loading && <div className={styles.notifEmpty}>SYNCING...</div>}

                                {!loading && shown.length === 0 && staleCount === 0 && (
                                    <div className={styles.notifEmpty}>NO SIGNALS</div>
                                )}

                                {!loading && shown.map(n => {
                                    const meta = describe(n);
                                    const Icon = meta.icon;
                                    return (
                                        <button
                                            type="button"
                                            key={n.id}
                                            className={`${styles.notifRow} ${n.read ? styles.notifRead : ''}`}
                                            onClick={() => go(n)}
                                        >
                                            <span className={styles.notifIcon}
                                                style={{ color: SEVERITY_COLOR[meta.severity] || 'var(--info)' }}>
                                                <Icon aria-hidden="true" />
                                            </span>
                                            <span className={styles.notifBody}>
                                                <span className={styles.notifType}>
                                                    {meta.label}
                                                    <time className={styles.notifTime}>{relativeTime(n.createdAt)}</time>
                                                </span>
                                                <span className={styles.notifMsg}>{n.message}</span>
                                            </span>
                                            {!n.read && <span className={styles.notifUnreadDot} aria-label="Unread" />}
                                        </button>
                                    );
                                })}

                                {!loading && notifs.length > VISIBLE_LIMIT && (
                                    <div className={styles.notifEmpty}>
                                        SHOWING {VISIBLE_LIMIT} OF {notifs.length}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <div className={styles.userCard} aria-label={`Logged in as ${user?.username}, ${displayRole}`}>
                    <div className={styles.avatar} aria-hidden="true">{initials}</div>
                    <div className={styles.userMeta}>
                        <span className={styles.userName}>{user?.username}</span>
                        <span className={styles.roleTag}>{displayRole}</span>
                    </div>
                </div>

                <button type="button" className={styles.logoutTrigger} onClick={logout} aria-label="Sign out of session">
                    <FiLogOut aria-hidden="true" />
                </button>
            </div>
        </header>
    );
};

export default Header;
