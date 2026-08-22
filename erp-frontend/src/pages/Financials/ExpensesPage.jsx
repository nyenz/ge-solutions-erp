// PATH: erp-frontend/src/pages/Financials/ExpensesPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
    FiTrendingDown, FiPlus, FiRefreshCw, FiEdit2, FiTrash2,
    FiBarChart2, FiX, FiSearch, FiClock, FiChevronDown
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import expenseService from '../../services/expenseService';
import HardwarePanel from '../../components/ui/HardwarePanel';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import styles from './ExpensesPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const EDIT_WINDOW_HOURS = 24;

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

    const [presets, setPresets] = useState([]);
    const [recent, setRecent] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);

    const flash = (text, type = 'info') => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 4000);
    };

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
            flash('Could not load expenses. Check your connection.', 'error');
        } finally {
            setLoading(false);
        }
    }, []);

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
        if (logModal.isOther && !logCategory.trim()) { flash('What is this expense for?', 'error'); return; }
        if (!logAmount || Number(logAmount) <= 0) { flash('Enter an amount.', 'error'); return; }
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
            flash('Expense logged.', 'success');
        } catch (err) {
            flash(err.response?.data?.message || 'Could not log this expense.', 'error');
        } finally {
            setLogging(false);
        }
    };

    // -- NEW PRESET MODAL ------------------------------------------
    const [presetModal, setPresetModal] = useState(false);
    const [newPresetName, setNewPresetName] = useState('');
    const [savingPreset, setSavingPreset] = useState(false);

    const submitPreset = async () => {
        if (!newPresetName.trim()) { flash('Enter a name for this preset.', 'error'); return; }
        setSavingPreset(true);
        try {
            await expenseService.createPreset(newPresetName.trim());
            setPresetModal(false);
            setNewPresetName('');
            await loadAll();
            flash('Preset added.', 'success');
        } catch (err) {
            flash(err.response?.data?.message || 'Could not create this preset.', 'error');
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
        if (!editAmount || Number(editAmount) <= 0) { flash('Enter an amount.', 'error'); return; }
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
            flash('Expense updated.', 'success');
        } catch (err) {
            flash(err.response?.data?.message || 'Could not save this edit.', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (expense) => {
        if (!window.confirm(`Delete this ${expense.category} expense of UGX ${fmt(expense.amount)}? This cannot be undone.`)) return;
        try {
            await expenseService.remove(expense.id);
            await loadAll();
            flash('Entry deleted.', 'warn');
        } catch {
            flash('Could not delete this entry.', 'error');
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

    const loadSummary = useCallback(async (p) => {
        setSummaryLoading(true);
        try {
            const data = await expenseService.getSummary(p);
            setSummary(data || { total: 0, byCategory: {} });
        } catch {
            flash('Could not load the analysis summary.', 'error');
        } finally {
            setSummaryLoading(false);
        }
    }, []);

    const loadByStaff = useCallback(async (p) => {
        setStaffLoading(true);
        try {
            const data = await expenseService.getByStaff(p);
            setByStaff(data || {});
        } catch {
            flash('Could not load the staff breakdown.', 'error');
        } finally {
            setStaffLoading(false);
        }
    }, []);

    const loadSeries = useCallback(async (p, b) => {
        setSeriesLoading(true);
        try {
            const data = await expenseService.getTimeSeries(p, undefined, undefined, b);
            setSeries(data || []);
        } catch {
            flash('Could not load the spending trend.', 'error');
        } finally {
            setSeriesLoading(false);
        }
    }, []);

    useEffect(() => {
        if (isDirector && analysisOpen) {
            loadSummary(period);
            loadByStaff(period);
            loadSeries(period, bucket);
        }
    }, [isDirector, analysisOpen, period, bucket, loadSummary, loadByStaff, loadSeries]);

    const runSearch = async () => {
        setSearching(true);
        try {
            const cleanFilters = Object.fromEntries(
                Object.entries(filters).filter(([, v]) => v !== '' && v !== null)
            );
            const data = await expenseService.search(cleanFilters, 0, 100);
            setSearchResults(data.content || []);
        } catch {
            flash('Search failed.', 'error');
        } finally {
            setSearching(false);
        }
    };

    const clearSearch = () => {
        setFilters({ from: '', to: '', category: '', recordedBy: '', spentBy: '', minAmount: '', maxAmount: '' });
        setSearchResults(null);
    };

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
                    <button className={styles.refreshBtn} onClick={loadAll} aria-label="Refresh">
                        <FiRefreshCw size={13} /> REFRESH
                    </button>
                    {isDirector && (
                        <button
                            className={analysisOpen ? styles.analysisBtnActive : styles.analysisBtn}
                            onClick={() => setAnalysisOpen(o => !o)}
                        >
                            <FiBarChart2 size={14} /> ANALYSIS
                        </button>
                    )}
                </div>
            </header>

            {message && (
                <div className={`${styles.flashBanner} ${styles['flash_' + message.type]}`}>
                    {message.text}
                </div>
            )}

            {/* Shared autocomplete source for every "type it yourself" category field */}
            <datalist id="expense-categories">
                {categories.map(c => <option key={c} value={c} />)}
            </datalist>

            {/* PRESET GRID -- ONE TAP LOGGING */}
            <HardwarePanel title="LOG AN EXPENSE" icon={FiTrendingDown}>
                <div className={styles.presetGrid}>
                    {presets.map(p => (
                        <button key={p.id} className={styles.presetTile} onClick={() => openLogModal(p.name)}>
                            {p.name.toUpperCase()}
                        </button>
                    ))}
                    <button className={styles.presetTileOther} onClick={openOtherModal}>
                        OTHER
                    </button>
                    <button className={styles.presetTileNew} onClick={() => setPresetModal(true)}>
                        <FiPlus size={16} /> NEW PRESET
                    </button>
                </div>
            </HardwarePanel>

            {/* RECENT ENTRIES -- EDITABLE WITHIN 24H */}
            <div className={styles.panelSpacer}>
                <HardwarePanel title="RECENT ENTRIES (LAST 24H)" icon={FiClock}>
                    <div className={styles.tableWrap}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>TIME</th>
                                    <th>CATEGORY</th>
                                    <th>AMOUNT</th>
                                    <th>LOGGED BY</th>
                                    <th>NOTE</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="6" className={styles.emptyCell}>LOADING EXPENSES...</td></tr>
                                ) : recent.length === 0 ? (
                                    <tr><td colSpan="6" className={styles.emptyCell}>NO EXPENSES LOGGED IN THE LAST 24 HOURS</td></tr>
                                ) : recent.map(e => {
                                    const editable = isStillEditable(e.createdAt);
                                    return (
                                        <tr key={e.id}>
                                            <td className={styles.dateCell}>
                                                {new Date(e.createdAt).toLocaleString()}
                                            </td>
                                            <td>
                                                <span className={styles.categoryTag}>{e.category}</span>
                                                {e.editedAt && <span className={styles.editedBadge}>EDITED</span>}
                                            </td>
                                            <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                            <td className={styles.metaCell}>
                                                {e.recordedBy}
                                                {e.spentBy && e.spentBy !== e.recordedBy && (
                                                    <span className={styles.spentByTag}>SPENT: {e.spentBy}</span>
                                                )}
                                            </td>
                                            <td className={styles.notesCell} title={e.note}>{e.note || '---'}</td>
                                            <td>
                                                <div className={styles.rowActions}>
                                                    {editable ? (
                                                        <button className={styles.editIconBtn} onClick={() => openEdit(e)} title={`Editable for ${hoursLeft(e.createdAt)}h more`}>
                                                            <FiEdit2 size={13} />
                                                        </button>
                                                    ) : (
                                                        <span className={styles.lockedTag}>LOCKED</span>
                                                    )}
                                                    {isDirector && (
                                                        <button className={styles.deleteIconBtn} onClick={() => handleDelete(e)} title="Delete entry">
                                                            <FiTrash2 size={13} />
                                                        </button>
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
                            {['TODAY', 'WEEK', 'MONTH', 'YEAR'].map(p => (
                                <button
                                    key={p}
                                    className={period === p ? styles.periodBtnActive : styles.periodBtn}
                                    onClick={() => setPeriod(p)}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>

                        <div className={styles.totalBox}>
                            <label>TOTAL SPENT ({period})</label>
                            <strong>{summaryLoading ? '...' : `UGX ${fmt(summary.total)}`}</strong>
                        </div>

                        <div className={styles.categoryBars}>
                            {Object.entries(summary.byCategory || {}).map(([cat, amt]) => (
                                <div key={cat} className={styles.barRow}>
                                    <span className={styles.barLabel}>{cat}</span>
                                    <div className={styles.barTrack}>
                                        <div
                                            className={styles.barFill}
                                            style={{ width: maxCategoryAmount ? `${(Number(amt) / maxCategoryAmount) * 100}%` : '0%' }}
                                        />
                                    </div>
                                    <span className={styles.barValue}>UGX {fmt(amt)}</span>
                                </div>
                            ))}
                            {!summaryLoading && Object.keys(summary.byCategory || {}).length === 0 && (
                                <div className={styles.emptyCell}>NO EXPENSES IN THIS PERIOD</div>
                            )}
                        </div>

                        <div className={styles.sectionLabel}>BY STAFF (WHO SPENT IT)</div>
                        <div className={styles.categoryBars}>
                            {Object.entries(byStaff || {}).map(([who, amt]) => (
                                <div key={who} className={styles.barRow}>
                                    <span className={styles.barLabel}>{who}</span>
                                    <div className={styles.barTrack}>
                                        <div
                                            className={styles.barFill}
                                            style={{ width: maxStaffAmount ? `${(Number(amt) / maxStaffAmount) * 100}%` : '0%' }}
                                        />
                                    </div>
                                    <span className={styles.barValue}>UGX {fmt(amt)}</span>
                                </div>
                            ))}
                            {!staffLoading && Object.keys(byStaff || {}).length === 0 && (
                                <div className={styles.emptyCell}>NO EXPENSES IN THIS PERIOD</div>
                            )}
                        </div>

                        <div className={styles.sectionLabel}>SPENDING OVER TIME</div>
                        <div className={styles.bucketRow}>
                            {['DAY', 'WEEK', 'MONTH'].map(b => (
                                <button
                                    key={b}
                                    className={bucket === b ? styles.bucketBtnActive : styles.bucketBtn}
                                    onClick={() => setBucket(b)}
                                >
                                    {b}
                                </button>
                            ))}
                        </div>
                        {seriesLoading ? (
                            <div className={styles.emptyCell}>LOADING TREND...</div>
                        ) : series.length === 0 ? (
                            <div className={styles.emptyCell}>NO ACTIVITY IN THIS WINDOW</div>
                        ) : (
                            <div className={styles.tsChart}>
                                {series.map(point => (
                                    <div key={point.bucket} className={styles.tsBarWrap} title={`${point.bucket}: UGX ${fmt(point.total)}`}>
                                        <div className={styles.tsBarTrack}>
                                            <div
                                                className={styles.tsBarFill}
                                                style={{ height: maxSeriesAmount ? `${Math.max(2, (Number(point.total) / maxSeriesAmount) * 100)}%` : '2%' }}
                                            />
                                        </div>
                                        <span className={styles.tsBarLabel}>{point.bucket.slice(-5)}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className={styles.searchDivider}>SEARCH ALL EXPENSES</div>
                        <div className={styles.filterRow}>
                            <input type="date" className={styles.filterInput} value={filters.from}
                                onChange={e => setFilters({ ...filters, from: e.target.value })} title="From date" />
                            <input type="date" className={styles.filterInput} value={filters.to}
                                onChange={e => setFilters({ ...filters, to: e.target.value })} title="To date" />
                            <div className={styles.categoryDropdown} ref={categoryDropdownRef}>
                                <button
                                    type="button"
                                    className={styles.categoryDropdownBtn}
                                    onClick={() => setCategoryDropdownOpen(o => !o)}
                                >
                                    <span>{filters.category || 'ALL CATEGORIES'}</span>
                                    <FiChevronDown className={categoryDropdownOpen ? styles.categoryDropdownIconOpen : ''} />
                                </button>
                                {categoryDropdownOpen && (
                                    <div className={styles.categoryDropdownList}>
                                        <div
                                            className={`${styles.categoryDropdownOption} ${!filters.category ? styles.categoryDropdownOptionActive : ''}`}
                                            onClick={() => { setFilters({ ...filters, category: '' }); setCategoryDropdownOpen(false); }}
                                        >
                                            ALL CATEGORIES
                                        </div>
                                        {presets.map(p => (
                                            <div
                                                key={p.id}
                                                className={`${styles.categoryDropdownOption} ${filters.category === p.name ? styles.categoryDropdownOptionActive : ''}`}
                                                onClick={() => { setFilters({ ...filters, category: p.name }); setCategoryDropdownOpen(false); }}
                                            >
                                                {p.name}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <input type="text" className={styles.filterInput} placeholder="Logged by..."
                                value={filters.recordedBy} onChange={e => setFilters({ ...filters, recordedBy: e.target.value })} />
                            <input type="text" className={styles.filterInput} placeholder="Spent by..."
                                value={filters.spentBy} onChange={e => setFilters({ ...filters, spentBy: e.target.value })} />
                            <input type="number" className={styles.filterInput} placeholder="Min UGX"
                                value={filters.minAmount} onChange={e => setFilters({ ...filters, minAmount: e.target.value })} />
                            <input type="number" className={styles.filterInput} placeholder="Max UGX"
                                value={filters.maxAmount} onChange={e => setFilters({ ...filters, maxAmount: e.target.value })} />
                            <button className={styles.searchBtn} onClick={runSearch} disabled={searching}>
                                <FiSearch size={13} /> {searching ? 'SEARCHING...' : 'SEARCH'}
                            </button>
                            {searchResults && (
                                <button className={styles.clearBtn} onClick={clearSearch}>
                                    <FiX size={13} /> CLEAR
                                </button>
                            )}
                        </div>

                        {searchResults && (
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
                                                <td className={styles.notesCell} title={e.note}>{e.note || '---'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
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
        </div>
    );
};

export default ExpensesPage;
