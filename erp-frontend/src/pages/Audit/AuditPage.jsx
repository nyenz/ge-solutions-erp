// PATH: erp-frontend/src/pages/Audit/AuditPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
    FiSearch, FiActivity, FiClock, FiRefreshCw,
    FiDatabase, FiChevronDown, FiX, FiFilter,
    FiChevronLeft, FiChevronRight, FiPhoneCall, FiUser, FiDownloadCloud
} from 'react-icons/fi';
import auditService from '../../services/auditService';
import HardwareSelect from '../../components/common/HardwareSelect';
import HardwareDatePicker from '../../components/common/HardwareDatePicker';
import { ACTION_GROUPS, actionColor, friendlyAction } from './auditCatalog';
import CornerDecor from '../../components/ui/CornerDecor';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import styles from './AuditPage.module.css';
import { LoadingState } from '../../components/common/LoadingState';
import { toCSV, downloadCSV, plainStamp } from '../../utils/csv';

const PAGE_SIZE = 50;
const EXPORT_CAP = 20000;
const ALL_ACTIONS = 'ALL ACTIONS';
const ALL_STAFF = 'ALL STAFF';

/* fix181 (10.1): the ACTION filter is built from the catalog groups. Picking a group sends all its codes; picking one
   action sends that code. HardwareSelect takes plain text, so a group is its own row ("MONEY: all") above its actions. */
const ACTION_OPTIONS = [ALL_ACTIONS];
const CODES_OF_OPTION = {};
ACTION_GROUPS.forEach(g => {
    const head = g.group + ': all';
    ACTION_OPTIONS.push(head);
    CODES_OF_OPTION[head] = g.actions.map(a => a.code);
    g.actions.forEach(a => {
        const label = '   ' + a.label + ' (' + g.group.toLowerCase() + ')';
        ACTION_OPTIONS.push(label);
        CODES_OF_OPTION[label] = [a.code];
    });
});

/** "2026-10-04" -> "2026-10-05T00:00:00": the end is exclusive on the server, so the whole TO day is included (10.11). */
const dayAfter = (ymd) => {
    const d = new Date(ymd + 'T00:00:00');
    d.setDate(d.getDate() + 1);
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0') + 'T00:00:00';
};

const AuditPage = () => {
    const [logs,       setLogs]       = useState([]);
    const [meta,       setMeta]       = useState({ total: 0, totalPages: 0, last: true });
    const [loading,    setLoading]    = useState(true);
    const [fault,      setFault]      = useState(null);   // { message, status } -- 10.5
    const [page,       setPage]       = useState(0);
    const [expandedId, setExpandedId] = useState(null);
    const [filters,    setFilters]    = useState({ operator: '', action: '', search: '', from: '', to: '' });
    const [operators,  setOperators]  = useState([]);
    const [exporting,  setExporting]  = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    // fix181 (10.11): a filter is not unsaved work, so leaving this page never asks

    // fix181 (10.3): the names come from the audit trail itself (works for the Director, includes SYSTEM)
    useEffect(() => {
        auditService.getOperators().then(setOperators).catch(() => setOperators([]));
    }, []);

    const serverFilters = useMemo(() => ({
        operator: filters.operator && filters.operator !== ALL_STAFF ? filters.operator : null,
        actions: filters.action && filters.action !== ALL_ACTIONS ? (CODES_OF_OPTION[filters.action] || []) : [],
        keyword: filters.search.trim().slice(0, 100),
        start: filters.from ? filters.from + 'T00:00:00' : null,
        end: filters.to ? dayAfter(filters.to) : null,
    }), [filters]);

    const reqRef = useRef(0);
    const fetchForensics = useCallback(async () => {
        const myReq = ++reqRef.current;   // only the newest request may update the screen
        setLoading(true);
        try {
            const data = await auditService.searchForensics(serverFilters, page, PAGE_SIZE);
            if (myReq !== reqRef.current) return;
            setLogs(data.content || []);
            setMeta({ total: data.totalElements || 0, totalPages: data.totalPages || 0, last: data.last !== false });
            setFault(null);
        } catch (e) {
            if (myReq === reqRef.current) setFault({ message: e.message, status: e.status });
        }
        finally  { if (myReq === reqRef.current) setLoading(false); }
    }, [page, serverFilters]);

    // any filter change starts again from the newest page
    useEffect(() => { setPage(0); }, [filters]);

    useEffect(() => { fetchForensics(); }, [fetchForensics]);

    // fix181 (13.0c): the rows are shown exactly as the server sent them (no second date filter in the browser)
    const visibleLogs = logs;
    const firstShown = meta.total === 0 ? 0 : page * PAGE_SIZE + 1;
    const lastShown = page * PAGE_SIZE + logs.length;

    // fix181 (10.6): export EVERY row that matches the filters (pages of 200, up to a cap), server time as plain text,
    // formula-safe cells (13.8), and one AUDIT_EXPORT line in the trail
    const exportAll = async () => {
        setExporting('Preparing...');
        try {
            const all = [];
            let total = 0;
            for (let pg = 0; all.length < EXPORT_CAP; pg += 1) {
                const data = await auditService.searchForensics(serverFilters, pg, 200);
                total = data.totalElements || 0;
                all.push(...(data.content || []));
                setExporting(`Preparing ${all.length.toLocaleString()} of ${total.toLocaleString()}...`);
                if (data.last !== false || (data.content || []).length === 0) break;
            }
            const rows = all.map(l => [plainStamp(l.timestamp), l.performedBy, l.action, friendlyAction(l.action), l.details || '']);
            downloadCSV('GOLDEN_SEED_AUDIT_' + new Date().toISOString().slice(0, 10) + '.csv',
                toCSV(['TIME', 'OPERATOR', 'CODE', 'ACTION', 'DETAILS'], rows));
            auditService.logExport({ ...serverFilters, actionFilter: filters.action || ALL_ACTIONS }, all.length);
            setExporting(total > all.length ? `Exported the newest ${all.length.toLocaleString()} of ${total.toLocaleString()} rows (the limit).` : '');
        } catch (e) {
            setExporting('Export failed: ' + e.message);
        }
    };

    const operatorOptions = [ALL_STAFF, ...operators];

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Audit Log</h1>
                    <p className={styles.subtitle}>Full history of all staff actions in the system</p>
                </div>
                <div className={styles.diagHUD}>
                    <div className={styles.diagItem}>
                        <FiDatabase aria-hidden="true" />
                        <span>{meta.total === 0 ? 'NO MATCHES' : <>SHOWING <strong>{firstShown.toLocaleString()} to {lastShown.toLocaleString()}</strong> OF <strong>{meta.total.toLocaleString()}</strong></>}</span>
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
                            value={filters.operator || ALL_STAFF}
                            onChange={val => setFilters({...filters, operator: val})}
                        />
                    </div>
                    <div className={styles.hwSelectWrap}>
                        <HardwareSelect
                            label="ACTION"
                            options={ACTION_OPTIONS}
                            value={filters.action || ALL_ACTIONS}
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
                    <button className={styles.resetBtn} onClick={exportAll} disabled={meta.total === 0 || (exporting && exporting.startsWith('Preparing'))} aria-label="Export every matching row to CSV">
                        <FiDownloadCloud aria-hidden="true" /> EXPORT CSV ({meta.total.toLocaleString()})
                    </button>
                </div>
            </div>

            <div className={styles.timelineFrame}>
                <div className={styles.timelineStream}>
                    {exporting && <div className={styles.emptySignal} role="status">{exporting}</div>}
                    {loading && <LoadingState label="Loading the audit trail..." tone="bare" />}
                    {/* fix181 (10.5): a failed load is an error with Retry, never "nothing found" */}
                    {!loading && fault && (
                        <div className={styles.emptySignal} role="alert">
                            Could not load the audit trail{fault.status ? ` (HTTP ${fault.status})` : ''}: {fault.message}{' '}
                            <button type="button" className={styles.resetBtn} onClick={() => fetchForensics()}><FiRefreshCw aria-hidden="true" /> RETRY</button>
                        </div>
                    )}
                    {!loading && !fault && visibleLogs.length === 0 && <div className={styles.emptySignal} role="status">No audit lines match these filters.</div>}
                    {!loading && !fault && visibleLogs.length > 0 && (<div className={styles.logTray}><div className={styles.logCard}>
                    {visibleLogs.map(log => (
                        <div
                            key={log.id}
                            className={`${styles.logRow} ${expandedId === log.id ? styles.expanded : ''}`}
                            style={{ '--rail': actionColor(log.action) }}
                            onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                            role="button"
                            tabIndex={0}
                            aria-expanded={expandedId === log.id}
                            aria-label={`Log entry: ${friendlyAction(log.action)} by ${log.performedBy}`}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedId(expandedId === log.id ? null : log.id); } }}
                        >
                            <div className={styles.logMain}>
                                <div className={styles.timeMark}>
                                    <div className={styles.clockPair}>
                                        <FiClock aria-hidden="true" />
                                        <span>{plainStamp(log.timestamp).slice(11, 16)}</span>
                                    </div>
                                    <small>{plainStamp(log.timestamp).slice(0, 10)}</small>
                                </div>
                                <div className={styles.actionMark}>
                                    <div className={styles.iconChassis} aria-hidden="true">
                                        {log.action === 'RECOVERY_NOTE' ? <FiPhoneCall aria-hidden="true" /> :
                                         log.performedBy === 'SYSTEM' ? <FiActivity aria-hidden="true" /> : <FiUser aria-hidden="true" />}
                                    </div>
                                    <div className={styles.actionMeta}>
                                        <strong>{friendlyAction(log.action)}</strong>
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
                    {/* fix181 (10.4): page 0 is the NEWEST; the labels now say what the buttons do */}
                    <button className={styles.pgBtn} disabled={page === 0 || loading} onClick={() => setPage(p => Math.max(0, p - 1))} aria-label="Newer lines">
                        <FiChevronLeft aria-hidden="true" /> NEWER
                    </button>
                    <span className={styles.pageLabel} aria-current="page">PAGE {meta.totalPages === 0 ? 0 : page + 1} OF {meta.totalPages.toLocaleString()}</span>
                    <button className={styles.pgBtn} onClick={() => setPage(p => p + 1)} disabled={meta.last || loading} aria-label="Older lines">
                        OLDER <FiChevronRight aria-hidden="true" />
                    </button>
                </footer>
                <CornerDecor hideTop />
            </div>
        </div>
    );
};

export default AuditPage;