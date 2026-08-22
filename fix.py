# PATH: fix_stage13.py  (STAGE 13)
# STAGE 13 -- dead-code cleanup + naming + stale comments
# Run from project root: py fix_stage13.py
#
# This addresses the 6 suggestions from the last review, in order, after
# verifying each one directly against the cloned repo (not assumed):
#
# 1. Delete CompanyExpense/CompanyExpensesPage/CompanyExpenseController --
#    CONFIRMED zero callers anywhere. Grepped the whole backend and frontend:
#    the only non-self references are two code COMMENTS in Expense.java and
#    DataInitializer.java explaining that Expense/ExpenseController replaced
#    it. App.jsx routes /financials to ExpensesPage, never CompanyExpensesPage
#    -- that page and its service file are wired to nothing. Same shape as
#    the Notification-model deletion in Stage 7. DONE, included below.
#
# 2. Delete PaymentEngineService + the payment_schedules table's model/repo --
#    CONFIRMED. PaymentScheduleRepository and the PaymentSchedule model are
#    used ONLY by PaymentEngineService, and PaymentEngineService itself has
#    zero callers anywhere else (no controller, nothing autowires it). All
#    three can go together. Note: SystemAdminController's TABLES_TO_WIPE list
#    still references the raw "payment_schedules" TABLE NAME for the nuclear
#    reset -- that's a raw-SQL truncate list, not a Java dependency on these
#    classes, and the table itself is being left in the DB (same "deprecated,
#    not deleted" policy already documented for company_expenses and
#    notifications), so that list is correctly left untouched. DONE, included.
#
# 3. Rename LocalStorageServiceImpl -> CloudinaryStorageServiceImpl --
#    CONFIRMED it's 100% Cloudinary (the class body never touches local disk
#    at all). CONFIRMED nothing references the class by name anywhere except
#    its own file (Spring wires it by the FileStorageService interface), so
#    the rename is fully self-contained. DONE, included.
#
# 4. Lock down/remove /api/v1/vault/** -- NOT INCLUDED. Investigated this one
#    closely and it changed the answer: FolderPage.jsx's getDocUrl() has a
#    real, live fallback path -- if a document's stored file_path is NOT
#    already a full http(s) URL, it builds a /vault/... URL to serve it from
#    local disk via WebConfig's resource handler. ProjectDocument.filePath's
#    own doc comment says it can hold either "the physical path on Local Disk
#    or a Cloud Bucket URL" -- there's no migrated/legacy flag in the schema
#    to tell those apart. Every NEW upload is 100% Cloudinary now (confirmed
#    via FileStorageService's single impl), but I have no way to confirm from
#    a git clone whether any OLD project_documents rows in the live database
#    still carry a pre-Cloudinary local path. If any do, deleting WebConfig
#    and the permitAll rule would 404 those old scans. This needs a DB check
#    (or a one-time migration of any remaining local paths to Cloudinary)
#    before it's safe to remove -- see the note at the end of this file for
#    exactly how to check. Flagging this rather than guessing.
#
# 5. Fix the two stale comments -- CONFIRMED both are wrong:
#    - Role.java's class comment says "no @PreAuthorize check anywhere
#      references them yet" / "Phase 3B -- a separate, dedicated patch" for
#      ROLE_DIRECTOR/ROLE_SECRETARY. Not true anymore: grepped every
#      @PreAuthorize in the backend, ROLE_DIRECTOR appears on 40+ of them and
#      ROLE_SECRETARY on several (LandController, StageTemplateController,
#      RecoveryController), all landed via Stage 1/Stage 2 of the bug-fix
#      roadmap. The guide's own Section 17.10 already carries a "doc
#      correction" note for this same staleness -- this brings the code
#      comment in line with it.
#    - LoginRateLimiter.java's class comment says "Blocks an IP for 15
#      minutes" but BLOCK_SECONDS = 10 * 60 with its own "// 10 minutes"
#      comment right next to it. The Javadoc just never got updated when the
#      constant was set. DONE, included below.
#
# 6. Sweep every controller's @PreAuthorize against the Section 17.7 table --
#    DONE AS A CHECK, not a code change, because I didn't find anything to
#    fix. Read LandController and ExpenseController in full, spot-checked
#    StageTemplateController/ReportController/DashboardController's
#    role-differentiated methods, and ran a whole-backend grep for
#    ROLE_SECRETARY appearing near delete/search/summary/analytics/storage/
#    receivable/financial endpoints (zero hits). Everywhere I checked, the
#    wiring matches the table and the STAGE-tagged comments explain the
#    reasoning (e.g. StageTemplateController explicitly says Secretary gets
#    stage-toggle but not cost-edit, matching "Changes Stages: Yes (stage
#    only)" in the table). I did NOT open every remaining line of every
#    controller (ClientController, RecoveryController, AuditController,
#    PaymentController, StaffController were only grep-checked, not read in
#    full) -- so this is a solid sample, not a 100%-exhaustive line audit.
#    Nothing here needed a patch.

import os

ROOT = os.path.dirname(os.path.abspath(__file__))
results = []


def patch(label, rel_path, old, new):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print("[STAGE 13] " + label + " ... MISSING (file not found: " + rel_path + ")")
        results.append(False)
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Idempotency check FIRST (see Stage 12 for why this ordering matters).
    if new in content:
        print("[STAGE 13] " + label + " ... OK (already applied)")
        results.append(True)
        return

    if old not in content:
        print("[STAGE 13] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        results.append(False)
        return

    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("[STAGE 13] " + label + " ... OK")
    results.append(True)


def delete_file(label, rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print("[STAGE 13] " + label + " ... OK (already deleted)")
        results.append(True)
        return
    os.remove(path)
    print("[STAGE 13] " + label + " ... OK (deleted)")
    results.append(True)


def rename_java_class(label, old_rel_path, new_rel_path, old_class, new_class):
    """Reads the current file, renames the class + constructor + PATH
    comment, writes it to the new path, then removes the old file. Safe to
    run twice: if the old file is already gone and the new one already has
    the new class name, treats it as done rather than erroring."""
    old_path = os.path.join(ROOT, old_rel_path)
    new_path = os.path.join(ROOT, new_rel_path)

    if not os.path.exists(old_path):
        if os.path.exists(new_path):
            with open(new_path, "r", encoding="utf-8", errors="replace") as f:
                if new_class in f.read():
                    print("[STAGE 13] " + label + " ... OK (already applied)")
                    results.append(True)
                    return
        print("[STAGE 13] " + label + " ... MISSING (neither old nor new file found)")
        results.append(False)
        return

    with open(old_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    content = content.replace("PATH: " + old_rel_path, "PATH: " + new_rel_path)
    content = content.replace("class " + old_class, "class " + new_class)
    content = content.replace("public " + old_class + "(", "public " + new_class + "(")

    with open(new_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    os.remove(old_path)
    print("[STAGE 13] " + label + " ... OK (renamed)")
    results.append(True)


# ── 1. Delete dead CompanyExpense stack (backend + frontend) ────────────────
delete_file(
    "Delete CompanyExpense.java (dead model, zero callers)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/model/CompanyExpense.java",
)
delete_file(
    "Delete CompanyExpenseRepository.java (dead, zero callers)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/CompanyExpenseRepository.java",
)
delete_file(
    "Delete CompanyExpenseService.java (dead, zero callers)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/service/CompanyExpenseService.java",
)
delete_file(
    "Delete CompanyExpenseController.java (dead, unrouted endpoint /finance/company-expenses)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/controller/CompanyExpenseController.java",
)
delete_file(
    "Delete CompanyExpensesPage.jsx (dead, App.jsx routes /financials to ExpensesPage instead)",
    "erp-frontend/src/pages/Financials/CompanyExpensesPage.jsx",
)
delete_file(
    "Delete CompanyExpensesPage.module.css (dead, styles for the unrouted page above)",
    "erp-frontend/src/pages/Financials/CompanyExpensesPage.module.css",
)
delete_file(
    "Delete companyExpenseService.js (dead, calls the unrouted endpoint above)",
    "erp-frontend/src/services/companyExpenseService.js",
)

# ── 2. Delete dead PaymentEngineService cluster ──────────────────────────────
delete_file(
    "Delete PaymentEngineService.java (dead, zero callers)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/PaymentEngineService.java",
)
delete_file(
    "Delete PaymentSchedule.java (dead, only used by PaymentEngineService above)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/PaymentSchedule.java",
)
delete_file(
    "Delete PaymentScheduleRepository.java (dead, only used by PaymentEngineService above)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentScheduleRepository.java",
)

# ── 3. Rename LocalStorageServiceImpl -> CloudinaryStorageServiceImpl ───────
rename_java_class(
    "Rename LocalStorageServiceImpl -> CloudinaryStorageServiceImpl (it's 100% Cloudinary, never touches local disk)",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LocalStorageServiceImpl.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/CloudinaryStorageServiceImpl.java",
    "LocalStorageServiceImpl",
    "CloudinaryStorageServiceImpl",
)

# ── 5. Fix stale comments ────────────────────────────────────────────────────
patch(
    "Role.java: update class comment -- Phase 3B/3C are actually wired now",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java",
    "/**\n"
    " * GOLDEN SEED ERP - INDUSTRIAL ROLE DICTIONARY\n"
    " *\n"
    " * PHASE 3A: Enum expanded to prepare for the 4-tier hierarchy (Section 17.7\n"
    " * of LLM_CONTEXT_GUIDE.md). This is additive only -- ROLE_DIRECTOR and\n"
    " * ROLE_SECRETARY exist now but no @PreAuthorize check anywhere references\n"
    " * them yet. Every existing access-control check still only knows about\n"
    " * ROLE_ADMIN and ROLE_MANAGER, so current behavior is unchanged.\n"
    " *\n"
    " * The 'Root Founder' (Programmer tier) is still not a role here; it remains\n"
    " * the 'isRoot' boolean on the User entity, layered on top of ROLE_ADMIN.\n"
    " *\n"
    " * Wiring these new values into actual permission checks (backend\n"
    " * @PreAuthorize + frontend role gates) is Phase 3B -- a separate, dedicated\n"
    " * patch, since it touches every controller and several frontend files.\n"
    " */\n",
    "/**\n"
    " * GOLDEN SEED ERP - INDUSTRIAL ROLE DICTIONARY\n"
    " *\n"
    " * 4-tier hierarchy per Section 17.7 of LLM_CONTEXT_GUIDE.md. ROLE_DIRECTOR\n"
    " * and ROLE_SECRETARY are fully wired: every controller's @PreAuthorize\n"
    " * checks and the frontend's route/nav gates already reference them\n"
    " * (landed via the separate bug-fix roadmap's Stage 1 and Stage 2, not the\n"
    " * original Phase 3B/3C patches -- see LLM_CONTEXT_GUIDE.md Section 17.10\n"
    " * for the corrected Phase Tracker entry).\n"
    " *\n"
    " * The 'Root Founder' (Programmer tier) is still not a role here; it remains\n"
    " * the 'isRoot' boolean on the User entity, layered on top of ROLE_ADMIN.\n"
    " */\n",
)

patch(
    "Role.java: update ROLE_DIRECTOR javadoc -- it is enforced now",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java",
    "    /**\n"
    "     * TIER 2 (NEW, Phase 3A groundwork): DIRECTOR\n"
    "     * Full company-wide financial visibility per Section 17.7, distinct\n"
    "     * from ROLE_ADMIN in the target design (Director sees everything;\n"
    "     * Manager sees project-level only). Not yet enforced anywhere.\n"
    "     */\n"
    "    ROLE_DIRECTOR,\n",
    "    /**\n"
    "     * TIER 2: DIRECTOR\n"
    "     * Full company-wide financial visibility per Section 17.7, distinct\n"
    "     * from ROLE_ADMIN in the target design (Director sees everything;\n"
    "     * Manager sees project-level only). Enforced across every controller's\n"
    "     * @PreAuthorize checks and the frontend's route gates.\n"
    "     */\n"
    "    ROLE_DIRECTOR,\n",
)

patch(
    "Role.java: update ROLE_SECRETARY javadoc -- it is enforced now",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java",
    "    /**\n"
    "     * TIER 4 (NEW, Phase 3A groundwork): SECRETARY\n"
    "     * Data-entry only, stage changes but not cost changes, no company\n"
    "     * financials, no template edits, per Section 17.7. Not yet enforced\n"
    "     * anywhere -- currently behaves identically to whatever @PreAuthorize\n"
    "     * checks already exist (i.e. blocked from anything ROLE_ADMIN/\n"
    "     * ROLE_MANAGER-gated, same as any unrecognized role would be).\n"
    "     */\n"
    "    ROLE_SECRETARY\n",
    "    /**\n"
    "     * TIER 4: SECRETARY\n"
    "     * Data-entry only, stage changes but not cost changes, no company\n"
    "     * financials, no template edits, per Section 17.7. Enforced per-method\n"
    "     * on the relevant controllers (LandController, StageTemplateController,\n"
    "     * RecoveryController) rather than at the class level, since Secretary\n"
    "     * needs some but not all of what Manager can do on the same endpoints.\n"
    "     */\n"
    "    ROLE_SECRETARY\n",
)

patch(
    "LoginRateLimiter.java: fix '15 minutes' javadoc -- code actually blocks for 10",
    "erp-backend/src/main/java/com/gesolutions/erp/config/LoginRateLimiter.java",
    "/**\n"
    " * Simple in-memory rate limiter for the login endpoint.\n"
    " * Blocks an IP for 15 minutes after 10 failed attempts.\n"
    " */\n",
    "/**\n"
    " * Simple in-memory rate limiter for the login endpoint.\n"
    " * Blocks an IP for 10 minutes after 10 failed attempts.\n"
    " */\n",
)

print("")
if all(results):
    print("All Stage 13 patches applied cleanly.")
else:
    print("Some patches were MISSING -- review output above before committing.")

print("")
print("SKIPPED ON PURPOSE -- suggestion 4 (/api/v1/vault/** lockdown):")
print("Before removing WebConfig.java and the permitAll rule in SecurityConfig.java,")
print("confirm no OLD document actually needs that fallback. Easiest way: query the")
print("live DB for  SELECT COUNT(*) FROM project_documents WHERE file_path NOT LIKE 'http%';")
print("If that returns 0, it's fully safe to delete both. If it doesn't, those rows'")
print("documents need to be re-uploaded to Cloudinary (or the paths migrated) first --")
print("say the word and I'll write that as a one-time migration + the removal together.")