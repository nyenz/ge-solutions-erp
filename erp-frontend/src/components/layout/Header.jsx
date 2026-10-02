// PATH: erp-frontend/src/components/layout/Header.jsx
/**
 * GOLDEN SEED -- HEADER / NOTIFICATION CENTRE
 *
 * fix133: the recovery queue is a normal RECOVERY-tinted unread row (same
 * markup and classes as every other row), not a dark pinned card.
 *
 * fix131: the dropdown is now a hero (unread count + colour meter + mode,
 * refresh, read) over a dot-chip tray and a day-grouped, icon-free list.
 * Bell dots, chip counts and the hero number are all UNREAD counts computed
 * from the same rows. READ is scoped to the group being viewed.
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
 * POLLING is the user's choice (Settings -> Notification refresh). Five
 * minutes is the default; a phone on mobile data can drop to fifteen, and
 * MANUAL stops the timer entirely. The old build hard-coded five minutes
 * with no way to change it, and the setting itself did not exist in
 * Settings until fix114 -- Header read prefs.notifPoll, nothing ever wrote it.
 */
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiBell, FiLogOut, FiCheck, FiRefreshCw, FiShield } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { usePreferences } from '../../context/usePreferences';
import recoveryService from '../../services/recoveryService';
import { describe, routeFor, relativeTime, GROUP_COLOR, GROUPS } from '../common/notificationCatalog';
import styles from './Header.module.css';

const VISIBLE_LIMIT = 40;
const GROUP_KEYS = Object.values(GROUPS);
const CRITICAL_TINT = '#dc2626';
const BUCKETS = ['TODAY', 'YESTERDAY', 'EARLIER'];

/* fix131: signals are bucketed by calendar day (since local midnight),
   not by a rolling 24 hours, so TODAY means what people mean by it. */
const dayBucket = (iso) => {
    const t = new Date(iso);
    if (Number.isNaN(t.getTime())) return 'EARLIER';
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    if (t >= start) return 'TODAY';
    if (t.getTime() >= start.getTime() - 86400000) return 'YESTERDAY';
    return 'EARLIER';
};

const Header = ({ onToggle }) => {
    const { user, logout } = useAuth();
    const { prefs } = usePreferences();
    const navigate = useNavigate();

    const [staleCount, setStaleCount] = useState(0);
    const [notifOpen, setNotifOpen] = useState(false);
    const [notifs, setNotifs] = useState([]);
    const [unread, setUnread] = useState(0);
    const [filter, setFilter] = useState('ALL');
    const [mode, setMode] = useState('UNREAD');
    const [keep, setKeep] = useState([]);
    const [spin, setSpin] = useState(false);
    const [loading, setLoading] = useState(false);
    const dropRef = useRef(null);

    const isRoot = user?.isRoot;
    const roleMap = { ROLE_ADMIN: 'ADMIN', ROLE_DIRECTOR: 'DIRECTOR', ROLE_MANAGER: 'MANAGER', ROLE_SECRETARY: 'SECRETARY' };
    const displayRole = isRoot ? 'ROOT OWNER' : (roleMap[user?.role] || 'STAFF');
    const initials = user?.username?.charAt(0).toUpperCase() || 'A';

    /* fix131: pullList can run silently, and sync now keeps the list itself
       fresh, so the per-group dots on the bell are computed from the very
       same rows the drawer shows -- one source of truth, no SYNCING flash. */
    const pullList = useCallback(async (silent) => {
        if (!silent) setLoading(true);
        try { setNotifs(await recoveryService.getNotifications()); }
        catch { if (!silent) setNotifs([]); }
        finally { if (!silent) setLoading(false); }
    }, []);

    const sync = useCallback(async () => {
        // fix170: the three checks run together instead of one after another
        await Promise.all([
            recoveryService.getTaskCount().then((n) => setStaleCount(n ?? 0)).catch(() => { /* offline */ }),
            recoveryService.getUnreadCount().then((n) => setUnread(n ?? 0)).catch(() => { /* offline */ }),
            pullList(true),
        ]);
    }, [pullList]);

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
        setKeep([]);
        if (next) await pullList(notifs.length > 0);
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

    /* fix131: READ is scoped to what you are looking at. On ALL it is the
       server-side mark-all; on one group it marks only that group's unread
       rows, so that group's bell dot clears and the others are untouched.
       Rows read this way stay listed until the filter or mode changes. */
    const readAll = async () => {
        const scope = notifs.filter(n => !n.read && (filter === 'ALL' || describe(n).group === filter));
        if (scope.length === 0) return;
        const ids = new Set(scope.map(n => n.id));
        setKeep(k => [...k, ...scope.map(n => n.id)]);
        setNotifs(list => list.map(x => (ids.has(x.id) ? { ...x, read: true } : x)));
        setUnread(u => (filter === 'ALL' ? 0 : Math.max(0, u - scope.length)));
        try {
            if (filter === 'ALL') await recoveryService.markAllRead();
            else await Promise.all(scope.map(n => recoveryService.markRead(n.id)));
        } catch { /* retried on next sync */ }
        sync();
    };

    const refresh = async () => {
        setSpin(true);
        try { await Promise.all([sync(), new Promise(r => setTimeout(r, 600))]); }
        finally { setSpin(false); }
    };

    /* Unread per group. The recovery queue is a computed row, not a stored
       one, so its missions count toward the RECOVERY dot exactly as they
       already counted toward the old single badge. */
    const groupUnread = useMemo(() => {
        const out = {};
        GROUP_KEYS.forEach(g => { out[g] = 0; });
        notifs.forEach(n => { if (!n.read) out[describe(n).group] += 1; });
        if (staleCount > 0) out[GROUPS.RECOVERY] += staleCount;
        return out;
    }, [notifs, staleCount]);

    const dots = GROUP_KEYS.filter(g => groupUnread[g] > 0);
    const dotTotal = dots.reduce((sum, g) => sum + groupUnread[g], 0);
    /* Offline / list not loaded yet: fall back to the server counters so the
       bell still says something is pending. */
    const badge = dotTotal || (unread + (staleCount > 0 ? staleCount : 0));
    const scopeUnread = filter === 'ALL' ? dotTotal : groupUnread[filter];
    const hasPinned = staleCount > 0 && (filter === 'ALL' || filter === 'RECOVERY');
    const accent = filter === 'ALL' ? '#EE8C3A' : GROUP_COLOR[filter];

    const shown = useMemo(() => {
        const keepSet = new Set(keep);
        const list = notifs.filter(n => {
            if (filter !== 'ALL' && describe(n).group !== filter) return false;
            return mode === 'ALL' || !n.read || keepSet.has(n.id);
        });
        return list.slice(0, VISIBLE_LIMIT);
    }, [notifs, filter, mode, keep]);

    const sections = useMemo(() => BUCKETS.map(b => ({
        key: b,
        rows: shown.filter(n => dayBucket(n.createdAt) === b)
            .sort((a, c) => Number(a.read) - Number(c.read)),
    })).filter(s => s.rows.length > 0), [shown]);

    const pickFilter = (g) => { setFilter(f => (f === g ? 'ALL' : g)); setKeep([]); };
    const pickMode = (m) => { setMode(m); setKeep([]); };

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
                        {badge > 0 && (
                            <span className={styles.bellDots} aria-hidden="true">
                                {dots.length > 0 ? dots.map(g => (
                                    <span key={g} className={styles.bellDot} style={{ background: GROUP_COLOR[g] }}>
                                        {groupUnread[g] > 99 ? '99+' : groupUnread[g]}
                                    </span>
                                )) : (
                                    <span className={styles.bellDot} style={{ background: '#EE8C3A' }}>
                                        {badge > 99 ? '99+' : badge}
                                    </span>
                                )}
                            </span>
                        )}
                    </button>

                    {notifOpen && (
                        <div className={styles.notifDrop} role="dialog" aria-label="Notifications" style={{ '--a': accent }}>
                            <div className={styles.notifHero}>
                                <div className={styles.notifHeroRow}>
                                    <span className={styles.notifCount} aria-live="polite">{scopeUnread}</span>
                                    <div className={styles.notifMeter} aria-hidden="true">
                                        {dots.map(g => (
                                            <span
                                                key={g}
                                                className={styles.notifMeterSeg}
                                                style={{
                                                    width: (groupUnread[g] / (dotTotal || 1) * 100) + '%',
                                                    background: GROUP_COLOR[g],
                                                    opacity: filter === 'ALL' || filter === g ? 1 : 0.3,
                                                }}
                                            />
                                        ))}
                                    </div>
                                    <div className={styles.notifMode} role="group" aria-label="Show signals">
                                        {['UNREAD', 'ALL'].map(m => (
                                            <button
                                                key={m}
                                                type="button"
                                                className={mode === m ? styles.notifModeOn : styles.notifModeBtn}
                                                onClick={() => pickMode(m)}
                                                aria-pressed={mode === m}
                                            >
                                                {m}
                                            </button>
                                        ))}
                                    </div>
                                    <button
                                        type="button"
                                        className={`${styles.notifTool} ${spin ? styles.notifSpin : ''}`}
                                        onClick={refresh}
                                        aria-label="Refresh signals"
                                        title="Refresh"
                                    >
                                        <FiRefreshCw aria-hidden="true" />
                                    </button>
                                    <button
                                        type="button"
                                        className={styles.notifTool}
                                        onClick={readAll}
                                        aria-label={filter === 'ALL' ? 'Mark all read' : 'Mark ' + filter + ' read'}
                                        title={filter === 'ALL' ? 'Mark all read' : 'Mark ' + filter + ' read'}
                                    >
                                        <FiCheck aria-hidden="true" />
                                    </button>
                                </div>

                                <div className={styles.notifChips}>
                                    {['ALL', ...GROUP_KEYS].map(k => {
                                        const n = k === 'ALL' ? dotTotal : groupUnread[k];
                                        const on = filter === k;
                                        return (
                                            <button
                                                key={k}
                                                type="button"
                                                data-empty={!on && n === 0 ? 'true' : undefined}
                                                className={on ? styles.notifChipOn : styles.notifChip}
                                                style={{ '--a': k === 'ALL' ? '#EE8C3A' : GROUP_COLOR[k] }}
                                                onClick={() => pickFilter(k)}
                                                aria-pressed={on}
                                            >
                                                <span className={styles.notifChipDot} aria-hidden="true" />
                                                <span className={styles.notifChipLabel}>{k}</span>
                                                <em className={styles.notifChipCount}>{n}</em>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className={styles.notifList}>
                                {/* The recovery queue is computed, not stored, so it is not a
                                    row in the notifications table -- but it is the most
                                    actionable thing the bell knows, so it pins to the top. */}
                                {hasPinned && (
                                    <button
                                        type="button"
                                        data-group="RECOVERY"
                                        className={`${styles.notifRow} ${styles.notifUnread}`}
                                        style={{ '--t': GROUP_COLOR.RECOVERY }}
                                        onClick={() => { setNotifOpen(false); navigate('/recovery'); }}
                                    >
                                        <span className={styles.notifBody}>
                                            <span className={styles.notifType}>
                                                Recovery queue
                                                <time className={styles.notifTime}>NOW</time>
                                            </span>
                                            <span className={styles.notifMsg}>
                                                {staleCount} mission{staleCount > 1 ? 's' : ''} due now
                                            </span>
                                        </span>
                                        <span className={styles.notifUnreadDot} aria-label="Unread" />
                                    </button>
                                )}

                                {loading && <div className={styles.notifEmpty}>SYNCING...</div>}

                                {!loading && sections.length === 0 && !hasPinned && (
                                    <div className={styles.notifEmpty}>
                                        {mode === 'UNREAD' ? 'ALL CAUGHT UP' : 'NO SIGNALS'}
                                        {mode === 'UNREAD' && (
                                            <button type="button" className={styles.notifLink} onClick={() => pickMode('ALL')}>
                                                VIEW ALL
                                            </button>
                                        )}
                                    </div>
                                )}

                                {!loading && sections.map(s => (
                                    <React.Fragment key={s.key}>
                                        <div className={styles.notifDay}>{s.key}</div>
                                        {s.rows.map(n => {
                                            const meta = describe(n);
                                            /* One hue per group drives the row tint, the type
                                               heading and the unread dot; CRITICAL goes red. */
                                            const tint = meta.severity === 'CRITICAL'
                                                ? CRITICAL_TINT
                                                : (GROUP_COLOR[meta.group] || '#94a3b8');
                                            return (
                                                <button
                                                    type="button"
                                                    key={n.id}
                                                    data-group={meta.group}
                                                    className={`${styles.notifRow} ${n.read ? styles.notifRead : styles.notifUnread}`}
                                                    style={{ '--t': tint }}
                                                    onClick={() => go(n)}
                                                >
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
                                    </React.Fragment>
                                ))}

                                {!loading && notifs.length > VISIBLE_LIMIT && (
                                    <div className={styles.notifEmpty}>
                                        SHOWING {VISIBLE_LIMIT} OF {notifs.length}
                                    </div>
                                )}
                            </div>

                            <button type="button" className={styles.notifFoot}
                                onClick={() => { setNotifOpen(false); navigate('/settings'); }}>
                                NOTIFICATION SETTINGS
                            </button>
                        </div>
                    )}
                </div>

                <div className={styles.userCard} aria-label={`Logged in as ${user?.username}, ${displayRole}`}>
                    <div className={styles.avatar} aria-hidden="true">{initials}</div>
                    <div className={styles.userMeta}>
                        <span className={styles.userName}>{user?.username}</span>
                        <span className={`${styles.roleTag} ${isRoot ? styles.roleTagRoot : ''}`}>
                            {isRoot && <FiShield aria-hidden="true" />}
                            {displayRole}
                        </span>
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
