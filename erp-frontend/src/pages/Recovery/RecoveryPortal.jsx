import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch, FiCheckCircle, FiChevronRight, 
    FiMessageSquare, FiSave, FiList, FiCalendar, FiLock, FiUser, 
    FiChevronDown, FiChevronUp, FiX, FiCheckSquare, FiAlertCircle, 
    FiAlertTriangle, FiInfo, FiDollarSign, FiAlertOctagon, FiActivity, FiSettings
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Paid within 14 days', YELLOW: 'Paid within 30 days', RED: 'No recent payment' };

const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [viewMode, setViewMode] = useState('ACTION');
    const [missions, setMissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');
    const [callModal, setCallModal] = useState({ open: false, mission: null });
    const [logContent, setLogContent] = useState('');
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION' ? await recoveryService.getMissionQueue() : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch { console.error("SIGNAL_LOST"); }
        finally { setLoading(false); }
    }, [viewMode]);

    useEffect(() => { loadData(); }, [loadData]);

    const filteredMissions = useMemo(() => {
        let list = missions;
        if (searchTerm.trim()) {
            const t = searchTerm.toLowerCase();
            list = list.filter(m => m.ownerName.toLowerCase().includes(t) || m.phoneNumber.includes(t) || m.plots.some(p => p.plotNumber.toLowerCase().includes(t)));
        }
        if (statusFilter === 'BACKLOG') list = list.filter(m => m.hasBacklogPlots);
        if (statusFilter === 'ACTIVE')  list = list.filter(m => !m.hasBacklogPlots);
        return list;
    }, [missions, searchTerm, statusFilter]);

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Call Recovery</h1>
                    <p className={styles.pageSubtitle}>Log client calls and record payments</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.modeSwitch}>
                        <button className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive} onClick={() => setViewMode('ACTION')}><FiList /> DUE FOR CALL</button>
                        <button className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive} onClick={() => setViewMode('FORECAST')}><FiCalendar /> ALL TARGETS</button>
                    </div>
                </div>
            </header>

            <div className={styles.finHUD}>
                <div className={styles.finHUDCard}><label>ACTIVE TITLES OWED</label><strong>UGX {fmt(missions.filter(m => !m.hasBacklogPlots).reduce((s, m) => s + m.totalDemand, 0))}</strong></div>
                <div className={styles.finHUDCard}><label>BACKLOG TOTAL OWED</label><strong>UGX {fmt(missions.filter(m => m.hasBacklogPlots).reduce((s, m) => s + m.totalDemand, 0))}</strong></div>
                <div className={styles.finHUDCard}><label>STORAGE FEES</label><strong>UGX {fmt(missions.reduce((s, m) => s + m.totalStorageFees, 0))}</strong></div>
            </div>

            <div className={styles.filterBar}>
                <div className={styles.searchInner}><FiSearch className={styles.searchIcon} /><input className={styles.searchInput} placeholder="Search names, plots, phones..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} /></div>
                <div className={styles.filterPills}>
                    {['ALL', 'ACTIVE', 'BACKLOG'].map(f => (
                        <button key={f} className={`${styles.filterPill} ${statusFilter === f ? styles.filterPillActive : ''}`} onClick={() => setStatusFilter(f)}>{f}</button>
                    ))}
                </div>
            </div>

            <div className={styles.legend}>
                {Object.entries(BADGE_COLORS).map(([k, c]) => (
                    <span key={k} className={styles.legendItem}><span style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />{BADGE_LABELS[k]}</span>
                ))}
            </div>

            <div className={styles.missionGrid}>
                {filteredMissions.map(m => (
                    <div key={m.clientId} className={`${styles.missionCard} ${m.hasBacklogPlots ? styles.cardBacklog : ''}`}>
                        <div className={styles.cardHeader} onClick={() => setExpandedId(expandedId === m.clientId ? null : m.clientId)}>
                            <div className={styles.cardTopRow}>
                                <div className={styles.cardTopRowLeft}>
                                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: BADGE_COLORS[m.plots[0].paymentHealthBadge] }} />
                                    <span className={styles.plotId}>{m.plots.map(p => p.plotNumber).join(' & ')}</span>
                                    {m.hasBacklogPlots && <span className={styles.backlogPill}>BACKLOG</span>}
                                </div>
                                <div className={styles.balanceLine}>
                                    <span className={styles.balanceLabel}>TOTAL OWED</span>
                                    <span className={`${styles.balanceVal} ${m.hasBacklogPlots ? styles.balanceRed : ''}`}>UGX {fmt(m.totalDemand)}</span>
                                </div>
                            </div>
                            <div className={styles.cardMain}>
                                <span className={styles.ownerLine}>{m.ownerName}</span>
                                <span className={styles.phoneLine}>{m.phoneNumber}</span>
                                <div className={styles.cardSideActions}>
                                    <button className={styles.logCallBtnSmall} disabled={m.isLocked} onClick={(e) => { e.stopPropagation(); setCallModal({ open: true, mission: m.plots[0] }); }}>
                                        <FiPhoneCall /> {m.isLocked ? 'LOCKED' : 'LOG CALL'}
                                    </button>
                                    {expandedId === m.clientId ? <FiChevronUp className={styles.expandIcon} /> : <FiChevronDown className={styles.expandIcon} />}
                                </div>
                            </div>
                        </div>
                        {expandedId === m.clientId && (
                            <div className={styles.cardBody}>
                                <div className={styles.timingRow}><FiClock /> Last: {m.lastContactDate} | Next: {m.nextCallDue} | Monthly: {m.monthlyCallCount}/2</div>
                                {m.plots.map(p => (
                                    <div key={p.projectId} className={styles.plotSubCard}>
                                        <div style={{display:'flex', justifyContent:'space-between', marginBottom:8}}>
                                            <strong style={{color:'var(--orange)'}}>{p.plotNumber}</strong>
                                            <span style={{fontSize:10, opacity:0.5}}>Box: {p.physicalBoxNumber}</span>
                                        </div>
                                        <div className={styles.finDetail}>
                                            <div className={styles.finDetailRow}><span>Arrears</span><strong>UGX {fmt(p.isBacklog ? p.totalBacklogOwed : p.currentBalance)}</strong></div>
                                            <div className={styles.finDetailRow}><span>Last Note</span><i>"{p.lastInteractionNote}"</i></div>
                                        </div>
                                        <div className={styles.expandedActions}>
                                            <button className={styles.folderBtn} onClick={() => navigate(`/folder/${p.projectId}`)}>OPEN FOLDER</button>
                                            {isAdmin && <button className={styles.payBtn} onClick={() => navigate(`/folder/${p.projectId}?action=pay`)}>RECORD PAYMENT</button>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <HardwareModal isOpen={callModal.open} onClose={() => setCallModal({ open: false, mission: null })} title="LOG CALL">
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>INTERACTION NOTES</label>
                    <textarea className={modalStyles.modalTextarea} value={logContent} onChange={e => setLogContent(e.target.value)} placeholder="Type result of call..." />
                </div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton onClick={async () => {
                        await recoveryService.logRecoveryCall(callModal.mission.projectId, logContent);
                        setCallModal({ open: false, mission: null });
                        setLogContent('');
                        loadData();
                    }} icon={FiSave}>SAVE LOG</HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};
export default RecoveryPortal;
