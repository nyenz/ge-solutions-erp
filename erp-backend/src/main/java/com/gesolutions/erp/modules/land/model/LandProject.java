// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java
package com.gesolutions.erp.modules.land.model;

import com.gesolutions.erp.modules.client.model.Client;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/**
 * GE SOLUTIONS - THE DIGITAL BINDER (TERMINAL X VERSION)
 * 
 * Physically consolidates the 5 data clusters. 
 * Managed via the 'God-Mode' service logic.
 */
@Entity
@Table(name = "land_projects")
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class LandProject {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /**
     * CLUSTER 1: TECHNICAL ASSET
     * CascadeType.ALL ensures technical specs are updated during Master Handshake.
     */
    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)
    @JoinColumn(name = "title_id", nullable = false)
    private LandTitle landTitle;

    /**
     * CLUSTER 2: IDENTITY LEDGER
     * Managed as a Join Table to allow unlimited Joint Proprietors.
     */
    @Builder.Default
    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "project_proprietors",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "client_id")
    )
    private Set<Client> proprietors = new HashSet<>();

    /* --- CLUSTER 3: FINANCIAL HARDWARE --- */
    
    @Column(name = "total_cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal totalCost;

    @Builder.Default
    @Column(name = "amount_paid", nullable = false, precision = 15, scale = 2)
    private BigDecimal amountPaid = BigDecimal.ZERO;

    @Column(name = "weekly_installment", precision = 15, scale = 2)
    private BigDecimal weeklyInstallment;

    @Column(name = "plan_type", length = 100)
    private String planType;

    /**
     * THE LEGACY OVERRIDE:
     * When TRUE, this folder belongs to the 1,000 title backlog 
     * and standard financial locks are loosened.
     */
    @Builder.Default
    @Column(name = "is_legacy", nullable = false)
    private boolean isLegacy = false;

    /* --- CLUSTER 5: OPERATIONAL CIRCUIT --- */

    /**
     * PIPELINE PROGRESSION:
     * Values 1 to 5. Corresponds to the 5-dot UI progress bar.
     */
    @Builder.Default
    @Column(name = "current_stage_index", nullable = false)
    private Integer currentStageIndex = 1;

    /**
     * GLOBAL SYSTEM STATUS:
     * ACTIVE, RECOVERY (for manually moved backlog), COMPLETED, or DEFAULTED.
     */
    @Builder.Default
    @Column(length = 50, nullable = false)
    private String status = "ACTIVE";

    /**
     * DOMAIN LOGIC: Proprietor Management
     * Safely adds owners without triggering collection corruption.
     */
    public void addProprietor(Client client) {
        if (this.proprietors == null) {
            this.proprietors = new HashSet<>();
        }
        if (client != null) {
            this.proprietors.add(client);
        }
    }
}