# PATH: fix.py
# PHASE 7 - DIRECTOR'S DASHBOARD
# Run from project root: py fix.py
#
# WHAT THIS PHASE DOES (per Section 17.9 of LLM_CONTEXT_GUIDE.md):
# Adds a company-wide snapshot view for the Director role: revenue
# collected in a time window, staff activity (who did how much, from
# the audit log), the project pipeline stage breakdown, and the
# company financials snapshot (committed/paid/outstanding from Phase
# 5's CompanyExpense module). Default view fetches WEEK and MONTH
# side by side; DAY and YEAR are available as opt-in extra panels
# ("must be possible to break down by day if needed... DEFAULT view
# is week + month, unless the Director changes it").
#
# BACKEND:
#   - NEW FILE: DirectorDashboardDTO.java
#   - PATCHED: DashboardController.java (new GET /api/v1/dashboard/director
#     endpoint, gated to ROLE_ADMIN / ROLE_DIRECTOR same as the rest of
#     this controller)
#
# FRONTEND:
#   - NEW FILE: DirectorDashboardPanel.jsx (self-contained panel, reuses
#     Dashboard.module.css tokens/classes already in the app)
#   - PATCHED: RootTerminal.jsx (renders the new panel)
#   - PATCHED: landService.js (getDirectorDashboard() API call)
#   - PATCHED: Dashboard.module.css (new classes for period toggle buttons
#     and staff activity rows -- appended at end of file, nothing removed)
#
# No DB migration needed -- this phase only reads existing tables
# (audit_logs, land_projects, company_expenses, payment_records).

import os

def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  -> Saved: " + path)

def patch_file(path, anchor, replacement, label):
    content = read_file(path)
    if content is None:
        print("FAIL: " + label + " (" + path + " not found)")
        return
    if anchor not in content:
        print("MISSING: " + label + " (anchor not found in " + path + " -- may already be patched, or file changed)")
        return
    if content.count(anchor) > 1:
        print("WARN: " + label + " (anchor appears more than once -- patching first occurrence only)")
    content = content.replace(anchor, replacement, 1)
    write_file(path, content)
    print("OK: " + label)

def create_new_file(path, content, label):
    if os.path.isfile(path):
        print("SKIP: " + label + " (file already exists at " + path + " -- not overwriting)")
        return
    write_file(path, content)
    print("OK: " + label + " (new file)")

print("Starting Phase 7 - Director's Dashboard...")
print("-" * 60)

# ============================================================
# BACKEND FILE PATHS
# ============================================================

dashboard_controller_path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java"
director_dto_path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/DirectorDashboardDTO.java"

# ============================================================
# NEW FILE: DirectorDashboardDTO.java
# ============================================================

director_dto_content = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/DirectorDashboardDTO.java
package com.gesolutions.erp.modules.land.dto;

import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * GE SOLUTIONS - DIRECTOR'S DASHBOARD (PHASE 7)
 *
 * Company-wide snapshot for a single time window (DAY/WEEK/MONTH/YEAR),
 * plus the always-current pipeline and company financials snapshots
 * (those two are not time-windowed -- they reflect the live state).
 *
 * See Section 17.9 of the LLM context guide for the business rules.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DirectorDashboardDTO {

    private String period;       // DAY, WEEK, MONTH, YEAR
    private String periodLabel;  // human-readable, e.g. "LAST 7 DAYS"

    private BigDecimal revenueCollected;
    private long transactionCount;

    private List<StaffActivityDTO> staffActivity;

    private Map<Integer, Long> pipelineStageCounts;

    private BigDecimal companyExpensesCommitted;
    private BigDecimal companyExpensesPaid;
    private BigDecimal companyExpensesOutstanding;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class StaffActivityDTO {
        private String username;
        private int actionCount;
        private LocalDateTime lastActiveAt;
    }
}
"""

create_new_file(director_dto_path, director_dto_content, "DirectorDashboardDTO.java")

# ============================================================
# PATCH 1: DashboardController.java - imports
# ============================================================

anchor_1 = """import com.gesolutions.erp.modules.land.dto.DashboardSummaryDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;"""

replacement_1 = """import com.gesolutions.erp.modules.land.dto.DashboardSummaryDTO;
import com.gesolutions.erp.modules.land.dto.DirectorDashboardDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.finance.repository.CompanyExpenseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;"""

patch_file(dashboard_controller_path, anchor_1, replacement_1, "DashboardController.java - imports")

# ============================================================
# PATCH 2: DashboardController.java - new repository field
# ============================================================

anchor_2 = """    private final LandProjectRepository projectRepository;
    private final ClientRepository clientRepository;
    private final UserRepository userRepository;
    private final AuditLogRepository auditLogRepository;
    private final PaymentRecordRepository paymentRecordRepository;"""

replacement_2 = """    private final LandProjectRepository projectRepository;
    private final ClientRepository clientRepository;
    private final UserRepository userRepository;
    private final AuditLogRepository auditLogRepository;
    private final PaymentRecordRepository paymentRecordRepository;
    private final CompanyExpenseRepository companyExpenseRepository;"""

patch_file(dashboard_controller_path, anchor_2, replacement_2, "DashboardController.java - add CompanyExpenseRepository field")

# ============================================================
# PATCH 3: DashboardController.java - new /director endpoint
# ============================================================

anchor_3 = """        return ResponseEntity.ok(builder.build());
    }
}"""

replacement_3 = """        return ResponseEntity.ok(builder.build());
    }

    /**
     * PHASE 7: DIRECTOR'S DASHBOARD
     *
     * Company-wide snapshot for a single time window. Frontend calls this
     * twice by default (period=WEEK and period=MONTH) to satisfy the
     * "default view is week + month" rule in Section 17.9, and can call
     * again with period=DAY or period=YEAR when the Director drills down.
     *
     * pipelineStageCounts and the company financials snapshot are NOT
     * time-windowed -- they always reflect the current live state,
     * regardless of which period was requested.
     */
    @GetMapping("/director")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<DirectorDashboardDTO> getDirectorDashboard(
            @RequestParam(defaultValue = "WEEK") String period) {

        String normalizedPeriod = period == null ? "WEEK" : period.toUpperCase();
        LocalDateTime since;
        String periodLabel;

        switch (normalizedPeriod) {
            case "DAY":
                since = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0).withNano(0);
                periodLabel = "TODAY";
                break;
            case "MONTH":
                since = LocalDateTime.now().minusDays(30);
                periodLabel = "LAST 30 DAYS";
                break;
            case "YEAR":
                since = LocalDateTime.now().minusDays(365);
                periodLabel = "LAST 365 DAYS";
                break;
            case "WEEK":
            default:
                since = LocalDateTime.now().minusDays(7);
                periodLabel = "LAST 7 DAYS";
                normalizedPeriod = "WEEK";
                break;
        }

        // Revenue collected in the window (all payment types, title + storage fee + company cost payments excluded)
        BigDecimal revenueCollected = paymentRecordRepository.sumAllPaymentsSince(since);

        List<AuditLog> logsInPeriod = auditLogRepository.findAll().stream()
                .filter(a -> a.getTimestamp() != null && a.getTimestamp().isAfter(since))
                .collect(Collectors.toList());

        long transactionCount = logsInPeriod.stream()
                .filter(a -> "PAYMENT_RECORDED".equals(a.getAction()) || "COMPANY_EXPENSE_PAYMENT".equals(a.getAction()))
                .count();

        // Staff activity: group audit logs in this window by operator
        Map<String, List<AuditLog>> byOperator = logsInPeriod.stream()
                .filter(a -> a.getPerformedBy() != null && !"SYSTEM".equals(a.getPerformedBy()))
                .collect(Collectors.groupingBy(AuditLog::getPerformedBy));

        List<DirectorDashboardDTO.StaffActivityDTO> staffActivity = byOperator.entrySet().stream()
                .map(entry -> {
                    LocalDateTime lastActive = entry.getValue().stream()
                            .map(AuditLog::getTimestamp)
                            .max(Comparator.naturalOrder())
                            .orElse(null);
                    return DirectorDashboardDTO.StaffActivityDTO.builder()
                            .username(entry.getKey())
                            .actionCount(entry.getValue().size())
                            .lastActiveAt(lastActive)
                            .build();
                })
                .sorted(Comparator.comparingInt(DirectorDashboardDTO.StaffActivityDTO::getActionCount).reversed())
                .collect(Collectors.toList());

        // Pipeline stage counts -- live snapshot, same 5-stage index used by /summary
        List<LandProject> allPlots = projectRepository.findAll();
        Map<Integer, Long> pipelineStageCounts = allPlots.stream()
                .collect(Collectors.groupingBy(LandProject::getCurrentStageIndex, Collectors.counting()));

        // Company financials -- live snapshot, not time-windowed
        BigDecimal companyCommitted = companyExpenseRepository.sumTotalCommitted();
        BigDecimal companyPaid = companyExpenseRepository.sumTotalPaid();
        BigDecimal companyOutstanding = companyCommitted.subtract(companyPaid).max(BigDecimal.ZERO);

        DirectorDashboardDTO dto = DirectorDashboardDTO.builder()
                .period(normalizedPeriod)
                .periodLabel(periodLabel)
                .revenueCollected(revenueCollected)
                .transactionCount(transactionCount)
                .staffActivity(staffActivity)
                .pipelineStageCounts(pipelineStageCounts)
                .companyExpensesCommitted(companyCommitted)
                .companyExpensesPaid(companyPaid)
                .companyExpensesOutstanding(companyOutstanding)
                .build();

        return ResponseEntity.ok(dto);
    }
}"""

patch_file(dashboard_controller_path, anchor_3, replacement_3, "DashboardController.java - new GET /dashboard/director endpoint")

# ============================================================
# FRONTEND FILE PATHS
# ============================================================

land_service_path = "erp-frontend/src/services/landService.js"
root_terminal_path = "erp-frontend/src/pages/Dashboard/RootTerminal.jsx"
dashboard_css_path = "erp-frontend/src/pages/Dashboard/Dashboard.module.css"
director_panel_path = "erp-frontend/src/pages/Dashboard/DirectorDashboardPanel.jsx"

# ============================================================
# PATCH 4: landService.js - add getDirectorDashboard()
# ============================================================

anchor_4 = """    authorizeRelease: async (projectId, managerNote) => {
        await api.patch(`/land/projects/${projectId}/release`, null, {
            params: managerNote ? { managerNote } : {}
        });
    }
};

export default landService;"""

replacement_4 = """    authorizeRelease: async (projectId, managerNote) => {
        await api.patch(`/land/projects/${projectId}/release`, null, {
            params: managerNote ? { managerNote } : {}
        });
    },

    // PHASE 7: Director's Dashboard -- period is 'DAY' | 'WEEK' | 'MONTH' | 'YEAR'
    getDirectorDashboard: async (period = 'WEEK') => {
        const response = await api.get('/dashboard/director', { params: { period } });
        return response.data;
    }
};

export default landService;"""

patch_file(land_service_path, anchor_4, replacement_4, "landService.js - add getDirectorDashboard()")

# ============================================================
# NEW FILE: DirectorDashboardPanel.jsx
# ============================================================

director_panel_content = """// PATH: erp-frontend/src/pages/Dashboard/DirectorDashboardPanel.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { FiTrendingUp, FiUsers, FiClock, FiPlus, FiX } from 'react-icons/fi';
import landService from '../../services/landService';
import styles from './Dashboard.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const PeriodCard = ({ data, loading }) => {
    if (loading) {
        return (
            <div className={styles.hwPanel}>
                <div className={styles.panelInner}>
                    <div className={styles.periodLoading}>SYNCING...</div>
                </div>
            </div>
        );
    }
    if (!data) return null;

    return (
        <div className={styles.hwPanel}>
            <div className={styles.panelHeader}>
                <FiTrendingUp aria-hidden=\"true\" /> {data.periodLabel}
            </div>
            <div className={styles.panelInner}>
                <div className={styles.periodStatRow}>
                    <div className={styles.periodStatBox}>
                        <label>REVENUE COLLECTED</label>
                        <strong>UGX {fmt(data.revenueCollected)}</strong>
                    </div>
                    <div className={styles.periodStatBox}>
                        <label>TRANSACTIONS</label>
                        <strong>{data.transactionCount}</strong>
                    </div>
                </div>

                <div className={styles.staffActivityHeader}>
                    <FiUsers aria-hidden=\"true\" /> STAFF ACTIVITY
                </div>
                {(!data.staffActivity || data.staffActivity.length === 0) ? (
                    <div className={styles.periodEmpty}>NO ACTIVITY IN THIS WINDOW</div>
                ) : (
                    <div className={styles.staffActivityList}>
                        {data.staffActivity.slice(0, 6).map((s, i) => (
                            <div key={i} className={styles.staffActivityRow}>
                                <span className={styles.staffActivityName}>{s.username}</span>
                                <span className={styles.staffActivityCount}>{s.actionCount} actions</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

const DirectorDashboardPanel = () => {
    const [weekData,  setWeekData]  = useState(null);
    const [monthData, setMonthData] = useState(null);
    const [loading,   setLoading]   = useState(true);

    const [extraPeriod, setExtraPeriod] = useState(null); // null | 'DAY' | 'YEAR'
    const [extraData,   setExtraData]   = useState(null);
    const [extraLoading, setExtraLoading] = useState(false);

    const loadDefault = useCallback(async () => {
        setLoading(true);
        try {
            const [week, month] = await Promise.all([
                landService.getDirectorDashboard('WEEK'),
                landService.getDirectorDashboard('MONTH'),
            ]);
            setWeekData(week);
            setMonthData(month);
        } catch {
            // Non-fatal -- panel stays empty, rest of dashboard still works
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadDefault(); }, [loadDefault]);

    const toggleExtra = async (period) => {
        if (extraPeriod === period) {
            setExtraPeriod(null);
            setExtraData(null);
            return;
        }
        setExtraPeriod(period);
        setExtraLoading(true);
        try {
            const data = await landService.getDirectorDashboard(period);
            setExtraData(data);
        } catch {
            setExtraData(null);
        } finally {
            setExtraLoading(false);
        }
    };

    // Pipeline + company financials are live snapshots -- same on week/month, so read from whichever loaded first
    const snapshot = weekData || monthData || extraData;

    return (
        <div className={styles.directorSection}>
            <div className={styles.directorSectionHeader}>
                <span>DIRECTOR'S DASHBOARD</span>
                <div className={styles.directorToggleRow}>
                    <button
                        className={extraPeriod === 'DAY' ? styles.directorToggleBtnActive : styles.directorToggleBtn}
                        onClick={() => toggleExtra('DAY')}
                    >
                        {extraPeriod === 'DAY' ? <FiX aria-hidden=\"true\" /> : <FiPlus aria-hidden=\"true\" />} TODAY
                    </button>
                    <button
                        className={extraPeriod === 'YEAR' ? styles.directorToggleBtnActive : styles.directorToggleBtn}
                        onClick={() => toggleExtra('YEAR')}
                    >
                        {extraPeriod === 'YEAR' ? <FiX aria-hidden=\"true\" /> : <FiPlus aria-hidden=\"true\" />} THIS YEAR
                    </button>
                </div>
            </div>

            {snapshot && (
                <div className={styles.hwPanel} style={{ marginBottom: 12 }}>
                    <div className={styles.panelHeader}>
                        <FiClock aria-hidden=\"true\" /> COMPANY FINANCIALS SNAPSHOT
                    </div>
                    <div className={styles.panelInner}>
                        <div className={styles.moneyRow}>
                            <div className={styles.moneyBox}>
                                <label>COMPANY COSTS COMMITTED</label>
                                <strong>UGX {fmt(snapshot.companyExpensesCommitted)}</strong>
                            </div>
                            <div className={styles.moneyBox}>
                                <label>COMPANY COSTS PAID</label>
                                <strong className={styles.valueEmerald}>UGX {fmt(snapshot.companyExpensesPaid)}</strong>
                            </div>
                        </div>
                        <div className={`${styles.moneyBox} ${styles.moneyBoxArrears}`}>
                            <label>COMPANY COSTS OUTSTANDING</label>
                            <strong className={styles.valueRuby}>UGX {fmt(snapshot.companyExpensesOutstanding)}</strong>
                        </div>
                    </div>
                </div>
            )}

            <div className={styles.directorPeriodGrid}>
                <PeriodCard data={weekData}  loading={loading} />
                <PeriodCard data={monthData} loading={loading} />
                {extraPeriod && <PeriodCard data={extraData} loading={extraLoading} />}
            </div>
        </div>
    );
};

export default DirectorDashboardPanel;
"""

create_new_file(director_panel_path, director_panel_content, "DirectorDashboardPanel.jsx")

# ============================================================
# PATCH 5: RootTerminal.jsx - import
# ============================================================

anchor_5 = """import styles from './Dashboard.module.css';"""

replacement_5 = """import styles from './Dashboard.module.css';
import DirectorDashboardPanel from './DirectorDashboardPanel';"""

patch_file(root_terminal_path, anchor_5, replacement_5, "RootTerminal.jsx - import DirectorDashboardPanel")

# ============================================================
# PATCH 6: RootTerminal.jsx - render the new panel
# ============================================================

anchor_6 = """                                <button className={styles.launchBtn} onClick={() => navigate('/recovery')}      aria-label=\"Go to recovery\"><FiPhoneCall aria-hidden=\"true\" /> RECOVERY</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RootTerminal;"""

replacement_6 = """                                <button className={styles.launchBtn} onClick={() => navigate('/recovery')}      aria-label=\"Go to recovery\"><FiPhoneCall aria-hidden=\"true\" /> RECOVERY</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* PHASE 7: Director's Dashboard -- company-wide snapshot */}
            <DirectorDashboardPanel />
        </div>
    );
};

export default RootTerminal;"""

patch_file(root_terminal_path, anchor_6, replacement_6, "RootTerminal.jsx - render DirectorDashboardPanel")

# ============================================================
# PATCH 7: Dashboard.module.css - append new classes at end of file
# ============================================================

anchor_7 = """@media (max-width: 600px) {
    /* statGrid stays 2-col minimum — prevents over-scrolling on small screens */
    .moneyRow    { grid-template-columns: 1fr; }
    .launchPad   { grid-template-columns: 1fr; }
    .header      { flex-direction: column; align-items: flex-start; }
    .errorHUD    { flex-direction: column; }
    .rebootBtn   { margin-left: 0; width: 100%; justify-content: center; }
}"""

replacement_7 = """@media (max-width: 600px) {
    /* statGrid stays 2-col minimum — prevents over-scrolling on small screens */
    .moneyRow    { grid-template-columns: 1fr; }
    .launchPad   { grid-template-columns: 1fr; }
    .header      { flex-direction: column; align-items: flex-start; }
    .errorHUD    { flex-direction: column; }
    .rebootBtn   { margin-left: 0; width: 100%; justify-content: center; }
}


/* ── PHASE 7: DIRECTOR'S DASHBOARD ─────────────────────────────── */
.directorSection {
    margin-top: var(--gap-xl);
}

.directorSectionHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--gap-md);
    margin-bottom: var(--gap-lg);
    padding-bottom: clamp(8px, 1vw, 12px);
    border-bottom: 1.5px solid rgba(238, 140, 58, 0.2);
    font-family: 'Cinzel', serif;
    color: var(--orange);
    font-size: clamp(13px, 1.6vw, 17px);
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.directorToggleRow {
    display: flex;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: wrap;
}

.directorToggleBtn,
.directorToggleBtnActive {
    display: inline-flex;
    align-items: center;
    gap: clamp(4px, 0.5vw, 6px);
    height: clamp(28px, 3.4vw, 34px);
    padding: 0 clamp(10px, 1.3vw, 14px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.85vw, 10px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
}

.directorToggleBtn {
    background: rgba(255, 255, 255, 0.04);
    border: 1.5px solid rgba(255, 255, 255, 0.15);
    color: rgba(255, 255, 255, 0.65);
}
.directorToggleBtn:hover {
    border-color: var(--orange);
    color: var(--orange);
    background: rgba(238, 140, 58, 0.08);
}

.directorToggleBtnActive {
    background: var(--orange);
    border: 1.5px solid var(--orange);
    color: var(--navy);
}
.directorToggleBtnActive:hover {
    background: #f0a050;
}

.directorPeriodGrid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(clamp(220px, 30vw, 320px), 1fr));
    gap: var(--gap-lg);
}

.periodStatRow {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--gap-md);
    margin-bottom: var(--gap-md);
}

.periodStatBox {
    background: rgba(0, 0, 0, 0.3);
    padding: clamp(10px, 1.4vw, 14px);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.05);
}
.periodStatBox label {
    display: block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.3);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: clamp(4px, 0.5vw, 6px);
}
.periodStatBox strong {
    font-family: 'Space Mono', monospace;
    color: #fff;
    font-size: clamp(13px, 1.5vw, 17px);
    font-weight: 700;
    word-break: break-all;
}

.staffActivityHeader {
    display: flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 8px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: clamp(6px, 0.8vw, 9px);
    padding-top: clamp(4px, 0.5vw, 6px);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.staffActivityList {
    display: flex;
    flex-direction: column;
    gap: clamp(4px, 0.5vw, 6px);
}

.staffActivityRow {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(6px, 0.8vw, 9px) clamp(9px, 1.1vw, 12px);
    background: rgba(0, 0, 0, 0.2);
    border-radius: var(--radius-sm);
    border-left: 2px solid rgba(238, 140, 58, 0.3);
}
.staffActivityName {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.95vw, 11px);
    font-weight: 800;
    color: rgba(255, 255, 255, 0.85);
}
.staffActivityCount {
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 700;
    color: var(--orange);
}

.periodEmpty {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-label);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.25);
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: clamp(10px, 1.4vw, 14px) 0;
    text-align: center;
}

.periodLoading {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-label);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    text-align: center;
    padding: clamp(20px, 3vw, 30px) 0;
    animation: glowPulse 2s infinite;
}
@keyframes glowPulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

@media (max-width: 600px) {
    .directorPeriodGrid { grid-template-columns: 1fr; }
    .periodStatRow { grid-template-columns: 1fr; }
}"""

patch_file(dashboard_css_path, anchor_7, replacement_7, "Dashboard.module.css - append Director's Dashboard styles")

print("-" * 60)
print("DONE. Check for FAIL / MISSING messages above.")
print("")
print("If all OK, run:")
print("git add -A && git commit -m 'feat: Phase 7 - Directors Dashboard' && git push")
print("")
print("TEST PLAN (per the permanent deferred-testing rule -- Phase 7 is the")
print("last planned phase, so this is the point to run the FULL end-to-end")
print("pass covering Phases 1 through 7 together):")
print("  1. Log in as Root/Admin/Director -> Dashboard -> confirm a new")
print("     'DIRECTOR'S DASHBOARD' section appears below the existing panels.")
print("  2. Confirm it shows two cards by default: LAST 7 DAYS and LAST 30 DAYS,")
print("     each with revenue collected, transaction count, and a staff")
print("     activity list.")
print("  3. Confirm the COMPANY FINANCIALS SNAPSHOT panel shows committed/")
print("     paid/outstanding numbers matching the Company Costs page.")
print("  4. Click '+ TODAY' -> confirm a third card appears for today's data,")
print("     and the button changes to an X / active state. Click it again to")
print("     remove the card.")
print("  5. Click '+ THIS YEAR' -> same check for the 365-day window.")
print("  6. Log in as a plain Manager -> confirm the Director's Dashboard")
print("     section does NOT appear (RootTerminal is Admin/Director/Root only,")
print("     unchanged from before this phase).")
print("  7. Now run the full Phase 1-7 regression pass per Section 3's")
print("     deferred-testing rule: project index display/search, NIN identity")
print("     checks, 4-tier role gates, stage checklist on Intake/Folder,")
print("     Company Costs page, Legacy Receivables toggle, and this dashboard.")