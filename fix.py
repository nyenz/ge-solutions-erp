# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content.strip() + '\n')
    print(f"OK (OVERWRITTEN): {path}")

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK (PATCHED): {label}")
    else:
        print(f"MISSING: {label}")

BASE = os.path.dirname(os.path.abspath(__file__))

print("=== STARTING COMPREHENSIVE RECOVERY REDESIGN ===")

# ─── 1. OVERWRITE: RecoveryTaskDTO.java ──────────────────────────────
dto_path = os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'client', 'dto', 'RecoveryTaskDTO.java')
write(dto_path, """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java
package com.gesolutions.erp.modules.client.dto;

import lombok.*;
import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RecoveryTaskDTO {
    private UUID clientId;
    private String ownerName;
    private String phoneNumber;
    private String email;

    private String lastContactDate;
    private String nextCallDue;
    private String missionStatus;
    private boolean isLocked;
    private int monthlyCallCount;

    private BigDecimal totalDemand;
    private BigDecimal totalOriginalDebt;
    private BigDecimal totalStorageFees;
    private boolean hasBacklogPlots;

    private List<PlotSummary> plots;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PlotSummary {
        private UUID projectId;
        private String plotNumber;
        private String physicalBoxNumber;
        private boolean isBacklog;

        private BigDecimal totalCost;
        private BigDecimal amountPaid;
        private BigDecimal currentBalance;

        private BigDecimal originalDebt;
        private BigDecimal storageFeesAccumulated;
        private BigDecimal totalBacklogOwed;
        private long storageMonthsCount;
        private boolean storagePaused;
        private BigDecimal storageFeeOverride;

        private String paymentHealthBadge;
        private String lastPaymentDate;
        private String lastInteractionNote;
    }
}""")

# ─── 2. OVERWRITE: RecoveryController.java ───────────────────────────
ctrl_path = os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'client', 'controller', 'RecoveryController.java')
write(ctrl_path, """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java
package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.dto.RecoveryTaskDTO;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.service.LandService;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class RecoveryController {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;
    private final PaymentRecordRepository paymentRecordRepository;
    private final LandService landService;

    @GetMapping("/count")
    public ResponseEntity<Map<String, Long>> getStaleCount() {
        List<LandProject> allProjects = projectRepository.findAll();
        long count = buildOwnerTasks(allProjects).stream()
                .filter(dto -> !dto.isLocked())
                .count();
        return ResponseEntity.ok(Map.of("staleCount", count));
    }

    @GetMapping("/queue")
    public ResponseEntity<List<RecoveryTaskDTO>> getRecoveryQueue() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> queue = buildOwnerTasks(allProjects).stream()
                .filter(dto -> !dto.isLocked())
                .filter(dto -> dto.getTotalDemand().compareTo(BigDecimal.ZERO) > 0)
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(queue);
    }

    @GetMapping("/schedule")
    public ResponseEntity<List<RecoveryTaskDTO>> getFullSchedule() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> all = buildOwnerTasks(allProjects).stream()
                .filter(dto -> dto.getTotalDemand().compareTo(BigDecimal.ZERO) > 0)
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(all);
    }

    private List<RecoveryTaskDTO> buildOwnerTasks(List<LandProject> allProjects) {
        Map<UUID, List<LandProject>> clientPlotsMap = new LinkedHashMap<>();
        Map<UUID, Client> clientRegistry = new HashMap<>();

        for (LandProject plot : allProjects) {
            BigDecimal balance = plot.isBacklog() ? plot.backlogTotalOwed() : plot.activeTotalOwed();
            if (balance.compareTo(BigDecimal.ZERO) <= 0) continue;

            Set<Client> proprietors = plot.getProprietors();
            if (proprietors == null || proprietors.isEmpty()) continue;

            Client primary = proprietors.stream()
                    .sorted(Comparator.comparing(Client::getFullName))
                    .findFirst().orElse(null);

            if (primary != null) {
                clientPlotsMap.computeIfAbsent(primary.getId(), k -> new ArrayList<>()).add(plot);
                clientRegistry.put(primary.getId(), primary);
            }
        }

        List<RecoveryTaskDTO> result = new ArrayList<>();

        for (Map.Entry<UUID, List<LandProject>> entry : clientPlotsMap.entrySet()) {
            UUID clientId = entry.getKey();
            List<LandProject> plots = entry.getValue();
            Client client = clientRegistry.get(clientId);

            if (client.shouldResetMonthlyCounter()) {
                client.setMonthlyContactCount(0);
            }

            LocalDateTime lastContact = client.getLastContactedAt();
            int callCount = client.getMonthlyContactCount();

            String missionStatus;
            String nextCallDue;
            boolean isLocked;

            if (lastContact == null) {
                missionStatus = "NEW ASSIGNMENT";
                nextCallDue = LocalDate.now().toString();
                isLocked = false;
            } else if (callCount >= 2) {
                missionStatus = "MONTHLY LIMIT";
                nextCallDue = LocalDate.now().plusMonths(1)
                        .with(TemporalAdjusters.firstDayOfMonth()).toString();
                isLocked = true;
            } else {
                LocalDate eligibleDate = lastContact.toLocalDate().plusDays(14);
                if (!LocalDate.now().isBefore(eligibleDate)) {
                    missionStatus = "ACTION REQUIRED";
                    nextCallDue = LocalDate.now().toString();
                    isLocked = false;
                } else {
                    missionStatus = "COOLING DOWN";
                    nextCallDue = eligibleDate.toString();
                    isLocked = true;
                }
            }

            BigDecimal totalDemand = BigDecimal.ZERO;
            BigDecimal totalOriginalDebt = BigDecimal.ZERO;
            BigDecimal totalStorageFees = BigDecimal.ZERO;
            boolean hasBacklog = false;

            List<RecoveryTaskDTO.PlotSummary> plotSummaries = new ArrayList<>();

            for (LandProject plot : plots) {
                List<FollowUpLog> logs = followUpRepository.findByProjectIdOrderByTimestampDesc(plot.getId());
                String lastNote = logs.isEmpty() ? "NO PRIOR CONTACT" : logs.get(0).getNotes();

                BigDecimal plotBalance = plot.isBacklog() ? plot.backlogTotalOwed() : plot.activeTotalOwed();
                totalDemand = totalDemand.add(plotBalance);

                String badge = computePaymentBadge(plot);
                String lastPaymentStr = plot.getLastPaymentDate() != null
                        ? plot.getLastPaymentDate().toLocalDate().toString() : "NEVER";

                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()
                        .projectId(plot.getId())
                        .plotNumber(plot.getLandTitle().getPlotNumber())
                        .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())
                        .isBacklog(plot.isBacklog())
                        .lastInteractionNote(lastNote)
                        .paymentHealthBadge(badge)
                        .lastPaymentDate(lastPaymentStr);

                if (plot.isBacklog()) {
                    hasBacklog = true;
                    BigDecimal fees = plot.getStorageFeesAccumulated() != null ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;
                    BigDecimal origDebt = plot.getTotalCost() != null ? plot.getTotalCost() : BigDecimal.ZERO;
                    long months = plot.getBacklogStartDate() != null
                            ? ChronoUnit.MONTHS.between(plot.getBacklogStartDate(), LocalDateTime.now()) : 0;

                    summaryBuilder
                            .originalDebt(origDebt)
                            .storageFeesAccumulated(fees)
                            .totalBacklogOwed(plotBalance)
                            .storageMonthsCount(months)
                            .storagePaused(plot.isStoragePaused())
                            .storageFeeOverride(plot.getStorageFeeOverride())
                            .amountPaid(plot.getAmountPaid());

                    totalOriginalDebt = totalOriginalDebt.add(origDebt);
                    totalStorageFees = totalStorageFees.add(fees);
                } else {
                    summaryBuilder
                            .totalCost(plot.getTotalCost())
                            .amountPaid(plot.getAmountPaid())
                            .currentBalance(plotBalance);
                }

                plotSummaries.add(summaryBuilder.build());
            }

            RecoveryTaskDTO dto = RecoveryTaskDTO.builder()
                    .clientId(client.getId())
                    .ownerName(client.getFullName())
                    .phoneNumber(client.getPhoneNumber())
                    .email(client.getEmail())
                    .lastContactDate(lastContact != null ? lastContact.toLocalDate().toString() : "NEVER")
                    .nextCallDue(nextCallDue)
                    .missionStatus(missionStatus)
                    .isLocked(isLocked)
                    .monthlyCallCount(callCount)
                    .totalDemand(totalDemand)
                    .totalOriginalDebt(totalOriginalDebt)
                    .totalStorageFees(totalStorageFees)
                    .hasBacklogPlots(hasBacklog)
                    .plots(plotSummaries)
                    .build();

            result.add(dto);
        }

        return result;
    }

    private String computePaymentBadge(LandProject plot) {
        if (plot.getLastPaymentDate() == null) return "RED";
        long daysSince = ChronoUnit.DAYS.between(plot.getLastPaymentDate(), LocalDateTime.now());
        if (daysSince <= 14) return "GREEN";
        if (daysSince <= 30) return "YELLOW";
        return "RED";
    }
}""")

# ─── 3. PATCH: DashboardController.java ────────────────────────────────
dash_path = os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules/land/controller/DashboardController.java')
patch(
    dash_path,
    'long staleCalls = allPlots.stream()',
    '''// Stale count = unique owners (Client IDs) who are due for a call today
        long staleCalls = allPlots.stream()''',
    'DashboardController: Sync Bell Logic'
)

# ─── 4. OVERWRITE: RecoveryPortal.jsx ──────────────────────────────────
jsx_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.jsx')
write(jsx_path, """// PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity, FiHome, FiTrendingDown,
    FiArchive, FiZap, FiSettings, FiRepeat
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);
    const dismiss = useCallback((id) => setToasts(prev => prev.filter(t => t.id !== id)), []);
    return { toasts, toast, dismissToast: dismiss };
};

const TOAST_ICONS = {
    success: <FiCheckSquare aria-hidden="true" />,
    error:   <FiAlertCircle aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo aria-hidden="true" />,
};

const ToastContainer = ({ toasts, onDismiss }) => {
    if (typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
                    <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
                    <span className={styles.toastMsg}>{t.message}</span>
                    <button className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss">
                        <FiX aria-hidden="true" />
                    </button>
                </div>
            ))}
        </div>,
        document.body
    );
};

const fmt = (n) => Number(n || 0).toLocaleString();

const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Paid within 14 days', YELLOW: 'Paid within 30 days', RED: 'No recent payment' };

const PaymentBadge = ({ badge }) => (
    <span
        style={{
            display: 'inline-block', width: 9, height: 9, borderRadius: '50%',
            background: BADGE_COLORS[badge] || BADGE_COLORS.RED,
            flexShrink: 0, marginTop: 3,
            boxShadow: `0 0 5px ${BADGE_COLORS[badge] || BADGE_COLORS.RED}`
        }}
        title={BADGE_LABELS[badge] || 'No recent payment'}
        aria-label={BADGE_LABELS[badge] || 'No recent payment'}
    />
);

// ── STORAGE FEE INLINE CONTROLS ────────────────────────────────
const StorageFeeInlineControls = ({ plot, onUpdated, toast }) => {
    const [rateInput, setRateInput] = React.useState('');
    const [saving, setSaving] = React.useState(false);
    const [expanded, setExpanded] = React.useState(false);

    const handleSetRate = async () => {
        const val = Number(rateInput);
        if (rateInput === '' || val < 0) {
            toast('ENTER A VALID MONTHLY RATE', 'error');
            return;
        }
        setSaving(true);
        try {
            await recoveryService.setStorageRate(plot.projectId, val);
            setRateInput('');
            setExpanded(false);
            await onUpdated();
            toast('MONTHLY FEE UPDATED', 'success');
        } catch {
            toast('FEE UPDATE FAILED', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleTogglePause = async () => {
        setSaving(true);
        try {
            await recoveryService.pauseStorageFees(plot.projectId, !plot.storagePaused);
            await onUpdated();
            toast(plot.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED', 'info');
        } catch {
            toast('ACTION FAILED', 'error');
        } finally {
            setSaving(false);
        }
    };

    const currentRate = plot.storageFeeOverride && Number(plot.storageFeeOverride) > 0
        ? Number(plot.storageFeeOverride)
        : 50000;

    if (!expanded) {
        return (
            <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <button
                    onClick={() => setExpanded(true)}
                    style={{
                        background: 'transparent',
                        border: '1px solid rgba(239,68,68,0.3)',
                        borderRadius: 5,
                        color: 'rgba(252,165,165,0.7)',
                        fontFamily: 'DM Sans,sans-serif',
                        fontSize: 9,
                        fontWeight: 900,
                        letterSpacing: 1,
                        textTransform: 'uppercase',
                        padding: '4px 10px',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                    }}>
                    <FiSettings size={10} />
                    FEE: UGX {Number(currentRate).toLocaleString()}/mo
                    {plot.storagePaused && <span style={{color:'#fcd34d'}}> · PAUSED</span>}
                </button>
            </div>
        );
    }

    return (
        <div style={{
            marginTop: 10,
            padding: '10px 12px',
            background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: 7,
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#fca5a5', textTransform: 'uppercase', letterSpacing: 1.5 }}>
                    STORAGE FEE SETTINGS
                </span>
                <button onClick={() => setExpanded(false)} style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.4)', cursor: 'pointer', fontSize: 14 }}>
                    <FiX size={13} />
                </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div>
                    <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 8, fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 5 }}>
                        MONTHLY RATE (UGX)
                    </div>
                    <div style={{ display: 'flex', gap: 5 }}>
                        <input
                            type="number"
                            value={rateInput}
                            onChange={e => setRateInput(e.target.value)}
                            placeholder={String(currentRate)}
                            style={{
                                flex: 1,
                                background: '#fff',
                                border: '1.5px solid #c8d6d7',
                                borderRadius: 5,
                                color: '#1a2e30',
                                fontFamily: 'Space Mono,monospace',
                                fontWeight: 700,
                                fontSize: 11,
                                padding: '5px 8px',
                                outline: 'none',
                                minWidth: 0,
                            }}
                        />
                        <button
                            onClick={handleSetRate}
                            disabled={saving}
                            style={{
                                background: '#EE8C3A',
                                border: 'none',
                                borderRadius: 5,
                                color: '#1a2e30',
                                fontFamily: 'DM Sans,sans-serif',
                                fontSize: 9,
                                fontWeight: 900,
                                padding: '0 9px',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                flexShrink: 0,
                            }}>
                            SET
                        </button>
                    </div>
                </div>
                <div>
                    <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 8, fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 5 }}>
                        FEE STATUS
                    </div>
                    <button
                        onClick={handleTogglePause}
                        disabled={saving}
                        style={{
                            width: '100%',
                            background: plot.storagePaused ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                            border: plot.storagePaused ? '1.5px solid rgba(16,185,129,0.5)' : '1.5px solid rgba(245,158,11,0.5)',
                            borderRadius: 5,
                            color: plot.storagePaused ? '#34d399' : '#fcd34d',
                            fontFamily: 'DM Sans,sans-serif',
                            fontSize: 9,
                            fontWeight: 900,
                            padding: '6px 0',
                            cursor: 'pointer',
                            textTransform: 'uppercase',
                            letterSpacing: 1,
                        }}>
                        {plot.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                    </button>
                </div>
            </div>
        </div>
    );
};

// ── MAIN COMPONENT ──────────────────────────────────────────────
const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;

    const [viewMode,      setViewMode]      = useState('ACTION');
    const [missions,      setMissions]      = useState([]);
    const [loading,       setLoading]       = useState(true);
    const [expandedId,    setExpandedId]    = useState(null);
    const [searchTerm,    setSearchTerm]    = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [statusFilter,  setStatusFilter]  = useState('ALL');

    const [callModal,     setCallModal]     = useState({ open: false, mission: null });
    const [callHistory,   setCallHistory]   = useState([]);
    const [logContent,    setLogContent]    = useState('');
    const [committing,    setCommitting]    = useState(false);

    const callDirty = callModal.open && logContent.trim() !== '';
    const { blocked: guardOpen, proceed: guardLeave, reset: guardStay } = useRouterBlock(callDirty);

    const [discardModalOpen, setDiscardModalOpen] = useState(false);

    const handleCloseCallModal = () => {
        if (callDirty) {
            setDiscardModalOpen(true);
            return;
        }
        setCallModal({ open: false, mission: null });
        setLogContent('');
    };

    const handleConfirmDiscard = () => {
        setDiscardModalOpen(false);
        setCallModal({ open: false, mission: null });
        setLogContent('');
    };

    const handleCancelDiscard = () => {
        setDiscardModalOpen(false);
    };

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION'
                ? await recoveryService.getMissionQueue()
                : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch {
            toast('Failed to load recovery data', 'error', 6000);
        } finally {
            setLoading(false);
        }
    }, [viewMode, toast]);

    useEffect(() => { loadData(); }, [loadData]);

    useEffect(() => {
        if (!callModal.mission) return;
        recoveryService.getHistory(callModal.mission.projectId)
            .then(setCallHistory)
            .catch(() => setCallHistory([]));
    }, [callModal.mission]);

    const handleLogCall = async () => {
        if (!logContent.trim() || !callModal.mission) return;
        setCommitting(true);
        try {
            await recoveryService.logRecoveryCall(callModal.mission.projectId, logContent);
            await loadData();
            setCallModal({ open: false, mission: null });
            setLogContent('');
            setExpandedId(null);
            toast('Call logged. 14-day timer reset.', 'success');
        } catch {
            toast('LOG FAILURE', 'error', 8000);
        } finally {
            setCommitting(false);
        }
    };

    const filteredMissions = useMemo(() => {
        let list = missions;

        // Search filter
        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase().replace(/\\s+/g, '');
            list = list.filter(m =>
                m.plotNumber?.toLowerCase().includes(term) ||
                m.physicalBoxNumber?.toLowerCase().includes(term) ||
                (m.owners || []).some(o =>
                    o.fullName?.toLowerCase().includes(term) ||
                    o.phoneNumber?.replace(/\\s+/g, '').includes(term)
                )
            );
        }

        // Status filter
        if (statusFilter === 'BACKLOG') list = list.filter(m => m.backlog || m.isBacklog);
        if (statusFilter === 'ACTIVE')  list = list.filter(m => !(m.backlog || m.isBacklog));
        if (statusFilter === 'DUE')     list = list.filter(m => !m.isLocked);

        return list;
    }, [missions, searchTerm, statusFilter]);

    const getStatusStyle = (status) => {
        if (status === 'ACTION REQUIRED' || status === 'NEW ASSIGNMENT') return styles.statusRed;
        if (status === 'COOLING DOWN')  return styles.statusBlue;
        if (status === 'MONTHLY LIMIT') return styles.statusGrey;
        return styles.statusDefault;
    };

    const totalBacklogOwed  = useMemo(() => filteredMissions.filter(m => m.isBacklog || m.backlog).reduce((s, m) => s + Number(m.totalBacklogOwed || 0), 0), [filteredMissions]);
    const totalActiveOwed   = useMemo(() => filteredMissions.filter(m => !(m.isBacklog || m.backlog)).reduce((s, m) => s + Number(m.currentBalance || 0), 0), [filteredMissions]);
    const totalStorageFees  = useMemo(() => filteredMissions.reduce((s, m) => s + Number(m.storageFeesAccumulated || 0), 0), [filteredMissions]);

    const renderCard = (mission) => {
        const isExpanded = expandedId === mission.projectId;
        const toggle = () => setExpandedId(prev => prev === mission.projectId ? null : mission.projectId);
        const owners = mission.owners || [];
        const ownerNames = owners.map(o => o.fullName).join(' & ') || '---';
        const phones = owners.map(o => o.phoneNumber).join(' / ') || '---';
        const balance = mission.isBacklog || mission.backlog
            ? mission.totalBacklogOwed
            : mission.currentBalance;

        return (
            <div key={mission.projectId}
                className={`${styles.missionCard} ${mission.isLocked ? styles.cardLocked : ''} ${(mission.isBacklog || mission.backlog) ? styles.cardBacklog : ''}`}>

                <div className={`${styles.statusBadge} ${getStatusStyle(mission.missionStatus)}`}>
                    {mission.isLocked && <FiLock size={10} />}
                    {mission.missionStatus}
                </div>

                {/* COMPACT CLOSED VIEW */}
                <div className={styles.cardHeader} onClick={toggle} role="button" tabIndex={0}
                    aria-expanded={isExpanded}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } }}>

                    <div className={styles.cardMain}>
                        <div className={styles.cardTopRow}>
                            <PaymentBadge badge={mission.paymentHealthBadge} />
                            <span className={styles.plotId}>{mission.plotNumber}</span>
                            {(mission.isBacklog || mission.backlog) && (
                                <span className={styles.backlogPill}>BACKLOG</span>
                            )}
                        </div>
                        <div className={styles.ownerLine}>{ownerNames}</div>
                        <div className={styles.phoneLine}>{phones}</div>
                        <div className={styles.balanceLine}>
                            <span className={styles.balanceLabel}>OWED:</span>
                            <span className={`${styles.balanceVal} ${(mission.isBacklog || mission.backlog) ? styles.balanceRed : ''}`}>
                                UGX {fmt(balance)}
                            </span>
                        </div>
                    </div>

                    <div className={styles.cardSideActions}>
                        <button className={styles.logCallBtnSmall}
                            disabled={mission.isLocked}
                            onClick={e => { e.stopPropagation(); setCallModal({ open: true, mission }); setLogContent(''); }}
                            aria-label="Log call">
                            <FiPhoneCall size={12} />
                            {mission.isLocked ? 'LOCKED' : 'LOG CALL'}
                        </button>
                        <div className={styles.expandIcon} aria-hidden="true">
                            {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                        </div>
                    </div>
                </div>

                {/* EXPANDED DETAILS */}
                {isExpanded && (
                    <div className={styles.cardBody}>
                        <div className={styles.divider} />
                        <div className={styles.timingRow}>
                            <FiClock size={11} />
                            <span>Last call: <strong>{mission.lastContactDate}</strong></span>
                            <span className={styles.timingSep} />
                            <span>Next: <strong>{mission.nextCallDue}</strong></span>
                            <span className={styles.timingSep} />
                            <span>Calls: <strong>{mission.monthlyCallCount}/2</strong></span>
                        </div>
                        {/* financial detail */}
                        {(mission.isBacklog || mission.backlog) ? (
                            <div className={styles.finDetail}>
                                <div className={styles.finDetailRow}>
                                    <span>Title cost</span><strong>UGX {fmt(mission.totalCost)}</strong>
                                </div>
                                <div className={styles.finDetailRow}>
                                    <span style={{color:'#fca5a5'}}>+ Storage fees</span>
                                    <strong style={{color:'#ef4444'}}>UGX {fmt(mission.storageFeesAccumulated)}</strong>
                                </div>
                                <div className={styles.finDetailRow}>
                                    <span>- Paid</span>
                                    <strong style={{color:'#86efac'}}>UGX {fmt(mission.amountPaid)}</strong>
                                </div>
                                <div className={`${styles.finDetailRow} ${styles.finDetailTotal}`}>
                                    <span>NOW OWED</span>
                                    <strong style={{color:'#ef4444'}}>UGX {fmt(mission.totalBacklogOwed)}</strong>
                                </div>
                            </div>
                        ) : (
                            <div className={styles.finDetail}>
                                <div className={styles.finDetailRow}>
                                    <span>Total cost</span><strong>UGX {fmt(mission.totalCost)}</strong>
                                </div>
                                <div className={styles.finDetailRow}>
                                    <span>Paid</span>
                                    <strong style={{color:'#86efac'}}>UGX {fmt(mission.amountPaid)}</strong>
                                </div>
                                <div className={`${styles.finDetailRow} ${styles.finDetailTotal}`}>
                                    <span>BALANCE</span>
                                    <strong>UGX {fmt(mission.currentBalance)}</strong>
                                </div>
                            </div>
                        )}
                        <div className={styles.lastNote}>
                            <FiMessageSquare size={11} />
                            <span>"{mission.lastInteractionNote}"</span>
                        </div>
                        
                        {(mission.isBacklog || mission.backlog) && isAdmin && (
                            <StorageFeeInlineControls
                                plot={mission}
                                onUpdated={loadData}
                                toast={toast}
                            />
                        )}

                        <div className={styles.expandedActions}>
                            <button className={styles.folderBtn}
                                onClick={() => navigate(`/folder/${mission.projectId}#financials`)}>
                                <FiChevronRight size={12} /> OPEN FOLDER
                            </button>
                            {isAdmin && (
                                <button className={styles.payBtn}
                                    onClick={() => navigate(`/folder/${mission.projectId}?action=pay#financials`)}>
                                    <FiDollarSign size={12} /> RECORD PAYMENT
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const backlogMissions = filteredMissions.filter(m => m.backlog || m.isBacklog);
    const activeMissions  = filteredMissions.filter(m => !(m.backlog || m.isBacklog));

    if (loading) return (
        <div className={styles.bootScreen} role="status">
            <div className={styles.bootSpinner} aria-hidden="true" />
            <span className={styles.bootLabel}>LOADING RECOVERY DATA...</span>
        </div>
    );

    return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={guardStay} onLeave={guardLeave} context="Recovery Portal" />
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Call Recovery</h1>
                    <p className={styles.pageSubtitle}>Log client calls and record payments</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.modeSwitch} role="group" aria-label="View mode">
                        <button className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('ACTION'); setExpandedId(null); }}
                            aria-pressed={viewMode === 'ACTION'}>
                            <FiList aria-hidden="true" /> DUE FOR CALL
                        </button>
                        <button className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('FORECAST'); setExpandedId(null); }}
                            aria-pressed={viewMode === 'FORECAST'}>
                            <FiCalendar aria-hidden="true" /> ALL TARGETS
                        </button>
                    </div>
                </div>
            </header>

            {/* FINANCIAL SUMMARY HUD */}
            <div className={styles.finHUD}>
                <div className={styles.finHUDCard}>
                    <label>ACTIVE TITLES OWED</label>
                    <strong style={{color:'#EE8C3A'}}>UGX {fmt(totalActiveOwed)}</strong>
                    <span>{activeMissions.length} active plot{activeMissions.length !== 1 ? 's' : ''}</span>
                </div>
                <div className={styles.finHUDCard} style={{borderColor:'rgba(239,68,68,0.35)'}}>
                    <label style={{color:'#fca5a5'}}>BACKLOG TOTAL OWED</label>
                    <strong style={{color:'#ef4444'}}>UGX {fmt(totalBacklogOwed)}</strong>
                    <span>{backlogMissions.length} backlog plot{backlogMissions.length !== 1 ? 's' : ''}</span>
                </div>
                <div className={styles.finHUDCard} style={{borderColor:'rgba(239,68,68,0.2)'}}>
                    <label style={{color:'rgba(252,165,165,0.8)'}}>STORAGE FEES IN BACKLOG</label>
                    <strong style={{color:'rgba(239,68,68,0.85)'}}>UGX {fmt(totalStorageFees)}</strong>
                    <span>across all backlog plots</span>
                </div>
            </div>

            {/* SEARCH + FILTER */}
            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <input type="search" placeholder="Search plot ID, owner, or phone..."
                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)} />
                    {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}
                    {searchTerm && (
                        <button className={styles.searchClear} onClick={() => setSearchTerm('')} aria-label="Clear">
                            <FiX aria-hidden="true" />
                        </button>
                    )}
                </div>
                <div className={styles.filterPills}>
                    {[
                        { key: 'ALL',     label: 'ALL' },
                        { key: 'DUE',     label: 'DUE NOW' },
                        { key: 'ACTIVE',  label: 'ACTIVE TITLES' },
                        { key: 'BACKLOG', label: 'BACKLOG' },
                    ].map(f => (
                        <button key={f.key}
                            className={`${styles.filterPill} ${statusFilter === f.key ? styles.filterPillActive : ''}`}
                            onClick={() => setStatusFilter(f.key)}>
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* PAYMENT HEALTH LEGEND */}
            <div className={styles.legend}>
                {Object.entries(BADGE_COLORS).map(([k, c]) => (
                    <span key={k} className={styles.legendItem}>
                        <span style={{
                            width: 9, height: 9, borderRadius: '50%',
                            background: c, display: 'inline-block', flexShrink: 0,
                            boxShadow: `0 0 4px ${c}`
                        }} />
                        {BADGE_LABELS[k]}
                    </span>
                ))}
            </div>

            <div className={styles.missionGrid}>
                {filteredMissions.length === 0 ? (
                    <div className={styles.emptyGate} role="status">
                        <FiCheckCircle className={styles.emptyIcon} />
                        <h2 className={styles.emptyTitle}>NO TARGETS FOUND</h2>
                    </div>
                ) : (
                    <>
                        {activeMissions.length > 0 && (
                            <div className={styles.sectionGroup}>
                                <div className={styles.sectionHeader}>
                                    <FiActivity aria-hidden="true" /> ACTIVE TITLES ({activeMissions.length})
                                </div>
                                {activeMissions.map(renderCard)}
                            </div>
                        )}
                        {backlogMissions.length > 0 && (
                            <div className={styles.sectionGroup}>
                                <div className={`${styles.sectionHeader} ${styles.sectionHeaderBacklog}`}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG — STORAGE FEES RUNNING ({backlogMissions.length})
                                </div>
                                {backlogMissions.map(renderCard)}
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* DISCARD CONFIRM MODAL */}
            {discardModalOpen && typeof document !== 'undefined' && (
                <div style={{
                    position:'fixed',inset:0,zIndex:99999,
                    background:'rgba(10,20,22,0.88)',backdropFilter:'blur(6px)',
                    display:'flex',alignItems:'center',justifyContent:'center',padding:'clamp(16px,3vw,32px)'
                }} role="dialog" aria-modal="true">
                    <div style={{
                        background:'linear-gradient(160deg,#1c3335 0%,#213E40 100%)',
                        border:'1.5px solid rgba(238,140,58,0.4)',borderRadius:14,
                        maxWidth:460,width:'100%',overflow:'hidden',
                        boxShadow:'0 30px 80px rgba(0,0,0,0.7)'
                    }}>
                        <div style={{display:'flex',alignItems:'center',gap:12,padding:'14px 20px',borderBottom:'1px solid rgba(245,158,11,0.2)',background:'rgba(245,158,11,0.12)'}}>
                            <FiAlertTriangle style={{fontSize:20,color:'#f59e0b',flexShrink:0}} />
                            <span style={{fontFamily:'Space Mono,monospace',fontSize:11,fontWeight:900,textTransform:'uppercase',letterSpacing:1.5,color:'#fcd34d'}}>DISCARD CALL LOG?</span>
                        </div>
                        <p style={{padding:'16px 20px',fontFamily:'DM Sans,sans-serif',fontSize:13,fontWeight:800,lineHeight:1.6,color:'rgba(255,255,255,0.8)',margin:0}}>
                            Your call log has unsaved content. Discard it?
                        </p>
                        <div style={{display:'flex',justifyContent:'flex-end',gap:10,padding:'12px 20px',background:'rgba(0,0,0,0.2)',borderTop:'1px solid rgba(255,255,255,0.06)'}}>
                            <button onClick={handleCancelDiscard} autoFocus style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'rgba(255,255,255,0.06)',border:'1.5px solid rgba(255,255,255,0.2)',color:'rgba(255,255,255,0.7)',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                                KEEP EDITING
                            </button>
                            <button onClick={handleConfirmDiscard} style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'#EE8C3A',border:'none',color:'#1a2e30',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                                DISCARD
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* CALL LOG MODAL */}
            <HardwareModal isOpen={callModal.open} onClose={handleCloseCallModal}
                title={`LOG CALL: ${callModal.mission?.plotNumber || ''}`}>
                <div className={styles.historyStream}>
                    <div className={styles.historyTitle}>PREVIOUS INTERACTIONS</div>
                    {callHistory.length === 0 ? (
                        <div className={styles.emptyHistory}>No prior logs found.</div>
                    ) : callHistory.slice(0, 5).map(log => (
                        <div key={log.id} className={styles.historyItem}>
                            <div className={styles.historyMeta}>
                                <span><FiUser aria-hidden="true" /> {log.recordedBy}</span>
                                <small>{new Date(log.timestamp).toLocaleDateString()}</small>
                            </div>
                            <p>{log.notes}</p>
                        </div>
                    ))}
                </div>
                <div className={modalStyles.modalField} style={{marginTop:14}}>
                    <label className={modalStyles.modalLabel}>CALL RESULT / NOTE</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="Enter call result or interaction note..."
                        value={logContent} onChange={e => setLogContent(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton loading={committing} onClick={handleLogCall} icon={FiSave}>
                        COMMIT &amp; RESET CLOCK
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default RecoveryPortal;""")

# ─── 5. OVERWRITE: RecoveryPortal.module.css ─────────────────────────────
css_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.module.css')
write(css_path, '''/* PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238,140,58,0.15);
    --orange-border: rgba(238,140,58,0.3);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg,#1c3335 0%,#213E40 100%);
    --red:           #ef4444;
    --emerald:       #10b981;
    --cyan:          #06b6d4;
    --gap-xl:   clamp(12px,1.8vw,20px);
    --gap-lg:   clamp(8px,1.2vw,14px);
    --gap-md:   clamp(6px,0.9vw,11px);
    --radius:   10px;
    --radius-sm:7px;
    --fs-label: clamp(8px,0.82vw,10px);
    --fs-meta:  clamp(9px,0.9vw,11px);
    --fs-value: clamp(11px,1.1vw,13px);
    --fs-phone: clamp(12px,1.2vw,14px);
    --fs-owner: clamp(14px,1.5vw,17px);
    --fs-demand:clamp(12px,1.4vw,16px);
    --fs-badge: clamp(7px,0.75vw,9px);
    --fs-btn:   clamp(9px,0.9vw,11px);
    --fs-note:  clamp(10px,1vw,12px);
    --fs-h1:    clamp(18px,2.5vw,24px);
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    font-family: 'DM Sans',sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

/* ── TOAST ── */
.toastContainer { position:fixed; bottom:20px; right:20px; z-index:99999; display:flex; flex-direction:column-reverse; gap:8px; max-width:380px; pointer-events:none; }
.toast { display:flex; align-items:flex-start; gap:10px; padding:12px 14px; border-radius:8px; box-shadow:0 6px 22px rgba(0,0,0,0.5); pointer-events:all; animation:toastIn 0.3s cubic-bezier(0.18,0.89,0.32,1.28) both; }
@keyframes toastIn { from{opacity:0;transform:translateX(40px)} to{opacity:1;transform:translateX(0)} }
.toast_success { background:rgba(16,185,129,0.95); border-left:4px solid #059669; color:#fff; }
.toast_error   { background:rgba(239,68,68,0.95);  border-left:4px solid #b91c1c; color:#fff; }
.toast_warn    { background:rgba(245,158,11,0.95); border-left:4px solid #b45309; color:#fff; }
.toast_info    { background:rgba(6,182,212,0.95);  border-left:4px solid #0369a1; color:#fff; }
.toastIcon  { font-size:15px; flex-shrink:0; margin-top:1px; }
.toastMsg   { font-family:'Space Mono',monospace; font-size:10px; font-weight:700; line-height:1.4; flex:1; min-width:0; word-break:break-word; }
.toastClose { background:transparent; border:none; color:inherit; opacity:0.6; cursor:pointer; padding:2px; font-size:13px; flex-shrink:0; }
.toastClose:hover { opacity:1; }

/* ── BOOT ── */
.bootScreen  { height:60vh; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px; }
.bootSpinner { width:36px; height:36px; border:3px solid rgba(238,140,58,0.15); border-top-color:#EE8C3A; border-radius:50%; animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.bootLabel   { font-family:'Cinzel',serif; font-size:11px; font-weight:700; letter-spacing:4px; color:#EE8C3A; text-transform:uppercase; }

/* ── HEADER ── */
.pageHeader {
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
    gap:clamp(10px,1.4vw,16px); margin-bottom:clamp(14px,2vw,24px);
    border-left:clamp(3px,0.4vw,5px) solid #EE8C3A;
    padding:clamp(10px,1.4vw,16px) clamp(16px,2.2vw,28px);
    background:rgba(255,255,255,0.62); border-radius:0 var(--radius) var(--radius) 0;
    backdrop-filter:blur(15px); box-shadow:0 4px 15px rgba(0,0,0,0.07);
    flex-shrink:0;
}
.headerLeft { display:flex; flex-direction:column; gap:3px; min-width:0; flex:1; }
.headerRight { display:flex; align-items:center; gap:clamp(8px,1.2vw,14px); flex-shrink:0; flex-wrap:wrap; }
.pageTitle { font-family:'Cinzel',serif; color:#1a2e30; font-size:var(--fs-h1); font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin:0; line-height:1.1; }
.pageSubtitle { font-family:'DM Sans',sans-serif; color:#64748b; font-size:clamp(8px,0.85vw,10px); font-weight:900; text-transform:uppercase; letter-spacing:1px; margin:0; }

/* ── MODE SWITCH ── */
.modeSwitch { display:flex; background:var(--navy); padding:4px; border-radius:var(--radius-sm); border:1px solid var(--orange-border); gap:3px; flex-wrap:nowrap; flex-shrink:0; }
.modeActive   { background:var(--orange); color:var(--navy); border:none; padding:clamp(6px,0.9vw,8px) clamp(10px,1.3vw,16px); border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:clamp(9px,1vw,11px); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; }
.modeInactive { background:transparent; color:rgba(255,255,255,0.75); border:none; padding:clamp(6px,0.9vw,8px) clamp(10px,1.3vw,16px); border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:clamp(9px,1vw,11px); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; transition:background 0.2s,color 0.2s; }
.modeInactive:hover { background:rgba(255,255,255,0.1); color:#fff; }

/* ── FINANCIAL HUD ── */
.finHUD {
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:var(--gap-md);
    margin-bottom:var(--gap-lg);
    flex-shrink: 0;
}
.finHUDCard {
    background:var(--panel-bg);
    border:1.5px solid var(--orange-border);
    border-radius:var(--radius);
    padding:clamp(12px,1.5vw,18px);
    display:flex; flex-direction:column; gap:4px;
}
.finHUDCard label { font-family:'DM Sans',sans-serif; font-size:var(--fs-badge); font-weight:900; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:1px; }
.finHUDCard strong { font-family:'Space Mono',monospace; font-size:clamp(15px,1.8vw,22px); font-weight:700; word-break:break-all; }
.finHUDCard span { font-size:var(--fs-badge); color:rgba(255,255,255,0.35); }

/* ── FILTER BAR — sticky so search+filters stay accessible after header scrolls ── */
.filterBar {
    display:flex; flex-direction:column; gap:var(--gap-md);
    margin-bottom:clamp(10px,1.3vw,14px);
    flex-shrink:0;
    position:sticky;
    top:0;
    z-index:200;
    background:transparent;
    padding:clamp(8px,1vw,12px) 0;
    margin-left:clamp(-12px,-2vw,-24px);
    margin-right:clamp(-12px,-2vw,-24px);
    padding-left:clamp(12px,2vw,24px);
    padding-right:clamp(12px,2vw,24px);
}
.searchInner {
    position:relative; display:flex; align-items:center;
    background:#fff; border:1.5px solid #c8d6d7;
    border-radius:var(--radius-sm);
    width:100%; max-width:clamp(300px,42vw,500px);
    height:clamp(36px,4vw,42px);
    transition:border-color 0.2s;
}
.searchInner:focus-within { border-color:var(--orange); box-shadow:0 0 0 3px rgba(238,140,58,0.15); }
.searchIcon { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--orange); font-size:16px; pointer-events:none; }
.searchInput {
    width:100%; border:none; outline:none; background:transparent;
    color:var(--navy); padding-right:34px !important; padding-left:42px !important;
    font-family:'DM Sans',sans-serif; font-weight:800; font-size:clamp(11px,1.1vw,13px);
    height:100%; transition:padding 0.2s ease;
}
.searchInputActive { padding-left:14px !important; }
.searchInput::placeholder { font-weight:500; color:rgba(26,46,48,0.35); }
.searchClear { position:absolute; right:8px; top:50%; transform:translateY(-50%); background:transparent; border:none; cursor:pointer; color:rgba(26,46,48,0.4); display:flex; align-items:center; padding:3px; border-radius:4px; }
.searchClear:hover { color:var(--navy); }

.filterPills { display:flex; flex-wrap:nowrap; overflow-x:auto; gap:clamp(6px,0.8vw,10px); scrollbar-width:none; padding-bottom:2px; }
.filterPills::-webkit-scrollbar { display:none; }
.filterPill {
    background:rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(6px,0.8vw,8px) clamp(12px,1.4vw,18px);
    border-radius:var(--radius-sm);
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size:clamp(9px,0.9vw,11px); letter-spacing:1.5px;
    text-transform:uppercase; cursor:pointer; white-space:nowrap;
    transition:all 0.2s ease; flex-shrink:0;
}
.filterPill:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.filterPillActive { background: #EE8C3A !important; color: #1a2e30 !important; border-color: #EE8C3A !important; box-shadow: 0 0 12px rgba(238, 140, 58, 0.35); }

/* ── LEGEND ── */
.legend {
    display:flex; flex-wrap:wrap; gap:clamp(10px,1.5vw,18px);
    margin-bottom:clamp(8px,1vw,12px);
    padding:clamp(6px,0.8vw,9px) 0;
    flex-shrink:0;
}
.legendItem {
    display:flex; align-items:center; gap:clamp(5px,0.6vw,7px);
    font-family:'DM Sans',sans-serif; font-size:clamp(9px,0.9vw,11px);
    font-weight:800; color:rgba(26, 46, 48, 0.7); white-space:nowrap;
}

/* ── SECTION GROUPS ── */
.sectionGroup {
    margin-bottom: clamp(24px, 3.2vw, 40px);
    display: flex;
    flex-direction: column;
    gap: clamp(10px, 1.3vw, 16px);
}
.sectionHeader {
    font-family:'DM Sans',sans-serif; font-size:clamp(9px,0.95vw,11px);
    font-weight:900; color:#fff; text-transform:uppercase; letter-spacing:2px;
    margin-bottom:var(--gap-md);
    display:inline-flex; align-items:center; gap:8px;
    padding:clamp(6px,0.8vw,10px) clamp(12px,1.5vw,20px);
    border-radius:6px; background:rgba(26,46,48,0.75);
    border:1px solid rgba(238,140,58,0.25);
    align-self: flex-start; /* Prevent stretching */
}
.sectionHeaderBacklog { color:#fca5a5; background:rgba(127,29,29,0.5); border-color:rgba(239,68,68,0.35); }

/* ── MISSION GRID ── */
.missionGrid { display:flex; flex-direction:column; gap:clamp(16px,2vw,24px); }

/* ── MISSION CARD ── */
.missionCard {
    background:var(--panel-bg);
    border:1.5px solid rgba(238,140,58,0.2);
    border-radius:var(--radius);
    box-shadow:0 6px 20px rgba(0,0,0,0.18);
    transition:border-color 0.2s, box-shadow 0.2s;
    overflow:hidden; width:100%;
}
.missionCard:hover { border-color:rgba(238,140,58,0.5); box-shadow:0 8px 26px rgba(0,0,0,0.25); }
.cardLocked  { opacity:0.7; border-style:dashed; }
.cardBacklog { border-color:rgba(239,68,68,0.3); }
.cardBacklog:hover { border-color:rgba(239,68,68,0.6); }

/* ── STATUS BADGE ── */
.statusBadge {
    float:right; display:inline-flex; align-items:center; gap:5px;
    padding:6px 12px; font-family:'DM Sans',sans-serif;
    font-size:clamp(8px,0.8vw,10px); font-weight:900; letter-spacing:0.8px;
    text-transform:uppercase;
}
.statusRed     { color:#fca5a5; }
.statusBlue    { color:#93c5fd; }
.statusGrey    { color:rgba(255,255,255,0.4); }
.statusDefault { color:rgba(255,255,255,0.5); }

/* ── CARD HEADER (compact closed view) ── */
.cardHeader {
    display:flex; justify-content:space-between; align-items:flex-start;
    padding:clamp(12px,1.5vw,18px) var(--pad-card);
    cursor:pointer; user-select:none; clear:both; gap:12px;
}
.cardHeader:focus-visible { outline:2px solid var(--orange); outline-offset:-2px; border-radius:var(--radius); }

.cardMain { display:flex; flex-direction:column; gap:clamp(4px,0.6vw,8px); min-width:0; flex:1; }

.cardTopRow { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.plotId { font-family:'Space Mono',monospace; color:var(--orange); font-size:clamp(14px,1.6vw,20px); font-weight:900; letter-spacing:0.5px; }
.backlogPill {
    font-family:'DM Sans',sans-serif; font-size:8px; font-weight:900;
    text-transform:uppercase; letter-spacing:0.8px;
    background:rgba(239,68,68,0.2); border:1px solid rgba(239,68,68,0.45);
    border-radius:4px; padding:2px 8px; color:#fca5a5; flex-shrink:0;
}
.ownerLine { font-family:'Cinzel',serif; color:#fff; font-size:clamp(14px,1.6vw,18px); font-weight:700; letter-spacing:0.5px; }
.phoneLine { font-family:'Space Mono',monospace; color:rgba(255,255,255,0.55); font-size:clamp(11px,1.2vw,14px); font-weight:700; }
.balanceLine { display:flex; align-items:center; gap:8px; margin-top:2px; }
.balanceLabel { font-family:'DM Sans',sans-serif; font-size:clamp(9px,0.9vw,11px); font-weight:900; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:1px; white-space:nowrap; }
.balanceVal { font-family:'Space Mono',monospace; font-size:clamp(14px,1.6vw,18px); font-weight:900; color:#fff; }
.balanceRed { color:#fca5a5; }

.cardSideActions { display:flex; flex-direction:column; align-items:flex-end; gap:10px; flex-shrink:0; }
.logCallBtnSmall {
    background:var(--orange); color:var(--navy); border:none;
    border-radius:var(--radius-sm); font-family:'DM Sans',sans-serif; font-weight:900;
    font-size:clamp(9px,0.95vw,11px); text-transform:uppercase; letter-spacing:1px;
    padding:clamp(8px,1.1vw,12px) clamp(12px,1.5vw,18px); cursor:pointer;
    display:flex; align-items:center; justify-content:center; gap:6px;
    transition:background 0.2s; white-space:nowrap;
}
.logCallBtnSmall:hover:not(:disabled) { background:#d4732a; }
.logCallBtnSmall:disabled { background:transparent; color:rgba(255,255,255,0.25); border:1.5px solid rgba(255,255,255,0.1); cursor:not-allowed; font-size:clamp(8px,0.85vw,10px); }
.expandIcon { color:rgba(255,255,255,0.4); font-size:22px; transition:color 0.2s; margin-top:4px; }
.missionCard:hover .expandIcon { color:var(--orange); }

/* ── CARD BODY (expanded) ── */
.cardBody { padding:0 var(--pad-card) var(--pad-card); }
.divider  { height:1px; background:rgba(238,140,58,0.18); margin:clamp(10px,1.3vw,16px) 0; }

.timingRow {
    display:flex; align-items:center; flex-wrap:wrap; gap:8px;
    font-size:clamp(10px,1vw,12px); color:#e2e8f0; font-weight:700;
    background:rgba(0,0,0,0.3); padding:10px 14px; border-radius:6px;
    border:1px solid rgba(255,255,255,0.06); margin-bottom:12px;
}
.timingRow strong { color:#fff; }
.timingSep { width:1px; height:14px; background:rgba(255,255,255,0.2); flex-shrink:0; }

/* ── FINANCIAL DETAIL (expanded) ── */
.finDetail {
    background:rgba(0,0,0,0.25); border-radius:6px;
    padding:clamp(10px,1.2vw,14px); margin-bottom:12px;
    display:flex; flex-direction:column; gap:7px;
}
.finDetailRow {
    display:flex; justify-content:space-between; align-items:baseline; gap:12px;
    font-family:'DM Sans',sans-serif; font-size:clamp(11px,1.1vw,13px); font-weight:700;
    color:rgba(255,255,255,0.7);
}
.finDetailRow strong { font-family:'Space Mono',monospace; color:#fff; font-size:clamp(12px,1.2vw,14px); }
.finDetailTotal {
    border-top:1px solid rgba(255,255,255,0.1);
    padding-top:7px; margin-top:4px;
    font-weight:900;
}
.finDetailTotal span { color:rgba(255,255,255,0.9); font-weight:900; text-transform:uppercase; letter-spacing:0.5px; }

.lastNote { display:flex; align-items:flex-start; gap:6px; font-size:clamp(10px,1vw,12px); color:rgba(255,255,255,0.45); font-style:italic; font-weight:600; line-height:1.4; margin-bottom:14px; }

.expandedActions { display:flex; gap:10px; flex-wrap:wrap; }
.folderBtn {
    background:rgba(255,255,255,0.1); border:1.5px solid rgba(255,255,255,0.25);
    color:#fff; font-family:'DM Sans',sans-serif; font-weight:900;
    border-radius:var(--radius-sm); font-size:clamp(9px,0.95vw,11px);
    padding:clamp(7px,0.9vw,10px) clamp(12px,1.5vw,18px);
    cursor:pointer; display:inline-flex; align-items:center; justify-content:center;
    gap:5px; transition:all 0.2s; white-space:nowrap;
}
.folderBtn:hover { border-color:var(--orange); color:var(--orange); background:rgba(238,140,58,0.1); }
.payBtn {
    background:rgba(34,197,94,0.15); border:1.5px solid rgba(34,197,94,0.45);
    color:#4ade80; font-family:'DM Sans',sans-serif; font-weight:900;
    border-radius:var(--radius-sm); font-size:clamp(9px,0.95vw,11px);
    padding:clamp(7px,0.9vw,10px) clamp(12px,1.5vw,18px);
    cursor:pointer; display:inline-flex; align-items:center; justify-content:center;
    gap:5px; transition:all 0.2s; white-space:nowrap;
}
.payBtn:hover { background:#22c55e; color:#1a2e30; border-color:#22c55e; }

/* ── CALL MODAL ── */
.historyStream { max-height:160px; overflow-y:auto; background:#f8fafc; border-radius:8px; padding:10px; margin-bottom:12px; border:1px solid #e2e8f0; scrollbar-width:thin; }
.historyTitle  { font-family:'DM Sans',sans-serif; font-size:9px; font-weight:900; color:#475569; margin-bottom:8px; border-bottom:1px solid #e2e8f0; padding-bottom:5px; text-transform:uppercase; letter-spacing:1px; }
.historyItem   { border-bottom:1px solid #f1f5f9; padding-bottom:7px; margin-bottom:7px; }
.historyItem:last-child { border-bottom:none; margin-bottom:0; }
.historyMeta   { display:flex; justify-content:space-between; align-items:center; font-family:'DM Sans',sans-serif; font-size:10px; font-weight:800; color:#c2410c; margin-bottom:3px; }
.historyItem p { font-family:'DM Sans',sans-serif; font-size:12px; color:#1a2e30; line-height:1.5; font-weight:600; margin:0; }
.emptyHistory  { font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700; color:#94a3b8; text-align:center; padding:16px 0; }

/* ── EMPTY STATE ── */
.emptyGate {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    gap:16px; padding:clamp(40px,8vw,80px) 20px; text-align:center;
    background:rgba(26,46,48,0.35); border:1.5px solid rgba(238,140,58,0.15);
    border-radius:12px;
}
.emptyIcon  { font-size:clamp(40px,6vw,60px); color:#10b981; opacity:0.4; }
.emptyTitle { font-family:'Cinzel',serif; font-size:clamp(14px,1.8vw,20px); font-weight:700; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:2px; margin:0; }

/* ── RESPONSIVE ── */
@media (max-width:900px) {
    .finHUD { grid-template-columns:repeat(3,1fr); }
    .pageHeader { flex-direction:column; align-items:flex-start; }
    .headerRight { width:100%; }
    .modeSwitch { width:100%; }
    .modeActive,.modeInactive { flex:1; justify-content:center; }
}
@media (max-width:640px) {
    .finHUD { grid-template-columns:1fr 1fr; }
    .finHUD .finHUDCard:last-child { grid-column:1/-1; }
    .cardHeader { flex-direction:column; gap:12px; }
    .cardSideActions { flex-direction:row; align-items:center; width:100%; justify-content:space-between; }
    .logCallBtnSmall { flex:1; }
}
@media (max-width:480px) {
    .finHUD { grid-template-columns:1fr; }
    .finHUD .finHUDCard:last-child { grid-column:1; }
    .finDetailRow { font-size:11px; }
    .plotId { font-size:14px; }
    .ownerLine { font-size:13px; }
}
''')

print("\n=== COMPLETE ===")git add -A && git commit -m "recovery" && git push