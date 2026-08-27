// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight,
    FiArrowUp, FiArrowDown, FiClock, FiUsers,
    FiAlertTriangle, FiX, FiPhoneCall
} from 'react-icons/fi';
import HardwarePanel from '../../components/ui/HardwarePanel';
import ErrorMessage from '../../components/common/ErrorMessage';
import landService from '../../services/landService';
import styles from './LedgerPage.module.css';

// Search mirrors EVERY field captured at intake
const matchesSearch = (proj, term) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');
    const fields = [
        proj.projectIndex,
        proj.landTitle?.plotNumber,
        proj.landTitle?.titleId,
        proj.landTitle?.blockRoad,
        proj.landTitle?.tenure,
        proj.district,
        proj.county,
        proj.subCounty,
        proj.parish,
        proj.village,
        proj.area,
        proj.status,
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

const getPaymentBadge = (proj) => {
    if (!proj.lastPaymentDate) return 'RED';
    const days = Math.floor((Date.now() - new Date(proj.lastPaymentDate)) / 86400000);
    if (days <= 14) return 'GREEN';
    if (days <= 30) return 'YELLOW';
    return 'RED';
};

const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Recent payment', YELLOW: 'Payment 2-4 weeks ago', RED: 'No recent payment' };

const PaymentDot = ({ proj }) => {
    const badge = getPaymentBadge(proj);
    return (
        <span
            title={BADGE_LABELS[badge]}
            aria-label={BADGE_LABELS[badge]}
            style={{
                display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
                background: BADGE_COLORS[badge], boxShadow: `0 0 4px ${BADGE_COLORS[badge]}`,
                flexShrink: 0, marginTop: 4,
            }}
        />
    );
};

const typeBadge = (proj) => (proj.isLegacy ? 'LEGACY' : proj.landTitle ? 'TITLED' : 'FOLDER');

const LedgerPage = () => {
    const navigate = useNavigate();
    const containerRef = useRef(null);

    const [projects,     setProjects]     = useState([]);
    const [loading,      setLoading]      = useState(true);
    const [loadError,    setLoadError]    = useState(false);
    const [page,         setPage]         = useState(0);
    const [searchTerm,   setSearchTerm]   = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [sortConfig,   setSortConfig]   = useState({ key: 'plotNumber', direction: 'asc' });

    // STANDARD: sidebar auto-collapses once the user starts working on the page
    const collapsedOnce = useRef(false);
    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const handler = () => {
            if (collapsedOnce.current) return;
            collapsedOnce.current = true;
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) {
                toggle.click();
            }
        };
        el.addEventListener('focusin', handler);
        el.addEventListener('input', handler);
        el.addEventListener('click', handler);
        return () => {
            el.removeEventListener('focusin', handler);
            el.removeEventListener('input', handler);
            el.removeEventListener('click', handler);
        };
    }, []);

    // Free-tier cold start: the API can take ~a minute to wake. Retry once
    // after 5s before declaring a fault, so a waking backend no longer
    // shows LEDGER SYNC FAULT.
    const fetchLedger = useCallback(async (attempt = 0) => {
        setLoading(true);
        setLoadError(false);
        try {
            const data = await landService.getGlobalLedger(page, 50);
            setProjects(data.content || []);
            setLoading(false);
        } catch {
            if (attempt < 1) {
                setTimeout(() => fetchLedger(attempt + 1), 5000);
                return;
            }
            setLoadError(true);
            setLoading(false);
        }
    }, [page]);

    useEffect(() => { fetchLedger(); }, [fetchLedger]);

    const processedData = useMemo(() => {
        let filtered = projects.filter(p => matchesSearch(p, searchTerm));

        if (activeFilter === 'BACKLOG')     filtered = filtered.filter(p => !p.landTitle);
        if (activeFilter === 'TITLED')      filtered = filtered.filter(p => !!p.landTitle && !p.isLegacy);
        if (activeFilter === 'LEGACY')      filtered = filtered.filter(p => p.isLegacy);
        if (activeFilter === 'RECEIVABLES') filtered = filtered.filter(p => p.isReceivable);
        if (activeFilter === 'PAID')        filtered = filtered.filter(p => (p.amountPaid >= p.totalCost || p.landTitle?.isReleased));
        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(p => (p.totalCost || 0) > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25 && !(p.amountPaid >= p.totalCost));

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

    const FILTERS = [
        { key: 'ALL',         label: 'ALL PROJECTS' },
        { key: 'BACKLOG',     label: 'BACKLOG'      },
        { key: 'TITLED',      label: 'TITLED'       },
        { key: 'LEGACY',      label: 'LEGACY'       },
        { key: 'RECEIVABLES', label: 'RECEIVABLES'  },
        { key: 'CRITICAL',    label: 'CRITICAL'     },
        { key: 'PAID',        label: 'PAID'         },
    ];

    return (
        <div className={styles.container} ref={containerRef}>

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Project Ledger</h1>
                    <p className={styles.subtitle}>Every registered project — from first folder to released title, with live payment health</p>
                </div>
            </header>

            <div className={styles.controlHub}>
                <div className={styles.searchBlock}>
                    <div className={styles.searchInner}>
                        <input
                            type="search" id="ledger-search"
                            placeholder="Search any field: index, plot, title ID, owner, phone, NIN, email, district, county, parish, village, tenure..."
                            className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            onFocus={() => setIsSearchFocused(true)}
                            onBlur={() => setIsSearchFocused(false)}
                            aria-label="Search ledger records"
                            autoComplete="off"
                        />
                        {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}
                        {searchTerm && (
                            <button className={styles.searchClearBtn} onClick={() => setSearchTerm('')}
                                aria-label="Clear search" type="button">
                                <FiX aria-hidden="true" />
                            </button>
                        )}
                    </div>
                </div>

                <div className={styles.filterRailContainer}>
                    <div className={styles.filterRail} role="group" aria-label="Filter records">
                        {FILTERS.map(f => (
                            <button key={f.key}
                                onClick={() => setActiveFilter(f.key)}
                                className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}
                                aria-pressed={activeFilter === f.key} aria-label={f.label}>
                                {f.label}
                            </button>
                        ))}
                    </div>
                </div>

                <div className={styles.badgeLegend}>
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (
                        <span key={k} className={styles.badgeLegendItem}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, display: 'inline-block', boxShadow: `0 0 4px ${c}` }} />
                            {BADGE_LABELS[k]}
                        </span>
                    ))}
                </div>
            </div>

            <div>
            <HardwarePanel variant="dark">
                <div className={styles.tableScroll}>
                    <table className={styles.ledgerTable} aria-label="Project ledger" aria-rowcount={processedData.length}>
                        <thead>
                            <tr>
                                <th onClick={() => handleSort('plotNumber')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'plotNumber' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiMapPin aria-hidden="true" /> INDEX {renderSortIcon('plotNumber')}
                                </th>
                                <th onClick={() => handleSort('owner')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'owner' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiUser aria-hidden="true" /> OWNER(S) {renderSortIcon('owner')}
                                </th>
                                <th>
                                    <FiPhoneCall aria-hidden="true" /> PHONE
                                </th>
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
                            {loading && (
                                <tr><td colSpan={7} className={styles.loadingCell}>
                                    <FiClock aria-hidden="true" /> SYNCING ARCHIVE...
                                </td></tr>
                            )}
                            {!loading && loadError && (
                                <tr><td colSpan={7} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> LEDGER SYNC FAULT —{' '}
                                    <button className={styles.retryBtn} onClick={fetchLedger}>RETRY</button>
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.length === 0 && (
                                <tr><td colSpan={7} className={styles.emptyCell}>
                                    <FiLayers aria-hidden="true" />
                                    {searchTerm ? `NO RECORDS MATCH "${searchTerm.toUpperCase()}"` : 'NO RECORDS FOUND'}
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.map((proj) => {
                                const isReceivable  = proj.isReceivable;
                                const storageFees = Number(proj.storageFeesAccumulated || 0);
                                const debt       = isReceivable
                                    ? (proj.totalCost || 0) + storageFees - (proj.amountPaid || 0)
                                    : (proj.totalCost || 0) - (proj.amountPaid || 0);
                                const pct        = proj.totalCost > 0 ? Math.min(((proj.amountPaid || 0) / proj.totalCost) * 100, 100) : 0;
                                const isCritical = pct < 25 && proj.totalCost > 0 && !(proj.amountPaid >= proj.totalCost);
                                const owners     = proj.proprietors || [];
                                const phones     = owners.map(o => o.phoneNumber).filter(Boolean);

                                return (
                                    <tr key={proj.id}
                                        onClick={() => navigate(`/folder/${proj.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/folder/${proj.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Record: ${proj.landTitle?.plotNumber || proj.projectIndex}`}
                                        className={isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}
                                    >
                                        <td className={styles.plotCell}>
                                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                                                <PaymentDot proj={proj} />
                                                <div>
                                                    <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                    {proj.projectIndex && (
                                                        <span className={styles.districtTag}> #{proj.projectIndex}</span>
                                                    )}
                                                    <span className={proj.landTitle ? styles.statusTagTitled : styles.statusTagFolder}>
                                                        {typeBadge(proj)}
                                                    </span>
                                                    <div>
                                                        {proj.landTitle?.tenure && (
                                                            <span className={styles.tenureTag}>{proj.landTitle.tenure}</span>
                                                        )}
                                                        {proj.district && (
                                                            <span className={styles.districtTag}>{proj.district}</span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.ownerWrap}>
                                                <div className={styles.ownerMeta}>
                                                    <span className={styles.ownerName}>{owners[0]?.fullName || '---'}</span>
                                                </div>
                                                {owners.length > 1 && (
                                                    <div className={styles.jointBadge}>
                                                        <FiUsers aria-hidden="true" />
                                                        <span>+{owners.length - 1} MORE</span>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.ownerWrap}>
                                                <div className={styles.ownerMeta}>
                                                    <span className={styles.ownerPhone}>{phones[0] || '---'}</span>
                                                </div>
                                                {phones.length > 1 && (
                                                    <div className={styles.jointBadge}>
                                                        <span>+{phones.length - 1} MORE</span>
                                                    </div>
                                                )}
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
                                                <span className={isCritical ? styles.debtCritical : styles.debtAmount}>
                                                    UGX {debt.toLocaleString()}
                                                </span>
                                            </div>
                                            {isReceivable && proj.storageFeesAccumulated > 0 && (
                                                <div style={{ fontSize: '0.7rem', color: '#ef4444', marginBottom: 4 }}>
                                                    +UGX {Number(proj.storageFeesAccumulated).toLocaleString()} storage fees
                                                </div>
                                            )}
                                            <div className={styles.velocityBar} role="progressbar"
                                                aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
                                                <div className={`${styles.velocityFill} ${isCritical ? styles.velocityFillCritical : ''}`}
                                                    style={{ width: `${pct}%` }} />
                                            </div>
                                            <span className={styles.pctLabel}>{Math.round(pct)}%</span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                <footer className={styles.pagination} aria-label="Pagination">
                    <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                        aria-label="Previous page" className={styles.pageBtn}>
                        <FiChevronLeft aria-hidden="true" /> PREV
                    </button>
                    <span className={styles.pageIndicator} aria-current="page">
                        RANGE {page + 1}
                        {processedData.length > 0 && <span className={styles.recordCount}> — {processedData.length} RECORDS</span>}
                    </span>
                    <button onClick={() => setPage(p => p + 1)} disabled={processedData.length < 50}
                        aria-label="Next page" className={styles.pageBtn}>
                        NEXT <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
            </HardwarePanel>
            </div>
        </div>
    );
};

export default LedgerPage;
