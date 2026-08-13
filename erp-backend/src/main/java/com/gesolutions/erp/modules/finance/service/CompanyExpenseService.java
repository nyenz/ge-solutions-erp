// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/CompanyExpenseService.java
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
