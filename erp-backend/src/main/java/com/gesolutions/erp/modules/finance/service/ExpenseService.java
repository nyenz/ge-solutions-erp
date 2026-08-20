// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/ExpenseService.java
package com.gesolutions.erp.modules.finance.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.finance.model.Expense;
import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.finance.repository.ExpenseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * GE SOLUTIONS - EXPENSES ENGINE (EXPENSES REBUILD)
 *
 * Every expense is a flat, permanent cash-out record. No committed/paid
 * split, no debt tracking -- if it hasn't left the office yet, it doesn't
 * get logged yet. Editable for 24 hours after creation by any Manager+
 * user to fix mistakes; every create/edit/delete is written to the audit
 * log. Presets can be created instantly by any Manager+ user.
 */
@Service
@RequiredArgsConstructor
public class ExpenseService {

    private static final int EDIT_WINDOW_HOURS = 24;

    private final ExpenseRepository expenseRepository;
    private final ExpensePresetRepository presetRepository;
    private final AuditService auditService;

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    // -- PRESETS ------------------------------------------------------

    @Transactional(readOnly = true)
    public List<ExpensePreset> getPresets() {
        return presetRepository.findAllByOrderByNameAsc();
    }

    @Transactional
    public ExpensePreset createPreset(String name) {
        if (name == null || name.isBlank()) {
            throw new BusinessException("PRESET_NAME_REQUIRED: Enter a name for this preset.");
        }
        String trimmed = name.trim();
        if (presetRepository.existsByNameIgnoreCase(trimmed)) {
            throw new BusinessException("PRESET_EXISTS: A preset with this name already exists.");
        }
        ExpensePreset preset = ExpensePreset.builder()
                .name(trimmed)
                .createdBy(getCurrentOperator())
                .build();
        ExpensePreset saved = presetRepository.save(preset);

        auditService.logAction("EXPENSE_PRESET_CREATED",
            "Operator [" + getCurrentOperator() + "] created expense preset: " + trimmed);

        return saved;
    }

    // -- LOGGING ------------------------------------------------------

    @Transactional
    public Expense createExpense(String category, BigDecimal amount, String note) {
        if (category == null || category.isBlank()) {
            throw new BusinessException("CATEGORY_REQUIRED: Pick a category for this expense.");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("AMOUNT_REQUIRED: Enter an amount greater than zero.");
        }

        Expense expense = Expense.builder()
                .category(category.trim())
                .amount(amount)
                .note(note)
                .recordedBy(getCurrentOperator())
                .build();

        Expense saved = expenseRepository.save(expense);

        auditService.logAction("EXPENSE_LOGGED",
            "Operator [" + getCurrentOperator() + "] logged expense: " + category
            + " -- UGX " + amount);

        return saved;
    }

    @Transactional(readOnly = true)
    public List<Expense> getRecent(int hours) {
        LocalDateTime since = LocalDateTime.now().minusHours(hours);
        return expenseRepository.findByCreatedAtAfterOrderByCreatedAtDesc(since);
    }

    // -- EDITING (24-HOUR WINDOW, ANY MANAGER+) ----------------------

    @Transactional
    public Expense editExpense(UUID id, String category, BigDecimal amount, String note) {
        Expense expense = expenseRepository.findById(id)
                .orElseThrow(() -> new BusinessException("EXPENSE_NOT_FOUND"));

        if (!expense.isEditable()) {
            throw new BusinessException("EDIT_WINDOW_CLOSED: This expense is more than "
                + EDIT_WINDOW_HOURS + " hours old and can no longer be edited. Ask a Director to delete it if it's wrong.");
        }
        if (category == null || category.isBlank()) {
            throw new BusinessException("CATEGORY_REQUIRED: Pick a category for this expense.");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("AMOUNT_REQUIRED: Enter an amount greater than zero.");
        }

        String oldCategory = expense.getCategory();
        BigDecimal oldAmount = expense.getAmount();

        expense.setCategory(category.trim());
        expense.setAmount(amount);
        expense.setNote(note);
        expense.setEditedAt(LocalDateTime.now());
        expense.setEditedBy(getCurrentOperator());

        Expense saved = expenseRepository.save(expense);

        auditService.logAction("EXPENSE_EDITED",
            "Operator [" + getCurrentOperator() + "] edited expense (originally logged by "
            + saved.getRecordedBy() + "): " + oldCategory + " UGX " + oldAmount
            + " -> " + category + " UGX " + amount);

        return saved;
    }

    // -- DELETE (DIRECTOR/ADMIN ONLY, ENFORCED AT CONTROLLER LEVEL) --

    @Transactional
    public void deleteExpense(UUID id) {
        Expense expense = expenseRepository.findById(id)
                .orElseThrow(() -> new BusinessException("EXPENSE_NOT_FOUND"));
        expenseRepository.delete(expense);

        auditService.logAction("EXPENSE_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted expense: " + expense.getCategory()
            + " -- UGX " + expense.getAmount() + " (originally logged by " + expense.getRecordedBy() + ")");
    }

    // -- DIRECTOR ANALYSIS: SEARCH ------------------------------------

    @Transactional(readOnly = true)
    public Page<Expense> search(LocalDateTime from, LocalDateTime to, String category,
                                 String recordedBy, BigDecimal minAmount, BigDecimal maxAmount,
                                 Pageable pageable) {
        return expenseRepository.search(from, to, category, recordedBy, minAmount, maxAmount, pageable);
    }

    // -- DIRECTOR ANALYSIS: SUMMARY (TOTALS + CATEGORY BREAKDOWN) ----

    @Transactional(readOnly = true)
    public Map<String, Object> getSummary(LocalDateTime from, LocalDateTime to) {
        BigDecimal total = expenseRepository.sumBetween(from, to);
        List<Object[]> rows = expenseRepository.sumByCategoryBetween(from, to);

        Map<String, BigDecimal> byCategory = new LinkedHashMap<>();
        for (Object[] row : rows) {
            byCategory.put((String) row[0], (BigDecimal) row[1]);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total", total);
        result.put("byCategory", byCategory);
        return result;
    }

    // -- LIVE, NOT TIME-WINDOWED (used by the main Director Dashboard) -

    @Transactional(readOnly = true)
    public BigDecimal getAllTimeTotal() {
        return expenseRepository.sumAll();
    }

    @Transactional(readOnly = true)
    public Map<String, BigDecimal> getAllTimeByCategory() {
        Map<String, BigDecimal> byCategory = new LinkedHashMap<>();
        for (Object[] row : expenseRepository.sumByCategoryAll()) {
            byCategory.put((String) row[0], (BigDecimal) row[1]);
        }
        return byCategory;
    }
}
