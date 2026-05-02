// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/PaymentRecord.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "payment_records", indexes = {
    @Index(name = "idx_payment_project", columnList = "project_id"),
    @Index(name = "idx_payment_timestamp", columnList = "timestamp")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PaymentRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "amount_paid", nullable = false, precision = 15, scale = 2)
    private BigDecimal amountPaid;

    // "STANDARD" for active plots, "BACKLOG_PARTIAL" for backlog plots
    @Builder.Default
    @Column(name = "payment_type", nullable = false, length = 50)
    private String paymentType = "STANDARD";

    @Column(name = "recorded_by", nullable = false, length = 100)
    private String recordedBy;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    @Builder.Default
    @Column(name = "timestamp", nullable = false, updatable = false)
    private LocalDateTime timestamp = LocalDateTime.now();

    // Snapshot of balance AFTER this payment was applied
    @Column(name = "balance_after", precision = 15, scale = 2)
    private BigDecimal balanceAfter;
}