// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight, FiActivity,
    FiArrowUp, FiArrowDown, FiArchive, FiClock, FiUsers,
    FiAlertTriangle, FiX, FiAlertOctagon
} from 'react-icons/fi';
import HardwarePanel from '../../components/ui/HardwarePanel';
import ErrorMessage from '../../components/common/ErrorMessage';
import BackToTopButton from '../../components/common/BackToTopButton';
import landService from '../../services/landService';
import styles from './LedgerPage.module.css';

const matchesSearch = (proj, term) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');
    const fields = [
        proj.landTitle?.plotNumber,
        proj.projectIndex,
        proj.district,
        proj.county,
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

// Payment health badge logic
// GREEN = payment within 14 days
// YELLOW = payment within 30 days
// RED = no payment or over 30 days
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
                display: 'inline-block',
                width: 7, height: 7,
                borderRadius: '50%',
                background: BADGE_COLORS[badge],
                boxShadow: `0 0 4px ${BADGE_COLORS[badge]}`,
                flexShrink: 0,
                marginTop: 4,
            }}
        />
    );
};

const LedgerPage = () => {
    const navigate = useNavigate();

    const [projects,     setProjects]     = useState([]);
    const [loading,      setLoading]      = useState(true);
    const [loadError,    setLoadError]    = useState(false);
    const [page,         setPage]         = useState(0);
    const [searchTerm,   setSearchTerm]   = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [bulkProcessing, setBulkProcessing] = useState(false);
    const [sortConfig,   setSortConfig]   = useState({ key: 'plotNumber', direction: 'asc' });

    // guard vars used by UnsavedChangesModal below

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

        if (activeFilter === 'PAID')     filtered = filtered.filter(p => (p.amountPaid >= p.totalCost || p.landTitle?.isReleased) && !p.isReceivable);
        if (activeFilter === 'RECEIVABLES')  filtered = filtered.filter(p => p.isReceivable);
        if (activeFilter === 'ACTIVE')   filtered = filtered.filter(p => !p.isReceivable);
        if (activeFilter === 'DEBTORS')  filtered = filtered.filter(p => p.isReceivable ? (Number(p.totalCost||0) + Number(p.storageFeesAccumulated||0) - Number(p.amountPaid||0)) > 0 : p.amountPaid < p.totalCost);
        if (activeFilter === 'CRITICAL') filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && (p.amountPaid / p.totalCost) < 0.25);
    if (activeFilter === 'READY_FOR_TITLING') {
        filtered = filtered.filter(p => {
            if (p.landTitle) return false;
            const stages = p.stages || [];
            if (stages.length === 0) return false;
            const finalStage = stages.find(s => (s.stageName || '').toLowerCase().includes('registration'));
            if (!finalStage) return false;
            const priorStages = stages.filter(s => s.id !== finalStage.id);
            const allPriorComplete = priorStages.every(s => s.isCompleted);
            const finalOutstanding = !finalStage.isCompleted;
            const finalCheckedButEmpty = finalStage.isCompleted && !p.landTitle;
            return (allPriorComplete && finalOutstanding) || finalCheckedButEmpty;
        });
    }

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

    const isReadyForTitling = (p) => {
        if (p.landTitle) return false;
        const stages = p.stages || [];
        if (stages.length === 0) return false;
        const finalStage = stages.find(s => (s.stageName || '').toLowerCase().includes('registration'));
        if (!finalStage) return false;
        const priorStages = stages.filter(s => s.id !== finalStage.id);
        const allPriorComplete = priorStages.every(s => s.isCompleted);
        const finalOutstanding = !finalStage.isCompleted;
        const finalCheckedButEmpty = finalStage.isCompleted && !p.landTitle;
        return (allPriorComplete && finalOutstanding) || finalCheckedButEmpty;
    };

    const handleBulkMark = async () => {
        setBulkProcessing(true);
        try {
            await landService.bulkMarkTitleProduced([...selectedIds]);
            await fetchLedger();
            setSelectedIds(new Set());
        } catch (e) {
            console.error(e);
        } finally {
            setBulkProcessing(false);
        }
    };

    const toggleSelect = (id, e) => {
        e.stopPropagation();
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const toggleSelectAll = () => {
        const readyIds = new Set(processedData.map(p => p.id));
        const allSelected = processedData.length > 0 && processedData.every(p => selectedIds.has(p.id));
        if (allSelected) setSelectedIds(new Set());
        else setSelectedIds(readyIds);
    };

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

    const SEARCH_HINT = 'Plot ID � Box � Owner name � Phone � NIN � Email � District � County � Tenure';

    const FILTERS = [
        { key: 'ALL',      label: 'ALL ARCHIVES'  },
        { key: 'PAID',     label: 'PAID TITLES'   },
        { key: 'RECEIVABLES',  label: 'RECEIVABLES'        },
        { key: 'ACTIVE',   label: 'ACTIVE TITLES'  },
        { key: 'DEBTORS',  label: 'UNPAID'         },
        { key: 'CRITICAL', label: 'CRITICAL'       },
        { key: 'READY_FOR_TITLING', label: 'READY FOR TITLING' },
    ];

    return (
        <div className={styles.container}>
            <BackToTopButton />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Plot Ledger</h1>
                    <p className={styles.subtitle}>All registered plots and their payment status</p>
                </div>
            </header>

            <div className={styles.controlHub}>
                <div className={styles.searchBlock}>
                    <div className={styles.searchInner}>
                        <input
                            type="search" id="ledger-search"
                            placeholder="Plot ID, box, owner, phone, NIN, email, district, county, tenure..."
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
                                {f.icon} {f.label}
                            </button>
                        ))}
                    </div>
                </div>

                {activeFilter === 'READY_FOR_TITLING' && selectedIds.size > 0 && (
                    <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: '10px', fontWeight: 900, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: '1px' }}>
                            {selectedIds.size} RECORD{selectedIds.size > 1 ? 'S' : ''} SELECTED
                        </span>
                        <button className={styles.bulkActionBtn} onClick={handleBulkMark} disabled={bulkProcessing}>
                            {bulkProcessing ? 'PROCESSING...' : 'MARK AS TITLE-PRODUCED'}
                        </button>
                    </div>
                )}

                {/* BADGE LEGEND */}
                <div className={styles.badgeLegend}>
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (
                        <span key={k} className={styles.badgeLegendItem}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, display: 'inline-block', flexShrink: 0, boxShadow: `0 0 4px ${c}` }} />
                            {BADGE_LABELS[k]}
                        </span>
                    ))}
                </div>
            </div>

            <div>
            <HardwarePanel variant="dark">
                <div className={styles.tableScroll}>
                    <table className={styles.ledgerTable} aria-label="Land records ledger" aria-rowcount={processedData.length}>
                        <thead>
                            <tr>
                                {activeFilter === 'READY_FOR_TITLING' && (
                                    <th style={{width: '30px'}}>
                                        <input 
                                            type="checkbox" 
                                            onChange={toggleSelectAll} 
                                            checked={processedData.length > 0 && processedData.every(p => selectedIds.has(p.id))} 
                                            onClick={e => e.stopPropagation()} 
                                        />
                                    </th>
                                )}
                                <th onClick={() => handleSort('plotNumber')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'plotNumber' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiMapPin aria-hidden="true" /> PLOT ID {renderSortIcon('plotNumber')}
                                </th>
                                <th onClick={() => handleSort('owner')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'owner' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiUser aria-hidden="true" /> PRIMARY OWNER {renderSortIcon('owner')}
                                </th>

                                <th onClick={() => handleSort('paid')} className={styles.sortable}
                                    aria-sort={sortConfig.key === 'paid' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                                    <FiCreditCard aria-hidden="true" /> PROGRESS {renderSortIcon('paid')}
                                </th>
                                <th>STATUS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && (
                                <tr><td colSpan={activeFilter === 'READY_FOR_TITLING' ? 6 : 5} className={styles.loadingCell}>
                                    <FiClock aria-hidden="true" /> SYNCING ARCHIVE...
                                </td></tr>
                            )}
                            {!loading && loadError && (
                                <tr><td colSpan={activeFilter === 'READY_FOR_TITLING' ? 6 : 5} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> LEDGER SYNC FAULT �{' '}
                                    <button className={styles.retryBtn} onClick={fetchLedger}>RETRY</button>
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.length === 0 && (
                                <tr><td colSpan={activeFilter === 'READY_FOR_TITLING' ? 6 : 5} className={styles.emptyCell}>
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
                                const pct        = proj.totalCost > 0 ? Math.min((proj.amountPaid / proj.totalCost) * 100, 100) : 0;
                                const isCritical = pct < 25 && proj.totalCost > 0;

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
                                                        {proj.landTitle ? 'TITLED' : 'FOLDER'}
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
                                                    <span className={styles.ownerName}>{proj.proprietors?.[0]?.fullName || '---'}</span>
                                                    <span className={styles.ownerPhone}>{proj.proprietors?.[0]?.phoneNumber || '---'}</span>
                                                </div>
                                                {proj.proprietors?.length > 1 && (
                                                    <div className={styles.jointBadge}>
                                                        <FiUsers aria-hidden="true" />
                                                        <span>+{proj.proprietors.length - 1} MORE</span>
                                                    </div>
                                                )}
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
                                        <td>
                                            <div className={styles.statusGroup}>
                                                {isReceivable && <span className={styles.tagReceivable}>RECEIVABLES</span>}
                                                {!isReceivable && proj.landTitle?.isReleased && <span className={styles.tagPaid}>RELEASED</span>}
                                                {!isReceivable && !proj.landTitle?.isReleased && proj.amountPaid >= proj.totalCost && <span className={styles.tagPaid}>FULLY PAID</span>}
                                                {!isReceivable && proj.amountPaid < proj.totalCost && <span className={styles.tagStandard}>ACTIVE</span>}
                                                {isCritical && <span className={styles.tagCritical}>CRITICAL</span>}
                                            </div>
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
                        {processedData.length > 0 && <span className={styles.recordCount}> � {processedData.length} RECORDS</span>}
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