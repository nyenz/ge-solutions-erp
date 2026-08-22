// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/model/Expense.java
package com.gesolutions.erp.modules.finance.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - EXPENSE (EXPENSES REBUILD)
 *
 * Replaces the old CompanyExpense "committed vs paid" model. An Expense is
 * a flat, permanent fact: this amount of cash left the office, for this
 * category, logged by this person, at this moment. No debt tracking, no
 * partial payments -- if money hasn't left yet, it isn't logged yet.
 *
 * Category is free text (usually one of the ExpensePreset names, but
 * "Other" one-off categories are allowed too).
 *
 * Editable for 24 hours after creation by any Manager+ user (not just the
 * person who logged it) to fix mistakes -- every edit is written to the
 * audit log and also tracked here via editedAt/editedBy so the UI can show
 * an "edited" badge without needing to read the audit log.
 */
@Entity
@Table(name = "expenses", indexes = {
    @Index(name = "idx_expenses_created_at", columnList = "created_at"),
    @Index(name = "idx_expenses_category", columnList = "category")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Expense {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "category", nullable = false, length = 150)
    private String category;

    @Column(name = "amount", nullable = false, precision = 15, scale = 2)
    private BigDecimal amount;

    @Column(name = "note", columnDefinition = "TEXT")
    private String note;

    @Column(name = "recorded_by", length = 100)
    private String recordedBy;

    /**
     * Who the cash actually left the office with -- NOT necessarily the same
     * person as recordedBy. A secretary can log a fuel expense that was
     * actually spent by a field agent. Optional: if blank, the UI and every
     * analysis query fall back to recordedBy so old rows and same-person
     * entries behave exactly as before.
     */
    @Column(name = "spent_by", length = 100)
    private String spentBy;

    @Builder.Default
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "edited_at")
    private LocalDateTime editedAt;

    @Column(name = "edited_by", length = 100)
    private String editedBy;

    /**
     * Editable for 24 hours after creation. Checked server-side on every
     * edit attempt -- this is not just a UI hint.
     */
    @Transient
    public boolean isEditable() {
        return createdAt != null && createdAt.plusHours(24).isAfter(LocalDateTime.now());
    }
}
