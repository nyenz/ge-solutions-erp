// PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import {
    FiPhoneCall, FiFolder, FiMapPin, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiUsers, FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import styles from './RecoveryPortal.module.css';

// ─── TOAST ────────────────────────────────────────────────────────
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
    success: <FiCheckSquare  aria-hidden="true" />,
    error:   <FiAlertCircle  aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo          aria-hidden="true" />,
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

// ─── MAIN ─────────────────────────────────────────────────────────
const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { toasts, toast, dismissToast } = useToast();

    const [viewMode,      setViewMode]      = useState('ACTION');
    const [missions,      setMissions]      = useState([]);
    const [loading,       setLoading]       = useState(true);
    const [expandedId,    setExpandedId]    = useState(null);
    const [searchTerm,    setSearchTerm]    = useState('');
    const [activeMission, setActiveMission] = useState(null);
    const [missionHistory,setMissionHistory]= useState([]);
    const [logContent,    setLogContent]    = useState('');
    const [committing,    setCommitting]    = useState(false);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION'
                ? await recoveryService.getMissionQueue()
                : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch {
            toast('DATA STREAM LOST — RETRYING', 'error', 6000);
        } finally {
            setLoading(false);
        }
    }, [viewMode, toast]);

    useEffect(() => { loadData(); }, [loadData]);

    useEffect(() => {
        if (!activeMission) return;
        recoveryService.getHistory(activeMission.projectId)
            .then(setMissionHistory)
            .catch(() => setMissionHistory([]));
    }, [activeMission]);

    const handleLogCall = async () => {
        if (!logContent.trim() || !activeMission) return;
        setCommitting(true);
        try {
            await recoveryService.logRecoveryCall(activeMission.projectId, logContent);
            if (viewMode === 'ACTION') {
                setMissions(prev => prev.filter(m => m.projectId !== activeMission.projectId));
            } else {
                await loadData();
            }
            setActiveMission(null);
            setLogContent('');
            setExpandedId(null);
            toast('ASSET STATUS UPDATED — 14-DAY CLOCK RESET', 'success');
        } catch {
            toast('LOG FAILURE — COULD NOT COMMIT CALL', 'error', 8000);
        } finally {
            setCommitting(false);
        }
    };

    const toggleCard = (id) => setExpandedId(prev => prev === id ? null : id);

    const filteredMissions = useMemo(() => {
        const term = searchTerm.toLowerCase().replace(/\s+/g, '');
        return missions.filter(m =>
            m.plotNumber?.toLowerCase().includes(term) ||
            (m.allOwners || []).some(o =>
                o.name?.toLowerCase().includes(term) ||
                o.phone?.replace(/\s+/g, '').includes(term)
            )
        );
    }, [missions, searchTerm]);

    const getStatusStyle = (status) => {
        if (status === 'ACTION REQUIRED' || status === 'NEW ASSIGNMENT') return styles.statusRed;
        if (status === 'COOLING DOWN') return styles.statusBlue;
        if (status === 'MONTHLY LIMIT') return styles.statusGrey;
        return styles.statusDefault;
    };

    // Safe accessor — guard against empty allOwners
    const primaryName = (mission) => mission?.allOwners?.[0]?.name || 'UNKNOWN OWNER';

    if (loading) return (
        <div className={styles.bootScreen} role="status" aria-label="Loading recovery terminal">
            <div className={styles.bootSpinner} aria-hidden="true" />
            <span className={styles.bootLabel}>BOOTING RECOVERY TERMINAL...</span>
        </div>
    );

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            {/* HEADER */}
            <header className={styles.header}>
                <div className={styles.titleBlock}>
                    <h1 className={styles.title}>Recovery Hub</h1>
                    <div className={styles.modeSwitch} role="group" aria-label="View mode">
                        <button
                            className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('ACTION'); setExpandedId(null); }}
                            aria-pressed={viewMode === 'ACTION'}
                        >
                            <FiList aria-hidden="true" /> ACTION QUEUE
                        </button>
                        <button
                            className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('FORECAST'); setExpandedId(null); }}
                            aria-pressed={viewMode === 'FORECAST'}
                        >
                            <FiCalendar aria-hidden="true" /> FULL SCHEDULE
                        </button>
                    </div>
                </div>
                <div className={styles.hudStats}>
                    <div className={styles.statBox}>
                        <label>ASSET TARGETS</label>
                        <strong>{missions.length}</strong>
                    </div>
                </div>
            </header>

            {/* SEARCH */}
            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <FiSearch className={styles.searchIcon} aria-hidden="true" />
                    <input
                        type="search"
                        placeholder="Search Plot ID, proprietor name, or phone number..."
                        className={styles.searchInput}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        aria-label="Search recovery missions"
                    />
                    {searchTerm && (
                        <button className={styles.searchClear} onClick={() => setSearchTerm('')} aria-label="Clear search">
                            <FiX aria-hidden="true" />
                        </button>
                    )}
                </div>
            </div>

            {/* MISSION GRID */}
            <div className={styles.missionGrid}>
                {filteredMissions.length === 0 ? (
                    <div className={styles.emptyGate} role="status">
                        <FiCheckCircle className={styles.emptyIcon} aria-hidden="true" />
                        <h2 className={styles.emptyTitle}>
                            {searchTerm ? `NO TARGETS MATCH "${searchTerm.toUpperCase()}"` : 'NO TARGETS FOUND'}
                        </h2>
                        <p className={styles.emptyMsg}>Registry is synchronised for current filters.</p>
                    </div>
                ) : (
                    filteredMissions.map(mission => {
                        const isExpanded   = expandedId === mission.projectId;
                        const primaryOwner = mission.allOwners?.[0];
                        const jointOwners  = mission.allOwners?.slice(1) || [];

                        return (
                            <div
                                key={mission.projectId}
                                className={`${styles.missionCard} ${isExpanded ? styles.cardExpanded : ''} ${mission.isLocked ? styles.cardLocked : ''}`}
                                onClick={() => toggleCard(mission.projectId)}
                                role="button"
                                tabIndex={0}
                                aria-expanded={isExpanded}
                                aria-label={`Mission: ${primaryOwner?.name || 'Unknown'}, plot ${mission.plotNumber}`}
                                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleCard(mission.projectId); } }}
                            >
                                <div className={`${styles.statusBadge} ${getStatusStyle(mission.missionStatus)}`}>
                                    {mission.missionStatus === 'MONTHLY LIMIT' && <FiLock aria-hidden="true" />}
                                    {mission.missionStatus}
                                </div>

                                <div className={styles.cardHeader}>
                                    <div className={styles.identity}>
                                        <h3 className={styles.ownerName}>{primaryOwner?.name || '---'}</h3>
                                        <div className={styles.miniMeta}>
                                            <span className={styles.phoneNum}>{primaryOwner?.phone || '---'}</span>
                                            {jointOwners.length > 0 && (
                                                <span className={styles.jointCountBadge} aria-label={`${jointOwners.length} joint owner${jointOwners.length > 1 ? 's' : ''}`}>
                                                    <FiUsers aria-hidden="true" /> +{jointOwners.length} JOINT
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className={styles.expandIcon} aria-hidden="true">
                                        {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                                    </div>
                                </div>

                                <div className={`${styles.cardBody} ${isExpanded ? styles.bodyOpen : styles.bodyClosed}`}>
                                    <div className={styles.divider} aria-hidden="true" />

                                    {jointOwners.length > 0 && (
                                        <div className={styles.jointContactsZone}>
                                            <label>JOINT OWNERS / CO-SIGNERS</label>
                                            {jointOwners.map(owner => (
                                                <div key={owner.id} className={styles.contactRow}>
                                                    <span className={styles.jointName}>{owner.name}</span>
                                                    <span className={styles.jointPhone}>{owner.phone}</span>
                                                </div>
                                            ))}
                                            <div className={styles.divider} aria-hidden="true" />
                                        </div>
                                    )}

                                    <div className={styles.assetContext}>
                                        <div className={styles.metaRow}><FiMapPin aria-hidden="true" /><span>{mission.plotNumber}</span></div>
                                        <div className={styles.metaRow}><FiFolder aria-hidden="true" /><span>BOX: {mission.physicalBoxNumber}</span></div>
                                    </div>

                                    {viewMode === 'FORECAST' && (
                                        <div className={styles.scheduleRow}>
                                            <FiClock aria-hidden="true" />
                                            <span>ELIGIBLE ON: <strong>{new Date(mission.nextCallDue).toLocaleDateString()}</strong></span>
                                        </div>
                                    )}

                                    <div className={styles.demandTerminal}>
                                        <div className={styles.demandLabel}>WEEKLY REQUIREMENT</div>
                                        <div className={styles.demandValue}>UGX {mission.weeklyRequirement?.toLocaleString()}</div>
                                        <div className={styles.subArrears}>TOTAL DEBT: UGX {mission.totalArrears?.toLocaleString()}</div>
                                    </div>

                                    <div className={styles.intelSnippet}>
                                        <div className={styles.intelHead}>
                                            <FiMessageSquare aria-hidden="true" />
                                            <span>LAST LOGGED INTEL:</span>
                                        </div>
                                        <p className={styles.noteText}>"{mission.lastInteractionNote}"</p>
                                    </div>

                                    <div className={styles.cardActions}>
                                        <button
                                            className={styles.logCallBtn}
                                            onClick={e => { e.stopPropagation(); setActiveMission(mission); }}
                                            disabled={mission.isLocked}
                                            aria-label={mission.isLocked ? 'Mission locked' : `Log call for ${primaryOwner?.name}`}
                                        >
                                            <FiPhoneCall aria-hidden="true" />
                                            {mission.isLocked ? 'LOCKED' : 'LOG CALL'}
                                        </button>
                                        <button
                                            className={styles.folderBtn}
                                            onClick={e => { e.stopPropagation(); navigate(`/folder/${mission.projectId}`); }}
                                            aria-label={`Open binder for ${mission.plotNumber}`}
                                        >
                                            <FiChevronRight aria-hidden="true" /> BINDER
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* MODAL: LOG CALL */}
            <HardwareModal
                isOpen={!!activeMission}
                onClose={() => setActiveMission(null)}
                title={`LOG CALL: ${primaryName(activeMission)}`}
            >
                <div className={styles.modalBody}>
                    <div className={styles.historyStream}>
                        <div className={styles.historyTitle}>PREVIOUS INTERACTIONS</div>
                        {missionHistory.length === 0 ? (
                            <div className={styles.emptyHistory}>No prior logs found.</div>
                        ) : (
                            missionHistory.map(log => (
                                <div key={log.id} className={styles.historyItem}>
                                    <div className={styles.historyMeta}>
                                        <span><FiUser aria-hidden="true" /> {log.recordedBy}</span>
                                        <small>{new Date(log.timestamp).toLocaleDateString()}</small>
                                    </div>
                                    <p>{log.notes}</p>
                                </div>
                            ))
                        )}
                    </div>
                    <p className={styles.modalHint}>Enter technical response or call result below.</p>
                    <textarea
                        className={styles.notebookArea}
                        placeholder="e.g. Promises payment by Monday MTN line..."
                        value={logContent}
                        onChange={e => setLogContent(e.target.value)}
                        aria-label="Call log entry"
                    />
                    <div className={styles.modalFooter}>
                        <HardwareButton loading={committing} onClick={handleLogCall} icon={FiSave}>
                            Commit &amp; Reset
                        </HardwareButton>
                    </div>
                </div>
            </HardwareModal>
        </div>
    );
};

export default RecoveryPortal;