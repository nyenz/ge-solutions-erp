import os

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

BASE = os.path.dirname(os.path.abspath(__file__))

# ── RecoveryPortal.jsx ───────────────────────────────────────────────
RECOVERY_JSX = r"""import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch,
    FiSave, FiList, FiCalendar,
    FiChevronDown, FiChevronUp,
    FiDollarSign, FiAlertOctagon, FiActivity
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = {
    GREEN:  'Paid within 14 days',
    YELLOW: 'Paid within 30 days',
    RED:    'No recent payment',
};

const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;

    const [viewMode,     setViewMode]     = useState('ACTION');
    const [missions,     setMissions]     = useState([]);
    const [loading,      setLoading]      = useState(true);
    const [expandedId,   setExpandedId]   = useState(null);
    const [searchTerm,   setSearchTerm]   = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');
    const [callModal,    setCallModal]    = useState({ open: false, mission: null, lastNote: '' });
    const [logContent,   setLogContent]   = useState('');
    const [committing,   setCommitting]   = useState(false);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION'
                ? await recoveryService.getMissionQueue()
                : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch { /* silent */ }
        finally { setLoading(false); }
    }, [viewMode]);

    useEffect(() => { loadData(); }, [loadData]);

    const filteredMissions = useMemo(() => {
        let list = missions;
        if (searchTerm.trim()) {
            const t = searchTerm.toLowerCase();
            list = list.filter(m =>
                m.ownerName.toLowerCase().includes(t) ||
                m.phoneNumber.includes(t) ||
                m.plots.some(p => p.plotNumber.toLowerCase().includes(t))
            );
        }
        if (statusFilter === 'BACKLOG') list = list.filter(m => m.hasBacklogPlots);
        if (statusFilter === 'ACTIVE')  list = list.filter(m => !m.hasBacklogPlots);
        return list;
    }, [missions, searchTerm, statusFilter]);

    const totalActiveOwed  = missions.filter(m => !m.hasBacklogPlots).reduce((s, m) => s + Number(m.totalDemand || 0), 0);
    const totalBacklogOwed = missions.filter(m =>  m.hasBacklogPlots).reduce((s, m) => s + Number(m.totalDemand || 0), 0);
    const totalStorageFees = missions.reduce((s, m) => s + Number(m.totalStorageFees || 0), 0);

    const handleLogCall = async () => {
        if (!callModal.mission) return;
        setCommitting(true);
        try {
            await recoveryService.logRecoveryCall(callModal.mission.projectId, logContent);
            setCallModal({ open: false, mission: null, lastNote: '' });
            setLogContent('');
            loadData();
        } catch { /* silent */ }
        finally { setCommitting(false); }
    };

    const openCallModal = (e, plot) => {
        e.stopPropagation();
        const lastNote = plot.lastInteractionNote || 'NO PRIOR CONTACT';
        setCallModal({ open: true, mission: plot, lastNote });
        setLogContent('');
    };

    return (
        <div className={styles.container}>

            {/* HEADER */}
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Call Recovery</h1>
                    <p className={styles.pageSubtitle}>Log client calls and record payments</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.modeSwitch}>
                        <button
                            className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive}
                            onClick={() => setViewMode('ACTION')}
                        >
                            <FiList aria-hidden="true" /> DUE FOR CALL
                        </button>
                        <button
                            className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive}
                            onClick={() => setViewMode('FORECAST')}
                        >
                            <FiCalendar aria-hidden="true" /> ALL TARGETS
                        </button>
                    </div>
                </div>
            </header>

            {/* FINANCIAL HUD */}
            <div className={styles.finHUD}>
                <div className={styles.finHUDCard}>
                    <label>ACTIVE TITLES OWED</label>
                    <strong>UGX {fmt(totalActiveOwed)}</strong>
                </div>
                <div className={styles.finHUDCard}>
                    <label>BACKLOG TOTAL OWED</label>
                    <strong>UGX {fmt(totalBacklogOwed)}</strong>
                </div>
                <div className={styles.finHUDCard}>
                    <label>STORAGE FEES</label>
                    <strong>UGX {fmt(totalStorageFees)}</strong>
                </div>
            </div>

            {/* FILTER BAR */}
            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <FiSearch className={styles.searchIcon} aria-hidden="true" />
                    <input
                        className={styles.searchInput}
                        type="search"
                        placeholder="Search owner name, plot ID, phone..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        aria-label="Search recovery missions"
                    />
                </div>
                <div className={styles.filterPills} role="group" aria-label="Filter missions">
                    {['ALL', 'ACTIVE', 'BACKLOG'].map(f => (
                        <button
                            key={f}
                            className={`${styles.filterPill} ${statusFilter === f ? styles.filterPillActive : ''}`}
                            onClick={() => setStatusFilter(f)}
                            aria-pressed={statusFilter === f}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* BADGE LEGEND */}
            <div className={styles.legend} aria-label="Payment health legend">
                {Object.entries(BADGE_COLORS).map(([k, c]) => (
                    <span key={k} className={styles.legendItem}>
                        <span style={{ width: 9, height: 9, borderRadius: '50%', background: c, display: 'inline-block', flexShrink: 0, boxShadow: `0 0 4px ${c}` }} />
                        {BADGE_LABELS[k]}
                    </span>
                ))}
            </div>

            {/* MISSION LIST */}
            {loading ? (
                <div className={styles.emptyState} role="status">
                    <div className={styles.loadingSpinner} aria-hidden="true" />
                    <span>LOADING RECOVERY QUEUE...</span>
                </div>
            ) : filteredMissions.length === 0 ? (
                <div className={styles.emptyState} role="status">
                    <FiActivity className={styles.emptyIcon} aria-hidden="true" />
                    <span>{searchTerm ? `NO MISSIONS MATCH "${searchTerm.toUpperCase()}"` : 'NO MISSIONS IN QUEUE'}</span>
                </div>
            ) : (
                <div className={styles.missionGrid}>
                    {filteredMissions.map(m => {
                        const isExpanded = expandedId === m.clientId;
                        const badgeColor = BADGE_COLORS[m.plots[0]?.paymentHealthBadge] || '#ef4444';
                        return (
                            <div
                                key={m.clientId}
                                className={`${styles.missionCard} ${m.hasBacklogPlots ? styles.cardBacklog : ''}`}
                            >
                                {/* CARD HEADER */}
                                <div
                                    className={styles.cardHeader}
                                    onClick={() => setExpandedId(isExpanded ? null : m.clientId)}
                                    role="button"
                                    tabIndex={0}
                                    aria-expanded={isExpanded}
                                    aria-label={`${m.ownerName} — ${isExpanded ? 'collapse' : 'expand'}`}
                                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedId(isExpanded ? null : m.clientId); } }}
                                >
                                    {/* ROW 1: Plot ID + Balance */}
                                    <div className={styles.cardTopRow}>
                                        <div className={styles.cardTopRowLeft}>
                                            <span
                                                style={{ width: 9, height: 9, borderRadius: '50%', background: badgeColor, display: 'inline-block', flexShrink: 0, boxShadow: `0 0 5px ${badgeColor}` }}
                                                title={BADGE_LABELS[m.plots[0]?.paymentHealthBadge]}
                                            />
                                            <span className={styles.plotId}>
                                                {m.plots.map(p => p.plotNumber).join(' / ')}
                                            </span>
                                            {m.hasBacklogPlots && (
                                                <span className={styles.backlogPill}>BACKLOG</span>
                                            )}
                                        </div>
                                        <div className={styles.balanceLine}>
                                            <span className={styles.balanceLabel}>TOTAL OWED</span>
                                            <span className={`${styles.balanceVal} ${m.hasBacklogPlots ? styles.balanceRed : ''}`}>
                                                UGX {fmt(m.totalDemand)}
                                            </span>
                                        </div>
                                    </div>

                                    {/* ROW 2: Owner + Phone + Actions */}
                                    <div className={styles.cardMain}>
                                        <div className={styles.ownerPhoneBlock}>
                                            <span className={styles.ownerLine}>{m.ownerName}</span>
                                            <span className={styles.phoneLine}>{m.phoneNumber}</span>
                                        </div>
                                        <div className={styles.cardSideActions}>
                                            <button
                                                className={styles.logCallBtnSmall}
                                                disabled={m.isLocked}
                                                onClick={e => openCallModal(e, m.plots[0])}
                                                aria-label={m.isLocked ? 'Call locked' : `Log call for ${m.ownerName}`}
                                            >
                                                <FiPhoneCall aria-hidden="true" />
                                                {m.isLocked ? 'LOCKED' : 'LOG CALL'}
                                            </button>
                                            {isExpanded
                                                ? <FiChevronUp  className={styles.expandIcon} aria-hidden="true" />
                                                : <FiChevronDown className={styles.expandIcon} aria-hidden="true" />
                                            }
                                        </div>
                                    </div>
                                </div>

                                {/* EXPANDED BODY */}
                                {isExpanded && (
                                    <div className={styles.cardBody}>
                                        <div className={styles.timingRow}>
                                            <FiClock aria-hidden="true" />
                                            <span>Last contact: <strong>{m.lastContactDate}</strong></span>
                                            <span>Next due: <strong>{m.nextCallDue}</strong></span>
                                            <span>This month: <strong>{m.monthlyCallCount}/2</strong></span>
                                        </div>

                                        {m.plots.map(p => {
                                            // UNIFIED FINANCIAL MATH:
                                            // TOTAL VALUE = totalCost (active) or originalDebt (backlog baseline)
                                            // AMOUNT OWED = totalCost + storageFees - amountPaid
                                            const totalValue = Number(
                                                p.isBacklog
                                                    ? (p.originalDebt || p.totalCost || 0)
                                                    : (p.totalCost || 0)
                                            );
                                            const amtPaid = Number(p.amountPaid || 0);
                                            const storageFees = Number(p.storageFeesAccumulated || 0);
                                            const amountOwed = Number(
                                                p.isBacklog
                                                    ? (p.totalBacklogOwed || Math.max(0, totalValue + storageFees - amtPaid))
                                                    : (p.currentBalance || Math.max(0, totalValue - amtPaid))
                                            );

                                            return (
                                            <div key={p.projectId} className={styles.plotSubCard}>
                                                <div className={styles.plotSubCardHeader}>
                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>
                                                    <span className={styles.plotSubCardBox}>BOX: {p.physicalBoxNumber || '---'}</span>
                                                </div>

                                                {/* LAST INTERACTION NOTE — notebook style */}
                                                {p.lastInteractionNote && p.lastInteractionNote !== 'NO PRIOR CONTACT' && (
                                                    <div className={styles.interactionNote}>
                                                        <span className={styles.interactionNoteLabel}>LAST CONTACT NOTE</span>
                                                        <p className={styles.interactionNoteText}>{p.lastInteractionNote}</p>
                                                    </div>
                                                )}

                                                {/* Financial breakdown: TOTAL VALUE + STORAGE FEES - PAID = AMOUNT OWED */}
                                                <div className={styles.finBreakdown}>
                                                    <div className={styles.finRow}>
                                                        <span className={styles.finLabel}>TOTAL VALUE</span>
                                                        <span className={styles.finValWhite}>UGX {fmt(totalValue)}</span>
                                                    </div>
                                                    {p.isBacklog && storageFees > 0 && (
                                                        <div className={styles.finRow}>
                                                            <span className={styles.finLabel}>+ STORAGE FEES</span>
                                                            <span className={styles.finValOrange}>UGX {fmt(storageFees)}</span>
                                                        </div>
                                                    )}
                                                    <div className={styles.finRow}>
                                                        <span className={styles.finLabel}>PAID</span>
                                                        <span className={styles.finValGreen}>UGX {fmt(amtPaid)}</span>
                                                    </div>
                                                    <div className={styles.finRowTotal}>
                                                        <span className={styles.finLabelTotal}>AMOUNT OWED</span>
                                                        <span className={styles.finValRed}>UGX {fmt(amountOwed)}</span>
                                                    </div>
                                                </div>

                                                <div className={styles.expandedActions}>
                                                    <button
                                                        className={styles.folderBtn}
                                                        onClick={() => navigate(`/folder/${p.projectId}`)}
                                                    >
                                                        OPEN FOLDER
                                                    </button>
                                                    {isAdmin && (
                                                        <button
                                                            className={styles.payBtn}
                                                            onClick={() => navigate(`/folder/${p.projectId}?action=pay`)}
                                                        >
                                                            <FiDollarSign aria-hidden="true" /> RECORD PAYMENT
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* LOG CALL MODAL */}
            <HardwareModal
                isOpen={callModal.open}
                onClose={() => { setCallModal({ open: false, mission: null, lastNote: '' }); setLogContent(''); }}
                title={callModal.mission ? `LOG CALL — ${callModal.mission.plotNumber}` : 'LOG CALL'}
            >
                {/* Last interaction note — notebook style */}
                {callModal.lastNote && callModal.lastNote !== 'NO PRIOR CONTACT' && (
                    <div className={styles.modalInteractionNote}>
                        <span className={styles.modalInteractionNoteLabel}>LAST INTERACTION NOTE</span>
                        <p className={styles.modalInteractionNoteText}>{callModal.lastNote}</p>
                    </div>
                )}
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>INTERACTION NOTES</label>
                    <textarea
                        className={modalStyles.modalTextarea}
                        value={logContent}
                        onChange={e => setLogContent(e.target.value)}
                        placeholder="e.g. Client confirmed payment by Friday, awaiting bank transfer..."
                        autoFocus
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button
                        type="button"
                        className={modalStyles.modalBtnSecondary}
                        onClick={() => { setCallModal({ open: false, mission: null, lastNote: '' }); setLogContent(''); }}
                    >
                        CANCEL
                    </button>
                    <HardwareButton onClick={handleLogCall} loading={committing} icon={FiSave}>
                        SAVE LOG
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default RecoveryPortal;
"""

# ── RecoveryPortal.module.css ────────────────────────────────────────
RECOVERY_CSS = """/* PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --panel-border:  rgba(238, 140, 58, 0.2);
    --red:           #ef4444;
    --green:         #10b981;
    --cyan:          #06b6d4;

    --gap-xl:   clamp(14px, 2vw, 24px);
    --gap-lg:   clamp(10px, 1.5vw, 18px);
    --gap-md:   clamp(7px,  1.1vw, 13px);
    --radius:   12px;
    --radius-sm: 7px;

    --fs-h1:    clamp(18px, 2.5vw, 24px);
    --fs-sub:   clamp(8px,  0.85vw, 10px);
    --fs-label: clamp(7px,  0.75vw, 9px);
    --fs-value: clamp(13px, 1.4vw, 17px);
    --fs-tag:   clamp(7px,  0.78vw, 9px);
    --fs-td:    clamp(11px, 1.15vw, 13px);
    --fs-meta:  clamp(9px,  0.95vw, 11px);
    --fs-btn:   clamp(9px,  0.9vw,  11px);

    max-width: 1400px;
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    gap: 0;
    box-sizing: border-box;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}

@keyframes warmBoot {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── PAGE HEADER ── */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 22px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 var(--radius) var(--radius) 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
    flex-shrink: 0;
}
.headerLeft  { display: flex; flex-direction: column; gap: clamp(3px, 0.4vw, 5px); flex: 1; min-width: 0; }
.headerRight { display: flex; align-items: center; gap: clamp(8px, 1.2vw, 14px); flex-shrink: 0; flex-wrap: wrap; }
.pageTitle   { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0; line-height: 1; }
.pageSubtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

/* ── MODE SWITCH ── */
.modeSwitch {
    display: flex;
    background: rgba(26, 46, 48, 0.85);
    padding: clamp(3px, 0.4vw, 5px);
    border-radius: var(--radius-sm);
    border: 1.5px solid var(--orange-border);
    gap: clamp(4px, 0.5vw, 6px);
}
.modeActive {
    background: #EE8C3A;
    color: #1a2e30;
    border: none;
    padding: clamp(7px, 0.9vw, 10px) clamp(12px, 1.5vw, 18px);
    border-radius: calc(var(--radius-sm) - 2px);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 8px);
    white-space: nowrap;
    transition: background 0.2s;
}
.modeActive:hover { background: #f0a050; }
.modeInactive {
    background: transparent;
    color: rgba(255, 255, 255, 0.6);
    border: none;
    padding: clamp(7px, 0.9vw, 10px) clamp(12px, 1.5vw, 18px);
    border-radius: calc(var(--radius-sm) - 2px);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 8px);
    white-space: nowrap;
    transition: color 0.2s, background 0.2s;
}
.modeInactive:hover { color: #fff; background: rgba(255, 255, 255, 0.06); }
.modeActive:focus-visible, .modeInactive:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── FIN HUD CARDS ── */
.finHUD {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--gap-lg);
    margin-bottom: var(--gap-xl);
    flex-shrink: 0;
}
.finHUDCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--panel-border);
    border-radius: var(--radius);
    padding: clamp(14px, 2vw, 22px) clamp(16px, 2.2vw, 26px);
    display: flex;
    flex-direction: column;
    gap: clamp(4px, 0.5vw, 6px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    transition: border-color 0.2s, transform 0.2s;
}
.finHUDCard:hover { border-color: var(--orange); transform: translateY(-2px); }
.finHUDCard label {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.finHUDCard strong {
    font-family: 'Space Mono', monospace;
    font-size: clamp(15px, 1.8vw, 21px);
    font-weight: 700;
    color: #fff;
    word-break: break-all;
    line-height: 1.2;
}

/* ── FILTER BAR ── */
.filterBar {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: var(--gap-lg);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: transparent;
    padding: clamp(8px, 1vw, 12px) 0;
    margin-left: clamp(-12px, -2vw, -24px);
    margin-right: clamp(-12px, -2vw, -24px);
    padding-left: clamp(12px, 2vw, 24px);
    padding-right: clamp(12px, 2vw, 24px);
}

.searchInner {
    position: relative;
    display: flex;
    align-items: center;
    background: #fff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    height: clamp(36px, 4.5vw, 44px);
    max-width: clamp(320px, 55vw, 560px);
    width: 100%;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.searchInner:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.18); }
.searchIcon {
    position: absolute;
    left: clamp(10px, 1.2vw, 14px);
    top: 50%;
    transform: translateY(-50%);
    color: var(--orange);
    font-size: clamp(14px, 1.6vw, 18px);
    pointer-events: none;
    flex-shrink: 0;
}
.searchInput {
    width: 100%;
    border: none;
    outline: none;
    background: transparent;
    color: #1a2e30;
    padding: 0 clamp(10px, 1.2vw, 14px) 0 clamp(36px, 4.5vw, 44px) !important;
    font-family: 'DM Sans', sans-serif;
    font-weight: 800;
    font-size: clamp(11px, 1.1vw, 13px);
    height: 100%;
}
.searchInput::placeholder { font-weight: 500; color: rgba(26, 46, 48, 0.3); }

/* Filter pills */
.filterPills {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: clamp(6px, 0.9vw, 10px);
    scrollbar-width: none;
    padding-bottom: 2px;
}
.filterPills::-webkit-scrollbar { display: none; }

.filterPill {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(12px, 1.5vw, 18px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    flex-shrink: 0;
}
.filterPill:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.filterPillActive {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    box-shadow: 0 0 12px rgba(238, 140, 58, 0.35);
}
.filterPill:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── BADGE LEGEND ── */
.legend {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(12px, 1.8vw, 20px);
    padding: clamp(6px, 0.8vw, 8px) 0;
    margin-bottom: var(--gap-lg);
    flex-shrink: 0;
}
.legendItem {
    display: flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 8px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 800;
    color: rgba(26, 46, 48, 0.65);
    white-space: nowrap;
}

/* ── MISSION GRID ── */
.missionGrid {
    display: flex;
    flex-direction: column;
    gap: var(--gap-lg);
}

/* ── MISSION CARD ── */
.missionCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--panel-border);
    border-radius: var(--radius);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.18);
    overflow: hidden;
    transition: border-color 0.22s, box-shadow 0.22s, transform 0.22s;
}
.missionCard:hover {
    border-color: rgba(238, 140, 58, 0.45);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.28);
    transform: translateY(-2px);
}
.cardBacklog {
    border-color: rgba(239, 68, 68, 0.35) !important;
    border-left: clamp(3px, 0.4vw, 5px) solid rgba(239, 68, 68, 0.6) !important;
}
.cardBacklog:hover { border-color: rgba(239, 68, 68, 0.6) !important; }

/* Card header */
.cardHeader {
    display: flex;
    flex-direction: column;
    gap: clamp(10px, 1.3vw, 14px);
    padding: clamp(16px, 2.2vw, 24px) clamp(18px, 2.5vw, 28px);
    cursor: pointer;
    user-select: none;
    transition: background 0.15s;
}
.cardHeader:hover { background: rgba(255, 255, 255, 0.025); }

/* Top row: plot ID + balance */
.cardTopRow {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: clamp(10px, 1.4vw, 16px);
    flex-wrap: wrap;
}
.cardTopRowLeft {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    min-width: 0;
    flex: 1;
}
.plotId {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-value);
    font-weight: 900;
    color: var(--orange);
    letter-spacing: 0.5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.backlogPill {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.45);
    color: #fca5a5;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(7px, 0.75vw, 8px);
    font-weight: 900;
    padding: clamp(2px, 0.3vw, 3px) clamp(7px, 0.9vw, 10px);
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 1px;
    white-space: nowrap;
    flex-shrink: 0;
}
.balanceLine {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: clamp(2px, 0.3vw, 3px);
    flex-shrink: 0;
}
.balanceLabel {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.35);
    text-transform: uppercase;
    letter-spacing: 1px;
}
/* BOLD WHITE prominent total owed */
.balanceVal {
    font-family: 'Space Mono', monospace;
    font-size: clamp(16px, 2vw, 22px);
    font-weight: 900;
    color: #fff;
    letter-spacing: 0.3px;
}
.balanceRed {
    color: #fca5a5 !important;
    text-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
}

/* Main row: owner + phone + actions */
.cardMain {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: clamp(10px, 1.4vw, 16px);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding-top: clamp(10px, 1.3vw, 14px);
    flex-wrap: wrap;
}

/* Owner + phone stacked together */
.ownerPhoneBlock {
    display: flex;
    flex-direction: column;
    gap: clamp(4px, 0.5vw, 6px);
    flex: 1;
    min-width: 0;
}

/* Owner name — large, bold */
.ownerLine {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-td);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.9);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

/* Phone — SAME SIZE AND WEIGHT as owner name (the most important call tool) */
.phoneLine {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 900;
    color: var(--orange);
    white-space: nowrap;
    letter-spacing: 0.5px;
}

.cardSideActions {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1.1vw, 12px);
    flex-shrink: 0;
}
.expandIcon {
    color: rgba(255, 255, 255, 0.3);
    font-size: clamp(16px, 1.8vw, 20px);
    transition: color 0.2s;
    flex-shrink: 0;
}
.cardHeader:hover .expandIcon { color: var(--orange); }

/* Log call button */
.logCallBtnSmall {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(34px, 4vw, 40px);
    padding: 0 clamp(12px, 1.6vw, 18px);
    background: #EE8C3A;
    border: none;
    color: #1a2e30;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, box-shadow 0.2s;
    box-shadow: 0 3px 10px rgba(238, 140, 58, 0.3);
}
.logCallBtnSmall:hover:not(:disabled) {
    background: #f0a050;
    box-shadow: 0 0 18px rgba(238, 140, 58, 0.5);
}
.logCallBtnSmall:disabled {
    background: rgba(255, 255, 255, 0.08);
    border: 1.5px solid rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.3);
    cursor: not-allowed;
    box-shadow: none;
}
.logCallBtnSmall:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── CARD BODY (expanded) ── */
.cardBody {
    padding: 0 clamp(18px, 2.5vw, 28px) clamp(18px, 2.5vw, 24px);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(0, 0, 0, 0.12);
}

.timingRow {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(8px, 1.2vw, 14px);
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: clamp(9px, 1.2vw, 12px) clamp(12px, 1.5vw, 16px);
    border-radius: var(--radius-sm);
    margin: clamp(12px, 1.6vw, 16px) 0;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-meta);
    font-weight: 800;
    color: rgba(255, 255, 255, 0.45);
    letter-spacing: 0.3px;
}
.timingRow strong { color: #fff; font-weight: 900; }
.timingRow svg { color: var(--orange); flex-shrink: 0; }

/* ── INTERACTION NOTE — notebook style (white bg, navy text, orange left border) ── */
.interactionNote {
    background: #ffffff;
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    border-radius: 0 4px 4px 0;
    padding: clamp(8px, 1vw, 11px) clamp(10px, 1.3vw, 14px);
    margin-bottom: var(--gap-md);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}
.interactionNoteLabel {
    display: block;
    font-family: 'Space Mono', monospace;
    font-size: clamp(7px, 0.75vw, 9px);
    font-weight: 900;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: clamp(3px, 0.4vw, 5px);
}
.interactionNoteText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(11px, 1.05vw, 13px);
    font-weight: 700;
    color: #1a2e30;
    line-height: 1.5;
    margin: 0;
    word-break: break-word;
}

/* ── PLOT SUB-CARD ── */
.plotSubCard {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-left: clamp(3px, 0.4vw, 4px) solid rgba(238, 140, 58, 0.35);
    border-radius: var(--radius-sm);
    padding: clamp(12px, 1.6vw, 18px) clamp(14px, 1.8vw, 20px);
    margin-bottom: var(--gap-md);
    transition: border-color 0.2s, background 0.2s;
}
.plotSubCard:hover {
    border-color: rgba(238, 140, 58, 0.5);
    border-left-color: var(--orange);
    background: rgba(255, 255, 255, 0.05);
}
.plotSubCard:last-child { margin-bottom: 0; }

.plotSubCardHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: clamp(10px, 1.3vw, 14px);
    padding-bottom: clamp(8px, 1vw, 10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.plotSubCardTitle {
    font-family: 'Space Mono', monospace;
    color: var(--orange);
    font-size: clamp(11px, 1.2vw, 14px);
    font-weight: 900;
}
.plotSubCardBox {
    font-family: 'Space Mono', monospace;
    font-size: clamp(9px, 0.95vw, 10px);
    color: rgba(255, 255, 255, 0.35);
    font-weight: 700;
    text-transform: uppercase;
}

/* Financial breakdown — TOTAL VALUE + STORAGE FEES - PAID = AMOUNT OWED */
.finBreakdown {
    display: flex;
    flex-direction: column;
    gap: clamp(6px, 0.8vw, 9px);
    margin-bottom: clamp(12px, 1.5vw, 16px);
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-sm);
    padding: clamp(10px, 1.3vw, 14px) clamp(12px, 1.5vw, 16px);
}
.finRow {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: clamp(10px, 1.4vw, 16px);
}
.finRowTotal {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: clamp(10px, 1.4vw, 16px);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: clamp(6px, 0.8vw, 9px);
    margin-top: clamp(3px, 0.4vw, 5px);
}
.finLabel {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-meta);
    font-weight: 800;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
    flex-shrink: 0;
}
.finLabelTotal {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-meta);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.55);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
    flex-shrink: 0;
}
.finValWhite {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 700;
    color: #fff;
    word-break: break-all;
}
.finValGreen {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 700;
    color: #22c55e;
    word-break: break-all;
}
.finValOrange {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 700;
    color: #EE8C3A;
    word-break: break-all;
}
.finValRed {
    font-family: 'Space Mono', monospace;
    font-size: clamp(13px, 1.4vw, 16px);
    font-weight: 900;
    color: #fca5a5;
    word-break: break-all;
    text-shadow: 0 0 8px rgba(239,68,68,0.35);
}

/* Expanded action buttons */
.expandedActions {
    display: flex;
    gap: clamp(8px, 1.1vw, 12px);
    flex-wrap: wrap;
}
.folderBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.6vw, 7px);
    height: clamp(32px, 3.8vw, 38px);
    padding: 0 clamp(12px, 1.5vw, 17px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.8);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
}
.folderBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.folderBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.payBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.6vw, 7px);
    height: clamp(32px, 3.8vw, 38px);
    padding: 0 clamp(12px, 1.5vw, 17px);
    background: rgba(16, 185, 129, 0.12);
    border: 1.5px solid rgba(16, 185, 129, 0.4);
    color: #34d399;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
}
.payBtn:hover { background: #10b981; color: #1a2e30; border-color: #10b981; box-shadow: 0 0 12px rgba(16,185,129,0.3); }
.payBtn:focus-visible { outline: 2px solid #10b981; outline-offset: 2px; }

/* ── LOG CALL MODAL — notebook interaction note ── */
.modalInteractionNote {
    background: #ffffff;
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    border-radius: 0 4px 4px 0;
    padding: clamp(10px, 1.3vw, 14px) clamp(12px, 1.5vw, 16px);
    margin-bottom: clamp(14px, 1.8vw, 18px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}
.modalInteractionNoteLabel {
    display: block;
    font-family: 'Space Mono', monospace;
    font-size: clamp(7px, 0.75vw, 9px);
    font-weight: 900;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: clamp(4px, 0.5vw, 7px);
}
.modalInteractionNoteText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 14px);
    font-weight: 700;
    color: #1a2e30;
    line-height: 1.55;
    margin: 0;
    word-break: break-word;
    font-style: italic;
}

/* ── EMPTY / LOADING ── */
.emptyState {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: clamp(10px, 1.5vw, 16px);
    padding: clamp(48px, 8vh, 80px) 24px;
    background: var(--panel-bg);
    border: 1.5px solid var(--panel-border);
    border-radius: var(--radius);
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-meta);
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.2);
}
.emptyIcon { font-size: clamp(32px, 5vw, 48px); opacity: 0.18; }
.loadingSpinner {
    width: clamp(30px, 4vw, 40px);
    height: clamp(30px, 4vw, 40px);
    border: 3px solid rgba(238, 140, 58, 0.15);
    border-top-color: #EE8C3A;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
    .finHUD { grid-template-columns: repeat(3, 1fr); }
}

/* MOBILE: stack HUD cards vertically, center content */
@media (max-width: 600px) {
    .finHUD {
        grid-template-columns: 1fr;
        gap: clamp(8px, 2vw, 12px);
    }
    .finHUDCard {
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
        padding: clamp(12px, 3vw, 16px) clamp(14px, 4vw, 20px);
        text-align: left;
    }
    .finHUDCard label {
        font-size: clamp(8px, 2.5vw, 10px);
        margin-bottom: 0;
    }
    .finHUDCard strong {
        font-size: clamp(15px, 4.5vw, 19px);
        text-align: right;
    }
    .cardTopRow { flex-direction: column; align-items: flex-start; gap: 8px; }
    .balanceLine { align-items: flex-start; }
    .cardMain { flex-direction: column; align-items: flex-start; gap: 10px; }
    .cardSideActions { width: 100%; }
    .logCallBtnSmall { flex: 1; justify-content: center; }
    .expandedActions { flex-direction: column; }
    .folderBtn, .payBtn { width: 100%; justify-content: center; }
    .timingRow { flex-direction: column; align-items: flex-start; gap: 5px; }
}

@media (max-width: 480px) {
    .searchInner { max-width: 100%; }
    .finHUD { grid-template-columns: 1fr; }
    .finHUDCard {
        flex-direction: column;
        align-items: flex-start;
        text-align: left;
    }
    .finHUDCard strong { font-size: clamp(16px, 5vw, 20px); }
}
"""

write(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.jsx'),
    RECOVERY_JSX
)

write(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.module.css'),
    RECOVERY_CSS
)

print("\n=== ALL DONE ===")
