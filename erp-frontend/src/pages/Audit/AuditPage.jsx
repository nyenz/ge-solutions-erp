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

/* fix181 (10.1, 13.9): two dropdowns built from the catalog. PROTOCOL CLASS = all actions or one group (sends the
   group's codes); ACTION appears when a group is chosen and lists that group's actions by friendly name (sends one
   code). The friendly text on screen is never sent: a small label -> code map is kept here. */
const ALL_IN_GROUP = 'ALL IN THIS GROUP';
const CLASS_OPTIONS = [ALL_ACTIONS, ...ACTION_GROUPS.map(g => g.group)];
const groupOf = (name) => ACTION_GROUPS.find(g => g.group === name);
const actionOptionsOf = (name) => [ALL_IN_GROUP, ...(groupOf(name)?.actions || []).map(a => a.label)];
const codesFor = (group, action) => {
    const g = groupOf(group);
    if (!g) return [];
    if (!action || action === ALL_IN_GROUP) return g.actions.map(a => a.code);
    const hit = g.actions.find(a => a.label === action);
    return hit ? [hit.code] : g.actions.map(a => a.code);
};
const EMPTY_FILTERS = { operator: '', group: '', action: '', search: '', from: '', to: '', page: 0 };

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
    const [expandedId, setExpandedId] = useState(null);
    // fix181 (13.10b): the page number lives in the same state as the filters, so a filter change resets it in the same
    // update (one request, not two)
    const [filters,    setFiltersRaw] = useState(EMPTY_FILTERS);
    const setFilters = useCallback((next) => setFiltersRaw({ ...next, page: 0 }), []);
    const page = filters.page;
    const setPage = (fn) => setFiltersRaw(f => ({ ...f, page: typeof fn === 'function' ? fn(f.page) : fn }));
    // fix181 (13.10a): the keyword is sent 400 ms after the last key, and only from 2 letters
    const [searchText, setSearchText] = useState('');
    useEffect(() => {
        const t = setTimeout(() => {
            const k = searchText.trim();
            const next = k.length >= 2 ? k : '';
            setFiltersRaw(f => (f.search === next ? f : { ...f, search: next, page: 0 }));
        }, 400);
        return () => clearTimeout(t);
    }, [searchText]);
    const [copiedId, setCopiedId] = useState(null);
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
        actions: filters.group && filters.group !== ALL_ACTIONS ? codesFor(filters.group, filters.action) : [],
        keyword: filters.search.trim().slice(0, 100),
        start: filters.from ? filters.from + 'T00:00:00' : null,
        end: filters.to ? dayAfter(filters.to) : null,
    }), [filters.operator, filters.group, filters.action, filters.search, filters.from, filters.to]);

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
            auditService.logExport({ ...serverFilters, group: filters.group || ALL_ACTIONS, action: filters.action || '' }, all.length);
            setExporting(total > all.length ? `Exported the newest ${all.length.toLocaleString()} of ${total.toLocaleString()} rows (the limit).` : '');
        } catch (e) {
            setExporting('Export failed: ' + e.message);
        }
    };

    const operatorOptions = [ALL_STAFF, ...operators];

    // fix181 (13.11): one line that quotes an audit row exactly
    const lineOf = (log) => `${plainStamp(log.timestamp)} | ${log.performedBy} | ${log.action} | ${log.details || ''} | id ${log.id}`;
    const copyLine = async (e, log) => {
        e.stopPropagation();
        try { await navigator.clipboard.writeText(lineOf(log)); setCopiedId(log.id); setTimeout(() => setCopiedId(null), 1500); }
        catch { setCopiedId(null); }
    };

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
                        className={`${styles.searchInput} ${(searchText || isSearchFocused) ? styles.searchInputActive : ''}`}
                        value={searchText}
                        maxLength={100}
                        onChange={e => setSearchText(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)}
                        aria-label="Search forensic logs"
                    />
                    {!(searchText || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}
                    {searchText && (
                        <button className={styles.searchClear} onClick={() => setSearchText('')} aria-label="Clear search">
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
                            label="PROTOCOL CLASS"
                            options={CLASS_OPTIONS}
                            value={filters.group || ALL_ACTIONS}
                            onChange={val => setFilters({...filters, group: val === ALL_ACTIONS ? '' : val, action: ''})}
                        />
                    </div>
                    {filters.group && (
                        <div className={styles.hwSelectWrap}>
                            <HardwareSelect
                                label="ACTION"
                                options={actionOptionsOf(filters.group)}
                                value={filters.action || ALL_IN_GROUP}
                                onChange={val => setFilters({...filters, action: val === ALL_IN_GROUP ? '' : val})}
                            />
                        </div>
                    )}
                    <label className={styles.dateField}>
                        <span>FROM</span>
                        <HardwareDatePicker value={filters.from} ariaLabel="From date" onChange={v => setFilters({...filters, from: v})} />
                    </label>
                    <label className={styles.dateField}>
                        <span>TO</span>
                        <HardwareDatePicker value={filters.to} ariaLabel="To date" onChange={v => setFilters({...filters, to: v})} />
                    </label>
                    <button className={styles.resetBtn} onClick={() => { setSearchText(''); setFiltersRaw(EMPTY_FILTERS); }} aria-label="Reset all filters">
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
                                        <FiDatabase aria-hidden="true" /> <span>AUDIT LINE</span>
                                        <button type="button" className={styles.resetBtn} onClick={(e) => copyLine(e, log)} aria-label="Copy this line">
                                            {copiedId === log.id ? 'COPIED' : 'COPY LINE'}
                                        </button>
                                    </div>
                                    {/* fix181 (13.11): the facts an auditor quotes: code, exact time, person, row id */}
                                    <dl className={styles.factList}>
                                        <dt>Code</dt><dd>{log.action}</dd>
                                        <dt>Time</dt><dd>{plainStamp(log.timestamp)}</dd>
                                        <dt>Operator</dt><dd>{log.performedBy}</dd>
                                        <dt>Row id</dt><dd>{log.id}</dd>
                                    </dl>
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