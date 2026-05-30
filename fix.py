import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch_file(path, old, new):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    if old not in content:
        print(f"MISSING: patch target not found in {path}")
        return
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content.replace(old, new, 1))
    print(f"OK: patched {path}")

BASE = "erp-backend/src/main/java/com/gesolutions/erp"

# ============================================================
# 1. LandProject.java - Add backlogMonthsBilled field
# ============================================================
patch_file(
    f"{BASE}/modules/land/model/LandProject.java",
    """    @Column(name = "backlog_start_override")
    private java.time.LocalDateTime backlogStartOverride;""",
    """    @Column(name = "backlog_start_override")
    private java.time.LocalDateTime backlogStartOverride;

    /**
     * BACKLOG MONTHS BILLED COUNTER
     * Tracks how many monthly storage fee periods have been billed.
     * Used by BacklogSchedulerService instead of division math, so
     * rate changes mid-way do not corrupt the billing calculation.
     */
    @Builder.Default
    @Column(name = "backlog_months_billed", nullable = false)
    private Integer backlogMonthsBilled = 0;"""
)

# ============================================================
# 2. DataInitializer.java - Add migration for new column
# ============================================================
patch_file(
    f"{BASE}/config/DataInitializer.java",
    """            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS survey_date DATE",""",
    """            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS survey_date DATE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0","""
)

# ============================================================
# 3. BacklogSchedulerService.java - Use counter instead of division
# ============================================================
patch_file(
    f"{BASE}/modules/land/service/BacklogSchedulerService.java",
    """            long daysSinceBacklog = ChronoUnit.DAYS.between(plot.getBacklogStartDate(), now);
            long periodsOwed = daysSinceBacklog / 30;

            if (periodsOwed <= 0) continue;

            BigDecimal monthlyRate = (plot.getStorageFeeOverride() != null && plot.getStorageFeeOverride().compareTo(BigDecimal.ZERO) > 0)
                    ? plot.getStorageFeeOverride() : DEFAULT_MONTHLY_FEE;

            BigDecimal currentFees = plot.getStorageFeesAccumulated() != null
                    ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;

            long feesAlreadyApplied = monthlyRate.compareTo(BigDecimal.ZERO) > 0
                    ? currentFees.divide(monthlyRate, 0, RoundingMode.DOWN).longValue()
                    : 0L;

            if (feesAlreadyApplied >= periodsOwed) continue;

            long feesMissing = periodsOwed - feesAlreadyApplied;
            BigDecimal toAdd = monthlyRate.multiply(BigDecimal.valueOf(feesMissing));

            plot.setStorageFeesAccumulated(currentFees.add(toAdd));
            projectRepository.save(plot);

            auditService.logAction("STORAGE_FEE_APPLIED",
                "SYSTEM: Added UGX " + toAdd + " monthly storage fee to backlog plot: "
                + plot.getLandTitle().getPlotNumber()
                + " (" + feesMissing + " month(s) x UGX " + monthlyRate + ")"
                + " | Total accumulated fees: UGX " + plot.getStorageFeesAccumulated());""",
    """            long daysSinceBacklog = ChronoUnit.DAYS.between(plot.getBacklogStartDate(), now);
            long periodsOwed = daysSinceBacklog / 30;

            if (periodsOwed <= 0) continue;

            // Use the counter (not division) to determine how many months remain to bill.
            // This is immune to rate changes mid-way through the backlog period.
            int alreadyBilled = plot.getBacklogMonthsBilled() != null ? plot.getBacklogMonthsBilled() : 0;

            if (alreadyBilled >= periodsOwed) continue;

            BigDecimal monthlyRate = (plot.getStorageFeeOverride() != null && plot.getStorageFeeOverride().compareTo(BigDecimal.ZERO) > 0)
                    ? plot.getStorageFeeOverride() : DEFAULT_MONTHLY_FEE;

            BigDecimal currentFees = plot.getStorageFeesAccumulated() != null
                    ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;

            long feesMissing = periodsOwed - alreadyBilled;
            BigDecimal toAdd = monthlyRate.multiply(BigDecimal.valueOf(feesMissing));

            plot.setStorageFeesAccumulated(currentFees.add(toAdd));
            plot.setBacklogMonthsBilled((int) periodsOwed);
            projectRepository.save(plot);

            auditService.logAction("STORAGE_FEE_APPLIED",
                "SYSTEM: Added UGX " + toAdd + " monthly storage fee to backlog plot: "
                + plot.getLandTitle().getPlotNumber()
                + " (" + feesMissing + " month(s) x UGX " + monthlyRate + ")"
                + " | Total accumulated fees: UGX " + plot.getStorageFeesAccumulated());"""
)

# ============================================================
# 4. LandService.java - Fix updateProjectFull to sync originalDebt
# ============================================================
patch_file(
    f"{BASE}/modules/land/service/LandService.java",
    """        project.setTotalCost(request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO);
        project.setAmountPaid(request.getInitialPayment() != null ? request.getInitialPayment() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());""",
    """        BigDecimal newTotalCost = request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO;
        project.setTotalCost(newTotalCost);
        project.setAmountPaid(request.getInitialPayment() != null ? request.getInitialPayment() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());

        // FIX 1: If in backlog, keep originalDebt in sync with totalCost changes.
        // originalDebt = new title cost minus payments already made toward the title.
        if (project.isBacklog()) {
            BigDecimal amtPaid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
            project.setOriginalDebt(newTotalCost.subtract(amtPaid).max(BigDecimal.ZERO));
        }"""
)

# ============================================================
# 5. LandService.java - Fix exitBacklog to recalibrate math
# ============================================================
patch_file(
    f"{BASE}/modules/land/service/LandService.java",
    """        project.setBacklog(false);
        project.setBacklogStartDate(null);
        project.setOriginalDebt(BigDecimal.ZERO);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setStatus("ACTIVE");
        projectRepository.save(project);

        auditService.logAction("BACKLOG_EXIT",
            "Operator [" + getCurrentOperator() + "] manually removed plot "
            + project.getLandTitle().getPlotNumber()
            + " from BACKLOG. Accumulated storage fees of UGX " + project.getStorageFeesAccumulated() + " cleared.");""",
    """        // FIX 3: Recalibrate amountPaid on exit so active math is correct.
        // Payments made toward storage fees should not be counted against the title cost.
        // We recalculate how much was actually paid toward the title by subtracting
        // storage fees that were paid (excess over original debt).
        BigDecimal titleCost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal totalPaid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        BigDecimal storageFees = project.getStorageFeesAccumulated() != null ? project.getStorageFeesAccumulated() : BigDecimal.ZERO;

        // Amount that went toward the title = totalPaid minus any overpayment that covered storage fees
        BigDecimal backlogTotal = titleCost.add(storageFees);
        BigDecimal titlePaymentPortion = totalPaid;
        if (totalPaid.compareTo(backlogTotal) >= 0) {
            // Fully paid everything; title is fully paid
            titlePaymentPortion = titleCost;
        } else if (totalPaid.compareTo(titleCost) > 0) {
            // Paid more than title cost - excess went to storage
            titlePaymentPortion = titleCost;
        }
        // else: paid less than or equal to title cost, all goes to title

        project.setAmountPaid(titlePaymentPortion);
        project.setBacklog(false);
        project.setBacklogStartDate(null);
        project.setOriginalDebt(BigDecimal.ZERO);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setBacklogMonthsBilled(0);
        project.setStatus("ACTIVE");
        projectRepository.save(project);

        auditService.logAction("BACKLOG_EXIT",
            "Operator [" + getCurrentOperator() + "] manually removed plot "
            + project.getLandTitle().getPlotNumber()
            + " from BACKLOG. Storage fees cleared. Title amount paid recalibrated to UGX " + titlePaymentPortion + ".");"""
)

# ============================================================
# 6. LandService.java - Fix recordPayment to honour payment type
# ============================================================
patch_file(
    f"{BASE}/modules/land/service/LandService.java",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        String operator = getCurrentOperator();
        String paymentType = project.isBacklog() ? "BACKLOG_PARTIAL" : "STANDARD";

        BigDecimal newAmountPaid = project.getAmountPaid().add(amount);
        project.setAmountPaid(newAmountPaid);
        project.setLastPaymentDate(LocalDateTime.now());

        BigDecimal balanceAfter;
        if (project.isBacklog()) {
            balanceAfter = project.backlogTotalOwed();
        } else {
            balanceAfter = project.getTotalCost().subtract(newAmountPaid);
        }

        PaymentRecord record = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(amount)
                .paymentType(paymentType)
                .recordedBy(operator)
                .notes(notes)
                .balanceAfter(balanceAfter)
                .build();
        paymentRecordRepository.save(record);

        // Auto-exit backlog if fully paid
        if (project.isBacklog() && balanceAfter.compareTo(BigDecimal.ZERO) <= 0) {
            project.setBacklog(false);
            project.setStatus("ACTIVE");
            projectRepository.save(project);
            auditService.logAction("BACKLOG_EXIT",
                "Operator [" + operator + "] -- Plot " + project.getLandTitle().getPlotNumber()
                + " EXITED BACKLOG after full payment clearance.");
        } else {
            projectRepository.save(project);
        }

        auditService.logAction("PAYMENT_RECORDED",
            "Operator [" + operator + "] recorded UGX " + amount
            + " for plot: " + project.getLandTitle().getPlotNumber()
            + " | Type: " + paymentType
            + " | Balance after: UGX " + balanceAfter);
    }""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        String operator = getCurrentOperator();

        // FIX 4: Honour payment type. If notes start with [STORAGE FEE PAYMENT],
        // deduct from storageFeesAccumulated and record as BACKLOG_STORAGE.
        // Otherwise treat as title payment (STANDARD or BACKLOG_PARTIAL).
        boolean isStorageFeePayment = project.isBacklog()
                && notes != null && notes.startsWith("[STORAGE FEE PAYMENT]");

        String paymentType;
        BigDecimal balanceAfter;

        if (isStorageFeePayment) {
            // Payment goes toward storage fees
            paymentType = "BACKLOG_STORAGE";
            BigDecimal currentFees = project.getStorageFeesAccumulated() != null
                    ? project.getStorageFeesAccumulated() : BigDecimal.ZERO;
            BigDecimal newFees = currentFees.subtract(amount).max(BigDecimal.ZERO);
            project.setStorageFeesAccumulated(newFees);
            project.setLastPaymentDate(LocalDateTime.now());
            balanceAfter = project.backlogTotalOwed();
        } else {
            // Payment goes toward title cost
            paymentType = project.isBacklog() ? "BACKLOG_PARTIAL" : "STANDARD";
            BigDecimal newAmountPaid = project.getAmountPaid().add(amount);
            project.setAmountPaid(newAmountPaid);
            project.setLastPaymentDate(LocalDateTime.now());
            if (project.isBacklog()) {
                balanceAfter = project.backlogTotalOwed();
            } else {
                balanceAfter = project.getTotalCost().subtract(newAmountPaid);
            }
        }

        PaymentRecord record = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(amount)
                .paymentType(paymentType)
                .recordedBy(operator)
                .notes(notes)
                .balanceAfter(balanceAfter)
                .build();
        paymentRecordRepository.save(record);

        // Auto-exit backlog if fully paid
        if (project.isBacklog() && balanceAfter.compareTo(BigDecimal.ZERO) <= 0) {
            project.setBacklog(false);
            project.setStatus("ACTIVE");
            projectRepository.save(project);
            auditService.logAction("BACKLOG_EXIT",
                "Operator [" + operator + "] -- Plot " + project.getLandTitle().getPlotNumber()
                + " EXITED BACKLOG after full payment clearance.");
        } else {
            projectRepository.save(project);
        }

        auditService.logAction("PAYMENT_RECORDED",
            "Operator [" + operator + "] recorded UGX " + amount
            + " for plot: " + project.getLandTitle().getPlotNumber()
            + " | Type: " + paymentType
            + " | Balance after: UGX " + balanceAfter);
    }"""
)

print("\nAll patches applied.")
print("Run: git add -A && git commit -m 'fix: sync originalDebt, months-billed counter, exitBacklog recalibration, payment type routing' && git push")