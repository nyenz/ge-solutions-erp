// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/FollowUpLog.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - ARCHIVE INTELLIGENCE LOG
 * Stores all qualitative notes, excuses, and recovery call results.
 * Supports 'Multiple Notes' from the Master Intake form.
 */
@Entity
@Table(name = "follow_up_logs")
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class FollowUpLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** fix225: empty for a note about the CLIENT (clientId is set instead). */
    @Column(name = "project_id")
    private UUID projectId;

    /** fix225 (David): a note about the client alone ("prefers calls after 5 pm"), not about one project. */
    @Column(name = "client_id")
    private UUID clientId;

    /**
     * STAGE 10 FIX: WHICH PERSON THIS CONTACT BELONGS TO.
     * Null for general project notes not tied to a specific call (e.g.
     * logNewNote). Set whenever this entry comes from logFollowUp, so a
     * joint project's contact history can be shown per owner instead of
     * one shared/anonymous note field (design brief 3.3).
     */
    @Column(name = "owner_id")
    private UUID ownerId;

    /**
     * THE INTELLIGENCE: Detailed record of the interaction or status.
     */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String notes;

    /**
     * AUDIT ANCHOR: Captured from the security context (Admin/Manager).
     */
    @Column(name = "recorded_by", nullable = false, length = 100)
    private String recordedBy;

    @Builder.Default
    @Column(name = "timestamp", nullable = false, updatable = false)
    private LocalDateTime timestamp = LocalDateTime.now();

    // fix215 (David): the Notes timeline. A note can be PINNED to the top, carry a FOLLOW-UP date (the bell reminds the
    // office that morning), a short TOPIC picked from the quick list, and ONE attached file (a project document).
    @Builder.Default
    @Column(name = "pinned")
    private Boolean pinned = Boolean.FALSE;

    @Column(name = "follow_up_on")
    private java.time.LocalDate followUpOn;

    @Column(name = "topic", length = 60)
    private String topic;

    @Column(name = "document_id")
    private UUID documentId;

    @Column(name = "edited_at")
    private LocalDateTime editedAt;
}