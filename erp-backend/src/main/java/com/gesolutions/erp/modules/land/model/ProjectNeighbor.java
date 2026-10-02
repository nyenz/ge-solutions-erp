// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectNeighbor.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix180: NEIGHBORS panel. The people whose land borders this project, kept on every project type and independent
 * of Title Details and of the Client / Owner panels. Neighbors are not clients: no NIN, no recovery.
 */
@Entity
@Table(name = "project_neighbors", indexes = {
    @Index(name = "idx_neighbor_project", columnList = "project_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProjectNeighbor {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "full_name", nullable = false, length = 200)
    private String fullName;

    @Column(name = "phone", length = 100)
    private String phone;

    // which side of the plot (e.g. NORTH, SOUTH-EAST) -- free text
    @Column(name = "side", length = 50)
    private String side;

    @Column(name = "plot_number", length = 100)
    private String plotNumber;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    @Builder.Default
    @Column(name = "display_order", nullable = false)
    private Integer displayOrder = 0;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
