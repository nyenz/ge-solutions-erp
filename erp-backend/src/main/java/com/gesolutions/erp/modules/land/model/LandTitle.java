// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
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

    @Column(name = "plot_number", unique = true, nullable = false, length = 100)
    private String plotNumber;

    @Column(name = "block_road", length = 100)
    private String blockRoad;

    @Column(length = 100)
    private String district;

    @Column(length = 100)
    private String county;

    /* --- TECHNICAL CABINET SPECS --- */
    
    @Column(length = 50)
    private String volume;

    @Column(length = 50)
    private String folio;

    @Column(name = "instrument_no", length = 100)
    private String instrumentNo;

    /**
     * PHYSICAL ARCHIVE LOGISTICS
     * Mandatory link to the physical location in the office.
     */
    @Column(name = "physical_box_number", nullable = false, length = 100)
    private String physicalBoxNumber;

    @Builder.Default
    @Column(name = "is_released", nullable = false)
    private boolean isReleased = false;

    @Column(name = "created_at", updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}