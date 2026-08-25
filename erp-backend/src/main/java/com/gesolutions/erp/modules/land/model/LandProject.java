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

    // PHASE A (Section 18.10): landTitle is now optional. A LandProject
    // exists from intake onward and only gains a LandTitle once the final
    // processing stage is checked (or immediately, if the legacy preset is
    // used). See Section 18.9 in LLM_CONTEXT_GUIDE.md for the full target
    // model.
    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)
    @JoinColumn(name = "title_id", nullable = true)
    private LandTitle landTitle;

    /**
     * PROJECT INDEX (Section 18.3): short, never-repeating, searchable
     * code shown to clients and staff (e.g. "001A"). Assigned at
     * LandProject creation, before any title exists -- permanent and
     * universal across a record's whole life, folder or titled. Moved up
     * from LandTitle in Phase B (existing data migrated by
     * DataInitializer below) because the null-safe audit-log fallback
     * needs a project index that exists even when landTitle does not.
     * LandTitle.projectIndex is deprecated, not deleted.
     */
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    /**
     * PROJECT START DATE — set at intake, exists even before any title does.
     * Maps to LandEntryRequest.projectStartDate from the frontend.
     */
    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    /**
     * LOCATION (Section 18.4/18.9): permanent, not folder-only -- stays
     * visible for the whole life of the record, title or no title.
     * district/county are moved up from LandTitle (existing data migrated
     * by DataInitializer below); subCounty, parish, village, and area are
     * new. Area is left as free text since it is recorded in mixed units
     * (acres, decimals, etc) and is optional per Section 18.9.3.
     */
    @Column(length = 100)
    private String district;

    @Column(length = 100)
    private String county;

    @Column(name = "sub_county", length = 100)
    private String subCounty;

    @Column(length = 100)
    private String parish;

    @Column(length = 100)
    private String village;

    @Column(length = 100)
    private String area;

    @Transient
    @Builder.Default
    private java.util.List<ProjectStage> stages = new java.util.ArrayList<>();

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
    //
    // NOTE (Stage 5 cleanup pass): the 4 raw column names below (is_backlog,
    // backlog_start_date, backlog_start_override, backlog_months_billed) are
    // the only place in the whole app still saying "backlog" instead of
    // "receivable" -- the Java fields themselves were already renamed in
    // c858569. Left as-is on purpose: ddl-auto=update makes Hibernate sync
    // its schema from these @Column names BEFORE DataInitializer's raw-JDBC
    // migrations ever run, so renaming the annotation would make Hibernate
    // silently create a new empty column at boot and strand all the real
    // historical data in the old column name. Do not rename these without a
    // manual, out-of-band migration run directly against the live DB first.
    @Builder.Default
    @Column(name = "is_backlog")
    private Boolean isReceivable = false;

    @Column(name = "backlog_start_date")
    private LocalDateTime receivableStartDate;

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
     * RECEIVABLE START DATE OVERRIDE: Allows admin to set the actual receivable start date
     * for titles entered late into the system (e.g. 2 months ago).
     */
    @Column(name = "backlog_start_override")
    private java.time.LocalDateTime receivableStartOverride;

    /**
     * RECEIVABLE MONTHS BILLED COUNTER
     * Tracks how many monthly storage fee periods have been billed.
     * Used by ReceivableSchedulerService instead of division math, so
     * rate changes mid-way do not corrupt the billing calculation.
     */
    @Builder.Default
    @Column(name = "backlog_months_billed", nullable = false)
    private Integer receivableMonthsBilled = 0;

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

    // STAGE 3: SOFT DELETE -- nuclearDelete() no longer removes the row.
    @Builder.Default
    @Column(name = "deleted", nullable = false)
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    public void addProprietor(Client client) {
        if (this.proprietors == null) this.proprietors = new HashSet<>();
        if (client != null) this.proprietors.add(client);
    }

    // Safe null-check — old DB rows have NULL for isReceivable
    public boolean isReceivable() {
        return Boolean.TRUE.equals(this.isReceivable);
    }

    public void setReceivable(boolean value) {
        this.isReceivable = value;
    }

    public BigDecimal receivableTotalOwed() {
        // 4-Pocket Math: AMOUNT OWED = (totalCost + storageFeesAccumulated) - amountPaid
        BigDecimal value = totalCost != null ? totalCost : BigDecimal.ZERO;
        BigDecimal fees  = storageFeesAccumulated != null ? storageFeesAccumulated : BigDecimal.ZERO;
        BigDecimal paid  = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return value.add(fees).subtract(paid).max(BigDecimal.ZERO);
    }

    public BigDecimal activeTotalOwed() {
        BigDecimal cost = totalCost != null ? totalCost : BigDecimal.ZERO;
        BigDecimal paid = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return cost.subtract(paid);
    }
}