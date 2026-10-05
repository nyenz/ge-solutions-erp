// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java
package com.gesolutions.erp.modules.land.model;

import com.gesolutions.erp.modules.client.model.Client;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.LocalDate;
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
     * ENTRY DATE -- automatic, never client-editable. The actual calendar
     * day this record was keyed into Golden Seed, set once by the server
     * at intake (atomicIntake()) and never touched again. Distinct from
     * PROJECT START DATE above, which is when fieldwork began on the
     * ground and CAN be backdated by the operator (e.g. entering a
     * project two days after it actually started).
     */
    @Column(name = "entry_date", updatable = false)
    private LocalDate entryDate;

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
    private java.util.List<ProjectStatus> statuses = new java.util.ArrayList<>();

    /**
     * fix180: PROJECT TYPE -- one of the eight ProjectType names (FRESH_SURVEY, SUBDIVISION, LEGACY_TITLES,
     * TRANSFER_OF_TITLE, BOUNDARY_OPENING, TOPOGRAPHIC_SURVEY, RESURVEY, SPECIAL_PROJECTS). It decides whether
     * Title Details are kept and which status list the project starts with. Old rows (null) read through
     * ProjectType.of(project).
     */
    @Column(name = "project_type", length = 40)
    private String projectType;

    // fix180: Topographic Survey only -- staff switched the optional Title Details panel on
    @Builder.Default
    @com.fasterxml.jackson.annotation.JsonProperty("titleDetailsEnabled")
    @Column(name = "title_details_enabled", nullable = false)
    private boolean titleDetailsEnabled = false;

    // fix180: Subdivision only -- how many plots (subdivisions) the project creates
    @Column(name = "subdivision_count")
    private Integer subdivisionCount;

    // fix180: a Transfer of Title made from a subdivision points back to the subdivision project and plot number
    @Column(name = "parent_project_id")
    private UUID parentProjectId;

    @Column(name = "parent_subdivision_no")
    private Integer parentSubdivisionNo;

    /**
     * OWNERS (the people on the title). fix180: separate from the CLIENTS below. At intake the owners start as a copy
     * of the clients and staff can change them independently.
     */
    @Builder.Default
    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "project_proprietors",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "client_id")
    )
    private Set<Client> proprietors = new HashSet<>();

    /**
     * fix180: CLIENTS (the people who hired the company and pay). Shown first on every project. The CLIENT, not the
     * owner, is who the Recovery module calls and who pays.
     */
    @Builder.Default
    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "project_clients",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "client_id")
    )
    private Set<Client> clients = new HashSet<>();

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
     * fix173: THE system default monthly storage fee. The only place the number lives. The nightly fee job, the intake
     * save and (through GET /api/v1/land/storage-fee-default) the Intake and Folder pages all read this constant.
     */
    public static final BigDecimal DEFAULT_MONTHLY_STORAGE_FEE = new BigDecimal("50000");

    /**
     * STORAGE FEE OVERRIDE: Custom monthly rate (null = follow DEFAULT_MONTHLY_STORAGE_FEE).
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

    // fix167: sent as "isLegacy" (Lombok alone named it "legacy": the LEGACY badge never showed and every EDIT + SAVE wiped the flag)
    @Builder.Default
    @com.fasterxml.jackson.annotation.JsonProperty("isLegacy")
    @Column(name = "is_legacy", nullable = false)
    private boolean isLegacy = false;

    @Builder.Default
    @Column(name = "is_problem", nullable = false)
    private boolean problem = false;

    // fix167: who flagged the PROBLEM, when, and what it is (shown on the folder page)
    @Column(name = "problem_by", length = 100)
    private String problemBy;

    @Column(name = "problem_at")
    private LocalDateTime problemAt;

    @Column(name = "problem_note", columnDefinition = "TEXT")
    private String problemNote;

    // fix167: when the current storage-fee pause started. When the pause ends the billing clock is moved
    // forward by the paused days, so a pause really saves the client those months (it used to bill them all at once).
    @Column(name = "storage_paused_at")
    private LocalDateTime storagePausedAt;

    // fix167: how much of storageFeesAccumulated has been PAID (payments recorded as STORAGE). amountPaid still holds
    // every shilling received; this only splits it, so the page can show "fees paid" and "fees still owed".
    // It goes back to 0 whenever the project leaves receivables (the paid fees are then moved into the total cost).
    @Column(name = "storage_fees_paid", precision = 15, scale = 2)
    private BigDecimal storageFeesPaid;

    // fix180: was current_stage_index (renamed by StatusRenameMigration before Hibernate starts)
    @Builder.Default
    @Column(name = "current_status_index", nullable = false)
    private Integer currentStatusIndex = 1;

    @Builder.Default
    @Column(length = 50, nullable = false)
    private String status = "ACTIVE";

    // STAGE 3: SOFT DELETE -- nuclearDelete() no longer removes the row.
    @Builder.Default
    @Column(name = "deleted", nullable = false)
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    // fix181 (14.7a): why and by whom it was deleted (before, the reason was only inside the audit text)
    @Column(name = "deleted_reason", columnDefinition = "TEXT")
    private String deletedReason;

    @Column(name = "deleted_by", length = 100)
    private String deletedBy;

    /**
     * fix181 (8.9): PENDING = entered from the field (by an Employee) and not yet priced and accepted by the office.
     * A Pending project is left out of every money figure, Recovery and the nightly jobs: the plain findAll() of
     * LandProjectRepository skips it. Old rows are never Pending (default false).
     */
    @Builder.Default
    @com.fasterxml.jackson.annotation.JsonProperty("pending")
    @Column(name = "pending", nullable = false, columnDefinition = "boolean default false")
    private boolean pending = false;

    // fix181 (8.9, 4.4): when a Pending project was accepted (graduated); null for projects that were never Pending
    @Column(name = "graduated_at")
    private LocalDateTime graduatedAt;

    // fix181 (8.9): who entered the project (the account id, and the username as it was then); null on old rows
    @Column(name = "created_by_id")
    private UUID createdById;

    @Column(name = "created_by", length = 100)
    private String createdBy;

    /**
     * fix181 (20.9): the moment the record was saved, set once by the server. Old rows were back-filled from the
     * entry date, else the title's created date, else the start date (left empty when none is known).
     */
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    /** fix181 (16.12a): second safety against two people saving the same project at once (the first is the row lock). */
    @Version
    @Builder.Default
    @com.fasterxml.jackson.annotation.JsonIgnore
    @Column(name = "version", nullable = false, columnDefinition = "bigint default 0")
    private Long version = 0L;

    @PrePersist
    void fix181OnCreate() {
        if (createdAt == null) createdAt = LocalDateTime.now();
    }

    public void addProprietor(Client client) {
        if (this.proprietors == null) this.proprietors = new HashSet<>();
        if (client != null) this.proprietors.add(client);
    }

    // fix180
    public void addClient(Client client) {
        if (this.clients == null) this.clients = new HashSet<>();
        if (client != null) this.clients.add(client);
    }

    /** fix180: the people Recovery calls and who pay = the clients. A project saved before fix180 with no clients falls back to its owners. */
    public Set<Client> billingParties() {
        if (clients != null && !clients.isEmpty()) return clients;
        return proprietors != null ? proprietors : new HashSet<>();
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

    // fix167: storage fees paid so far (null in old rows = 0)
    public BigDecimal storagePaidSafe() {
        return storageFeesPaid != null ? storageFeesPaid : BigDecimal.ZERO;
    }

    // fix167: storage fees not yet paid (never below 0)
    public BigDecimal storageUnpaid() {
        BigDecimal fees = storageFeesAccumulated != null ? storageFeesAccumulated : BigDecimal.ZERO;
        return fees.subtract(storagePaidSafe()).max(BigDecimal.ZERO);
    }

    // fix167: ends a storage-fee pause. The billing clock (receivableStartDate) moves forward by the paused days, so the
    // months inside the pause are never billed. Before, the nightly job billed every paused month the day the pause ended.
    public void endStoragePause(LocalDateTime endAt) {
        if (storagePausedAt != null && receivableStartDate != null && endAt != null && endAt.isAfter(storagePausedAt)) {
            long days = java.time.temporal.ChronoUnit.DAYS.between(storagePausedAt, endAt);
            if (days > 0) receivableStartDate = receivableStartDate.plusDays(days);
        }
        storagePausedAt = null;
        storagePaused = false;
        negotiationDeadline = null;
    }

    public BigDecimal activeTotalOwed() {
        BigDecimal cost = totalCost != null ? totalCost : BigDecimal.ZERO;
        BigDecimal paid = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return cost.subtract(paid);
    }
}