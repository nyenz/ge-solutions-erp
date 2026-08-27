#!/usr/bin/env python3
"""fix18.py — Ledger polish (sticky toolbar/header, stacked multi-values,
sidebar collapse, legend popover) + Folder page standards.
Run: py fix18.py"""
import subprocess
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
WROTE, WARN = [], []

def write(rel, content):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8"); WROTE.append(rel)

def patch(rel, old, new):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    if new.strip() and new in t: return
    if old not in t: WARN.append(rel + " (anchor not found)"); return
    p.write_text(t.replace(old, new, 1), encoding="utf-8"); WROTE.append(rel + " (patched)")

# =====================================================================
# 1) LedgerPage.jsx — sticky toolbar/header, stacked values, sidebar collapse
# =====================================================================
write('erp-frontend/src/pages/Ledger/LedgerPage.jsx', r"""// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight,
    FiArrowUp, FiArrowDown, FiClock, FiAlertTriangle, FiX, FiInfo
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

const PaymentDot = ({ proj }) => {
    const badge = getPaymentBadge(proj);
    return (
        <span title={BADGE_LABELS[badge]} aria-label={BADGE_LABELS[badge]}
            style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
                background: BADGE_COLORS[badge], boxShadow: `0 0 4px ${BADGE_COLORS[badge]}`,
                flexShrink: 0, marginTop: 4 }} />
    );
};

// multi-value helper: "a / b" -> ["a","b"] so entries stack downward
const splitMulti = (v) => (v || '').split('/').map(s => s.trim()).filter(Boolean);

const isReadyForTitling = (p) => {
    if (p.landTitle) return false;
    const stages = p.stages || [];
    if (stages.length === 0) return false;
    const finalStage = stages.find(s => (s.stageName || '').toLowerCase().includes('registration'));
    if (!finalStage) return false;
    const prior = stages.filter(s => s.id !== finalStage.id);
    return (prior.every(s => s.isCompleted) && !finalStage.isCompleted) || (finalStage.isCompleted && !p.landTitle);
};

const LedgerPage = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [page, setPage] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [sortConfig, setSortConfig] = useState({ key: 'plotNumber', direction: 'asc' });

    // STANDARD: sidebar auto-collapses when the Ledger page is opened
    useEffect(() => {
        const t = setTimeout(() => {
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
        }, 150);
        return () => clearTimeout(t);
    }, []);

    const fetchLedger = useCallback(async (attempt = 0) => {
        setLoading(true); setLoadError(false);
        try {
            const data = await landService.getGlobalLedger(page, 50);
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
        if (activeFilter === 'READY_FOR_TITLING') filtered = filtered.filter(isReadyForTitling);
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
        { key: 'ALL',         label: 'ALL PROJECTS' },
        { key: 'BACKLOG',     label: 'BACKLOG' },
        { key: 'TITLED',      label: 'TITLED' },
        { key: 'LEGACY',      label: 'LEGACY' },
        { key: 'RECEIVABLES', label: 'RECEIVABLES' },
        { key: 'CRITICAL',    label: 'CRITICAL' },
        { key: 'PAID',        label: 'PAID' },
    ];

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Project Ledger</h1>
                    <p className={styles.subtitle}>Every registered project — from first folder to released title, with live payment health</p>
                </div>
            </header>

            {/* Sticky toolbar: search + filters stay visible; legend is a hover popover */}
            <div className={styles.controlHub}>
                <div className={styles.toolbarRow}>
                    <div className={styles.searchBlock}>
                        <div className={styles.searchInner}>
                            <input type="search" id="ledger-search"
                                placeholder="Search any field: index, plot, title ID, owner, phone, NIN, email, district, county, parish, village..."
                                className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                                value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                                onFocus={() => setIsSearchFocused(true)} onBlur={() => setIsSearchFocused(false)}
                                aria-label="Search ledger records" autoComplete="off" />
                            {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}
                            {searchTerm && (
                                <button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label="Clear search" type="button">
                                    <FiX aria-hidden="true" />
                                </button>
                            )}
                        </div>
                    </div>
                    <div className={styles.legendWrap}>
                        <button type="button" className={styles.legendChip} aria-label="Payment health legend">
                            <FiInfo aria-hidden="true" /> LEGEND
                        </button>
                        <div className={styles.legendPop} role="tooltip">
                            {Object.entries(BADGE_COLORS).map(([k, c]) => (
                                <span key={k} className={styles.legendItem}>
                                    <span className={styles.legendDot} style={{ background: c, boxShadow: `0 0 4px ${c}` }} /> {BADGE_LABELS[k]}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
                <div className={styles.filterRailContainer}>
                    <div className={styles.filterRail} role="group" aria-label="Filter records">
                        {FILTERS.map(f => (
                            <button key={f.key} onClick={() => setActiveFilter(f.key)}
                                className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}
                                aria-pressed={activeFilter === f.key} aria-label={f.label}>
                                {f.label}
                            </button>
                        ))}
                    </div>
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
                            {loading && (<tr><td colSpan={7} className={styles.loadingCell}><FiClock aria-hidden="true" /> SYNCING ARCHIVE...</td></tr>)}
                            {!loading && loadError && (
                                <tr><td colSpan={7} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> LEDGER SYNC FAULT —{' '}
                                    <button className={styles.retryBtn} onClick={() => fetchLedger()}>RETRY</button>
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.length === 0 && (
                                <tr><td colSpan={7} className={styles.emptyCell}>
                                    <FiLayers aria-hidden="true" />
                                    {searchTerm ? `NO RECORDS MATCH "${searchTerm.toUpperCase()}"` : 'NO RECORDS FOUND'}
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.map((proj) => {
                                const isReceivable = proj.isReceivable;
                                const storageFees = Number(proj.storageFeesAccumulated || 0);
                                const debt = isReceivable
                                    ? (proj.totalCost || 0) + storageFees - (proj.amountPaid || 0)
                                    : (proj.totalCost || 0) - (proj.amountPaid || 0);
                                const pct = proj.totalCost > 0 ? Math.min(((proj.amountPaid || 0) / proj.totalCost) * 100, 100) : 0;
                                const isCritical = pct < 25 && proj.totalCost > 0;
                                const names  = (proj.proprietors || []).map(p => p.fullName).filter(Boolean);
                                const nins   = (proj.proprietors || []).map(p => p.nationalId).filter(Boolean);
                                const phones = (proj.proprietors || []).flatMap(p => splitMulti(p.phoneNumber));
                                return (
                                    <tr key={proj.id}
                                        onClick={() => navigate(`/folder/${proj.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/folder/${proj.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Record: ${proj.projectIndex || proj.landTitle?.plotNumber}`}
                                        className={isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>
                                        {/* INDEX: dot + index + NINs stacked downward */}
                                        <td className={styles.plotCell}>
                                            <div className={styles.indexRow}>
                                                <PaymentDot proj={proj} />
                                                <div className={styles.stack}>
                                                    <strong>#{proj.projectIndex || '---'}</strong>
                                                    {nins.length
                                                        ? nins.map((nn, i) => <span key={i} className={styles.stackSub}>{nn}</span>)
                                                        : <span className={styles.stackSub}>---</span>}
                                                </div>
                                            </div>
                                        </td>
                                        {/* OWNER(S): names stacked downward */}
                                        <td>
                                            <div className={styles.stack}>
                                                {names.length
                                                    ? names.map((nm, i) => <span key={i} className={i === 0 ? styles.ownerName : styles.stackSub}>{nm}</span>)
                                                    : <span className={styles.ownerName}>---</span>}
                                            </div>
                                        </td>
                                        {/* PHONE: every number stacked downward */}
                                        <td>
                                            <div className={styles.stack}>
                                                {phones.length
                                                    ? phones.map((ph, i) => <span key={i} className={styles.ownerPhone}>{ph}</span>)
                                                    : <span className={styles.ownerPhone}>---</span>}
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
                                                <div style={{ fontSize: '0.7rem', color: '#ef4444', marginBottom: 4 }}>
                                                    +UGX {Number(proj.storageFeesAccumulated).toLocaleString()} storage fees
                                                </div>
                                            )}
                                            <div className={styles.velocityBar} role="progressbar"
                                                aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
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
                <footer className={styles.pagination} aria-label="Pagination">
                    <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} aria-label="Previous page" className={styles.pageBtn}>
                        <FiChevronLeft aria-hidden="true" /> PREV
                    </button>
                    <span className={styles.pageIndicator} aria-current="page">
                        RANGE {page + 1}
                        {processedData.length > 0 && <span className={styles.recordCount}> — {processedData.length} RECORDS</span>}
                    </span>
                    <button onClick={() => setPage(p => p + 1)} disabled={processedData.length < 50} aria-label="Next page" className={styles.pageBtn}>
                        NEXT <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
            </HardwarePanel>
            </div>
            <BackToTopButton />
        </div>
    );
};
export default LedgerPage;
""")

# =====================================================================
# 2) LedgerPage.module.css — sticky toolbar, inner-scroll grid, stacked values
# =====================================================================
write('erp-frontend/src/pages/Ledger/LedgerPage.module.css', r"""/* PATH: erp-frontend/src/pages/Ledger/LedgerPage.module.css */
:root {
    --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
    --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981;
    --app-header-h: 64px;
}
.container {
    max-width: 1400px; width: 100%; margin: 0 auto;
    padding: clamp(12px,2vh,22px) clamp(12px,2vw,24px) 0;
    font-family: 'Inter', sans-serif; color: #fff;
    display: flex; flex-direction: column;
}
.pageHeader {
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
    gap: clamp(8px,1.2vw,14px); border-left: clamp(3px,0.4vw,5px) solid var(--orange);
    padding: clamp(8px,1.2vw,14px) clamp(14px,1.8vw,22px);
    background: rgba(255,255,255,0.62); border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07);
    margin-bottom: clamp(10px,1.5vh,16px);
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
.title { font-family: 'Cinzel', serif; color: var(--navy-deep); font-size: clamp(18px,2.5vw,24px); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin: 0; }
.subtitle { font-family: 'Inter', sans-serif; color: #64748b; font-size: clamp(9px,0.9vw,11px); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

/* Sticky toolbar: solid bg so rows never show through */
.controlHub {
    position: sticky; top: var(--app-header-h); z-index: 60;
    background: rgba(244,242,239,0.97); backdrop-filter: blur(8px);
    padding: 10px 0 8px; box-shadow: 0 6px 14px rgba(0,0,0,0.06);
    display: flex; flex-direction: column; gap: 8px;
}
.toolbarRow { display: flex; align-items: center; gap: 10px; }
.searchBlock { flex: 1; min-width: 0; }
.searchInner { position: relative; display: flex; align-items: center; background: #fff; border: 1.5px solid #c8d6d7; border-radius: 6px; height: clamp(36px,4.5vw,42px); transition: border-color .2s, box-shadow .2s; }
.searchInner:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238,140,58,0.18); }
.searchIcon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--orange); pointer-events: none; }
.searchInput { width: 100%; border: none; outline: none; background: transparent; color: #1a2e30; padding: 0 12px 0 38px; font-family: 'Inter',sans-serif; font-weight: 600; font-size: 12px; height: 100%; }
.searchInput::placeholder { color: rgba(26,46,48,0.35); font-weight: 500; }
.searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--orange); cursor: pointer; display: flex; }

/* Legend as hover popover (no scroll clutter) */
.legendWrap { position: relative; flex-shrink: 0; }
.legendChip { display: inline-flex; align-items: center; gap: 6px; background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 8px 12px; border-radius: 6px; font-family: 'Inter',sans-serif; font-weight: 900; font-size: 9px; letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; }
.legendChip:hover { color: var(--orange); border-color: var(--orange); }
.legendPop { display: none; position: absolute; right: 0; top: calc(100% + 6px); background: #1a2e30; border: 1px solid var(--orange-border); border-radius: 8px; padding: 10px 12px; flex-direction: column; gap: 6px; z-index: 80; box-shadow: 0 8px 24px rgba(0,0,0,0.35); white-space: nowrap; }
.legendWrap:hover .legendPop, .legendChip:focus + .legendPop { display: flex; }
.legendItem { display: flex; align-items: center; gap: 8px; font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.85); }
.legendDot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }

.filterRailContainer { overflow-x: auto; scrollbar-width: none; }
.filterRailContainer::-webkit-scrollbar { display: none; }
.filterRail { display: flex; gap: 8px; }
.filterBtn { background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 8px 16px; border-radius: 6px; font-family: 'Inter',sans-serif; font-weight: 900; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; white-space: nowrap; transition: all .2s; }
.filterBtn:hover { color: var(--orange); border-color: var(--orange); }
.activeFilter { background: var(--orange) !important; color: #1a2e30 !important; border-color: var(--orange) !important; }

/* Inner-scroll grid: page toolbar stays, headers stay */
.tableScroll { max-height: calc(100vh - 250px); min-height: 300px; overflow: auto; border-radius: 10px; }
.ledgerTable { width: 100%; border-collapse: separate; border-spacing: 0; }
.ledgerTable thead th {
    position: sticky; top: 0; z-index: 5;
    background: #16282a; color: var(--orange);
    font-family: 'Inter',sans-serif; font-size: 10px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
    text-align: left; padding: 12px 14px; border-bottom: 2px solid var(--orange);
}
.sortable { cursor: pointer; }
.sortActive { margin-left: 4px; }
.ledgerTable tbody td { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.06); vertical-align: top; color: #fff; font-size: 12px; }
.ledgerTable tbody tr { cursor: pointer; transition: background .15s; }
.ledgerTable tbody tr:hover { background: rgba(255,255,255,0.04); }
.rowReceivable { background: rgba(239,68,68,0.05); }
.rowCritical { background: rgba(239,68,68,0.07); }

/* stacked multi-values expand downward */
.stack { display: flex; flex-direction: column; gap: 2px; }
.stackSub { font-size: 10px; font-weight: 600; color: rgba(255,255,255,0.55); font-family: 'Space Mono', monospace; letter-spacing: 0.3px; }
.indexRow { display: flex; align-items: flex-start; gap: 6px; }
.indexRow strong { font-family: 'Space Mono', monospace; color: #fff; }
.ownerName { font-weight: 800; color: #fff; }
.ownerPhone { font-family: 'Space Mono', monospace; font-size: 11px; color: rgba(255,255,255,0.7); }

.statusGroup { display: flex; flex-direction: column; gap: 4px; align-items: flex-start; }
.tagReceivable, .tagPaid, .tagStandard, .tagCritical { font-size: 9px; font-weight: 900; letter-spacing: 1px; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
.tagReceivable { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }
.tagPaid { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.4); }
.tagStandard { color: rgba(255,255,255,0.6); }
.tagCritical { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.4); }

.moneyCell { min-width: 150px; }
.moneyRow { display: flex; justify-content: space-between; gap: 8px; }
.debtLabel { color: rgba(255,255,255,0.5); font-size: 10px; font-weight: 800; }
.debtAmount { font-family: 'Space Mono', monospace; color: #fca5a5; font-weight: 700; }
.debtCritical { font-family: 'Space Mono', monospace; color: #ef4444; font-weight: 900; }
.velocityBar { height: 5px; background: rgba(255,255,255,0.1); border-radius: 3px; margin-top: 6px; overflow: hidden; }
.velocityFill { height: 100%; background: var(--orange); border-radius: 3px; }
.velocityFillCritical { background: var(--red); }
.pctLabel { font-size: 9px; color: rgba(255,255,255,0.5); font-weight: 700; }

.loadingCell, .errorCell, .emptyCell { text-align: center; padding: 30px !important; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px; }
.retryBtn { background: none; border: 1px solid var(--red); color: var(--red); padding: 4px 10px; border-radius: 4px; cursor: pointer; font-weight: 800; }

.pagination { display: flex; justify-content: space-between; align-items: center; padding: 10px 4px; }
.pageBtn { background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 7px 14px; border-radius: 6px; font-weight: 900; font-size: 10px; cursor: pointer; display: inline-flex; gap: 6px; align-items: center; }
.pageBtn:disabled { opacity: 0.4; cursor: not-allowed; }
.pageIndicator { color: rgba(255,255,255,0.6); font-size: 10px; font-weight: 800; letter-spacing: 1px; }
.recordCount { color: var(--orange); }
""")

# =====================================================================
# 3) FolderPage.jsx — add BackToTopButton + sidebar auto-collapse
# =====================================================================
patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"import styles from './FolderPage.module.css';\n",
"import styles from './FolderPage.module.css';\nimport BackToTopButton from '../../components/common/BackToTopButton';\n")

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"const fileInputRef  = useRef(null);\n",
"const fileInputRef  = useRef(null);\n\n// STANDARD: sidebar auto-collapses when the folder page is opened\nuseEffect(() => {\n    const t = setTimeout(() => {\n        const aside = document.querySelector('aside');\n        const toggle = document.querySelector('[class*=\"sidebarToggle\"]');\n        if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();\n    }, 150);\n    return () => clearTimeout(t);\n}, []);\n")

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"</HardwareModal>\n</div>\n);\n};\n\nexport default FolderPage;",
"</HardwareModal>\n<BackToTopButton />\n</div>\n);\n};\n\nexport default FolderPage;")

# =====================================================================
subprocess.run(['git', 'add', '.'], check=False, cwd=ROOT, capture_output=True)
subprocess.run(['git', 'commit', '-m', 'fix18: Ledger sticky toolbar+header, stacked multi-values, legend popover, sidebar collapse; Folder page standards'], check=False, cwd=ROOT, capture_output=True)
subprocess.run(['git', 'push'], check=False, cwd=ROOT, capture_output=True)
print("Wrote:", len(WROTE))
for f in WROTE: print("  +", f)
for f in WARN: print("  ~", f)
print("Done. Pushed.")