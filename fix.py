import os, re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK: {label}")
    else:
        print(f"MISSING: {label}")

BASE = "erp-backend/src/main/java/com/gesolutions/erp/modules/land"
SERVICE = f"{BASE}/service/ReportService.java"
CONTROLLER = f"{BASE}/controller/ReportController.java"
FRONTEND_HUB = "erp-frontend/src/pages/Reports/ReportHub.jsx"
FRONTEND_SERVICE = "erp-frontend/src/services/reportService.js"

# ─── 1. ReportService.java ────────────────────────────────────────────────────

# Replace generateRevenueHistory (Pillar 8) with full payment history version
OLD_PILLAR8 = '''    /**
     * PILLAR 8: REVENUE INFLOW HISTORY (NEW)
     * Lists actual financial intake movements.
     */
    @Transactional(readOnly = true)
    public byte[] generateRevenueHistory() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,PAID_AMOUNT,CUMULATIVE_COLLECTION,PROTOCOL_MODE").append(NEW_LINE);

        for (LandProject p : data) {
            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getAmountPaid()).append(CSV_DIVIDER)
               .append(p.getAmountPaid()).append(CSV_DIVIDER)
               .append(p.isLegacy() ? "BACKLOG_RECOVERY" : "STANDARD_INGESTION").append(NEW_LINE);
        }
        return csv.toString().getBytes();
    }'''

NEW_PILLAR8 = '''    /**
     * PILLAR 8: FULL PAYMENT HISTORY (PROMOTED FROM P2)
     * Every payment record across all plots - date, amount, operator, notes.
     */
    @Transactional(readOnly = true)
    public byte[] generateRevenueHistory() {
        List<com.gesolutions.erp.modules.land.model.PaymentRecord> records =
            paymentRecordRepository.findAll(Sort.by("timestamp").descending());
        StringBuilder csv = new StringBuilder();
        csv.append("DATE,PLOT_ID,OWNER_NAME,PAYMENT_TYPE,AMOUNT_UGX,BALANCE_AFTER_UGX,RECORDED_BY,NOTES").append(NEW_LINE);

        for (com.gesolutions.erp.modules.land.model.PaymentRecord pay : records) {
            String plotNumber = "---";
            String ownerName = "---";
            try {
                java.util.Optional<LandProject> proj = projectRepository.findById(pay.getProjectId());
                if (proj.isPresent()) {
                    plotNumber = proj.get().getLandTitle().getPlotNumber();
                    ownerName = proj.get().getProprietors().stream()
                        .findFirst().map(com.gesolutions.erp.modules.client.model.Client::getFullName).orElse("---");
                }
            } catch (Exception ignored) {}

            String notes = pay.getNotes() != null ? pay.getNotes().replace(",", ";") : "";
            csv.append(pay.getTimestamp().toLocalDate()).append(CSV_DIVIDER)
               .append(plotNumber).append(CSV_DIVIDER)
               .append(ownerName).append(CSV_DIVIDER)
               .append(pay.getPaymentType()).append(CSV_DIVIDER)
               .append(pay.getAmountPaid()).append(CSV_DIVIDER)
               .append(pay.getBalanceAfter() != null ? pay.getBalanceAfter() : "").append(CSV_DIVIDER)
               .append(pay.getRecordedBy()).append(CSV_DIVIDER)
               .append(notes).append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Pillar 8: Full Payment History Exported");
        return csv.toString().getBytes();
    }'''

patch(SERVICE, OLD_PILLAR8, NEW_PILLAR8, "ReportService: Replace Pillar 8 with full payment history")

# Replace generatePaymentHistory (P2-3) - remove it and storage fees (P2-4), add operator reconciliation
OLD_PAYHIST = '''    /**
     * PRIORITY 2 - REPORT 3: FULL PAYMENT HISTORY REPORT
     * All payment records across all plots.
     */
    @Transactional(readOnly = true)
    public byte[] generatePaymentHistory() {
        List<com.gesolutions.erp.modules.land.model.PaymentRecord> records =
            paymentRecordRepository.findAll(Sort.by("timestamp").descending());
        StringBuilder csv = new StringBuilder();
        csv.append("DATE,PLOT_ID,OWNER_NAME,PAYMENT_TYPE,AMOUNT_UGX,BALANCE_AFTER_UGX,RECORDED_BY,NOTES").append(NEW_LINE);

        for (com.gesolutions.erp.modules.land.model.PaymentRecord pay : records) {
            String plotNumber = "---";
            String ownerName = "---";
            try {
                java.util.Optional<LandProject> proj = projectRepository.findById(pay.getProjectId());
                if (proj.isPresent()) {
                    plotNumber = proj.get().getLandTitle().getPlotNumber();
                    ownerName = proj.get().getProprietors().stream()
                        .findFirst().map(Client::getFullName).orElse("---");
                }
            } catch (Exception ignored) {}

            String notes = pay.getNotes() != null ? pay.getNotes().replace(",", ";") : "";
            csv.append(pay.getTimestamp().toLocalDate()).append(CSV_DIVIDER)
               .append(plotNumber).append(CSV_DIVIDER)
               .append(ownerName).append(CSV_DIVIDER)
               .append(pay.getPaymentType()).append(CSV_DIVIDER)
               .append(pay.getAmountPaid()).append(CSV_DIVIDER)
               .append(pay.getBalanceAfter() != null ? pay.getBalanceAfter() : "").append(CSV_DIVIDER)
               .append(pay.getRecordedBy()).append(CSV_DIVIDER)
               .append(notes).append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Full Payment History Exported");
        return csv.toString().getBytes();
    }'''

NEW_PAYHIST = '''    /**
     * PRIORITY 2 - REPORT 3: OPERATOR CASH RECONCILIATION (ANTI-THEFT)
     * Groups all payments by the operator who recorded them.
     * Allows Root Owner to reconcile physical cash against system records.
     */
    @Transactional(readOnly = true)
    public byte[] generatePaymentHistory() {
        List<com.gesolutions.erp.modules.land.model.PaymentRecord> records =
            paymentRecordRepository.findAll(Sort.by("timestamp").ascending());
        StringBuilder csv = new StringBuilder();
        csv.append("OPERATOR_ID,TOTAL_CASH_COLLECTED_UGX,NUMBER_OF_TRANSACTIONS,FIRST_PAYMENT_DATE,LAST_PAYMENT_DATE").append(NEW_LINE);

        java.util.Map<String, java.util.List<com.gesolutions.erp.modules.land.model.PaymentRecord>> byOperator =
            records.stream().collect(java.util.stream.Collectors.groupingBy(
                com.gesolutions.erp.modules.land.model.PaymentRecord::getRecordedBy));

        byOperator.entrySet().stream()
            .sorted(java.util.Map.Entry.comparingByKey())
            .forEach(entry -> {
                String operator = entry.getKey();
                java.util.List<com.gesolutions.erp.modules.land.model.PaymentRecord> ops = entry.getValue();
                java.math.BigDecimal total = ops.stream()
                    .map(com.gesolutions.erp.modules.land.model.PaymentRecord::getAmountPaid)
                    .reduce(java.math.BigDecimal.ZERO, java.math.BigDecimal::add);
                long count = ops.size();
                String firstDate = ops.get(0).getTimestamp().toLocalDate().toString();
                String lastDate = ops.get(ops.size() - 1).getTimestamp().toLocalDate().toString();
                csv.append(operator).append(CSV_DIVIDER)
                   .append(total).append(CSV_DIVIDER)
                   .append(count).append(CSV_DIVIDER)
                   .append(firstDate).append(CSV_DIVIDER)
                   .append(lastDate).append(NEW_LINE);
            });

        auditService.logAction("REPORT_EXPORT", "Priority 2: Operator Cash Reconciliation Exported");
        return csv.toString().getBytes();
    }'''

patch(SERVICE, OLD_PAYHIST, NEW_PAYHIST, "ReportService: Replace payment history with operator reconciliation")

# Remove generateStorageFeesReport entirely
OLD_STORAGE = '''        /**
     * PRIORITY 2 - REPORT 4: STORAGE FEES PER PLOT REPORT
     * Total storage fees accumulated per backlog plot.
     */
    @Transactional(readOnly = true)
    public byte[] generateStorageFeesReport() {
        List<LandProject> data = projectRepository.findAllBacklogPlots();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,BOX,PRIMARY_OWNER,PHONE,BACKLOG_START_DATE,MONTHS_IN_BACKLOG,ORIGINAL_DEBT_UGX,STORAGE_FEES_UGX,RATE_PER_MONTH_UGX,TOTAL_PAID_UGX,OUTSTANDING_UGX").append(NEW_LINE);

        java.math.BigDecimal monthlyRate = new java.math.BigDecimal("50000");

        for (LandProject p : data) {
            Client owner = p.getProprietors().stream().findFirst().orElse(new Client());
            java.math.BigDecimal origDebt = p.getTotalCost() != null ? p.getTotalCost() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal storageFees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal amountPaid = p.getAmountPaid() != null ? p.getAmountPaid() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal outstanding = origDebt.add(storageFees).subtract(amountPaid).max(java.math.BigDecimal.ZERO);
            long months = p.getBacklogStartDate() != null
                ? java.time.temporal.ChronoUnit.MONTHS.between(p.getBacklogStartDate(), java.time.LocalDateTime.now())
                : 0;
            String backlogStart = p.getBacklogStartDate() != null
                ? p.getBacklogStartDate().toLocalDate().toString() : "UNKNOWN";

            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
               .append(owner.getFullName() != null ? owner.getFullName() : "").append(CSV_DIVIDER)
               .append(owner.getPhoneNumber() != null ? owner.getPhoneNumber() : "").append(CSV_DIVIDER)
               .append(backlogStart).append(CSV_DIVIDER)
               .append(months).append(CSV_DIVIDER)
               .append(origDebt).append(CSV_DIVIDER)
               .append(storageFees).append(CSV_DIVIDER)
               .append(monthlyRate).append(CSV_DIVIDER)
               .append(amountPaid).append(CSV_DIVIDER)
               .append(outstanding).append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Storage Fees Report Exported");
        return csv.toString().getBytes();
    }'''

patch(SERVICE, OLD_STORAGE, '', "ReportService: Remove storage fees report")

# ─── 2. ReportController.java ─────────────────────────────────────────────────

OLD_CTRL_STORAGE = '''    /** P2-4: Storage Fees Per Plot */
    @GetMapping("/storage-fees")
    @PreAuthorize("hasRole(\'ROLE_ADMIN\')")
    public ResponseEntity<byte[]> downloadStorageFees() {
        return streamCsv(reportService.generateStorageFeesReport(), "STORAGE_FEES_REPORT");
    }

    /** P2-5: Monthly Collection */'''

NEW_CTRL_STORAGE = '''    /** P2-4: Monthly Collection */'''

patch(CONTROLLER, OLD_CTRL_STORAGE, NEW_CTRL_STORAGE, "ReportController: Remove storage fees endpoint")

# Update monthly collection from P2-5 to P2-4 in controller (label only, method unchanged)
# Also rename payment-history endpoint label
OLD_CTRL_PAYHIST = '''    /** P2-3: Full Payment History */
    @GetMapping("/payment-history")
    @PreAuthorize("hasRole(\'ROLE_ADMIN\')")
    public ResponseEntity<byte[]> downloadPaymentHistory() {
        return streamCsv(reportService.generatePaymentHistory(), "FULL_PAYMENT_HISTORY");
    }'''

NEW_CTRL_PAYHIST = '''    /** P2-3: Operator Cash Reconciliation (Anti-Theft) */
    @GetMapping("/payment-history")
    @PreAuthorize("hasRole(\'ROLE_ADMIN\')")
    public ResponseEntity<byte[]> downloadPaymentHistory() {
        return streamCsv(reportService.generatePaymentHistory(), "OPERATOR_CASH_RECONCILIATION");
    }'''

patch(CONTROLLER, OLD_CTRL_PAYHIST, NEW_CTRL_PAYHIST, "ReportController: Rename payment-history to operator reconciliation")

# ─── 3. reportService.js ─────────────────────────────────────────────────────

OLD_JS_STORAGE = '''    downloadStorageFees:       () => reportService._triggerDownload(\'/storage-fees\',       \'STORAGE_FEES_REPORT\'),
    downloadMonthlyCollection: () => reportService._triggerDownload(\'/monthly-collection\', \'MONTHLY_COLLECTION\'),'''

NEW_JS_STORAGE = '''    downloadMonthlyCollection: () => reportService._triggerDownload(\'/monthly-collection\', \'MONTHLY_COLLECTION\'),'''

patch(FRONTEND_SERVICE, OLD_JS_STORAGE, NEW_JS_STORAGE, "reportService.js: Remove downloadStorageFees")

OLD_JS_PAYHIST = '''    downloadPaymentHistory:    () => reportService._triggerDownload(\'/payment-history\',    \'FULL_PAYMENT_HISTORY\'),'''
NEW_JS_PAYHIST = '''    downloadOperatorReconciliation: () => reportService._triggerDownload(\'/payment-history\', \'OPERATOR_CASH_RECONCILIATION\'),'''

patch(FRONTEND_SERVICE, OLD_JS_PAYHIST, NEW_JS_PAYHIST, "reportService.js: Rename to downloadOperatorReconciliation")

# ─── 4. ReportHub.jsx ─────────────────────────────────────────────────────────

OLD_HUB_P2 = '''    const PRIORITY2_GROUP = [
        { id: \'backlog\',   title: \'Backlog Breakdown\',       desc: \'All backlog plots with storage fees, months owed, and total outstanding.\',          icon: FiLock,       action: reportService.downloadBacklogBreakdown  },
        { id: \'completed\', title: \'Completed Titles\',        desc: \'All released or fully paid plots ready for handover.\',                               icon: FiCheckSquare, action: reportService.downloadCompletedTitles  },
        { id: \'payhist\',   title: \'Full Payment History\',    desc: \'Every payment record across all plots — type, amount, balance after.\',              icon: FiCreditCard, action: reportService.downloadPaymentHistory    },
        { id: \'storage\',   title: \'Storage Fees Per Plot\',   desc: \'Per-plot breakdown of accumulated storage fees and outstanding backlog balance.\',    icon: FiDatabase,   action: reportService.downloadStorageFees       },
        { id: \'monthly\',   title: \'Monthly Collection\',      desc: \'Total cash collected per calendar month for the last 24 months.\',                   icon: FiBarChart2,  action: reportService.downloadMonthlyCollection },
    ];'''

NEW_HUB_P2 = '''    const PRIORITY2_GROUP = [
        { id: \'backlog\',   title: \'Backlog Breakdown\',            desc: \'All backlog plots with storage fees, months owed, and total outstanding.\',                                         icon: FiLock,       action: reportService.downloadBacklogBreakdown         },
        { id: \'completed\', title: \'Completed Titles\',             desc: \'All released or fully paid plots ready for handover.\',                                                            icon: FiCheckSquare, action: reportService.downloadCompletedTitles         },
        { id: \'reconcile\', title: \'Operator Cash Reconciliation\', desc: \'Anti-theft: total cash collected per operator, transaction count, and date range. Compare against physical cash.\', icon: FiShield,     action: reportService.downloadOperatorReconciliation   },
        { id: \'monthly\',   title: \'Monthly Collection\',           desc: \'Total cash collected per calendar month for the last 24 months.\',                                                 icon: FiBarChart2,  action: reportService.downloadMonthlyCollection        },
    ];'''

patch(FRONTEND_HUB, OLD_HUB_P2, NEW_HUB_P2, "ReportHub.jsx: Update Priority 2 group")

# Update status keys in ReportHub
OLD_HUB_STATUS = '''    const [status,  setStatus]  = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
        backlog: false, completed: false, payhist: false, storage: false, monthly: false,
    });'''

NEW_HUB_STATUS = '''    const [status,  setStatus]  = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
        backlog: false, completed: false, reconcile: false, monthly: false,
    });'''

patch(FRONTEND_HUB, OLD_HUB_STATUS, NEW_HUB_STATUS, "ReportHub.jsx: Update status keys")

print("\nDone. All patches applied.")