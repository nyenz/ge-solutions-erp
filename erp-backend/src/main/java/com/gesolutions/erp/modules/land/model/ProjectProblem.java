// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectProblem.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix289 (David, 5 Nov 2026): one problem on one project. Older titles in the office often have missing or wrong details
 * (no NIN, no phone, no contract number, the same number on two projects, wrong title details). A problem records what is
 * wrong and what will be done about it (the solution: a site visit, a call, a fix in the office, or decide later).
 * A problem about a person (phone, NIN) also carries that client, so the Clients page can show it.
 * Nothing here changes the project itself: it is a list beside the project.
 */
@Entity
@Table(name = "project_problems", indexes = {
        @Index(name = "ix_problem_project", columnList = "project_id"),
        @Index(name = "ix_problem_status", columnList = "status")
})
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class ProjectProblem {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "client_id")
    private UUID clientId;                 // the person the problem is about (phone, NIN), when there is one

    @Column(name = "kind", length = 30, nullable = false)
    private String kind;                   // NO_NIN, MISSING_PHONE, MISSING_INVOICE, MISSING_CONTRACT, WRONG_NUMBER, SAME_NUMBER, TITLE_DETAILS, LOCATION, FLAGGED, OTHER

    @Column(name = "label", length = 80, nullable = false)
    private String label;                  // what the list shows (for OTHER: the words typed, remembered for next time)

    @Column(name = "detail", columnDefinition = "TEXT")
    private String detail;

    @Column(name = "solution", length = 20, nullable = false)
    @Builder.Default
    private String solution = "LATER";     // SITE_VISIT, CALL, OFFICE, LATER

    @Column(name = "status", length = 10, nullable = false)
    @Builder.Default
    private String status = "OPEN";        // OPEN, SOLVED

    @Column(name = "linked_project_id")
    private UUID linkedProjectId;          // SAME_NUMBER: the other project with that number

    @Column(name = "auto_added", nullable = false)
    @Builder.Default
    private boolean autoAdded = false;     // added by a MISSING tick, not typed

    @Column(name = "created_by", length = 100)
    private String createdBy;

    @Column(name = "created_at", nullable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "solved_by", length = 100)
    private String solvedBy;

    @Column(name = "solved_at")
    private LocalDateTime solvedAt;

    @Column(name = "solved_note", columnDefinition = "TEXT")
    private String solvedNote;

    public boolean isOpen() { return "OPEN".equals(status); }
}
