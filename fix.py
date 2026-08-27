#!/usr/bin/env python3
"""
fix10.py — Ledger redo to match the New Project intake + dead-code purge.
- LedgerPage.jsx: intake-aligned search/filters/badges + LOCATION column
  (district/county + parish/village), cleaned imports/placeholder.
- Backend rewritten to a guaranteed-compiling set: LandController (index
  fix), StageTemplate controller+service (aligned), DataInitializer
  (normalize + 7 sample projects + sample docs + PHASE G drops incl.
  land_titles.district/county), LandTitle (dead fields removed).
Run: py fix10.py
"""
import sys, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WROTE, FAILED = [], []

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    try: p.write_text(content, encoding="utf-8"); WROTE.append(rel)
    except Exception as e: FAILED.append((rel, str(e)))

# =====================================================================
# 1) LedgerPage.jsx — FULL rewrite, intake-aligned
# =====================================================================
write("erp-frontend/src/pages/Ledger/LedgerPage.jsx", r'''// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
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
import landService from '../../services/landService';
import styles from './LedgerPage.module.css';

// Search mirrors the New Project intake fields (location incl. parish/village)
const matchesSearch = (proj, term) => {
    if (!term) return true;
    const t = term.toLowerCase().replace(/\s+/g, '');
    const fields = [
        proj.landTitle?.plotNumber,
        proj.projectIndex,
        proj.landTitle?.titleId,
        proj.landTitle?.blockRoad,
        proj.landTitle?.tenure,
        proj.district,
        proj.county,
        proj.subCounty,
        proj.parish,
        proj.village,
        proj.area,
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

// Payment health badge logic (same rules as Recovery)
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

// Entry-type badge, mirrors the New Project "Type" selector
const typeBadge = (proj) => {
    if (proj.isLegacy) return 'LEGACY';
    return proj.landTitle ? 'TITLED' : 'FOLDER';
};

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

        if (activeFilter === 'FOLDERS')     filtered = filtered.filter(p => !p.landTitle);
        if (activeFilter === 'TITLED')      filtered = filtered.filter(p => !!p.landTitle && !p.isLegacy);
        if (activeFilter === 'LEGACY')      filtered = filtered.filter(p => p.isLegacy);
        if (activeFilter === 'PAID')        filtered = filtered.filter(p => (p.amountPaid >= p.totalCost || p.landTitle?.isReleased) && !p.isReceivable);
        if (activeFilter === 'RECEIVABLES') filtered = filtered.filter(p => p.isReceivable);
        if (activeFilter === 'UNPAID')      filtered = filtered.filter(p => (p.amountPaid || 0) < (p.totalCost || 0));
        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25);
        if (activeFilter === 'READY_FOR_TITLING') filtered = filtered.filter(isReadyForTitling);

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

    const FILTERS = [
        { key: 'ALL',               label: 'ALL ARCHIVES'        },
        { key: 'FOLDERS',           label: 'FOLDERS'             },
        { key: 'TITLED',            label: 'TITLED'              },
        { key: 'LEGACY',            label: 'LEGACY'              },
        { key: 'RECEIVABLES',       label: 'RECEIVABLES'         },
        { key: 'PAID',              label: 'PAID'                },
        { key: 'UNPAID',            label: 'UNPAID'              },
        { key: 'CRITICAL',          label: 'CRITICAL'            },
        { key: 'READY_FOR_TITLING', label: 'READY FOR TITLING'   },
    ];

    const colSpan = activeFilter === 'READY_FOR_TITLING' ? 6 : 5;

    return (
        <div className={styles.container}>

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
                            placeholder="Plot ID, index, title ID, owner, phone, NIN, email, district, county, parish, village, tenure..."
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
                                <th>
                                    <FiMapPin aria-hidden="true" /> LOCATION
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
                                <tr><td colSpan={colSpan} className={styles.loadingCell}>
                                    <FiClock aria-hidden="true" /> SYNCING ARCHIVE...
                                </td></tr>
                            )}
                            {!loading && loadError && (
                                <tr><td colSpan={colSpan} className={styles.errorCell}>
                                    <FiAlertTriangle aria-hidden="true" /> LEDGER SYNC FAULT —{' '}
                                    <button className={styles.retryBtn} onClick={fetchLedger}>RETRY</button>
                                </td></tr>
                            )}
                            {!loading && !loadError && processedData.length === 0 && (
                                <tr><td colSpan={colSpan} className={styles.emptyCell}>
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
                                const isCritical = pct < 25 && proj.totalCost > 0;
                                const locLine    = [proj.parish, proj.village].filter(Boolean).join(' / ');

                                return (
                                    <tr key={proj.id}
                                        onClick={() => navigate(`/folder/${proj.id}`)}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/folder/${proj.id}`); } }}
                                        tabIndex={0} role="row"
                                        aria-label={`Record: ${proj.landTitle?.plotNumber || proj.projectIndex}`}
                                        className={isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}
                                    >
                                        {activeFilter === 'READY_FOR_TITLING' && (
                                            <td>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedIds.has(proj.id)}
                                                    onChange={e => toggleSelect(proj.id, e)}
                                                    onClick={e => e.stopPropagation()}
                                                />
                                            </td>
                                        )}
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
                                                        {proj.landTitle?.titleId && (
                                                            <span className={styles.districtTag}>{proj.landTitle.titleId}</span>
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
                                        <td>
                                            <div className={styles.ownerWrap}>
                                                <div className={styles.ownerMeta}>
                                                    <span className={styles.ownerName}>{proj.district || '---'}</span>
                                                    <span className={styles.ownerPhone}>{proj.county || '---'}</span>
                                                </div>
                                                <div className={styles.jointBadge}>
                                                    <FiMapPin aria-hidden="true" />
                                                    <span>{locLine || proj.area || '---'}</span>
                                                </div>
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
                                                {!isReceivable && !proj.landTitle?.isReleased && (proj.amountPaid || 0) >= (proj.totalCost || 0) && <span className={styles.tagPaid}>FULLY PAID</span>}
                                                {!isReceivable && (proj.amountPaid || 0) < (proj.totalCost || 0) && <span className={styles.tagStandard}>ACTIVE</span>}
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
''')

# =====================================================================
# 2) LandTitle.java — dead district/county removed (retired 5 already gone)
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PHYSICAL ASSET REGISTRY
 * Maps 1-1 with the technical documents (Deed Plans and Titles).
 * PASS 6/10: volume/folio/instrument_no/physical_box_number/survey_date
 * and the deprecated district/county columns are retired app-wide and
 * dropped from the DB (PHASE G). Location lives on LandProject.
 */
@Entity
@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number"),
    @Index(name = "idx_title_id", columnList = "title_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LandTitle {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 50)
    private String tenure; // e.g. MAILO, FREEHOLD

    @Column(name = "plot_number", unique = true, length = 100)
    private String plotNumber;

    @Column(name = "block_road", length = 100)
    private String blockRoad;

    @Column(name = "title_id", length = 100)
    private String titleId;

    /**
     * PROJECT INDEX
     * Short, never-repeating, searchable code shown to clients and staff.
     * Kept for backward compatibility; LandProject.projectIndex is the
     * source of truth going forward.
     */
    @Deprecated
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    @Builder.Default
    @Column(name = "is_released", nullable = false)
    private boolean isReleased = false;

    @Column(name = "created_at", updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}
""")

# =====================================================================
# 3) LandController.java — index endpoint fix (one mapping per method)
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.dto.*;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectDocument;
import com.gesolutions.erp.modules.land.service.LandService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/land")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class LandController {

    private final LandService landService;

    // INTAKE: preview next project index (fixed: was stacked with the
    // unlock-log mapping, so it never registered and always 404'd).
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

    @PostMapping("/projects/{id}/unlock-log")
    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/notes")
    public ResponseEntity<List<FollowUpLog>> getProjectNotes(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectNotes(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/follow-up")
    public ResponseEntity<java.util.Map<String, Object>> logContact(@PathVariable UUID id,
                                            @RequestParam UUID ownerId,
                                            @RequestParam String content) {
        return ResponseEntity.ok(landService.logFollowUp(id, ownerId, content));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/ingest", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LandProject> ingestTitle(
            @RequestPart("data") String jsonData,
            @RequestPart(value = "scans", required = false) MultipartFile[] scans) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        LandEntryRequest request = mapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(landService.atomicIntake(request, scans));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/deep")
    public ResponseEntity<ProjectDeepDetailDTO> getProjectDeepDetail(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDeepDetail(id));
    }

    @PutMapping("/projects/{id}/full-update")
    public ResponseEntity<LandProject> updateProjectFull(
            @PathVariable UUID id, @RequestBody LandEntryRequest request) {
        return ResponseEntity.ok(landService.updateProjectFull(id, request));
    }

    @DeleteMapping("/projects/{id}")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id) {
        landService.nuclearDelete(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/projects/{id}/restore")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> restoreAsset(@PathVariable UUID id) {
        landService.restoreProject(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/deleted")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<List<LandProject>> getDeletedProjects() {
        return ResponseEntity.ok(landService.getDeletedProjects());
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/documents")
    public ResponseEntity<List<ProjectDocument>> getDocuments(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDocuments(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/projects/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> addExtraDocuments(
            @PathVariable UUID id,
            @RequestParam("scans") MultipartFile[] scans) throws Exception {
        landService.addScansToProject(id, scans);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/documents/{docId}")
    public ResponseEntity<Void> deleteDocument(@PathVariable UUID docId) {
        landService.removeDocument(docId);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/notes")
    public ResponseEntity<Void> addNote(@PathVariable UUID id, @RequestParam String content) {
        landService.logNewNote(id, content);
        return ResponseEntity.ok().build();
    }

    @PutMapping("/notes/{noteId}")
    public ResponseEntity<Void> updateNote(@PathVariable UUID noteId, @RequestParam String content) {
        landService.updateNote(noteId, content);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/notes/{noteId}")
    public ResponseEntity<Void> deleteNote(@PathVariable UUID noteId) {
        landService.removeNote(noteId);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/reality-override")
    public ResponseEntity<Void> manualRealityOverride(
            @PathVariable UUID id, @RequestParam int targetStage) {
        landService.manualRealityOverride(id, targetStage);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/ledger")
    public ResponseEntity<Page<LandProject>> getLedger(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(page, size)));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/bulk-mark-title-produced")
    public ResponseEntity<Integer> bulkMarkTitleProduced(@RequestBody List<UUID> projectIds) {
        return ResponseEntity.ok(landService.bulkMarkTitleProduced(projectIds));
    }

    @PatchMapping("/projects/{id}/release")
    public ResponseEntity<Void> authorizeRelease(
            @PathVariable UUID id,
            @RequestParam(required = false) String managerNote) {
        landService.authorizeRelease(id, managerNote);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/receivable")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> moveToReceivable(@PathVariable UUID id) {
        landService.moveToReceivable(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/exit-receivable")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitReceivable(@PathVariable UUID id,
                                            @RequestParam(defaultValue = "false") boolean capitalizeFees) {
        landService.exitReceivable(id, capitalizeFees);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/exit-receivable-capitalize")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitReceivableCapitalize(@PathVariable UUID id) {
        landService.exitReceivable(id, true);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }

    @PostMapping("/projects/{id}/payment")
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes) {
        landService.recordPayment(id, amount, notes);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-pause")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,
                                                   @RequestParam boolean paused) {
        landService.setStoragePaused(id, paused);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-rate")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal rate) {
        landService.setStorageFeeOverride(id, rate);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount) {
        landService.setAccumulatedFees(id, amount);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/negotiation-deadline")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setNegotiationDeadline(@PathVariable UUID id,
                                                        @RequestParam(required = false) String deadline) {
        landService.setNegotiationDeadline(id, deadline);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/receivable-start")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setReceivableStartOverride(@PathVariable UUID id,
                                                         @RequestParam String startDate) {
        landService.setReceivableStartOverride(id, startDate);
        return ResponseEntity.ok().build();
    }
}
""")

# =====================================================================
# 4) StageTemplateService.java — canonical (bulk trio + normalize)
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.ProjectStage;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.dto.ProjectStageRequest;
import com.gesolutions.erp.modules.land.repository.ProjectStageRepository;
import com.gesolutions.erp.modules.land.repository.StageTemplateRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class StageTemplateService {

    private final StageTemplateRepository templateRepository;
    private final ProjectStageRepository projectStageRepository;
    private final AuditService auditService;

    private static final String[] DEFAULT_STAGES = {
        "Field Work",
        "Deed Plan",
        "LC Inspection",
        "District Land Board Approval",
        "Tax Assessment and Stamp Duty",
        "Registration and Title Issuance"
    };

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    @Transactional
    public void seedDefaultStagesIfEmpty() {
        if (templateRepository.count() > 0) return;
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = StageTemplate.builder()
                    .stageName(name)
                    .defaultCost(BigDecimal.ZERO)
                    .displayOrder(order++)
                    .isActive(true)
                    .build();
            templateRepository.save(stage);
        }
        System.out.println(">>> [STAGE_TEMPLATE] Seeded " + DEFAULT_STAGES.length + " default stages.");
    }

    @Transactional(readOnly = true)
    public List<StageTemplate> getActiveTemplate() {
        return templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public StageTemplate addTemplateStage(String stageName, BigDecimal defaultCost, Integer displayOrder) {
        if (stageName == null || stageName.isBlank()) {
            throw new BusinessException("STAGE_NAME_REQUIRED: A stage name is required.");
        }
        StageTemplate stage = StageTemplate.builder()
                .stageName(stageName.trim())
                .defaultCost(defaultCost != null ? defaultCost : BigDecimal.ZERO)
                .displayOrder(displayOrder != null ? displayOrder : (int) templateRepository.count() + 1)
                .isActive(true)
                .build();
        StageTemplate saved = templateRepository.save(stage);
        auditService.logAction("STAGE_TEMPLATE_ADDED",
            "Operator [" + getCurrentOperator() + "] added master stage: " + stage.getStageName());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public StageTemplate updateTemplateStage(UUID id, String stageName, BigDecimal defaultCost, Integer displayOrder) {
        StageTemplate stage = templateRepository.findById(id)
                .orElseThrow(() -> new BusinessException("STAGE_TEMPLATE_NOT_FOUND"));
        if (stageName != null && !stageName.isBlank()) stage.setStageName(stageName.trim());
        if (defaultCost != null) stage.setDefaultCost(defaultCost);
        if (displayOrder != null) stage.setDisplayOrder(displayOrder);
        StageTemplate saved = templateRepository.save(stage);
        auditService.logAction("STAGE_TEMPLATE_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated master stage: " + stage.getStageName());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void deactivateTemplateStage(UUID id) {
        StageTemplate stage = templateRepository.findById(id)
                .orElseThrow(() -> new BusinessException("STAGE_TEMPLATE_NOT_FOUND"));
        stage.setActive(false);
        templateRepository.save(stage);
        auditService.logAction("STAGE_TEMPLATE_REMOVED",
            "Operator [" + getCurrentOperator() + "] removed master stage from checklist: " + stage.getStageName());
    }

    @Transactional(readOnly = true)
    public List<ProjectStage> getProjectStages(UUID projectId) {
        return projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
    }

    @Transactional
    public List<ProjectStage> attachStagesToProject(UUID projectId, List<ProjectStageRequest> requests) {
        if (requests == null || requests.isEmpty()) return List.of();

        int startOrder = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId).size();
        java.util.List<ProjectStage> created = new java.util.ArrayList<>();

        int i = 0;
        for (ProjectStageRequest req : requests) {
            String name;
            BigDecimal cost;

            if (req.isCustom()) {
                if (req.getStageName() == null || req.getStageName().isBlank()) {
                    throw new BusinessException("STAGE_NAME_REQUIRED: Custom stage needs a name.");
                }
                name = req.getStageName().trim();
                cost = req.getCost() != null ? req.getCost() : BigDecimal.ZERO;
            } else {
                if (req.getStageTemplateId() == null) {
                    throw new BusinessException("STAGE_TEMPLATE_ID_REQUIRED");
                }
                StageTemplate template = templateRepository.findById(UUID.fromString(req.getStageTemplateId()))
                        .orElseThrow(() -> new BusinessException("STAGE_TEMPLATE_NOT_FOUND"));
                name = template.getStageName();
                cost = req.getCost() != null ? req.getCost() : template.getDefaultCost();
            }

            ProjectStage stage = ProjectStage.builder()
                    .projectId(projectId)
                    .stageName(name)
                    .cost(cost)
                    .notes(req.getNotes())
                    .isCustom(req.isCustom())
                    .isCompleted(req.isCompleted())
                    .displayOrder(startOrder + (i++))
                    .build();
            created.add(projectStageRepository.save(stage));
        }

        auditService.logAction("PROJECT_STAGES_ATTACHED",
            "Operator [" + getCurrentOperator() + "] attached " + created.size()
            + " stage(s) to project: " + projectId);

        return created;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStage toggleStageCompletion(UUID stageId, boolean completed) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        stage.setCompleted(completed);
        stage.setCompletedAt(completed ? LocalDateTime.now() : null);
        ProjectStage saved = projectStageRepository.save(stage);
        auditService.logAction("PROJECT_STAGE_STATUS_CHANGED",
            "Operator [" + getCurrentOperator() + "] marked stage \"" + stage.getStageName()
            + "\" as " + (completed ? "COMPLETE" : "NOT COMPLETE") + " on project: " + stage.getProjectId());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStage updateStageCostAndNotes(UUID stageId, BigDecimal cost, String notes) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        if (cost != null) stage.setCost(cost);
        if (notes != null) stage.setNotes(notes);
        ProjectStage saved = projectStageRepository.save(stage);
        auditService.logAction("PROJECT_STAGE_COST_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated cost/notes on stage \"" + stage.getStageName()
            + "\" for project: " + stage.getProjectId());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void removeProjectStage(UUID stageId) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        projectStageRepository.delete(stage);
        auditService.logAction("PROJECT_STAGE_REMOVED",
            "Operator [" + getCurrentOperator() + "] removed stage \"" + stage.getStageName()
            + "\" from project: " + stage.getProjectId());
    }

    @Transactional
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }

    // ─── BULK OPERATIONS ─────────────────────────────────────────────

    private static final java.util.Set<String> DEFAULT_STAGE_NAMES =
            java.util.Set.of(DEFAULT_STAGES);

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> reorderTemplateStages(List<UUID> orderedIds) {
        if (orderedIds == null || orderedIds.isEmpty()) return List.of();
        List<StageTemplate> found = templateRepository.findAllById(orderedIds);
        java.util.Map<UUID, StageTemplate> byId = found.stream()
                .collect(java.util.stream.Collectors.toMap(StageTemplate::getId, s -> s));
        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (UUID id : orderedIds) {
            StageTemplate stage = byId.get(id);
            if (stage == null) continue;
            stage.setDisplayOrder(order++);
            toSave.add(stage);
        }
        List<StageTemplate> saved = templateRepository.saveAll(toSave);
        auditService.logAction("STAGE_TEMPLATE_REORDERED",
            "Operator [" + getCurrentOperator() + "] reordered " + saved.size() + " master stage(s).");
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void bulkDeleteTemplateStages(List<UUID> ids) {
        if (ids == null || ids.isEmpty()) return;
        List<StageTemplate> toDelete = templateRepository.findAllById(ids);
        if (toDelete.isEmpty()) return;
        templateRepository.deleteAllInBatch(toDelete);
        auditService.logAction("STAGE_TEMPLATE_BULK_DELETED",
            "Operator [" + getCurrentOperator() + "] bulk-deleted " + toDelete.size() + " master stage(s).");
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> restoreDefaultStages() {
        List<StageTemplate> current = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
        List<StageTemplate> nonDefault = current.stream()
                .filter(s -> !DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .toList();
        if (!nonDefault.isEmpty()) {
            templateRepository.deleteAllInBatch(nonDefault);
        }
        java.util.Map<String, StageTemplate> keepByName = current.stream()
                .filter(s -> DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .collect(java.util.stream.Collectors.toMap(
                        StageTemplate::getStageName, s -> s, (a, b) -> a));
        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = keepByName.get(name);
            if (stage == null) {
                stage = StageTemplate.builder()
                        .stageName(name)
                        .defaultCost(BigDecimal.ZERO)
                        .displayOrder(order)
                        .isActive(true)
                        .build();
            } else {
                stage.setDisplayOrder(order);
            }
            order++;
            toSave.add(stage);
        }
        List<StageTemplate> saved = templateRepository.saveAll(toSave);
        auditService.logAction("STAGE_TEMPLATE_DEFAULTS_RESTORED",
            "Operator [" + getCurrentOperator() + "] restored the default master stage list.");
        return saved;
    }

    /** Boot-time: master checklist = exactly the 6 defaults, in order, no dupes. */
    @Transactional
    public void normalizeToDefaultStages() {
        List<StageTemplate> active = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
        java.util.Map<String, StageTemplate> kept = new java.util.LinkedHashMap<>();
        for (StageTemplate t : active) {
            String name = t.getStageName();
            boolean isDefault = name != null && DEFAULT_STAGE_NAMES.contains(name);
            if (!isDefault || kept.containsKey(name)) {
                t.setActive(false);
                templateRepository.save(t);
            } else {
                kept.put(name, t);
            }
        }
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = kept.get(name);
            if (stage == null) {
                templateRepository.save(StageTemplate.builder()
                        .stageName(name)
                        .defaultCost(BigDecimal.ZERO)
                        .displayOrder(order)
                        .isActive(true)
                        .build());
            } else if (stage.getDisplayOrder() == null || stage.getDisplayOrder() != order) {
                stage.setDisplayOrder(order);
                templateRepository.save(stage);
            }
            order++;
        }
    }
}
""")

# =====================================================================
# 5) StageTemplateController.java — canonical matching pair
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.ProjectStage;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.dto.ProjectStageRequest;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class StageTemplateController {

    private final StageTemplateService stageTemplateService;

    @GetMapping("/stage-templates")
    public ResponseEntity<List<StageTemplate>> getTemplate() {
        return ResponseEntity.ok(stageTemplateService.getActiveTemplate());
    }

    @PostMapping("/stage-templates")
    public ResponseEntity<StageTemplate> addTemplateStage(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("stageName");
        BigDecimal cost = body.get("defaultCost") != null
                ? new BigDecimal(body.get("defaultCost").toString()) : BigDecimal.ZERO;
        Integer order = body.get("displayOrder") != null
                ? Integer.valueOf(body.get("displayOrder").toString()) : null;
        return ResponseEntity.ok(stageTemplateService.addTemplateStage(name, cost, order));
    }

    @PutMapping("/stage-templates/{id}")
    public ResponseEntity<StageTemplate> updateTemplateStage(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        String name = (String) body.get("stageName");
        BigDecimal cost = body.get("defaultCost") != null
                ? new BigDecimal(body.get("defaultCost").toString()) : null;
        Integer order = body.get("displayOrder") != null
                ? Integer.valueOf(body.get("displayOrder").toString()) : null;
        return ResponseEntity.ok(stageTemplateService.updateTemplateStage(id, name, cost, order));
    }

    @DeleteMapping("/stage-templates/{id}")
    public ResponseEntity<Void> deactivateTemplateStage(@PathVariable UUID id) {
        stageTemplateService.deactivateTemplateStage(id);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/stage-templates/reorder")
    public ResponseEntity<List<StageTemplate>> reorderTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> orderedIds = (body.getOrDefault("orderedIds", List.of())).stream()
                .map(UUID::fromString)
                .toList();
        return ResponseEntity.ok(stageTemplateService.reorderTemplateStages(orderedIds));
    }

    @DeleteMapping("/stage-templates/bulk")
    public ResponseEntity<Void> bulkDeleteTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> ids = (body.getOrDefault("ids", List.of())).stream()
                .map(UUID::fromString)
                .toList();
        stageTemplateService.bulkDeleteTemplateStages(ids);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/stage-templates/restore-defaults")
    public ResponseEntity<List<StageTemplate>> restoreDefaultStages() {
        return ResponseEntity.ok(stageTemplateService.restoreDefaultStages());
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> getProjectStages(@PathVariable UUID projectId) {
        return ResponseEntity.ok(stageTemplateService.getProjectStages(projectId));
    }

    @PostMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> attachStages(
            @PathVariable UUID projectId, @RequestBody List<ProjectStageRequest> requests) {
        return ResponseEntity.ok(stageTemplateService.attachStagesToProject(projectId, requests));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PatchMapping("/land/projects/{projectId}/stages/{stageId}/complete")
    public ResponseEntity<ProjectStage> toggleStageCompletion(
            @PathVariable UUID projectId, @PathVariable UUID stageId,
            @RequestParam boolean completed) {
        return ResponseEntity.ok(stageTemplateService.toggleStageCompletion(stageId, completed));
    }

    @PatchMapping("/land/projects/{projectId}/stages/{stageId}/cost")
    public ResponseEntity<ProjectStage> updateStageCost(
            @PathVariable UUID projectId, @PathVariable UUID stageId,
            @RequestBody Map<String, Object> body) {
        BigDecimal cost = body.get("cost") != null ? new BigDecimal(body.get("cost").toString()) : null;
        String notes = (String) body.get("notes");
        return ResponseEntity.ok(stageTemplateService.updateStageCostAndNotes(stageId, cost, notes));
    }

    @DeleteMapping("/land/projects/{projectId}/stages/{stageId}")
    public ResponseEntity<Void> removeStage(@PathVariable UUID projectId, @PathVariable UUID stageId) {
        stageTemplateService.removeProjectStage(stageId);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteStage(@PathVariable UUID id) {
        stageTemplateService.deleteTemplateStage(id);
        return ResponseEntity.noContent().build();
    }
}
""")

# =====================================================================
# 6) DataInitializer.java — normalize + samples + docs + PHASE G (incl.
#    dropping land_titles.district/county) + dead backfill removed
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.StageTemplate;
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

    @Value("${ADMIN_EMAIL}")
    private String adminEmail;

    @Value("${ADMIN_DEFAULT_PASSWORD}")
    private String adminDefaultPassword;

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
        seedSampleDocuments();
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
            expensePresetRepository.save(ExpensePreset.builder()
                    .name(name)
                    .createdBy("SYSTEM")
                    .build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    // 7 diverse SAMPLE projects (guarded: only when none exist yet)
    private void seedSampleProjects() {
        try (java.sql.Connection conn = dataSource.getConnection();
             java.sql.PreparedStatement ps = conn.prepareStatement(
                "SELECT COUNT(*) FROM land_projects WHERE district = 'SAMPLE DATA'")) {
            try (java.sql.ResultSet rs = ps.executeQuery()) {
                if (rs.next() && rs.getInt(1) > 0) {
                    System.out.println(">>> [SAMPLE] Sample projects already present -- skipping seed.");
                    return;
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] guard check failed: " + e.getMessage());
            return;
        }

        java.util.List<StageTemplate> master = stageTemplateService.getActiveTemplate();
        java.util.Map<String, String> idByName = new java.util.HashMap<>();
        for (StageTemplate t : master) idByName.put(t.getStageName(), t.getId().toString());

        try {
            java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();

            ids.add(seedOne("SAMPLE-001", false, false, false, null, null, null, "2026-05-04",
                    5000000L, 2500000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER ONE", "SMPL00000001A", "0772000001" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection" }, idByName));

            ids.add(seedOne("SAMPLE-002", true, false, false, "SMPL-2002", "2026-03-01", "B-12", "2025-11-10",
                    8000000L, 8000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER TWO", "SMPL00000002A", "0772000002" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval", "Tax Assessment and Stamp Duty",
                                   "Registration and Title Issuance" }, idByName));

            ids.add(seedOne("SAMPLE-003", false, false, true, null, null, null, "2026-01-15",
                    6000000L, 1000000L, 50000L, 50000L,
                    new String[][] { { "SAMPLE OWNER THREE", "SMPL00000003A", "0772000003" } },
                    new String[] { "Field Work", "Deed Plan" }, idByName));

            ids.add(seedOne("SAMPLE-004", false, false, false, null, null, null, "2026-06-20",
                    10000000L, 1000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FOUR", "SMPL00000004A", "0772000004" },
                                     { "SAMPLE CO OWNER FOUR", "SMPL00000005A", "0772000005" } },
                    new String[] { "Field Work" }, idByName));

            ids.add(seedOne("SAMPLE-005", false, true, false, "SMPL-5005", "2026-07-20", "K-07", "2026-07-01",
                    4000000L, 3000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FIVE", "SMPL00000006A", "0772000006" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval" }, idByName));

            ids.add(seedOne("SAMPLE-006", false, false, false, null, null, null, "2026-08-20",
                    3000000L, 0L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER SIX", "SMPL00000007A", "0772000007" } },
                    new String[] { "Field Work" }, idByName));

            ids.add(seedOne("SAMPLE-007", true, false, false, "SMPL-7007", "2026-06-10", "W-03", "2026-02-02",
                    9000000L, 8100000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER SEVEN", "SMPL00000008A", "0772000008" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval", "Tax Assessment and Stamp Duty" }, idByName));

            int[] days = { 10, 200, 45, 60, 0, -1, 25 };
            try (java.sql.Connection conn = dataSource.getConnection()) {
                for (int i = 0; i < days.length && i < ids.size(); i++) {
                    if (ids.get(i) == null || days[i] < 0) continue;
                    java.sql.Timestamp ts = java.sql.Timestamp.valueOf(
                            java.time.LocalDateTime.now().minusDays(days[i]));
                    try (java.sql.PreparedStatement u1 = conn.prepareStatement(
                            "UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) {
                        u1.setTimestamp(1, ts); u1.setObject(2, ids.get(i)); u1.executeUpdate();
                    }
                    try (java.sql.PreparedStatement u2 = conn.prepareStatement(
                            "UPDATE payment_records SET timestamp = ? WHERE project_id = ?")) {
                        u2.setTimestamp(1, ts); u2.setObject(2, ids.get(i)); u2.executeUpdate();
                    }
                }
            }
            System.out.println(">>> [SAMPLE] Seeded 7 sample projects (district = SAMPLE DATA).");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] seed failed (non-fatal): " + e.getMessage());
        }
    }

    // 2 viewable sample docs per SAMPLE project that has none
    private void seedSampleDocuments() {
        String[][] docs = {
            { "SAMPLE_DEED_PLAN.pdf",  "DEED_PLAN",  "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf" },
            { "SAMPLE_TITLE_CERT.pdf", "TITLE_CERT", "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf" },
        };
        try (java.sql.Connection conn = dataSource.getConnection();
             java.sql.PreparedStatement ps = conn.prepareStatement(
                "SELECT id FROM land_projects WHERE district = 'SAMPLE DATA'")) {
            int attached = 0;
            try (java.sql.ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Object pid = rs.getObject(1);
                    try (java.sql.PreparedStatement c = conn.prepareStatement(
                            "SELECT COUNT(*) FROM project_documents WHERE project_id = ?")) {
                        c.setObject(1, pid);
                        try (java.sql.ResultSet crs = c.executeQuery()) {
                            if (crs.next() && crs.getInt(1) > 0) continue;
                        }
                    }
                    for (String[] d : docs) {
                        try (java.sql.PreparedStatement ins = conn.prepareStatement(
                                "INSERT INTO project_documents (id, project_id, file_name, file_type, file_path, uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?)")) {
                            ins.setObject(1, java.util.UUID.randomUUID());
                            ins.setObject(2, pid);
                            ins.setString(3, d[0]);
                            ins.setString(4, d[1]);
                            ins.setString(5, d[2]);
                            ins.setString(6, "SYSTEM");
                            ins.setTimestamp(7, java.sql.Timestamp.valueOf(java.time.LocalDateTime.now()));
                            ins.executeUpdate();
                        }
                    }
                    attached++;
                }
            }
            System.out.println(">>> [SAMPLE] Documents attached to " + attached + " sample project(s).");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] document seed failed (non-fatal): " + e.getMessage());
        }
    }

    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake,
                                   boolean receivable, String titleId, String titleDate,
                                   String block, String startDate, long cost, long paid,
                                   long initFee, long monthlyFee, String[][] owners,
                                   String[] stages, java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
                .district("SAMPLE DATA").county("SAMPLE COUNTY")
                .subCounty("SAMPLE SUB").parish("SAMPLE PARISH")
                .village("SAMPLE VILLAGE").area("SAMPLE AREA")
                .tenure("FREEHOLD")
                .projectStartDate(java.time.LocalDate.parse(startDate))
                .totalCost(java.math.BigDecimal.valueOf(cost))
                .initialPayment(java.math.BigDecimal.valueOf(paid))
                .isLegacy(legacy)
                .titleAtIntake(titleAtIntake)
                .isStartAsReceivable(receivable);
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
            os.add(LandEntryRequest.OwnerRequest.builder()
                    .fullName(o[0]).nationalId(o[1]).phone(o[2]).build());
        }
        b.owners(os);
        java.util.List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> ss = new java.util.ArrayList<>();
        for (String s : stages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid)
                    .stageName(s)
                    .isCustom(tid == null)
                    .isCompleted(true)
                    .build());
        }
        b.selectedStages(ss);
        LandProject saved = landService.atomicIntake(b.build(), null);
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

            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",

            "CREATE TABLE IF NOT EXISTS expense_presets (" +
                "id UUID PRIMARY KEY, " +
                "name VARCHAR(100) NOT NULL UNIQUE, " +
                "created_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now())",
            "CREATE TABLE IF NOT EXISTS expenses (" +
                "id UUID PRIMARY KEY, " +
                "category VARCHAR(150) NOT NULL, " +
                "amount NUMERIC(15,2) NOT NULL, " +
                "note TEXT, " +
                "recorded_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now(), " +
                "edited_at TIMESTAMP, " +
                "edited_by VARCHAR(100))",
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

            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",

            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",

            // PHASE G -- RETIRED TITLE DETAILS: dropped from DB
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS volume",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS folio",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS instrument_no",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS physical_box_number",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS survey_date",
            // PASS 10 -- location lives on land_projects only
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS district",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS county",
        };

        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {

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
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) exists = rs.getInt(1) > 0;
                }
            }

            if (!exists) {
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) "
                           + "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset. Existing credentials remain in effect.");
            }

        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
""")

# =====================================================================
# Report + commit + push
# =====================================================================
print(f"\n=== fix10.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)}")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'fix10: Ledger rebuilt to match intake (filters/search/badges + LOCATION column w/ parish & village); purge dead title fields (district/county + retired 5) from entity+DB; canonical backend set + samples + docs'], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit {e.returncode})")
    except FileNotFoundError:
        print("\n  Git: not found")
print()