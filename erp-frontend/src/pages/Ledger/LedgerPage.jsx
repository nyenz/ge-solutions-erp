// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight, FiArrowUp, FiArrowDown, FiClock, FiAlertTriangle, FiX
} from 'react-icons/fi';
import landService from '../../services/landService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './LedgerPage.module.css';

const matchesSearch = (proj, term) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');
    const fields = [
        proj.projectIndex, proj.landTitle?.plotNumber, proj.landTitle?.titleId,
        proj.landTitle?.blockRoad, proj.landTitle?.tenure,
        proj.district, proj.county, proj.subCounty, proj.parish, proj.village, proj.area,
        ...(proj.proprietors || []).flatMap(p => [
            p.fullName, p.phoneNumber?.replace(/\s+/g, ''), p.nationalId, p.email, p.homeAddress,
        ]),
    ];
    return fields.some(f => f && f.toLowerCase().replace(/\s+/g, '').includes(t));
};
const getPaymentBadge = (proj) => {
    if (!proj.lastPaymentDate) return 'RED';
    const days = Math.floor((Date.now() - new Date(proj.lastPaymentDate)) / 86400000);
    if (days <= 14) return 'GREEN';
    if (days <= 30) return 'YELLOW';
    return 'RED';
};
const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Recent payment', YELLOW: 'Payment 2-4 weeks ago', RED: 'No recent payment' };
const PAGE_SIZE = 15;
const PaymentDot = ({ proj }) => {
    const badge = getPaymentBadge(proj);
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

// -- SCROLL PARENT DISCOVERY (fix37) ------------------------------------
// The app's real scrolling element is Shell's .scrollArea (overflow-y:
// auto) -- the outer .shell is height:100vh with overflow:hidden, so
// document/window never actually scrolls at all. The old fix36 code used
// document.scrollingElement, which meant its "page scroll" branch was
// always a no-op -- this is why scrolling up used to dead-end once the
// table hit its own top. Walking up from the table to find the nearest
// real scrolling ancestor fixes that, and keeps working no matter how
// deeply the page is nested, on any screen size, without hardcoding a
// class name.
function findScrollParent(el) {
    let node = el ? el.parentElement : null;
    while (node && node !== document.body && node !== document.documentElement) {
        const overflowY = window.getComputedStyle(node).overflowY;
        if (overflowY === 'auto' || overflowY === 'scroll') return node;
        node = node.parentElement;
    }
    return document.scrollingElement || document.documentElement;
}

// -- DIRECTIONAL SCROLL HANDOFF (fix41) ---------------------------------
// Reverted to match the approved design mockup exactly:
//   - scrolling DOWN -> the PAGE scrolls first; the table only takes
//                         over once the page has hit its own bottom edge.
//   - scrolling UP   -> the TABLE scrolls first (inverse); the page only
//                         takes over once the table has hit its own top
//                         edge.
// (findScrollParent above is still used instead of the mockup's plain
// document.scrollingElement -- the mockup is a bare HTML page where the
// document itself really does scroll, but inside the real app the page
// scrolls inside Shell's .scrollArea, so that's the element this needs
// to drive for the behavior to actually match the mockup.)
// This is done in JS (not left to native scroll-chaining) because a fast
// flick/fling handed off mid-gesture by the browser's own chaining can
// dump un-damped momentum onto the page and skip past the toolbar --
// `overscroll-behavior: contain` on .tableScroll (see CSS) blocks that
// native handoff so every bit of table<->page scrolling goes through
// this clamped routing instead, identically across browsers and screen
// sizes.
function useDirectionalScrollHandoff(scrollRef) {
    useEffect(() => {
        const tableScroll = scrollRef.current;
        if (!tableScroll) return undefined;
        const pageScroll = findScrollParent(tableScroll);

        // small buffer so sub-pixel rounding (common on mobile/high-DPI
        // screens) can never leave a scroller "stuck" a few px short of
        // its true edge
        const EDGE_TOLERANCE = 2;

        const pageAtTop = () => pageScroll.scrollTop <= EDGE_TOLERANCE;
        const pageAtBottom = () =>
            pageScroll.scrollTop + pageScroll.clientHeight >= pageScroll.scrollHeight - EDGE_TOLERANCE;
        const tableAtTop = () => tableScroll.scrollTop <= EDGE_TOLERANCE;
        const tableAtBottom = () =>
            tableScroll.scrollTop + tableScroll.clientHeight >= tableScroll.scrollHeight - EDGE_TOLERANCE;

        // deltaY units differ across browsers: deltaMode 0 = pixels
        // (Chrome/Safari, ~100-120px per notch), 1 = lines (Firefox,
        // ~3/tick), 2 = pages. Normalize to pixels so the same physical
        // scroll produces the same jump size everywhere.
        const normalizeWheelDelta = (e) => {
            const LINE_HEIGHT = 16;
            if (e.deltaMode === 1) return e.deltaY * LINE_HEIGHT;
            if (e.deltaMode === 2) return e.deltaY * window.innerHeight;
            return e.deltaY;
        };

        // Even with units normalized, a fast flick/fling (or a
        // high-precision touchpad) can still report one huge deltaY in a
        // single event -- capping the max px moved per event keeps every
        // programmatic step roughly the same size as a normal native step.
        const MAX_STEP_PX = 120;
        const clampStep = (px) => Math.sign(px) * Math.min(Math.abs(px), MAX_STEP_PX);

        // deltaY convention: positive = scrolling down, negative = up
        const routeDelta = (deltaY, e) => {
            if (deltaY > 0) {
                // scrolling down: PAGE has priority until it bottoms out
                if (!pageAtBottom()) {
                    pageScroll.scrollTop += clampStep(deltaY);
                    e.preventDefault();
                    return;
                }
                if (tableAtBottom()) return; // nothing left to scroll anywhere
                tableScroll.scrollTop += clampStep(deltaY);
                e.preventDefault();
            } else if (deltaY < 0) {
                // scrolling up: TABLE has priority (inverse) until it
                // hits its own top edge -- only then hand off to the page
                if (!tableAtTop()) {
                    tableScroll.scrollTop += clampStep(deltaY);
                    e.preventDefault();
                    return;
                }
                if (pageAtTop()) return; // nothing left to scroll anywhere
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
            // finger moving UP the screen means content scrolls DOWN --
            // same sign convention as wheel's deltaY. Touch deltas are
            // already in CSS pixels, no unit normalization needed.
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

const LedgerPage = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [page, setPage] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [sortConfig, setSortConfig] = useState({ key: 'plotNumber', direction: 'asc' });
    const tableScrollRef = useRef(null);
    useDirectionalScrollHandoff(tableScrollRef);

    const fetchLedger = useCallback(async (attempt = 0) => {
        setLoading(true); setLoadError(false);
        try {
            const data = await landService.getGlobalLedger(page, PAGE_SIZE);
            setProjects(data.content || []); setLoading(false);
        } catch {
            if (attempt < 1) { setTimeout(() => fetchLedger(attempt + 1), 5000); return; }
            setLoadError(true); setLoading(false);
        }
    }, [page]);
    useEffect(() => { fetchLedger(); }, [fetchLedger]);

    const processedData = useMemo(() => {
        let filtered = projects.filter(p => matchesSearch(p, searchTerm));
        if (activeFilter === 'BACKLOG')     filtered = filtered.filter(p => !p.landTitle);
        if (activeFilter === 'TITLED')      filtered = filtered.filter(p => !!p.landTitle && !p.isLegacy);
        if (activeFilter === 'LEGACY')      filtered = filtered.filter(p => p.isLegacy);
        if (activeFilter === 'PAID')        filtered = filtered.filter(p => (p.amountPaid >= p.totalCost || p.landTitle?.isReleased) && !p.isReceivable);
        if (activeFilter === 'RECEIVABLES') filtered = filtered.filter(p => p.isReceivable);
        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25);
        filtered.sort((a, b) => {
            let aVal, bVal;
            if      (sortConfig.key === 'plotNumber') { aVal = a.landTitle?.plotNumber || a.projectIndex || ''; bVal = b.landTitle?.plotNumber || b.projectIndex || ''; }
            else if (sortConfig.key === 'owner')      { aVal = a.proprietors?.[0]?.fullName || ''; bVal = b.proprietors?.[0]?.fullName || ''; }
            else if (sortConfig.key === 'paid')       { aVal = a.amountPaid || 0; bVal = b.amountPaid || 0; }
            else                                      { aVal = a[sortConfig.key]; bVal = b[sortConfig.key]; }
            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ?  1 : -1;
            return 0;
        });
        return filtered;
    }, [projects, searchTerm, activeFilter, sortConfig]);

    const handleSort = (key) => setSortConfig(prev => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
    const renderSortIcon = (key) => sortConfig.key !== key ? null
        : (sortConfig.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

    const FILTERS = [
        { key: 'ALL', label: 'ALL PROJECTS' }, { key: 'BACKLOG', label: 'BACKLOG' },
        { key: 'TITLED', label: 'TITLED' }, { key: 'LEGACY', label: 'LEGACY' },
        { key: 'RECEIVABLES', label: 'RECEIVABLES' }, { key: 'CRITICAL', label: 'CRITICAL' },
        { key: 'PAID', label: 'PAID' },
    ];

    return (
        <div className={styles.container}>
            {/* Page title -- scrolls away */}
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Project Ledger</h1>
                    <p className={styles.subtitle}>Every project — folder to release, live payment health</p>
                </div>
            </header>

            {/* Control cluster (fix42): only .searchBlock is sticky (see
                CSS) -- filters and legend are normal in-flow content and
                scroll away with the page. Only 2 things are sticky on
                this page in total: the search bar here, and the table's
                own column header row below (inside .tableScroll, pinned
                to its own scroll container, never to the viewport). */}
            <div className={styles.controlHub}>
                <div className={styles.searchBlock}>
                    <div className={styles.searchInner}>
                        <input type="search" placeholder="Search any field..." className={styles.searchInput}
                            value={searchTerm} onChange={e => setSearchTerm(e.target.value)} aria-label="Search ledger records" autoComplete="off" />
                        <FiSearch className={styles.searchIcon} aria-hidden="true" />
                        {searchTerm && (<button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label="Clear search" type="button"><FiX aria-hidden="true" /></button>)}
                    </div>
                </div>
                <div className={styles.filterRail} role="group" aria-label="Filter records">
                    {FILTERS.map(f => (
                        <button key={f.key} onClick={() => setActiveFilter(f.key)}
                            className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}
                            aria-pressed={activeFilter === f.key} aria-label={f.label}>{f.label}</button>
                    ))}
                </div>
                <div className={styles.legendRow} aria-label="Payment health legend">
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (
                        <span key={k} className={styles.legendItem}>
                            <span className={styles.legendDot} style={{ background: c, boxShadow: `0 0 4px ${c}` }} /> {BADGE_LABELS[k]}
                        </span>
                    ))}
                </div>
            </div>

            {/* Table panel (fix42): NOT sticky itself -- scrolls away with
                the page. Only the table's own header row (inside
                .tableScroll below) stays pinned, and only to ITS OWN
                scroll container, never to the viewport.

                Border/corner decor -- now correctly scoped to THIS card
                (fixed in fix42 by adding position:relative to
                .tablePanel in the CSS; without it, these absolutely-
                positioned pieces were attaching to a positioned ancestor
                much higher up the page instead of this card, which is
                why they looked like they belonged to the page rather
                than the table): .tablePanel keeps its full 1.5px
                orange-tinted border all the way around; 4 pin marks
                render at BOTH the top and bottom center edges of THIS
                card; the bracket-style corner decor (with a small
                glowing dot at the tip) renders ONLY on the two bottom
                corners of THIS card -- no top corner brackets. */}
            <div className={styles.tablePanel}>
                <Pins pos="top" />
                <div className={styles.decorBl} aria-hidden="true" />
                <div className={styles.decorBr} aria-hidden="true" />
                <div className={styles.tableScroll} ref={tableScrollRef}>
                    <table className={styles.ledgerTable} aria-label="Project ledger" aria-rowcount={processedData.length}>
                        <thead>
                            <tr>
                                <th className={styles.rowNum}>#</th>
                                <th onClick={() => handleSort('plotNumber')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'plotNumber' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiMapPin aria-hidden="true" /> INDEX {renderSortIcon('plotNumber')}
                                </th>
                                <th onClick={() => handleSort('owner')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'owner' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiUser aria-hidden="true" /> OWNER(S) {renderSortIcon('owner')}
                                </th>
                                <th>PHONE</th>
                                <th>PARISH</th>
                                <th>VILLAGE</th>
                                <th>STATUS</th>
                                <th onClick={() => handleSort('paid')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'paid' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiCreditCard aria-hidden="true" /> PROGRESS {renderSortIcon('paid')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && (<tr><td colSpan={8} className={styles.loadingCell}><FiClock aria-hidden="true" /> SYNCING ARCHIVE...</td></tr>)}
                            {!loading && loadError && (
                                <tr><td colSpan={8} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> LEDGER SYNC FAULT —{' '}
                                    <button className={styles.retryBtn} onClick={() => fetchLedger()}>RETRY</button>
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.length === 0 && (
                                <tr><td colSpan={8} className={styles.emptyCell}>
                                    <FiLayers aria-hidden="true" />
                                    {searchTerm ? `NO RECORDS MATCH "${searchTerm.toUpperCase()}"` : 'NO RECORDS FOUND'}
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.map((proj, i) => {
                                const isReceivable = proj.isReceivable;
                                const storageFees = Number(proj.storageFeesAccumulated || 0);
                                const debt = isReceivable ? (proj.totalCost || 0) + storageFees - (proj.amountPaid || 0) : (proj.totalCost || 0) - (proj.amountPaid || 0);
                                const pct = proj.totalCost > 0 ? Math.min(((proj.amountPaid || 0) / proj.totalCost) * 100, 100) : 0;
                                const isCritical = pct < 25 && proj.totalCost > 0;
                                const names  = (proj.proprietors || []).map(p => p.fullName).filter(Boolean);
                                const nins   = (proj.proprietors || []).map(p => p.nationalId).filter(Boolean);
                                const phones = (proj.proprietors || []).flatMap(p => (p.phoneNumber || '').split('/').map(s => s.trim()).filter(Boolean));
                                return (
                                    <tr key={proj.id} onClick={() => navigate(`/folder/${proj.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/folder/${proj.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Record: ${proj.projectIndex || proj.landTitle?.plotNumber}`}
                                        className={isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>
                                        <td className={styles.rowNum}>{page * PAGE_SIZE + i + 1}</td>
                                        <td className={styles.plotCell}>
                                            <div className={styles.indexRow}>
                                                <PaymentDot proj={proj} />
                                                <div className={styles.stack}>
                                                    <strong>#{proj.projectIndex || '---'}</strong>
                                                    {nins.length ? nins.map((nn, i) => <span key={i} className={styles.stackSub}>{nn}</span>) : <span className={styles.stackSub}>---</span>}
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.stack}>
                                                {names.length ? names.map((nm, i) => <span key={i} className={i === 0 ? styles.ownerName : styles.stackSub}>{nm}</span>) : <span className={styles.ownerName}>---</span>}
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.stack}>
                                                {phones.length ? phones.map((ph, i) => <span key={i} className={styles.ownerPhone}>{ph}</span>) : <span className={styles.ownerPhone}>---</span>}
                                            </div>
                                        </td>
                                        <td><span className={styles.ownerName}>{proj.parish || '---'}</span></td>
                                        <td><span className={styles.ownerName}>{proj.village || '---'}</span></td>
                                        <td>
                                            <div className={styles.statusGroup}>
                                                {isReceivable && <span className={styles.tagReceivable}>RECEIVABLES</span>}
                                                {!isReceivable && proj.landTitle?.isReleased && <span className={styles.tagPaid}>RELEASED</span>}
                                                {!isReceivable && !proj.landTitle?.isReleased && (proj.amountPaid || 0) >= (proj.totalCost || 0) && <span className={styles.tagPaid}>FULLY PAID</span>}
                                                {!isReceivable && (proj.amountPaid || 0) < (proj.totalCost || 0) && <span className={styles.tagStandard}>ACTIVE</span>}
                                                {isCritical && <span className={styles.tagCritical}>CRITICAL</span>}
                                            </div>
                                        </td>
                                        <td className={styles.moneyCell}>
                                            <div className={styles.moneyRow}>
                                                <span className={styles.debtLabel}>DEBT:</span>
                                                <span className={isCritical ? styles.debtCritical : styles.debtAmount}>UGX {debt.toLocaleString()}</span>
                                            </div>
                                            {isReceivable && proj.storageFeesAccumulated > 0 && (
                                                <div className={styles.feesLine}>+UGX {Number(proj.storageFeesAccumulated).toLocaleString()} storage fees</div>
                                            )}
                                            <div className={styles.velocityBar} role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
                                                <div className={`${styles.velocityFill} ${isCritical ? styles.velocityFillCritical : ''}`} style={{ width: `${pct}%` }} />
                                            </div>
                                            <span className={styles.pctLabel}>{Math.round(pct)}%</span>
                                        </td>
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
                        {processedData.length > 0 && <span className={styles.recordCount}> — {processedData.length} RECORDS</span>}
                    </span>
                    <button onClick={() => setPage(p => p + 1)} disabled={processedData.length < PAGE_SIZE} aria-label="Next page" className={styles.pageBtn}>
                        NEXT <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
            </div>
            <BackToTopButton />
        </div>
    );
};
export default LedgerPage;
