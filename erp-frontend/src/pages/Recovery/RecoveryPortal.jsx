import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
    const [callModal,    setCallModal]    = useState({ open: false, mission: null });
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
            setCallModal({ open: false, mission: null });
            setLogContent('');
            loadData();
        } catch { /* silent */ }
        finally { setCommitting(false); }
    };

    const openCallModal = (e, plot) => {
        e.stopPropagation();
        // PRE-FILL textarea with the last interaction note so user can edit/append
        const lastNote = plot.lastInteractionNote && plot.lastInteractionNote !== 'NO PRIOR CONTACT'
            ? plot.lastInteractionNote
            : '';
        setCallModal({ open: true, mission: plot });
        setLogContent(lastNote);
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
                                            <span className={styles.timingItem}>Last contact: <strong>{m.lastContactDate}</strong></span>
                                            <span className={styles.timingItem}>Next due: <strong>{m.nextCallDue}</strong></span>
                                            <span className={styles.timingItem}>This month: <strong>{m.monthlyCallCount}/2</strong></span>
                                        </div>

                                        {m.plots.map(p => {
                                            // CORRECT MATH:
                                            // totalValue  = the true plot cost (totalCost from DTO, same as originalDebt for backlog)
                                            // amtPaid     = what has been paid so far
                                            // storageFees = accumulated fees (backlog only)
                                            // amountOwed  = totalValue + storageFees - amtPaid
                                            const totalValue  = Number(p.totalCost  || p.originalDebt || 0);
                                            const amtPaid     = Number(p.amountPaid || 0);
                                            const storageFees = Number(p.storageFeesAccumulated || 0);
                                            const amountOwed  = Math.max(0, totalValue + storageFees - amtPaid);

                                            return (
                                            <div key={p.projectId} className={styles.plotSubCard}>
                                                <div className={styles.plotSubCardHeader}>
                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>
                                                    <span className={styles.plotSubCardBox}>BOX: {p.physicalBoxNumber || '---'}</span>
                                                </div>
                                                {p.isBacklog && p.surveyDate && (
                                                    <div className={styles.surveyDateRow}>
                                                        SURVEYED: <strong>{p.surveyDate}</strong>
                                                    </div>
                                                )}

                                                {/* Last interaction note — notebook style */}
                                                {p.lastInteractionNote && p.lastInteractionNote !== 'NO PRIOR CONTACT' && (
                                                    <div className={styles.interactionNote}>
                                                        <span className={styles.interactionNoteLabel}>LAST CONTACT NOTE</span>
                                                        <p className={styles.interactionNoteText}>{p.lastInteractionNote}</p>
                                                    </div>
                                                )}

                                                {/* Financial breakdown */}
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

            {/* LOG CALL MODAL — textarea pre-filled with last note */}
            <HardwareModal
                isOpen={callModal.open}
                onClose={() => { setCallModal({ open: false, mission: null }); setLogContent(''); }}
                title={callModal.mission ? `LOG CALL — ${callModal.mission.plotNumber}` : 'LOG CALL'}
            >
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
                        onClick={() => { setCallModal({ open: false, mission: null }); setLogContent(''); }}
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
