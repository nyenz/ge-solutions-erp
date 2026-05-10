// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java
package com.gesolutions.erp.modules.land.model;

import com.gesolutions.erp.modules.client.model.Client;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

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

    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)
    @JoinColumn(name = "title_id", nullable = false)
    private LandTitle landTitle;

    @Builder.Default
    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "project_proprietors",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "client_id")
    )
    private Set<Client> proprietors = new HashSet<>();

    @Column(name = "total_cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal totalCost;

    @Builder.Default
    @Column(name = "amount_paid", nullable = false, precision = 15, scale = 2)
    private BigDecimal amountPaid = BigDecimal.ZERO;

    @Column(name = "weekly_installment", precision = 15, scale = 2)
    private BigDecimal weeklyInstallment;

    @Column(name = "plan_type", length = 100)
    private String planType;

    // Boolean (object not primitive) so existing DB rows with NULL don't crash
    @Builder.Default
    @Column(name = "is_backlog")
    private Boolean isBacklog = false;

    @Column(name = "backlog_start_date")
    private LocalDateTime backlogStartDate;

    @Builder.Default
    @Column(name = "original_debt", precision = 15, scale = 2)
    private BigDecimal originalDebt = BigDecimal.ZERO;

    @Builder.Default
    @Column(name = "storage_fees_accumulated", precision = 15, scale = 2)
    private BigDecimal storageFeesAccumulated = BigDecimal.ZERO;

    /**
     * STORAGE FEE PAUSE: When true, the scheduler skips this plot.
     * Useful when a client is in active negotiation.
     */
    @Builder.Default
    @Column(name = "storage_paused", nullable = false)
    private boolean storagePaused = false;

    /**
     * STORAGE FEE OVERRIDE: Custom monthly rate (null = use system default 50,000).
     */
    @Column(name = "storage_fee_override", precision = 15, scale = 2)
    private BigDecimal storageFeeOverride;

    /**
     * NEGOTIATION DEADLINE: When set, storage fees pause automatically until this date.
     * Admin sets this when in active negotiation with client.
     */
    @Column(name = "negotiation_deadline")
    private java.time.LocalDateTime negotiationDeadline;

    /**
     * BACKLOG START DATE OVERRIDE: Allows admin to set the actual backlog start date
     * for titles entered late into the system (e.g. 2 months ago).
     */
    @Column(name = "backlog_start_override")
    private java.time.LocalDateTime backlogStartOverride;

    @Column(name = "last_payment_date")
    private LocalDateTime lastPaymentDate;

    @Builder.Default
    @Column(name = "is_legacy", nullable = false)
    private boolean isLegacy = false;

    @Builder.Default
    @Column(name = "current_stage_index", nullable = false)
    private Integer currentStageIndex = 1;

    @Builder.Default
    @Column(length = 50, nullable = false)
    private String status = "ACTIVE";

    public void addProprietor(Client client) {
        if (this.proprietors == null) this.proprietors = new HashSet<>();
        if (client != null) this.proprietors.add(client);
    }

    // Safe null-check — old DB rows have NULL for isBacklog
    public boolean isBacklog() {
        return Boolean.TRUE.equals(this.isBacklog);
    }

    public void setBacklog(boolean value) {
        this.isBacklog = value;
    }

    public BigDecimal backlogTotalOwed() {
        BigDecimal base = originalDebt != null ? originalDebt : BigDecimal.ZERO;
        BigDecimal fees = storageFeesAccumulated != null ? storageFeesAccumulated : BigDecimal.ZERO;
        BigDecimal paid = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return base.add(fees).subtract(paid);
    }

    public BigDecimal activeTotalOwed() {
        BigDecimal cost = totalCost != null ? totalCost : BigDecimal.ZERO;
        BigDecimal paid = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return cost.subtract(paid);
    }
}