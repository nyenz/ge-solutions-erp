// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/ExpenseController.java
package com.gesolutions.erp.modules.finance.controller;

import com.gesolutions.erp.modules.finance.model.Expense;
import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.service.ExpenseService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * GE SOLUTIONS - EXPENSES MODULE (EXPENSES REBUILD)
 *
 * Any Manager+ (Manager, Director, Admin/Root) can log an expense, create a
 * preset, view recent entries, and edit within the 24-hour window. Only
 * Director/Admin can delete an entry, run the detailed search/filter, or
 * pull the totals-by-category summary used by the Analysis view.
 */
@RestController
@RequestMapping("/api/v1/finance/expenses")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class ExpenseController {

    private final ExpenseService expenseService;

    // -- PRESETS (Manager+) ------------------------------------------

    @GetMapping("/presets")
    public ResponseEntity<List<ExpensePreset>> getPresets() {
        return ResponseEntity.ok(expenseService.getPresets());
    }

    @PostMapping("/presets")
    public ResponseEntity<ExpensePreset> createPreset(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("name");
        return ResponseEntity.ok(expenseService.createPreset(name));
    }

    // -- CATEGORY AUTOCOMPLETE (Manager+) ------------------------------

    @GetMapping("/categories")
    public ResponseEntity<List<String>> getCategorySuggestions() {
        return ResponseEntity.ok(expenseService.getCategorySuggestions());
    }

    // -- LOGGING (Manager+) -------------------------------------------

    @PostMapping
    public ResponseEntity<Expense> createExpense(@RequestBody Map<String, Object> body) {
        String category = (String) body.get("category");
        BigDecimal amount = body.get("amount") != null ? new BigDecimal(body.get("amount").toString()) : null;
        String note = (String) body.get("note");
        String spentBy = (String) body.get("spentBy");
        return ResponseEntity.ok(expenseService.createExpense(category, amount, note, spentBy));
    }

    @GetMapping("/recent")
    public ResponseEntity<List<Expense>> getRecent(@RequestParam(defaultValue = "24") int hours) {
        return ResponseEntity.ok(expenseService.getRecent(hours));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Expense> editExpense(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        String category = (String) body.get("category");
        BigDecimal amount = body.get("amount") != null ? new BigDecimal(body.get("amount").toString()) : null;
        String note = (String) body.get("note");
        String spentBy = (String) body.get("spentBy");
        return ResponseEntity.ok(expenseService.editExpense(id, category, amount, note, spentBy));
    }

    // -- DELETE (DIRECTOR/ADMIN ONLY) ----------------------------------

    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> deleteExpense(@PathVariable UUID id) {
        expenseService.deleteExpense(id);
        return ResponseEntity.noContent().build();
    }

    // -- ANALYSIS: SEARCH (DIRECTOR/ADMIN ONLY) ------------------------

    @GetMapping("/search")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Page<Expense>> search(
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String recordedBy,
            @RequestParam(required = false) String spentBy,
            @RequestParam(required = false) BigDecimal minAmount,
            @RequestParam(required = false) BigDecimal maxAmount,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {

        LocalDateTime fromDt = (from != null && !from.isBlank()) ? LocalDate.parse(from).atStartOfDay() : null;
        LocalDateTime toDt = (to != null && !to.isBlank()) ? LocalDate.parse(to).atTime(LocalTime.MAX) : null;

        return ResponseEntity.ok(expenseService.search(
            fromDt, toDt, category, recordedBy, spentBy, minAmount, maxAmount, PageRequest.of(page, size)
        ));
    }

    // -- ANALYSIS: SUMMARY (DIRECTOR/ADMIN ONLY) -----------------------

    @GetMapping("/summary")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Map<String, Object>> getSummary(
            @RequestParam(defaultValue = "MONTH") String period,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to) {

        LocalDateTime fromDt;
        LocalDateTime toDt = LocalDateTime.now();

        if ("CUSTOM".equalsIgnoreCase(period) && from != null && !from.isBlank()) {
            fromDt = LocalDate.parse(from).atStartOfDay();
            toDt = (to != null && !to.isBlank()) ? LocalDate.parse(to).atTime(LocalTime.MAX) : toDt;
        } else {
            switch (period.toUpperCase()) {
                case "TODAY": fromDt = LocalDate.now().atStartOfDay(); break;
                case "WEEK":  fromDt = LocalDate.now().minusDays(7).atStartOfDay(); break;
                case "YEAR":  fromDt = LocalDate.now().minusYears(1).atStartOfDay(); break;
                case "MONTH":
                default:      fromDt = LocalDate.now().minusDays(30).atStartOfDay(); break;
            }
        }

        return ResponseEntity.ok(expenseService.getSummary(fromDt, toDt));
    }

    // -- ANALYSIS: BY STAFF (DIRECTOR/ADMIN ONLY) -----------------------

    @GetMapping("/analytics/by-staff")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Map<String, BigDecimal>> byStaff(
            @RequestParam(defaultValue = "MONTH") String period,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to) {
        LocalDateTime[] range = resolveRange(period, from, to);
        return ResponseEntity.ok(expenseService.getByStaff(range[0], range[1]));
    }

    // -- ANALYSIS: SPENDING OVER TIME (DIRECTOR/ADMIN ONLY) -------------

    @GetMapping("/analytics/timeseries")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<List<Map<String, Object>>> timeseries(
            @RequestParam(defaultValue = "MONTH") String period,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to,
            @RequestParam(defaultValue = "DAY") String bucket) {
        LocalDateTime[] range = resolveRange(period, from, to);
        return ResponseEntity.ok(expenseService.getTimeSeries(range[0], range[1], bucket));
    }

    /** Same TODAY/WEEK/MONTH/YEAR/CUSTOM resolution already used by getSummary(), shared here. */
    private LocalDateTime[] resolveRange(String period, String from, String to) {
        LocalDateTime fromDt;
        LocalDateTime toDt = LocalDateTime.now();

        if ("CUSTOM".equalsIgnoreCase(period) && from != null && !from.isBlank()) {
            fromDt = LocalDate.parse(from).atStartOfDay();
            toDt = (to != null && !to.isBlank()) ? LocalDate.parse(to).atTime(LocalTime.MAX) : toDt;
        } else {
            switch (period.toUpperCase()) {
                case "TODAY": fromDt = LocalDate.now().atStartOfDay(); break;
                case "WEEK":  fromDt = LocalDate.now().minusDays(7).atStartOfDay(); break;
                case "YEAR":  fromDt = LocalDate.now().minusYears(1).atStartOfDay(); break;
                case "MONTH":
                default:      fromDt = LocalDate.now().minusDays(30).atStartOfDay(); break;
            }
        }
        return new LocalDateTime[]{fromDt, toDt};
    }
}
