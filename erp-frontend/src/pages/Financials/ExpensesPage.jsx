// PATH: erp-frontend/src/pages/Financials/ExpensesPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
    FiTrendingDown, FiPlus, FiRefreshCw, FiEdit2, FiTrash2,
    FiBarChart2, FiX, FiSearch, FiClock, FiChevronDown, FiLock, FiInfo
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import expenseService from '../../services/expenseService';
import HardwarePanel from '../../components/ui/HardwarePanel';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import { LoadingState, LoadingRow } from '../../components/common/LoadingState';
import { Tooltip, IconButton, Term } from '../../components/common/Tooltip';
import { GLOSSARY } from '../../components/common/glossary';
import { useToasts, useConfirm } from '../../components/common/useFeedback';
import { ToastStack, ConfirmDialog } from '../../components/common/Feedback';
import styles from './ExpensesPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const EDIT_WINDOW_HOURS = 24;
const SEARCH_LIMIT = 100;

const isStillEditable = (createdAt) => {
    if (!createdAt) return false;
    const ageMs = Date.now() - new Date(createdAt).getTime();
    return ageMs < EDIT_WINDOW_HOURS * 60 * 60 * 1000;
};

const hoursLeft = (createdAt) => {
    const ageMs = Date.now() - new Date(createdAt).getTime();
    const remaining = EDIT_WINDOW_HOURS * 60 * 60 * 1000 - ageMs;
    return Math.max(0, Math.ceil(remaining / (60 * 60 * 1000)));
};

const ExpensesPage = () => {
    const { user } = useAuth();
    const isDirector = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';

    const { toasts, toast, dismissToast } = useToasts();
    const { confirmState, confirm, handleAnswer } = useConfirm();

    const [presets, setPresets] = useState([]);
    const [recent, setRecent] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);

    // F3: the 24h edit window used to be judged only at render time, so a row
    // kept its edit button until someone reloaded the page. This tick makes
    // the row flip to LOCKED on its own, within a minute of the window closing.
    const [, setClockTick] = useState(0);
    useEffect(() => {
        const id = setInterval(() => setClockTick(t => t + 1), 60 * 1000);
        return () => clearInterval(id);
    }, []);

    const loadAll = useCallback(async () => {
        setLoading(true);
        try {
            const [presetData, recentData, categoryData] = await Promise.all([
                expenseService.getPresets(),
                expenseService.getRecent(EDIT_WINDOW_HOURS),
                expenseService.getCategories(),
            ]);
            setPresets(presetData || []);
            setRecent(recentData || []);
            setCategories(categoryData || []);
        } catch {
            toast('Could not load expenses. Check your connection.', 'error');
        } finally {
            setLoading(false);
        }
    }, [toast]);

    useEffect(() => { loadAll(); }, [loadAll]);

    // -- LOG MODAL (tap a preset, or OTHER) --------------------------
    const [logModal, setLogModal] = useState({ open: false, presetName: '', isOther: false });
    const [logCategory, setLogCategory] = useState('');
    const [logAmount, setLogAmount] = useState('');
    const [logNote, setLogNote] = useState('');
    const [logSpentBy, setLogSpentBy] = useState('');
    const [logging, setLogging] = useState(false);

    const openLogModal = (presetName) => {
        setLogModal({ open: true, presetName, isOther: false });
        setLogCategory(presetName);
        setLogAmount('');
        setLogNote('');
        setLogSpentBy('');
    };
    const openOtherModal = () => {
        setLogModal({ open: true, presetName: '', isOther: true });
        setLogCategory('');
        setLogAmount('');
        setLogNote('');
        setLogSpentBy('');
    };
    const closeLogModal = () => setLogModal({ open: false, presetName: '', isOther: false });

    const submitLog = async () => {
        if (logModal.isOther && !logCategory.trim()) { toast('What is this expense for?', 'error'); return; }
        if (!logAmount || Number(logAmount) <= 0) { toast('Enter an amount.', 'error'); return; }
        setLogging(true);
        try {
            await expenseService.create({
                category: (logModal.isOther ? logCategory : logModal.presetName).trim(),
                amount: Number(logAmount),
                note: logNote,
                spentBy: logSpentBy,
            });
            closeLogModal();
            await loadAll();
            toast('Expense logged.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not log this expense.', 'error');
        } finally {
            setLogging(false);
        }
    };

    // -- NEW PRESET MODAL ------------------------------------------
    const [presetModal, setPresetModal] = useState(false);
    const [newPresetName, setNewPresetName] = useState('');
    const [savingPreset, setSavingPreset] = useState(false);

    const submitPreset = async () => {
        if (!newPresetName.trim()) { toast('Enter a name for this preset.', 'error'); return; }
        setSavingPreset(true);
        try {
            await expenseService.createPreset(newPresetName.trim());
            setPresetModal(false);
            setNewPresetName('');
            await loadAll();
            toast('Preset added.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not create this preset.', 'error');
        } finally {
            setSavingPreset(false);
        }
    };

    // -- EDIT MODAL (within 24h only) --------------------------------
    const [editModal, setEditModal] = useState({ open: false, expense: null });
    const [editCategory, setEditCategory] = useState('');
    const [editAmount, setEditAmount] = useState('');
    const [editNote, setEditNote] = useState('');
    const [editSpentBy, setEditSpentBy] = useState('');
    const [saving, setSaving] = useState(false);

    const openEdit = (expense) => {
        setEditModal({ open: true, expense });
        setEditCategory(expense.category);
        setEditAmount(String(expense.amount));
        setEditNote(expense.note || '');
        setEditSpentBy(expense.spentBy || '');
    };

    const submitEdit = async () => {
        if (!editAmount || Number(editAmount) <= 0) { toast('Enter an amount.', 'error'); return; }
        setSaving(true);
        try {
            await expenseService.update(editModal.expense.id, {
                category: editCategory.trim(),
                amount: Number(editAmount),
                note: editNote,
                spentBy: editSpentBy,
            });
            setEditModal({ open: false, expense: null });
            await loadAll();
            toast('Expense updated.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not save this edit.', 'error');
        } finally {
            setSaving(false);
        }
    };

    // F2: deletingId guards against a double-click firing two deletes.
    const [deletingId, setDeletingId] = useState(null);

    const handleDelete = async (expense) => {
        if (deletingId) return;
        const ok = await confirm(
            'DELETE EXPENSE',
            `Delete the ${expense.category} entry of UGX ${fmt(expense.amount)}? This cannot be undone.`,
            'danger',
        );
        if (!ok) return;
        setDeletingId(expense.id);
        try {
            await expenseService.remove(expense.id);
            await loadAll();
            toast('Entry deleted.', 'warn');
        } catch {
            toast('Could not delete this entry.', 'error');
        } finally {
            setDeletingId(null);
        }
    };

    // -- DIRECTOR ANALYSIS --------------------------------------------
    const [analysisOpen, setAnalysisOpen] = useState(false);
    const [period, setPeriod] = useState('MONTH');
    const [summary, setSummary] = useState({ total: 0, byCategory: {} });
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [byStaff, setByStaff] = useState({});
    const [staffLoading, setStaffLoading] = useState(false);
    const [series, setSeries] = useState([]);
    const [bucket, setBucket] = useState('DAY');
    const [seriesLoading, setSeriesLoading] = useState(false);

    const [filters, setFilters] = useState({ from: '', to: '', category: '', recordedBy: '', spentBy: '', minAmount: '', maxAmount: '' });
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

    // F1: the dropdown used to list PRESETS only, so anything logged through
    // OTHER was unfilterable. The full category list was already being loaded
    // for the datalist -- this just uses it.
    const filterableCategories = useMemo(() => {
        const names = new Set();
        presets.forEach(p => p.name && names.add(p.name));
        categories.forEach(c => c && names.add(c));
        return [...names].sort((a, b) => a.localeCompare(b));
    }, [presets, categories]);

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

    useEffect(() => {
        if (isDirector && analysisOpen) {
            loadSummary(period);
            loadByStaff(period);
            loadSeries(period, bucket);
        }
    }, [isDirector, analysisOpen, period, bucket, loadSummary, loadByStaff, loadSeries]);

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
        setFilters({ from: '', to: '', category: '', recordedBy: '', spentBy: '', minAmount: '', maxAmount: '' });
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

    const maxSeriesAmount = useMemo(() => {
        return series.length ? Math.max(...series.map(pt => Number(pt.total))) : 0;
    }, [series]);

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Expenses</h1>
                    <p className={styles.subtitle}>Log any cash that leaves the office</p>
                </div>
                <div className={styles.headerActions}>
                    <Tooltip label="Reload the presets and the last 24 hours of entries">
                        <button className={styles.refreshBtn} onClick={loadAll} aria-label="Refresh expenses">
                            <FiRefreshCw size={13} aria-hidden="true" /> REFRESH
                        </button>
                    </Tooltip>
                    {isDirector && (
                        <Tooltip label="Directors only: totals by category, by staff, spending over time, and a full search">
                            <button
                                className={analysisOpen ? styles.analysisBtnActive : styles.analysisBtn}
                                onClick={() => setAnalysisOpen(o => !o)}
                                aria-expanded={analysisOpen}
                            >
                                <FiBarChart2 size={14} aria-hidden="true" /> ANALYSIS
                            </button>
                        </Tooltip>
                    )}
                </div>
            </header>

            {/* Shared autocomplete source for every "type it yourself" category field */}
            <datalist id="expense-categories">
                {filterableCategories.map(c => <option key={c} value={c} />)}
            </datalist>

            {/* PRESET GRID -- ONE TAP LOGGING */}
            <HardwarePanel title="LOG AN EXPENSE" icon={FiTrendingDown}>
                <div className={styles.presetGrid}>
                    {presets.map(p => (
                        <Tooltip key={p.id} label={`Log a ${p.name} expense`}>
                            <button className={styles.presetTile} onClick={() => openLogModal(p.name)}>
                                {p.name.toUpperCase()}
                            </button>
                        </Tooltip>
                    ))}
                    <Tooltip label="Anything with no tile -- you type what it was for">
                        <button className={styles.presetTileOther} onClick={openOtherModal}>
                            OTHER
                        </button>
                    </Tooltip>
                    <Tooltip label="Add a new tile for a cost you log often">
                        <button className={styles.presetTileNew} onClick={() => setPresetModal(true)}>
                            <FiPlus size={16} aria-hidden="true" /> NEW PRESET
                        </button>
                    </Tooltip>
                </div>
            </HardwarePanel>

            {/* RECENT ENTRIES -- EDITABLE WITHIN 24H */}
            <div className={styles.panelSpacer}>
                <HardwarePanel title="RECENT ENTRIES (LAST 24H)" icon={FiClock}>
                    <p className={styles.panelHint}>
                        <FiInfo size={12} aria-hidden="true" />
                        You can edit your own entries for {EDIT_WINDOW_HOURS} hours. After that they lock.
                    </p>
                    <div className={styles.tableWrap}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>TIME</th>
                                    <th>CATEGORY</th>
                                    <th>AMOUNT</th>
                                    <th>LOGGED BY</th>
                                    <th>NOTE</th>
                                    <th><span className={styles.srOnly}>Actions</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <LoadingRow colSpan={6} label="LOADING EXPENSES..." />
                                ) : recent.length === 0 ? (
                                    <tr><td colSpan="6" className={styles.emptyCell}>NO EXPENSES LOGGED IN THE LAST 24 HOURS</td></tr>
                                ) : recent.map(e => {
                                    const editable = isStillEditable(e.createdAt);
                                    return (
                                        <tr key={e.id} className={deletingId === e.id ? styles.rowBusy : undefined}>
                                            <td className={styles.dateCell}>
                                                {new Date(e.createdAt).toLocaleString()}
                                            </td>
                                            <td>
                                                <Tooltip label={GLOSSARY.CATEGORY}>
                                                    <span className={styles.categoryTag}>{e.category}</span>
                                                </Tooltip>
                                                {e.editedAt && (
                                                    <Tooltip label={GLOSSARY.EDITED}>
                                                        <span className={styles.editedBadge}>EDITED</span>
                                                    </Tooltip>
                                                )}
                                            </td>
                                            <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                            <td className={styles.metaCell}>
                                                {e.recordedBy}
                                                {e.spentBy && e.spentBy !== e.recordedBy && (
                                                    <Tooltip label={GLOSSARY.SPENT_BY}>
                                                        <span className={styles.spentByTag}>SPENT: {e.spentBy}</span>
                                                    </Tooltip>
                                                )}
                                            </td>
                                            <td className={styles.notesCell}>
                                                {e.note
                                                    ? <Tooltip label={e.note}><span>{e.note}</span></Tooltip>
                                                    : <span className={styles.noNote}>---</span>}
                                            </td>
                                            <td>
                                                <div className={styles.rowActions}>
                                                    {editable ? (
                                                        <IconButton
                                                            tip={`Edit this entry -- ${hoursLeft(e.createdAt)}h left before it locks`}
                                                            icon={FiEdit2}
                                                            className={styles.editIconBtn}
                                                            onClick={() => openEdit(e)}
                                                        />
                                                    ) : (
                                                        <Term tip={GLOSSARY.LOCKED} className={styles.lockedTag}>
                                                            <FiLock size={10} aria-hidden="true" /> LOCKED
                                                        </Term>
                                                    )}
                                                    {isDirector && (
                                                        <IconButton
                                                            tip="Delete this entry permanently (Directors only)"
                                                            icon={FiTrash2}
                                                            className={styles.deleteIconBtn}
                                                            onClick={() => handleDelete(e)}
                                                            disabled={deletingId === e.id}
                                                        />
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </HardwarePanel>
            </div>

            {/* DIRECTOR ANALYSIS */}
            {isDirector && analysisOpen && (
                <div className={styles.panelSpacer}>
                    <HardwarePanel title="ANALYSIS" icon={FiBarChart2}>
                        <div className={styles.periodRow}>
                            {[
                                ['TODAY', 'Since midnight today'],
                                ['WEEK', 'The last 7 days'],
                                ['MONTH', 'The last 30 days'],
                                ['YEAR', 'The last 365 days'],
                            ].map(([p, tip]) => (
                                <Tooltip key={p} label={tip}>
                                    <button
                                        className={period === p ? styles.periodBtnActive : styles.periodBtn}
                                        onClick={() => setPeriod(p)}
                                        aria-pressed={period === p}
                                    >
                                        {p}
                                    </button>
                                </Tooltip>
                            ))}
                        </div>

                        <div className={styles.totalBox}>
                            <label>TOTAL SPENT ({period})</label>
                            {summaryLoading
                                ? <LoadingState label="SYNCING TOTAL..." tone="bare" />
                                : <strong>UGX {fmt(summary.total)}</strong>}
                        </div>

                        <div className={styles.sectionLabel}>
                            <Term tip="Every expense in this period, added up per category, biggest first.">BY CATEGORY</Term>
                        </div>
                        <div className={styles.categoryBars}>
                            {summaryLoading ? (
                                <LoadingState label="SYNCING CATEGORIES..." tone="bare" />
                            ) : (
                                <>
                                    {Object.entries(summary.byCategory || {}).map(([cat, amt]) => (
                                        <div key={cat} className={styles.barRow}>
                                            <span className={styles.barLabel} >
                                                <Tooltip label={`${cat}: UGX ${fmt(amt)}`}><span>{cat}</span></Tooltip>
                                            </span>
                                            <div className={styles.barTrack}>
                                                <div
                                                    className={styles.barFill}
                                                    style={{ width: maxCategoryAmount ? `${(Number(amt) / maxCategoryAmount) * 100}%` : '0%' }}
                                                />
                                            </div>
                                            <span className={styles.barValue}>UGX {fmt(amt)}</span>
                                        </div>
                                    ))}
                                    {Object.keys(summary.byCategory || {}).length === 0 && (
                                        <div className={styles.emptyCell}>NO EXPENSES IN THIS PERIOD</div>
                                    )}
                                </>
                            )}
                        </div>

                        <div className={styles.sectionLabel}>
                            <Term tip={GLOSSARY.SPENT_BY}>BY STAFF (WHO SPENT IT)</Term>
                        </div>
                        <div className={styles.categoryBars}>
                            {staffLoading ? (
                                <LoadingState label="SYNCING STAFF BREAKDOWN..." tone="bare" />
                            ) : (
                                <>
                                    {Object.entries(byStaff || {}).map(([who, amt]) => (
                                        <div key={who} className={styles.barRow}>
                                            <span className={styles.barLabel}>
                                                <Tooltip label={`${who}: UGX ${fmt(amt)}`}><span>{who}</span></Tooltip>
                                            </span>
                                            <div className={styles.barTrack}>
                                                <div
                                                    className={styles.barFill}
                                                    style={{ width: maxStaffAmount ? `${(Number(amt) / maxStaffAmount) * 100}%` : '0%' }}
                                                />
                                            </div>
                                            <span className={styles.barValue}>UGX {fmt(amt)}</span>
                                        </div>
                                    ))}
                                    {Object.keys(byStaff || {}).length === 0 && (
                                        <div className={styles.emptyCell}>NO EXPENSES IN THIS PERIOD</div>
                                    )}
                                </>
                            )}
                        </div>

                        <div className={styles.sectionLabel}>SPENDING OVER TIME</div>
                        <div className={styles.bucketRow}>
                            {[
                                ['DAY', 'One bar per day'],
                                ['WEEK', 'One bar per week'],
                                ['MONTH', 'One bar per month'],
                            ].map(([b, tip]) => (
                                <Tooltip key={b} label={tip}>
                                    <button
                                        className={bucket === b ? styles.bucketBtnActive : styles.bucketBtn}
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

                        <div className={styles.searchDivider}>SEARCH ALL EXPENSES</div>
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
                                <button className={styles.searchBtn} onClick={runSearch} disabled={searching}>
                                    <FiSearch size={13} aria-hidden="true" /> {searching ? 'SEARCHING...' : 'SEARCH'}
                                </button>
                            </Tooltip>
                            {searchResults && (
                                <Tooltip label="Reset every filter and hide these results">
                                    <button className={styles.clearBtn} onClick={clearSearch}>
                                        <FiX size={13} aria-hidden="true" /> CLEAR
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
                                <div className={styles.tableWrap}>
                                    <table className={styles.table}>
                                        <thead>
                                            <tr>
                                                <th>DATE</th>
                                                <th>CATEGORY</th>
                                                <th>AMOUNT</th>
                                                <th>LOGGED BY</th>
                                                <th>SPENT BY</th>
                                                <th>NOTE</th>
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
                    </HardwarePanel>
                </div>
            )}

            {/* LOG EXPENSE MODAL */}
            <HardwareModal isOpen={logModal.open} onClose={closeLogModal}
                title={logModal.isOther ? 'LOG EXPENSE -- OTHER' : `LOG EXPENSE -- ${logModal.presetName.toUpperCase()}`}>
                {logModal.isOther && (
                    <div className={modalStyles.modalField}>
                        <label className={modalStyles.modalLabel}>WHAT IS THIS EXPENSE FOR?</label>
                        <input
                            type="text"
                            list="expense-categories"
                            className={modalStyles.modalInput}
                            placeholder="e.g. Courier fee"
                            value={logCategory}
                            onChange={e => setLogCategory(e.target.value)}
                        />
                    </div>
                )}
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT (UGX)</label>
                    <input
                        type="number"
                        inputMode="decimal"
                        className={styles.amountInput}
                        placeholder="0"
                        autoFocus
                        value={logAmount}
                        onChange={e => setLogAmount(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Any extra detail..."
                        value={logNote}
                        onChange={e => setLogNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>WHO ACTUALLY SPENT THIS (IF NOT YOU)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Defaults to you"
                        value={logSpentBy}
                        onChange={e => setLogSpentBy(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={closeLogModal}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitLog} loading={logging} icon={FiPlus}>
                        SAVE EXPENSE
                    </HardwareButton>
                </div>
            </HardwareModal>

            {/* NEW PRESET MODAL */}
            <HardwareModal isOpen={presetModal} onClose={() => setPresetModal(false)} title="NEW PRESET">
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>PRESET NAME</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="e.g. Generator Fuel"
                        autoFocus
                        value={newPresetName}
                        onChange={e => setNewPresetName(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={() => setPresetModal(false)}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitPreset} loading={savingPreset} icon={FiPlus}>
                        ADD PRESET
                    </HardwareButton>
                </div>
            </HardwareModal>

            {/* EDIT MODAL */}
            <HardwareModal isOpen={editModal.open} onClose={() => setEditModal({ open: false, expense: null })}
                title="EDIT EXPENSE">
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>CATEGORY</label>
                    <input
                        type="text"
                        list="expense-categories"
                        className={modalStyles.modalInput}
                        value={editCategory}
                        onChange={e => setEditCategory(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT (UGX)</label>
                    <input
                        type="number"
                        inputMode="decimal"
                        className={styles.amountInput}
                        value={editAmount}
                        onChange={e => setEditAmount(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        value={editNote}
                        onChange={e => setEditNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>WHO ACTUALLY SPENT THIS (IF NOT THE LOGGER)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Defaults to whoever logged it"
                        value={editSpentBy}
                        onChange={e => setEditSpentBy(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setEditModal({ open: false, expense: null })}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitEdit} loading={saving} icon={FiEdit2}>
                        SAVE CHANGES
                    </HardwareButton>
                </div>
            </HardwareModal>

            <BackToTopButton />
            <ToastStack toasts={toasts} onDismiss={dismissToast} />
            <ConfirmDialog state={confirmState} onAnswer={handleAnswer} />
        </div>
    );
};

export default ExpensesPage;
