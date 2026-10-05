// PATH: erp-frontend/src/components/layout/Header.jsx
/**
 * GOLDEN SEED -- HEADER / NOTIFICATION CENTRE
 *
 * fix181 (Sections 17 and 21): ONE summary call per tick (unread per group from the server, critical count, the
 * groups this rank can receive, "due now" for callers only); the list is loaded only when the drawer opens and pages
 * with SHOW MORE; READ is one call with the group and the time of the newest row shown; each row carries its own
 * link from the server (no link = the page is not yours, the row stays unread); day groups and ages come from the
 * server clock; no polling while the tab is hidden, the key must be changed, or for the Employee.
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
import { roleFlags } from '../../utils/roles';
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiBell, FiLogOut, FiCheck, FiRefreshCw, FiShield } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { usePreferences } from '../../context/usePreferences';
import recoveryService from '../../services/recoveryService';
import { describe, GROUP_COLOR, GROUPS } from '../common/notificationCatalog';
import styles from './Header.module.css';
import { IS_LOCAL_API } from '../../api/axios';
import { anyDirty, allowLeave } from '../../utils/dirtyRegistry';
import HardwareModal from '../common/HardwareModal';

const STEP = 40;
const GROUP_KEYS = Object.values(GROUPS);
const CRITICAL_TINT = '#dc2626';
const BUCKETS = ['TODAY', 'YESTERDAY', 'EARLIER'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const SR_ONLY = { position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap' };

// fix181 (21.8): the age comes from the server; past two days the date is printed in one fixed format
const ageText = (n) => {
    const secs = Number(n.ageSeconds);
    if (!Number.isFinite(secs)) return '';
    if (secs < 45) return 'just now';
    if (secs < 3600) return Math.floor(secs / 60) + ' min ago';
    if (secs < 86400) return Math.floor(secs / 3600) + ' hr ago';
    if (secs < 172800) return 'yesterday';
    const m = String(n.createdAt || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
    return m ? m[3] + ' ' + MONTHS[Number(m[2]) - 1] + ' ' + m[1] : '';
};

const Header = ({ onToggle }) => {
    const { user, logout } = useAuth();
    // fix181 (21.9): sign out asks first when a form on this page has unsaved changes
    const [confirmOut, setConfirmOut] = useState(false);
    const signOut = () => { if (anyDirty()) setConfirmOut(true); else logout(); };
    const { prefs } = usePreferences();
    const navigate = useNavigate();

    const flags = roleFlags(user);
    const isRoot = user?.isRoot;
    const displayRole = flags.chip;
    const initials = user?.username?.charAt(0).toUpperCase() || 'A';
    // fix181 (8.4a, 14.6c, 21.5a): no bell for the Employee, and no calls while the key must be changed
    const noBell = flags.isEmployee || !!user?.mustChangePassword;

    const [summary, setSummary] = useState(null);
    const [failCount, setFailCount] = useState(0);
    const [notifOpen, setNotifOpen] = useState(false);
    const [notifs, setNotifs] = useState([]);
    const [listError, setListError] = useState('');
    const [lastGood, setLastGood] = useState(null);
    const [filter, setFilter] = useState('ALL');
    const [mode, setMode] = useState('UNREAD');
    const [keep, setKeep] = useState([]);
    const [limit, setLimit] = useState(STEP);
    const [spin, setSpin] = useState(false);
    const [loading, setLoading] = useState(false);
    const [blocked, setBlocked] = useState(null);
    const [announce, setAnnounce] = useState('');
    const dropRef = useRef(null);
    const bellRef = useRef(null);
    const titleRef = useRef(null);
    const lastSync = useRef(0);
    const lastUnread = useRef(null);

    const sync = useCallback(async () => {
        if (noBell) return;
        try {
            const s = await recoveryService.getSummary();
            setSummary(s); setFailCount(0); lastSync.current = Date.now();
            if (lastUnread.current !== null && s.unread > lastUnread.current) setAnnounce('New alert. ' + s.unread + ' unread.');
            lastUnread.current = s.unread;
        } catch {
            setFailCount(c => c + 1);
        }
    }, [noBell]);

    const pullList = useCallback(async (silent) => {
        if (noBell) return;
        if (!silent) setLoading(true);
        try {
            setNotifs(await recoveryService.getNotifications());
            setListError(''); setLastGood(new Date());
        } catch {
            setListError('COULD NOT LOAD');   // the last good list stays on screen
        } finally { if (!silent) setLoading(false); }
    }, [noBell]);

    const moreFromServer = async () => {
        const last = notifs[notifs.length - 1];
        if (!last) return;
        try {
            const more = await recoveryService.getNotifications(last.createdAt);
            setNotifs(list => [...list, ...more.filter(m => !list.some(x => x.id === m.id))]);
        } catch { setListError('COULD NOT LOAD'); }
    };

    /* Poll interval comes from the user's own setting (0 = manual). fix181 (21.5b): nothing while the tab is hidden;
       coming back to the tab refreshes at once when the last refresh is older than the interval. */
    useEffect(() => {
        if (noBell) return undefined;
        const secs = Number(prefs?.notifPoll ?? 300);
        const first = setTimeout(sync, 0);
        let iv;
        if (Number.isFinite(secs) && secs > 0) iv = setInterval(() => { if (!document.hidden) sync(); }, secs * 1000);
        const onVis = () => { if (!document.hidden && Number.isFinite(secs) && secs > 0 && Date.now() - lastSync.current > secs * 1000) sync(); };
        document.addEventListener('visibilitychange', onVis);
        return () => { clearTimeout(first); if (iv) clearInterval(iv); document.removeEventListener('visibilitychange', onVis); };
    }, [sync, prefs?.notifPoll, noBell]);

    const closeDrop = useCallback(() => {
        setNotifOpen(false);
        if (bellRef.current) bellRef.current.focus();
    }, []);

    useEffect(() => {
        const h = (e) => { if (dropRef.current && !dropRef.current.contains(e.target)) setNotifOpen(false); };
        const key = (e) => {
            if (e.key === 'Escape' && notifOpen) closeDrop();
            // fix181 (21.7): Tab stays inside the open drawer
            if (e.key === 'Tab' && notifOpen && dropRef.current) {
                const items = dropRef.current.querySelectorAll('[role="dialog"] button, [role="dialog"] [tabindex="-1"]');
                if (items.length === 0) return;
                const firstEl = items[0], lastEl = items[items.length - 1];
                if (e.shiftKey && document.activeElement === firstEl) { e.preventDefault(); lastEl.focus(); }
                else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); firstEl.focus(); }
            }
        };
        document.addEventListener('mousedown', h);
        document.addEventListener('keydown', key);
        return () => { document.removeEventListener('mousedown', h); document.removeEventListener('keydown', key); };
    }, [notifOpen, closeDrop]);

    useEffect(() => { if (notifOpen && titleRef.current) titleRef.current.focus(); }, [notifOpen]);

    const openDrop = async () => {
        const next = !notifOpen;
        setNotifOpen(next);
        setKeep([]); setLimit(STEP); setBlocked(null);
        if (next) await pullList(notifs.length > 0);
    };

    const go = (n) => {
        // fix181 (17.10, 17.18d, 21.9): no link = not a page for this rank; the row stays unread and says so
        if (!n.link) { setBlocked(n.id); return; }
        setNotifOpen(false);
        navigate(n.link);
        if (!n.read) {
            setNotifs(list => list.map(x => (x.id === n.id ? { ...x, read: true } : x)));
            recoveryService.markRead(n.id).then(sync).catch(() => {});
        }
    };

    const groupOf = (n) => n.category || describe(n).group;

    const scopeRows = useMemo(() => notifs.filter(n => filter === 'ALL' || groupOf(n) === filter), [notifs, filter]);
    const shownAll = useMemo(() => {
        const keepSet = new Set(keep);
        return scopeRows.filter(n => mode === 'ALL' || !n.read || keepSet.has(n.id));
    }, [scopeRows, mode, keep]);
    const shown = useMemo(() => shownAll.slice(0, limit), [shownAll, limit]);

    /* fix181 (21.2, 17.18b): READ marks the chosen group up to the newest row shown, in ONE call */
    const readAll = async () => {
        const unreadInScope = summary ? (filter === 'ALL' ? summary.unread : (summary.unreadByGroup || {})[filter] || 0) : 0;
        if (unreadInScope === 0) return;
        const onScreen = shown.filter(n => !n.read).length;
        if (unreadInScope > onScreen && !window.confirm('Mark ' + unreadInScope + ' unread ' + (filter === 'ALL' ? '' : filter + ' ') + 'alerts as read? ' + onScreen + ' are shown.')) return;
        const upTo = (notifs[0] && notifs[0].createdAt) || (summary && summary.serverTime);
        setKeep(k => [...k, ...shown.filter(n => !n.read).map(n => n.id)]);
        setNotifs(list => list.map(x => ((filter === 'ALL' || groupOf(x) === filter) && x.createdAt <= upTo ? { ...x, read: true } : x)));
        try { await recoveryService.markAllRead(filter === 'ALL' ? null : filter, upTo); } catch { /* the next tick shows the truth */ }
        sync();
    };

    const refresh = async () => {
        setSpin(true);
        try { await Promise.all([sync(), notifOpen ? pullList(true) : null, new Promise(r => setTimeout(r, 600))]); }
        finally { setSpin(false); }
    };

    const groups = (summary && summary.groups && summary.groups.length) ? summary.groups.filter(g => GROUP_KEYS.includes(g)) : GROUP_KEYS;
    const byGroup = (summary && summary.unreadByGroup) || {};
    const dueNow = summary && summary.dueNow != null ? Number(summary.dueNow) : 0;
    const unread = summary ? Number(summary.unread || 0) : 0;
    const critical = summary ? Number(summary.unreadCritical || 0) : 0;
    const dots = groups.filter(g => (byGroup[g] || 0) > 0);
    const badge = unread;
    const scopeUnread = filter === 'ALL' ? unread : (byGroup[filter] || 0);
    const showDue = dueNow > 0 && (filter === 'ALL' || filter === 'RECOVERY');
    const accent = filter === 'ALL' ? '#EE8C3A' : GROUP_COLOR[filter];

    const sections = useMemo(() => BUCKETS.map(b => ({
        key: b,
        rows: shown.filter(n => (n.dayBucket || 'EARLIER') === b).sort((a, c) => Number(a.read) - Number(c.read)),
    })).filter(sct => sct.rows.length > 0), [shown]);

    const pickFilter = (g) => { setFilter(f => (f === g ? 'ALL' : g)); setKeep([]); setLimit(STEP); };
    const pickMode = (m) => { setMode(m); setKeep([]); setLimit(STEP); };
    const fmtClock = (d) => (d ? String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') : '');

    return (
        <header className={styles.header}>
            <div className={styles.headerLeft}>
                <button type="button" className={styles.sidebarToggle} onClick={onToggle} aria-label="Toggle sidebar navigation">
                    <FiMenu aria-hidden="true" />
                </button>
                {/* fix181 (15.2j): never mistake a test copy for the live system */}
                {IS_LOCAL_API && <span className={styles.localStrip} title="This page is not using the live server">LOCAL</span>}
                <div className={styles.logoSection} aria-label="Golden Seed ERP">
                    <div className={styles.logoSmallPulse} aria-hidden="true">
                        <div className={styles.pulseInner}>🌱</div>
                        <div className={styles.pulseRing} />
                    </div>
                    <span className={styles.brandName}>GOLDEN SEED</span>
                </div>
            </div>

            <div className={styles.headerRight}>
                <span style={SR_ONLY} aria-live="polite">{notifOpen ? '' : announce}</span>
                {!noBell && (<div className={styles.notifWrap} ref={dropRef}>
                    <button
                        ref={bellRef}
                        type="button"
                        className={`${styles.notificationGroup} ${badge > 0 || dueNow > 0 ? styles.activeSensor : ''}`}
                        onClick={openDrop}
                        aria-label={(badge > 0 ? badge + ' unread alert' + (badge === 1 ? '' : 's') : 'No unread alerts') + (critical > 0 ? ', ' + critical + ' critical' : '') + '. Open notifications'}
                        aria-expanded={notifOpen}
                        aria-haspopup="dialog"
                        aria-controls="notif-drawer"
                        style={critical > 0 ? { boxShadow: '0 0 0 2px ' + CRITICAL_TINT } : undefined}
                    >
                        <FiBell className={styles.bellIcon} aria-hidden="true" />
                        {(badge > 0 || dueNow > 0 || failCount >= 2) && (
                            <span className={styles.bellDots} aria-hidden="true">
                                {dots.map(g => (
                                    <span key={g} className={styles.bellDot} style={{ background: critical > 0 && g === dots[0] ? CRITICAL_TINT : GROUP_COLOR[g] }}>
                                        {byGroup[g] > 99 ? '99+' : byGroup[g]}
                                    </span>
                                ))}
                                {dueNow > 0 && (
                                    <span className={styles.bellDot} title="Clients due for a call (not an alert)"
                                        style={{ background: 'transparent', border: '2px solid ' + GROUP_COLOR.RECOVERY, color: GROUP_COLOR.RECOVERY }}>
                                        {dueNow > 99 ? '99+' : dueNow}
                                    </span>
                                )}
                                {failCount >= 2 && <span className={styles.bellDot} title="The last updates failed" style={{ background: '#64748b' }}>!</span>}
                            </span>
                        )}
                    </button>

                    {notifOpen && (
                        <div id="notif-drawer" className={styles.notifDrop} role="dialog" aria-label="Notifications" aria-modal="false" style={{ '--a': accent }}>
                            <div className={styles.notifHero}>
                                <div className={styles.notifHeroRow}>
                                    <span className={styles.notifCount} tabIndex={-1} ref={titleRef} aria-live="polite">{scopeUnread}{critical > 0 && filter === 'ALL' ? ' (' + critical + ' critical)' : ''}</span>
                                    <div className={styles.notifMeter} aria-hidden="true">
                                        {dots.map(g => (
                                            <span key={g} className={styles.notifMeterSeg}
                                                style={{ width: ((byGroup[g] || 0) / (unread || 1) * 100) + '%', background: GROUP_COLOR[g], opacity: filter === 'ALL' || filter === g ? 1 : 0.3 }} />
                                        ))}
                                    </div>
                                    <div className={styles.notifMode} role="group" aria-label="Show signals">
                                        {['UNREAD', 'ALL'].map(m => (
                                            <button key={m} type="button" className={mode === m ? styles.notifModeOn : styles.notifModeBtn}
                                                onClick={() => pickMode(m)} aria-pressed={mode === m}>{m}</button>
                                        ))}
                                    </div>
                                    <button type="button" className={`${styles.notifTool} ${spin ? styles.notifSpin : ''}`} onClick={refresh} aria-label="Refresh signals" title="Refresh">
                                        <FiRefreshCw aria-hidden="true" />
                                    </button>
                                    <button type="button" className={styles.notifTool} onClick={readAll} disabled={scopeUnread === 0}
                                        aria-label={filter === 'ALL' ? 'Mark all read' : 'Mark ' + filter + ' read'}
                                        title={scopeUnread === 0 ? 'Nothing unread here (the calls due are not alerts)' : (filter === 'ALL' ? 'Mark all read' : 'Mark ' + filter + ' read')}>
                                        <FiCheck aria-hidden="true" />
                                    </button>
                                </div>

                                <div className={styles.notifChips}>
                                    {['ALL', ...groups].map(k => {
                                        const n = k === 'ALL' ? unread : (byGroup[k] || 0);
                                        const on = filter === k;
                                        return (
                                            <button key={k} type="button" data-empty={!on && n === 0 ? 'true' : undefined}
                                                className={on ? styles.notifChipOn : styles.notifChip}
                                                style={{ '--a': k === 'ALL' ? '#EE8C3A' : GROUP_COLOR[k] }}
                                                onClick={() => pickFilter(k)} aria-pressed={on}>
                                                <span className={styles.notifChipDot} aria-hidden="true" />
                                                <span className={styles.notifChipLabel}>{k}</span>
                                                <em className={styles.notifChipCount}>{n}</em>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* fix181 (21.3): the calls due are a computed number, not an alert -- their own box, not in the unread count */}
                            {showDue && (
                                <button type="button" className={styles.notifRow} style={{ '--t': GROUP_COLOR.RECOVERY, borderStyle: 'dashed' }}
                                    onClick={() => { setNotifOpen(false); navigate('/recovery'); }}>
                                    <span className={styles.notifBody}>
                                        <span className={styles.notifType}>Clients due for a call<time className={styles.notifTime}>NOW</time></span>
                                        <span className={styles.notifMsg}>{dueNow} client{dueNow > 1 ? 's' : ''} to call. Open Recovery.</span>
                                    </span>
                                </button>
                            )}

                            <div className={styles.notifList}>
                                {listError && (
                                    <div className={styles.notifEmpty} role="alert">
                                        {listError}{lastGood ? ' (last updated ' + fmtClock(lastGood) + ')' : ''}
                                        <button type="button" className={styles.notifLink} onClick={() => pullList(false)}>RETRY</button>
                                    </div>
                                )}
                                {loading && <div className={styles.notifEmpty}>SYNCING...</div>}

                                {!loading && !listError && sections.length === 0 && (
                                    <div className={styles.notifEmpty}>
                                        {mode === 'UNREAD' ? 'ALL CAUGHT UP' : 'NO SIGNALS'}
                                        {mode === 'UNREAD' && (<button type="button" className={styles.notifLink} onClick={() => pickMode('ALL')}>VIEW ALL</button>)}
                                    </div>
                                )}

                                {!loading && sections.map(sct => (
                                    <React.Fragment key={sct.key}>
                                        <div className={styles.notifDay}>{sct.key}</div>
                                        {sct.rows.map(n => {
                                            const meta = describe(n);
                                            const group = groupOf(n);
                                            const tint = meta.severity === 'CRITICAL' || n.severity === 'CRITICAL' ? CRITICAL_TINT : (GROUP_COLOR[group] || '#94a3b8');
                                            return (
                                                <button type="button" key={n.id} data-group={group}
                                                    className={`${styles.notifRow} ${n.read ? styles.notifRead : styles.notifUnread}`}
                                                    style={{ '--t': tint }} onClick={() => go(n)}>
                                                    <span className={styles.notifBody}>
                                                        <span className={styles.notifType}>
                                                            {meta.label}
                                                            <time className={styles.notifTime}>{ageText(n)}</time>
                                                        </span>
                                                        <span className={styles.notifMsg}>{n.message}</span>
                                                        {blocked === n.id && <span className={styles.notifMsg} role="status">You cannot open this page.</span>}
                                                    </span>
                                                    {!n.read && (<><span className={styles.notifUnreadDot} aria-hidden="true" /><span style={SR_ONLY}>Unread</span></>)}
                                                </button>
                                            );
                                        })}
                                    </React.Fragment>
                                ))}

                                {!loading && shownAll.length > 0 && (
                                    <div className={styles.notifEmpty}>
                                        SHOWING {shown.length} OF {mode === 'UNREAD' ? scopeUnread : (filter === 'ALL' && summary ? summary.total : shownAll.length)}
                                        {shownAll.length > limit && (<button type="button" className={styles.notifLink} onClick={() => setLimit(l => l + STEP)}>SHOW MORE</button>)}
                                        {shownAll.length <= limit && notifs.length >= 200 && (<button type="button" className={styles.notifLink} onClick={moreFromServer}>LOAD OLDER</button>)}
                                    </div>
                                )}
                            </div>

                            <button type="button" className={styles.notifFoot}
                                onClick={() => { setNotifOpen(false); navigate('/settings?tab=appearance'); }}>
                                NOTIFICATION SETTINGS{lastGood ? ' - updated ' + fmtClock(lastGood) : ''}
                            </button>
                        </div>
                    )}
                </div>)}

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

                <button type="button" className={styles.logoutTrigger} onClick={signOut} aria-label="Sign out">
                    <FiLogOut aria-hidden="true" />
                </button>
            </div>
            <HardwareModal isOpen={confirmOut} onClose={() => setConfirmOut(false)} title="SIGN OUT?">
                <p className={styles.signOutText}>This page has changes that are not saved. Sign out anyway? The changes will be lost.</p>
                <div className={styles.signOutRow}>
                    <button type="button" className={styles.signOutYes} onClick={() => { allowLeave(); logout(); }}>SIGN OUT</button>
                    <button type="button" className={styles.signOutNo} onClick={() => setConfirmOut(false)}>STAY</button>
                </div>
            </HardwareModal>
        </header>
    );
};

export default Header;
