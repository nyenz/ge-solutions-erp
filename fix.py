#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix166: FOLDER PAGE LOOPHOLES. Apply AFTER fix165.
#
# MONEY / RECEIVABLES
#  1. MOVE TO RECEIVABLES was open to managers (the page showed it to them, the other receivable buttons are director-only),
#     had NO checks and NO reason. Calling it twice restarted the billing clock; calling it on a handed-over or fully paid
#     project overwrote its status. Now: director only, reason (5+), refused if deleted / already receivable / handed over /
#     nothing owed.
#  2. Receivable EXIT (set aside / add fees to cost / waive): works only on a project that IS in receivables, only the 3
#     known actions (an unknown word used to fall through to SET ASIDE), and ALL THREE need a reason. ADD FEES TO COST
#     changes the total cost -- the audit line now shows old -> new cost.
#  3. REDUCE FEES / rate / pause: only on a receivable project. A pause must end in the future and within 365 days (a pause
#     to the year 2999 switched billing off for ever). A bad rate or date is a clear 400, not a server crash.
#
# RECORD LOCKS
#  4. A HANDED-OVER TITLE IS NOW LOCKED. Before, a manager could still change the plot number, tenure, owners and total
#     cost of a released title, delete its documents, and un-tick its stages. Server refuses all of it (a director must
#     UNDO the hand-over, with a reason). A deleted project is locked the same way.
#  5. The server now refuses a blank district / plot / tenure and removing every owner (only the page checked before).
#  6. Changes to plot / title ID / tenure / block and to the OWNERS are audited OLD -> NEW (before: just "modified Binder").
#  7. Stage endpoints ignored the project in the web address: any stage id could be ticked / removed through any project.
#     Now the stage must belong to that project and the project must be open.
#
# WORKFLOW
#  8. THE PAGE SAVED BY ITSELF after 5 idle minutes (half-typed cost, owner, plot number and all). Removed; it only warns.
#  9. HAND OVER is refused while the plot is flagged PROBLEM (page + server), when deleted, and when already handed over.
# 10. CLEARING a PROBLEM flag needs a reason (5+). Anyone could wipe a flag a director raised with one click.
# 11. DELETE needs a reason, refuses an already-deleted project, and no longer says "PERMANENTLY erase" (it is a soft
#     delete: root can restore it from Settings > Archive).
# 12. reality-override (stage number) was open to every manager with no limits (negative, 999) and could overwrite the
#     status of a receivable / handed-over project. Now director/admin only, 1..5 only, refused on locked projects.
# 13. Stage tick could double-fire on a double click (flipped back). RESTORE DEFAULTS deleted every stage BEFORE adding the
#     new ones, so one failure left the project with NO stages; it now adds first, removes after.
# 14. RECORD PAYMENT button disabled when nothing is owed; EDIT disabled after hand-over; ?action=storage only means a
#     storage payment on a receivable project.
# 15. LLM_CONTEXT_GUIDE.md records all of this.
#
# NOT in this fix: call logs with promise dates, who-flagged-it display, per-plot history tab, a reason on hand-over,
# an editable global storage-fee default (needs a settings table), server-side "edit conflict" for fields other than cost.
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix166"
COMMIT_MSG = "fix166: folder page loopholes closed (no idle auto-save, handed-over title locked, receivables director-only + reasons, problem clear + delete need reasons, stage guards, audit old->new)"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
LAND_SVC_JS = os.path.join(SRC, "services", "landService.js")
PORTAL_SVC_JS = os.path.join(SRC, "services", "folderPortalService.js")
LAND_SERVICE = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
LAND_CTRL = os.path.join(JAVA, "modules", "land", "controller", "LandController.java")
PORTAL_CTRL = os.path.join(JAVA, "modules", "land", "controller", "FolderPortalController.java")
STAGE_SVC = os.path.join(JAVA, "modules", "land", "service", "StageTemplateService.java")
STAGE_CTRL = os.path.join(JAVA, "modules", "land", "controller", "StageTemplateController.java")
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
# ============================= EDIT PART 1 END =============================


# ================== DO NOT EDIT: helpers (copy exactly) ====================
MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# sub = exact find/replace of the FIRST match. Prints OK / SKIP / MISSING.
def sub(text, old, new, desc):
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


# newfile = create (or replace) a whole file. SKIP if it already holds `marker`.
def newfile(path, text, label, marker):
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)



# ============================ EDIT PART 2 START ============================
LOAD_FILES = (FOLDER_JSX, LAND_SVC_JS, PORTAL_SVC_JS, LAND_SERVICE, LAND_CTRL, PORTAL_CTRL, STAGE_SVC, STAGE_CTRL, GUIDE)
for _p in LOAD_FILES:
    load(_p)

patch(LAND_SERVICE,
r"""        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: Arrears Detected.");
        }""",
r"""        LandProject project = projectRepository.findById(id).orElseThrow();
        // fix166: no hand-over of a deleted project, no second hand-over, and none while the plot is flagged as a PROBLEM.
        if (project.isDeleted()) {
            throw new BusinessException("RELEASE DENIED: This project is deleted. Restore it first.");
        }
        if (project.getLandTitle() != null && project.getLandTitle().isReleased()) {
            throw new BusinessException("RELEASE DENIED: This title has already been handed over.");
        }
        if (project.isProblem()) {
            throw new BusinessException("RELEASE DENIED: This plot is flagged as a PROBLEM. Clear the flag (with a reason) before handing over the title.");
        }
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: Arrears Detected.");
        }""",
'fix166: hand-over refused when deleted / already handed over / PROBLEM flag up')

patch(LAND_SERVICE,
r"""    @Transactional(rollbackFor = Exception.class)
    public LandProject updateProjectFull(UUID projectId, LandEntryRequest request) {""",
r"""    // fix166: one-line descriptions of the title and the owners, used to write OLD -> NEW into the audit log.
    private String fix166TitleLine(LandTitle t) {
        if (t == null) return "no title";
        return "plot " + t.getPlotNumber() + ", title ID " + t.getTitleId() + ", tenure " + t.getTenure() + ", block " + t.getBlockRoad();
    }

    private String fix166OwnersLine(LandProject p) {
        if (p.getProprietors() == null || p.getProprietors().isEmpty()) return "none";
        return p.getProprietors().stream()
                .map(c -> c.getFullName() + " (NIN " + c.getNationalId() + ")")
                .sorted()
                .collect(java.util.stream.Collectors.joining("; "));
    }

    @Transactional(rollbackFor = Exception.class)
    public LandProject updateProjectFull(UUID projectId, LandEntryRequest request) {""",
'fix166: audit helper lines for title + owners')

patch(LAND_SERVICE,
r"""        LandTitle title = project.getLandTitle();

        // PHASE E (Section 18.9.4): Create LandTitle on edit if title fields""",
r"""        LandTitle title = project.getLandTitle();

        // fix166 EDIT GUARDS (the page checks these too, but the server must not trust the page):
        // a deleted project and a handed-over title cannot be edited; district, plot and tenure cannot be blanked;
        // a project cannot lose all its owners.
        if (project.isDeleted()) {
            throw new BusinessException("EDIT_BLOCKED: This project is deleted. Restore it first.");
        }
        if (title != null && title.isReleased()) {
            throw new BusinessException("EDIT_LOCKED: The title has been handed over, so this record is locked. A director must UNDO the hand-over (with a reason) before anything can be changed.");
        }
        if (request.getDistrict() == null || request.getDistrict().isBlank()) {
            throw new BusinessException("DISTRICT_REQUIRED: The district cannot be empty.");
        }
        if (title != null && (request.getPlotNumber() == null || request.getPlotNumber().isBlank())) {
            throw new BusinessException("PLOT_REQUIRED: A titled project must keep its plot number.");
        }
        if (title != null && (request.getTenure() == null || request.getTenure().isBlank())) {
            throw new BusinessException("TENURE_REQUIRED: A titled project must keep its tenure.");
        }
        if (request.getOwners() != null && request.getOwners().isEmpty()
                && project.getProprietors() != null && !project.getProprietors().isEmpty()) {
            throw new BusinessException("OWNER_REQUIRED: A project must keep at least one owner.");
        }
        final String fix166OldTitle = fix166TitleLine(title);
        final String fix166OldOwners = fix166OwnersLine(project);

        // PHASE E (Section 18.9.4): Create LandTitle on edit if title fields""",
'fix166: server-side edit guards (deleted / handed over / blanks / no owners)')

patch(LAND_SERVICE,
r"""        LandProject saved = projectRepository.save(project);
        auditService.logAction("RECORD_UPDATED",
            "Operator [" + getCurrentOperator() + "] modified Binder: "
            + plotLabel(project));
        return saved;""",
r"""        LandProject saved = projectRepository.save(project);
        auditService.logAction("RECORD_UPDATED",
            "Operator [" + getCurrentOperator() + "] modified Binder: "
            + plotLabel(project));
        // fix166: a change of plot / title ID / tenure / block, or of the owners, is written with OLD -> NEW.
        String fix166NewTitle = fix166TitleLine(project.getLandTitle());
        if (!fix166OldTitle.equals(fix166NewTitle)) {
            auditService.logAction("TITLE_FIELDS_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed the title details of project #" + project.getProjectIndex()
                + ". Old: " + fix166OldTitle + " -> New: " + fix166NewTitle);
        }
        String fix166NewOwners = fix166OwnersLine(project);
        if (!fix166OldOwners.equals(fix166NewOwners)) {
            auditService.logAction("OWNERS_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed the owners of project #" + project.getProjectIndex()
                + ". Old: " + fix166OldOwners + " -> New: " + fix166NewOwners);
        }
        return saved;""",
'fix166: audit title + owner changes as OLD -> NEW')

patch(LAND_SERVICE,
r"""        fileStorageService.deleteFile(doc.getFilePath());
        documentRepository.delete(doc);
        auditService.logAction("DOCUMENT_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted file: " + doc.getFileName());""",
r"""        // fix166: documents of a deleted project or of a handed-over title are locked, and the audit line says whose folder.
        LandProject docProject = doc.getProjectId() == null ? null : projectRepository.findById(doc.getProjectId()).orElse(null);
        if (docProject != null && docProject.isDeleted()) {
            throw new BusinessException("DOCUMENT_LOCKED: This project is deleted. Restore it first.");
        }
        if (docProject != null && docProject.getLandTitle() != null && docProject.getLandTitle().isReleased()) {
            throw new BusinessException("DOCUMENT_LOCKED: The title has been handed over, so its documents cannot be deleted. A director must UNDO the hand-over first.");
        }
        fileStorageService.deleteFile(doc.getFilePath());
        documentRepository.delete(doc);
        auditService.logAction("DOCUMENT_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted file: " + doc.getFileName()
            + (doc.getCategory() != null ? " (" + doc.getCategory() + ")" : "")
            + (docProject != null ? " from " + plotLabel(docProject) : ""));""",
'fix166: document delete locked on deleted / handed-over projects, audit names the plot')

patch(LAND_SERVICE,
r"""    @Transactional
    public void manualRealityOverride(UUID id, int targetStage) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        int oldStage = project.getCurrentStageIndex();""",
r"""    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void manualRealityOverride(UUID id, int targetStage) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        // fix166: any manager could push ANY number in (negative, 999) and overwrite the status of a
        // receivable / handed-over / deleted project. Now director-only, 1..5 only, and those projects are refused.
        if (targetStage < 1 || targetStage > 5) {
            throw new BusinessException("STAGE_INVALID: The stage must be a number from 1 to 5.");
        }
        if (project.isDeleted() || project.isReceivable()
                || (project.getLandTitle() != null && project.getLandTitle().isReleased())) {
            throw new BusinessException("STAGE_LOCKED: The stage of a deleted, receivable or handed-over project cannot be changed.");
        }
        int oldStage = project.getCurrentStageIndex();""",
'fix166: reality-override director-only, bounded, refused on locked projects')

patch(LAND_SERVICE,
r"""        if (project.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot is already in receivable.");
        }""",
r"""        if (project.isDeleted()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is deleted. Restore it first.");
        }
        if (project.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot is already in receivable.");
        }""",
'fix166: moveToReceivable refuses a deleted project')

patch(LAND_SERVICE,
r"""    public void nuclearDelete(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = plotLabel(project);""",
r"""    public void nuclearDelete(UUID id, String reason) {
        // fix166: deleting a project needs a written reason, and an already-deleted project cannot be "deleted" again.
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why this project is being deleted (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.isDeleted()) {
            throw new BusinessException("ALREADY_DELETED: This project is already deleted.");
        }
        String plotNo = plotLabel(project);""",
'fix166: delete needs a reason, no double delete')

patch(LAND_SERVICE,
r""""Root user [" + getCurrentOperator() + "] deleted plot: " + plotNo);""",
r""""Root user [" + getCurrentOperator() + "] deleted plot: " + plotNo + ". Reason: " + why);""",
'fix166: delete reason goes into the audit line')

patch(LAND_CTRL,
r"""    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id) {
        landService.nuclearDelete(id);""",
r"""    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id, @RequestParam String reason) {
        landService.nuclearDelete(id, reason);""",
'fix166: DELETE /land/projects/{id} takes a reason')

patch(PORTAL_CTRL,
r"""    @PostMapping("/receivable/enter")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> enter(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setReceivable(true);""",
r"""    @PostMapping("/receivable/enter")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> enter(@PathVariable UUID id, @RequestBody(required = false) Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        // fix166: starting storage fees is a money action -> director only (like every other receivable control), with a
        // written reason. Before: a manager could call it, it had no checks, and calling it AGAIN on a project already in
        // receivables restarted the billing clock; calling it on a handed-over or fully paid project overwrote its status.
        String enterWhy = (body != null && body.get("reason") != null) ? body.get("reason").trim() : "";
        if (enterWhy.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why this project is moving to receivables (at least 5 characters).");
        }
        if (p.isDeleted()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is deleted. Restore it first.");
        }
        if (p.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is already in receivables.");
        }
        if (p.getLandTitle() != null && p.getLandTitle().isReleased()) {
            throw new BusinessException("RECEIVABLE_FAULT: The title has been handed over. Undo the hand-over first.");
        }
        BigDecimal enterOwed = (p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO)
                .add(p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO)
                .subtract(p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        if (enterOwed.signum() <= 0) {
            throw new BusinessException("RECEIVABLE_FAULT: Nothing is owed on this project, so it cannot go to receivables.");
        }
        p.setReceivable(true);""",
'fix166: enter receivables = director only, reason, not twice / deleted / handed over / nothing owed')

patch(PORTAL_CTRL,
r"""auditService.logAction("RECEIVABLE_ENTER", "Operator [" + op() + "] moved project #" + p.getProjectIndex() + " into receivables.");""",
r"""auditService.logAction("RECEIVABLE_ENTER", "Operator [" + op() + "] moved project #" + p.getProjectIndex() + " into receivables. Debt frozen at UGX " + owed.max(BigDecimal.ZERO).toPlainString() + ". Reason: " + enterWhy);""",
'fix166: receivable-enter audit line carries the debt and the reason')

patch(PORTAL_CTRL,
r"""        String reason = body.get("reason") != null ? body.get("reason").trim() : "";
        if ("WAIVE".equals(action)) {""",
r"""        String reason = body.get("reason") != null ? body.get("reason").trim() : "";
        // fix166: only the three known actions (an unknown word used to fall through to SET_ASIDE), only on a project that
        // IS in receivables (before, WAIVE / ADD-TO-COST on a normal project zeroed or moved retained fees and forced its
        // status to ACTIVE), and every one of them needs a written reason (ADD FEES TO COST changes the total cost).
        if (!"WAIVE".equals(action) && !"CAPITALIZE".equals(action) && !"SET_ASIDE".equals(action)) {
            throw new BusinessException("ACTION_INVALID: Unknown receivable action.");
        }
        if (!p.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is not in receivables.");
        }
        if (reason.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why (at least 5 characters).");
        }
        if ("WAIVE".equals(action)) {""",
'fix166: receivable exit = known action, must be receivable, reason for all three')

patch(PORTAL_CTRL,
r"""            p.setTotalCost((p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO).add(fees));
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
            auditService.logAction("FEES_CAPITALIZED", "Operator [" + op() + "] capitalized UGX " + fees + " into total cost on #" + p.getProjectIndex() + ".");""",
r"""            BigDecimal costBefore = p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO;
            p.setTotalCost(costBefore.add(fees));
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
            auditService.logAction("FEES_CAPITALIZED", "Operator [" + op() + "] capitalized UGX " + fees + " into total cost on #" + p.getProjectIndex()
                    + " (total cost UGX " + costBefore.toPlainString() + " -> UGX " + costBefore.add(fees).toPlainString() + "). Reason: " + reason);""",
'fix166: capitalize audit = old -> new cost + reason')

patch(PORTAL_CTRL,
r"""auditService.logAction("RECEIVABLE_SET_ASIDE", "Operator [" + op() + "] set aside #" + p.getProjectIndex() + " (fees UGX " + fees + " retained, billing stopped).");""",
r"""auditService.logAction("RECEIVABLE_SET_ASIDE", "Operator [" + op() + "] set aside #" + p.getProjectIndex() + " (fees UGX " + fees + " retained, billing stopped). Reason: " + reason);""",
'fix166: set-aside audit carries the reason')

patch(PORTAL_CTRL,
r"""            throw new BusinessException("REASON_REQUIRED: Write why the fees are being reduced (at least 5 characters).");
        }""",
r"""            throw new BusinessException("REASON_REQUIRED: Write why the fees are being reduced (at least 5 characters).");
        }
        if (!p.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is not in receivables.");
        }""",
'fix166: reduce-fees only on a receivable project')

patch(PORTAL_CTRL,
r"""            newRate = body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate"));""",
r"""            try {
                newRate = body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate").trim());
            } catch (NumberFormatException e) {
                throw new BusinessException("RATE_INVALID: Enter the monthly storage rate as a plain number.");
            }""",
'fix166: a bad rate is a clear 400, not a crash')

patch(PORTAL_CTRL,
r"""            newDeadline = body.get("deadline") == null || body.get("deadline").isBlank() ? null : LocalDateTime.parse(body.get("deadline"));""",
r"""            try {
                newDeadline = body.get("deadline") == null || body.get("deadline").isBlank() ? null : LocalDateTime.parse(body.get("deadline").trim());
            } catch (java.time.format.DateTimeParseException e) {
                throw new BusinessException("PAUSE_INVALID: The pause date is not a valid date and time.");
            }""",
'fix166: a bad pause date is a clear 400, not a crash')

patch(PORTAL_CTRL,
r"""        boolean pauseSet = newDeadline != null && !newDeadline.equals(oldDeadline);""",
r"""        boolean pauseSet = newDeadline != null && !newDeadline.equals(oldDeadline);
        // fix166: a pause must end in the future and not more than a year away (a pause to the year 2999 switched billing
        // off for ever), and rate / pause only make sense on a project that is in receivables.
        if (pauseSet && !newDeadline.isAfter(LocalDateTime.now())) {
            throw new BusinessException("PAUSE_INVALID: The pause must end in the future.");
        }
        if (pauseSet && newDeadline.isAfter(LocalDateTime.now().plusDays(365))) {
            throw new BusinessException("PAUSE_INVALID: A pause cannot be longer than 365 days. Pause again later if more time is needed.");
        }
        if ((rateChanged || pauseSet) && !p.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is not in receivables.");
        }""",
'fix166: pause window + rate only on receivable projects')

patch(PORTAL_CTRL,
r"""        if (!p.isProblem() && (note == null || note.trim().length() < 5)) {
            throw new BusinessException("REASON_REQUIRED: Write what the problem is (at least 5 characters).");
        }""",
r"""        // fix166: CLEARING a flag needs words too (anyone could silently wipe a flag a director raised), and a deleted project is not touched.
        if (p.isDeleted()) {
            throw new BusinessException("PLOT_DELETED: This project is deleted. Restore it first.");
        }
        if (note == null || note.trim().length() < 5) {
            throw new BusinessException(p.isProblem()
                    ? "REASON_REQUIRED: Write why the problem flag is being cleared (at least 5 characters)."
                    : "REASON_REQUIRED: Write what the problem is (at least 5 characters).");
        }""",
'fix166: clearing a PROBLEM flag needs a reason')

patch(STAGE_SVC,
r"""    private final AuditService auditService;""",
r"""    private final AuditService auditService;
    private final com.gesolutions.erp.modules.land.repository.LandProjectRepository projectRepository;

    // fix166: the stage endpoints used to ignore the project in the web address: any stage id could be ticked or removed
    // through ANY project, including a deleted project or a title that was already handed over. Now the stage must
    // belong to that project and the project must be open.
    public void requireStageEditable(UUID projectId, UUID stageId) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        if (stage.getProjectId() == null || !stage.getProjectId().equals(projectId)) {
            throw new BusinessException("STAGE_MISMATCH: That stage does not belong to this project.");
        }
        com.gesolutions.erp.modules.land.model.LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (project.isDeleted()) {
            throw new BusinessException("STAGE_LOCKED: This project is deleted. Restore it first.");
        }
        if (project.getLandTitle() != null && project.getLandTitle().isReleased()) {
            throw new BusinessException("STAGE_LOCKED: The title has been handed over, so its stages are locked. A director must UNDO the hand-over first.");
        }
    }""",
'fix166: stage guard (belongs to this project, project open)')

patch(STAGE_CTRL,
r"""        return ResponseEntity.ok(stageTemplateService.toggleStageCompletion(stageId, completed));""",
r"""        stageTemplateService.requireStageEditable(projectId, stageId);
        return ResponseEntity.ok(stageTemplateService.toggleStageCompletion(stageId, completed));""",
'fix166: tick/untick guarded')

patch(STAGE_CTRL,
r"""        return ResponseEntity.ok(stageTemplateService.updateStageCostAndNotes(stageId, cost, notes));""",
r"""        stageTemplateService.requireStageEditable(projectId, stageId);
        return ResponseEntity.ok(stageTemplateService.updateStageCostAndNotes(stageId, cost, notes));""",
'fix166: stage cost edit guarded')

patch(STAGE_CTRL,
r"""        stageTemplateService.removeProjectStage(stageId);""",
r"""        stageTemplateService.requireStageEditable(projectId, stageId);
        stageTemplateService.removeProjectStage(stageId);""",
'fix166: stage remove guarded')

patch(LAND_SVC_JS,
r"""    purgeAsset: async (projectId) => {
        await api.delete(`/land/projects/${projectId}`);
    },""",
r"""    // fix166: deleting a project needs a written reason (5+ characters)
    purgeAsset: async (projectId, reason) => {
        await api.delete(`/land/projects/${projectId}`, { params: { reason } });
    },""",
'fix166: purgeAsset sends the reason')

patch(PORTAL_SVC_JS,
r"""  enter:    (id) => api.post(`/land/portal/${id}/receivable/enter`).then(r => r.data),""",
r"""  enter:    (id, reason) => api.post(`/land/portal/${id}/receivable/enter`, { reason }).then(r => r.data),""",
'fix166: enter receivables sends the reason')

patch(FOLDER_JSX,
r"""            if (Date.now() - lastActiveRef.current > 5 * 60 * 1000) {
                lastActiveRef.current = Date.now();
                handleCommit();
            }""",
r"""            // fix166: the page used to SAVE EVERYTHING BY ITSELF after 5 minutes of silence, whatever half-finished
            // thing was typed (a cost, an owner, a plot number). Nothing is saved without a click now; it only reminds.
            if (Date.now() - lastActiveRef.current > 10 * 60 * 1000) {
                lastActiveRef.current = Date.now();
                toast('You have unsaved edits open. Nothing is saved automatically - press SAVE, or CANCEL to throw them away.', 'warn', 15000);
            }""",
'fix166: idle timer no longer auto-saves, it only warns')

patch(FOLDER_JSX,
r"""setTimeout(() => { setPayType('STORAGE'); setPayAmount('');""",
r"""setTimeout(() => { setPayType(binder.project?.isReceivable ? 'STORAGE' : 'TITLE'); setPayAmount('');""",
'fix166: ?action=storage only means storage when the project is in receivables')

patch(FOLDER_JSX,
r"""    const [saving, setSaving] = useState(false);
    const autoTicked = useRef(false);""",
r"""    const [saving, setSaving] = useState(false);
    const [toggling, setToggling] = useState(false);
    const autoTicked = useRef(false);""",
'fix166: stage tick busy flag')

patch(FOLDER_JSX,
r"""    const handleToggleComplete = async (stage, isLast) => {
        const next = !stage.isCompleted;
        try {
            await stageTemplateService.toggleStageCompletion(projectId, stage.id, next);
            await loadStages();
            // Ticking the final stage means the title is now ready -- hand
            // off to the title panel. Unticking it (a correction) hands
            // back to the stage checklist. See onLastStageToggle in the
            // parent for what this actually does.
            if (isLast && onLastStageToggle) onLastStageToggle(next);
        } catch (err) { toast && toast('Failed to update stage (HTTP ' + (err.response?.status || 'network') + ')', 'error'); }
    };""",
r"""    const handleToggleComplete = async (stage, isLast) => {
        if (toggling) return;   // fix166: a double click used to send two ticks and flip the stage back
        setToggling(true);
        const next = !stage.isCompleted;
        try {
            await stageTemplateService.toggleStageCompletion(projectId, stage.id, next);
            await loadStages();
            // Ticking the final stage means the title is now ready -- hand
            // off to the title panel. Unticking it (a correction) hands
            // back to the stage checklist. See onLastStageToggle in the
            // parent for what this actually does.
            if (isLast && onLastStageToggle) onLastStageToggle(next);
        } catch (err) { await loadStages(); toast && toast('STAGE NOT UPDATED: ' + errText(err), 'error', 12000); }
        finally { setToggling(false); }
    };""",
'fix166: stage tick cannot double-fire, error shows the server words')

patch(FOLDER_JSX,
r"""checked={!!stage.isCompleted} disabled={!canEdit}""",
r"""checked={!!stage.isCompleted} disabled={!canEdit || toggling}""",
'fix166: checkbox locked while a tick is saving')

patch(FOLDER_JSX,
r"""            const tpls = await stageTemplateService.getTemplate() || [];
            await Promise.all(stages.map(s => stageTemplateService.removeStage(projectId, s.id)));
            await stageTemplateService.attachStages(projectId, tpls.map((t, i) => ({ stageTemplateId: t.id, isCustom: false, cost: 0, isCompleted: i === 0 })));""",
r"""            const tpls = await stageTemplateService.getTemplate() || [];
            if (!tpls.length) { toast && toast('The master checklist is empty, so nothing was changed.', 'error', 9000); return; }
            // fix166: the new list is added FIRST and the old one removed AFTER, so a failure half-way can never leave
            // the project with NO stages (it used to delete every stage first and only then try to add the new ones).
            const oldIds = stages.map(s => s.id);
            await stageTemplateService.attachStages(projectId, tpls.map((t, i) => ({ stageTemplateId: t.id, isCustom: false, cost: 0, isCompleted: i === 0 })));
            for (const sid of oldIds) { await stageTemplateService.removeStage(projectId, sid); }""",
'fix166: RESTORE DEFAULTS adds before it removes')

patch(FOLDER_JSX,
r"""        } catch { await loadStages(); toast && toast('Failed to restore defaults', 'error'); } finally { setSaving(false); }""",
r"""        } catch (err) { await loadStages(); toast && toast('DEFAULTS NOT RESTORED: ' + errText(err), 'error', 12000); } finally { setSaving(false); }""",
'fix166: restore-defaults error shows the server words')

patch(FOLDER_JSX,
r"""const handleToggleProblem = () => { if (project.problem) { runToggleProblem(''); } else {""",
r"""const handleToggleProblem = () => { if (project.problem) { openReasonModal({ kind: 'CLEAR_PROBLEM', title: 'CLEAR PROBLEM FLAG', confirmLabel: 'CLEAR FLAG', info: 'This removes the PROBLEM flag from this plot. Write why it is no longer a problem; your words go into the notes and the audit log.' }); } else {""",
'fix166: clearing a PROBLEM flag opens the reason window')

patch(FOLDER_JSX,
r"""            else if (m.kind === 'REVERT_TITLE') {""",
r"""            else if (m.kind === 'ENTER') { await folderPortalService.enter(id, why); toast('Moved to receivables.', 'success'); }
            else if (m.kind === 'SET_ASIDE') { await folderPortalService.exit(id, 'SET_ASIDE', why); toast('Receivable set aside - record retained.', 'success'); }
            else if (m.kind === 'CAPITALIZE') { await folderPortalService.exit(id, 'CAPITALIZE', why); toast('Storage fees added to the total cost.', 'success'); }
            else if (m.kind === 'CLEAR_PROBLEM') {
                await folderPortalService.toggleProblem(id, why);
                try { await landService.addStandaloneNote(id, '[PROBLEM CLEARED] ' + why); } catch { toast('Flag cleared, but the note did NOT save. Add it again from the NOTES tab.', 'warn', 12000); }
                toast('Problem flag removed.', 'info');
            }
            else if (m.kind === 'DELETE') {
                await landService.purgeAsset(id, why);
                touchedRef.current = false; setIsEditing(false);
                setReasonModal(x => ({ ...x, open: false }));
                toast('Project deleted. The root user can restore it from Settings > Archive.', 'warn', 6000);
                setTimeout(() => navigate('/land/projects'), 1500);
                return;
            }
            else if (m.kind === 'REVERT_TITLE') {""",
'fix166: reason window handles ENTER / SET_ASIDE / CAPITALIZE / CLEAR_PROBLEM / DELETE')

patch(FOLDER_JSX,
r"""    const handleNuclearPurge = async () => { const ok = await confirm('DELETE', 'PERMANENTLY erase this entire archive entry. Cannot be undone.', 'danger'); if (!ok) return; try { await landService.purgeAsset(id); toast('Record permanently deleted', 'warn', 3000); setTimeout(() => navigate('/land/projects'), 1500); } catch { toast('Delete failed', 'error'); } };""",
r"""    // fix166: DELETE is a soft delete (the root user can restore it), so it no longer claims "permanent"; it needs a written reason.
    const handleNuclearPurge = () => openReasonModal({ kind: 'DELETE', title: 'DELETE THIS PROJECT', confirmLabel: 'DELETE PROJECT',
        info: 'This takes the whole project (payments, notes and documents included) out of every list. It is NOT erased: the root user can restore it from Settings > Archive. Write why it is being deleted.' });""",
'fix166: DELETE needs a reason, wording is honest')

patch(FOLDER_JSX,
r"""    const runReceivableAction = async (action) => {
        setRecvBusy(true);
        try {
            if (action === 'ENTER') await folderPortalService.enter(id);
            else if (action === 'SETTINGS') await folderPortalService.settings(id, { rate: rateFee, deadline: rateDeadline });
            else await folderPortalService.exit(id, action);
            await loadFolderData();
            toast(action === 'WAIVE' ? 'Storage fees waived.' : action === 'CAPITALIZE' ? 'Storage fees capitalized.' : action === 'SET_ASIDE' ? 'Receivable set aside — record retained.' : action === 'ENTER' ? 'Moved to receivables.' : 'Receivable settings saved.', 'success');
        } catch (err) { toast('RECEIVABLE ACTION FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setRecvBusy(false); }
    };
    const askReceivable = async (action) => {
        const msgs = {
            ENTER: ['MOVE TO RECEIVABLES', 'Freeze the balance and start monthly storage fees (default UGX 50,000). Continue?', 'warn'],
            SET_ASIDE: ['SET ASIDE', 'Take this project out of receivables and stop new fees. The fee record is KEPT (hidden) so the project can be moved back later. Continue?', 'warn'],
            CAPITALIZE: ['ADD FEES TO COST', 'Add the accumulated storage fees to the total cost and take this project out of receivables. Continue?', 'warn'],
            WAIVE: ['WAIVE FEES', 'Permanently forgive the accumulated storage fees and take this project out of receivables. This cannot be undone. Continue?', 'danger'],
            SETTINGS: ['SAVE SETTINGS', 'Update the monthly rate / freeze deadline for this project. Continue?', 'warn'],
        };
        const m = msgs[action];
        const ok = await confirm(m[0], m[1], m[2]);
        if (ok) runReceivableAction(action);
    };""",
r"""    // fix166: runReceivableAction / askReceivable are gone. Every receivable move (enter, set aside, add fees to cost,
    // waive, reduce, rate, pause) now goes through the ONE reason window and the server refuses it without a reason.""",
'fix166: remove the old reason-less receivable actions')

patch(FOLDER_JSX,
r"""{canEdit && <HardwareButton type="button" icon={FiAlertOctagon} loading={recvBusy} onClick={() => askReceivable('ENTER')}>MOVE TO RECEIVABLES</HardwareButton>}""",
r"""{canMoney && !project.landTitle?.isReleased && amountOwed > 0 && <HardwareButton type="button" icon={FiAlertOctagon} loading={recvBusy} onClick={() => openReasonModal({ kind: 'ENTER', title: 'MOVE TO RECEIVABLES', confirmLabel: 'MOVE TO RECEIVABLES',
                                    info: 'This freezes the balance (UGX ' + fmt(amountOwed) + ' owed) and starts a monthly storage fee of UGX 50,000 unless a different rate is set, added every 30 days. Write why this project is moving to receivables.' })}>MOVE TO RECEIVABLES</HardwareButton>}""",
'fix166: MOVE TO RECEIVABLES director-only, reason, hidden when handed over / nothing owed')

patch(FOLDER_JSX,
r"""<HardwareButton type="button" icon={FiArchive} loading={recvBusy} onClick={() => askReceivable('SET_ASIDE')}>SET ASIDE (KEEP FEES)</HardwareButton>""",
r"""<HardwareButton type="button" icon={FiArchive} loading={recvBusy} onClick={() => openReasonModal({ kind: 'SET_ASIDE', title: 'SET ASIDE', confirmLabel: 'SET ASIDE',
                                        info: 'This takes the project out of receivables and stops new fees. The UGX ' + fmt(storageFees) + ' of fees is KEPT (hidden) so the project can be moved back later. Write why.' })}>SET ASIDE (KEEP FEES)</HardwareButton>""",
'fix166: SET ASIDE needs a reason')

patch(FOLDER_JSX,
r"""onClick={() => askReceivable('CAPITALIZE')} disabled={recvBusy}>""",
r"""onClick={() => openReasonModal({ kind: 'CAPITALIZE', title: 'ADD FEES TO COST', confirmLabel: 'ADD FEES TO COST',
                                        info: 'This adds the UGX ' + fmt(storageFees) + ' of storage fees to the total cost (UGX ' + fmt(totalValue) + ' becomes UGX ' + fmt(totalValue + storageFees) + ') and takes the project out of receivables. Write why.' })} disabled={recvBusy}>""",
'fix166: ADD FEES TO COST needs a reason, shows the old and new cost')

patch(FOLDER_JSX,
r"""onClick={handleRelease} disabled={amountOwed > 0}""",
r"""onClick={handleRelease} disabled={amountOwed > 0 || !!project.problem}""",
'fix166: HAND OVER disabled while the plot is flagged PROBLEM')

patch(FOLDER_JSX,
r"""title={amountOwed > 0 ? 'Cannot hand over yet: UGX ' + fmt(amountOwed) + ' is still owed.' : 'Record that the client has received the title deed.'}""",
r"""title={amountOwed > 0 ? 'Cannot hand over yet: UGX ' + fmt(amountOwed) + ' is still owed.' : project.problem ? 'Cannot hand over while this plot is flagged as a PROBLEM. Clear the flag first.' : 'Record that the client has received the title deed.'}""",
'fix166: hand-over tooltip explains the PROBLEM block')

patch(FOLDER_JSX,
r"""{canEdit && <button className={styles.ctrlBtnPay} onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>""",
r"""{canEdit && <button className={styles.ctrlBtnPay} disabled={amountOwed <= 0} title={amountOwed <= 0 ? 'Nothing is owed on this project.' : 'Record a payment with its receipt.'} onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>""",
'fix166: RECORD PAYMENT disabled when nothing is owed')

patch(FOLDER_JSX,
r"""{canEdit && <button className={styles.unlockMasterBtn} onClick={handleUnlock}>""",
r"""{canEdit && <button className={styles.unlockMasterBtn} onClick={handleUnlock} disabled={!!project.landTitle?.isReleased} title={project.landTitle?.isReleased ? 'The title has been handed over, so this record is locked. A director can UNDO the hand-over first.' : 'Edit this record.'}>""",
'fix166: EDIT locked once the title is handed over')

patch(GUIDE,
r"""(7) uploads only accept PDF/JPG/PNG/WEBP, not empty, under 50 MB (page + server).""",
r"""(7) uploads only accept PDF/JPG/PNG/WEBP, not empty, under 50 MB (page + server).
- FOLDER PAGE LOOPHOLES CLOSED (fix166): (1) the page no longer AUTO-SAVES after 5 idle minutes (it only warns after 10). (2) A handed-over title is LOCKED: `updateProjectFull`, document delete, stage tick/remove/cost and the reality-override refuse it (director UNDO first); a deleted project is locked the same way. (3) Server now refuses blank district / plot / tenure and removing every owner; plot, title ID, tenure, block and owner changes are audited OLD -> NEW (`TITLE_FIELDS_CHANGED`, `OWNERS_CHANGED`). (4) HAND OVER is refused while the plot is flagged PROBLEM, when deleted, and when already handed over. (5) Clearing a PROBLEM flag needs a reason of 5+ characters (reason window `CLEAR_PROBLEM`, saved as a note + audit). (6) Receivables: MOVE TO RECEIVABLES is director-only (`FolderPortalController.enter` was open to managers, had no checks, restarted billing when called twice and overwrote the status of handed-over projects) and needs a reason; SET ASIDE and ADD FEES TO COST need a reason (capitalize audit shows old -> new cost); `exit`, `reduce-fees` and rate/pause only work on a project that IS in receivables; unknown exit actions are refused; a pause must end in the future and within 365 days; bad rate/date = clear 400. The old reason-less `runReceivableAction`/`askReceivable` are deleted. (7) DELETE needs a reason (`DELETE /land/projects/{id}?reason=`), refuses an already-deleted project, and the page no longer says "permanent" (it is a soft delete, root can restore). (8) `PATCH .../reality-override` is director/admin only, stage 1..5 only, refused on deleted / receivable / handed-over projects. (9) Stage endpoints check the stage belongs to the project in the web address (`StageTemplateService.requireStageEditable`). (10) Stage tick cannot double-fire; RESTORE DEFAULTS adds the new stages before removing the old (a failure can no longer leave zero stages). (11) RECORD PAYMENT is disabled when nothing is owed; EDIT is disabled after hand-over; `?action=storage` only means a storage payment on a receivable project.""",
'fix166: guide records the loopholes closed')

# ============================= EDIT PART 2 END =============================


# ================= DO NOT EDIT: gates, rollback, git (copy exactly) ========
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since the last fix).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True


def working_tree_dirty():
    r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return bool((r.stdout or "").strip())


# active = this script wrote something, OR files were already changed by hand (commit-only mode)
active = changed or working_tree_dirty()
if not changed and active:
    print("note: commit-only mode -- no patches defined, committing the changes already in the working tree")
if not active:
    print("note: nothing changed and the working tree is clean -- nothing to do")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file this script touched was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if active and RUN_GATES:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate ----
if active and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif active and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif active:
    print("note: RUN_GATES is False (docs-only fix) -- compile and build skipped")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

if not active:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", COMMIT_MSG)
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip())
print("")
print("DONE: " + FIX_NO + " applied.")