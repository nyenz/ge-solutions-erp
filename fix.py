# fix.py -- Client Ledger page rebuilt to match Project Ledger 1:1
# (padding, typography, decor pins/corners, sticky search + sticky table
# header, directional scroll handoff, sortable columns, pagination
# footer) -- columns rethought for what a CLIENT record actually needs
# (contact health dot, plot list w/ status dots, contact info, status
# tags, reliability, debt+progress money cell) instead of the old
# generic column set. Backend endpoint (/recovery/clients/ledger)
# already returns every field this needs -- no backend changes.
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
CLP = FE / "pages" / "Clients" / "ClientLedgerPage.jsx"
CLCSS = FE / "pages" / "Clients" / "ClientLedgerPage.module.css"

def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    print("WROTE", p)

CLIENT_LEDGER_JSX = r"""// PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiUsers, FiSearch, FiPhone, FiUser, FiCreditCard, FiLayers,
    FiChevronLeft, FiChevronRight, FiArrowUp, FiArrowDown, FiClock, FiAlertTriangle, FiX
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './ClientLedgerPage.module.css';

const matchesSearch = (c, term) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');
    const fields = [
        c.name, c.nin, c.phone, c.email,
        ...(c.plots || []).map(p => p.plot),
        ...(c.plots || []).map(p => p.district),
    ];
    return fields.some(f => f && String(f).toLowerCase().replace(/\s+/g, '').includes(t));
};

// -- CONTACT HEALTH BADGE -- mirrors the Project Ledger's payment-health
// dot, but keyed off recency of the last recovery contact instead of the
// last payment: GREEN = touched within 14 days, YELLOW = 2-4 weeks,
// RED = over a month or never contacted.
const getContactBadge = (c) => {
    if (!c.lastContact) return 'RED';
    const days = Math.floor((Date.now() - new Date(c.lastContact)) / 86400000);
    if (days <= 14) return 'GREEN';
    if (days <= 30) return 'YELLOW';
    return 'RED';
};
const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Recent contact', YELLOW: 'Contacted 2-4 weeks ago', RED: 'No recent contact' };
const PAGE_SIZE = 15;
const ContactDot = ({ c }) => {
    const badge = getContactBadge(c);
    return (<span title={BADGE_LABELS[badge]} aria-label={BADGE_LABELS[badge]}
        style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
            background: BADGE_COLORS[badge], boxShadow: `0 0 4px ${BADGE_COLORS[badge]}`,
            flexShrink: 0, marginTop: 4 }} />);
};
const Pins = ({ pos }) => (
    <div className={pos === 'top' ? styles.pinsTop : styles.pinsBottom} aria-hidden="true">
        {[...Array(4)].map((_, i) => <div key={i} className={styles.pin} />)}
    </div>
);

// -- SCROLL PARENT DISCOVERY -- identical to Project Ledger: the app's
// real scrolling element is Shell's .scrollArea, so walk up from the
// table to find the nearest ancestor that actually scrolls.
function findScrollParent(el) {
    let node = el ? el.parentElement : null;
    while (node && node !== document.body && node !== document.documentElement) {
        const overflowY = window.getComputedStyle(node).overflowY;
        if (overflowY === 'auto' || overflowY === 'scroll') return node;
        node = node.parentElement;
    }
    return document.scrollingElement || document.documentElement;
}

// -- DIRECTIONAL SCROLL HANDOFF -- identical behavior to Project Ledger:
//   - scrolling DOWN -> the PAGE scrolls first; the table only takes
//                        over once the page has hit its own bottom edge.
//   - scrolling UP   -> the TABLE scrolls first (inverse); the page only
//                        takes over once the table has hit its own top
//                        edge.
// Done in JS (not native scroll-chaining) so a fast flick can't dump
// un-damped momentum onto the page -- overscroll-behavior:contain on
// .tableScroll (CSS) blocks native handoff so this clamped routing owns
// 100% of the table<->page transition, identically across browsers.
function useDirectionalScrollHandoff(scrollRef) {
    useEffect(() => {
        const tableScroll = scrollRef.current;
        if (!tableScroll) return undefined;
        const pageScroll = findScrollParent(tableScroll);

        const EDGE_TOLERANCE = 2;
        const pageAtTop = () => pageScroll.scrollTop <= EDGE_TOLERANCE;
        const pageAtBottom = () =>
            pageScroll.scrollTop + pageScroll.clientHeight >= pageScroll.scrollHeight - EDGE_TOLERANCE;
        const tableAtTop = () => tableScroll.scrollTop <= EDGE_TOLERANCE;
        const tableAtBottom = () =>
            tableScroll.scrollTop + tableScroll.clientHeight >= tableScroll.scrollHeight - EDGE_TOLERANCE;

        const normalizeWheelDelta = (e) => {
            const LINE_HEIGHT = 16;
            if (e.deltaMode === 1) return e.deltaY * LINE_HEIGHT;
            if (e.deltaMode === 2) return e.deltaY * window.innerHeight;
            return e.deltaY;
        };

        const MAX_STEP_PX = 120;
        const clampStep = (px) => Math.sign(px) * Math.min(Math.abs(px), MAX_STEP_PX);

        const routeDelta = (deltaY, e) => {
            if (deltaY > 0) {
                if (!pageAtBottom()) {
                    pageScroll.scrollTop += clampStep(deltaY);
                    e.preventDefault();
                    return;
                }
                if (tableAtBottom()) return;
                tableScroll.scrollTop += clampStep(deltaY);
                e.preventDefault();
            } else if (deltaY < 0) {
                if (!tableAtTop()) {
                    tableScroll.scrollTop += clampStep(deltaY);
                    e.preventDefault();
                    return;
                }
                if (pageAtTop()) return;
                pageScroll.scrollTop += clampStep(deltaY);
                e.preventDefault();
            }
        };

        const handleWheel = (e) => routeDelta(normalizeWheelDelta(e), e);
        tableScroll.addEventListener('wheel', handleWheel, { passive: false });

        let touchLastY = 0;
        const handleTouchStart = (e) => { touchLastY = e.touches[0].clientY; };
        const handleTouchMove = (e) => {
            const currentY = e.touches[0].clientY;
            const deltaY = touchLastY - currentY;
            touchLastY = currentY;
            routeDelta(deltaY, e);
        };
        tableScroll.addEventListener('touchstart', handleTouchStart, { passive: true });
        tableScroll.addEventListener('touchmove', handleTouchMove, { passive: false });

        return () => {
            tableScroll.removeEventListener('wheel', handleWheel);
            tableScroll.removeEventListener('touchstart', handleTouchStart);
            tableScroll.removeEventListener('touchmove', handleTouchMove);
        };
    }, [scrollRef]);
}

const ClientLedgerPage = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const role = String(user?.role || '').toUpperCase();
    const isDirector = !!user?.isRoot || role === 'ROLE_ADMIN' || role === 'ROLE_DIRECTOR';

    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [loadCode, setLoadCode] = useState('');
    const [page, setPage] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
    const tableScrollRef = useRef(null);
    useDirectionalScrollHandoff(tableScrollRef);

    const load = useCallback(async (attempt = 0) => {
        setLoading(true); setLoadError(false);
        try {
            const data = await recoveryService.getClientLedger();
            setRows(data || []); setLoading(false); setLoadCode('');
        } catch (err) {
            if (attempt < 1) { setTimeout(() => load(attempt + 1), 5000); return; }
            setLoadError(true); setLoading(false);
            setLoadCode(err && err.response ? 'HTTP ' + err.response.status : 'NETWORK');
        }
    }, []);
    useEffect(() => { load(); }, [load]);
    useEffect(() => { setPage(0); }, [searchTerm, activeFilter, sortConfig]);

    const processedData = useMemo(() => {
        let filtered = rows.filter(c => matchesSearch(c, searchTerm));
        const owed = c => Number(c.owed || 0);
        const isCriticalRow = c => {
            const paid = Number(c.paid || 0);
            const total = paid + owed(c);
            return owed(c) > 0 && total > 0 && (paid / total) < 0.25;
        };
        if (activeFilter === 'OWING')       filtered = filtered.filter(c => owed(c) > 0);
        if (activeFilter === 'RECEIVABLES') filtered = filtered.filter(c => (c.plots || []).some(p => p.receivable));
        if (activeFilter === 'PAID')        filtered = filtered.filter(c => (c.plotCount || 0) > 0 && owed(c) <= 0);
        if (activeFilter === 'NOPLOTS')     filtered = filtered.filter(c => (c.plotCount || 0) === 0);
        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(isCriticalRow);
        filtered.sort((a, b) => {
            let aVal, bVal;
            if      (sortConfig.key === 'name')       { aVal = a.name || ''; bVal = b.name || ''; }
            else if (sortConfig.key === 'plotCount')  { aVal = a.plotCount || 0; bVal = b.plotCount || 0; }
            else if (sortConfig.key === 'lastContact'){ aVal = a.lastContact || ''; bVal = b.lastContact || ''; }
            else if (sortConfig.key === 'reliability'){ aVal = a.reliability ?? -1; bVal = b.reliability ?? -1; }
            else if (sortConfig.key === 'owed')       { aVal = Number(a.owed || 0); bVal = Number(b.owed || 0); }
            else                                      { aVal = a[sortConfig.key]; bVal = b[sortConfig.key]; }
            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ?  1 : -1;
            return 0;
        });
        return filtered;
    }, [rows, searchTerm, activeFilter, sortConfig]);

    const pageData = useMemo(() => processedData.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE), [processedData, page]);

    const handleSort = (key) => setSortConfig(prev => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
    const renderSortIcon = (key) => sortConfig.key !== key ? null
        : (sortConfig.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

    const FILTERS = [
        { key: 'ALL', label: 'ALL CLIENTS' }, { key: 'OWING', label: 'OWING' },
        { key: 'RECEIVABLES', label: 'IN RECEIVABLES' }, { key: 'CRITICAL', label: 'CRITICAL' },
        { key: 'PAID', label: 'PAID UP' }, { key: 'NOPLOTS', label: 'NO PLOTS' },
    ];

    const cols = isDirector ? 8 : 7;

    return (
        <div className={styles.container}>
            {/* Page title -- scrolls away */}
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Client Ledger</h1>
                    <p className={styles.subtitle}>Every client — click a row for the full portfolio dossier</p>
                </div>
            </header>

            {/* Control cluster: only .searchBlock is sticky -- filters and
                legend are normal in-flow content and scroll away with the
                page, matching the Project Ledger exactly. */}
            <div className={styles.controlHub}>
                <div className={styles.searchBlock}>
                    <div className={styles.searchInner}>
                        <input type="search" placeholder="Search name, NIN, phone, email or plot..." className={styles.searchInput}
                            value={searchTerm} onChange={e => setSearchTerm(e.target.value)} aria-label="Search clients" autoComplete="off" />
                        <FiSearch className={styles.searchIcon} aria-hidden="true" />
                        {searchTerm && (<button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label="Clear search" type="button"><FiX aria-hidden="true" /></button>)}
                    </div>
                </div>
                <div className={styles.filterRail} role="group" aria-label="Filter clients">
                    {FILTERS.map(f => (
                        <button key={f.key} onClick={() => setActiveFilter(f.key)}
                            className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}
                            aria-pressed={activeFilter === f.key} aria-label={f.label}>{f.label}</button>
                    ))}
                </div>
                <div className={styles.legendRow} aria-label="Contact health legend">
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (
                        <span key={k} className={styles.legendItem}>
                            <span className={styles.legendDot} style={{ background: c, boxShadow: `0 0 4px ${c}` }} /> {BADGE_LABELS[k]}
                        </span>
                    ))}
                </div>
            </div>

            {/* Table panel -- NOT sticky itself, scrolls away with the page.
                Only the table's own header row (inside .tableScroll) stays
                pinned, and only to ITS OWN scroll container. */}
            <div className={styles.tablePanel}>
                <Pins pos="top" />
                <div className={styles.decorBl} aria-hidden="true" />
                <div className={styles.decorBr} aria-hidden="true" />
                <div className={styles.tableScroll} ref={tableScrollRef}>
                    <table className={styles.ledgerTable} aria-label="Client ledger" aria-rowcount={processedData.length}>
                        <thead>
                            <tr>
                                <th className={styles.rowNum}>#</th>
                                <th onClick={() => handleSort('name')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'name' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiUser aria-hidden="true" /> CLIENT {renderSortIcon('name')}
                                </th>
                                <th><FiPhone aria-hidden="true" /> CONTACT</th>
                                <th onClick={() => handleSort('plotCount')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'plotCount' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiLayers aria-hidden="true" /> PLOTS {renderSortIcon('plotCount')}
                                </th>
                                <th>STATUS</th>
                                <th onClick={() => handleSort('lastContact')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'lastContact' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    LAST CONTACT {renderSortIcon('lastContact')}
                                </th>
                                <th onClick={() => handleSort('reliability')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'reliability' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    RELIABILITY {renderSortIcon('reliability')}
                                </th>
                                {isDirector && (
                                    <th onClick={() => handleSort('owed')} className={styles.sortable}
                                        aria-sort={sortConfig.key === 'owed' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                        <FiCreditCard aria-hidden="true" /> PROGRESS {renderSortIcon('owed')}
                                    </th>
                                )}
                            </tr>
                        </thead>
                        <tbody>
                            {loading && (<tr><td colSpan={cols} className={styles.loadingCell}><FiClock aria-hidden="true" /> SYNCING CLIENT REGISTER...</td></tr>)}
                            {!loading && loadError && (
                                <tr><td colSpan={cols} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> CLIENT SYNC FAULT{loadCode ? ` (${loadCode})` : ''} —{' '}
                                    <button className={styles.retryBtn} onClick={() => load()}>RETRY</button>
                                </td></tr>
                            )}
                            {!loading && !loadError && pageData.length === 0 && (
                                <tr><td colSpan={cols} className={styles.emptyCell}>
                                    <FiUsers aria-hidden="true" />
                                    {searchTerm ? `NO CLIENTS MATCH "${searchTerm.toUpperCase()}"` : 'NO CLIENTS MATCH THIS VIEW'}
                                </td></tr>
                            )}
                            {!loading && !loadError && pageData.map((c, i) => {
                                const owed = Number(c.owed || 0);
                                const paid = Number(c.paid || 0);
                                const storageFees = Number(c.storage || 0);
                                const total = paid + owed;
                                const pct = total > 0 ? Math.min((paid / total) * 100, 100) : 0;
                                const isCritical = owed > 0 && total > 0 && pct < 25;
                                const hasReceivable = (c.plots || []).some(p => p.receivable);
                                const plotCount = c.plotCount || 0;
                                const recCount = (c.plots || []).filter(p => p.receivable).length;
                                const titledCount = (c.plots || []).filter(p => p.titled && !p.receivable).length;
                                const folderCount = (c.plots || []).filter(p => !p.titled && !p.receivable).length;
                                const plotNums = (c.plots || []).map(p => p.plot).filter(Boolean);
                                return (
                                    <tr key={c.id} onClick={() => navigate(`/client/${c.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/client/${c.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Client: ${c.name}`}
                                        className={hasReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>
                                        <td className={styles.rowNum}>{page * PAGE_SIZE + i + 1}</td>
                                        <td className={styles.plotCell}>
                                            <div className={styles.indexRow}>
                                                <ContactDot c={c} />
                                                <div className={styles.stack}>
                                                    <span className={styles.ownerName}>{c.name || '---'}</span>
                                                    <span className={styles.stackSub}>{c.nin || 'NO NIN'}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.stack}>
                                                <span className={styles.ownerPhone}>{c.phone || '---'}</span>
                                                <span className={styles.stackSub}>{c.email || 'no email'}</span>
                                            </div>
                                        </td>
                                        <td className={styles.stageCell}>
                                            {plotNums.length === 0 ? <span className={styles.stackSub}>---</span> : (
                                                <div className={styles.stack}>
                                                    <span className={styles.stageName} title={plotNums.join(' · ')}>
                                                        {plotNums.length === 1 ? plotNums[0] : `${plotNums[0]} +${plotNums.length - 1} more`}
                                                    </span>
                                                    <span className={styles.stageDots}>
                                                        {(c.plots || []).map((p, pi) => (
                                                            <span key={p.projectId || pi}
                                                                className={`${styles.stageDot} ${p.receivable ? styles.stageDotCritical : p.titled ? styles.stageDotDone : styles.stageDotPart}`}
                                                                title={p.plot} />
                                                        ))}
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                        <td>
                                            <div className={styles.statusGroup}>
                                                {hasReceivable && <span className={styles.tagReceivable}>RECEIVABLES {recCount}</span>}
                                                {!hasReceivable && plotCount > 0 && owed <= 0 && <span className={styles.tagPaid}>PAID UP</span>}
                                                {!hasReceivable && plotCount > 0 && owed > 0 && <span className={styles.tagStandard}>ACTIVE</span>}
                                                {plotCount === 0 && <span className={styles.tagIdle}>NO PLOTS</span>}
                                                {isCritical && <span className={styles.tagCritical}>CRITICAL</span>}
                                                {titledCount > 0 && <span className={styles.tagMuted}>{titledCount} TITLED</span>}
                                                {folderCount > 0 && <span className={styles.tagMuted}>{folderCount} FOLDER</span>}
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.stack}>
                                                <span className={styles.ownerName}>{c.lastContact ? String(c.lastContact).slice(0, 10) : 'NEVER'}</span>
                                                {(c.lastTone === 'POSITIVE' || c.lastTone === 'NEGATIVE') && (
                                                    <span className={styles.stackSub}>
                                                        <span className={`${styles.toneDot} ${c.lastTone === 'NEGATIVE' ? styles.toneNeg : styles.tonePos}`} title={c.lastTag} /> {c.lastTag}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className={styles.rowNum}>{c.reliability != null ? Number(c.reliability).toFixed(0) : '---'}</td>
                                        {isDirector && (
                                            <td className={styles.moneyCell}>
                                                <div className={styles.moneyRow}>
                                                    <span className={styles.debtLabel}>DEBT:</span>
                                                    <span className={isCritical ? styles.debtCritical : styles.debtAmount}>UGX {owed.toLocaleString()}</span>
                                                </div>
                                                {storageFees > 0 && (
                                                    <div className={styles.feesLine}>+UGX {storageFees.toLocaleString()} storage fees</div>
                                                )}
                                                <div className={styles.velocityBar} role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
                                                    <div className={`${styles.velocityFill} ${isCritical ? styles.velocityFillCritical : ''}`} style={{ width: `${pct}%` }} />
                                                </div>
                                                <span className={styles.pctLabel}>{Math.round(pct)}% paid</span>
                                            </td>
                                        )}
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
                <Pins pos="bottom" />
                <footer className={styles.pagination} aria-label="Pagination">
                    <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} aria-label="Previous page" className={styles.pageBtn}>
                        <FiChevronLeft aria-hidden="true" /> PREV
                    </button>
                    <span className={styles.pageIndicator} aria-current="page">
                        RANGE {page + 1}
                        {processedData.length > 0 && <span className={styles.recordCount}> — {processedData.length} CLIENTS</span>}
                    </span>
                    <button onClick={() => setPage(p => p + 1)} disabled={(page + 1) * PAGE_SIZE >= processedData.length} aria-label="Next page" className={styles.pageBtn}>
                        NEXT <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
            </div>
            <BackToTopButton />
        </div>
    );
};
export default ClientLedgerPage;
"""

CLIENT_LEDGER_CSS = r"""/* PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.module.css */
/* Rebuilt to match Project Ledger (LedgerPage.module.css) 1:1 -- same
   tokens, padding, typography, decor, sticky/scroll behavior -- with
   only the extra classes this page's client-specific columns need
   (status tags, tone dots) appended at the bottom. */
.container {
    --orange:#EE8C3A; --orange-dim:rgba(238,140,58,0.18); --orange-border:rgba(238,140,58,0.28);
    --navy:#213E40; --navy-deep:#1a2e30; --red:#ef4444; --green:#10b981;
    --fs-th: clamp(8px,0.85vw,10px); --fs-td: clamp(10px,1.05vw,12px);
    --radius: 10px;
    max-width:1400px; width:100%; margin:0 auto;
    padding:clamp(12px,2vh,22px) clamp(12px,2vw,24px) 16px;
    font-family:'Inter',sans-serif; color:#fff;
    display:flex; flex-direction:column;
}
.pageHeader {
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
    gap:clamp(8px,1.2vw,14px); border-left:clamp(3px,0.4vw,5px) solid var(--orange);
    padding:clamp(8px,1.2vw,14px) clamp(14px,1.8vw,22px);
    background:rgba(255,255,255,0.62); border-radius:0 12px 12px 0;
    backdrop-filter:blur(15px); box-shadow:0 4px 15px rgba(0,0,0,0.07);
    margin-bottom:clamp(10px,1.5vh,16px);
    transform:translateZ(0);
    will-change:transform;
}
.headerLeft{display:flex;flex-direction:column;gap:3px;min-width:0;flex:1;}
.title{font-family:'Cinzel',serif;color:var(--navy-deep);font-size:clamp(18px,2.5vw,24px);font-weight:700;text-transform:uppercase;letter-spacing:2px;margin:0;}
.subtitle{color:#64748b;font-size:clamp(9px,0.9vw,11px);font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:0;}
.controlHub {
    background: transparent;
    padding: 0 0 8px;
    display: flex; flex-direction: column; gap: 8px;
}
.searchBlock{
    position:sticky; top:0; z-index:30;
    width:min(100%, clamp(220px,38vw,420px));
    padding:4px 0;
}
.searchInner{position:relative;display:flex;align-items:center;background:#fff;border:1.5px solid #c8d6d7;border-radius:6px;height:clamp(36px,4.5vw,44px);transition:border-color .2s,box-shadow .2s;}
.searchInner:focus-within{border-color:var(--orange);box-shadow:0 0 0 3px rgba(238,140,58,0.18);}
.searchIcon{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--orange);pointer-events:none;}
.searchInput{width:100%;border:none;outline:none;background:transparent;color:#1a2e30;padding:0 34px 0 38px;font-weight:600;font-size:12px;height:100%;}
.searchInput::placeholder{color:rgba(26,46,48,0.35);font-weight:500;}
.searchInput::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none;}
.searchClearBtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--orange);cursor:pointer;display:flex;}
.filterRail{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;}
.filterRail::-webkit-scrollbar{display:none;}
.filterBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:8px 16px;border-radius:6px;font-weight:900;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;white-space:nowrap;transition:all .2s;}
.filterBtn:hover{background:rgba(238,140,58,0.12);color:var(--orange);border-color:var(--orange);}
.activeFilter{background:var(--orange) !important;color:#1a2e30 !important;border-color:var(--orange) !important;}
.legendRow{display:flex;flex-wrap:nowrap;gap:14px;padding:4px 0 2px clamp(6px,1vw,12px);overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;margin-bottom:clamp(10px,1.2vw,14px);}
.legendRow::-webkit-scrollbar{display:none;}
.legendItem{display:flex;align-items:center;gap:6px;font-size:10px;font-weight:700;color:rgba(26,46,48,0.6);white-space:nowrap;flex-shrink:0;}
.legendDot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0;}
.tablePanel{
    position:relative;
    background:linear-gradient(160deg,#1c3335 0%,#213E40 100%);border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;isolation:isolate;
}
.decorBl,.decorBr{position:absolute;width:14px;height:14px;border:1.5px solid var(--orange);opacity:.55;pointer-events:none;z-index:20;}
.decorBl::after,.decorBr::after{content:'';position:absolute;width:4px;height:4px;background:rgba(255,255,255,0.5);border-radius:50%;box-shadow:0 0 6px rgba(255,255,255,0.4);}
.decorBl{bottom:8px;left:8px;border-right:none;border-top:none;border-radius:0 0 0 6px;}
.decorBl::after{bottom:-2px;left:-2px;}
.decorBr{bottom:8px;right:8px;border-left:none;border-top:none;border-radius:0 0 6px 0;}
.decorBr::after{bottom:-2px;right:-2px;}
.pinsTop,.pinsBottom{position:absolute;display:flex;gap:7px;left:50%;transform:translateX(-50%);pointer-events:none;z-index:20;}
.pinsTop{top:-3px;}
.pinsBottom{bottom:-3px;}
.pin{width:3px;height:5px;background:var(--orange);border-radius:1px;box-shadow:0 0 5px rgba(238,140,58,.4);}
.tableScroll{
    max-height:calc(100vh - 220px); min-height:280px;
    overflow:auto; overscroll-behavior:contain; overflow-anchor:none;
    border-radius:var(--radius);
    scrollbar-width:none; -ms-overflow-style:none;
    transform:translateZ(0);
}
.tableScroll::-webkit-scrollbar{display:none;width:0;height:0;}
.ledgerTable{width:100%;border-collapse:separate;border-spacing:0;min-width:760px;}
.ledgerTable thead th{
    position:sticky;top:0;z-index:5;
    background:#162a2c;color:var(--orange);
    font-size:var(--fs-th);font-weight:900;letter-spacing:2px;text-transform:uppercase;
    text-align:left;padding:clamp(11px,1.5vw,18px) clamp(12px,1.8vw,20px);
    border-bottom:3px solid var(--orange);white-space:nowrap;user-select:none;
    box-shadow:0 1px 0 var(--orange);
}
.ledgerTable thead th:first-child{border-radius:var(--radius) 0 0 0;}
.ledgerTable thead th:last-child{border-radius:0 var(--radius) 0 0;}
.sortable{cursor:pointer;transition:background .18s,color .18s;}
.sortable:hover{background:linear-gradient(rgba(238,140,58,0.12),rgba(238,140,58,0.12)),#162a2c;color:#fff;}
.ledgerTable tbody td{padding:12px 14px;border-bottom:1px solid rgba(255,255,255,0.06);vertical-align:top;color:#fff;font-size:var(--fs-td);}
.ledgerTable tbody td.rowNum{font-family:'Space Mono',monospace;color:rgba(255,255,255,0.5);}
.ledgerTable tbody tr{cursor:pointer;transition:background .15s;border-left:3px solid transparent;}
.ledgerTable tbody tr:hover{background:rgba(255,255,255,0.04);border-left-color:var(--orange);}
.stageCell{min-width:150px;}
.stageName{font-weight:800;color:#fff;font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block;font-family:'Space Mono',monospace;}
.stageDots{display:flex;gap:4px;flex-wrap:wrap;margin-top:5px;}
.stageDot{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.18);flex-shrink:0;}
.stageDotDone{background:var(--green);box-shadow:0 0 4px var(--green);}
.stageDotPart{background:var(--orange);box-shadow:0 0 4px var(--orange);}
.stageDotCritical{background:var(--red);box-shadow:0 0 4px var(--red);}
.rowReceivable{background:rgba(239,68,68,0.05);}
.rowCritical{background:rgba(239,68,68,0.07);}
.indexRow{display:flex;align-items:flex-start;gap:6px;}
.stack{display:flex;flex-direction:column;gap:2px;}
.stackSub{display:flex;align-items:center;gap:4px;font-size:10px;font-weight:600;color:rgba(255,255,255,0.55);font-family:'Space Mono',monospace;}
.ownerName{font-weight:800;color:#fff;}
.ownerPhone{font-family:'Space Mono',monospace;font-size:11px;color:rgba(255,255,255,0.7);}
.statusGroup{display:flex;flex-direction:column;gap:4px;align-items:flex-start;}
.moneyCell{min-width:150px;}
.moneyRow{display:flex;justify-content:space-between;gap:8px;}
.debtLabel{color:rgba(255,255,255,0.5);font-size:10px;font-weight:800;}
.debtAmount{font-family:'Space Mono',monospace;color:#fca5a5;font-weight:700;}
.debtCritical{font-family:'Space Mono',monospace;color:#ef4444;font-weight:900;}
.feesLine{font-size:0.7rem;color:#ef4444;margin-bottom:4px;}
.velocityBar{height:5px;background:rgba(255,255,255,0.1);border-radius:3px;margin-top:6px;overflow:hidden;}
.velocityFill{height:100%;background:var(--orange);border-radius:3px;}
.velocityFillCritical{background:var(--red);}
.pctLabel{font-size:9px;color:rgba(255,255,255,0.5);font-weight:700;}
.loadingCell,.errorCell,.emptyCell{text-align:center;padding:30px !important;color:rgba(255,255,255,0.5);font-weight:800;letter-spacing:1px;}
.retryBtn{background:none;border:1px solid var(--red);color:var(--red);padding:4px 10px;border-radius:4px;cursor:pointer;font-weight:800;}
.pagination{display:flex;justify-content:space-between;align-items:center;padding:10px 4px 2px;}
.pageBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:7px 14px;border-radius:6px;font-weight:900;font-size:10px;cursor:pointer;display:inline-flex;gap:6px;align-items:center;transition:all .2s;}
.pageBtn:hover:not(:disabled){background:rgba(255,255,255,0.07);border-color:rgba(255,255,255,0.22);color:#fff;}
.pageBtn:disabled{opacity:0.4;cursor:not-allowed;}
.pageIndicator{color:rgba(255,255,255,0.6);font-size:10px;font-weight:800;letter-spacing:1px;}
.recordCount{color:var(--orange);}

/* -- client-specific status tags & tone dots -- same visual language
   (no background/border, colored caps text) as the Project Ledger's
   .tagReceivable/.tagPaid/.tagStandard/.tagCritical. */
.tagReceivable,.tagPaid,.tagStandard,.tagCritical,.tagIdle,.tagMuted{background:none;border:none;font-size:10px;font-weight:900;letter-spacing:1px;text-transform:uppercase;padding:0;}
.tagReceivable{color:#fca5a5;}
.tagPaid{color:#34d399;}
.tagStandard{color:rgba(255,255,255,0.6);}
.tagCritical{color:#ef4444;}
.tagIdle{color:rgba(255,255,255,0.35);}
.tagMuted{color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;}
.toneDot{display:inline-block;width:6px;height:6px;border-radius:50%;flex-shrink:0;}
.tonePos{background:var(--green);box-shadow:0 0 6px rgba(16,185,129,0.7);}
.toneNeg{background:var(--red);box-shadow:0 0 6px rgba(239,68,68,0.7);}

@media (max-width: 700px) {
    .ledgerTable{min-width:640px;}
    .ledgerTable thead th{font-size:7px;letter-spacing:1px;}
    .filterBtn{padding:6px 10px;font-size:9px;letter-spacing:1px;}
}
"""

write(CLP, CLIENT_LEDGER_JSX)
write(CLCSS, CLIENT_LEDGER_CSS)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "Rebuild Client Ledger to match Project Ledger design/scroll/pagination; rethink columns"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")