// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/TimelineEntry.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix215 (David): one line of a project's Notes timeline that the APP writes -- a REASON typed in a reason window
 * (add fees to cost, pause, reduce, delete ...) or an EVENT (project started, stage ticked, storage fee added ...).
 * Typed notes stay in follow_up_logs, payments in payment_records and calls in recovery_notes; TimelineService joins them.
 * Lines are never edited or deleted (like the audit trail). money = only the Manager and above see the line.
 */
@Entity
@Table(name = "project_timeline", indexes = {
    @Index(name = "idx_timeline_project", columnList = "project_id"),
    @Index(name = "idx_timeline_source", columnList = "source_audit_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TimelineEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    /** REASON or EVENT */
    @Column(name = "kind", nullable = false, length = 10)
    private String kind;

    /** the audit code it belongs to (FEES_CAPITALIZED, PROJECT_STATUS_CHANGED ...) */
    @Column(name = "action", length = 60)
    private String action;

    /** the short words people read first: "Fees added to the cost" */
    @Column(name = "title", nullable = false, length = 160)
    private String title;

    /** the reason typed by staff (REASON lines) */
    @Column(name = "reason", columnDefinition = "TEXT")
    private String reason;

    /** the facts: "UGX 2,000,000 -> UGX 2,150,000" */
    @Column(name = "detail", columnDefinition = "TEXT")
    private String detail;

    @Builder.Default
    @Column(name = "money", nullable = false)
    private boolean money = false;

    @Column(name = "recorded_by", nullable = false, length = 100)
    private String recordedBy;

    @Builder.Default
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    /** set on lines copied once from the audit trail (fix215 back-fill), so they are never copied twice */
    @Column(name = "source_audit_id")
    private UUID sourceAuditId;
}
