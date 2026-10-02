// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PHYSICAL ASSET REGISTRY
 * RETIRED (pass 6): instrument_no / physical_box_number / survey_date removed app-wide and dropped from the DB (PHASE G).
 * district/county stay as deprecated columns for backwards compatibility.
 * fix180: TITLE DETAILS = Plot Number, Block, Area (hectares, required), Volume, Folio, Tenure, Title Date.
 * Title ID is removed (field and column). Volume and Folio are back as new columns.
 */
@Entity
@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number")
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

    // fix180: BLOCK (the Java name was block; the column keeps its old name so no data moves)
    @Column(name = "block_road", length = 100)
    private String block;

    // fix180: AREA in hectares -- required whenever Title Details are saved
    @Column(name = "area_hectares", precision = 14, scale = 4)
    private java.math.BigDecimal areaHectares;

    // fix180: register VOLUME and FOLIO
    @Column(name = "volume", length = 50)
    private String volume;

    @Column(name = "folio", length = 50)
    private String folio;

    @Deprecated
    @Column(length = 100)
    private String district;

    @Deprecated
    @Column(length = 100)
    private String county;

    @Deprecated
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    // fix167: sent as "isReleased" (Lombok alone named it "released", so no page ever saw a hand-over)
    @Builder.Default
    @com.fasterxml.jackson.annotation.JsonProperty("isReleased")
    @Column(name = "is_released", nullable = false)
    private boolean isReleased = false;

    // fix167: when the title was handed over, by whom, and the hand-over note (who collected it)
    @Column(name = "released_at")
    private LocalDateTime releasedAt;

    @Column(name = "released_by", length = 100)
    private String releasedBy;

    @Column(name = "release_note", columnDefinition = "TEXT")
    private String releaseNote;

    @Column(name = "created_at", updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}
