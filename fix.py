#!/usr/bin/env python3
# PATH: fix131.py
# GOLDEN SEED -- fix131: NOTIFICATION CENTRE v2 ("Hero Chips").
#   The SIGNALS dropdown is rebuilt on the Settings-page system (dark
#   gradient hero, grey tray dock, accent rule that follows the active
#   filter) and its read/unread/group logic is made coherent with the
#   bell. Frontend only (Header.jsx + Header.module.css), no backend.
#
#     1. BELL DOTS. The single red count badge is replaced by one
#        coloured dot per group that has unread items (same colours as
#        the chips), each carrying its own count. sync() now also pulls
#        the list silently, so the dots and the drawer read the SAME rows.
#     2. HERO. Unread count for the current scope + a stacked colour
#        meter (other groups dim when one is selected) + UNREAD/ALL mode
#        switch + REFRESH + READ. The old "SIGNALS" title is gone.
#     3. CHIPS. ALL + five groups. Counts are UNREAD counts, identical to
#        the bell dots. The selected chip takes the free width and clips
#        its own label, so it can never overflow its tray (SYSTEM incl.).
#     4. LOGIC. Default mode is UNREAD; empty state = ALL CAUGHT UP with a
#        VIEW ALL link. READ is scoped to the current group (ALL uses the
#        server-side mark-all). Rows read this way stay visible until the
#        filter or mode changes, so the list never jumps under the cursor.
#        Clicking the selected chip again returns to ALL.
#     5. LIST. Grouped TODAY / YESTERDAY / EARLIER (calendar days), unread
#        first inside each. No icons. Hairline separators, no card gaps.
#        Unread rows are tinted by group, read rows sit on flat grey, type
#        headings take the group colour (CRITICAL severity = red).
#     6. SIZE. Wider (460px) and content-fit: it only grows to a short
#        list limit, then scrolls. Scrollbar is the app's own
#        (Shell.scrollArea: thin, orange thumb, 6px, radius 10px).
#     7. Footer link to Settings (where the refresh interval lives).
#
# Atomic: every patch for both files is matched in memory first; if any
# one is MISSING nothing is written and nothing is committed. Runs
# `npm run build` before committing if node_modules is installed and
# refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

HEADER_JSX = os.path.join(SRC, "components", "layout", "Header.jsx")
HEADER_CSS = os.path.join(SRC, "components", "layout", "Header.module.css")

MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sub(text, old, new, desc):
    """Exact find/replace, first occurrence. Prints OK / SKIP / MISSING."""
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


def between(text, start, end, new, desc):
    """Replace everything from `start` up to (not including) `end`."""
    i = text.find(start)
    j = text.find(end, i + 1) if i >= 0 else -1
    if i >= 0 and j > i:
        print("OK: " + desc)
        return text[:i] + new + text[j:]
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


def tail(text, start, new, desc):
    """Replace everything from `start` to end of file."""
    i = text.find(start)
    if i >= 0:
        print("OK: " + desc)
        return text[:i] + new
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


# ======================================================================
# Header.jsx
# ======================================================================
jsx0 = read(HEADER_JSX)
jsx = jsx0

jsx = sub(jsx,
          " * WHAT CHANGED AND WHY (fix71)",
          " * fix131: the dropdown is now a hero (unread count + colour meter + mode,\n"
          " * refresh, read) over a dot-chip tray and a day-grouped, icon-free list.\n"
          " * Bell dots, chip counts and the hero number are all UNREAD counts computed\n"
          " * from the same rows. READ is scoped to the group being viewed.\n"
          " *\n"
          " * WHAT CHANGED AND WHY (fix71)",
          "Header.jsx doc comment")

jsx = sub(jsx,
          "import { FiMenu, FiBell, FiLogOut, FiCheck, FiPhoneCall, FiShield } from 'react-icons/fi';",
          "import { FiMenu, FiBell, FiLogOut, FiCheck, FiRefreshCw, FiShield } from 'react-icons/fi';",
          "icon imports (FiRefreshCw in, FiPhoneCall out)")

jsx = sub(jsx,
          "import { describe, routeFor, relativeTime, GROUP_COLOR, GROUP_BG, SEVERITY_COLOR, FILTERS } from '../common/notificationCatalog';",
          "import { describe, routeFor, relativeTime, GROUP_COLOR, GROUPS } from '../common/notificationCatalog';",
          "catalog imports")

jsx = sub(jsx,
          "const VISIBLE_LIMIT = 40;\n",
          r'''const VISIBLE_LIMIT = 40;
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
''',
          "constants + dayBucket helper")

jsx = sub(jsx,
          "    const [loading, setLoading] = useState(false);\n    const dropRef = useRef(null);",
          "    const [mode, setMode] = useState('UNREAD');\n"
          "    const [keep, setKeep] = useState([]);\n"
          "    const [spin, setSpin] = useState(false);\n"
          "    const [loading, setLoading] = useState(false);\n"
          "    const dropRef = useRef(null);",
          "mode / keep / spin state")

jsx = between(jsx,
              "    const sync = useCallback(async () => {",
              "    /* Poll interval comes from the user's own setting.",
              r'''    /* fix131: pullList can run silently, and sync now keeps the list itself
       fresh, so the per-group dots on the bell are computed from the very
       same rows the drawer shows -- one source of truth, no SYNCING flash. */
    const pullList = useCallback(async (silent) => {
        if (!silent) setLoading(true);
        try { setNotifs(await recoveryService.getNotifications()); }
        catch { if (!silent) setNotifs([]); }
        finally { if (!silent) setLoading(false); }
    }, []);

    const sync = useCallback(async () => {
        try { setStaleCount((await recoveryService.getTaskCount()) ?? 0); } catch { /* offline */ }
        try { setUnread((await recoveryService.getUnreadCount()) ?? 0); } catch { /* offline */ }
        await pullList(true);
    }, [pullList]);

''',
              "sync + pullList (silent list refresh)")

jsx = sub(jsx,
          "        setNotifOpen(next);\n        if (next) await pullList();",
          "        setNotifOpen(next);\n        setKeep([]);\n        if (next) await pullList(notifs.length > 0);",
          "openDrop resets sticky rows, pulls silently when rows exist")

jsx = between(jsx,
              "    const readAll = async () => {",
              "    return (\n        <header className={styles.header}>",
              r'''    /* fix131: READ is scoped to what you are looking at. On ALL it is the
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

''',
              "readAll scope, groupUnread, dots, shown, sections")

jsx = sub(jsx,
          "{badge > 0 && <span className={styles.badge}>{badge > 99 ? '99+' : badge}</span>}",
          r'''{badge > 0 && (
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
                        )}''',
          "bell: per-group colour dots replace the single badge")

jsx = between(jsx,
              "                    {notifOpen && (\n",
              "                </div>\n\n                <div className={styles.userCard}",
              r'''                    {notifOpen && (
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
                                    <button type="button" className={styles.notifRowPinned}
                                        onClick={() => { setNotifOpen(false); navigate('/recovery'); }}>
                                        <span className={styles.notifBody}>
                                            <span className={styles.notifPinType}>
                                                RECOVERY QUEUE
                                                <time className={styles.notifPinTag}>PINNED</time>
                                            </span>
                                            <span className={styles.notifPinMsg}>
                                                {staleCount} mission{staleCount > 1 ? 's' : ''} due now
                                            </span>
                                        </span>
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
''',
              "notifDrop markup rebuilt (hero, chips, day-grouped rows, footer)")

# ======================================================================
# Header.module.css
# ======================================================================
css0 = read(HEADER_CSS)
css = css0

css = between(css,
              "/* Red badge counter */\n.badge {",
              ".userCard {",
              r'''/* fix131: one dot per group with unread items, same colours as the
   drawer chips, each carrying its own count. Replaces the single red
   count badge. Dark ink on the light group colours for contrast. */
.bellDots {
    position: absolute; top: -9px; right: -14px;
    display: flex;
    pointer-events: none;
}
.bellDot {
    box-sizing: border-box;
    min-width: 18px; height: 18px;
    margin-left: -5px;
    padding: 0 3px;
    border-radius: 9px;
    border: 2px solid #162a2c;
    color: #0f1f20;
    font-family: 'Space Mono', monospace;
    font-size: 8.5px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    animation: bellDotPop 0.3s ease-out both;
}
@keyframes bellDotPop { from { transform: scale(0); } to { transform: scale(1); } }

/* --- OPERATOR CARD --- */
''',
              "bell badge CSS -> group dots")

css = sub(css,
          "   Filters across the top, one icon per type, a relative timestamp on\n"
          "   every row, and an unread marker that is a shape as well as an\n"
          "   opacity so it survives the high-contrast setting.",
          "   fix131: hero (count + colour meter + mode/refresh/read), dot-chip\n"
          "   tray, day-grouped icon-free rows split by hairlines. Unread rows\n"
          "   are tinted by group, read rows sit on flat grey. The scrollbar is\n"
          "   the app's own (Shell.scrollArea): thin, orange thumb, 6px, r10.",
          "notification block heading comment")

css = tail(css,
           ".notifDrop {\n    position: absolute;",
           r'''.notifDrop {
    --a: #EE8C3A;
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    z-index: 10;
    width: min(460px, calc(100vw - 16px));
    max-height: calc(100vh - var(--header-height, 64px) - 24px);
    display: flex;
    flex-direction: column;
    background: #f3f6f6;
    border: 1.5px solid #aebdbc;
    border-radius: 10px;
    box-shadow: 0 16px 40px rgba(22, 42, 44, 0.28);
    overflow: hidden;
    transition: border-color 0.2s ease;
    animation: notifIn 0.2s ease-out both;
}
.notifDrop:hover { border-color: var(--a); }
@keyframes notifIn {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* -- hero ------------------------------------------------------------ */
.notifHero {
    flex-shrink: 0;
    padding: clamp(8px, 1vw, 10px);
    background: linear-gradient(135deg, #3a5a5c 0%, #1c3335 65%, #16292b 100%);
    border-bottom: 2px solid var(--a);
    transition: border-color 0.2s ease;
}
.notifHeroRow { display: flex; align-items: center; gap: clamp(6px, 0.8vw, 8px); }
.notifCount {
    min-width: 26px;
    font-family: 'Space Mono', monospace;
    font-size: clamp(20px, 2.2vw, 24px);
    font-weight: 700;
    line-height: 1;
    color: var(--a);
}
.notifMeter {
    flex: 1; min-width: 24px;
    display: flex; gap: 2px;
    height: 7px;
    border-radius: 4px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.14);
}
.notifMeterSeg { display: block; height: 100%; transition: width 0.4s ease, opacity 0.2s ease; }

.notifMode { display: inline-flex; flex-shrink: 0; background: rgba(0, 0, 0, 0.28); border-radius: 6px; padding: 2px; }
.notifModeBtn, .notifModeOn {
    -webkit-appearance: none; appearance: none;
    border: 0; border-radius: 4px;
    padding: 6px clamp(6px, 0.8vw, 8px);
    font-family: 'Inter', sans-serif;
    font-size: clamp(8px, 0.85vw, 9px);
    font-weight: 900;
    letter-spacing: 1px;
    cursor: pointer;
    transition: color 0.2s ease, background 0.2s ease;
}
.notifModeBtn { background: transparent; color: rgba(255, 255, 255, 0.7); }
.notifModeBtn:hover { color: #EE8C3A; }
.notifModeOn { background: #EE8C3A; color: #1a2e30; }

.notifTool {
    -webkit-appearance: none; appearance: none;
    flex-shrink: 0;
    width: 28px; height: 28px; padding: 0;
    display: inline-flex; align-items: center; justify-content: center;
    background: transparent;
    border: 1.5px solid rgba(238, 140, 58, 0.6);
    border-radius: 6px;
    color: #EE8C3A;
    font-size: 14px;
    cursor: pointer;
    transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}
.notifTool:hover { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.notifSpin svg { animation: notifSpin 0.8s linear infinite; }
@keyframes notifSpin { to { transform: rotate(360deg); } }

.notifModeBtn:focus-visible, .notifModeOn:focus-visible, .notifTool:focus-visible,
.notifChip:focus-visible, .notifChipOn:focus-visible, .notifRow:focus-visible,
.notifRowPinned:focus-visible, .notifFoot:focus-visible, .notifLink:focus-visible {
    outline: 2px solid #EE8C3A;
    outline-offset: -2px;
}

/* -- chips: the selected one takes the free width and clips its own
   label, so nothing can ever spill out of the tray ------------------- */
.notifChips {
    display: flex; gap: 3px;
    margin-top: clamp(6px, 0.8vw, 8px);
    padding: 3px;
    background: #4d5c5a;
    border-radius: 7px;
    overflow: hidden;
}
.notifChip, .notifChipOn {
    -webkit-appearance: none; appearance: none;
    min-width: 0;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 5px;
    border: 0; border-radius: 5px;
    padding: 6px clamp(5px, 0.7vw, 8px);
    font-family: 'Inter', sans-serif;
    font-size: clamp(8px, 0.85vw, 9.5px);
    font-weight: 900;
    letter-spacing: 1px;
    white-space: nowrap;
    cursor: pointer;
    transition: color 0.2s ease, background 0.2s ease, opacity 0.2s ease;
}
.notifChip { flex: 0 1 auto; background: transparent; color: #fff; }
.notifChip:hover { background: rgba(255, 255, 255, 0.1); }
.notifChip[data-empty='true'] { opacity: 0.5; }
.notifChipOn { flex: 1 1 0; background: var(--a); color: #1a2e30; }
.notifChipDot { flex-shrink: 0; width: 8px; height: 8px; border-radius: 50%; background: var(--a); }
.notifChipOn .notifChipDot { display: none; }
.notifChipLabel { display: none; overflow: hidden; text-overflow: ellipsis; }
.notifChipOn .notifChipLabel { display: inline; }
.notifChipCount {
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.85vw, 9.5px);
    font-style: normal;
    font-weight: 700;
    opacity: 0.9;
}

/* -- list: content-fit, short limit, then scroll. Scrollbar copied from
   Shell.module.css .scrollArea (the app's official one). --------------- */
.notifList {
    flex: 1 1 auto;
    min-height: 0;
    max-height: min(340px, calc(100vh - var(--header-height, 64px) - 190px));
    overflow-y: auto;
    overflow-x: hidden;
    background: #f3f6f6;
    scrollbar-width: thin;
    scrollbar-color: var(--orange, #EE8C3A) transparent;
}
.notifList::-webkit-scrollbar { width: 6px; }
.notifList::-webkit-scrollbar-track { background: transparent; }
.notifList::-webkit-scrollbar-thumb { background: var(--orange, #EE8C3A); border-radius: 10px; }
.notifList::-webkit-scrollbar-thumb:hover { background: #f59a4a; }

.notifDay {
    position: sticky; top: 0; z-index: 1;
    padding: 3px 12px;
    background: #3f5654;
    color: #fff;
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.85vw, 9px);
    font-weight: 700;
    letter-spacing: 2px;
}

/* -- rows: hairline separators, no icons, no card gaps --------------- */
.notifRow, .notifRowPinned {
    -webkit-appearance: none; appearance: none;
    display: flex; align-items: center; gap: 10px;
    width: 100%;
    margin: 0;
    text-align: left;
    border: 0;
    border-bottom: 1px solid #cbd6d6;
    border-left: 3px solid var(--t, transparent);
    border-radius: 0;
    padding: clamp(7px, 0.9vw, 9px) 12px;
    cursor: pointer;
    transition: background 0.2s ease;
}
.notifUnread { background: #ffffff; background: color-mix(in srgb, var(--t) 9%, #ffffff); }
.notifUnread:hover { background: #f6f9f9; background: color-mix(in srgb, var(--t) 17%, #ffffff); }
.notifRead { border-left-color: transparent; background: #e4eaea; }
.notifRead:hover { background: #dde4e4; }

.notifBody { display: flex; flex-direction: column; gap: 1px; min-width: 0; flex: 1; }
.notifType {
    display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
    font-family: 'Inter', sans-serif;
    font-size: clamp(8.5px, 0.9vw, 10px);
    font-weight: 900;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    color: var(--t);
    color: color-mix(in srgb, var(--t) 62%, #000000);
}
.notifRead .notifType { color: #6b7b79; }
.notifTime {
    flex-shrink: 0;
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.85vw, 9.5px);
    font-weight: 400;
    letter-spacing: 0.5px;
    text-transform: none;
    color: rgba(26, 46, 48, 0.55);
}
.notifMsg {
    font-family: 'Inter', sans-serif;
    font-size: clamp(11px, 1.1vw, 13px);
    font-weight: 600;
    color: #1a2e30;
    line-height: 1.35;
    word-break: break-word;
}
.notifRead .notifMsg { font-weight: 500; color: #4a5a58; }
.notifUnreadDot {
    flex-shrink: 0;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--t, #EE8C3A);
    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.22);
}

/* The recovery queue is pinned and is not a stored row, so it is dark and
   marked as different rather than pretending to be one of the list. */
.notifRowPinned {
    background: linear-gradient(135deg, #2a4a4c, #16292b);
    border-left-color: #f97316;
    border-bottom-color: #16292b;
}
.notifRowPinned:hover { background: linear-gradient(135deg, #335a5c, #1c3335); }
.notifPinType {
    display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
    font-family: 'Inter', sans-serif;
    font-size: clamp(8.5px, 0.9vw, 10px);
    font-weight: 900;
    letter-spacing: 1.1px;
    color: #fdba74;
}
.notifPinTag { font-family: 'Space Mono', monospace; font-size: 8px; font-weight: 400; letter-spacing: 1px; color: rgba(255, 255, 255, 0.5); }
.notifPinMsg { font-family: 'Inter', sans-serif; font-size: clamp(11px, 1.1vw, 13px); font-weight: 600; color: #ffffff; line-height: 1.35; }

.notifEmpty {
    padding: 22px 13px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.9vw, 10px);
    font-weight: 900;
    letter-spacing: 2px;
    color: rgba(26, 46, 48, 0.5);
}
.notifLink {
    -webkit-appearance: none; appearance: none;
    display: block;
    margin: 8px auto 0;
    padding: 6px 10px;
    background: transparent;
    border: 1.5px solid rgba(238, 140, 58, 0.6);
    border-radius: 5px;
    color: #bf6413;
    font-family: 'Inter', sans-serif;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1.2px;
    cursor: pointer;
    transition: color 0.2s ease, background 0.2s ease;
}
.notifLink:hover { background: #EE8C3A; color: #1a2e30; }

.notifFoot {
    -webkit-appearance: none; appearance: none;
    flex-shrink: 0;
    width: 100%;
    padding: 9px;
    border: 0;
    border-top: 2px solid var(--a);
    background: #162a2c;
    color: #ffffff;
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.9vw, 10px);
    font-weight: 700;
    letter-spacing: 1.6px;
    text-align: center;
    cursor: pointer;
    transition: color 0.2s ease, border-color 0.2s ease;
}
.notifFoot:hover { color: #EE8C3A; }

@media (max-width: 480px) {
    .notifDrop {
        position: fixed;
        top: var(--header-height);
        left: 8px;
        right: 8px;
        width: auto;
        max-height: calc(100vh - var(--header-height) - 16px);
    }
}
''',
           "notification CSS rebuilt from .notifDrop to end of file")

# ======================================================================
# write (atomic) + build gate + commit
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix130).")
    sys.exit(1)

if jsx != jsx0:
    write(HEADER_JSX, jsx)
    print("written: erp-frontend/src/components/layout/Header.jsx")
if css != css0:
    write(HEADER_CSS, css)
    print("written: erp-frontend/src/components/layout/Header.module.css")
if jsx == jsx0 and css == css0:
    print("note: nothing changed -- fix131 already applied")

# build gate (fix76)
if os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        print("FAIL: build is red -- aborting, nothing committed")
        sys.exit(1)
    print("build OK")
else:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

git("add", "-A")
git("commit", "-m", "fix131: notification centre v2 -- hero (unread count, colour meter, UNREAD/ALL, refresh, scoped read), dot chips that cannot overflow, per-group colour dots on the bell, day-grouped icon-free hairline rows with group tinting, content-fit height with the app's own scrollbar")
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip())