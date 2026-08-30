#!/usr/bin/env python3
"""fix31.py — Ledger demo scroll model: sticky toolbar, inner table scroll,
rows hide behind opaque sticky header, non-fading hover, bottom-only corner
brackets (top pins kept). Run: py fix31.py"""
import subprocess
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
WROTE=[]
def write(rel, content):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8"); WROTE.append(rel)

# ---------------- CornerDecor: add hideTopCorners (keep top pins) ----------------
write('erp-frontend/src/components/ui/CornerDecor.jsx', r"""// PATH: erp-frontend/src/components/ui/CornerDecor.jsx
import React from 'react';
import styles from './CornerDecor.module.css';
// hideTop            -> hide top corners AND top pins
// hideTopCorners     -> hide ONLY the two top corner brackets (keep top pins)
const CornerDecor = ({ hidePins = false, hideTop = false, hideTopCorners = false }) => {
    return (
        <>
            {!hideTop && !hideTopCorners && <div className={`${styles.cornerAccent} ${styles.topLeft}`}></div>}
            {!hideTop && !hideTopCorners && <div className={`${styles.cornerAccent} ${styles.topRight}`}></div>}
            <div className={`${styles.cornerAccent} ${styles.bottomLeft}`}></div>
            <div className={`${styles.cornerAccent} ${styles.bottomRight}`}></div>
            {!hidePins && !hideTop && (
                <div className={`${styles.pins} ${styles.top}`}>
                    {[...Array(4)].map((_, i) => <div key={i} className={styles.pin}></div>)}
                </div>
            )}
            {!hidePins && (
                <div className={`${styles.pins} ${styles.bottom}`}>
                    {[...Array(4)].map((_, i) => <div key={i} className={styles.pin}></div>)}
                </div>
            )}
        </>
    );
};
export default CornerDecor;
""")

# ---------------- LedgerPage.jsx ----------------
write('erp-frontend/src/pages/Ledger/LedgerPage.jsx', r"""// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight, FiArrowUp, FiArrowDown, FiClock, FiAlertTriangle, FiX
} from 'react-icons/fi';
import CornerDecor from '../../components/ui/CornerDecor';
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
    return (<span title={BADGE_LABELS[badge]} aria-label={BADGE_LABELS[badge]}
        style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
            background: BADGE_COLORS[badge], boxShadow: `0 0 4px ${BADGE_COLORS[badge]}`,
            flexShrink: 0, marginTop: 4 }} />);
};

const LedgerPage = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [page, setPage] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [sortConfig, setSortConfig] = useState({ key: 'plotNumber', direction: 'asc' });

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
            {/* Page title scrolls away */}
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Project Ledger</h1>
                    <p className={styles.subtitle}>Every project — folder to release, live payment health</p>
                </div>
            </header>

            {/* Sticky control cluster: locks under the app bar once reached */}
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

            {/* Table panel: bottom corner brackets + pins, NO top corner brackets */}
            <div className={styles.tablePanel}>
                <CornerDecor hideTopCorners />
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
            </div>
            <button type="button" className={styles.topBtn} onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Back to top">
                <FiArrowUp aria-hidden="true" />
            </button>
        </div>
    );
};
export default LedgerPage;
""")

# ---------------- LedgerPage.module.css ----------------
write('erp-frontend/src/pages/Ledger/LedgerPage.module.css', r"""/* PATH: erp-frontend/src/pages/Ledger/LedgerPage.module.css */
.container {
    --orange:#EE8C3A; --orange-dim:rgba(238,140,58,0.18); --orange-border:rgba(238,140,58,0.28);
    --navy:#213E40; --navy-deep:#1a2e30; --red:#ef4444; --green:#10b981;
    --app-header-h: 64px;
    --fs-th: clamp(8px,0.85vw,10px); --fs-td: clamp(10px,1.05vw,12px);
    --fs-label: clamp(8px,0.85vw,10px); --fs-value: clamp(11px,1.1vw,13px);
    --radius: 10px;
    max-width:1400px; width:100%; margin:0 auto;
    padding:clamp(12px,2vh,22px) clamp(12px,2vw,24px) 0;
    font-family:'Inter',sans-serif; color:#fff;
    display:flex; flex-direction:column;
}
/* Page title -- scrolls away */
.pageHeader {
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
    gap:clamp(8px,1.2vw,14px); border-left:clamp(3px,0.4vw,5px) solid var(--orange);
    padding:clamp(8px,1.2vw,14px) clamp(14px,1.8vw,22px);
    background:rgba(255,255,255,0.62); border-radius:0 12px 12px 0;
    backdrop-filter:blur(15px); box-shadow:0 4px 15px rgba(0,0,0,0.07);
    margin-bottom:clamp(10px,1.5vh,16px);
}
.headerLeft{display:flex;flex-direction:column;gap:3px;min-width:0;flex:1;}
.title{font-family:'Cinzel',serif;color:var(--navy-deep);font-size:clamp(18px,2.5vw,24px);font-weight:700;text-transform:uppercase;letter-spacing:2px;margin:0;}
.subtitle{color:#64748b;font-size:clamp(9px,0.9vw,11px);font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:0;}

/* Sticky control cluster -- locks under the app bar, page scrolls behind it */
.controlHub {
    position: sticky; top: var(--app-header-h); z-index: 60;
    background: #f4f1ec; /* solid page bg so nothing shows through */
    padding: 10px 0 8px;
    display: flex; flex-direction: column; gap: 8px;
}
.searchBlock{flex:0 1 clamp(280px,40vw,480px);min-width:0;}
.searchInner{position:relative;display:flex;align-items:center;background:#fff;border:1.5px solid #c8d6d7;border-radius:6px;height:clamp(36px,4.5vw,44px);}
.searchInner:focus-within{border-color:var(--orange);box-shadow:0 0 0 3px rgba(238,140,58,0.18);}
.searchIcon{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--orange);pointer-events:none;}
.searchInput{width:100%;border:none;outline:none;background:transparent;color:#1a2e30;padding:0 12px 0 38px;font-weight:600;font-size:12px;height:100%;}
.searchInput::placeholder{color:rgba(26,46,48,0.35);font-weight:500;}
.searchClearBtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--orange);cursor:pointer;display:flex;}
.filterRail{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;}
.filterRail::-webkit-scrollbar{display:none;}
.filterBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:8px 16px;border-radius:6px;font-weight:900;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;white-space:nowrap;transition:all .2s;}
.filterBtn:hover{color:var(--orange);border-color:var(--orange);}
.activeFilter{background:var(--orange) !important;color:#1a2e30 !important;border-color:var(--orange) !important;}
.legendRow{display:flex;flex-wrap:wrap;gap:14px;padding:2px 0 0;}
.legendItem{display:flex;align-items:center;gap:6px;font-size:10px;font-weight:700;color:rgba(26,46,48,0.6);}
.legendDot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0;}

/* Table panel -- bottom corner brackets + pins, NO top corner brackets */
.tablePanel{position:relative;background:linear-gradient(160deg,#1c3335 0%,#213E40 100%);border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;}
/* Inner scroll: down-scroll = table, up-scroll at top = page */
.tableScroll{max-height:calc(100vh - 320px);min-height:280px;overflow-y:auto;overflow-x:auto;border-radius:var(--radius);}
.tableScroll::-webkit-scrollbar{width:5px;height:5px;}
.tableScroll::-webkit-scrollbar-thumb{background:rgba(238,140,58,0.4);border-radius:2px;}
.ledgerTable{width:100%;border-collapse:separate;border-spacing:0;min-width:700px;}
/* Opaque sticky header -- rows slide under and disappear behind it */
.ledgerTable thead th{
    position:sticky;top:0;z-index:5;
    background:#162a2c;color:var(--orange);
    font-size:var(--fs-th);font-weight:900;letter-spacing:2px;text-transform:uppercase;
    text-align:left;padding:clamp(11px,1.5vw,18px) clamp(12px,1.8vw,20px);
    border-bottom:3px solid var(--orange);white-space:nowrap;user-select:none;
}
.ledgerTable thead th:first-child{border-radius:0;}
.sortable{cursor:pointer;transition:background .18s,color .18s;}
.sortable:hover{background:rgba(238,140,58,0.07);color:#fff;}
.ledgerTable tbody td{padding:12px 14px;border-bottom:1px solid rgba(255,255,255,0.06);vertical-align:top;color:#fff;font-size:var(--fs-td);}
/* Hover: solid subtle bg only -- never fades the text */
.ledgerTable tbody tr{cursor:pointer;transition:background .15s;}
.ledgerTable tbody tr:hover{background:rgba(255,255,255,0.05);}
.rowReceivable{background:rgba(239,68,68,0.05);}
.rowCritical{background:rgba(239,68,68,0.07);}
.indexRow{display:flex;align-items:flex-start;gap:6px;}
.indexRow strong{font-family:'Space Mono',monospace;color:#fff;}
.stack{display:flex;flex-direction:column;gap:2px;}
.stackSub{font-size:10px;font-weight:600;color:rgba(255,255,255,0.55);font-family:'Space Mono',monospace;}
.ownerName{font-weight:800;color:#fff;}
.ownerPhone{font-family:'Space Mono',monospace;font-size:11px;color:rgba(255,255,255,0.7);}
.statusGroup{display:flex;flex-direction:column;gap:4px;align-items:flex-start;}
.tagReceivable,.tagPaid,.tagStandard,.tagCritical{background:none;border:none;font-size:10px;font-weight:900;letter-spacing:1px;text-transform:uppercase;padding:0;}
.tagReceivable{color:#fca5a5;}
.tagPaid{color:#34d399;}
.tagStandard{color:rgba(255,255,255,0.6);}
.tagCritical{color:#ef4444;}
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
.pageBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:7px 14px;border-radius:6px;font-weight:900;font-size:10px;cursor:pointer;display:inline-flex;gap:6px;align-items:center;}
.pageBtn:disabled{opacity:0.4;cursor:not-allowed;}
.pageIndicator{color:rgba(255,255,255,0.6);font-size:10px;font-weight:800;letter-spacing:1px;}
.recordCount{color:var(--orange);}
.topBtn{position:fixed;left:clamp(14px,2vw,26px);bottom:clamp(14px,2vh,26px);z-index:9500;background:transparent;border:none;color:var(--orange);width:38px;height:38px;font-size:23px;display:flex;align-items:center;justify-content:center;cursor:pointer;opacity:0.9;filter:drop-shadow(0 0 6px rgba(238,140,58,0.6));transition:transform .2s,opacity .2s,filter .2s;}
.topBtn:hover{transform:translateY(-3px);opacity:1;filter:drop-shadow(0 0 10px rgba(238,140,58,0.85));}
""")

subprocess.run(['git','add','.'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','commit','-m','fix31: Ledger demo scroll model (sticky toolbar + inner table scroll + opaque sticky header + non-fading hover + bottom-only corner decor)'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','push'],check=False,cwd=ROOT,capture_output=True)
print("Wrote:", *WROTE, sep="\n  ")
print("Done. Pushed.")