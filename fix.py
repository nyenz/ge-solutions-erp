# PATH: fix.py
# STAGE 2 -- ROLES MATCH REALITY (bug-fix roadmap)
# Run from project root: python fix.py   (or: py fix.py)
# Assumes Stage 1's fix.py has already been run, committed, and pushed.
#
# WHY: the Secretary role exists on paper (the Role enum) but cannot
# actually log in and do anything -- every @PreAuthorize check in the
# app still only knows about Manager/Admin/Director. Directors also
# couldn't see the Record Payment button even though Stage 1 already
# opened the backend up to them.
#
# IMPORTANT DISCOVERY WHILE BUILDING THIS STAGE: the original roadmap
# assumed Sidebar.jsx and App.jsx's route guards would need Secretary
# added explicitly. They don't -- both were already built generically
# (Dashboard/New Plot/Ledger/Recovery/Settings use `access: true` for
# ANY authenticated role, Payments/Expenses/Reports/Audit use
# `hasHighLevelAccess`/`hasManagerAccess` booleans that simply evaluate
# to false for Secretary). So Fix 3 needed ZERO frontend nav/route
# changes -- Secretary already lands in the right place today. What was
# actually missing is that the BACKEND blocks Secretary from every API
# call those pages make, including /dashboard/summary itself (which
# would 403 a Secretary the instant they log in). That's the real gap
# this stage closes.
#
# BACKEND (patches):
#   - DashboardController.java: class-level @PreAuthorize widened to
#     include ROLE_SECRETARY, so /dashboard/summary loads for them.
#     (The DTO itself already hides financial figures from non-Admin/
#     Director users via a showFinancials flag -- nothing else to do
#     there.) The /director sub-route keeps its own stricter
#     Admin/Director-only override untouched.
#   - RecoveryController.java: class-level @PreAuthorize widened to
#     include ROLE_SECRETARY -- this class is read-only queue/schedule
#     data, no money-moving actions live here, so this is safe. Actual
#     call-logging goes through LandController's /follow-up endpoint,
#     patched below.
#   - LandController.java: per-METHOD @PreAuthorize overrides (not a
#     class-level change, which would over-grant Secretary access to
#     payments/receivable/deletion/storage-fee endpoints in the same
#     class) adding ROLE_SECRETARY to: getProjectDeepDetail (Folder
#     page can't load without this), getProjectNotes, logContact,
#     addNote, getDocuments, addExtraDocuments, ingestTitle, getLedger.
#   - StageTemplateController.java: per-METHOD overrides (same reasoning
#     -- this class also holds master TEMPLATE CRUD, which Secretary
#     must never touch per the role table) adding ROLE_SECRETARY to
#     getProjectStages and toggleStageCompletion ONLY. Template CRUD
#     (addTemplateStage/updateTemplateStage/deactivateTemplateStage) and
#     attachStages/updateStageCost/removeStage are deliberately left
#     alone -- Secretary is "stage-changing only," not cost- or
#     template-editing.
#
# FRONTEND (patches):
#   - SettingsPage.jsx: 'ROLE_SECRETARY' added to the INITIAL RANK
#     dropdown when creating a new operator, and a 'TIER 4: SECRETARY'
#     label (its own color) added wherever rank badges render.
#   - RecoveryPortal.jsx: RECORD PAYMENT button gated by a new
#     canRecordPayment check (Admin/Director/Manager/root) instead of
#     isAdmin-only, matching the backend permission Stage 1 already
#     granted to Managers.
#
# DOCS:
#   - LLM_CONTEXT_GUIDE.md Section 17.10's Phase 3 entry currently
#     claims "APPLIED AND PUSHED (all three sub-parts)" -- it wasn't;
#     this bug-fix roadmap is what actually finished the wiring. The
#     status line is corrected to say so.
#
# Safe to re-run: every patch is checked before writing; if a patch
# target is not found it prints MISSING and leaves that file alone
# (most likely meaning this stage, or a later one, is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

PATCHES = [
    # ---------------------------------------------------------------
    # BACKEND: DashboardController -- widen class-level auth so
    # Secretary's very first page after login actually loads
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java",
        '''@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class DashboardController {''',
        '''@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class DashboardController {''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: RecoveryController -- read-only queue/schedule data,
    # safe to widen at class level (no money-moving endpoints here)
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java",
        '''@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class RecoveryController {''',
        '''@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class RecoveryController {''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: LandController -- per-method overrides only (class also
    # holds payment/receivable/deletion/storage-fee endpoints that must
    # stay off-limits to Secretary)
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
        '''    @GetMapping("/projects/{id}/notes")
    public ResponseEntity<List<FollowUpLog>> getProjectNotes(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectNotes(id));
    }

    @PostMapping("/projects/{id}/follow-up")
    public ResponseEntity<Void> logContact(@PathVariable UUID id, @RequestParam String content) {
        landService.logFollowUp(id, content);
        return ResponseEntity.ok().build();
    }

    @PostMapping(value = "/ingest", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LandProject> ingestTitle(
            @RequestPart("data") String jsonData,
            @RequestPart(value = "scans", required = false) MultipartFile[] scans) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        LandEntryRequest request = mapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(landService.atomicIntake(request, scans));
    }

    @GetMapping("/projects/{id}/deep")
    public ResponseEntity<ProjectDeepDetailDTO> getProjectDeepDetail(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDeepDetail(id));
    }''',
        '''    // STAGE 2 FIX: Secretary is data-entry -- needs to read/add notes
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/notes")
    public ResponseEntity<List<FollowUpLog>> getProjectNotes(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectNotes(id));
    }

    // STAGE 2 FIX: Secretary logs recovery calls (data-entry)
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/follow-up")
    public ResponseEntity<Void> logContact(@PathVariable UUID id, @RequestParam String content) {
        landService.logFollowUp(id, content);
        return ResponseEntity.ok().build();
    }

    // STAGE 2 FIX: intake is a data-entry endpoint per the role table
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/ingest", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LandProject> ingestTitle(
            @RequestPart("data") String jsonData,
            @RequestPart(value = "scans", required = false) MultipartFile[] scans) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        LandEntryRequest request = mapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(landService.atomicIntake(request, scans));
    }

    // STAGE 2 FIX: Folder page cannot load at all for Secretary without this
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/deep")
    public ResponseEntity<ProjectDeepDetailDTO> getProjectDeepDetail(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDeepDetail(id));
    }''',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
        '''    @GetMapping("/projects/{id}/documents")
    public ResponseEntity<List<ProjectDocument>> getDocuments(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDocuments(id));
    }

    @PostMapping(value = "/projects/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> addExtraDocuments(
            @PathVariable UUID id,
            @RequestParam("scans") MultipartFile[] scans) throws Exception {
        landService.addScansToProject(id, scans);
        return ResponseEntity.ok().build();
    }''',
        '''    // STAGE 2 FIX: document upload/view is a data-entry endpoint
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/documents")
    public ResponseEntity<List<ProjectDocument>> getDocuments(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDocuments(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/projects/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> addExtraDocuments(
            @PathVariable UUID id,
            @RequestParam("scans") MultipartFile[] scans) throws Exception {
        landService.addScansToProject(id, scans);
        return ResponseEntity.ok().build();
    }''',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
        '''    @PostMapping("/projects/{id}/notes")
    public ResponseEntity<Void> addNote(@PathVariable UUID id, @RequestParam String content) {
        landService.logNewNote(id, content);
        return ResponseEntity.ok().build();
    }''',
        '''    // STAGE 2 FIX: adding a standalone note is data-entry
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/notes")
    public ResponseEntity<Void> addNote(@PathVariable UUID id, @RequestParam String content) {
        landService.logNewNote(id, content);
        return ResponseEntity.ok().build();
    }''',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
        '''    @GetMapping("/ledger")
    public ResponseEntity<Page<LandProject>> getLedger(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(page, size)));
    }''',
        '''    // STAGE 2 FIX: Secretary needs to browse the Ledger to find projects
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/ledger")
    public ResponseEntity<Page<LandProject>> getLedger(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(page, size)));
    }''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: StageTemplateController -- per-method overrides ONLY.
    # This class also holds master TEMPLATE CRUD, which the class-level
    # annotation covers today -- Secretary must NEVER get that, so we
    # cannot simply widen the class-level check the way Stage 2's
    # original prompt assumed. Only stage TOGGLING gets Secretary.
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java",
        '''    @GetMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> getProjectStages(@PathVariable UUID projectId) {
        return ResponseEntity.ok(stageTemplateService.getProjectStages(projectId));
    }''',
        '''    // STAGE 2 FIX: Secretary can view a project's stage checklist
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> getProjectStages(@PathVariable UUID projectId) {
        return ResponseEntity.ok(stageTemplateService.getProjectStages(projectId));
    }''',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java",
        '''    @PatchMapping("/land/projects/{projectId}/stages/{stageId}/complete")
    public ResponseEntity<ProjectStage> toggleStageCompletion(
            @PathVariable UUID projectId, @PathVariable UUID stageId,
            @RequestParam boolean completed) {
        return ResponseEntity.ok(stageTemplateService.toggleStageCompletion(stageId, completed));
    }''',
        '''    // STAGE 2 FIX: "Changes Stages: Yes (stage only)" per the role table --
    // Secretary may toggle stage completion but NOT edit stage cost, attach
    // new stages, remove stages, or touch the master template (all below
    // stay on the class-level Manager/Admin/Director-only default).
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PatchMapping("/land/projects/{projectId}/stages/{stageId}/complete")
    public ResponseEntity<ProjectStage> toggleStageCompletion(
            @PathVariable UUID projectId, @PathVariable UUID stageId,
            @RequestParam boolean completed) {
        return ResponseEntity.ok(stageTemplateService.toggleStageCompletion(stageId, completed));
    }''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: SettingsPage -- Secretary in the new-operator dropdown
    # and its own rank label/color
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''<HardwareSelect label="INITIAL RANK" options={['ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR']} value={newOpData.role} onChange={v => setNewOpData({...newOpData, role: v})} />''',
        '''<HardwareSelect label="INITIAL RANK" options={['ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR']} value={newOpData.role} onChange={v => setNewOpData({...newOpData, role: v})} />''',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''                                                    <span className={(op.role === 'ROLE_ADMIN' || op.role === 'ROLE_DIRECTOR') ? styles.rankAdmin : styles.rankManager}>
                                                        {op.isRoot ? 'MASTER FOUNDER' : op.role === 'ROLE_DIRECTOR' ? 'TIER 2: DIRECTOR' : op.role === 'ROLE_ADMIN' ? 'TIER 2: ADMIN' : 'TIER 3: OPERATOR'}
                                                    </span>''',
        '''                                                    <span className={(op.role === 'ROLE_ADMIN' || op.role === 'ROLE_DIRECTOR') ? styles.rankAdmin : op.role === 'ROLE_SECRETARY' ? styles.rankSecretary : styles.rankManager}>
                                                        {op.isRoot ? 'MASTER FOUNDER' : op.role === 'ROLE_DIRECTOR' ? 'TIER 2: DIRECTOR' : op.role === 'ROLE_ADMIN' ? 'TIER 2: ADMIN' : op.role === 'ROLE_SECRETARY' ? 'TIER 4: SECRETARY' : 'TIER 3: OPERATOR'}
                                                    </span>''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: SettingsPage.module.css -- Secretary's own badge color
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/settings/SettingsPage.module.css",
        '''.rankManager { font-family: 'Space Mono', monospace; color: #06b6d4; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; margin-top: clamp(2px,0.3vw,3px); display: block; }''',
        '''.rankManager { font-family: 'Space Mono', monospace; color: #06b6d4; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; margin-top: clamp(2px,0.3vw,3px); display: block; }
.rankSecretary { font-family: 'Space Mono', monospace; color: #a78bfa; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; margin-top: clamp(2px,0.3vw,3px); display: block; }''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: RecoveryPortal -- Directors (and Managers) can now see
    # the Record Payment button, matching the backend permission
    # Stage 1 already granted
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
        '''    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;''',
        '''    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;
    // STAGE 2 FIX: matches the backend permission on POST /land/projects/{id}/payment
    // (ROLE_MANAGER/ROLE_ADMIN/ROLE_DIRECTOR, widened in Stage 1) -- isAdmin alone
    // was hiding this button from Directors and Managers who could already use it.
    const canRecordPayment = user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR' || user?.role === 'ROLE_MANAGER' || user?.isRoot;''',
    ),
    (
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
        '''                                                    {isAdmin && (''',
        '''                                                    {canRecordPayment && (''',
    ),

    # ---------------------------------------------------------------
    # DOCS: correct the Phase 3 status claim
    # ---------------------------------------------------------------
    (
        "LLM_CONTEXT_GUIDE.md",
        '''**PHASE 3: 4-Tier Role System**
- What: `Role` enum expanded to the 4-tier system in 17.7 (Phase 3A), every `@PreAuthorize`
  check and every frontend role check wired to the new roles (Phase 3B), Settings UI updated
  with the Director option (Phase 3C).
- Status: APPLIED AND PUSHED (all three sub-parts). Deferred testing -- see Section 3 permanent
  testing rule. Known limitation: the promote/demote arrow on operator cards still only toggles
  ROLE_ADMIN/ROLE_MANAGER -- a proper 3+ tier rank selector is a small standalone follow-up,
  not yet done.''',
        '''**PHASE 3: 4-Tier Role System**
- What: `Role` enum expanded to the 4-tier system in 17.7 (Phase 3A). Phase 3B (every
  @PreAuthorize check and every frontend role check wired to the new roles) and Phase 3C
  (Settings UI updated with the Director/Secretary options and a real rank selector) were
  NOT actually finished at the time this entry originally claimed -- they were completed by
  Stage 1 and Stage 2 of the separate bug-fix roadmap instead (see LLM_CONTEXT_ADDENDUM.md).
- Status: APPLIED AND PUSHED, via the bug-fix roadmap rather than as part of the original
  Phase 3 rollout. Deferred testing -- see Section 3 permanent testing rule.''',
    ),
]


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def main():
    applied = 0
    missing = []
    total = len(PATCHES)

    for rel_path, old, new in PATCHES:
        full_path = os.path.join(ROOT, rel_path)
        desc = rel_path
        if not os.path.exists(full_path):
            print("[STAGE 2] " + desc + " ... MISSING (file not found)")
            missing.append(desc + " (file not found)")
            continue
        content = read_file(full_path)
        if new in content:
            print("[STAGE 2] " + desc + " ... OK (already patched)")
            applied += 1
            continue
        if old not in content:
            print("[STAGE 2] " + desc + " ... MISSING (patch target not found)")
            missing.append(desc + " (patch target not found)")
            continue
        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("[STAGE 2] " + desc + " ... OK")
        applied += 1

    print("")
    print("============================================")
    print("STAGE 2 COMPLETE: " + str(applied) + " of " + str(total) + " patches applied")
    print("FIXED: Secretary role wiring (dashboard, recovery, notes, follow-up, intake,")
    print("       documents, ledger, stage toggling), Director/Manager payment button,")
    print("       Settings UI rank options + label, Phase 3 status doc correction")
    print("============================================")

    if missing:
        print("")
        print("MISSING ITEMS (need manual attention):")
        for m in missing:
            print("  - " + m)

    print("")
    print("Next steps:")
    print("1. git add -A && git commit -m 'Stage 2: Secretary role wiring, Director payment access' && git push")
    print("2. Watch Render Events tab for the green tick.")
    print("3. Test: create a brand-new Secretary user. Confirm they can log in and see")
    print("   Dashboard, New Plot, Ledger, Recovery, Settings -- and CANNOT see Payments,")
    print("   Expenses, Reports, or Audit (those tabs should not even appear).")
    print("4. Test: as that Secretary, open a project's Folder page -- confirm it loads,")
    print("   and you can add a note, log a follow-up call, upload a document, and toggle")
    print("   a stage checkbox. Confirm you CANNOT edit stage cost or the master template.")
    print("5. Test: log in as a Director. Confirm the RECORD PAYMENT button now appears")
    print("   on the Recovery portal and a payment goes through.")


if __name__ == "__main__":
    main()