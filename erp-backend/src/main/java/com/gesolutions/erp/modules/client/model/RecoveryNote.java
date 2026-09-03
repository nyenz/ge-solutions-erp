package com.gesolutions.erp.modules.client.model;

import com.gesolutions.erp.modules.auth.model.User;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * NOTES TAG SUBSYSTEM v1 - one row per operator tap on the Recovery cockpit.
 * tone: POSITIVE | NEGATIVE. countsAsAttempt tags feed the 2-14 handbrake.
 */
@Entity
@Table(name = "recovery_notes", indexes = {
    @Index(name = "idx_rnote_client",  columnList = "client_id"),
    @Index(name = "idx_rnote_attempt", columnList = "counts_as_attempt"),
    @Index(name = "idx_rnote_created", columnList = "created_at")
})
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class RecoveryNote {

    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "client_id")
    private Client client;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "author_id")
    private User author;

    @Column(nullable = false, length = 60)
    private String tag;

    @Column(nullable = false, length = 10)
    private String tone;

    @Column(name = "counts_as_attempt", nullable = false)
    private boolean countsAsAttempt;

    @Column(length = 500)
    private String text;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    void onCreate() { if (createdAt == null) createdAt = LocalDateTime.now(); }
}
