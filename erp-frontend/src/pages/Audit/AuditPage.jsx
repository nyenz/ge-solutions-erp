// PATH: erp-frontend/src/pages/Audit/AuditPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
    FiShield, FiSearch, FiActivity, FiClock,
    FiDatabase, FiMaximize2, FiX, FiFilter,
    FiChevronLeft, FiChevronRight, FiPhoneCall, FiUser
} from 'react-icons/fi';
import auditService from '../../services/auditService';
import settingsService from '../../services/settingsService';
import HardwareSelect from '../../components/common/HardwareSelect';
import styles from './AuditPage.module.css';

const AuditPage = () => {
    const [logs,       setLogs]       = useState([]);
    const [loading,    setLoading]    = useState(true);
    const [page,       setPage]       = useState(0);
    const [expandedId, setExpandedId] = useState(null);
    const [filters,    setFilters]    = useState({ operator: '', action: '', search: '' });
    const [operators,  setOperators]  = useState([]);

    // Load real operators from database
    useEffect(() => {
        settingsService.getAllOperators()
            .then(data => setOperators(data))
            .catch(() => {});
    }, []);

    const fetchForensics = useCallback(async () => {
        setLoading(true);
        try {
            let activeAction = filters.action;
            if (activeAction === 'CALL LOG')         activeAction = 'RECOVERY_MISSION_COMPLETE';
            if (activeAction === 'GOD-MODE REWRITE') activeAction = 'MASTER_REWRITE';
            if (activeAction === 'STAGE OVERRIDE')   activeAction = 'STAGE_OVERRIDE';
            if (activeAction === 'ALL ACTIONS')      activeAction = null;
            const activeOperator = filters.operator === 'ALL STAFF' ? null : filters.operator;

            const data = filters.search
                ? await auditService.investigateKeyword(filters.search, page)
                : await auditService.searchForensics({ operator: activeOperator, action: activeAction }, page);
            setLogs(data.content || []);
        } catch { console.error('FORENSIC_SIGNAL_LOST'); }
        finally  { setLoading(false); }
    }, [page, filters]);

    useEffect(() => { fetchForensics(); }, [fetchForensics]);

    const getSeverityClass = action => {
        const a = action?.toUpperCase() || '';
        if (a.includes('DELETE') || a.includes('OVERRIDE') || a.includes('SUSPEND')) return styles.severityHigh;
        if (a.includes('REWRITE') || a.includes('UPDATE')  || a.includes('PAYMENT')) return styles.severityMed;
        if (a.includes('RECOVERY') || a.includes('MISSION'))                          return styles.severityIntel;
        return styles.severityLow;
    };

    const getFriendlyAction = action => {
        if (action === 'RECOVERY_MISSION_COMPLETE') return 'CALL LOG';
        if (action === 'MASTER_REWRITE')            return 'GOD-MODE REWRITE';
        if (action === 'STAGE_OVERRIDE')            return 'STAGE OVERRIDE';
        return action;
    };

    // Build operator options dynamically from real database users
    const operatorOptions = ['ALL STAFF', ...operators.map(op => op.username)];

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>System Forensics</h1>
                    <p className={styles.subtitle}>Unified Accountability Archive | Total Traceability Active</p>
                </div>
                <div className={styles.diagHUD}>
                    <div className={styles.diagItem}>
                        <FiDatabase aria-hidden="true" />
                        <span>VISIBLE RECORDS: <strong>{logs.length}</strong></span>
                    </div>
                </div>
            </header>

            <div className={styles.controlHub}>
                <div className={styles.searchPill}>
                    <FiSearch className={styles.searchIcon} aria-hidden="true" />
                    <input
                        type="search"
                        placeholder="Investigate specific Plot ID, Name, or Keyword..."
                        className={styles.searchInput}
                        value={filters.search}
                        onChange={e => setFilters({...filters, search: e.target.value})}
                        aria-label="Search forensic logs"
                    />
                    {filters.search && (
                        <button className={styles.searchClear} onClick={() => setFilters({...filters, search: ''})} aria-label="Clear search">
                            <FiX aria-hidden="true" />
                        </button>
                    )}
                </div>
                <div className={styles.filterGrid}>
                    <div className={styles.hwSelectWrap}>
                        <HardwareSelect
                            label="OPERATOR ID"
                            options={operatorOptions}
                            value={filters.operator || 'ALL STAFF'}
                            onChange={val => setFilters({...filters, operator: val})}
                        />
                    </div>
                    <div className={styles.hwSelectWrap}>
                        <HardwareSelect
                            label="PROTOCOL CLASS"
                            options={['ALL ACTIONS', 'CALL LOG', 'LOGIN_SUCCESS', 'GOD-MODE REWRITE', 'STAGE OVERRIDE', 'INTAKE']}
                            value={filters.action || 'ALL ACTIONS'}
                            onChange={val => setFilters({...filters, action: val})}
                        />
                    </div>
                    <button className={styles.resetBtn} onClick={() => setFilters({operator:'', action:'', search:''})} aria-label="Reset all filters">
                        <FiFilter aria-hidden="true" /> RESET FILTERS
                    </button>
                </div>
            </div>

            <div className={styles.timelineFrame}>
                <div className={styles.timelineStream}>
                    {loading && <div className={styles.loadingPulse} role="status">SYNCHRONIZING WITH BLACK BOX...</div>}
                    {!loading && logs.length === 0 && <div className={styles.emptySignal} role="status">NO DIGITAL FOOTPRINTS FOUND FOR THIS RANGE</div>}
                    {!loading && logs.map(log => (
                        <div
                            key={log.id}
                            className={`${styles.logRow} ${getSeverityClass(log.action)} ${expandedId === log.id ? styles.expanded : ''}`}
                            onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                            role="button"
                            tabIndex={0}
                            aria-expanded={expandedId === log.id}
                            aria-label={`Log entry: ${getFriendlyAction(log.action)} by ${log.performedBy}`}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedId(expandedId === log.id ? null : log.id); } }}
                        >
                            <div className={styles.logMain}>
                                <div className={styles.timeMark}>
                                    <div className={styles.clockPair}>
                                        <FiClock aria-hidden="true" />
                                        <span>{new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    </div>
                                    <small>{new Date(log.timestamp).toLocaleDateString()}</small>
                                </div>
                                <div className={styles.actionMark}>
                                    <div className={styles.iconChassis} aria-hidden="true">
                                        {log.action === 'RECOVERY_MISSION_COMPLETE' ? <FiPhoneCall aria-hidden="true" /> :
                                         log.performedBy === 'SYSTEM' ? <FiActivity aria-hidden="true" /> : <FiUser aria-hidden="true" />}
                                    </div>
                                    <div className={styles.actionMeta}>
                                        <strong>{getFriendlyAction(log.action)}</strong>
                                        <span>OP: {log.performedBy}</span>
                                    </div>
                                </div>
                                <div className={styles.targetMark}>
                                    <p>{log.details.length > 85 ? log.details.substring(0, 85) + '...' : log.details}</p>
                                </div>
                                <div className={styles.inspectIcon} aria-hidden="true">
                                    {expandedId === log.id ? <FiX /> : <FiMaximize2 />}
                                </div>
                            </div>
                            <div className={`${styles.traceDetails} ${expandedId === log.id ? styles.traceOpen : styles.traceClosed}`}>
                                <div className={styles.rawBox}>
                                    <div className={styles.rawHeader}>
                                        <FiDatabase aria-hidden="true" /> <span>FORENSIC DATA READOUT [SECURE]</span>
                                    </div>
                                    <pre className={styles.rawOutput}><code>{log.details}</code></pre>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <footer className={styles.pagination} aria-label="Pagination">
                    <button className={styles.pgBtn} disabled={page === 0} onClick={() => setPage(p => p - 1)} aria-label="Older logs">
                        <FiChevronLeft aria-hidden="true" /> OLDER LOGS
                    </button>
                    <span className={styles.pageLabel} aria-current="page">SECTOR {page + 1}</span>
                    <button className={styles.pgBtn} onClick={() => setPage(p => p + 1)} disabled={logs.length < 20} aria-label="Newer logs">
                        NEWER LOGS <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
            </div>
        </div>
    );
};

export default AuditPage;