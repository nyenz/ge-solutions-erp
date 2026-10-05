// PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.jsx
import { roleFlags } from '../../utils/roles';
import { PaymentHealthDot, PaymentHealthLegend } from '../../components/common/PaymentHealth';
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiUsers, FiSearch, FiPhone, FiUser, FiCreditCard, FiLayers,
    FiChevronLeft, FiChevronRight, FiArrowUp, FiArrowDown, FiAlertTriangle, FiX
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { cached, remember } from '../../utils/pageCache';
import recoveryService from '../../services/recoveryService';
import BackToTopButton from '../../components/common/BackToTopButton';
import { FiRefreshCw } from 'react-icons/fi';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import styles from './ClientLedgerPage.module.css';
import { LoadingRow } from '../../components/common/LoadingState';
import TabDock, { accentOf } from '../../components/common/TabDock';

const matchesSearch = (c, term) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');
    const fields = [
        c.name, c.nin, c.phone, c.email,
        ...(c.plots || []).map(p => p.index),
        ...(c.plots || []).map(p => p.subCounty),
    ];
    return fields.some(f => f && String(f).toLowerCase().replace(/\s+/g, '').includes(t));
};

// fix181 (5.2): the dot is the shared one (utils/paymentHealth): server day count, one gradient, NEW for a new project
const PAGE_SIZE = 15;
const PaymentDot = ({ c }) => <PaymentHealthDot days={c.daysSincePayment} isNew={!!c.newProjectOnly} startsOn={c.recoveryStartsOn} settled={!!c.paidUp} />;
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
    const isDirector = roleFlags(user).isOwnerLevel;

    // fix182 (speed): a return visit draws the last list at once and refreshes it quietly (utils/pageCache.js)
    const [rows, setRows] = useState(() => cached('clients') || []);
    const [loading, setLoading] = useState(() => !cached('clients'));
    const [loadError, setLoadError] = useState(false);
    const [loadCode, setLoadCode] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
    // a new search / filter / sort starts from the first page (worked out while drawing, not in an effect)
    const filterKey = searchTerm + '|' + activeFilter + '|' + sortConfig.key + '|' + sortConfig.direction;
    const [pageAt, setPageAt] = useState({ key: filterKey, page: 0 });
    const page = pageAt.key === filterKey ? pageAt.page : 0;
    const setPage = (next) => setPageAt(prev => {
        const cur = prev.key === filterKey ? prev.page : 0;
        return { key: filterKey, page: typeof next === 'function' ? next(cur) : next };
    });
    const tableScrollRef = useRef(null);
    useDirectionalScrollHandoff(tableScrollRef);

    const load = useCallback(async () => {
        let lastErr = null;
        // one quiet retry after 5 seconds (the free server may still be waking up), then the error row
        for (let attempt = 0; attempt < 2; attempt += 1) {
            try {
                const data = await recoveryService.getClientLedger();
                setRows(remember('clients', data || [])); setLoading(false); setLoadError(false); setLoadCode('');
                return;
            } catch (err) {
                lastErr = err;
                if (attempt === 0) await new Promise(r => setTimeout(r, 5000));
            }
        }
        setLoadError(true); setLoading(false);
        setLoadCode(lastErr && lastErr.response ? 'HTTP ' + lastErr.response.status : 'NETWORK');
    }, []);
    useEffect(() => { Promise.resolve().then(load); }, [load]);
    const reload = () => { if (!rows.length) setLoading(true); setLoadError(false); load(); };

    const processedData = useMemo(() => {
        let filtered = rows.filter(c => matchesSearch(c, searchTerm));
        // fix181 (5.4, 5.8, 11.3, 11.4): the server sends the rules as plain flags (the same for every rank)
        if (activeFilter === 'OWING')       filtered = filtered.filter(c => !!c.owing);
        if (activeFilter === 'RECEIVABLES') filtered = filtered.filter(c => (c.receivableCount || 0) > 0);
        if (activeFilter === 'PAID')        filtered = filtered.filter(c => !!c.paidUp);
        if (activeFilter === 'NOPLOTS')     filtered = filtered.filter(c => (c.plotCount || 0) === 0 && !c.pendingOnly);
        if (activeFilter === 'PENDINGONLY') filtered = filtered.filter(c => !!c.pendingOnly);
        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(c => (c.criticalCount || 0) > 0);
        filtered.sort((a, b) => {
            let aVal, bVal;
            if      (sortConfig.key === 'name')       { aVal = a.name || ''; bVal = b.name || ''; }
            else if (sortConfig.key === 'plotCount')  { aVal = ((a.plots || [])[0] || {}).index || ''; bVal = ((b.plots || [])[0] || {}).index || ''; }   // fix181 (5.10): INDEX sorts by index
            else if (sortConfig.key === 'lastContact'){ aVal = a.lastContact || ''; bVal = b.lastContact || ''; }
            else if (sortConfig.key === 'reliability'){ aVal = a.reliability ?? -1; bVal = b.reliability ?? -1; }
            else if (sortConfig.key === 'owed')       { aVal = Number(a.owed || 0); bVal = Number(b.owed || 0); }
            else                                      { aVal = a[sortConfig.key]; bVal = b[sortConfig.key]; }
            // fix181 (5.10): natural, case-blind order; empty values last in both directions
            const empty = (v) => v === null || v === undefined || v === '';
            if (empty(aVal) && empty(bVal)) return 0;
            if (empty(aVal)) return 1;
            if (empty(bVal)) return -1;
            const cmp = (typeof aVal === 'number' && typeof bVal === 'number') ? aVal - bVal
                : String(aVal).localeCompare(String(bVal), undefined, { numeric: true, sensitivity: 'base' });
            return sortConfig.direction === 'asc' ? cmp : -cmp;
        });
        return filtered;
    }, [rows, searchTerm, activeFilter, sortConfig]);

    const pageData = useMemo(() => processedData.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE), [processedData, page]);

    const handleSort = (key) => setSortConfig(prev => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
    const renderSortIcon = (key) => sortConfig.key !== key ? null
        : (sortConfig.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

    // fix181 (11.4): a row count on every tab, and a PENDING ONLY tab (clients known only from field entries)
    const n = (fn) => rows.filter(fn).length;
    const FILTERS = [
        { key: 'ALL', label: 'ALL CLIENTS ' + rows.length }, { key: 'OWING', label: 'OWING ' + n(c => !!c.owing), accent: 'yellow' },
        { key: 'RECEIVABLES', label: 'IN RECEIVABLES ' + n(c => (c.receivableCount || 0) > 0), accent: 'red' },
        { key: 'CRITICAL', label: 'CRITICAL ' + n(c => (c.criticalCount || 0) > 0), accent: 'red' },
        { key: 'PAID', label: 'PAID UP ' + n(c => !!c.paidUp), accent: 'green' },
        { key: 'NOPLOTS', label: 'NO PROJECTS ' + n(c => (c.plotCount || 0) === 0 && !c.pendingOnly), accent: 'cyan' },
        { key: 'PENDINGONLY', label: 'PENDING ONLY ' + n(c => !!c.pendingOnly), accent: 'cyan' },
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
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Reload every client and their totals" onClick={reload} />
                </HeaderActions>
            </header>

            {/* Control cluster: only .searchBlock is sticky -- filters and
                legend are normal in-flow content and scroll away with the
                page, matching the Project Ledger exactly. */}
            <div className={styles.controlHub}>
                <div className={styles.searchBlock}>
                    <div className={styles.searchInner}>
                        <input type="search" placeholder="Search name, NIN, phone, email or index..." className={styles.searchInput}
                            value={searchTerm} onChange={e => setSearchTerm(e.target.value)} aria-label="Search clients" autoComplete="off" />
                        <FiSearch className={styles.searchIcon} aria-hidden="true" />
                        {searchTerm && (<button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label="Clear search" type="button"><FiX aria-hidden="true" /></button>)}
                    </div>
                </div>
                <TabDock items={FILTERS} value={activeFilter} onChange={setActiveFilter} label="Filter clients" />
                <div className={styles.legendRow}><PaymentHealthLegend /></div>
            </div>

            {/* Table panel -- NOT sticky itself, scrolls away with the page.
                Only the table's own header row (inside .tableScroll) stays
                pinned, and only to ITS OWN scroll container. */}
            <div className={styles.tablePanel} data-tab-accent={accentOf(FILTERS, activeFilter)}>
                {/* fix148: no top pins -- bottom pins + bottom corners only */}
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
                                    <FiLayers aria-hidden="true" /> INDEX {renderSortIcon('plotCount')}
                                </th>
                                <th>STATUS</th>
                                <th onClick={() => handleSort('lastContact')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'lastContact' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    LAST CONTACT {renderSortIcon('lastContact')}
                                </th>
                                <th>SUB-COUNTY</th>
                                {isDirector && (
                                    <th onClick={() => handleSort('owed')} className={styles.sortable}
                                        aria-sort={sortConfig.key === 'owed' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                        <FiCreditCard aria-hidden="true" /> PROGRESS {renderSortIcon('owed')}
                                    </th>
                                )}
                            </tr>
                        </thead>
                        <tbody>
                            {loading && <LoadingRow colSpan={cols} label="SYNCING CLIENT REGISTER..." />}
                            {!loading && loadError && (
                                <tr><td colSpan={cols} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> CLIENT SYNC FAULT{loadCode ? ` (${loadCode})` : ''} —{' '}
                                    <button className={styles.retryBtn} onClick={reload}>RETRY</button>
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
                                const storagePaid = Number(c.storagePaid || 0);
                                const total = Number(c.billed || 0) || (paid + owed);
                                const pct = total > 0 ? Math.min((paid / total) * 100, 100) : 0;
                                const isCritical = (c.criticalCount || 0) > 0;   // fix181 (5.4): the server rule
                                const hasReceivable = (c.receivableCount || 0) > 0;
                                const plotCount = c.plotCount || 0;
                                const recCount = (c.plots || []).filter(p => p.receivable).length;
                                const plotNums = (c.plots || []).map(p => p.index).filter(Boolean);
                                const countyList = [...new Set((c.plots || []).map(p => p.subCounty).filter(Boolean))];
                                return (
                                    <tr key={c.id} onClick={() => navigate(`/client/${c.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/client/${c.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Client: ${c.name}`}
                                        className={hasReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>
                                        <td className={styles.rowNum}>{page * PAGE_SIZE + i + 1}</td>
                                        <td className={styles.plotCell}>
                                            <div className={styles.indexRow}>
                                                <PaymentDot c={c} />
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
                                        <td className={styles.statusCell}>
                                            {plotNums.length === 0 ? <span className={styles.stackSub}>---</span> : (
                                                <div className={styles.stack}>
                                                    {plotNums.map((num, pi) => (
                                                        <span key={pi} className={styles.statusName}>{pi + 1}. {num}</span>
                                                    ))}
                                                </div>
                                            )}
                                        </td>
                                        <td>
                                            {/* One status per row, in priority order -- legal receivables
                                                outrank a low payment rate, which outranks the plain
                                                paid/active split. Titled/folder counts already live on the
                                                plot dots to the left, so they don't repeat here. */}
                                            <div className={styles.statusGroup}>
                                                {/* fix181 (11.4): RECEIVABLES and CRITICAL show together; PENDING ONLY / FEES KEPT replace the old fallbacks */}
                                                {hasReceivable && <span className={styles.tagReceivable}>RECEIVABLES {recCount}</span>}
                                                {isCritical && <span className={styles.tagCritical}>CRITICAL</span>}
                                                {!hasReceivable && !isCritical && (c.pendingOnly ? <span className={styles.tagIdle}>PENDING ONLY</span>
                                                    : plotCount === 0 ? <span className={styles.tagIdle}>NO PROJECTS</span>
                                                    : c.feesKept ? <span className={styles.tagStandard}>FEES KEPT</span>
                                                    : c.paidUp ? <span className={styles.tagPaid}>PAID UP</span>
                                                    : <span className={styles.tagStandard}>ACTIVE</span>)}
                                                {c.recoveryState && (
                                                    <button type="button" className={styles.tagStandard} title="Open this client in Recovery"
                                                        onClick={e => { e.stopPropagation(); navigate('/recovery?client=' + c.id); }}>{c.recoveryState}</button>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.stack}>
                                                <span className={styles.ownerName}>{c.lastContact ? String(c.lastContact).slice(0, 10) : 'NEVER'}</span>
                                                {(c.lastTone === 'POSITIVE' || c.lastTone === 'NEGATIVE') && (
                                                    <span className={`${styles.stackSub} ${c.lastTone === 'NEGATIVE' ? styles.toneTextNeg : styles.toneTextPos}`}>
                                                        {c.lastTag}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td>{countyList.length === 0 ? '---' : countyList.join(', ')}</td>
                                        {isDirector && (
                                            <td className={styles.moneyCell}>
                                                <div className={styles.moneyRow}>
                                                    <span className={styles.debtLabel}>DEBT:</span>
                                                    <span className={isCritical ? styles.debtCritical : styles.debtAmount}>UGX {owed.toLocaleString()}</span>
                                                </div>
                                                {storageFees > 0 && (
                                                    <div className={styles.feesLine}>+UGX {storageFees.toLocaleString()} storage fees{storagePaid > 0 ? ' (UGX ' + storagePaid.toLocaleString() + ' paid)' : ''}</div>
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
