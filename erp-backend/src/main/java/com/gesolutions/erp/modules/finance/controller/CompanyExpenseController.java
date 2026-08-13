// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/CompanyExpenseController.java
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
