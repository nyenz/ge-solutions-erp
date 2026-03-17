// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight, FiActivity,
    FiArrowUp, FiArrowDown, FiArchive, FiClock, FiUsers,
    FiAlertTriangle, FiX
} from 'react-icons/fi';
import HardwarePanel from '../../components/ui/HardwarePanel';
import landService from '../../services/landService';
import styles from './LedgerPage.module.css';

/**
 * GOLDEN SEED — INDUSTRIAL INTELLIGENCE LEDGER (V2.5)
 * ERP Standard compliant + extended search:
 * - Searches: plot ID, ALL owner names, ALL phones, ALL NIDs,
 *   ALL emails, box number, district, county, block/road, tenure
 * - CRITICAL filter button added (was in logic but missing from UI)
 * - warmBoot animation on container
 * - clamp() on all fluid sizes
 * - DM Sans / Space Mono / Cinzel font families declared
 * - font-weight 800+ minimum on all UI text
 * - focus-visible on table rows and all interactive elements
 * - aria-label on search, pagination, filter buttons
 * - aria-hidden on all decorative icons
 * - Duplicate CSS classes eliminated
 */

// ─── SEARCH ENGINE ─────────────────────────────────────────────────
// Matches against every meaningful text field across ALL owners,
// not just the primary (index 0). Normalises to lowercase for case-
// insensitive matching. Phone numbers are stripped of spaces so
// "0712 345" matches "0712345678".
const matchesSearch = (proj, term) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');

    const fields = [
        proj.landTitle?.plotNumber,
        proj.landTitle?.physicalBoxNumber,
        proj.landTitle?.district,
        proj.landTitle?.county,
        proj.landTitle?.blockRoad,
        proj.landTitle?.tenure,
        ...(proj.proprietors || []).flatMap(p => [
            p.fullName,
            p.phoneNumber?.replace(/\s+/g, ''),
            p.nationalId,
            p.email,
            p.homeAddress,
        ]),
    ];

    return fields.some(f => f && f.toLowerCase().replace(/\s+/g, '').includes(t));
};

// ─── MAIN PAGE ──────────────────────────────────────────────────────
const LedgerPage = () => {
    const navigate = useNavigate();

    const [projects,    setProjects]    = useState([]);
    const [loading,     setLoading]     = useState(true);
    const [loadError,   setLoadError]   = useState(false);
    const [page,        setPage]        = useState(0);
    const [searchTerm,  setSearchTerm]  = useState('');
    const [activeFilter,setActiveFilter]= useState('ALL');
    const [sortConfig,  setSortConfig]  = useState({ key: 'plotNumber', direction: 'asc' });

    const fetchLedger = useCallback(async () => {
        setLoading(true);
        setLoadError(false);
        try {
            const data = await landService.getGlobalLedger(page, 50);
            setProjects(data.content || []);
        } catch {
            setLoadError(true);
        } finally {
            setLoading(false);
        }
    }, [page]);

    useEffect(() => { fetchLedger(); }, [fetchLedger]);

    const processedData = useMemo(() => {
        let filtered = projects.filter(p => matchesSearch(p, searchTerm));

        if (activeFilter === 'LEGACY')   filtered = filtered.filter(p => p.isLegacy);
        if (activeFilter === 'DEBTORS')  filtered = filtered.filter(p => p.amountPaid < p.totalCost);
        if (activeFilter === 'CRITICAL') filtered = filtered.filter(p => (p.amountPaid / p.totalCost) < 0.25);

        filtered.sort((a, b) => {
            let aVal, bVal;
            if      (sortConfig.key === 'plotNumber') { aVal = a.landTitle?.plotNumber || ''; bVal = b.landTitle?.plotNumber || ''; }
            else if (sortConfig.key === 'owner')      { aVal = a.proprietors?.[0]?.fullName || ''; bVal = b.proprietors?.[0]?.fullName || ''; }
            else if (sortConfig.key === 'paid')       { aVal = a.amountPaid || 0; bVal = b.amountPaid || 0; }
            else                                      { aVal = a[sortConfig.key]; bVal = b[sortConfig.key]; }
            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ?  1 : -1;
            return 0;
        });

        return filtered;
    }, [projects, searchTerm, activeFilter, sortConfig]);

    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
        }));
    };

    const renderSortIcon = (key) => {
        if (sortConfig.key !== key) return null;
        return sortConfig.direction === 'asc'
            ? <FiArrowUp  className={styles.sortActive} aria-hidden="true" />
            : <FiArrowDown className={styles.sortActive} aria-hidden="true" />;
    };

    // Search hint — shown below input to tell user what fields are searchable
    const SEARCH_HINT = 'Plot ID · Box · Owner name · Phone · NIN · Email · District · County · Tenure';

    const FILTERS = [
        { key: 'ALL',      label: 'ALL ARCHIVES', icon: <FiLayers   aria-hidden="true" /> },
        { key: 'LEGACY',   label: 'BACKLOG',       icon: <FiArchive  aria-hidden="true" /> },
        { key: 'DEBTORS',  label: 'UNPAID',        icon: <FiActivity aria-hidden="true" /> },
        { key: 'CRITICAL', label: 'CRITICAL',      icon: <FiAlertTriangle aria-hidden="true" /> },
    ];

    return (
        <div className={styles.container}>

            {/* ── PAGE HEADER ── */}
            <header className={styles.header}>
                <h1 className={styles.title}>Digital Asset Ledger</h1>
                <p className={styles.subtitle}>Unified Storage Recovery &amp; Debt Tracking</p>
            </header>

            {/* ── CONTROL HUB ── */}
            <div className={styles.controlHub}>

                {/* Search */}
                <div className={styles.searchBlock}>
                    <div className={styles.searchInner}>
                        <FiSearch className={styles.searchIcon} aria-hidden="true" />
                        <input
                            type="search"
                            id="ledger-search"
                            placeholder="Search by plot, name, phone, NIN, box, district..."
                            className={styles.searchInput}
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            aria-label="Search ledger records"
                            aria-describedby="ledger-search-hint"
                            autoComplete="off"
                        />
                        {searchTerm && (
                            <button
                                className={styles.searchClearBtn}
                                onClick={() => setSearchTerm('')}
                                aria-label="Clear search"
                                type="button"
                            >
                                <FiX aria-hidden="true" />
                            </button>
                        )}
                    </div>
                    <p id="ledger-search-hint" className={styles.searchHint}>
                        {SEARCH_HINT}
                    </p>
                </div>

                {/* Filter rail */}
                <div className={styles.filterRailContainer}>
                    <div className={styles.filterRail} role="group" aria-label="Filter records">
                        {FILTERS.map(f => (
                            <button
                                key={f.key}
                                onClick={() => setActiveFilter(f.key)}
                                className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}
                                aria-pressed={activeFilter === f.key}
                                aria-label={f.label}
                            >
                                {f.icon} {f.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── TABLE ── */}
            <HardwarePanel variant="dark">
                <div className={styles.tableScroll}>
                    <table
                        className={styles.ledgerTable}
                        aria-label="Land records ledger"
                        aria-rowcount={processedData.length}
                    >
                        <thead>
                            <tr>
                                <th
                                    onClick={() => handleSort('plotNumber')}
                                    className={styles.sortable}
                                    aria-sort={sortConfig.key === 'plotNumber' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                                >
                                    <FiMapPin aria-hidden="true" /> PLOT ID {renderSortIcon('plotNumber')}
                                </th>
                                <th
                                    onClick={() => handleSort('owner')}
                                    className={styles.sortable}
                                    aria-sort={sortConfig.key === 'owner' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                                >
                                    <FiUser aria-hidden="true" /> PRIMARY OWNER {renderSortIcon('owner')}
                                </th>
                                <th>BOX</th>
                                <th
                                    onClick={() => handleSort('paid')}
                                    className={styles.sortable}
                                    aria-sort={sortConfig.key === 'paid' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                                >
                                    <FiCreditCard aria-hidden="true" /> PROGRESS {renderSortIcon('paid')}
                                </th>
                                <th>STATUS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && (
                                <tr>
                                    <td colSpan="5" className={styles.loadingCell}>
                                        <FiClock aria-hidden="true" /> SYNCING ARCHIVE...
                                    </td>
                                </tr>
                            )}

                            {!loading && loadError && (
                                <tr>
                                    <td colSpan="5" className={styles.errorCell}>
                                        <FiAlertTriangle aria-hidden="true" /> LEDGER SYNC FAULT — <button className={styles.retryBtn} onClick={fetchLedger}>RETRY</button>
                                    </td>
                                </tr>
                            )}

                            {!loading && !loadError && processedData.length === 0 && (
                                <tr>
                                    <td colSpan="5" className={styles.emptyCell}>
                                        <FiLayers aria-hidden="true" />
                                        {searchTerm
                                            ? `NO RECORDS MATCH "${searchTerm.toUpperCase()}"`
                                            : 'NO RECORDS FOUND'
                                        }
                                    </td>
                                </tr>
                            )}

                            {!loading && !loadError && processedData.map((proj) => {
                                const pct        = proj.totalCost > 0 ? Math.min((proj.amountPaid / proj.totalCost) * 100, 100) : 0;
                                const debt       = (proj.totalCost || 0) - (proj.amountPaid || 0);
                                const isCritical = pct < 25 && proj.totalCost > 0;

                                return (
                                    <tr
                                        key={proj.id}
                                        onClick={() => navigate(`/folder/${proj.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/folder/${proj.id}`); } }}
                                        tabIndex={0}
                                        role="row"
                                        aria-label={`Record: ${proj.landTitle?.plotNumber}, owner: ${proj.proprietors?.[0]?.fullName || 'unknown'}`}
                                        className={isCritical ? styles.rowCritical : ''}
                                    >
                                        <td className={styles.plotCell}>
                                            <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                            <span>{proj.landTitle?.tenure}</span>
                                            {proj.landTitle?.district && (
                                                <span className={styles.districtTag}>{proj.landTitle.district}</span>
                                            )}
                                        </td>
                                        <td>
                                            <div className={styles.ownerWrap}>
                                                <div className={styles.ownerMeta}>
                                                    <span className={styles.ownerName}>
                                                        {proj.proprietors?.[0]?.fullName || '---'}
                                                    </span>
                                                    <span className={styles.ownerPhone}>
                                                        {proj.proprietors?.[0]?.phoneNumber || '---'}
                                                    </span>
                                                </div>
                                                {proj.proprietors?.length > 1 && (
                                                    <div
                                                        className={styles.jointBadge}
                                                        aria-label={`${proj.proprietors.length - 1} additional owner${proj.proprietors.length > 2 ? 's' : ''}`}
                                                    >
                                                        <FiUsers aria-hidden="true" />
                                                        <span>+{proj.proprietors.length - 1} MORE</span>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <span className={styles.boxTag}>
                                                {proj.landTitle?.physicalBoxNumber || '---'}
                                            </span>
                                        </td>
                                        <td className={styles.moneyCell}>
                                            <div className={styles.moneyRow}>
                                                <span className={styles.debtLabel}>DEBT:</span>
                                                <span className={isCritical ? styles.debtCritical : styles.debtAmount}>
                                                    UGX {debt.toLocaleString()}
                                                </span>
                                            </div>
                                            <div
                                                className={styles.velocityBar}
                                                role="progressbar"
                                                aria-valuenow={Math.round(pct)}
                                                aria-valuemin={0}
                                                aria-valuemax={100}
                                                aria-label={`${Math.round(pct)}% collected`}
                                            >
                                                <div
                                                    className={`${styles.velocityFill} ${isCritical ? styles.velocityFillCritical : ''}`}
                                                    style={{ width: `${pct}%` }}
                                                />
                                            </div>
                                            <span className={styles.pctLabel}>{Math.round(pct)}%</span>
                                        </td>
                                        <td>
                                            <div className={styles.statusGroup}>
                                                <span className={proj.isLegacy ? styles.tagLegacy : styles.tagStandard}>
                                                    {proj.isLegacy ? 'BACKLOG' : 'ACTIVE'}
                                                </span>
                                                {isCritical && (
                                                    <span className={styles.tagCritical}>CRITICAL</span>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* ── PAGINATION ── */}
                <footer className={styles.pagination} aria-label="Pagination">
                    <button
                        onClick={() => setPage(p => Math.max(0, p - 1))}
                        disabled={page === 0}
                        aria-label="Previous page"
                        className={styles.pageBtn}
                    >
                        <FiChevronLeft aria-hidden="true" /> PREV
                    </button>
                    <span className={styles.pageIndicator} aria-current="page" aria-label={`Page ${page + 1}`}>
                        RANGE {page + 1}
                        {processedData.length > 0 && (
                            <span className={styles.recordCount}> · {processedData.length} RECORDS</span>
                        )}
                    </span>
                    <button
                        onClick={() => setPage(p => p + 1)}
                        disabled={processedData.length < 50}
                        aria-label="Next page"
                        className={styles.pageBtn}
                    >
                        NEXT <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
            </HardwarePanel>
        </div>
    );
};

export default LedgerPage;