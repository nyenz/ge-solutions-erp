// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PHYSICAL ASSET REGISTRY
 * RETIRED (pass 6): volume / folio / instrument_no / physical_box_number /
 * survey_date removed app-wide and dropped from the DB (PHASE G).
 * district/county stay as deprecated columns for backwards compatibility.
 */
@Entity
@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number"),
    @Index(name = "idx_title_id", columnList = "title_id")
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

    @Deprecated
    @Column(length = 100)
    private String district;

    @Deprecated
    @Column(length = 100)
    private String county;

    @Column(name = "title_id", length = 100)
    private String titleId;

    @Deprecated
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    @Builder.Default
    @Column(name = "is_released", nullable = false)
    private boolean isReleased = false;

    @Column(name = "created_at", updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}
