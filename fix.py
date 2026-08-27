#!/usr/bin/env python3
"""
fix11.py — Ledger rebuild to spec + backend unblock so data finally shows.
- LedgerPage: PROJECT LEDGER; filters ALL/BACKLOG/TITLED/LEGACY/RECEIVABLES/
  CRITICAL/PAID; columns INDEX/OWNER(S)/PHONE/PARISH/VILLAGE/STATUS/PROGRESS;
  search every entered field; sidebar auto-collapse standard.
- Backend: LandTitle restored to compile-proven shape; LandController index
  fix; stage service/controller aligned; DataInitializer seeds 7 samples +
  docs and drops the 5 retired columns.
Run: py fix11.py
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

def patch(rel, old, new, skip_if=None):
    p = ROOT / rel
    try: text = p.read_text(encoding="utf-8")
    except Exception as e: FAILED.append((rel, "read: " + str(e))); return
    if skip_if and skip_if in text:
        print(f"    ~ {rel}: already applied, skipped"); return
    if old not in text:
        FAILED.append((rel, "ANCHOR NOT FOUND: " + old[:70].replace("\n", "\\n"))); return
    text = text.replace(old, new, 1)
    try: p.write_text(text, encoding="utf-8"); WROTE.append(rel + " (patched)")
    except Exception as e: FAILED.append((rel, str(e)))

# =====================================================================
# 1) LedgerPage.jsx — FULL redesign
# =====================================================================
write("erp-frontend/src/pages/Ledger/LedgerPage.jsx", r'''// PATH: erp-frontend/src/pages/Ledger/LedgerPage.jsx
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
''')

# =====================================================================
# 2) LandTitle.java — compile-proven shape (deprecated district/county kept,
#    retired 5 stay removed)
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
 * RETIRED (pass 6): volume / folio / instrument_no / physical_box_number /
 * survey_date removed app-wide and dropped from the DB (PHASE G).
 * district/county stay as deprecated columns (backwards compatibility).
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

    @Deprecated
    @Column(length = 100)
    private String district;

    @Deprecated
    @Column(length = 100)
    private String county;

    @Column(name = "title_id", length = 100)
    private String titleId;

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
# 3) LandController.java — split the stacked mappings (the index fix)
# =====================================================================
patch("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
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
"""    // INTAKE: preview next project index (fixed: one mapping per method)
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

    @PostMapping("/projects/{id}/unlock-log")
    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }""",
    skip_if="// INTAKE: preview next project index (fixed")

# =====================================================================
# 4) StageTemplateService.java — add normalize + bulk (idempotent)
# =====================================================================
patch("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java",
"""    // INTAKE REDESIGN: allow deleting middle stages from the template
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }
}""",
"""    // INTAKE REDESIGN: allow deleting middle stages from the template
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }

    private static final java.util.Set<String> DEFAULT_STAGE_NAMES =
            java.util.Set.of(DEFAULT_STAGES);

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
        return templateRepository.saveAll(toSave);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void bulkDeleteTemplateStages(List<UUID> ids) {
        if (ids == null || ids.isEmpty()) return;
        List<StageTemplate> toDelete = templateRepository.findAllById(ids);
        if (!toDelete.isEmpty()) templateRepository.deleteAllInBatch(toDelete);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> restoreDefaultStages() {
        List<StageTemplate> current = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
        List<StageTemplate> nonDefault = current.stream()
                .filter(s -> !DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .toList();
        if (!nonDefault.isEmpty()) templateRepository.deleteAllInBatch(nonDefault);
        java.util.Map<String, StageTemplate> keepByName = current.stream()
                .filter(s -> DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .collect(java.util.stream.Collectors.toMap(StageTemplate::getStageName, s -> s, (a, b) -> a));
        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = keepByName.get(name);
            if (stage == null) {
                stage = StageTemplate.builder().stageName(name).defaultCost(BigDecimal.ZERO)
                        .displayOrder(order).isActive(true).build();
            } else {
                stage.setDisplayOrder(order);
            }
            order++;
            toSave.add(stage);
        }
        return templateRepository.saveAll(toSave);
    }
}""",
    skip_if="normalizeToDefaultStages")

# =====================================================================
# 5) StageTemplateController.java — bulk endpoints (idempotent)
# =====================================================================
patch("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java",
"""    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteStage(@PathVariable UUID id) {
        stageTemplateService.deleteTemplateStage(id);
        return ResponseEntity.noContent().build();
    }
}""",
"""    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteStage(@PathVariable UUID id) {
        stageTemplateService.deleteTemplateStage(id);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/stage-templates/reorder")
    public ResponseEntity<List<StageTemplate>> reorderTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> orderedIds = (body.getOrDefault("orderedIds", List.of())).stream()
                .map(UUID::fromString).toList();
        return ResponseEntity.ok(stageTemplateService.reorderTemplateStages(orderedIds));
    }

    @DeleteMapping("/stage-templates/bulk")
    public ResponseEntity<Void> bulkDeleteTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> ids = (body.getOrDefault("ids", List.of())).stream()
                .map(UUID::fromString).toList();
        stageTemplateService.bulkDeleteTemplateStages(ids);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/stage-templates/restore-defaults")
    public ResponseEntity<List<StageTemplate>> restoreDefaultStages() {
        return ResponseEntity.ok(stageTemplateService.restoreDefaultStages());
    }
}""",
    skip_if="restore-defaults")

# =====================================================================
# 6) DataInitializer.java — add normalize + 7 sample projects + docs +
#    PHASE G drops (idempotent)
# =====================================================================
patch("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
"""import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.service.StageTemplateService;""",
"""import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.service.LandService;
import com.gesolutions.erp.modules.land.service.StageTemplateService;""",
    skip_if="seedSampleProjects")

patch("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
"""    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;""",
"""    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;
    private final LandService landService;""",
    skip_if="private final LandService landService;")

patch("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
"""        // PHASE 4: Seed the default stage template checklist if empty
        stageTemplateService.seedDefaultStagesIfEmpty();
""",
"""        // PHASE 4: Seed the default stage template checklist if empty
        stageTemplateService.seedDefaultStagesIfEmpty();

        // PASS 6: master checklist must always be exactly the 6 defaults
        try {
            stageTemplateService.normalizeToDefaultStages();
            System.out.println(">>> [STAGE_TEMPLATE] Normalized master checklist to defaults.");
        } catch (Exception e) {
            System.err.println(">>> [STAGE_TEMPLATE] normalize warning: " + e.getMessage());
        }

        // PASS 6/11: seed diverse SAMPLE projects so the Ledger has data (once)
        seedSampleProjects();
        seedSampleDocuments();
""",
    skip_if="seedSampleProjects();")

patch("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
"""            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
        };""",
"""            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",

            // PHASE G -- RETIRED TITLE DETAILS: dropped from DB
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS volume",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS folio",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS instrument_no",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS physical_box_number",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS survey_date",
        };""",
    skip_if="DROP COLUMN IF EXISTS volume")

patch("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
"""    // NOTE: Deliberately NOT @Transactional -- we use raw JDBC so this is
    // completely immune to Spring AOP proxy bypass, Hibernate L1 cache,
    // EntityManager flush timing, and @Builder.Default field conflicts.
    public void seedRootUser() {""",
"""    // 7 diverse SAMPLE projects (guarded: only when none exist yet)
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

    // NOTE: Deliberately NOT @Transactional -- we use raw JDBC so this is
    // completely immune to Spring AOP proxy bypass, Hibernate L1 cache,
    // EntityManager flush timing, and @Builder.Default field conflicts.
    public void seedRootUser() {""",
    skip_if="private void seedSampleProjects()")

# =====================================================================
# Report + commit + push
# =====================================================================
print(f"\n=== fix11.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)}")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'fix11: PROJECT LEDGER redesign (filters/columns/search per spec + sidebar standard) + backend unblock (compile-safe LandTitle, index fix, samples seed)'], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit {e.returncode})")
    except FileNotFoundError:
        print("\n  Git: not found")
print()