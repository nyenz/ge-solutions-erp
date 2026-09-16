// PATH: erp-frontend/src/pages/Financials/ExpensesPage.jsx
// EXPENSES v3 -- see ExpensesPage.module.css for the design note. Structurally
// this page is now the Client Dossier: frosted header, stat strip, then
// CollapsibleSection panels carrying CornerDecor and a corner badge. The
// Director analysis block that used to hang off the ANALYSIS toggle here now
// lives on the Report Hub (Reports/ExpenseAnalysis.jsx) -- this page is purely
// "log cash going out, and fix it within 24h".
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    FiTrendingDown, FiPlus, FiRefreshCw, FiEdit2, FiTrash2,
    FiClock, FiLock, FiInfo
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import expenseService from '../../services/expenseService';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import { LoadingRow } from '../../components/common/LoadingState';
import { Tooltip, IconButton, Term } from '../../components/common/Tooltip';
import { GLOSSARY } from '../../components/common/glossary';
import { useToasts, useConfirm } from '../../components/common/useFeedback';
import { ToastStack, ConfirmDialog } from '../../components/common/Feedback';
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

    // Every category ever used -- preset tiles plus anything typed under OTHER.
    // Feeds the shared datalist behind both "type it yourself" fields.
    const knownCategories = useMemo(() => {
        const names = new Set();
        presets.forEach(p => p.name && names.add(p.name));
        categories.forEach(c => c && names.add(c));
        return [...names].sort((a, b) => a.localeCompare(b));
    }, [presets, categories]);

    // The stat strip reads straight off the 24h window already in memory --
    // no extra call, and it agrees with the table underneath it by construction.
    const dayTotal = useMemo(
        () => recent.reduce((sum, e) => sum + Number(e.amount || 0), 0),
        [recent],
    );
    const editableCount = useMemo(
        () => recent.filter(e => isStillEditable(e.createdAt)).length,
        [recent],
    );

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

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Expenses</h1>
                    <p className={styles.subtitle}>Log any cash that leaves the office</p>
                </div>
                <div className={styles.headerActions}>
                    <Tooltip label="Reload the presets and the last 24 hours of entries">
                        <button className={styles.ghostBtn} onClick={loadAll} aria-label="Refresh expenses">
                            <FiRefreshCw size={12} aria-hidden="true" /> REFRESH
                        </button>
                    </Tooltip>
                    <Tooltip label="Add a new tile for a cost you log often">
                        <button className={styles.primaryBtn} onClick={() => setPresetModal(true)}>
                            <FiPlus size={12} aria-hidden="true" /> NEW PRESET
                        </button>
                    </Tooltip>
                </div>
            </header>

            {/* Shared autocomplete source for every "type it yourself" category field */}
            <datalist id="expense-categories">
                {knownCategories.map(c => <option key={c} value={c} />)}
            </datalist>

            {/* STAT STRIP -- same card spec as the dossier and Payment Records */}
            <div className={styles.moneyStrip}>
                <div className={`${styles.statCard} ${styles.statAmber}`}>
                    <label>SPENT (LAST 24H)</label>
                    <strong>UGX {fmt(dayTotal)}</strong>
                    <span className={styles.statNote}>{recent.length} {recent.length === 1 ? 'entry' : 'entries'}</span>
                </div>
                <div className={`${styles.statCard} ${styles.statGreen}`}>
                    <label>STILL EDITABLE</label>
                    <strong>{editableCount}</strong>
                    <span className={styles.statNote}>of {recent.length} in window</span>
                </div>
                <div className={styles.statCard}>
                    <label>PRESETS</label>
                    <strong>{presets.length}</strong>
                    <span className={styles.statNote}>one-tap categories</span>
                </div>
                <div className={styles.statCard}>
                    <label>CATEGORIES USED</label>
                    <strong>{knownCategories.length}</strong>
                    <span className={styles.statNote}>all time</span>
                </div>
            </div>

            {/* LOG AN EXPENSE -- ONE TAP */}
            <CollapsibleSection
                icon={<FiTrendingDown aria-hidden="true" />}
                title="LOG AN EXPENSE"
                right={<span className={styles.panelCornerBadge}>{presets.length} {presets.length === 1 ? 'PRESET' : 'PRESETS'}</span>}
            >
                <p className={styles.panelHint}>
                    <FiInfo size={12} aria-hidden="true" />
                    Tap a category to log it. Anything without a tile goes under OTHER.
                </p>
                <div className={styles.presetRow}>
                    {presets.map(p => (
                        <Tooltip key={p.id} label={`Log a ${p.name} expense`}>
                            <button className={styles.presetBtn} onClick={() => openLogModal(p.name)}>
                                {p.name.toUpperCase()}
                            </button>
                        </Tooltip>
                    ))}
                    <Tooltip label="Anything with no tile -- you type what it was for">
                        <button className={styles.presetBtnOther} onClick={openOtherModal}>
                            OTHER
                        </button>
                    </Tooltip>
                    <Tooltip label="Add a new tile for a cost you log often">
                        <button className={styles.presetBtnNew} onClick={() => setPresetModal(true)}>
                            <FiPlus size={12} aria-hidden="true" /> NEW PRESET
                        </button>
                    </Tooltip>
                </div>
            </CollapsibleSection>

            {/* RECENT ENTRIES -- EDITABLE WITHIN 24H */}
            <CollapsibleSection
                icon={<FiClock aria-hidden="true" />}
                title="RECENT ENTRIES (LAST 24H)"
                right={<span className={styles.panelCornerBadge}>{recent.length} {recent.length === 1 ? 'ENTRY' : 'ENTRIES'}</span>}
            >
                <p className={styles.panelHint}>
                    <FiInfo size={12} aria-hidden="true" />
                    You can edit your own entries for {EDIT_WINDOW_HOURS} hours. After that they lock.
                </p>
                <div className={styles.tableScroll}>
                    <table className={styles.ledgerTable}>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Category</th>
                                <th>Amount (UGX)</th>
                                <th>Logged By</th>
                                <th>Note</th>
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
                                    <tr key={e.id} className={`${styles.row} ${deletingId === e.id ? styles.rowBusy : ''}`}>
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
            </CollapsibleSection>

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
