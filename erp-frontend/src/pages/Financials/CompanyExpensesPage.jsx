// PATH: erp-frontend/src/pages/Financials/CompanyExpensesPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    FiTrendingDown, FiPlus, FiDollarSign, FiX,
    FiRefreshCw, FiSearch, FiRepeat, FiTrash2
} from 'react-icons/fi';
import companyExpenseService from '../../services/companyExpenseService';
import HardwarePanel from '../../components/ui/HardwarePanel';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import styles from './CompanyExpensesPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const CompanyExpensesPage = () => {
    const [expenses,   setExpenses]   = useState([]);
    const [categories, setCategories] = useState([]);
    const [summary,    setSummary]    = useState({ totalCommitted: 0, totalPaid: 0, outstanding: 0 });
    const [loading,    setLoading]    = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [message,    setMessage]    = useState(null);

    const [addModal, setAddModal] = useState(false);
    const [addForm,  setAddForm]  = useState({
        category: '', notes: '', totalCommitted: '', initialPayment: '',
        isRecurring: false, expenseDate: new Date().toISOString().substring(0, 10),
    });
    const [saving, setSaving] = useState(false);

    const [payModal, setPayModal] = useState({ open: false, expense: null });
    const [payAmount, setPayAmount] = useState('');
    const [payNotes,  setPayNotes]  = useState('');
    const [paying,    setPaying]    = useState(false);

    const flash = (text, type = 'info') => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 4000);
    };

    const loadAll = useCallback(async () => {
        setLoading(true);
        try {
            const [expData, catData, sumData] = await Promise.all([
                companyExpenseService.getAll(0, 200),
                companyExpenseService.getCategories(),
                companyExpenseService.getSummary(),
            ]);
            setExpenses(expData.content || []);
            setCategories(catData || []);
            setSummary(sumData || { totalCommitted: 0, totalPaid: 0, outstanding: 0 });
        } catch {
            flash('Could not load company costs. Check your connection.', 'error');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadAll(); }, [loadAll]);

    const filtered = useMemo(() => {
        if (!searchTerm.trim()) return expenses;
        const t = searchTerm.toLowerCase();
        return expenses.filter(e =>
            e.category?.toLowerCase().includes(t) ||
            e.notes?.toLowerCase().includes(t) ||
            e.recordedBy?.toLowerCase().includes(t)
        );
    }, [expenses, searchTerm]);

    const handleCreate = async () => {
        if (!addForm.category.trim()) { flash('Enter a category for this cost.', 'error'); return; }
        setSaving(true);
        try {
            await companyExpenseService.create({
                category: addForm.category.trim(),
                notes: addForm.notes,
                totalCommitted: Number(addForm.totalCommitted) || 0,
                initialPayment: Number(addForm.initialPayment) || 0,
                isRecurring: addForm.isRecurring,
                expenseDate: addForm.expenseDate,
            });
            setAddModal(false);
            setAddForm({ category: '', notes: '', totalCommitted: '', initialPayment: '', isRecurring: false, expenseDate: new Date().toISOString().substring(0, 10) });
            await loadAll();
            flash('Company cost recorded.', 'success');
        } catch (err) {
            flash(err.response?.data?.message || 'Could not save this cost entry.', 'error');
        } finally {
            setSaving(false);
        }
    };

    const openPayModal = (expense) => {
        setPayModal({ open: true, expense });
        setPayAmount('');
        setPayNotes('');
    };

    const handlePay = async () => {
        if (!payAmount || Number(payAmount) <= 0) { flash('Enter a valid amount.', 'error'); return; }
        setPaying(true);
        try {
            await companyExpenseService.recordPayment(payModal.expense.id, Number(payAmount), payNotes);
            setPayModal({ open: false, expense: null });
            await loadAll();
            flash('Payment recorded.', 'success');
        } catch (err) {
            flash(err.response?.data?.message || 'Payment failed.', 'error');
        } finally {
            setPaying(false);
        }
    };

    const handleDelete = async (expense) => {
        if (!window.confirm(`Delete company cost "${expense.category}"? This cannot be undone.`)) return;
        try {
            await companyExpenseService.remove(expense.id);
            await loadAll();
            flash('Entry deleted.', 'warn');
        } catch {
            flash('Could not delete this entry.', 'error');
        }
    };

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Company Costs</h1>
                    <p className={styles.subtitle}>Office and company expenses -- separate from project costs</p>
                </div>
                <div className={styles.headerActions}>
                    <button className={styles.refreshBtn} onClick={loadAll} aria-label="Refresh">
                        <FiRefreshCw size={13} /> REFRESH
                    </button>
                    <button className={styles.addBtn} onClick={() => setAddModal(true)}>
                        <FiPlus size={14} /> ADD COST
                    </button>
                </div>
            </header>

            {message && (
                <div className={`${styles.flashBanner} ${styles['flash_' + message.type]}`}>
                    {message.text}
                </div>
            )}

            <div className={styles.summaryRow}>
                <div className={styles.sumCard}>
                    <label>TOTAL COMMITTED</label>
                    <strong>UGX {fmt(summary.totalCommitted)}</strong>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#22c55e' }}>
                    <label style={{ color: '#22c55e' }}>TOTAL PAID</label>
                    <strong style={{ color: '#22c55e' }}>UGX {fmt(summary.totalPaid)}</strong>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#ef4444' }}>
                    <label style={{ color: '#ef4444' }}>OUTSTANDING</label>
                    <strong style={{ color: '#ef4444' }}>UGX {fmt(summary.outstanding)}</strong>
                </div>
            </div>

            <div className={styles.searchWrap}>
                <FiSearch className={styles.searchIcon} />
                <input
                    type="search"
                    className={styles.searchInput}
                    placeholder="Search category, notes, recorded by..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                />
                {searchTerm && (
                    <button className={styles.clearBtn} onClick={() => setSearchTerm('')}>
                        <FiX size={13} />
                    </button>
                )}
            </div>

            <div>
                <HardwarePanel variant="dark">
                    <div className={styles.tableScroll}>
                        <table className={styles.expenseTable}>
                            <thead>
                                <tr>
                                    <th>DATE</th>
                                    <th>CATEGORY</th>
                                    <th>COMMITTED</th>
                                    <th>PAID</th>
                                    <th>OUTSTANDING</th>
                                    <th>RECORDED BY</th>
                                    <th>NOTES</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="8" className={styles.emptyCell}>LOADING COMPANY COSTS...</td></tr>
                                ) : filtered.length === 0 ? (
                                    <tr><td colSpan="8" className={styles.emptyCell}>
                                        {searchTerm ? `NO ENTRIES MATCH "${searchTerm.toUpperCase()}"` : 'NO COMPANY COSTS RECORDED YET'}
                                    </td></tr>
                                ) : filtered.map(e => {
                                    const outstanding = Math.max(0, Number(e.totalCommitted || 0) - Number(e.amountPaid || 0));
                                    return (
                                        <tr key={e.id}>
                                            <td className={styles.dateCell}>
                                                {e.expenseDate ? new Date(e.expenseDate).toLocaleDateString() : '---'}
                                            </td>
                                            <td>
                                                <span className={styles.categoryTag}>{e.category}</span>
                                                {e.isRecurring && <FiRepeat className={styles.recurIcon} title="Recurring" />}
                                            </td>
                                            <td className={styles.moneyCell}>UGX {fmt(e.totalCommitted)}</td>
                                            <td className={styles.moneyCellGreen}>UGX {fmt(e.amountPaid)}</td>
                                            <td className={outstanding > 0 ? styles.moneyCellRed : styles.moneyCell}>
                                                UGX {fmt(outstanding)}
                                            </td>
                                            <td className={styles.metaCell}>{e.recordedBy}</td>
                                            <td className={styles.notesCell} title={e.notes}>{e.notes || '---'}</td>
                                            <td>
                                                <div className={styles.rowActions}>
                                                    {outstanding > 0 && (
                                                        <button className={styles.payIconBtn} onClick={() => openPayModal(e)} title="Record payment">
                                                            <FiDollarSign size={13} />
                                                        </button>
                                                    )}
                                                    <button className={styles.deleteIconBtn} onClick={() => handleDelete(e)} title="Delete entry">
                                                        <FiTrash2 size={13} />
                                                    </button>
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

            {/* ADD COST MODAL */}
            <HardwareModal isOpen={addModal} onClose={() => setAddModal(false)} title="ADD COMPANY COST">
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>CATEGORY</label>
                    <input
                        list="expense-categories"
                        className={modalStyles.modalInput}
                        placeholder="e.g. Fuel, Office Rent, Internet"
                        value={addForm.category}
                        onChange={e => setAddForm({ ...addForm, category: e.target.value })}
                    />
                    <datalist id="expense-categories">
                        {categories.map(c => <option key={c} value={c} />)}
                    </datalist>
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>TOTAL COMMITTED (UGX)</label>
                    <input
                        type="number"
                        className={modalStyles.modalInput}
                        placeholder="e.g. 500000"
                        value={addForm.totalCommitted}
                        onChange={e => setAddForm({ ...addForm, totalCommitted: e.target.value })}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>PAID SO FAR (UGX)</label>
                    <input
                        type="number"
                        className={modalStyles.modalInput}
                        placeholder="e.g. 500000 (leave 0 if not yet paid)"
                        value={addForm.initialPayment}
                        onChange={e => setAddForm({ ...addForm, initialPayment: e.target.value })}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>DATE</label>
                    <input
                        type="date"
                        className={modalStyles.modalInput}
                        value={addForm.expenseDate}
                        onChange={e => setAddForm({ ...addForm, expenseDate: e.target.value })}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={styles.checkboxRow}>
                        <input
                            type="checkbox"
                            checked={addForm.isRecurring}
                            onChange={e => setAddForm({ ...addForm, isRecurring: e.target.checked })}
                        />
                        <span>This is a recurring cost (e.g. monthly rent)</span>
                    </label>
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea
                        className={modalStyles.modalTextarea}
                        placeholder="Any extra detail..."
                        value={addForm.notes}
                        onChange={e => setAddForm({ ...addForm, notes: e.target.value })}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={() => setAddModal(false)}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={handleCreate} loading={saving} icon={FiPlus}>
                        SAVE COST
                    </HardwareButton>
                </div>
            </HardwareModal>

            {/* PAY MODAL */}
            <HardwareModal isOpen={payModal.open} onClose={() => setPayModal({ open: false, expense: null })}
                title={payModal.expense ? `RECORD PAYMENT -- ${payModal.expense.category}` : 'RECORD PAYMENT'}>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT PAID (UGX)</label>
                    <input
                        type="number"
                        className={modalStyles.modalInput}
                        placeholder="e.g. 100000"
                        value={payAmount}
                        onChange={e => setPayAmount(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea
                        className={modalStyles.modalTextarea}
                        placeholder="e.g. Paid via bank transfer..."
                        value={payNotes}
                        onChange={e => setPayNotes(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setPayModal({ open: false, expense: null })}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={handlePay} loading={paying} icon={FiDollarSign}>
                        CONFIRM PAYMENT
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default CompanyExpensesPage;
