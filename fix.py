# PATH: fix.py
# PHASE 5 - COMPANY FINANCIALS MODULE (COMPANY COSTS)
# Run from project root: py fix.py
#
# WHAT THIS PHASE DOES (per Section 17.8 of LLM_CONTEXT_GUIDE.md):
# Adds a brand-new, completely separate cost stream for company/office
# expenses (fuel, rent, general field costs) that is NEVER linked to any
# project. Uses the same "total committed vs amount paid" pattern already
# used for client debt, so the Director can see both money owed/committed
# and money actually paid out.
#
# Access: ROLE_ADMIN and ROLE_DIRECTOR only (Manager and Secretary have
# no company-financials access per the Section 17.7 role table).
#
# Per the permanent fix.py rule (Section 3 of the guide), this phase ships
# as ONE complete fix.py covering the full phase: backend model, repository,
# service, controller, plus frontend service, page, route, and nav link --
# all in this single file.
#
# NEW BACKEND FILES:
#   erp-backend/.../modules/finance/model/CompanyExpense.java
#   erp-backend/.../modules/finance/repository/CompanyExpenseRepository.java
#   erp-backend/.../modules/finance/service/CompanyExpenseService.java
#   erp-backend/.../modules/finance/controller/CompanyExpenseController.java
#
# NEW FRONTEND FILES:
#   erp-frontend/src/services/companyExpenseService.js
#   erp-frontend/src/pages/Financials/CompanyExpensesPage.jsx
#   erp-frontend/src/pages/Financials/CompanyExpensesPage.module.css
#
# PATCHED FRONTEND FILES:
#   erp-frontend/src/App.jsx            (new route: /financials)
#   erp-frontend/src/components/layout/Sidebar.jsx  (new nav link)
#
# DB TABLE: company_expenses is auto-created by Hibernate
# (spring.jpa.hibernate.ddl-auto=update) from the new @Entity -- no manual
# migration needed, consistent with how other new entities were added.

import os

def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  -> Saved: {path}")

def patch_file(path, anchor, replacement, label):
    content = read_file(path)
    if content is None:
        print(f"FAIL: {label} ({path} not found)")
        return
    if anchor not in content:
        print(f"MISSING: {label} (anchor not found in {path} -- may already be patched, or file changed)")
        return
    if content.count(anchor) > 1:
        print(f"WARN: {label} (anchor appears more than once -- patching first occurrence only)")
    content = content.replace(anchor, replacement, 1)
    write_file(path, content)
    print(f"OK: {label}")

print("Starting Phase 5 - Company Financials Module...")
print("-" * 60)

# ============================================================
# BACKEND: MODEL
# ============================================================

company_expense_model = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/model/CompanyExpense.java
package com.gesolutions.erp.modules.finance.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - COMPANY EXPENSE (PHASE 5)
 *
 * Represents a single company/office cost entry (fuel, rent, general field
 * costs, etc). Completely separate and unlinked from any LandProject cost --
 * see Section 17.8 of the LLM context guide.
 *
 * Categories are free-form text, not an enum, so staff can add/delete
 * categories as needed. The frontend suggests past categories the same way
 * predictionService suggests district/county on Intake.
 *
 * Uses the same "total committed vs amount paid" pattern already used for
 * client debt (LandProject.totalCost / amountPaid), so the Director can see
 * both money owed/committed and money actually paid out.
 */
@Entity
@Table(name = "company_expenses")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CompanyExpense {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "category", nullable = false, length = 150)
    private String category;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    @Builder.Default
    @Column(name = "total_committed", nullable = false, precision = 15, scale = 2)
    private BigDecimal totalCommitted = BigDecimal.ZERO;

    @Builder.Default
    @Column(name = "amount_paid", nullable = false, precision = 15, scale = 2)
    private BigDecimal amountPaid = BigDecimal.ZERO;

    @Builder.Default
    @Column(name = "is_recurring", nullable = false)
    private boolean isRecurring = false;

    @Column(name = "expense_date")
    private LocalDate expenseDate;

    @Column(name = "recorded_by", length = 100)
    private String recordedBy;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    public BigDecimal getOutstandingBalance() {
        BigDecimal committed = totalCommitted != null ? totalCommitted : BigDecimal.ZERO;
        BigDecimal paid = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return committed.subtract(paid).max(BigDecimal.ZERO);
    }
}
"""

write_file("erp-backend/src/main/java/com/gesolutions/erp/modules/finance/model/CompanyExpense.java", company_expense_model)
print("OK: CompanyExpense model created")

# ============================================================
# BACKEND: REPOSITORY
# ============================================================

company_expense_repo = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/CompanyExpenseRepository.java
package com.gesolutions.erp.modules.finance.repository;

import com.gesolutions.erp.modules.finance.model.CompanyExpense;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Repository
public interface CompanyExpenseRepository extends JpaRepository<CompanyExpense, UUID> {

    Page<CompanyExpense> findAllByOrderByExpenseDateDesc(Pageable pageable);

    @Query("SELECT DISTINCT c.category FROM CompanyExpense c ORDER BY c.category ASC")
    List<String> findDistinctCategories();

    @Query("SELECT COALESCE(SUM(c.totalCommitted), 0) FROM CompanyExpense c")
    BigDecimal sumTotalCommitted();

    @Query("SELECT COALESCE(SUM(c.amountPaid), 0) FROM CompanyExpense c")
    BigDecimal sumTotalPaid();
}
"""

write_file("erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/CompanyExpenseRepository.java", company_expense_repo)
print("OK: CompanyExpenseRepository created")

# ============================================================
# BACKEND: SERVICE
# ============================================================

company_expense_service = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/CompanyExpenseService.java
package com.gesolutions.erp.modules.finance.service;

import com.gesolutions.erp.modules.finance.model.CompanyExpense;
import com.gesolutions.erp.modules.finance.repository.CompanyExpenseRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * GE SOLUTIONS - COMPANY FINANCIALS ENGINE (PHASE 5)
 *
 * Manages company/office cost entries, completely separate from project
 * costs. See Section 17.8 of the LLM context guide for the full business
 * rules this implements.
 */
@Service
@RequiredArgsConstructor
public class CompanyExpenseService {

    private final CompanyExpenseRepository expenseRepository;
    private final AuditService auditService;

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    @Transactional(readOnly = true)
    public Page<CompanyExpense> getAllExpenses(Pageable pageable) {
        return expenseRepository.findAllByOrderByExpenseDateDesc(pageable);
    }

    @Transactional(readOnly = true)
    public List<String> getCategorySuggestions() {
        return expenseRepository.findDistinctCategories();
    }

    @Transactional
    public CompanyExpense createExpense(String category, String notes, BigDecimal totalCommitted,
                                         BigDecimal initialPayment, boolean isRecurring, LocalDate expenseDate) {
        if (category == null || category.isBlank()) {
            throw new BusinessException("CATEGORY_REQUIRED: A company cost category is required.");
        }
        BigDecimal committed = totalCommitted != null ? totalCommitted : BigDecimal.ZERO;
        BigDecimal paid = initialPayment != null ? initialPayment : BigDecimal.ZERO;

        CompanyExpense expense = CompanyExpense.builder()
                .category(category.trim())
                .notes(notes)
                .totalCommitted(committed)
                .amountPaid(paid)
                .isRecurring(isRecurring)
                .expenseDate(expenseDate != null ? expenseDate : LocalDate.now())
                .recordedBy(getCurrentOperator())
                .build();

        CompanyExpense saved = expenseRepository.save(expense);

        auditService.logAction("COMPANY_EXPENSE_ADDED",
            "Operator [" + getCurrentOperator() + "] recorded company cost: " + category
            + " (committed UGX " + committed + ", paid UGX " + paid + ")");

        return saved;
    }

    @Transactional
    public CompanyExpense recordPayment(UUID expenseId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }
        CompanyExpense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> new BusinessException("EXPENSE_NOT_FOUND"));

        expense.setAmountPaid(expense.getAmountPaid().add(amount));
        if (notes != null && !notes.isBlank()) {
            String existing = expense.getNotes() != null ? expense.getNotes() + " | " : "";
            expense.setNotes(existing + notes);
        }
        CompanyExpense saved = expenseRepository.save(expense);

        auditService.logAction("COMPANY_EXPENSE_PAYMENT",
            "Operator [" + getCurrentOperator() + "] paid UGX " + amount + " toward company cost: "
            + expense.getCategory() + " | Outstanding: UGX " + saved.getOutstandingBalance());

        return saved;
    }

    @Transactional
    public void deleteExpense(UUID expenseId) {
        CompanyExpense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> new BusinessException("EXPENSE_NOT_FOUND"));
        expenseRepository.delete(expense);
        auditService.logAction("COMPANY_EXPENSE_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted company cost entry: " + expense.getCategory());
    }

    @Transactional(readOnly = true)
    public Map<String, BigDecimal> getSummary() {
        BigDecimal committed = expenseRepository.sumTotalCommitted();
        BigDecimal paid = expenseRepository.sumTotalPaid();
        BigDecimal outstanding = committed.subtract(paid).max(BigDecimal.ZERO);
        return Map.of(
            "totalCommitted", committed,
            "totalPaid", paid,
            "outstanding", outstanding
        );
    }
}
"""

write_file("erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/CompanyExpenseService.java", company_expense_service)
print("OK: CompanyExpenseService created")

# ============================================================
# BACKEND: CONTROLLER
# ============================================================

company_expense_controller = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/CompanyExpenseController.java
package com.gesolutions.erp.modules.finance.controller;

import com.gesolutions.erp.modules.finance.model.CompanyExpense;
import com.gesolutions.erp.modules.finance.service.CompanyExpenseService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * GE SOLUTIONS - COMPANY FINANCIALS MODULE (PHASE 5)
 *
 * Tracks company/office costs (fuel, rent, general field costs) completely
 * separate from project costs. Per Section 17.7, only Director and Admin
 * (Root carries ROLE_ADMIN) may see or edit company financials -- Manager
 * and Secretary are excluded entirely.
 */
@RestController
@RequestMapping("/api/v1/finance/company-expenses")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class CompanyExpenseController {

    private final CompanyExpenseService expenseService;

    @GetMapping
    public ResponseEntity<Page<CompanyExpense>> getAllExpenses(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(expenseService.getAllExpenses(
            PageRequest.of(page, size, Sort.by("expenseDate").descending())
        ));
    }

    @GetMapping("/categories")
    public ResponseEntity<List<String>> getCategorySuggestions() {
        return ResponseEntity.ok(expenseService.getCategorySuggestions());
    }

    @GetMapping("/summary")
    public ResponseEntity<Map<String, BigDecimal>> getSummary() {
        return ResponseEntity.ok(expenseService.getSummary());
    }

    @PostMapping
    public ResponseEntity<CompanyExpense> createExpense(@RequestBody Map<String, Object> body) {
        String category = (String) body.get("category");
        String notes = (String) body.get("notes");
        BigDecimal totalCommitted = body.get("totalCommitted") != null
                ? new BigDecimal(body.get("totalCommitted").toString()) : BigDecimal.ZERO;
        BigDecimal initialPayment = body.get("initialPayment") != null
                ? new BigDecimal(body.get("initialPayment").toString()) : BigDecimal.ZERO;
        boolean isRecurring = body.get("isRecurring") != null && Boolean.parseBoolean(body.get("isRecurring").toString());
        LocalDate expenseDate = (body.get("expenseDate") != null && !body.get("expenseDate").toString().isBlank())
                ? LocalDate.parse(body.get("expenseDate").toString()) : LocalDate.now();

        return ResponseEntity.ok(expenseService.createExpense(
            category, notes, totalCommitted, initialPayment, isRecurring, expenseDate
        ));
    }

    @PostMapping("/{id}/payment")
    public ResponseEntity<CompanyExpense> recordPayment(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        BigDecimal amount = body.get("amount") != null ? new BigDecimal(body.get("amount").toString()) : null;
        String notes = (String) body.get("notes");
        return ResponseEntity.ok(expenseService.recordPayment(id, amount, notes));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteExpense(@PathVariable UUID id) {
        expenseService.deleteExpense(id);
        return ResponseEntity.noContent().build();
    }
}
"""

write_file("erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/CompanyExpenseController.java", company_expense_controller)
print("OK: CompanyExpenseController created")

# ============================================================
# FRONTEND: SERVICE
# ============================================================

company_expense_frontend_service = """// PATH: erp-frontend/src/services/companyExpenseService.js
import api from '../api/axios';

/**
 * GE SOLUTIONS - COMPANY FINANCIALS SERVICE (PHASE 5)
 * Talks to /finance/company-expenses. Restricted server-side to
 * ROLE_ADMIN and ROLE_DIRECTOR.
 */
const companyExpenseService = {
    getAll: async (page = 0, size = 50) => {
        const response = await api.get('/finance/company-expenses', { params: { page, size } });
        return response.data;
    },

    getCategories: async () => {
        const response = await api.get('/finance/company-expenses/categories');
        return response.data;
    },

    getSummary: async () => {
        const response = await api.get('/finance/company-expenses/summary');
        return response.data;
    },

    create: async (data) => {
        const response = await api.post('/finance/company-expenses', data);
        return response.data;
    },

    recordPayment: async (id, amount, notes) => {
        const response = await api.post(`/finance/company-expenses/${id}/payment`, { amount, notes });
        return response.data;
    },

    remove: async (id) => {
        await api.delete(`/finance/company-expenses/${id}`);
    },
};

export default companyExpenseService;
"""

write_file("erp-frontend/src/services/companyExpenseService.js", company_expense_frontend_service)
print("OK: companyExpenseService.js created")

# ============================================================
# FRONTEND: PAGE (JSX)
# ============================================================

company_expenses_page_jsx = """// PATH: erp-frontend/src/pages/Financials/CompanyExpensesPage.jsx
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
"""

write_file("erp-frontend/src/pages/Financials/CompanyExpensesPage.jsx", company_expenses_page_jsx)
print("OK: CompanyExpensesPage.jsx created")

# ============================================================
# FRONTEND: PAGE CSS
# ============================================================

company_expenses_page_css = """/* PATH: erp-frontend/src/pages/Financials/CompanyExpensesPage.module.css */
.container {
    --orange:        #EE8C3A;
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --red:           #ef4444;
    --green:         #10b981;

    --radius:    10px;
    --radius-sm: 6px;

    --fs-h1:    clamp(18px, 2.5vw, 24px);
    --fs-sub:   clamp(8px,  0.85vw, 10px);

    max-width: 1400px;
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(24px, 3vw, 36px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 24px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; margin: 0; letter-spacing: 1.5px; text-transform: uppercase; line-height: 1; }
.subtitle { color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

.headerActions { display: flex; gap: 8px; flex-shrink: 0; flex-wrap: wrap; }
.refreshBtn, .addBtn {
    display: flex; align-items: center; gap: 6px;
    height: clamp(34px, 4vw, 40px);
    padding: 0 clamp(12px, 1.5vw, 16px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.2s;
}
.refreshBtn { background: rgba(26,46,48,0.08); border: 1.5px solid rgba(26,46,48,0.2); color: #1a2e30; }
.refreshBtn:hover { background: #EE8C3A; color: #fff; border-color: #EE8C3A; }
.addBtn { background: #EE8C3A; border: none; color: #1a2e30; box-shadow: 0 3px 10px rgba(238,140,58,0.3); }
.addBtn:hover { background: #f0a050; box-shadow: 0 0 18px rgba(238,140,58,0.4); }

.flashBanner {
    padding: 10px 16px;
    border-radius: var(--radius-sm);
    font-weight: 800;
    font-size: 12px;
    margin-bottom: 14px;
}
.flash_success { background: rgba(16,185,129,0.15); border: 1px solid #10b981; color: #6ee7b7; }
.flash_error   { background: rgba(239,68,68,0.15);  border: 1px solid #ef4444; color: #fca5a5; }
.flash_warn    { background: rgba(245,158,11,0.15); border: 1px solid #f59e0b; color: #fcd34d; }
.flash_info    { background: rgba(6,182,212,0.15);  border: 1px solid #06b6d4; color: #67e8f9; }

.summaryRow {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 20px);
}
.sumCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    border-radius: var(--radius);
    padding: clamp(12px, 1.5vw, 18px);
    display: flex; flex-direction: column; gap: 4px;
}
.sumCard label { font-size: 9px; font-weight: 900; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 1px; }
.sumCard strong { font-family: 'Space Mono', monospace; font-size: clamp(14px,1.6vw,18px); color: #fff; font-weight: 700; word-break: break-all; }

.searchWrap {
    position: relative;
    display: flex; align-items: center;
    background: #fff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    height: clamp(36px, 4.5vw, 44px);
    max-width: clamp(300px, 50vw, 560px);
    margin-bottom: clamp(14px, 2vw, 20px);
}
.searchIcon { position: absolute; left: 12px; color: #EE8C3A; font-size: 16px; pointer-events: none; }
.searchInput { width: 100%; border: none; outline: none; background: transparent; color: #1a2e30; padding: 0 36px 0 42px !important; font-weight: 800; font-size: 12px; height: 100%; }
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.clearBtn { position: absolute; right: 8px; background: transparent; border: none; cursor: pointer; color: rgba(26,46,48,0.4); display: flex; align-items: center; padding: 4px; }
.clearBtn:hover { color: #1a2e30; }

.tableScroll { overflow-x: auto; border-radius: var(--radius); background: rgba(0,0,0,0.15); margin: -30px; }
.expenseTable { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 800px; }
.expenseTable th {
    background: #162a2c; padding: 14px 16px; text-align: left;
    font-family: 'DM Sans', sans-serif; font-size: 9px; font-weight: 900;
    color: var(--orange); text-transform: uppercase; letter-spacing: 1.5px;
    border-bottom: 3px solid var(--orange); white-space: nowrap;
}
.expenseTable td { padding: 11px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle; color: #fff; font-size: 11px; }
.dateCell { font-weight: 700; white-space: nowrap; }
.categoryTag { font-family: 'DM Sans', sans-serif; font-weight: 900; text-transform: uppercase; letter-spacing: 0.5px; }
.recurIcon { margin-left: 6px; color: var(--orange); vertical-align: middle; }
.moneyCell { font-family: 'Space Mono', monospace; font-weight: 700; }
.moneyCellGreen { font-family: 'Space Mono', monospace; font-weight: 700; color: #22c55e; }
.moneyCellRed { font-family: 'Space Mono', monospace; font-weight: 900; color: #fca5a5; }
.metaCell { color: rgba(255,255,255,0.6); font-size: 10px; }
.notesCell { color: rgba(255,255,255,0.45); font-style: italic; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.emptyCell { text-align: center; padding: 50px 20px; font-family: 'Space Mono', monospace; color: rgba(255,255,255,0.25); font-weight: 900; letter-spacing: 1px; text-transform: uppercase; font-size: 11px; }

.rowActions { display: flex; gap: 6px; }
.payIconBtn, .deleteIconBtn {
    width: 28px; height: 28px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; border: 1.5px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: #fff;
    transition: all 0.2s;
}
.payIconBtn:hover { background: #10b981; border-color: #10b981; color: #1a2e30; }
.deleteIconBtn:hover { background: #ef4444; border-color: #ef4444; color: #fff; }

.checkboxRow { display: flex; align-items: center; gap: 8px; font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.85); cursor: pointer; }
.checkboxRow input { width: 16px; height: 16px; cursor: pointer; }

@media (max-width: 768px) {
    .summaryRow { grid-template-columns: 1fr; }
    .tableScroll { margin: 0; border-radius: 0; }
    .pageHeader { border-radius: 0; }
}
"""

write_file("erp-frontend/src/pages/Financials/CompanyExpensesPage.module.css", company_expenses_page_css)
print("OK: CompanyExpensesPage.module.css created")

# ============================================================
# FRONTEND: PATCH App.jsx (add route)
# ============================================================

app_jsx_path = "erp-frontend/src/App.jsx"

import_anchor = """import PaymentsPage   from './pages/Payments/PaymentsPage';
import ReportHub      from './pages/Reports/ReportHub';"""

import_replacement = """import PaymentsPage   from './pages/Payments/PaymentsPage';
import CompanyExpensesPage from './pages/Financials/CompanyExpensesPage';
import ReportHub      from './pages/Reports/ReportHub';"""

patch_file(app_jsx_path, import_anchor, import_replacement, "App.jsx - import CompanyExpensesPage")

route_anchor = """            { path: "payments", element: <ProtectedRoute adminOnly><Shell><PaymentsPage /></Shell></ProtectedRoute> },
            { path: "reports", element: <ProtectedRoute adminOnly><Shell><ReportHub /></Shell></ProtectedRoute> },"""

route_replacement = """            { path: "payments", element: <ProtectedRoute adminOnly><Shell><PaymentsPage /></Shell></ProtectedRoute> },
            { path: "financials", element: <ProtectedRoute adminOnly><Shell><CompanyExpensesPage /></Shell></ProtectedRoute> },
            { path: "reports", element: <ProtectedRoute adminOnly><Shell><ReportHub /></Shell></ProtectedRoute> },"""

patch_file(app_jsx_path, route_anchor, route_replacement, "App.jsx - /financials route")

# ============================================================
# FRONTEND: PATCH Sidebar.jsx (add nav link)
# ============================================================

sidebar_path = "erp-frontend/src/components/layout/Sidebar.jsx"

sidebar_import_anchor = """import {
    FiGrid, FiPlusSquare, FiLayers, FiPhoneCall,
    FiSettings, FiBarChart2, FiShield, FiDollarSign
} from 'react-icons/fi';"""

sidebar_import_replacement = """import {
    FiGrid, FiPlusSquare, FiLayers, FiPhoneCall,
    FiSettings, FiBarChart2, FiShield, FiDollarSign, FiTrendingDown
} from 'react-icons/fi';"""

patch_file(sidebar_path, sidebar_import_anchor, sidebar_import_replacement, "Sidebar.jsx - import FiTrendingDown")

sidebar_nav_anchor = """        { path: '/payments',      label: 'PAYMENTS',  icon: <FiDollarSign aria-hidden="true" />, access: hasHighLevelAccess },
        { path: '/reports',       label: 'REPORTS',   icon: <FiBarChart2  aria-hidden="true" />, access: hasHighLevelAccess },"""

sidebar_nav_replacement = """        { path: '/payments',      label: 'PAYMENTS',  icon: <FiDollarSign aria-hidden="true" />, access: hasHighLevelAccess },
        { path: '/financials',    label: 'COMPANY COSTS', icon: <FiTrendingDown aria-hidden="true" />, access: hasHighLevelAccess },
        { path: '/reports',       label: 'REPORTS',   icon: <FiBarChart2  aria-hidden="true" />, access: hasHighLevelAccess },"""

patch_file(sidebar_path, sidebar_nav_anchor, sidebar_nav_replacement, "Sidebar.jsx - Company Costs nav link")

print("-" * 60)
print("DONE. Check for FAIL / MISSING messages above.")
print("")
print("If all OK, run:")
print("git add -A && git commit -m 'feat: Phase 5 - Company Financials Module' && git push")
print("")
print("NOTE: No manual DB migration needed -- company_expenses table is")
print("auto-created by Hibernate (ddl-auto=update) from the new @Entity,")
print("same as every other new table added since the revamp started.")
print("")
print("TEST PLAN (per the permanent deferred-testing rule, run together")
print("with Phases 1-7 once Phase 7 is code-complete, not before):")
print("  1. Log in as Admin or Director -> sidebar should show COMPANY COSTS")
print("     between PAYMENTS and REPORTS. Manager should NOT see it.")
print("  2. Click COMPANY COSTS -> ADD COST -> enter a category (try typing")
print("     a letter to confirm the autocomplete dropdown appears once a")
print("     second entry with a repeated category exists), committed and")
print("     paid amounts, save.")
print("  3. Confirm the three summary cards (COMMITTED / PAID / OUTSTANDING)")
print("     update correctly.")
print("  4. Click the $ icon on a row with an outstanding balance -> record")
print("     a partial payment -> confirm OUTSTANDING drops correctly.")
print("  5. Confirm a Manager-role login gets redirected away from /financials.")