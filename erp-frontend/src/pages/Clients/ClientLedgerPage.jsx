// PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.jsx
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
