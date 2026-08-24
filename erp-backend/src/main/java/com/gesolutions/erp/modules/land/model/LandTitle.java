// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PHYSICAL ASSET REGISTRY
 * Maps 1-1 with the technical documents (Deed Plans and Titles).
 * Optimized with Indexes for high-speed filing cabinet lookups.
 */
@Entity
@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number"),
    @Index(name = "idx_title_id", columnList = "title_id"),
    @Index(name = "idx_physical_archive", columnList = "physical_box_number")
})
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class LandTitle {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 50)
    private String tenure; // e.g. MAILO, FREEHOLD

    @Column(name = "plot_number", unique = true, length = 100)
    private String plotNumber;

    @Column(name = "block_road", length = 100)
    private String blockRoad;

    /**
     * PHYSICAL ARCHIVE LOGISTICS
     * Which physical box in the office holds this title's paperwork.
     * Restored after being accidentally deleted in Phase D -- previously
     * mandatory, now OPTIONAL, since a folder-only project has no title
     * yet and therefore nothing physical to file. Set once the physical
     * document actually arrives, same bucket as volume/folio/instrumentNo.
     */
    @Column(name = "physical_box_number", length = 100)
    private String physicalBoxNumber;

    // DEPRECATED (Phase A, Section 18.10): district/county now live on
    // LandProject and are the source of truth going forward. These
    // columns are kept here on purpose -- not deleted -- because
    // LandService.java and ReportService.java still read/write them
    // directly. Repointing those call sites to LandProject is scoped to
    // Phase B (Section 18.9.1), not this phase. Do not remove these
    // fields until Phase B has migrated every call site.
    @Deprecated
    @Column(length = 100)
    private String district;

    @Deprecated
    @Column(length = 100)
    private String county;

    /* --- TECHNICAL CABINET SPECS --- */
    
    @Column(length = 50)
    private String volume;

    @Column(length = 50)
    private String folio;

    @Column(name = "instrument_no", length = 100)
    private String instrumentNo;

    @Column(name = "title_id", length = 100)
    private String titleId;

    /**
     * PROJECT INDEX
     * Short, never-repeating, searchable code shown to clients and staff.
     * Format: 001A, 002A ... 999A, 001B, 002B ... 999B, 001C ...
     * Generated automatically at intake by ProjectIndexService.
     */
    // DEPRECATED (Phase B, Section 18.10/18.3): projectIndex now lives
    // on LandProject and is assigned there at creation, before any title
    // exists -- see LandProject.java. Kept here on purpose -- not
    // deleted -- since atomicIntake() still writes the same value to
    // both places for backward compatibility with anything still reading
    // it off LandTitle. Safe to drop once nothing reads it from here.
    @Deprecated
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    /**
     * PROJECT START DATE
     * The date when the project was initiated/intake was done.
     * Auto-filled with today's date during intake, but can be edited.
     */
    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    /**
     * TITLE ISSUE DATE
     * The date when the land title was actually issued/received.
     * Optional field - can be set later when title is received.
     * Can be backdated to match the actual title issue date.
     */
    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    @Column(name = "survey_date")
    private LocalDate surveyDate;

    @Builder.Default
    @Column(name = "is_released", nullable = false)
    private boolean isReleased = false;

    @Column(name = "created_at", updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}