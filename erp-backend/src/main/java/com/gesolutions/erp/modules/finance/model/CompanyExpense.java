// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/model/CompanyExpense.java
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
