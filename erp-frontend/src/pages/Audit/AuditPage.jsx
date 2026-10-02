// PATH: erp-frontend/src/pages/Audit/AuditPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
    FiSearch, FiActivity, FiClock, FiRefreshCw,
    FiDatabase, FiChevronDown, FiX, FiFilter,
    FiChevronLeft, FiChevronRight, FiPhoneCall, FiUser, FiDownloadCloud
} from 'react-icons/fi';
import auditService from '../../services/auditService';
import settingsService from '../../services/settingsService';
import HardwareSelect from '../../components/common/HardwareSelect';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import HardwareDatePicker from '../../components/common/HardwareDatePicker';
import { actionColor } from './auditCatalog';
import CornerDecor from '../../components/ui/CornerDecor';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import styles from './AuditPage.module.css';
import { LoadingState } from '../../components/common/LoadingState';

const AuditPage = () => {
    const [logs,       setLogs]       = useState([]);
    const [loading,    setLoading]    = useState(true);
    const [page,       setPage]       = useState(0);
    const [expandedId, setExpandedId] = useState(null);
    const [filters,    setFilters]    = useState({ operator: '', action: '', search: '', from: '', to: '' });
    const [operators,  setOperators]  = useState([]);
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const isDirty = filters.search !== '' || filters.from !== '' || filters.to !== '' || (filters.operator !== '' && filters.operator !== 'ALL STAFF') || (filters.action !== '' && filters.action !== 'ALL ACTIONS');
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);

    // Load real operators from database
    useEffect(() => {
        settingsService.getAllOperators()
            .then(data => setOperators(data))
            .catch(() => {});
    }, []);

    const reqRef = useRef(0);
    const fetchForensics = useCallback(async () => {
        const myReq = ++reqRef.current;   // fix169: only the newest request may update the screen
        setLoading(true);
        try {
            let activeAction = filters.action;
            if (activeAction === 'CALL LOG')         activeAction = 'RECOVERY_MISSION_COMPLETE';
            if (activeAction === 'EDIT RECORD')      activeAction = 'MASTER_REWRITE';
            if (activeAction === 'STAGE OVERRIDE')   activeAction = 'STAGE_OVERRIDE';
            if (activeAction === 'ALL ACTIONS')      activeAction = null;
            const activeOperator = filters.operator === 'ALL STAFF' ? null : filters.operator;

            // fix169: keyword, operator, action and dates all go to the server TOGETHER. The keyword used to go
            // to a different endpoint that ignored the other filters, and the dates were never sent at all.
            const data = await auditService.searchForensics({
                operator: activeOperator,
                action: activeAction,
                keyword: filters.search,
                start: filters.from ? filters.from + 'T00:00:00' : null,
                end: filters.to ? filters.to + 'T23:59:59' : null,
            }, page);
            if (myReq !== reqRef.current) return;
            setLogs(data.content || []);
        } catch { if (myReq === reqRef.current) console.error('FORENSIC_SIGNAL_LOST'); }
        finally  { if (myReq === reqRef.current) setLoading(false); }
    }, [page, filters]);

    // fix169: any filter change starts again from the first sector
    useEffect(() => { setPage(0); }, [filters]);

    useEffect(() => { fetchForensics(); }, [fetchForensics]);

    // WHEN, which is the first question anyone asks of an audit trail.
    // fix169: the dates now travel to the server with every other filter, so this
    // only stays as a harmless safety net on the page in hand.
    const visibleLogs = useMemo(() => {
        const from = filters.from ? new Date(filters.from + 'T00:00:00').getTime() : null;
        const to   = filters.to   ? new Date(filters.to   + 'T23:59:59').getTime() : null;
        if (from === null && to === null) return logs;
        return logs.filter(l => {
            const t = new Date(l.timestamp).getTime();
            if (!Number.isFinite(t)) return false;
            if (from !== null && t < from) return false;
            if (to !== null && t > to) return false;
            return true;
        });
    }, [logs, filters.from, filters.to]);

    const exportVisible = () => {
        const cell = v => {
            const str = v === null || v === undefined ? '' : String(v);
            return /[",\n]/.test(str) ? '"' + str.replace(/"/g, '""') + '"' : str;
        };
        const rows = visibleLogs.map(l => [
            new Date(l.timestamp).toISOString(), l.performedBy, l.action, l.details || '',
        ]);
        const csv = [['TIMESTAMP', 'OPERATOR', 'ACTION', 'DETAILS'], ...rows]
            .map(r => r.map(cell).join(',')).join('\n');
        // The BOM stops Excel reading a UTF-8 CSV as Latin-1.
        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.setAttribute('download', 'GOLDEN_SEED_AUDIT_' + new Date().toISOString().slice(0, 10) + '.csv');
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    };

    // Row colour: every action has its own, see actionColor() in auditCatalog.js
    const getFriendlyAction = action => {
        if (action === 'RECOVERY_MISSION_COMPLETE') return 'CALL LOG';
        if (action === 'RECOVERY_SYNC')             return 'CALL LOGGED';
        if (action === 'MASTER_REWRITE')            return 'EDIT RECORD';
        if (action === 'STAGE_OVERRIDE')            return 'STAGE OVERRIDE';
        if (action === 'INTAKE')                    return 'NEW PROJECT';
        if (action === 'NUCLEAR_PURGE')             return 'DELETE RECORD';
        if (action === 'EXPENSE_LOGGED')            return 'EXPENSE LOGGED';
        if (action === 'EXPENSE_EDITED')            return 'EXPENSE CORRECTED';
        if (action === 'EXPENSE_DELETED')           return 'EXPENSE DELETED';
        if (action === 'EXPENSE_PRESET_CREATED')    return 'PRESET ADDED';
        return action;
    };

    // Build operator options dynamically from real database users
    const operatorOptions = ['ALL STAFF', ...operators.map(op => op.username)];

    return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Audit Filters" />
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Audit Log</h1>
                    <p className={styles.subtitle}>Full history of all staff actions in the system</p>
                </div>
                <div className={styles.diagHUD}>
                    <div className={styles.diagItem}>
                        <FiDatabase aria-hidden="true" />
                        <span>VISIBLE RECORDS: <strong>{visibleLogs.length}</strong></span>
                    </div>
                </div>
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Re-run the current audit search" onClick={() => fetchForensics()} />
                </HeaderActions>
            </header>

            <div className={styles.controlHub}>
                <div className={styles.searchPill}>
                    <input
                        type="search"
                        placeholder="Investigate specific Plot Number, Name, or Keyword..."
                        className={`${styles.searchInput} ${(filters.search || isSearchFocused) ? styles.searchInputActive : ''}`}
                        value={filters.search}
                        onChange={e => setFilters({...filters, search: e.target.value})}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)}
                        aria-label="Search forensic logs"
                    />
                    {!(filters.search || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}
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
                            options={['ALL ACTIONS', 'CALL LOG', 'LOGIN_SUCCESS', 'EDIT RECORD', 'STAGE OVERRIDE', 'INTAKE']}
                            value={filters.action || 'ALL ACTIONS'}
                            onChange={val => setFilters({...filters, action: val})}
                        />
                    </div>
                    <label className={styles.dateField}>
                        <span>FROM</span>
                        <HardwareDatePicker value={filters.from} ariaLabel="From date" onChange={v => setFilters({...filters, from: v})} />
                    </label>
                    <label className={styles.dateField}>
                        <span>TO</span>
                        <HardwareDatePicker value={filters.to} ariaLabel="To date" onChange={v => setFilters({...filters, to: v})} />
                    </label>
                    <button className={styles.resetBtn} onClick={() => setFilters({operator:'', action:'', search:'', from:'', to:''})} aria-label="Reset all filters">
                        <FiFilter aria-hidden="true" /> RESET FILTERS
                    </button>
                    <button className={styles.resetBtn} onClick={exportVisible} disabled={visibleLogs.length === 0} aria-label="Export the visible log to CSV">
                        <FiDownloadCloud aria-hidden="true" /> EXPORT CSV
                    </button>
                </div>
            </div>

            <div className={styles.timelineFrame}>
                <div className={styles.timelineStream}>
                    {loading && <LoadingState label="SYNCHRONIZING WITH BLACK BOX..." tone="bare" />}
                    {!loading && visibleLogs.length === 0 && <div className={styles.emptySignal} role="status">NO DIGITAL FOOTPRINTS FOUND FOR THIS RANGE</div>}
                    {!loading && visibleLogs.length > 0 && (<div className={styles.logTray}><div className={styles.logCard}>
                    {visibleLogs.map(log => (
                        <div
                            key={log.id}
                            className={`${styles.logRow} ${expandedId === log.id ? styles.expanded : ''}`}
                            style={{ '--rail': actionColor(log.action) }}
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
                                    <p>{(log.details || '').length > 85 ? log.details.substring(0, 85) + '...' : (log.details || '')}</p>
                                </div>
                                <div className={styles.inspectIcon} aria-hidden="true">
                                    <FiChevronDown />
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
                    </div></div>)}
                </div>

                <footer className={styles.pagination} aria-label="Pagination">
                    <button className={styles.pgBtn} disabled={page === 0} onClick={() => setPage(p => p - 1)} aria-label="Older logs">
                        <FiChevronLeft aria-hidden="true" /> OLDER LOGS
                    </button>
                    <span className={styles.pageLabel} aria-current="page">SECTOR {page + 1}</span>
                    <button className={styles.pgBtn} onClick={() => setPage(p => p + 1)} disabled={logs.length < 50} aria-label="Newer logs">
                        NEWER LOGS <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
                <CornerDecor hideTop />
            </div>
        </div>
    );
};

export default AuditPage;