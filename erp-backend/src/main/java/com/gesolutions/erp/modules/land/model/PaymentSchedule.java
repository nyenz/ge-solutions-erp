// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/PaymentSchedule.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

/**
 * GE SOLUTIONS - FINANCIAL VELOCITY TRACKER
 * Physically implements the 3+1 payment architecture.
 * Every 4th entry is a Grace Week with 0 expected revenue.
 */
@Entity
@Table(name = "payment_schedules", indexes = {
    @Index(name = "idx_project_schedule", columnList = "project_id"),
    @Index(name = "idx_due_date", columnList = "due_date")
})
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class PaymentSchedule {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "due_date", nullable = false)
    private LocalDate dueDate;

    @Column(name = "expected_amount", nullable = false, precision = 15, scale = 2)
    private BigDecimal expectedAmount;

    @Builder.Default
    @Column(name = "actual_paid", nullable = false, precision = 15, scale = 2)
    private BigDecimal actualPaid = BigDecimal.ZERO;

    /**
     * GRACE MODULE: When TRUE, this is an rest week. 
     * System bypasses demand logic for this entry.
     */
    @Builder.Default
    @Column(name = "is_grace_week", nullable = false)
    private boolean isGraceWeek = false;

    /**
     * COMPLETION STATUS: 
     * True when actualPaid >= expectedAmount.
     */
    @Builder.Default
    @Column(name = "is_satisfied", nullable = false)
    private boolean isSatisfied = false;
}