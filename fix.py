import os

def write_file(path, content, label):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  OK: {label}")

def patch_file(path, old_str, new_str, label):
    if not os.path.exists(path):
        print(f"  MISSING FILE: {path}")
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    old_str = old_str.replace("\r\n", "\n")
    if old_str in content:
        content = content.replace(old_str, new_str, 1)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"  OK: {label}")
    else:
        print(f"  SKIP/NOT FOUND: {label}")

print("\nAdding Priority 2 Reports (5 new reports)...")

# =============================================================================
# 1. BACKEND: Add 5 new methods to ReportService.java
# =============================================================================

patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java",
    "    /**\n     * PILLAR 8: REVENUE INFLOW HISTORY (NEW)\n     * Lists actual financial intake movements.\n     */\n    @Transactional(readOnly = true)\n    public byte[] generateRevenueHistory() {\n        List<LandProject> data = projectRepository.findAll();\n        StringBuilder csv = new StringBuilder();\n        csv.append(\"PLOT_ID,PAID_AMOUNT,CUMULATIVE_COLLECTION,PROTOCOL_MODE\").append(NEW_LINE);\n\n        for (LandProject p : data) {\n            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)\n               .append(p.getAmountPaid()).append(CSV_DIVIDER)\n               .append(p.getAmountPaid()).append(CSV_DIVIDER)\n               .append(p.isLegacy() ? \"BACKLOG_RECOVERY\" : \"STANDARD_INGESTION\").append(NEW_LINE);\n        }\n        return csv.toString().getBytes();\n    }\n}",
    """    /**
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
    }

    /**
     * PRIORITY 2 - REPORT 1: BACKLOG BREAKDOWN REPORT
     * All backlog plots with storage fees breakdown.
     */
    @Transactional(readOnly = true)
    public byte[] generateBacklogBreakdown() {
        List<LandProject> data = projectRepository.findAllBacklogPlots();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,BOX,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,BACKLOG_START,ORIGINAL_DEBT,STORAGE_FEES_UGX,MONTHS_IN_BACKLOG,TOTAL_PAID,TOTAL_OWED").append(NEW_LINE);

        for (LandProject p : data) {
            Client owner = p.getProprietors().stream().findFirst().orElse(new Client());
            java.math.BigDecimal origDebt = p.getOriginalDebt() != null ? p.getOriginalDebt() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal storageFees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal amountPaid = p.getAmountPaid() != null ? p.getAmountPaid() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal totalOwed = origDebt.add(storageFees).subtract(amountPaid);
            long months = p.getBacklogStartDate() != null
                ? java.time.temporal.ChronoUnit.MONTHS.between(p.getBacklogStartDate(), java.time.LocalDateTime.now())
                : 0;
            String backlogStart = p.getBacklogStartDate() != null
                ? p.getBacklogStartDate().toLocalDate().toString() : "UNKNOWN";

            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getDistrict() != null ? p.getLandTitle().getDistrict() : "").append(CSV_DIVIDER)
               .append(p.getLandTitle().getTenure() != null ? p.getLandTitle().getTenure() : "").append(CSV_DIVIDER)
               .append(owner.getFullName() != null ? owner.getFullName() : "").append(CSV_DIVIDER)
               .append(owner.getPhoneNumber() != null ? owner.getPhoneNumber() : "").append(CSV_DIVIDER)
               .append(backlogStart).append(CSV_DIVIDER)
               .append(origDebt).append(CSV_DIVIDER)
               .append(storageFees).append(CSV_DIVIDER)
               .append(months).append(CSV_DIVIDER)
               .append(amountPaid).append(CSV_DIVIDER)
               .append(totalOwed.max(java.math.BigDecimal.ZERO)).append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Backlog Breakdown Report Exported");
        return csv.toString().getBytes();
    }

    /**
     * PRIORITY 2 - REPORT 2: COMPLETED TITLES REPORT
     * All released / fully paid plots.
     */
    @Transactional(readOnly = true)
    public byte[] generateCompletedTitles() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,BOX,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,TOTAL_COST,AMOUNT_PAID,STATUS").append(NEW_LINE);

        for (LandProject p : data) {
            boolean released = p.getLandTitle().isReleased();
            boolean fullyPaid = p.getAmountPaid().compareTo(p.getTotalCost()) >= 0;
            if (!released && !fullyPaid) continue;

            Client owner = p.getProprietors().stream().findFirst().orElse(new Client());
            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getDistrict() != null ? p.getLandTitle().getDistrict() : "").append(CSV_DIVIDER)
               .append(p.getLandTitle().getTenure() != null ? p.getLandTitle().getTenure() : "").append(CSV_DIVIDER)
               .append(owner.getFullName() != null ? owner.getFullName() : "").append(CSV_DIVIDER)
               .append(owner.getPhoneNumber() != null ? owner.getPhoneNumber() : "").append(CSV_DIVIDER)
               .append(p.getTotalCost()).append(CSV_DIVIDER)
               .append(p.getAmountPaid()).append(CSV_DIVIDER)
               .append(released ? "RELEASED" : "FULLY_PAID_PENDING_RELEASE").append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Completed Titles Report Exported");
        return csv.toString().getBytes();
    }

    /**
     * PRIORITY 2 - REPORT 3: FULL PAYMENT HISTORY REPORT
     * All payment records across all plots.
     */
    @Transactional(readOnly = true)
    public byte[] generatePaymentHistory() {
        List<com.gesolutions.erp.modules.land.model.PaymentRecord> records =
            paymentRecordRepository.findAll(
                org.springframework.data.domain.Sort.by("timestamp").descending());
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

            String notes = pay.getNotes() != null ? pay.getNotes().replace(",", ";").replace("\"", "'") : "";
            csv.append(pay.getTimestamp().toLocalDate()).append(CSV_DIVIDER)
               .append(plotNumber).append(CSV_DIVIDER)
               .append(ownerName).append(CSV_DIVIDER)
               .append(pay.getPaymentType()).append(CSV_DIVIDER)
               .append(pay.getAmountPaid()).append(CSV_DIVIDER)
               .append(pay.getBalanceAfter() != null ? pay.getBalanceAfter() : "").append(CSV_DIVIDER)
               .append(pay.getRecordedBy()).append(CSV_DIVIDER)
               .append("\"").append(notes).append("\"").append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Full Payment History Exported");
        return csv.toString().getBytes();
    }

    /**
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
            java.math.BigDecimal origDebt = p.getOriginalDebt() != null ? p.getOriginalDebt() : java.math.BigDecimal.ZERO;
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
    }

    /**
     * PRIORITY 2 - REPORT 5: MONTHLY COLLECTION REPORT
     * How much was collected each month.
     */
    @Transactional(readOnly = true)
    public byte[] generateMonthlyCollection() {
        // Go back 24 months
        java.time.LocalDateTime since = java.time.LocalDateTime.now().minusMonths(24);
        java.util.List<Object[]> monthlyData = paymentRecordRepository.monthlyRevenueSince(since);

        StringBuilder csv = new StringBuilder();
        csv.append("YEAR_MONTH,TOTAL_COLLECTED_UGX,TRANSACTION_COUNT").append(NEW_LINE);

        if (monthlyData.isEmpty()) {
            csv.append("NO_DATA,0,0").append(NEW_LINE);
        } else {
            // monthlyRevenueSince returns [month_timestamp, sum_amount]
            // We need count too -- use a simple approach
            for (Object[] row : monthlyData) {
                String month = row[0] != null ? row[0].toString().substring(0, 7) : "UNKNOWN";
                String total = row[1] != null ? row[1].toString() : "0";
                csv.append(month).append(CSV_DIVIDER)
                   .append(total).append(CSV_DIVIDER)
                   .append("--").append(NEW_LINE);
            }
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Monthly Collection Report Exported");
        return csv.toString().getBytes();
    }
}""",
    "Added 5 new report methods to ReportService.java"
)

# We need to inject the paymentRecordRepository into ReportService
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java",
    "import com.gesolutions.erp.modules.land.model.*;\nimport com.gesolutions.erp.modules.land.repository.*;\nimport com.gesolutions.erp.modules.client.model.Client;",
    "import com.gesolutions.erp.modules.land.model.*;\nimport com.gesolutions.erp.modules.land.repository.*;\nimport com.gesolutions.erp.modules.client.model.Client;\nimport com.gesolutions.erp.modules.client.repository.ClientRepository;",
    "Added ClientRepository import to ReportService"
)

patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java",
    "    private final LandProjectRepository projectRepository;\n    private final AuditLogRepository auditLogRepository;\n    private final FollowUpRepository followUpRepository;\n    private final AuditService auditService;",
    "    private final LandProjectRepository projectRepository;\n    private final AuditLogRepository auditLogRepository;\n    private final FollowUpRepository followUpRepository;\n    private final AuditService auditService;\n    private final PaymentRecordRepository paymentRecordRepository;",
    "Added PaymentRecordRepository to ReportService fields"
)

# =============================================================================
# 2. BACKEND: Add 5 new endpoints to ReportController.java
# =============================================================================

patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/ReportController.java",
    "    /**\n     * INDUSTRIAL HELPER: Formats the byte stream with CSV headers.\n     */\n    private ResponseEntity<byte[]> streamCsv(byte[] data, String reportName) {",
    """    // ========================================================================
    // SECTION C: PRIORITY 2 REPORTS (All restricted to ROLE_ADMIN)
    // ========================================================================

    /** P2-1: Backlog Breakdown */
    @GetMapping("/backlog-breakdown")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadBacklogBreakdown() {
        return streamCsv(reportService.generateBacklogBreakdown(), "BACKLOG_BREAKDOWN");
    }

    /** P2-2: Completed Titles */
    @GetMapping("/completed-titles")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadCompletedTitles() {
        return streamCsv(reportService.generateCompletedTitles(), "COMPLETED_TITLES");
    }

    /** P2-3: Full Payment History */
    @GetMapping("/payment-history")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadPaymentHistory() {
        return streamCsv(reportService.generatePaymentHistory(), "FULL_PAYMENT_HISTORY");
    }

    /** P2-4: Storage Fees Per Plot */
    @GetMapping("/storage-fees")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadStorageFees() {
        return streamCsv(reportService.generateStorageFeesReport(), "STORAGE_FEES_REPORT");
    }

    /** P2-5: Monthly Collection */
    @GetMapping("/monthly-collection")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadMonthlyCollection() {
        return streamCsv(reportService.generateMonthlyCollection(), "MONTHLY_COLLECTION");
    }

    /**
     * INDUSTRIAL HELPER: Formats the byte stream with CSV headers.
     */
    private ResponseEntity<byte[]> streamCsv(byte[] data, String reportName) {""",
    "Added 5 new report endpoints to ReportController.java"
)

# We also need to add the Sort import to ReportService since we use it
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java",
    "import lombok.RequiredArgsConstructor;\nimport org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;",
    "import lombok.RequiredArgsConstructor;\nimport org.springframework.data.domain.Sort;\nimport org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;",
    "Added Sort import to ReportService"
)

# Fix the findAll call to use Sort
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java",
    "        List<com.gesolutions.erp.modules.land.model.PaymentRecord> records =\n            paymentRecordRepository.findAll(\n                org.springframework.data.domain.Sort.by(\"timestamp\").descending());",
    "        List<com.gesolutions.erp.modules.land.model.PaymentRecord> records =\n            paymentRecordRepository.findAll(Sort.by(\"timestamp\").descending());",
    "Clean up Sort import reference in generatePaymentHistory"
)

# =============================================================================
# 3. FRONTEND: Add 5 new downloads to reportService.js
# =============================================================================

patch_file(
    "erp-frontend/src/services/reportService.js",
    "    // Operational Pillars (Open to Managers)\n    downloadArchiveMap:  () => reportService._triggerDownload('/archive-map',       'PHYSICAL_ARCHIVE_MAP'),\n    downloadBottlenecks: () => reportService._triggerDownload('/bottlenecks',       'SURVEY_STAGES'),\n    downloadReliability: () => reportService._triggerDownload('/reliability',       'CLIENT_RANKINGS')\n};",
    """    // Operational Pillars (Open to Managers)
    downloadArchiveMap:  () => reportService._triggerDownload('/archive-map',       'PHYSICAL_ARCHIVE_MAP'),
    downloadBottlenecks: () => reportService._triggerDownload('/bottlenecks',       'SURVEY_STAGES'),
    downloadReliability: () => reportService._triggerDownload('/reliability',       'CLIENT_RANKINGS'),

    // Priority 2 Reports (Admin only)
    downloadBacklogBreakdown:  () => reportService._triggerDownload('/backlog-breakdown',  'BACKLOG_BREAKDOWN'),
    downloadCompletedTitles:   () => reportService._triggerDownload('/completed-titles',   'COMPLETED_TITLES'),
    downloadPaymentHistory:    () => reportService._triggerDownload('/payment-history',    'FULL_PAYMENT_HISTORY'),
    downloadStorageFees:       () => reportService._triggerDownload('/storage-fees',       'STORAGE_FEES_REPORT'),
    downloadMonthlyCollection: () => reportService._triggerDownload('/monthly-collection', 'MONTHLY_COLLECTION'),
};""",
    "Added 5 new download methods to reportService.js"
)

# =============================================================================
# 4. FRONTEND: Add 5 new report cards to ReportHub.jsx
# =============================================================================

patch_file(
    "erp-frontend/src/pages/Reports/ReportHub.jsx",
    "    const SYSTEM_GROUP = [\n        { id: 'legal', title: 'Legal Readiness Audit', desc: 'NIN and Address completeness check for demand notices.',   icon: FiFileText, action: reportService.downloadLegalReady  },\n        { id: 'audit', title: 'Master System Audit',   desc: 'Forensic footprint of data rewrites and stage jumps.',     icon: FiShield,   action: reportService.downloadAuditTrail  },\n    ];",
    """    const SYSTEM_GROUP = [
        { id: 'legal', title: 'Legal Readiness Audit', desc: 'NIN and Address completeness check for demand notices.',   icon: FiFileText, action: reportService.downloadLegalReady  },
        { id: 'audit', title: 'Master System Audit',   desc: 'Forensic footprint of data rewrites and stage jumps.',     icon: FiShield,   action: reportService.downloadAuditTrail  },
    ];

    const PRIORITY2_GROUP = [
        { id: 'backlog',   title: 'Backlog Breakdown',       desc: 'All backlog plots with storage fees, months owed, and total outstanding.',          icon: FiLock,       action: reportService.downloadBacklogBreakdown  },
        { id: 'completed', title: 'Completed Titles',        desc: 'All released or fully paid plots ready for handover.',                               icon: FiCheckSquare, action: reportService.downloadCompletedTitles  },
        { id: 'payhist',   title: 'Full Payment History',    desc: 'Every payment record across all plots — type, amount, balance after.',              icon: FiCreditCard, action: reportService.downloadPaymentHistory    },
        { id: 'storage',   title: 'Storage Fees Per Plot',   desc: 'Per-plot breakdown of accumulated storage fees and outstanding backlog balance.',    icon: FiDatabase,   action: reportService.downloadStorageFees       },
        { id: 'monthly',   title: 'Monthly Collection',      desc: 'Total cash collected per calendar month for the last 24 months.',                   icon: FiBarChart2,  action: reportService.downloadMonthlyCollection },
    ];""",
    "Added PRIORITY2_GROUP to ReportHub.jsx"
)

# Add the drawer state for priority2
patch_file(
    "erp-frontend/src/pages/Reports/ReportHub.jsx",
    "    const [drawers, setDrawers] = useState({ finance: true, ops: true, system: false });",
    "    const [drawers, setDrawers] = useState({ finance: true, ops: true, system: false, p2: true });",
    "Added p2 drawer state"
)

# Add the status entries for p2 reports
patch_file(
    "erp-frontend/src/pages/Reports/ReportHub.jsx",
    "    const [status,  setStatus]  = useState({\n        debt: false, map: false, perf: false,\n        stage: false, legal: false, risk: false,\n        audit: false, revenue: false,\n    });",
    """    const [status,  setStatus]  = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
        backlog: false, completed: false, payhist: false, storage: false, monthly: false,
    });""",
    "Added p2 status entries"
)

# Add the imports needed: FiLock, FiCheckSquare are already used or need adding
patch_file(
    "erp-frontend/src/pages/Reports/ReportHub.jsx",
    "import {\n    FiBarChart2, FiMap, FiActivity, FiLayers,\n    FiShield, FiTrendingUp, FiLock, FiDownloadCloud,\n    FiChevronDown, FiCreditCard, FiDatabase, FiFileText,\n    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo\n} from 'react-icons/fi';",
    "import {\n    FiBarChart2, FiMap, FiActivity, FiLayers,\n    FiShield, FiTrendingUp, FiLock, FiDownloadCloud,\n    FiChevronDown, FiCreditCard, FiDatabase, FiFileText,\n    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo\n} from 'react-icons/fi';",
    "Icons already correct (FiLock, FiCheckSquare exist)"
)

# Add the Priority 2 panel in the JSX - add it after the system panel
patch_file(
    "erp-frontend/src/pages/Reports/ReportHub.jsx",
    "                {hasFinancialAccess && (\n                    <div className={styles.hwPanel}>\n                        <DrawerTitle label=\"SYSTEM FORENSICS\" isOpen={drawers.system} onClick={() => toggleDrawer('system')} icon={FiShield} />\n                        <div className={`${styles.panelBody} ${drawers.system ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.system}>\n                            <div className={styles.panelInner}>\n                                <div className={styles.reportList}>\n                                    {SYSTEM_GROUP.map(item => <ReportRow key={item.id} item={item} />)}\n                                </div>\n                            </div>\n                        </div>\n                    </div>\n                )}\n            </div>",
    """                {hasFinancialAccess && (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="SYSTEM FORENSICS" isOpen={drawers.system} onClick={() => toggleDrawer('system')} icon={FiShield} />
                        <div className={`${styles.panelBody} ${drawers.system ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.system}>
                            <div className={styles.panelInner}>
                                <div className={styles.reportList}>
                                    {SYSTEM_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {hasFinancialAccess && (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="PRIORITY REPORTS" isOpen={drawers.p2} onClick={() => toggleDrawer('p2')} icon={FiBarChart2} />
                        <div className={`${styles.panelBody} ${drawers.p2 ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.p2}>
                            <div className={styles.panelInner}>
                                <div className={styles.reportList}>
                                    {PRIORITY2_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>""",
    "Added Priority 2 report panel to ReportHub JSX"
)

print("\nAll Priority 2 report changes applied.")
print("Summary:")
print("  Backend: 5 new methods in ReportService.java")
print("  Backend: 5 new endpoints in ReportController.java")
print("  Frontend: 5 new downloads in reportService.js")
print("  Frontend: 5 new cards in ReportHub.jsx (Priority Reports section)")