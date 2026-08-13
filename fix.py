# PATH: fix.py
# PHASE 3B - 4-TIER ROLE PERMISSION WIRING (ADDITIVE, ROLE_DIRECTOR ONLY)
# Run from project root: py fix.py
#
# SCOPE OF THIS PATCH -- READ BEFORE RUNNING:
#
# This wires ROLE_DIRECTOR into every place that currently grants ROLE_ADMIN
# full/financial access, at BOTH layers (controller @PreAuthorize AND service
# @PreAuthorize, since method security checks both and a mismatch would cause
# a 403 even after the controller lets the request through).
#
# It is 100% ADDITIVE:
#   - Every check goes from  hasRole('ROLE_ADMIN')
#                       to    hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')
#   - Every check goes from  hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')
#                       to    hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')
#   - Nothing that ROLE_ADMIN or ROLE_MANAGER can currently do is removed.
#   - No user in your database has ROLE_DIRECTOR yet (StaffController's
#     create/promote endpoints DO already accept it as a raw enum value via
#     API, but nothing in the current UI offers it as a dropdown option),
#     so until you actually assign it to someone, this patch changes
#     ZERO real-world behavior. It is safe to deploy immediately.
#
# DELIBERATELY NOT INCLUDED IN THIS PATCH (and why):
#
#   1. ROLE_SECRETARY is NOT wired into anything yet.
#      Per Section 17.7, Secretary can change stages but NOT edit costs.
#      The current codebase has no endpoint-level separation between
#      "change a stage" and "edit a cost" -- LandController's full-update
#      endpoint does both in one call, and the backlog/storage endpoints
#      are inherently cost operations. Wiring Secretary in now would mean
#      Secretary could edit costs through the same door Managers use,
#      violating the target design. That separation is exactly what
#      Phase 4 (Stage Templates) introduces -- per-stage cost fields
#      distinct from stage-change actions. Secretary gets wired in
#      correctly as part of Phase 4, not bolted on early here.
#
#   2. SettingsPage.jsx (staff management UI) is NOT touched.
#      I do not have its current file content in context (it was marked
#      as a binary/unreadable file in the last full dump), and patching
#      a file blind violates the project's own fix.py safety rule
#      ("always verify the exact text to replace by reading the document
#      context before writing patches"). This means: until SettingsPage.jsx
#      is re-sent to me, there is still no UI dropdown to actually assign
#      ROLE_DIRECTOR to anyone. The backend/API will accept it either way
#      -- David could technically promote someone via Postman -- but no
#      button exists in the app yet. Flagged as Phase 3C.
#
#   3. StaffController.java is NOT touched. Staff governance (create,
#      promote, suspend, reset password) stays exactly as strict as it
#      is today -- ROLE_ADMIN + isRoot gated. The 4-tier table doesn't
#      grant Director any staff-management rights, so there's nothing to
#      add here, and touching it unnecessarily would only add risk.
#
#   4. Nuclear delete (DELETE /land/projects/{id}) stays root-only.
#      Not part of the Director grant -- deletion is a Founder-only action
#      by existing design, table doesn't override that.
#
# TEST PLAN (do this at your single end-of-phases test pass):
#   1. Log in as your existing admin_root / any ROLE_ADMIN account --
#      confirm every page, report, and payment action still works exactly
#      as before (this patch should be invisible to existing accounts).
#   2. Via Postman (since no UI yet): PATCH /api/v1/staff/{username}/role
#      with newRole=ROLE_DIRECTOR on a test account, log in as that
#      account, and confirm it now sees financials, reports, audit trail,
#      payments, and backlog controls -- same as ROLE_ADMIN would.
#   3. Confirm a ROLE_MANAGER account is UNCHANGED -- still blocked from
#      reports/audit/payments, same as before this patch.

import os

def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  -> Saved: {path}")

def patch_file(path, anchor, replacement, label):
    content = read_file(path)
    if content is None:
        print(f"FAIL: {label} ({path} not found)")
        return
    if anchor not in content:
        print(f"MISSING: {label} (anchor not found in {path} -- may already be patched, or file changed)")
        return
    if content.count(anchor) > 1:
        print(f"WARN: {label} (anchor appears more than once -- patching first occurrence only)")
    content = content.replace(anchor, replacement, 1)
    write_file(path, content)
    print(f"OK: {label}")

print("Starting Phase 3B Patch - ROLE_DIRECTOR Permission Wiring...")
print("-" * 60)

# ============================================================
# BACKEND CONTROLLERS
# ============================================================

# ---- AuditController.java ----
path = "erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditController.java"

patch_file(path,
    """@RestController
@RequestMapping("/api/v1/admin/audit")
@RequiredArgsConstructor
// Base Gate: Must be at least a Manager to hit the API, but specific methods are tighter
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class AuditController {""",
    """@RestController
@RequestMapping("/api/v1/admin/audit")
@RequiredArgsConstructor
// Base Gate: Must be at least a Manager to hit the API, but specific methods are tighter
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class AuditController {""",
    "AuditController class gate (+DIRECTOR)")

patch_file(path,
    """    @GetMapping("/stream")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<Page<AuditLog>> getRawStream(""",
    """    @GetMapping("/stream")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Page<AuditLog>> getRawStream(""",
    "AuditController /stream (+DIRECTOR)")

patch_file(path,
    """    @GetMapping("/search")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<Page<AuditLog>> searchForensics(""",
    """    @GetMapping("/search")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Page<AuditLog>> searchForensics(""",
    "AuditController /search (+DIRECTOR)")

patch_file(path,
    """    @GetMapping("/investigate")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<Page<AuditLog>> investigateKeyword(""",
    """    @GetMapping("/investigate")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Page<AuditLog>> investigateKeyword(""",
    "AuditController /investigate (+DIRECTOR)")

# ---- DashboardController.java ----
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java"

patch_file(path,
    """@RestController
@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class DashboardController {""",
    """@RestController
@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class DashboardController {""",
    "DashboardController class gate (+DIRECTOR)")

patch_file(path,
    """        boolean showFinancials = currentUser.isRoot() || currentUser.getRole() == Role.ROLE_ADMIN;""",
    """        boolean showFinancials = currentUser.isRoot()
                || currentUser.getRole() == Role.ROLE_ADMIN
                || currentUser.getRole() == Role.ROLE_DIRECTOR;""",
    "DashboardController showFinancials (+DIRECTOR)")

# ---- LandController.java ----
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java"

patch_file(path,
    """@RestController
@RequestMapping("/api/v1/land")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class LandController {""",
    """@RestController
@RequestMapping("/api/v1/land")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class LandController {""",
    "LandController class gate (+DIRECTOR)")

patch_file(path,
    """    @PostMapping("/projects/{id}/backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> moveToBacklog(@PathVariable UUID id) {""",
    """    @PostMapping("/projects/{id}/backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> moveToBacklog(@PathVariable UUID id) {""",
    "LandController /backlog (+DIRECTOR)")

patch_file(path,
    """    @PostMapping("/projects/{id}/exit-backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> exitBacklog(@PathVariable UUID id,""",
    """    @PostMapping("/projects/{id}/exit-backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitBacklog(@PathVariable UUID id,""",
    "LandController /exit-backlog (+DIRECTOR)")

patch_file(path,
    """    @PostMapping("/projects/{id}/exit-backlog-capitalize")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> exitBacklogCapitalize(@PathVariable UUID id) {""",
    """    @PostMapping("/projects/{id}/exit-backlog-capitalize")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitBacklogCapitalize(@PathVariable UUID id) {""",
    "LandController /exit-backlog-capitalize (+DIRECTOR)")

patch_file(path,
    """    @PatchMapping("/projects/{id}/storage-pause")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,""",
    """    @PatchMapping("/projects/{id}/storage-pause")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,""",
    "LandController /storage-pause (+DIRECTOR)")

patch_file(path,
    """    @PatchMapping("/projects/{id}/storage-rate")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,""",
    """    @PatchMapping("/projects/{id}/storage-rate")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,""",
    "LandController /storage-rate (+DIRECTOR)")

patch_file(path,
    """    @PatchMapping("/projects/{id}/storage-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,""",
    """    @PatchMapping("/projects/{id}/storage-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,""",
    "LandController /storage-fees (+DIRECTOR)")

patch_file(path,
    """    @PatchMapping("/projects/{id}/negotiation-deadline")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> setNegotiationDeadline(@PathVariable UUID id,""",
    """    @PatchMapping("/projects/{id}/negotiation-deadline")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setNegotiationDeadline(@PathVariable UUID id,""",
    "LandController /negotiation-deadline (+DIRECTOR)")

patch_file(path,
    """    @PatchMapping("/projects/{id}/backlog-start")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> setBacklogStartOverride(@PathVariable UUID id,""",
    """    @PatchMapping("/projects/{id}/backlog-start")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setBacklogStartOverride(@PathVariable UUID id,""",
    "LandController /backlog-start (+DIRECTOR)")

# ---- PaymentController.java ----
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PaymentController.java"

patch_file(path,
    """@RestController
@RequestMapping("/api/v1/recovery/payments")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN')")
public class PaymentController {""",
    """@RestController
@RequestMapping("/api/v1/recovery/payments")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class PaymentController {""",
    "PaymentController class gate (+DIRECTOR)")

# ---- RecoveryController.java ----
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java"

patch_file(path,
    """@RestController
@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class RecoveryController {""",
    """@RestController
@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class RecoveryController {""",
    "RecoveryController class gate (+DIRECTOR)")

# ---- ClientController.java ----
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java"

patch_file(path,
    """@RestController
@RequestMapping("/api/v1/clients")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class ClientController {""",
    """@RestController
@RequestMapping("/api/v1/clients")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class ClientController {""",
    "ClientController class gate (+DIRECTOR)")

# ---- ReportController.java ----
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/ReportController.java"

patch_file(path,
    """    /** Pillar 1: Master Debt Ledger */
    @GetMapping("/debt-ledger")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadDebtLedger() {""",
    """    /** Pillar 1: Master Debt Ledger */
    @GetMapping("/debt-ledger")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadDebtLedger() {""",
    "ReportController /debt-ledger (+DIRECTOR)")

patch_file(path,
    """    /** Pillar 3: Recovery Throughput */
    @GetMapping("/performance")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadPerformanceReport() {""",
    """    /** Pillar 3: Recovery Throughput */
    @GetMapping("/performance")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadPerformanceReport() {""",
    "ReportController /performance (+DIRECTOR)")

patch_file(path,
    """    /** Pillar 5: Legal Readiness */
    @GetMapping("/legal-readiness")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadLegalAudit() {""",
    """    /** Pillar 5: Legal Readiness */
    @GetMapping("/legal-readiness")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadLegalAudit() {""",
    "ReportController /legal-readiness (+DIRECTOR)")

patch_file(path,
    """    /** Pillar 7: Master Audit Log */
    @GetMapping("/audit-trail")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadAuditTrail() {""",
    """    /** Pillar 7: Master Audit Log */
    @GetMapping("/audit-trail")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadAuditTrail() {""",
    "ReportController /audit-trail (+DIRECTOR)")

patch_file(path,
    """    /** Pillar 8: Revenue History */
    @GetMapping("/revenue")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadRevenueHistory() {""",
    """    /** Pillar 8: Revenue History */
    @GetMapping("/revenue")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadRevenueHistory() {""",
    "ReportController /revenue (+DIRECTOR)")

patch_file(path,
    """    /** Pillar 2: Physical Archive Map */
    @GetMapping("/archive-map")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER')")
    public ResponseEntity<byte[]> downloadArchiveMap() {""",
    """    /** Pillar 2: Physical Archive Map */
    @GetMapping("/archive-map")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadArchiveMap() {""",
    "ReportController /archive-map (+DIRECTOR)")

patch_file(path,
    """    /** Pillar 4: Survey Stage Bottlenecks */
    @GetMapping("/bottlenecks")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER')")
    public ResponseEntity<byte[]> downloadStageAudit() {""",
    """    /** Pillar 4: Survey Stage Bottlenecks */
    @GetMapping("/bottlenecks")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadStageAudit() {""",
    "ReportController /bottlenecks (+DIRECTOR)")

patch_file(path,
    """    /** Pillar 6: Reliability Scorecard */
    @GetMapping("/reliability")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER')")
    public ResponseEntity<byte[]> downloadReliabilityRankings() {""",
    """    /** Pillar 6: Reliability Scorecard */
    @GetMapping("/reliability")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadReliabilityRankings() {""",
    "ReportController /reliability (+DIRECTOR)")

patch_file(path,
    """    /** P2-1: Backlog Breakdown */
    @GetMapping("/backlog-breakdown")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadBacklogBreakdown() {""",
    """    /** P2-1: Backlog Breakdown */
    @GetMapping("/backlog-breakdown")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadBacklogBreakdown() {""",
    "ReportController /backlog-breakdown (+DIRECTOR)")

patch_file(path,
    """    /** P2-2: Completed Titles */
    @GetMapping("/completed-titles")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadCompletedTitles() {""",
    """    /** P2-2: Completed Titles */
    @GetMapping("/completed-titles")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadCompletedTitles() {""",
    "ReportController /completed-titles (+DIRECTOR)")

patch_file(path,
    """    /** P2-3: Operator Cash Reconciliation (Anti-Theft) */
    @GetMapping("/payment-history")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadPaymentHistory() {""",
    """    /** P2-3: Operator Cash Reconciliation (Anti-Theft) */
    @GetMapping("/payment-history")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadPaymentHistory() {""",
    "ReportController /payment-history (+DIRECTOR)")

patch_file(path,
    """    /** P2-4: Monthly Collection */
    @GetMapping("/monthly-collection")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadMonthlyCollection() {""",
    """    /** P2-4: Monthly Collection */
    @GetMapping("/monthly-collection")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<byte[]> downloadMonthlyCollection() {""",
    "ReportController /monthly-collection (+DIRECTOR)")

# ============================================================
# BACKEND SERVICE LAYER -- must match controller layer exactly,
# since @EnableMethodSecurity checks both. A mismatch here would
# cause Director to pass the controller gate then get a 403 from
# the service method underneath.
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {""",
    "LandService.recordPayment (+DIRECTOR)")

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void moveToBacklog(UUID projectId) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void moveToBacklog(UUID projectId) {""",
    "LandService.moveToBacklog (+DIRECTOR)")

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void exitBacklog(UUID projectId, boolean capitalizeFees) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void exitBacklog(UUID projectId, boolean capitalizeFees) {""",
    "LandService.exitBacklog (+DIRECTOR)")

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setStoragePaused(UUID projectId, boolean paused) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setStoragePaused(UUID projectId, boolean paused) {""",
    "LandService.setStoragePaused (+DIRECTOR)")

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setStorageFeeOverride(UUID projectId, java.math.BigDecimal rate) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setStorageFeeOverride(UUID projectId, java.math.BigDecimal rate) {""",
    "LandService.setStorageFeeOverride (+DIRECTOR)")

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setAccumulatedFees(UUID projectId, java.math.BigDecimal amount) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setAccumulatedFees(UUID projectId, java.math.BigDecimal amount) {""",
    "LandService.setAccumulatedFees (+DIRECTOR)")

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setNegotiationDeadline(UUID projectId, String deadlineStr) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setNegotiationDeadline(UUID projectId, String deadlineStr) {""",
    "LandService.setNegotiationDeadline (+DIRECTOR)")

patch_file(path,
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setBacklogStartOverride(UUID projectId, String startDateStr) {""",
    """    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setBacklogStartOverride(UUID projectId, String startDateStr) {""",
    "LandService.setBacklogStartOverride (+DIRECTOR)")

# ============================================================
# FRONTEND
# ============================================================

# ---- App.jsx ----
path = "erp-frontend/src/App.jsx"

patch_file(path,
    """    if (adminOnly && !(user.isRoot || user.role === 'ROLE_ADMIN')) return <Navigate to="/dashboard" replace />;""",
    """    if (adminOnly && !(user.isRoot || user.role === 'ROLE_ADMIN' || user.role === 'ROLE_DIRECTOR')) return <Navigate to="/dashboard" replace />;""",
    "App.jsx adminOnly gate (+DIRECTOR)")

# ---- Sidebar.jsx ----
path = "erp-frontend/src/components/layout/Sidebar.jsx"

patch_file(path,
    """    const hasHighLevelAccess = user?.isRoot || user?.role === 'ROLE_ADMIN';""",
    """    const hasHighLevelAccess = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';""",
    "Sidebar.jsx hasHighLevelAccess (+DIRECTOR)")

# ---- Dashboard.jsx ----
path = "erp-frontend/src/pages/Dashboard/Dashboard.jsx"

patch_file(path,
    """            {user?.isRoot
                ? <RootTerminal stats={stats} />
                : <ManagerTerminal stats={stats} />
            }""",
    """            {(user?.isRoot || user?.role === 'ROLE_DIRECTOR')
                ? <RootTerminal stats={stats} />
                : <ManagerTerminal stats={stats} />
            }""",
    "Dashboard.jsx terminal picker (+DIRECTOR sees RootTerminal)")

patch_file(path,
    """                    <p className={styles.pageSubtitle}>
                        {user?.isRoot ? 'ROOT OWNER ACCESS' : 'MANAGER ACCESS'}
                        {' · '}SYSTEM ACTIVE
                    </p>""",
    """                    <p className={styles.pageSubtitle}>
                        {user?.isRoot ? 'ROOT OWNER ACCESS' : user?.role === 'ROLE_DIRECTOR' ? 'DIRECTOR ACCESS' : 'MANAGER ACCESS'}
                        {' · '}SYSTEM ACTIVE
                    </p>""",
    "Dashboard.jsx subtitle label (+DIRECTOR)")

# ---- FolderPage.jsx ----
path = "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"

patch_file(path,
    """    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;""",
    """    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR' || user?.isRoot;""",
    "FolderPage.jsx isAdmin (+DIRECTOR)")

# ---- ReportHub.jsx ----
path = "erp-frontend/src/pages/Reports/ReportHub.jsx"

patch_file(path,
    """    const hasFinancialAccess = user?.isRoot || user?.role === 'ROLE_ADMIN';""",
    """    const hasFinancialAccess = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';""",
    "ReportHub.jsx hasFinancialAccess (+DIRECTOR)")

print("-" * 60)
print("DONE. Check for FAIL / MISSING messages above.")
print("")
print("If everything shows OK, run:")
print("git add -A && git commit -m 'feat: Phase 3B - wire ROLE_DIRECTOR into permissions' && git push")
print("")
print("REMINDER:")
print("  - ROLE_SECRETARY is intentionally still not wired anywhere. It")
print("    gets wired in correctly during Phase 4 once stage/cost endpoints")
print("    are separated.")
print("  - SettingsPage.jsx (the staff dropdown UI) was NOT touched -- I")
print("    don't have its current content. Please send it so I can add a")
print("    'Director' option to the role picker as Phase 3C (small, quick).")
print("    Until then, ROLE_DIRECTOR can only be assigned via a direct API")
print("    call (Postman), not through the app UI.")