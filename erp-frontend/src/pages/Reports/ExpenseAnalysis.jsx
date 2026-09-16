// PATH: erp-frontend/src/pages/Reports/ExpenseAnalysis.jsx
// The Director expense analysis, moved here from the Expenses page.
//
// Expenses is a data-entry screen -- "log the cash that just left the office"
// -- and hanging a four-section analytics dashboard plus a full-table search
// off a toggle in its header made it two products in one. Reports is where
// every other "read the numbers back to me" surface already lives, so this
// mounts as a drawer there instead.
//
// Nothing was dropped in the move: same expenseService calls, same period and
// bucket toggles, same by-category / by-staff bars, same time series, same
// filter set, and the same 100-row truncation flag.
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiChevronDown } from 'react-icons/fi';
import expenseService from '../../services/expenseService';
import { LoadingState } from '../../components/common/LoadingState';
import { Tooltip, Term } from '../../components/common/Tooltip';
import { GLOSSARY } from '../../components/common/glossary';
import { useToasts } from '../../components/common/useFeedback';
import { ToastStack } from '../../components/common/Feedback';
import styles from './ExpenseAnalysis.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const SEARCH_LIMIT = 100;
const EMPTY_FILTERS = { from: '', to: '', category: '', recordedBy: '', spentBy: '', minAmount: '', maxAmount: '' };

const ExpenseAnalysis = ({ active = true }) => {
    const { toasts, toast, dismissToast } = useToasts();

    const [period, setPeriod] = useState('MONTH');
    const [bucket, setBucket] = useState('DAY');

    const [summary, setSummary] = useState({ total: 0, byCategory: {} });
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [byStaff, setByStaff] = useState({});
    const [staffLoading, setStaffLoading] = useState(false);
    const [series, setSeries] = useState([]);
    const [seriesLoading, setSeriesLoading] = useState(false);

    const [categories, setCategories] = useState([]);
    const [filters, setFilters] = useState(EMPTY_FILTERS);
    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);

    const [categoryDropdownOpen, setCategoryDropdownOpen] = useState(false);
    const categoryDropdownRef = useRef(null);
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (categoryDropdownRef.current && !categoryDropdownRef.current.contains(e.target)) {
                setCategoryDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const loadSummary = useCallback(async (p) => {
        setSummaryLoading(true);
        try {
            const data = await expenseService.getSummary(p);
            setSummary(data || { total: 0, byCategory: {} });
        } catch {
            toast('Could not load the analysis summary.', 'error');
        } finally {
            setSummaryLoading(false);
        }
    }, [toast]);

    const loadByStaff = useCallback(async (p) => {
        setStaffLoading(true);
        try {
            const data = await expenseService.getByStaff(p);
            setByStaff(data || {});
        } catch {
            toast('Could not load the staff breakdown.', 'error');
        } finally {
            setStaffLoading(false);
        }
    }, [toast]);

    const loadSeries = useCallback(async (p, b) => {
        setSeriesLoading(true);
        try {
            const data = await expenseService.getTimeSeries(p, undefined, undefined, b);
            setSeries(data || []);
        } catch {
            toast('Could not load the spending trend.', 'error');
        } finally {
            setSeriesLoading(false);
        }
    }, [toast]);

    // Only fetch while the drawer is actually open -- a closed drawer on the
    // Report Hub should not be firing three calls on every period change.
    useEffect(() => {
        if (!active) return;
        loadSummary(period);
        loadByStaff(period);
        loadSeries(period, bucket);
    }, [active, period, bucket, loadSummary, loadByStaff, loadSeries]);

    useEffect(() => {
        if (!active) return;
        let cancelled = false;
        expenseService.getCategories()
            .then(data => { if (!cancelled) setCategories(data || []); })
            .catch(() => { /* the dropdown just falls back to ALL CATEGORIES */ });
        return () => { cancelled = true; };
    }, [active]);

    const filterableCategories = useMemo(
        () => [...new Set((categories || []).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
        [categories],
    );

    const runSearch = async () => {
        // F5: a min above a max used to just return an empty list, which reads
        // as "no such expenses" rather than "your filter is impossible".
        const min = filters.minAmount === '' ? null : Number(filters.minAmount);
        const max = filters.maxAmount === '' ? null : Number(filters.maxAmount);
        if (min !== null && max !== null && min > max) {
            toast('Min UGX is higher than Max UGX -- nothing can match that.', 'error');
            return;
        }
        if (filters.from && filters.to && filters.from > filters.to) {
            toast('The From date is after the To date.', 'error');
            return;
        }
        setSearching(true);
        try {
            const cleanFilters = Object.fromEntries(
                Object.entries(filters).filter(([, v]) => v !== '' && v !== null)
            );
            const data = await expenseService.search(cleanFilters, 0, SEARCH_LIMIT);
            setSearchResults(data.content || []);
        } catch {
            toast('Search failed.', 'error');
        } finally {
            setSearching(false);
        }
    };

    const clearSearch = () => {
        setFilters(EMPTY_FILTERS);
        setSearchResults(null);
    };

    const searchTotal = useMemo(
        () => (searchResults || []).reduce((sum, e) => sum + Number(e.amount || 0), 0),
        [searchResults],
    );
    const maxCategoryAmount = useMemo(() => {
        const vals = Object.values(summary.byCategory || {});
        return vals.length ? Math.max(...vals.map(Number)) : 0;
    }, [summary]);
    const maxStaffAmount = useMemo(() => {
        const vals = Object.values(byStaff || {});
        return vals.length ? Math.max(...vals.map(Number)) : 0;
    }, [byStaff]);
    const maxSeriesAmount = useMemo(
        () => (series.length ? Math.max(...series.map(pt => Number(pt.total))) : 0),
        [series],
    );

    const Bars = ({ data, loading, loadingLabel, emptyLabel, max }) => {
        if (loading) return <LoadingState label={loadingLabel} tone="bare" />;
        const entries = Object.entries(data || {});
        if (entries.length === 0) return <div className={styles.emptyCell}>{emptyLabel}</div>;
        return (
            <div className={styles.bars}>
                {entries.map(([key, amt]) => (
                    <div key={key} className={styles.barRow}>
                        <span className={styles.barLabel}>
                            <Tooltip label={`${key}: UGX ${fmt(amt)}`}><span>{key}</span></Tooltip>
                        </span>
                        <div className={styles.barTrack}>
                            <div
                                className={styles.barFill}
                                style={{ width: max ? `${(Number(amt) / max) * 100}%` : '0%' }}
                            />
                        </div>
                        <span className={styles.barValue}>UGX {fmt(amt)}</span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className={styles.wrap}>
            <div className={styles.toggleRow}>
                {[
                    ['TODAY', 'Since midnight today'],
                    ['WEEK', 'The last 7 days'],
                    ['MONTH', 'The last 30 days'],
                    ['YEAR', 'The last 365 days'],
                ].map(([p, tip]) => (
                    <Tooltip key={p} label={tip}>
                        <button
                            className={period === p ? styles.toggleBtnActive : styles.toggleBtn}
                            onClick={() => setPeriod(p)}
                            aria-pressed={period === p}
                        >
                            {p}
                        </button>
                    </Tooltip>
                ))}
            </div>

            <div className={styles.totalCard}>
                <label>TOTAL SPENT ({period})</label>
                {summaryLoading
                    ? <LoadingState label="SYNCING TOTAL..." tone="bare" />
                    : <strong>UGX {fmt(summary.total)}</strong>}
            </div>

            <div className={styles.sectionLabel}>
                <Term tip="Every expense in this period, added up per category, biggest first.">BY CATEGORY</Term>
            </div>
            <Bars
                data={summary.byCategory}
                loading={summaryLoading}
                loadingLabel="SYNCING CATEGORIES..."
                emptyLabel="NO EXPENSES IN THIS PERIOD"
                max={maxCategoryAmount}
            />

            <div className={styles.sectionLabel}>
                <Term tip={GLOSSARY.SPENT_BY}>BY STAFF (WHO SPENT IT)</Term>
            </div>
            <Bars
                data={byStaff}
                loading={staffLoading}
                loadingLabel="SYNCING STAFF BREAKDOWN..."
                emptyLabel="NO EXPENSES IN THIS PERIOD"
                max={maxStaffAmount}
            />

            <div className={styles.sectionLabel}>SPENDING OVER TIME</div>
            <div className={styles.toggleRow}>
                {[
                    ['DAY', 'One bar per day'],
                    ['WEEK', 'One bar per week'],
                    ['MONTH', 'One bar per month'],
                ].map(([b, tip]) => (
                    <Tooltip key={b} label={tip}>
                        <button
                            className={bucket === b ? styles.toggleBtnActive : styles.toggleBtn}
                            onClick={() => setBucket(b)}
                            aria-pressed={bucket === b}
                        >
                            {b}
                        </button>
                    </Tooltip>
                ))}
            </div>
            {seriesLoading ? (
                <LoadingState label="LOADING TREND..." tone="bare" />
            ) : series.length === 0 ? (
                <div className={styles.emptyCell}>NO ACTIVITY IN THIS WINDOW</div>
            ) : (
                <div className={styles.tsChart}>
                    {series.map(point => (
                        <Tooltip key={point.bucket} label={`${point.bucket}: UGX ${fmt(point.total)}`}>
                            <div className={styles.tsBarWrap}>
                                <div className={styles.tsBarTrack}>
                                    <div
                                        className={styles.tsBarFill}
                                        style={{ height: maxSeriesAmount ? `${Math.max(2, (Number(point.total) / maxSeriesAmount) * 100)}%` : '2%' }}
                                    />
                                </div>
                                <span className={styles.tsBarLabel}>{point.bucket.slice(-5)}</span>
                            </div>
                        </Tooltip>
                    ))}
                </div>
            )}

            <div className={styles.divider}>
                <div className={styles.sectionLabel}>SEARCH ALL EXPENSES</div>
            </div>
            <div className={styles.filterRow}>
                <Tooltip label="Only show expenses logged on or after this date">
                    <input type="date" className={styles.filterInput} value={filters.from}
                        aria-label="From date"
                        onChange={e => setFilters({ ...filters, from: e.target.value })} />
                </Tooltip>
                <Tooltip label="Only show expenses logged on or before this date">
                    <input type="date" className={styles.filterInput} value={filters.to}
                        aria-label="To date"
                        onChange={e => setFilters({ ...filters, to: e.target.value })} />
                </Tooltip>
                <div className={styles.categoryDropdown} ref={categoryDropdownRef}>
                    <Tooltip label="Every category ever used -- preset tiles and anything typed in under OTHER">
                        <button
                            type="button"
                            className={styles.categoryDropdownBtn}
                            onClick={() => setCategoryDropdownOpen(o => !o)}
                            aria-expanded={categoryDropdownOpen}
                        >
                            <span>{filters.category || 'ALL CATEGORIES'}</span>
                            <FiChevronDown className={categoryDropdownOpen ? styles.categoryDropdownIconOpen : ''} aria-hidden="true" />
                        </button>
                    </Tooltip>
                    {categoryDropdownOpen && (
                        <div className={styles.categoryDropdownList} role="listbox">
                            <div
                                role="option"
                                aria-selected={!filters.category}
                                className={`${styles.categoryDropdownOption} ${!filters.category ? styles.categoryDropdownOptionActive : ''}`}
                                onClick={() => { setFilters({ ...filters, category: '' }); setCategoryDropdownOpen(false); }}
                            >
                                ALL CATEGORIES
                            </div>
                            {filterableCategories.map(name => (
                                <div
                                    key={name}
                                    role="option"
                                    aria-selected={filters.category === name}
                                    className={`${styles.categoryDropdownOption} ${filters.category === name ? styles.categoryDropdownOptionActive : ''}`}
                                    onClick={() => { setFilters({ ...filters, category: name }); setCategoryDropdownOpen(false); }}
                                >
                                    {name}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                <Tooltip label="The staff member who typed the entry into the system">
                    <input type="text" className={styles.filterInput} placeholder="Logged by..."
                        aria-label="Logged by"
                        value={filters.recordedBy} onChange={e => setFilters({ ...filters, recordedBy: e.target.value })} />
                </Tooltip>
                <Tooltip label={GLOSSARY.SPENT_BY}>
                    <input type="text" className={styles.filterInput} placeholder="Spent by..."
                        aria-label="Spent by"
                        value={filters.spentBy} onChange={e => setFilters({ ...filters, spentBy: e.target.value })} />
                </Tooltip>
                <Tooltip label="Hide anything cheaper than this">
                    <input type="number" className={styles.filterInput} placeholder="Min UGX"
                        aria-label="Minimum amount"
                        value={filters.minAmount} onChange={e => setFilters({ ...filters, minAmount: e.target.value })} />
                </Tooltip>
                <Tooltip label="Hide anything more expensive than this">
                    <input type="number" className={styles.filterInput} placeholder="Max UGX"
                        aria-label="Maximum amount"
                        value={filters.maxAmount} onChange={e => setFilters({ ...filters, maxAmount: e.target.value })} />
                </Tooltip>
                <Tooltip label={`Search every expense ever logged (returns up to ${SEARCH_LIMIT} entries)`}>
                    <button className={styles.toggleBtnActive} onClick={runSearch} disabled={searching}>
                        <FiSearch size={12} aria-hidden="true" /> {searching ? 'SEARCHING...' : 'SEARCH'}
                    </button>
                </Tooltip>
                {searchResults && (
                    <Tooltip label="Reset every filter and hide these results">
                        <button className={styles.toggleBtn} onClick={clearSearch}>
                            <FiX size={12} aria-hidden="true" /> CLEAR
                        </button>
                    </Tooltip>
                )}
            </div>

            {searchResults && (
                <>
                    {/* F4: the old version silently stopped at 100 rows, so a
                        truncated list could be read as the whole truth. */}
                    <div className={styles.searchSummary}>
                        <span>
                            {searchResults.length} {searchResults.length === 1 ? 'ENTRY' : 'ENTRIES'}
                            {' -- '}UGX {fmt(searchTotal)} TOTAL
                        </span>
                        {searchResults.length >= SEARCH_LIMIT && (
                            <Term tip={`Only the first ${SEARCH_LIMIT} matches are shown. Narrow the dates or the amount range to see the rest.`}>
                                <span className={styles.truncatedFlag}>SHOWING FIRST {SEARCH_LIMIT} ONLY</span>
                            </Term>
                        )}
                    </div>
                    <div className={styles.tableScroll}>
                        <table className={styles.ledgerTable}>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Category</th>
                                    <th>Amount (UGX)</th>
                                    <th>Logged By</th>
                                    <th>Spent By</th>
                                    <th>Note</th>
                                </tr>
                            </thead>
                            <tbody>
                                {searchResults.length === 0 ? (
                                    <tr><td colSpan="6" className={styles.emptyCell}>NO RESULTS</td></tr>
                                ) : searchResults.map(e => (
                                    <tr key={e.id}>
                                        <td className={styles.dateCell}>{new Date(e.createdAt).toLocaleDateString()}</td>
                                        <td><span className={styles.categoryTag}>{e.category}</span></td>
                                        <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                        <td className={styles.metaCell}>{e.recordedBy}</td>
                                        <td className={styles.metaCell}>{e.spentBy || e.recordedBy}</td>
                                        <td className={styles.notesCell}>
                                            {e.note
                                                ? <Tooltip label={e.note}><span>{e.note}</span></Tooltip>
                                                : <span className={styles.noNote}>---</span>}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            <ToastStack toasts={toasts} onDismiss={dismissToast} />
        </div>
    );
};

export default ExpenseAnalysis;
