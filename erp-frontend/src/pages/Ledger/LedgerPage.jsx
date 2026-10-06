// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import { PaymentHealthDot, PaymentHealthLegend } from '../../components/common/PaymentHealth';
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight, FiArrowUp, FiArrowDown, FiAlertTriangle, FiX
} from 'react-icons/fi';
import landService from '../../services/landService';
import { cached, remember } from '../../utils/pageCache';
import BackToTopButton from '../../components/common/BackToTopButton';
import { FiRefreshCw } from 'react-icons/fi';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import styles from './LedgerPage.module.css';
import { LoadingRow } from '../../components/common/LoadingState';
import TabDock, { accentOf } from '../../components/common/TabDock';
import { useSwapMotion } from '../../hooks/useTabMotion';
import useTableScrollHandoff from '../../hooks/useTableScrollHandoff';
import { projectTypeOf } from '../../constants/projectTypes';
import { statusOf, moneyWordsOf, hasPrice, MONEY_WORD } from '../../utils/projectStatus';
import { GLOSSARY } from '../../components/common/glossary';

// fix180: the clients (who pay, whom Recovery calls) are the people shown on the ledger; old rows fall back to the owners
const clientsOf = (proj) => ((proj.clients && proj.clients.length) ? proj.clients : (proj.proprietors || []));

const matchesSearch = (proj, term, statuses) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');
    const fields = [
        proj.projectIndex, proj.invoiceNumber, proj.contractNumber,   // fix196: find a project by its invoice or contract number
        proj.landTitle?.plotNumber, proj.landTitle?.block,
        proj.landTitle?.volume, proj.landTitle?.folio, proj.landTitle?.tenure, projectTypeOf(proj).label,
        proj.district, proj.county, proj.subCounty, proj.parish, proj.village, proj.area,
        ...[...clientsOf(proj), ...(proj.proprietors || [])].flatMap(p => [
            p.fullName, p.phoneNumber?.replace(/\s+/g, ''), p.nationalId, p.email, p.homeAddress,
        ]),
        ...(statuses || []).map(s => s.statusName),
    ];
    return fields.some(f => f && f.toLowerCase().replace(/\s+/g, '').includes(t));
};
// fix181 (2.2): the payment dot comes from utils/paymentHealth (server day count, one gradient)
const PAGE_SIZE = 15;
// fix169: the WHOLE ledger is loaded (200 rows per request, every page) and then filtered, sorted and paged
// here in the browser. Before, only one server page of 15 rows was fetched and the filters ran on those 15.
const LOAD_SIZE = 500;   // fix182: the server's largest page, so one call usually brings everything
// fix169: ONE rule for CRITICAL, used by the filter AND by the red tag on each row (they used to disagree:
// receivables showed the tag but were left out of the filter).
// fix171: progress and CRITICAL count only the money paid toward the TITLE work (paid storage fees are not part of the cost)
const titlePaidOf = (p) => Math.max(0, (p.amountPaid || 0) - (p.storageFeesPaid || 0));
// fix181 (5.4): the server decides (LandProject.isCritical); the old formula is only a fallback for an old answer
const isCriticalProject = (p) => (typeof p.critical === 'boolean' ? p.critical : ((p.totalCost || 0) > 0 && (titlePaidOf(p) / p.totalCost) < 0.25));
// fix181 (2.3): PAID = the title work is fully paid (never a project with no price), using the same title-money helper
// as CRITICAL (the server rule is LandProject.isTitleFullyPaid); still not a receivable
const isTitleFullyPaid = (p) => ((p.totalCost || 0) > 0 && titlePaidOf(p) >= p.totalCost) || !!p.landTitle?.isReleased;
const ageDays = (p) => (p.createdAt ? Math.max(0, Math.floor((Date.now() - new Date(p.createdAt).getTime()) / 86400000)) : null);
const PaymentDot = ({ proj }) => <PaymentHealthDot days={proj.daysSincePayment} settled={proj.owedNow != null && Number(proj.owedNow) === 0 && Number(proj.totalCost) > 0} />;
const Pins = ({ pos }) => (
    <div className={pos === 'top' ? styles.pinsTop : styles.pinsBottom} aria-hidden="true">
        {[...Array(4)].map((_, i) => <div key={i} className={styles.pin} />)}
    </div>
);

// fix183: the table scroll rule (page first going down, table first going up, sideways by touch) is the shared hook
// hooks/useTableScrollHandoff.js. This page used to carry its own copy.

const LedgerPage = () => {
    const navigate = useNavigate();
    // fix182 (speed): a return visit draws the last list at once and refreshes it quietly (utils/pageCache.js)
    const [projects, setProjects] = useState(() => cached('ledger') || []);
    const [loading, setLoading] = useState(() => !cached('ledger'));
    const [loadError, setLoadError] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    // fix181 (17.10, 17.20): a link can open a tab (/land/projects?tab=PENDING)
    const [ledgerParams] = useSearchParams();
    const [activeFilter, setActiveFilter] = useState(() => (ledgerParams.get('tab') || 'ALL').toUpperCase());
    const swapRef = useSwapMotion(activeFilter);   // fix192: the list fades in gently when the tab changes
    const [sortConfig, setSortConfig] = useState({ key: 'plotNumber', direction: 'asc' });
    // fix169: a new search / filter / sort always starts from the first page of results.
    // fix182: worked out while drawing (the page number belongs to one search/filter/sort) instead of an effect.
    const filterKey = searchTerm + '|' + activeFilter + '|' + sortConfig.key + '|' + sortConfig.direction;
    const [pageAt, setPageAt] = useState({ key: filterKey, page: 0 });
    const page = pageAt.key === filterKey ? pageAt.page : 0;
    const setPage = (next) => setPageAt(prev => {
        const cur = prev.key === filterKey ? prev.page : 0;
        return { key: filterKey, page: typeof next === 'function' ? next(cur) : next };
    });
    const tableScrollRef = useTableScrollHandoff();

    const fetchLedger = useCallback(async () => {
        // one quiet retry after 5 seconds (the free server may still be waking up), then the error row
        for (let attempt = 0; attempt < 2; attempt += 1) {
            try {
                // fix169: walk every server page so filters / search / sort see ALL projects, not 15 of them.
                const all = [];
                const seen = new Set();
                for (let p = 0; p < 60; p += 1) {
                    const data = await landService.getGlobalLedger(p, LOAD_SIZE);
                    const rows = (data && data.content) || [];
                    rows.forEach(r => { if (!seen.has(r.id)) { seen.add(r.id); all.push(r); } });
                    if (rows.length < LOAD_SIZE || (data && data.last)) break;
                }
                setProjects(remember('ledger', all)); setLoading(false); setLoadError(false);
                return;
            } catch {
                if (attempt === 0) await new Promise(r => setTimeout(r, 5000));
            }
        }
        setLoadError(true); setLoading(false);
    }, []);
    useEffect(() => { Promise.resolve().then(fetchLedger); }, [fetchLedger]);
    // REFRESH / RETRY: the spinner only when nothing is on screen yet
    const reload = () => { if (!projects.length) setLoading(true); setLoadError(false); fetchLedger(); };

    // STATUSES COLUMN (fix47): each row's status list -- exactly the statuses (template + custom) saved from the
    // Intake page. fix182: the ledger answer already carries them (LandService.getGlobalLedger), so the second
    // "statuses-bulk" round trip that used to follow every load is gone.
    const statusMap = useMemo(() => {
        const m = {};
        projects.forEach(p => { if (p && p.id) m[p.id] = p.statuses || []; });
        return m;
    }, [projects]);

    const processedData = useMemo(() => {
        let filtered = projects.filter(p => matchesSearch(p, searchTerm, statusMap[p.id]));
        // fix181 (2.1): ONE rule first -- Pending projects show ONLY in the PENDING tab (oldest first, 12.3)
        if (activeFilter === 'PENDING') {
            return filtered.filter(p => !!p.pending)
                .sort((a, b) => String(a.createdAt || '').localeCompare(String(b.createdAt || '')));
        }
        filtered = filtered.filter(p => !p.pending);
        if (activeFilter === 'BACKLOG')     filtered = filtered.filter(p => !p.landTitle);
        if (activeFilter === 'TITLED')      filtered = filtered.filter(p => !!p.landTitle && !p.isLegacy);
        if (activeFilter === 'LEGACY')      filtered = filtered.filter(p => p.isLegacy);
        if (activeFilter === 'PAID')        filtered = filtered.filter(p => isTitleFullyPaid(p) && !p.isReceivable);
        if (activeFilter === 'RECEIVABLES') filtered = filtered.filter(p => p.isReceivable);
        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(isCriticalProject);
        if (activeFilter === 'PROBLEM')     filtered = filtered.filter(p => !!p.problem);
        filtered.sort((a, b) => {
            let aVal, bVal;
            if      (sortConfig.key === 'plotNumber') { aVal = a.landTitle?.plotNumber || a.projectIndex || ''; bVal = b.landTitle?.plotNumber || b.projectIndex || ''; }
            else if (sortConfig.key === 'owner')      { aVal = clientsOf(a)[0]?.fullName || ''; bVal = clientsOf(b)[0]?.fullName || ''; }
            else if (sortConfig.key === 'paid')       { aVal = a.amountPaid || 0; bVal = b.amountPaid || 0; }
            else                                      { aVal = a[sortConfig.key]; bVal = b[sortConfig.key]; }
            // fix181 (2.4): natural order ("Plot 20" before "Plot 100"), empty values always last
            const empty = (v) => v === null || v === undefined || v === '';
            if (empty(aVal) && empty(bVal)) return 0;
            if (empty(aVal)) return 1;
            if (empty(bVal)) return -1;
            const cmp = (typeof aVal === 'number' && typeof bVal === 'number') ? aVal - bVal
                : String(aVal).localeCompare(String(bVal), undefined, { numeric: true, sensitivity: 'base' });
            return sortConfig.direction === 'asc' ? cmp : -cmp;
        });
        return filtered;
    }, [projects, searchTerm, activeFilter, sortConfig, statusMap]);

    // fix169: pages are cut from the FILTERED list, so every filter spans the whole ledger
    const pageData = useMemo(() => processedData.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE), [processedData, page]);

    const handleSort = (key) => setSortConfig(prev => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
    const renderSortIcon = (key) => sortConfig.key !== key ? null
        : (sortConfig.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

    const FILTERS = [
        { key: 'ALL', label: 'ALL PROJECTS' }, { key: 'BACKLOG', label: 'NO TITLE DETAILS', accent: 'yellow', title: 'Projects with no title details saved yet' },
        { key: 'TITLED', label: 'HAS TITLE DETAILS', accent: 'green', title: 'Projects whose title details (plot, block, area ...) are saved. Not the same as the stage called Titled.' }, { key: 'LEGACY', label: 'LEGACY', accent: 'cyan' },
        { key: 'RECEIVABLES', label: 'RECEIVABLES', accent: 'red' }, { key: 'CRITICAL', label: 'CRITICAL', accent: 'red' },
        { key: 'PAID', label: 'PAID', accent: 'green' }, { key: 'PROBLEM', label: 'PROBLEM', accent: 'red' },
        { key: 'PENDING', label: 'PENDING ' + projects.filter(p => p.pending).length, accent: 'yellow' },   // fix181 (2.1)
    ];

    return (
        <div className={styles.container}>
            {/* Page title -- scrolls away */}
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Project Ledger</h1>
                    <p className={styles.subtitle}>Every project — folder to release, live payment health</p>
                </div>
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Reload the ledger" onClick={reload} />
                </HeaderActions>
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
                <TabDock items={FILTERS} value={activeFilter} onChange={setActiveFilter} label="Filter records" />
                <div className={styles.legendRow}><PaymentHealthLegend /></div>
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
            <div className={styles.tablePanel} data-tab-accent={accentOf(FILTERS, activeFilter)} ref={swapRef}>
                {/* fix148: no top pins -- bottom pins + bottom corners only */}
                <div className={styles.decorBl} aria-hidden="true" />
                <div className={styles.decorBr} aria-hidden="true" />
                <div className={styles.tableScroll} ref={tableScrollRef}>
                    <table className={styles.ledgerTable} aria-label="Project ledger" aria-rowcount={processedData.length}>
                        <thead>
                            <tr>
                                <th className={`${styles.rowNum} gsHidePhone`}>#</th>
                                <th onClick={() => handleSort('plotNumber')} className={`${styles.sortable} gsStickyCol`}
                                    aria-sort={sortConfig.key === 'plotNumber' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiMapPin aria-hidden="true" /> INDEX {renderSortIcon('plotNumber')}
                                </th>
                                <th onClick={() => handleSort('owner')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'owner' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiUser aria-hidden="true" /> CLIENT(S) {renderSortIcon('owner')}
                                </th>
                                <th>PHONE</th>
                                <th>PARISH</th>
                                <th>VILLAGE</th>
                                <th title={GLOSSARY.STATUS}>STATUS</th>
                                <th title={GLOSSARY.STAGE + ' This column shows the stage the project is on now; the dots are all its stages.'}><FiLayers aria-hidden="true" /> STAGE</th>
                                <th onClick={() => handleSort('paid')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'paid' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiCreditCard aria-hidden="true" /> PROGRESS {renderSortIcon('paid')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && <LoadingRow colSpan={9} label="SYNCING ARCHIVE..." />}
                            {!loading && loadError && (
                                <tr><td colSpan={9} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> LEDGER SYNC FAULT —{' '}
                                    <button className={styles.retryBtn} onClick={reload}>RETRY</button>
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.length === 0 && (
                                <tr><td colSpan={9} className={styles.emptyCell}>
                                    <FiLayers aria-hidden="true" />
                                    {searchTerm ? `NO RECORDS MATCH "${searchTerm.toUpperCase()}"` : 'NO RECORDS FOUND'}
                                </td></tr>
                            )}
                            {!loading && !loadError && pageData.map((proj, i) => {
                                const isReceivable = proj.isReceivable;
                                const storageFees = Number(proj.storageFeesAccumulated || 0);
                                // fix182: owed comes from the server's one money rule (LandProject.owedNow, never below 0)
                                const debt = proj.owedNow != null ? Number(proj.owedNow)
                                    : Math.max(0, isReceivable ? (proj.totalCost || 0) + storageFees - (proj.amountPaid || 0) : (proj.totalCost || 0) - (proj.amountPaid || 0));
                                const pct = proj.totalCost > 0 ? Math.min((titlePaidOf(proj) / proj.totalCost) * 100, 100) : 0;
                                const isCritical = isCriticalProject(proj);
                                const status = statusOf(proj);
                                const moneyWords = moneyWordsOf(proj);
                                const WORD_CLASS = { PENDING: styles.tagWaiting, ACTIVE: styles.tagStandard, RECEIVABLES: styles.tagReceivable, HANDED_OVER: styles.tagReleased, DELETED: styles.tagCritical, NO_PRICE: styles.tagWaiting, FULLY_PAID: styles.tagPaid, CRITICAL: styles.tagCritical };
                                const people = clientsOf(proj);
                                const names  = people.map(p => p.fullName).filter(Boolean);
                                const nins   = people.map(p => p.nationalId).filter(Boolean);
                                const phones = people.flatMap(p => (p.phoneNumber || '').split('/').map(s => s.trim()).filter(Boolean));
                                const statuses = (statusMap[proj.id] || []).map(s => ({ ...s, done: !!(s.isCompleted ?? s.completed) })).sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
                                const curStatusIdx = statuses.findIndex(s => !s.done);
                                const curStatus = curStatusIdx >= 0 ? statuses[curStatusIdx] : null;
                                return (
                                    <tr key={proj.id} onClick={() => navigate(proj.pending ? `/pending/${proj.id}` : `/folder/${proj.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(proj.pending ? `/pending/${proj.id}` : `/folder/${proj.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Record: ${proj.projectIndex || proj.landTitle?.plotNumber}`}
                                        className={proj.problem ? styles.rowProblem : isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>
                                        <td className={`${styles.rowNum} gsHidePhone`}>{page * PAGE_SIZE + i + 1}</td>
                                        <td className={`${styles.plotCell} gsStickyCol`}>
                                            <div className={styles.indexRow}>
                                                <PaymentDot proj={proj} />
                                                <div className={styles.stack}>
                                                    <strong>#{proj.projectIndex || '---'}</strong>
                                                    <span className={styles.stackSub} title="Project type">{projectTypeOf(proj).label.toUpperCase()}</span>
                                                    {proj.invoiceNumber && <span className={styles.stackSub} title="Invoice number">INV {proj.invoiceNumber}</span>}
                                                    {proj.contractNumber && <span className={styles.stackSub} title="Contract number">CON {proj.contractNumber}</span>}
                                                    {proj.pending && <span className={styles.stackSub} title="How long this entry has been waiting for the office">PENDING {ageDays(proj) != null ? '- ' + ageDays(proj) + ' DAY(S)' : ''}</span>}
                                                    {proj.problem && <span className={styles.problemTag}>PROBLEM</span>}
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
                                            {/* fix184: ONE status per project (PENDING / ACTIVE / RECEIVABLES / HANDED OVER) and under it the money
                                                word, both from utils/projectStatus.js with their hover explainers. A project with no price says
                                                WAITING FOR PRICES; it used to say FULLY PAID ("owes 0" was read as "paid"). */}
                                            <div className={styles.statusGroup}>
                                                <span className={WORD_CLASS[status.key] || styles.tagStandard} title={status.tip}>{status.label}</span>
                                                {moneyWords.map(w => <span key={w.key} className={WORD_CLASS[w.key] || styles.tagStandard} title={w.tip}>{w.label}</span>)}
                                            </div>
                                        </td>
                                        <td className={styles.statusCell}>
                                            {statuses.length === 0 ? <span className={styles.stackSub}>---</span> : (
                                                <div className={styles.stack}>
                                                    <span className={styles.statusName} title={statuses.map(s => s.statusName + (s.done ? ' ✓' : '')).join(' · ')}>
                                                        {curStatus ? curStatus.statusName : 'COMPLETE'}
                                                    </span>
                                                    <span className={styles.statusDots}>
                                                        {statuses.map((s, si) => (
                                                            <span key={s.id || si} className={`${styles.statusDot} ${s.done ? (statuses.every(x => x.done) ? styles.statusDotDone : styles.statusDotPart) : si === curStatusIdx ? styles.statusDotCurrent : ''}`} />
                                                        ))}
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                        {!hasPrice(proj) ? (
                                            /* fix184: no price = no debt figure and no 0% bar; a quiet "no price yet" instead */
                                            <td className={styles.moneyCell}><span className={styles.tagWaiting} title={MONEY_WORD.NO_PRICE.tip}>NO PRICE YET</span></td>
                                        ) : (
                                        <td className={styles.moneyCell}>
                                            <div className={styles.moneyRow}>
                                                <span className={styles.debtLabel}>DEBT:</span>
                                                <span className={isCritical ? styles.debtCritical : styles.debtAmount}>UGX {debt.toLocaleString()}</span>
                                            </div>
                                            {isReceivable && proj.storageFeesAccumulated > 0 && (
                                                <div className={styles.feesLine}>+UGX {Number(proj.storageFeesAccumulated).toLocaleString()} storage fees{Number(proj.storageFeesPaid || 0) > 0 ? ' (UGX ' + Number(proj.storageFeesPaid).toLocaleString() + ' paid)' : ''}</div>
                                            )}
                                            <div className={styles.velocityBar} role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
                                                <div className={`${styles.velocityFill} ${isCritical ? styles.velocityFillCritical : ''}`} style={{ width: `${pct}%` }} />
                                            </div>
                                            <span className={styles.pctLabel}>{Math.round(pct)}%</span>
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
                        {processedData.length > 0 && <span className={styles.recordCount}> — {processedData.length} RECORDS</span>}
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
export default LedgerPage;
