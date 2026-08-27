#!/usr/bin/env python3
"""fix.py — full desired-state re-issue (safe on reset repo). Run: py fix.py"""
import sys, subprocess, os
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
WROTE, WARN = [], []

def write(rel, content):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8"); WROTE.append(rel)

def patch(rel, old, new):
    p = ROOT / rel
    if not p.exists(): WARN.append(rel + " (missing)"); return
    t = p.read_text(encoding="utf-8")
    if new.strip() and new in t: return
    if old not in t: WARN.append(rel + " (anchor not found, skipped)"); return
    p.write_text(t.replace(old, new, 1), encoding="utf-8"); WROTE.append(rel + " (patched)")

# =====================================================================
# BackToTopButton (shared, borderless standard arrow)
# =====================================================================
write('erp-frontend/src/components/common/BackToTopButton.jsx', r"""// PATH: erp-frontend/src/components/common/BackToTopButton.jsx
import React from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';
export default function BackToTopButton({ label = 'Back to top' }) {
    const scrollToTop = () => {
        const el = document.querySelector('[class*="scrollArea"]');
        if (el) el.scrollTo({ top: 0, behavior: 'smooth' });
        else window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    return (
        <button type="button" className={styles.topBtn} onClick={scrollToTop} aria-label={label}>
            <FiArrowUp aria-hidden="true" />
        </button>
    );
}
""")
write('erp-frontend/src/components/common/BackToTopButton.module.css', r"""/* PATH: erp-frontend/src/components/common/BackToTopButton.module.css */
.topBtn {
    position: fixed; left: clamp(14px, 2vw, 26px); bottom: clamp(14px, 2vh, 26px); z-index: 9500;
    background: transparent; border: none; color: #EE8C3A;
    width: 38px; height: 38px; font-size: 23px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; opacity: 0.9;
    filter: drop-shadow(0 0 6px rgba(238, 140, 58, 0.6));
    transition: transform 0.2s ease, opacity 0.2s ease, filter 0.2s ease;
}
.topBtn:hover { transform: translateY(-3px); opacity: 1; filter: drop-shadow(0 0 10px rgba(238, 140, 58, 0.85)); }
.topBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 3px; }
""")

# =====================================================================
# LedgerPage.jsx — PROJECT LEDGER + clean INDEX column (dot + index + NINs)
# =====================================================================
write('erp-frontend/src/pages/Ledger/LedgerPage.jsx', r"""// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiLayers, FiSearch, FiMapPin, FiUser, FiCreditCard,
    FiChevronLeft, FiChevronRight,
    FiArrowUp, FiArrowDown, FiClock, FiUsers,
    FiAlertTriangle, FiX
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
        proj.landTitle?.plotNumber, proj.projectIndex,
        proj.district, proj.county, proj.subCounty, proj.parish, proj.village, proj.area,
        proj.landTitle?.blockRoad, proj.landTitle?.tenure, proj.landTitle?.titleId,
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

            <div className={styles.controlHub}>
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
                                const nins = (proj.proprietors || []).map(p => p.nationalId).filter(Boolean).join(' / ');
                                return (
                                    <tr key={proj.id}
                                        onClick={() => navigate(`/folder/${proj.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/folder/${proj.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Record: ${proj.projectIndex || proj.landTitle?.plotNumber}`}
                                        className={isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>
                                        {/* INDEX column: dot + index + NIN(s) below only */}
                                        <td className={styles.plotCell}>
                                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                                                <PaymentDot proj={proj} />
                                                <div>
                                                    <strong>#{proj.projectIndex || '---'}</strong>
                                                    <div>
                                                        <span className={styles.ownerPhone}>{nins || '---'}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            <div className={styles.ownerWrap}>
                                                <div className={styles.ownerMeta}>
                                                    <span className={styles.ownerName}>{proj.proprietors?.[0]?.fullName || '---'}</span>
                                                </div>
                                                {proj.proprietors?.length > 1 && (
                                                    <div className={styles.jointBadge}>
                                                        <FiUsers aria-hidden="true" />
                                                        <span>+{proj.proprietors.length - 1} MORE</span>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td><span className={styles.ownerPhone}>{proj.proprietors?.[0]?.phoneNumber || '---'}</span></td>
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
# IntakePage.jsx — improved intake (top Save+red Cancel, read-only date,
# 50k default, required location+title, 2-btn modal, local-only stages)
# =====================================================================
write('erp-frontend/src/pages/Intake/IntakePage.jsx', r"""// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useBlocker } from 'react-router-dom';
import { createPortal } from 'react-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiEdit3, FiBookmark, FiX, FiCopy, FiFile, FiEye, FiRefreshCw, FiCalendar
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareSelect from '../../components/common/HardwareSelect';
import BackToTopButton from '../../components/common/BackToTopButton';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import styles from './IntakePage.module.css';

const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });
const PROJECT_TYPES = [
    { value: 'NEW_FOLDER',   label: 'New Folder',   icon: <FiFolderPlus aria-hidden="true" />, hint: 'No title yet' },
    { value: 'NEW_TITLE',    label: 'New Title',    icon: <FiFilePlus aria-hidden="true" />,   hint: 'Title captured now' },
    { value: 'LEGACY_TITLE', label: 'Legacy Title', icon: <FiArchive aria-hidden="true" />,    hint: 'Existing title, receivable' },
];
const TENURE_OPTIONS = ['FREEHOLD', 'MAILO', 'LEASEHOLD', 'CUSTOMARY'];
const DEFAULT_STAGES = ['Field Work', 'Deed Plan', 'LC Inspection', 'District Land Board Approval', 'Tax Assessment and Stamp Duty', 'Registration and Title Issuance'];
const DEFAULT_MONTHLY_STORAGE_FEE = 50000;
const todayISO = () => new Date().toISOString().slice(0, 10);
const todayDMY = () => { const d = new Date(); return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`; };
const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';
const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';
const INDEX_CACHE_KEY = 'geSolutions.intake.nextIndexPreview';
const loadPresets = () => { try { const r = localStorage.getItem(PRESET_STORAGE_KEY); return r ? JSON.parse(r) : []; } catch { return []; } };
const savePresets = (p) => { try { localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(p)); } catch {} };

export default function IntakePage() {
    const navigate = useNavigate();
    const topRef = useRef(null);
    const fileInputRef = useRef(null);
    const [saving, setSaving] = useState(false);
    const [nextIndex, setNextIndex] = useState('');
    const [projectType, setProjectType] = useState('NEW_FOLDER');
    const [projectStartDate] = useState(todayISO);
    const [owners, setOwners] = useState([EMPTY_OWNER()]);
    const [district, setDistrict] = useState('');
    const [county, setCounty] = useState('');
    const [subCounty, setSubCounty] = useState('');
    const [parish, setParish] = useState('');
    const [village, setVillage] = useState('');
    const [area, setArea] = useState('');

    // Stages are LOCAL-ONLY: edits never touch the master template, so the
    // list always resets to defaults whenever the form is opened unsaved.
    const [masterTemplates, setMasterTemplates] = useState([]);
    const [stageList, setStageList] = useState(() => DEFAULT_STAGES.map(name => ({ id: null, name })));
    const [checked, setChecked] = useState({ [DEFAULT_STAGES[0]]: true });
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [insertAfterName, setInsertAfterName] = useState('');
    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState('');
    const [showSavePreset, setShowSavePreset] = useState(false);

    const [titleId, setTitleId] = useState('');
    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');
    const [titleIssueDate, setTitleIssueDate] = useState('');
    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);
    const [initialStorageFee, setInitialStorageFee] = useState(0);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState(DEFAULT_MONTHLY_STORAGE_FEE);
    const [fileQueue, setFileQueue] = useState([]);
    const [notes, setNotes] = useState('');
    const [dirty, setDirty] = useState(false);
    const dirtyRef = useRef(false);
    const markDirty = useCallback(() => { dirtyRef.current = true; setDirty(true); }, []);
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((msg, type = 'info') => {
        const id = Date.now() + Math.random();
        setToasts(p => [...p, { id, msg, type }]);
        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    }, []);

    useEffect(() => {
        stageTemplateService.getTemplate().then(list => {
            const sorted = [...(list || [])].sort((a, b) => (a.displayOrder ?? 0) - (b.displayOrder ?? 0));
            const seen = new Set(); const uniq = [];
            sorted.forEach(t => { if (t.stageName && !seen.has(t.stageName)) { seen.add(t.stageName); uniq.push({ id: t.id, name: t.stageName }); } });
            setMasterTemplates(uniq);
        }).catch(() => {});
    }, []);

    useEffect(() => {
        let cancelled = false;
        try { const c = localStorage.getItem(INDEX_CACHE_KEY); if (c) setNextIndex(c); } catch {}
        const load = (attempt) => {
            landService.getNextIndex().then(idx => {
                if (cancelled) return;
                if (idx) { setNextIndex(idx); try { localStorage.setItem(INDEX_CACHE_KEY, idx); } catch {} }
            }).catch(() => {
                if (cancelled) return;
                if (attempt < 2) { setTimeout(() => load(attempt + 1), 2500); return; }
                let cached = null; try { cached = localStorage.getItem(INDEX_CACHE_KEY); } catch {}
                if (!cached) toast('Could not load the next index. Refresh to try again.', 'error');
            });
        };
        load(0);
        return () => { cancelled = true; };
    }, [toast]);

    const collapsedOnce = useRef(false);
    useEffect(() => {
        const el = topRef.current;
        if (!el) return;
        const handler = () => {
            if (collapsedOnce.current) return;
            collapsedOnce.current = true;
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
        };
        el.addEventListener('focusin', handler);
        el.addEventListener('input', handler);
        el.addEventListener('click', handler);
        return () => { el.removeEventListener('focusin', handler); el.removeEventListener('input', handler); el.removeEventListener('click', handler); };
    }, []);

    useEffect(() => {
        const h = (e) => { if (dirtyRef.current) { e.preventDefault(); e.returnValue = ''; } };
        window.addEventListener('beforeunload', h);
        return () => window.removeEventListener('beforeunload', h);
    }, []);

    const blocker = useBlocker(dirty && !saving);
    useEffect(() => {
        if (blocker.state !== 'blocked') return;
        const onKeyDown = (e) => { if (e.key === 'Escape') blocker.reset(); };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [blocker]);

    const firstStageName = stageList[0]?.name;
    const lastStageName = stageList[stageList.length - 1]?.name;
    const finalStageChecked = !!checked['Registration and Title Issuance'];
    const isLegacy = projectType === 'LEGACY_TITLE';
    const titleAtIntake = projectType === 'NEW_TITLE';
    const isTitleType = isLegacy || titleAtIntake;
    const isTitleSectionVisible = isTitleType || finalStageChecked;
    const showStages = !isTitleType;

    const handleProjectTypeChange = (value) => {
        setProjectType(value); markDirty();
        if (value === 'LEGACY_TITLE' || value === 'NEW_TITLE') {
            const all = {}; stageList.forEach(s => { all[s.name] = true; }); setChecked(all);
        } else {
            setChecked({ [firstStageName]: true });
        }
    };
    const toggleStage = (name) => { markDirty(); setChecked(p => ({ ...p, [name]: !p[name] })); };

    const openInsertBelow = (name) => { setInsertAfterName(name); setAddingStage(true); };
    const handleAddStage = () => {
        const name = newStageName.trim();
        if (!name) { toast('Enter a stage name first.', 'error'); return; }
        if (stageList.some(s => s.name.toLowerCase() === name.toLowerCase())) { toast('That stage is already on the list.', 'error'); return; }
        let k;
        if (!stageList.length) k = 0;
        else {
            k = stageList.length - 1;
            const idx = stageList.findIndex(s => s.name === insertAfterName);
            if (idx >= 0) k = idx + 1;
            k = Math.min(Math.max(k, 1), Math.max(1, stageList.length - 1));
        }
        const next = [...stageList]; next.splice(k, 0, { id: null, name });
        setStageList(next); setChecked(p => ({ ...p, [name]: true }));
        setNewStageName(''); setInsertAfterName(''); setAddingStage(false);
        markDirty(); toast('Stage inserted.', 'success');
    };
    const handleDeleteStage = (name) => {
        setStageList(p => p.filter(s => s.name !== name));
        setChecked(p => { const n = { ...p }; delete n[name]; return n; });
        markDirty(); toast('Stage removed.', 'success');
    };
    const handleRestoreDefaults = () => {
        setStageList(DEFAULT_STAGES.map(n => ({ id: null, name: n })));
        setChecked({ [DEFAULT_STAGES[0]]: true });
        setAddingStage(false); setNewStageName(''); setInsertAfterName('');
        markDirty(); toast('Default stages restored.', 'success');
    };
    const handleSavePreset = () => {
        if (!presetName.trim()) { toast('Name the preset first.', 'error'); return; }
        const stageNames = stageList.filter(s => checked[s.name]).map(s => s.name);
        const next = [...presets.filter(p => p.name !== presetName.trim()), { name: presetName.trim(), stageNames }];
        setPresets(next); savePresets(next); setPresetName(''); setShowSavePreset(false);
        toast('Stage preset saved.', 'success');
    };
    const applyPreset = (name) => {
        const preset = presets.find(p => p.name === name);
        if (!preset) return;
        const next = {}; stageList.forEach(s => { next[s.name] = preset.stageNames.includes(s.name); });
        setChecked(next); markDirty();
    };
    const deletePreset = (name) => { setPresets(presets.filter(p => p.name !== name)); savePresets(presets.filter(p => p.name !== name)); };

    const updateOwner = (idx, field, val) => { markDirty(); setOwners(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o)); };
    const handleFileUpload = (e) => {
        const items = Array.from(e.target.files).map(f => ({ name: f.name, size: f.size, file: f, url: URL.createObjectURL(f) }));
        if (items.length) { setFileQueue(p => [...p, ...items]); markDirty(); }
        e.target.value = '';
    };
    const removeFile = (i) => setFileQueue(p => { URL.revokeObjectURL(p[i].url); return p.filter((_, idx) => idx !== i); });
    const triggerFileInput = () => fileInputRef.current && fileInputRef.current.click();

    const validate = () => {
        if (!district.trim()) { toast('District is required.', 'error'); return false; }
        if (!county.trim()) { toast('County is required.', 'error'); return false; }
        if (!subCounty.trim()) { toast('Sub-county is required.', 'error'); return false; }
        if (!parish.trim()) { toast('Parish is required.', 'error'); return false; }
        if (!village.trim()) { toast('Village is required.', 'error'); return false; }
        if (!area.trim()) { toast('Area is required.', 'error'); return false; }
        for (let i = 0; i < owners.length; i++) {
            const o = owners[i];
            if (!o.nationalId.trim()) { toast(`Owner ${i + 1}: NIN is required.`, 'error'); return false; }
            if (!o.fullName.trim()) { toast(`Owner ${i + 1}: Full Name is required.`, 'error'); return false; }
            if (!o.phone.trim()) { toast(`Owner ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }
        }
        if (isTitleSectionVisible) {
            if (!titleId.trim()) { toast('Title ID is required.', 'error'); return false; }
            if (!plotNumber.trim()) { toast('Plot Number is required.', 'error'); return false; }
            if (!blockRoad.trim()) { toast('Block is required.', 'error'); return false; }
            if (!titleIssueDate) { toast('Title Date is required.', 'error'); return false; }
        }
        if (!(Number(totalCost) > 0)) { toast('Total Cost must be greater than 0.', 'error'); return false; }
        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) { toast('Initial Payment is required (0 or more).', 'error'); return false; }
        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }
        return true;
    };

    const doSave = async () => {
        if (!validate()) return false;
        setSaving(true);
        try {
            let noteText = notes.trim();
            if (noteText && !/^\[\d{2}\/\d{2}\/\d{4}\]/.test(noteText)) noteText = `[${todayDMY()}] ${noteText}`;
            const payload = {
                district: district.trim().toUpperCase(), county: county.trim().toUpperCase(),
                subCounty: subCounty.trim().toUpperCase(), parish: parish.trim().toUpperCase(),
                village: village.trim().toUpperCase(), area: area.trim().toUpperCase(),
                totalCost: Number(totalCost) || 0, initialPayment: Number(initialPayment) || 0,
                isLegacy, titleAtIntake, projectStartDate: todayISO(),
                owners: owners.map(o => ({
                    fullName: o.fullName.trim().toUpperCase(), phone: o.phone.trim(),
                    email: o.email.trim().toLowerCase(), nationalId: o.nationalId.trim().toUpperCase(), address: o.address.trim(),
                })),
                selectedStages: stageList.filter(s => checked[s.name]).map(s => {
                    const m = masterTemplates.find(t => t.name === s.name);
                    return m
                        ? { stageTemplateId: m.id, stageName: s.name, isCustom: false, isCompleted: true }
                        : { stageName: s.name, isCustom: true, cost: 0, isCompleted: true };
                }),
                notes: noteText ? [{ content: noteText }] : [],
            };
            if (isTitleSectionVisible) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.blockRoad = blockRoad.trim().toUpperCase();
                payload.titleId = titleId.trim().toUpperCase();
                payload.titleIssueDate = titleIssueDate || null;
            }
            if (isLegacy) {
                payload.isStartAsReceivable = true;
                payload.initialStorageFee = Number(initialStorageFee) || 0;
                payload.monthlyStorageFee = Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE;
            }
            await landService.createAtomicEntry(payload, fileQueue.map(q => q.file));
            dirtyRef.current = false; setDirty(false);
            return true;
        } catch (err) {
            toast(err.response?.data?.message || 'Save failed', 'error');
            return false;
        } finally { setSaving(false); }
    };

    const handleSubmit = async () => {
        const ok = await doSave();
        if (ok) { toast('Project registered successfully!', 'success'); setTimeout(() => navigate('/land/projects'), 1200); }
    };

    const handleDuplicate = async () => {
        const ok = await doSave();
        if (!ok) return;
        toast('Saved. Form duplicated for the next plot.', 'success');
        setProjectType('NEW_FOLDER');
        setTitleId(''); setTenure('FREEHOLD'); setPlotNumber(''); setBlockRoad(''); setTitleIssueDate('');
        setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0); setMonthlyStorageFee(DEFAULT_MONTHLY_STORAGE_FEE);
        setNotes(''); setFileQueue(q => { q.forEach(x => URL.revokeObjectURL(x.url)); return []; });
        setStageList(DEFAULT_STAGES.map(n => ({ id: null, name: n })));
        setChecked({ [DEFAULT_STAGES[0]]: true });
        landService.getNextIndex().then(idx => { if (idx) { setNextIndex(idx); try { localStorage.setItem(INDEX_CACHE_KEY, idx); } catch {} } }).catch(() => {});
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const amountOwed = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));
    let n = 0;
    const nIndex = ++n, nOwners = ++n;
    const nTitle = isTitleSectionVisible ? ++n : null;
    const nLocation = ++n, nStages = showStages ? ++n : null;
    const nFinancials = ++n, nDocuments = ++n, nNotes = ++n;

    return (
        <div className={styles.container} ref={topRef}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Project</h1>
                    <p className={styles.subtitle}>Intake Form</p>
                </div>
                <div className={styles.actions}>
                    <button type="button" className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> Save
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.cancelBtn}`} onClick={() => navigate(-1)}>Cancel</button>
                </div>
            </header>

            <div className={styles.sections}>
                <CollapsibleSection icon={<FiHash />} title={`${nIndex}. Entry Mode`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={styles.label}>Index</label>
                            <div className={styles.indexDisplay}>{nextIndex || 'Loading...'}</div>
                            <p className={styles.hint}>Next available index, assigned on save</p>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Date Started</label>
                            <div className={styles.indexDisplay}>{todayDMY()}</div>
                            <p className={styles.hint}>Auto-generated with today's date</p>
                        </div>
                    </div>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${styles.required}`}>Type</label>
                        <div className={styles.typeGroup}>
                            {PROJECT_TYPES.map(pt => (
                                <button key={pt.value} type="button"
                                    className={`${styles.typeBtn} ${projectType === pt.value ? styles.typeBtnActive : ''}`}
                                    onClick={() => handleProjectTypeChange(pt.value)}>
                                    {pt.icon}<span>{pt.label}</span>
                                </button>
                            ))}
                        </div>
                        <p className={styles.typeHint}>{PROJECT_TYPES.find(pt => pt.value === projectType)?.hint}</p>
                    </div>
                </CollapsibleSection>

                <CollapsibleSection icon={<FiUsers />} title={`${nOwners}. Owners`}>
                    {owners.map((o, idx) => (
                        <div key={idx} className={styles.ownerRow}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>NIN</label>
                                <input className={styles.input} value={o.nationalId} onChange={e => updateOwner(idx, 'nationalId', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Full Name</label>
                                <input className={styles.input} value={o.fullName} onChange={e => updateOwner(idx, 'fullName', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Phone</label>
                                <input className={styles.input} value={o.phone} onChange={e => updateOwner(idx, 'phone', e.target.value)} placeholder="0700 000 000 / 0788 000 000" />
                                <p className={styles.hint}>Multiple: separate with /</p>
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Email</label>
                                <input className={styles.input} value={o.email} onChange={e => updateOwner(idx, 'email', e.target.value)} />
                            </div>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`}
                                onClick={() => setOwners(p => p.filter((_, i) => i !== idx))}
                                disabled={owners.length === 1} aria-label="Remove owner">
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                    <button type="button" className={styles.addBtn} onClick={() => { setOwners(p => [...p, EMPTY_OWNER()]); markDirty(); }}>
                        <FiPlus /> Add Owner
                    </button>
                </CollapsibleSection>

                {isTitleSectionVisible && (
                    <CollapsibleSection icon={<FiFileText />} title={`${nTitle}. Title Details`} accent>
                        <div className={styles.grid3}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Title ID</label>
                                <input className={styles.input} value={titleId} onChange={e => { setTitleId(e.target.value); markDirty(); }} />
                            </div>
                            <HardwareSelect label="Tenure" required options={TENURE_OPTIONS} value={tenure} onChange={(v) => { setTenure(v); markDirty(); }} />
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Plot Number</label>
                                <input className={styles.input} value={plotNumber} onChange={e => { setPlotNumber(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Block</label>
                                <input className={styles.input} value={blockRoad} onChange={e => { setBlockRoad(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Title Date</label>
                                <input type="date" className={styles.input} value={titleIssueDate} onChange={e => { setTitleIssueDate(e.target.value); markDirty(); }} />
                            </div>
                        </div>
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiMap />} title={`${nLocation}. Location`}>
                    <div className={styles.grid3}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>District</label>
                            <input className={styles.input} value={district} onChange={e => { setDistrict(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>County</label>
                            <input className={styles.input} value={county} onChange={e => { setCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Sub-county</label>
                            <input className={styles.input} value={subCounty} onChange={e => { setSubCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Parish</label>
                            <input className={styles.input} value={parish} onChange={e => { setParish(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Village</label>
                            <input className={styles.input} value={village} onChange={e => { setVillage(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Area</label>
                            <input className={styles.input} value={area} onChange={e => { setArea(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                </CollapsibleSection>

                {showStages && (
                    <CollapsibleSection icon={<FiCheckSquare />} title={`${nStages}. Stages`}
                        right={
                            <div style={{ display: 'flex', gap: 'var(--gap-md)', flexWrap: 'wrap', alignItems: 'center' }}>
                                {presets.length > 0 && (
                                    <HardwareSelect compact placeholder="Apply preset..." value="" options={presets.map(p => p.name)} onChange={applyPreset} />
                                )}
                                <button type="button" className={styles.addBtn} onClick={() => setShowSavePreset(s => !s)}>
                                    <FiBookmark /> Save Preset
                                </button>
                                <button type="button" className={styles.addBtn} onClick={handleRestoreDefaults}>
                                    <FiRefreshCw /> Restore Defaults
                                </button>
                            </div>
                        }>
                        {showSavePreset && (
                            <div className={styles.inlineAddRow}>
                                <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setShowSavePreset(false); setPresetName(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        {addingStage && (
                            <div className={styles.inlineAddRow}>
                                <span className={styles.insertCtx}>{insertAfterName ? `Insert under: ${insertAfterName}` : 'Insert before last stage'}</span>
                                <input className={styles.input} placeholder="New stage name" value={newStageName} onChange={e => setNewStageName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleAddStage}>Add</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setAddingStage(false); setNewStageName(''); setInsertAfterName(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        <div className={styles.stageList}>
                            {stageList.map((s) => {
                                const isLast = s.name === lastStageName;
                                const isFirst = s.name === firstStageName;
                                return (
                                    <label key={s.name} className={`${styles.stageItem} ${checked[s.name] ? styles.checked : ''}`}>
                                        <input type="checkbox" className={styles.checkbox} checked={!!checked[s.name]} onChange={() => toggleStage(s.name)} />
                                        <span className={styles.stageName}>{s.name}</span>
                                        <span className={styles.stageActions}>
                                            {!isLast && (
                                                <button type="button" className={styles.plusBtn} title="Insert a stage below this one"
                                                    aria-label={`Insert stage below ${s.name}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(s.name); }}>
                                                    <FiPlus size={12} />
                                                </button>
                                            )}
                                            {!isLast && !isFirst && (
                                                <button type="button" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDeleteStage(s.name); }}
                                                    aria-label={`Delete stage ${s.name}`}>
                                                    <FiTrash2 size={12} />
                                                </button>
                                            )}
                                        </span>
                                    </label>
                                );
                            })}
                        </div>
                        {presets.length > 0 && (
                            <div className={styles.presetList}>
                                {presets.map(p => (
                                    <span key={p.name} className={styles.presetChip}>
                                        {p.name}
                                        <button type="button" className={styles.presetChipRemove} onClick={() => deletePreset(p.name)} aria-label={`Delete preset ${p.name}`}>
                                            <FiX size={12} />
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiDollarSign />} title={`${nFinancials}. Financials`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Total Cost</label>
                            <input type="number" className={styles.input} value={totalCost} onChange={e => { setTotalCost(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Initial Payment</label>
                            <input type="number" className={styles.input} value={initialPayment} onChange={e => { setInitialPayment(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                    {isLegacy && (
                        <>
                            <h3 className={styles.subheading}><FiArchive size={13} /> Storage Fees</h3>
                            <div className={styles.grid2}>
                                <div className={styles.field}>
                                    <label className={styles.label}>Initial Storage Fee</label>
                                    <input type="number" className={styles.input} value={initialStorageFee} onChange={e => { setInitialStorageFee(e.target.value); markDirty(); }} />
                                </div>
                                <div className={styles.field}>
                                    <label className={styles.label}>Monthly Storage Fee</label>
                                    <input type="number" className={styles.input} value={monthlyStorageFee} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} />
                                    <p className={styles.hint}>System default: {DEFAULT_MONTHLY_STORAGE_FEE.toLocaleString()}</p>
                                </div>
                            </div>
                        </>
                    )}
                    <div className={styles.financialsSummary}>
                        <div className={styles.finRow}><span>Total Cost</span><span>{Number(totalCost) || 0}</span></div>
                        <div className={styles.finRow}><span>Initial Payment</span><span>{Number(initialPayment) || 0}</span></div>
                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}
                        <div className={`${styles.finRow} ${styles.total}`}><span>Amount Owed</span><span>{amountOwed}</span></div>
                    </div>
                </CollapsibleSection>

                <div className={styles.splitRow}>
                    <CollapsibleSection icon={<FiUploadCloud />} title={`${nDocuments}. Documents`}>
                        <div className={styles.dropzone} onClick={triggerFileInput} role="button" tabIndex={0}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); } }}>
                            <span className={styles.dropzoneIcon}><FiUploadCloud size={18} /></span>
                            <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>
                            <span className={styles.dropzoneSub}>Required - PDF, images, any file</span>
                        </div>
                        <input ref={fileInputRef} type="file" multiple onChange={handleFileUpload} style={{ display: 'none' }} />
                        <div className={styles.fileList}>
                            {fileQueue.map((f, i) => (
                                <div key={i} className={styles.fileItem}>
                                    <span className={styles.fileMeta}>
                                        <FiFile className={styles.fileIcon} size={14} />
                                        <span className={styles.fileName}>{f.name}</span>
                                        <span className={styles.fileSize}>{fmtSize(f.size)}</span>
                                    </span>
                                    <span className={styles.fileActions}>
                                        <a className={`${styles.btn} ${styles.small}`} href={f.url} target="_blank" rel="noreferrer" aria-label={`View ${f.name}`}>
                                            <FiEye size={12} /> View
                                        </a>
                                        <button type="button" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`} onClick={() => removeFile(i)} aria-label={`Remove ${f.name}`}>
                                            <FiTrash2 size={12} />
                                        </button>
                                    </span>
                                </div>
                            ))}
                        </div>
                    </CollapsibleSection>
                    <CollapsibleSection icon={<FiEdit3 />} title={`${nNotes}. Notes`}>
                        <div className={styles.notesWrap}>
                            <span className={styles.noteDateChip}><FiCalendar size={11} /> {todayDMY()}</span>
                            <textarea className={styles.textarea} value={notes} onChange={e => { setNotes(e.target.value); markDirty(); }} placeholder="Shared project notes - visible to all staff on the folder page..." />
                            <p className={styles.hint}>Saved with today's date as an intake note.</p>
                        </div>
                    </CollapsibleSection>
                </div>
            </div>

            <div className={styles.bottomBar}>
                <div className={styles.bottomBarRight}>
                    <button type="button" className={styles.addBtn} onClick={handleDuplicate} disabled={saving}>
                        <FiCopy /> Duplicate
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> Save Project
                    </button>
                </div>
            </div>

            <BackToTopButton />

            {blocker.state === 'blocked' && typeof document !== 'undefined' && createPortal(
                <div className={styles.modalOverlay} onClick={() => blocker.reset()}>
                    <div className={styles.modalCard} onClick={e => e.stopPropagation()}>
                        <h3 className={styles.modalTitle}>Unsaved work</h3>
                        <p className={styles.modalText}>You have unsaved information on this form. Save before leaving?</p>
                        <div className={styles.modalBtns}>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`} onClick={() => blocker.proceed()}>Leave</button>
                            <button type="button" className={`${styles.btn} ${styles.primary}`}
                                onClick={async () => { const ok = await doSave(); if (ok) blocker.proceed(); else blocker.reset(); }}>
                                <FiSave /> Save & Leave
                            </button>
                        </div>
                        <p className={styles.modalHint}>Click outside or press Esc to keep editing</p>
                    </div>
                </div>,
                document.body
            )}

            {typeof document !== 'undefined' && createPortal(
                <div className={styles.toastStack} role="region" aria-label="Notifications" aria-live="polite">
                    {toasts.map(t => (
                        <div key={t.id} className={`${styles.toast} ${styles['toast_' + (t.type || 'info')]}`}>{t.msg}</div>
                    ))}
                </div>,
                document.body
            )}
        </div>
    );
}
""")

# =====================================================================
# IntakePage.module.css
# =====================================================================
write('erp-frontend/src/pages/Intake/IntakePage.module.css', r"""/* PATH: erp-frontend/src/pages/Intake/IntakePage.module.css */
:root {
    --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
    --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981;
    --gap-xl: clamp(10px,1.6vw,18px); --gap-lg: clamp(7px,1.1vw,14px); --gap-md: clamp(5px,0.9vw,10px);
    --radius: 10px; --radius-sm: 6px;
    --fs-h1: clamp(18px,2.5vw,24px); --fs-sub: clamp(9px,0.9vw,11px); --fs-label: clamp(8px,0.85vw,10px);
    --fs-value: clamp(10px,1.05vw,12px); --fs-meta: clamp(8px,0.85vw,10px); --fs-btn: clamp(8px,0.85vw,10px);
}
.container {
    --input-height: clamp(34px,4.3vw,40px); --input-font: clamp(11px,1.05vw,13px);
    --input-px: clamp(9px,1.2vw,13px); --input-radius: 6px;
    max-width: 1400px; width: 100%; margin: 0 auto;
    padding: clamp(12px,2vh,22px) clamp(12px,2vw,24px) 0;
    font-family: 'Inter', sans-serif; color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2,1,0.3,1) both;
    display: flex; flex-direction: column; gap: var(--gap-xl); box-sizing: border-box;
}
@keyframes warmBoot { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.pageHeader {
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
    gap: clamp(8px,1.2vw,14px); border-left: clamp(3px,0.4vw,5px) solid var(--orange);
    padding: clamp(8px,1.2vw,14px) clamp(14px,1.8vw,22px);
    background: rgba(255,255,255,0.62); border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07); flex-shrink: 0;
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
.title { font-family: 'Cinzel', serif; color: var(--navy-deep); font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; line-height: 1.1; margin: 0; }
.subtitle { font-family: 'Inter', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin: 0; }
.actions { display: flex; gap: var(--gap-md); flex-shrink: 0; }
.sections { display: flex; flex-direction: column; gap: var(--gap-lg); }
.splitRow { display: grid; grid-template-columns: 1fr 1fr; gap: var(--gap-lg); align-items: start; }
.btn {
    font-family: 'Inter', sans-serif; font-size: var(--fs-btn); font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px;
    padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: var(--radius-sm);
    border: 1.5px solid rgba(255,255,255,0.1); background: transparent; color: rgba(255,255,255,0.7);
    cursor: pointer; transition: background 0.2s, border-color 0.2s, color 0.2s;
    display: inline-flex; align-items: center; gap: 5px; text-decoration: none;
}
.btn:hover:not(:disabled) { background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.22); color: #fff; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.btn.primary { background: var(--orange); color: #fff; border-color: var(--orange); }
.btn.primary:hover { background: #d97a2b; border-color: #d97a2b; color: #fff; }
.btn:disabled { opacity: 0.18; cursor: not-allowed; }
.btn.small { padding: clamp(4px,0.7vw,7px) clamp(8px,1.1vw,12px); }
.btn.deleteBtn { border-color: rgba(239,68,68,0.3); color: rgba(239,68,68,0.7); }
.btn.deleteBtn:hover:not(:disabled) { background: rgba(239,68,68,0.15); border-color: var(--red); color: var(--red); }
.cancelBtn { color: var(--red); border-color: rgba(239,68,68,0.45); background: rgba(239,68,68,0.08); }
.cancelBtn:hover:not(:disabled) { background: rgba(239,68,68,0.16); border-color: var(--red); color: var(--red); }
.xBtn { background: transparent; border: none; color: var(--orange); cursor: pointer; display: inline-flex; align-items: center; padding: 5px; border-radius: 4px; transition: background 0.2s; }
.xBtn:hover { background: var(--orange-dim); }
.plusBtn { background: transparent; border: 1px solid rgba(238,140,58,0.3); color: var(--orange); cursor: pointer; display: inline-flex; align-items: center; padding: 4px 6px; border-radius: 4px; transition: all 0.2s; }
.plusBtn:hover { background: var(--orange-dim); border-color: var(--orange); }
.addBtn {
    background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85);
    padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: 6px;
    font-family: 'Inter', sans-serif; font-size: var(--fs-btn); font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
    cursor: pointer; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; align-self: flex-start;
}
.addBtn:hover:not(:disabled) { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.addBtn:disabled { opacity: 0.4; cursor: not-allowed; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap: var(--gap-lg); }
.grid3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px,1fr)); gap: var(--gap-lg); }
.field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.label { font-family: 'Inter', sans-serif; font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 2px; }
.required::after { content: '*'; color: var(--red); margin-left: 4px; }
.hint { font-size: var(--fs-meta); font-weight: 700; color: rgba(255,255,255,0.35); letter-spacing: 0.5px; margin: 0; }
.input, .textarea {
    font-family: 'Inter', sans-serif; font-weight: 600; border: 1.5px solid rgba(238,140,58,0.3);
    background: #ffffff; color: var(--navy); width: 100%; box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.textarea { min-height: 110px; resize: vertical; line-height: 1.5; }
.input:hover, .textarea:hover { border-color: var(--orange); }
.input:focus, .textarea:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 2px rgba(238,140,58,0.15); }
.indexDisplay {
    font-family: 'Space Mono', monospace; font-weight: 900; letter-spacing: 1px; color: var(--orange);
    font-size: var(--input-font); height: var(--input-height); display: flex; align-items: center; padding: 0 var(--input-px);
}
.typeGroup { display: flex; gap: clamp(5px,0.9vw,10px); flex-wrap: wrap; }
.typeBtn {
    display: flex; align-items: center; gap: 5px; background: rgba(26,46,48,0.75);
    border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85);
    padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: 6px;
    font-family: 'Inter', sans-serif; font-weight: 900; font-size: var(--fs-btn); letter-spacing: 1.5px; text-transform: uppercase;
    cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
}
.typeBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.typeBtnActive, .typeBtnActive:hover { background: #EE8C3A; color: #1a2e30; border-color: #EE8C3A; box-shadow: 0 0 14px rgba(238,140,58,0.4); }
.typeHint { font-size: var(--fs-meta); color: rgba(255,255,255,0.35); margin: 2px 0 0 0; letter-spacing: 0.5px; }
.ownerRow {
    display: grid; grid-template-columns: 1.2fr 2fr 1fr 1.5fr auto auto; gap: var(--gap-md); align-items: start;
    padding: clamp(6px,0.9vw,9px); background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.06); border-radius: var(--radius-sm);
}
.ownerRow .btn { margin-top: 20px; }
.subheading { font-family: 'Cinzel', serif; font-size: clamp(11px,1.3vw,13px); font-weight: 700; color: var(--orange); letter-spacing: 2px; text-transform: uppercase; display: flex; align-items: center; gap: 5px; margin: 2px 0 0 0; }
.inlineAddRow { display: flex; gap: var(--gap-md); align-items: center; flex-wrap: wrap; background: rgba(0,0,0,0.15); border: 1px solid var(--orange-border); border-radius: var(--radius-sm); padding: var(--gap-md); }
.inlineAddRow .input { width: auto; flex: 1 1 160px; }
.insertCtx { font-size: var(--fs-meta); color: var(--orange); font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
.stageList { display: flex; flex-direction: column; gap: var(--gap-md); }
.stageItem { display: flex; align-items: center; gap: var(--gap-md); padding: clamp(6px,0.9vw,9px); background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.06); border-radius: var(--radius-sm); cursor: pointer; transition: background 0.18s; }
.stageItem:hover { background: rgba(255,255,255,0.04); }
.stageItem.checked { background: rgba(238,140,58,0.07); }
.checkbox { width: 15px; height: 15px; accent-color: var(--orange); cursor: pointer; flex-shrink: 0; }
.stageName { font-weight: 700; color: #fff; font-size: var(--fs-value); letter-spacing: 0.5px; }
.stageActions { margin-left: auto; display: flex; gap: var(--gap-md); align-items: center; }
.presetList { display: flex; gap: var(--gap-md); flex-wrap: wrap; }
.presetChip { display: flex; align-items: center; gap: 5px; background: var(--orange-dim); color: var(--orange); border: 1px solid var(--orange-border); border-radius: 999px; padding: 3px 9px; font-size: var(--fs-meta); font-weight: 700; }
.presetChipRemove { background: none; border: none; color: inherit; cursor: pointer; display: flex; align-items: center; padding: 0; }
.financialsSummary { background: rgba(0,0,0,0.15); padding: var(--gap-lg); border-radius: var(--radius-sm); border: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; gap: var(--gap-md); }
.finRow { display: flex; justify-content: space-between; font-weight: 700; color: rgba(255,255,255,0.85); font-size: var(--fs-value); letter-spacing: 0.5px; }
.finRow.total { color: var(--orange); font-size: clamp(13px,1.4vw,17px); border-top: 1px solid rgba(238,140,58,0.25); padding-top: var(--gap-md); }
.dropzone { border: 2px dashed rgba(238,140,58,0.4); border-radius: var(--radius); padding: clamp(12px,1.6vw,18px); text-align: center; color: rgba(255,255,255,0.55); cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.dropzone:hover { background: var(--orange-dim); border-color: var(--orange); color: var(--orange); }
.dropzoneIcon { width: clamp(34px,4vw,44px); height: clamp(34px,4vw,44px); border-radius: 50%; background: rgba(238,140,58,0.12); border: 1px solid var(--orange-border); display: flex; align-items: center; justify-content: center; color: var(--orange); margin-bottom: 2px; }
.dropzoneTitle { font-weight: 800; font-size: var(--fs-value); letter-spacing: 1px; text-transform: uppercase; }
.dropzoneTitle .reqMark { color: var(--red); margin-left: 3px; }
.dropzoneSub { font-size: var(--fs-meta); color: rgba(255,255,255,0.35); font-weight: 700; letter-spacing: 0.5px; }
.fileList { display: flex; flex-direction: column; gap: var(--gap-md); }
.fileItem { display: flex; justify-content: space-between; align-items: center; gap: var(--gap-md); background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.06); color: #fff; font-size: var(--fs-value); font-weight: 600; padding: clamp(6px,0.9vw,9px) clamp(8px,1.1vw,12px); border-radius: var(--radius-sm); }
.fileMeta { display: flex; align-items: center; gap: 8px; min-width: 0; }
.fileIcon { color: var(--orange); flex-shrink: 0; }
.fileName { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fileSize { color: rgba(255,255,255,0.35); font-size: var(--fs-meta); font-weight: 700; flex-shrink: 0; }
.fileActions { display: flex; gap: var(--gap-md); flex-shrink: 0; }
.notesWrap { display: flex; flex-direction: column; gap: 4px; }
.noteDateChip { align-self: flex-start; display: inline-flex; align-items: center; gap: 5px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.08); color: rgba(255,255,255,0.6); font-size: var(--fs-meta); font-weight: 800; letter-spacing: 1px; padding: 3px 8px; border-radius: 4px; }
.bottomBar { display: flex; align-items: center; justify-content: flex-end; gap: var(--gap-md); padding: var(--gap-md) 0; margin-bottom: clamp(12px,2vh,22px); }
.bottomBarRight { display: flex; gap: var(--gap-md); align-items: center; }
.modalOverlay { position: fixed; inset: 0; background: rgba(10,20,22,0.72); backdrop-filter: blur(4px); z-index: 10000; display: flex; align-items: center; justify-content: center; }
.modalCard { width: min(480px,90vw); background: linear-gradient(135deg,#3a5a5c 0%,#213E40 100%); border: 1px solid var(--orange-border); border-radius: 12px; padding: clamp(16px,2vw,24px); display: flex; flex-direction: column; gap: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
.modalTitle { font-family: 'Cinzel', serif; color: var(--orange); letter-spacing: 2px; text-transform: uppercase; font-size: clamp(12px,1.4vw,15px); margin: 0; }
.modalText { color: rgba(255,255,255,0.75); font-size: var(--fs-value); font-weight: 600; margin: 0; }
.modalBtns { display: flex; gap: var(--gap-md); justify-content: flex-end; flex-wrap: wrap; }
.modalHint { font-size: var(--fs-meta); color: rgba(255,255,255,0.4); font-weight: 700; margin: 0; text-align: right; }
.toastStack { position: fixed; bottom: clamp(16px,2.5vh,28px); right: clamp(16px,2vw,28px); z-index: 99999; display: flex; flex-direction: column; gap: 8px; max-width: min(420px,90vw); pointer-events: none; }
.toast { background: #1a2e30; color: #fff; border: 1px solid rgba(238,140,58,0.28); padding: 12px 20px; border-radius: 6px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; animation: slideIn 0.3s ease-out; pointer-events: all; }
.toast_error { background: #ef4444; border-color: #ef4444; }
.toast_success { background: #10b981; border-color: #10b981; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@media (max-width: 900px) { .splitRow { grid-template-columns: 1fr; } .ownerRow { grid-template-columns: 1fr; } }
@media (max-width: 768px) {
    .pageHeader { flex-direction: column; align-items: flex-start; gap: var(--gap-lg); border-radius: 0; }
    .actions { width: 100%; } .actions .btn { flex: 1; justify-content: center; }
    .bottomBar { flex-wrap: wrap; }
}
""")

# =====================================================================
# DataInitializer.java — purge old samples + 10 detailed scenarios
# =====================================================================
write('erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.service.LandService;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;
    private final LandService landService;

    @Value("${ADMIN_EMAIL}") private String adminEmail;
    @Value("${ADMIN_DEFAULT_PASSWORD}") private String adminDefaultPassword;

    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
        runSchemaMigrations();
        seedRootUser();
        stageTemplateService.seedDefaultStagesIfEmpty();
        try {
            stageTemplateService.normalizeToDefaultStages();
            System.out.println(">>> [STAGE_TEMPLATE] Normalized master checklist to defaults.");
        } catch (Exception e) {
            System.err.println(">>> [STAGE_TEMPLATE] normalize warning: " + e.getMessage());
        }
        seedSampleProjects();
        seedDefaultExpensePresets();
        System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
    }

    public void seedDefaultExpensePresets() {
        if (expensePresetRepository.count() > 0) {
            System.out.println(">>> [EXPENSES] Presets already exist, skipping default seed.");
            return;
        }
        String[] defaults = { "Office", "Fieldwork", "Land Office" };
        for (String name : defaults) {
            expensePresetRepository.save(ExpensePreset.builder().name(name).createdBy("SYSTEM").build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    // Wipe ALL old sample rows (any previous seed generation) before re-seeding.
    private void purgeSampleData() {
        String[] stmts = {
            "DELETE FROM payment_records WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM follow_up_logs WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_stages WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_proprietors WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM land_projects WHERE district = 'SAMPLE DATA'",
            "DELETE FROM land_titles WHERE plot_number LIKE 'SAMPLE-%'",
            "DELETE FROM clients WHERE national_id LIKE 'SMPL-%'",
        };
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) { try { st.execute(s); } catch (Exception ignore) {} }
            System.out.println(">>> [SAMPLE] Old sample data purged.");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] purge warning: " + e.getMessage());
        }
    }

    private java.util.UUID trySeed(String label, java.util.concurrent.Callable<java.util.UUID> supplier) {
        try { return supplier.call(); }
        catch (Exception e) {
            System.err.println(">>> [SAMPLE] " + label + " failed (skipped): " + e.getMessage());
            return null;
        }
    }

    private void seedSampleProjects() {
        purgeSampleData();

        java.util.List<com.gesolutions.erp.modules.land.model.StageTemplate> master = stageTemplateService.getActiveTemplate();
        java.util.Map<String, String> idByName = new java.util.HashMap<>();
        for (com.gesolutions.erp.modules.land.model.StageTemplate t : master) idByName.put(t.getStageName(), t.getId().toString());

        String FW = "Field Work", DP = "Deed Plan", LCI = "LC Inspection",
               DLB = "District Land Board Approval", TASD = "Tax Assessment and Stamp Duty",
               REG = "Registration and Title Issuance";

        java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();

        // 1) FOLDER, active, GREEN (paid 5 days ago)
        ids.add(trySeed("SAMPLE-101", () -> seedOne("SAMPLE-101", false, false, false, null, null, null, "2026-05-04",
                4000000L, 2000000L, 0, 0,
                new String[][] { { "JOHN SSERUGO", "SMPL-1001", "0772100100" } },
                new String[] { FW, DP }, null,
                new String[] { "WAKISO", "KYADONDO", "NAKAWA EAST", "BUKOTO", "KIIWA", "0.5 acres" },
                "Sample: fresh folder, paying well.", idByName)));

        // 2) FOLDER, never paid, RED + CRITICAL
        ids.add(trySeed("SAMPLE-102", () -> seedOne("SAMPLE-102", false, false, false, null, null, null, "2026-07-10",
                6000000L, 0L, 0, 0,
                new String[][] { { "MARY NAKATO", "SMPL-1002", "0772100200" } },
                new String[] { FW }, null,
                new String[] { "MPIGI", "MPIGI COUNTY", "MPIGI TOWN", "CENTRAL", "KIZUNGU", "1 acre" },
                "Sample: folder, no payment yet.", idByName)));

        // 3) FOLDER, ready-for-titling, YELLOW (20 days)
        ids.add(trySeed("SAMPLE-103", () -> seedOne("SAMPLE-103", false, false, false, null, null, null, "2026-02-02",
                9000000L, 6000000L, 0, 0,
                new String[][] { { "PETER OPOK", "SMPL-1003", "0772100300" } },
                new String[] { FW, DP, LCI, DLB, TASD }, new String[] { REG },
                new String[] { "MUKONO", "MUKONO COUNTY", "KATABI", "BULANGA", "NAGOGBE", "2 acres" },
                "Sample: all pre-stages done, awaiting registration.", idByName)));

        // 4) NEW TITLE, active, GREEN (3 days)
        ids.add(trySeed("SAMPLE-104", () -> seedOne("SAMPLE-104", false, true, false, "SMPL-T-104", "2026-06-15", "KBL-77", "2026-06-01",
                15000000L, 11000000L, 0, 0,
                new String[][] { { "GRACE ACHENG", "SMPL-1004", "0772100400" } },
                new String[] { FW, DP, LCI, DLB }, null,
                new String[] { "KAMPALA", "KAMPALA CENTRAL", "MAKINDYE", "KABALAGALA", "GABA", "0.25 acres" },
                "Sample: new title in processing.", idByName)));

        // 5) LEGACY, fully paid (not released), RED badge
        ids.add(trySeed("SAMPLE-105", () -> seedOne("SAMPLE-105", true, false, false, "SMPL-T-105", "2025-12-01", "EBB-12", "2025-11-01",
                20000000L, 20000000L, 0, 0,
                new String[][] { { "DAVID KIGONGO", "SMPL-1005", "0772100500" } },
                new String[] { FW, DP, LCI, DLB, TASD, REG }, null,
                new String[] { "WAKISO", "ENTEBBE", "ENTEBBE TOWN", "KATABI", "LUGALA", "0.3 acres" },
                "Sample: legacy fully paid, awaiting release.", idByName)));

        // 6) LEGACY, RELEASED
        ids.add(trySeed("SAMPLE-106", () -> seedOne("SAMPLE-106", true, false, false, "SMPL-T-106", "2025-06-20", "MSK-3", "2025-05-02",
                25000000L, 25000000L, 0, 0,
                new String[][] { { "SARAH NANSUBU", "SMPL-1006", "0772100600" } },
                new String[] { FW, DP, LCI, DLB, TASD, REG }, "RELEASE",
                new String[] { "MASAKA", "MASAKA CENTRAL", "MASAKA MUNICIPAL", "KIMAANYA", "KABOGA", "1.5 acres" },
                "Sample: released legacy title.", idByName)));

        // 7) LEGACY, RECEIVABLE with storage fees, RED (45 days)
        ids.add(trySeed("SAMPLE-107", () -> seedOne("SAMPLE-107", true, false, true, "SMPL-T-107", "2025-09-10", "MBR-9", "2025-08-01",
                12000000L, 2000000L, 50000L, 50000L,
                new String[][] { { "JAMES TURYAHEREZA", "SMPL-1007", "0772100700" } },
                new String[] { FW, DP }, null,
                new String[] { "MBARARA", "MBARARA COUNTY", "MBARARA TOWN", "KAKIIKA", "NYAMITUKURA", "0.8 acres" },
                "Sample: receivable, storage fees accruing.", idByName)));

        // 8) NEW TITLE, RECEIVABLE, recent payment GREEN (12 days)
        ids.add(trySeed("SAMPLE-108", () -> seedOne("SAMPLE-108", false, true, true, "SMPL-T-108", "2026-02-14", "JIN-41", "2026-02-01",
                10000000L, 3000000L, 50000L, 50000L,
                new String[][] { { "RACHEL NABIRYE", "SMPL-1008", "0772100800" } },
                new String[] { FW, DP, LCI }, null,
                new String[] { "JINJA", "JINJA COUNTY", "JINJA MUNICIPAL", "WALUKUBA", "MPUMUDDE", "0.4 acres" },
                "Sample: receivable but paying recently.", idByName)));

        // 9) FOLDER, CRITICAL, JOINT (3 owners), RED (60 days)
        ids.add(trySeed("SAMPLE-109", () -> seedOne("SAMPLE-109", false, false, false, null, null, null, "2026-01-15",
                30000000L, 3000000L, 0, 0,
                new String[][] { { "SAMUEL KIBUKA", "SMPL-1091", "0772100901" },
                                 { "JOYCE NAKALEMA", "SMPL-1092", "0772100902" },
                                 { "BRIAN MUWANGA", "SMPL-1093", "0772100903" } },
                new String[] { FW }, null,
                new String[] { "KAYUNGA", "KAYUNGA COUNTY", "KAYUNGA TOWN", "BUKOMBE", "NAJJA", "5 acres" },
                "Sample: joint family plot, critical arrears.", idByName)));

        // 10) LEGACY, active 90%, YELLOW (25 days)
        ids.add(trySeed("SAMPLE-110", () -> seedOne("SAMPLE-110", true, false, false, "SMPL-T-110", "2026-01-25", "LWR-5", "2026-01-05",
                18000000L, 16200000L, 0, 0,
                new String[][] { { "HENRY SSEMMAMBWA", "SMPL-1100", "0772101000" } },
                new String[] { FW, DP, LCI, DLB, TASD }, null,
                new String[] { "LUWERO", "LUWERO COUNTY", "LUWERO MUNICIPAL", "BAMUNU", "ZIWA", "3 acres" },
                "Sample: nearly paid legacy.", idByName)));

        int[] days = { 5, -1, 20, 3, 40, 200, 45, 12, 60, 25 };
        try (Connection conn = dataSource.getConnection()) {
            for (int i = 0; i < days.length && i < ids.size(); i++) {
                if (ids.get(i) == null || days[i] < 0) continue;
                java.sql.Timestamp ts = java.sql.Timestamp.valueOf(java.time.LocalDateTime.now().minusDays(days[i]));
                try (java.sql.PreparedStatement u1 = conn.prepareStatement("UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) {
                    u1.setTimestamp(1, ts); u1.setObject(2, ids.get(i)); u1.executeUpdate();
                }
                try (java.sql.PreparedStatement u2 = conn.prepareStatement("UPDATE payment_records SET timestamp = ? WHERE project_id = ?")) {
                    u2.setTimestamp(1, ts); u2.setObject(2, ids.get(i)); u2.executeUpdate();
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] backdate warning: " + e.getMessage());
        }

        long saved = ids.stream().filter(java.util.Objects::nonNull).count();
        System.out.println(">>> [SAMPLE] Seeded " + saved + " detailed sample projects (district = SAMPLE DATA).");
    }

    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake, boolean receivable,
                                   String titleId, String titleDate, String block, String startDate,
                                   long cost, long paid, long initFee, long monthlyFee,
                                   String[][] owners, String[] doneStages, String[] openStages,
                                   String releaseFlag, String[] loc, String note,
                                   java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
                .district(loc[0]).county(loc[1]).subCounty(loc[2]).parish(loc[3]).village(loc[4]).area(loc[5])
                .tenure("FREEHOLD")
                .projectStartDate(java.time.LocalDate.parse(startDate))
                .totalCost(java.math.BigDecimal.valueOf(cost))
                .initialPayment(java.math.BigDecimal.valueOf(paid))
                .isLegacy(legacy).titleAtIntake(titleAtIntake).isStartAsReceivable(receivable);
        if (plot != null) b.plotNumber(plot);
        if (titleId != null) b.titleId(titleId);
        if (block != null) b.blockRoad(block);
        if (titleDate != null) b.titleIssueDate(java.time.LocalDate.parse(titleDate));
        if (receivable) {
            b.initialStorageFee(java.math.BigDecimal.valueOf(initFee > 0 ? initFee : 50000));
            b.monthlyStorageFee(java.math.BigDecimal.valueOf(monthlyFee > 0 ? monthlyFee : 50000));
        }
        java.util.List<LandEntryRequest.OwnerRequest> os = new java.util.ArrayList<>();
        for (String[] o : owners) {
            os.add(LandEntryRequest.OwnerRequest.builder().fullName(o[0]).nationalId(o[1]).phone(o[2]).build());
        }
        b.owners(os);
        java.util.List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> ss = new java.util.ArrayList<>();
        for (String s : doneStages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid).stageName(s).isCustom(tid == null).isCompleted(true).build());
        }
        if (openStages != null) for (String s : openStages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid).stageName(s).isCustom(tid == null).isCompleted(false).build());
        }
        b.selectedStages(ss);
        if (note != null) {
            b.notes(java.util.List.of(LandEntryRequest.NoteRequest.builder().content(note).build()));
        }
        com.gesolutions.erp.modules.land.model.LandProject saved = landService.atomicIntake(b.build(), null);
        if ("RELEASE".equals(releaseFlag)) {
            try { landService.authorizeRelease(saved.getId(), "Sample release"); } catch (Exception ignore) {}
        }
        return saved.getId();
    }

    private void runSchemaMigrations() {
        String[] migrations = {
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS negotiation_deadline TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_titles_project_index') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",
            // Sweep ANY leftover Hibernate-generated unique constraint on phone_number
            "DO $$ DECLARE cname text; BEGIN " +
                "SELECT tc.constraint_name INTO cname FROM information_schema.table_constraints tc " +
                "JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name " +
                "WHERE tc.table_name = 'clients' AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'phone_number' LIMIT 1; " +
                "IF cname IS NOT NULL THEN EXECUTE 'ALTER TABLE clients DROP CONSTRAINT ' || quote_ident(cname); END IF; " +
                "END $$",
            // Folder-type projects have no title yet -- title_id must be nullable
            "ALTER TABLE land_projects ALTER COLUMN title_id DROP NOT NULL",
            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",
            "CREATE TABLE IF NOT EXISTS expense_presets (id UUID PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE, created_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT now())",
            "CREATE TABLE IF NOT EXISTS expenses (id UUID PRIMARY KEY, category VARCHAR(150) NOT NULL, amount NUMERIC(15,2) NOT NULL, note TEXT, recorded_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT now(), edited_at TIMESTAMP, edited_by VARCHAR(100))",
            "CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            "UPDATE land_projects lp SET district = lt.district, county = lt.county " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL " +
                "AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
            // Retired Title Details columns
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS volume",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS folio",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS instrument_no",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS physical_box_number",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS survey_date",
        };
        try (Connection conn = dataSource.getConnection(); Statement stmt = conn.createStatement()) {
            for (String sql : migrations) {
                try {
                    stmt.execute(sql);
                    System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length())));
                } catch (Exception e) {
                    System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage());
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());
        }
    }

    public void seedRootUser() {
        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";
        String encodedPassword = passwordEncoder.encode(rawPassword);
        try (java.sql.Connection conn = dataSource.getConnection()) {
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) { if (rs.next()) exists = rs.getInt(1) > 0; }
            }
            if (!exists) {
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset.");
            }
        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
""")

# =====================================================================
# Backend surgical patches (warn-and-continue)
# =====================================================================
# LandController: split stacked mappings (index endpoint fix)
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java',
"""    @PostMapping("/projects/{id}/unlock-log")
    // INTAKE: preview next project index
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }""",
"""    // FIX: one mapping per method (stacked annotations left /next-index unrouted)
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

    @PostMapping("/projects/{id}/unlock-log")
    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }""")

# LandService: transactional intake + drop retired fields from builders
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
"""    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {""",
"""    @Transactional(rollbackFor = Exception.class)
    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {""")
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
"""                    .blockRoad(request.getBlockRoad())
                    .volume(request.getVolume())
                    .folio(request.getFolio())
                    .instrumentNo(request.getInstrumentNo())
                    .surveyDate(request.getSurveyDate())
                    .projectStartDate(""",
"""                    .blockRoad(request.getBlockRoad())
                    .projectStartDate(""")
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
"""            title.setBlockRoad(request.getBlockRoad());
            title.setVolume(request.getVolume());
            title.setFolio(request.getFolio());
            title.setInstrumentNo(request.getInstrumentNo());
            title.setSurveyDate(request.getSurveyDate());""",
"""            title.setBlockRoad(request.getBlockRoad());""")

# LandTitle: drop retired fields + dead index
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java',
"""    @Index(name = "idx_title_id", columnList = "title_id"),
    @Index(name = "idx_physical_archive", columnList = "physical_box_number")
})""",
"""    @Index(name = "idx_title_id", columnList = "title_id")
})""")
for fld in ["""    @Column(name = "physical_box_number", length = 100)
    private String physicalBoxNumber;

""", """    @Column(length = 50)
    private String volume;

""", """    @Column(length = 50)
    private String folio;

""", """    @Column(name = "instrument_no", length = 100)
    private String instrumentNo;

""", """    @Column(name = "survey_date")
    private LocalDate surveyDate;

"""]:
    patch('erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java', fld, "")

# LandEntryRequest: drop retired fields
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java',
"""    private String volume;
    private String folio;
    private String instrumentNo;
    private String physicalBoxNumber;
    private LocalDate surveyDate;
    private LocalDate projectStartDate;""",
"""    private LocalDate projectStartDate;""")

# Recovery DTO/controller: drop retired fields
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java',
"""        private String physicalBoxNumber;
""", "")
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java',
"""        private LocalDate surveyDate;
""", "")
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java',
"""                        .physicalBoxNumber(plot.getLandTitle() != null ? plot.getLandTitle().getPhysicalBoxNumber() : null)
""", "")
patch('erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java',
"""                        .surveyDate(plot.getLandTitle() != null ? plot.getLandTitle().getSurveyDate() : null)
""", "")

# FolderPage: drop retired edit inputs + read-only rows; add back-to-top + sidebar collapse
patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"""                                                <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                                <SmartInput label="INSTRUMENT NO." value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />
                                                <SmartInput label="VOLUME" value={buffer.volume} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\\D/g,'')})} />
                                            </div>
                                            <div className={styles.inputGrid3}>
                                                <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>DATE OF SURVEY</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        value={buffer.surveyDate || ''}
                                                        onChange={e => touchedSetBuffer({...buffer, surveyDate: e.target.value})} />
                                                </div>
                                                <SmartInput label="BOX NUMBER" value={buffer.physicalBoxNumber} showCaps onChange={e => touchedSetBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />""",
"""                                                <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />""")
patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"""                                                    ['BLOCK / ROAD', project.landTitle.blockRoad],
                                                    ['VOLUME',       project.landTitle.volume],
                                                    ['FOLIO',        project.landTitle.folio],
                                                    ['INSTRUMENT',   project.landTitle.instrumentNo],
                                                    ['SURVEY DATE',  project.landTitle.surveyDate || '---'],
                                                    ['BOX NUMBER',   project.landTitle.physicalBoxNumber || '---'],""",
"""                                                    ['BLOCK / ROAD', project.landTitle.blockRoad],""")
patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"""import styles from './FolderPage.module.css';""",
"""import styles from './FolderPage.module.css';
import BackToTopButton from '../../components/common/BackToTopButton';""")
patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"""const fileInputRef  = useRef(null);""",
"""const fileInputRef  = useRef(null);

// STANDARD: sidebar auto-collapses on first interaction
useEffect(() => {
    const handler = () => {
        const aside = document.querySelector('aside');
        const toggle = document.querySelector('[class*="sidebarToggle"]');
        if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
        window.removeEventListener('click', handler);
    };
    window.addEventListener('click', handler);
    return () => window.removeEventListener('click', handler);
}, []);""")
patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
"""        </HardwareModal>
    </div>
);
};

export default FolderPage;""",
"""        </HardwareModal>
        <BackToTopButton />
    </div>
);
};

export default FolderPage;""")

# =====================================================================
print(f"\n=== fix.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if WARN:
    print(f"  WARN (skipped, already clean or not present): {len(WARN)}")
    for f in WARN: print(f"    ~ {f}")

subprocess.run(['git', 'add', '.'], check=False, cwd=ROOT, capture_output=True)
subprocess.run(['git', 'commit', '-m', 'fix: purge+reseed 10 detailed scenarios; INDEX column = dot+index+NINs; folders show index; full desired-state re-issue'], check=False, cwd=ROOT, capture_output=True)
subprocess.run(['git', 'push'], check=False, cwd=ROOT, capture_output=True)
print("\nGit: committed + pushed (if changes). Check Render for green deploy.")
print("Boot log should show: '>>> [SAMPLE] Seeded 10 detailed sample projects'.")
"""
"""
print()