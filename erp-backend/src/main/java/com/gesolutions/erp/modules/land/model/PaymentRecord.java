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
    @Index(name = "idx_payment_timestamp", columnList = "timestamp"),
    @Index(name = "idx_payment_client_request", columnList = "client_request_id")
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

    // "STANDARD" for active plots, "RECEIVABLE_PARTIAL" for receivable plots
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

    // fix167: WHICH owner paid (joint owners are tracked one by one), WHAT the money is for
    // (TITLE = the work, STORAGE = storage fees) and the receipt document filed with it.
    @Column(name = "payer_client_id")
    private UUID payerClientId;

    @Column(name = "payer_name", length = 200)
    private String payerName;

    @Column(name = "allocation", length = 20)
    private String allocation;

    @Column(name = "receipt_document_id")
    private UUID receiptDocumentId;

    /**
     * fix181 (11.6, 16.0): the day the money was PAID. `timestamp` is when the line was typed in.
     * NULL only for an undated intake deposit (paid before the project was entered, day unknown).
     * A reversal has its own date (when it was made), so money-by-period nets to zero.
     * "Last payment", the Dashboard and Reports read this, never `timestamp`.
     */
    @Column(name = "paid_on")
    private LocalDateTime paidOn;

    /** fix181 (16.12b): one-time id sent by the payment window, so a retried request is not saved twice. */
    @Column(name = "client_request_id", length = 64)
    private String clientRequestId;
}