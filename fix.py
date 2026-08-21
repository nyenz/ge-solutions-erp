# PATH: fix.py
# STAGE 5 -- NAMING CONSISTENCY CLEANUP (bug-fix roadmap continuation)
# Run from project root: python fix.py   (or: py fix.py)
# Assumes Stages 1-4 have already been run, committed, and pushed.
#
# WHAT THIS STAGE IS -- read before running:
#
# David asked for a full-codebase read-through and a consistency cleanup pass
# (wording, naming, flow). The codebase was cloned fresh and every module was
# checked against the two things already flagged as known issues in
# LLM_CONTEXT_GUIDE.md Section 12 plus a fresh terminology sweep:
#
# CHECKED AND ALREADY CONSISTENT (no patch needed, listed so nothing gets
# re-litigated in a future session):
#   - Payment type naming (STANDARD / INITIAL_DEPOSIT / RECEIVABLE_PARTIAL /
#     STORAGE_FEE) -- identical everywhere in both frontend and backend.
#   - Role naming (ROLE_ADMIN / ROLE_MANAGER / ROLE_DIRECTOR / ROLE_SECRETARY)
#     -- identical everywhere, matches Section 17.7's 4-tier table.
#   - "Receivable" vs "Receivables" (work-not-done vs done-but-unpaid, Section
#     17.2) -- used correctly and distinctly wherever both appear together
#     (RecoveryPortal, ReportHub, Dashboard).
#   - The Section 11 "language simplification" list (Master Hardware
#     Override, Nuclear Purge, Intel, Vault, Recovery Sync, Asset Intake,
#     Forensic Stream) -- Stage 4 already finished this; nothing left.
#
# FIX 1 -- APP NAME INCONSISTENCY (Section 12's "NYENZ ERP vs Golden Seed"
# known issue). Every user-visible surface already said "Golden Seed"
# correctly (Header, LoginPage, print dossier). The leftover "NYENZ" was in
# two places a real user (or a screen reader) actually sees:
#   - Sidebar.jsx footer: aria-label + visible branding text still read
#     "NYENZ" while the header logo two inches above it reads "GOLDEN SEED".
#   - ReportController.java: every downloaded report CSV was literally named
#     NYENZ_<report>_<date>.csv -- a client-facing filename that didn't match
#     the app's own branding.
# Every remaining "NYENZ" was in code comments / doc-block headers (not
# visible to any user) -- patched too for internal consistency, since David
# asked for the whole codebase to read consistently, not just the UI.
#
# FIX 2 -- BACKLOG/RECEIVABLE DB COLUMN NAMES (David's exact example: he
# wants "receivable" used for everything that used to say "backlog"). The
# Java side is already fully done (c858569 renamed every field, label, and
# variable). The ONLY thing still called "backlog" anywhere in the app is 4
# raw Postgres column names behind @Column(name=...) on LandProject.java:
# is_backlog, backlog_start_date, backlog_start_override,
# backlog_months_billed. These are invisible to every user and even to the
# Java code (the fields themselves are already isReceivable, etc).
#
# THIS SCRIPT DOES NOT RENAME THOSE COLUMNS. Reason, checked against your
# actual config: application.properties has
# spring.jpa.hibernate.ddl-auto=update. Hibernate runs its own schema sync
# from the @Column names BEFORE DataInitializer's CommandLineRunner (which is
# where a RENAME COLUMN migration would have to live) ever executes. So the
# instant the Java @Column annotation changed to "is_receivable", Hibernate
# would silently ADD a new empty is_receivable column at boot -- then the
# RENAME migration would fail (target name already taken) and get silently
# skipped by the existing try/catch-and-continue pattern in
# runSchemaMigrations(). Net result on your real production data: a
# fresh, empty is_receivable column the app now reads from, while every real
# historical value sits stranded in the old is_backlog column, invisible.
# That is a silent real-money data loss risk on a live financial table, not
# a cosmetic issue, so it does not belong in an automatic cleanup script.
# Instead: a code comment is added at the site explaining exactly why the
# name is intentionally still "backlog" at the DB level, so nobody
# accidentally "fixes" this later without seeing the reasoning. If you want
# this actually renamed, it needs a one-time manual migration run by hand
# against the live DB (not via ddl-auto), separately from a code deploy --
# flag it to a future session explicitly if you want that scheduled.
#
# Safe to re-run: every patch is checked before writing; if a patch target
# is not found it prints MISSING and leaves that file alone (most likely
# meaning this stage is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# Each tuple: (label, relative_path, old_str, new_str)
PATCHES = [
    # --- FIX 1: user-visible branding (the two real leftovers) ---
    (
        "Sidebar footer aria-label",
        "erp-frontend/src/components/layout/Sidebar.jsx",
        'aria-label="NYENZ branding"',
        'aria-label="Golden Seed branding"',
    ),
    (
        "Sidebar footer visible text",
        "erp-frontend/src/components/layout/Sidebar.jsx",
        '<div className={styles.branding} aria-hidden="true">NYENZ</div>',
        '<div className={styles.branding} aria-hidden="true">GOLDEN SEED</div>',
    ),
    (
        "Report CSV download filename",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/ReportController.java",
        'String fileName = "NYENZ_" + reportName + "_" + LocalDateTime.now().format(fileStamp) + ".csv";',
        'String fileName = "GOLDEN_SEED_" + reportName + "_" + LocalDateTime.now().format(fileStamp) + ".csv";',
    ),

    # --- FIX 1: internal-only doc-comment headers / boot log lines ---
    (
        "SystemAdminController header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java",
        " * NYENZ ERP - SYSTEM RESET CONTROLLER",
        " * GOLDEN SEED ERP - SYSTEM RESET CONTROLLER",
    ),
    (
        "Role.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java",
        " * NYENZ ERP - INDUSTRIAL ROLE DICTIONARY",
        " * GOLDEN SEED ERP - INDUSTRIAL ROLE DICTIONARY",
    ),
    (
        "User.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/User.java",
        " * NYENZ ERP - SYSTEM OPERATOR IDENTITY",
        " * GOLDEN SEED ERP - SYSTEM OPERATOR IDENTITY",
    ),
    (
        "UserRepository.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/repository/UserRepository.java",
        " * NYENZ ERP - OPERATOR REGISTRY ACCESS",
        " * GOLDEN SEED ERP - OPERATOR REGISTRY ACCESS",
    ),
    (
        "AuthService.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/AuthService.java",
        " * NYENZ ERP - AUTHENTICATION & RECOVERY ENGINE (V2.0 - REBOOT)",
        " * GOLDEN SEED ERP - AUTHENTICATION & RECOVERY ENGINE (V2.0 - REBOOT)",
    ),
    (
        "StaffManagementService.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/StaffManagementService.java",
        " * NYENZ ERP - STAFF MANAGEMENT ENGINE (V5)",
        " * GOLDEN SEED ERP - STAFF MANAGEMENT ENGINE (V5)",
    ),
    (
        "StaffController.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/StaffController.java",
        " * NYENZ ERP - STAFF MASTERY CONTROLLER",
        " * GOLDEN SEED ERP - STAFF MASTERY CONTROLLER",
    ),
    (
        "ProfileController.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/ProfileController.java",
        " * NYENZ ERP - PROFILE & SECURITY PANEL",
        " * GOLDEN SEED ERP - PROFILE & SECURITY PANEL",
    ),
    (
        "AuthController.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/AuthController.java",
        " * NYENZ ERP - AUTHENTICATION GATEWAY (V2.1 - HEALTH CHECK ADDED)",
        " * GOLDEN SEED ERP - AUTHENTICATION GATEWAY (V2.1 - HEALTH CHECK ADDED)",
    ),
    (
        "ReportController.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/ReportController.java",
        " * NYENZ ERP - INTELLIGENCE COMMAND HUB (V16)",
        " * GOLDEN SEED ERP - INTELLIGENCE COMMAND HUB (V16)",
    ),
    (
        "DataInitializer.java boot log line 1",
        "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
        'System.out.println(">>> NYENZ SYSTEM: Verifying Master Identity Registry...");',
        'System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");',
    ),
    (
        "DataInitializer.java boot log line 2",
        "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
        'System.out.println(">>> NYENZ SYSTEM: Identity Protocol Active. Registry Locked.");',
        'System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");',
    ),
    (
        "SecurityConfig.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/config/SecurityConfig.java",
        " * NYENZ ERP - MASTER SECURITY CONFIG (V3.0 - CLOUD STABLE)",
        " * GOLDEN SEED ERP - MASTER SECURITY CONFIG (V3.0 - CLOUD STABLE)",
    ),
    (
        "WebConfig.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/config/WebConfig.java",
        " * NYENZ ERP - DIGITAL VAULT BRIDGE (V1.2 - CROSS-PLATFORM)",
        " * GOLDEN SEED ERP - DIGITAL VAULT BRIDGE (V1.2 - CROSS-PLATFORM)",
    ),
    (
        "GlobalExceptionHandler.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/common/exception/GlobalExceptionHandler.java",
        " * NYENZ ERP - MASTER DIAGNOSTIC INTERCEPTOR (V1.3 - LOUD REPORTING)",
        " * GOLDEN SEED ERP - MASTER DIAGNOSTIC INTERCEPTOR (V1.3 - LOUD REPORTING)",
    ),
    (
        "AuditController.java header comment",
        "erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditController.java",
        " * NYENZ ERP - SYSTEM FORENSICS TERMINAL",
        " * GOLDEN SEED ERP - SYSTEM FORENSICS TERMINAL",
    ),
    (
        "auditService.js header comment",
        "erp-frontend/src/services/auditService.js",
        " * NYENZ INDUSTRIAL AUDIT SERVICE",
        " * GOLDEN SEED INDUSTRIAL AUDIT SERVICE",
    ),
    (
        "reportService.js header comment",
        "erp-frontend/src/services/reportService.js",
        " * NYENZ INDUSTRIAL REPORTING SERVICE",
        " * GOLDEN SEED INDUSTRIAL REPORTING SERVICE",
    ),
    (
        "reportService.js pillars comment",
        "erp-frontend/src/services/reportService.js",
        "/* --- THE 8 PILLARS OF NYENZ INTELLIGENCE --- */",
        "/* --- THE 8 PILLARS OF GOLDEN SEED INTELLIGENCE --- */",
    ),
    (
        "predictionService.js header comment",
        "erp-frontend/src/services/predictionService.js",
        " * NYENZ PREDICTION ENGINE",
        " * GOLDEN SEED PREDICTION ENGINE",
    ),
    (
        "authService.js header comment",
        "erp-frontend/src/services/authService.js",
        " * NYENZ ERP - AUTHENTICATION PIPELINE (V2.1 - CLOUD FIXED)",
        " * GOLDEN SEED ERP - AUTHENTICATION PIPELINE (V2.1 - CLOUD FIXED)",
    ),
    (
        "settingsService.js header comment",
        "erp-frontend/src/services/settingsService.js",
        " * NYENZ ERP - SECURITY & GOVERNANCE SERVICE (V5)",
        " * GOLDEN SEED ERP - SECURITY & GOVERNANCE SERVICE (V5)",
    ),
    (
        "FolderPage.module.css header comment",
        "erp-frontend/src/pages/DigitalFolder/FolderPage.module.css",
        "   NYENZ ERP \u2014 TERMINAL X  |  FolderPage.module.css  |  V15.7",
        "   GOLDEN SEED ERP \u2014 TERMINAL X  |  FolderPage.module.css  |  V15.7",
    ),

    # --- FIX 2: explain-don't-touch comment on the backlog/receivable columns ---
    (
        "LandProject.java backlog column risk-note comment",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java",
        "    // Boolean (object not primitive) so existing DB rows with NULL don't crash\n"
        "    @Builder.Default\n"
        '    @Column(name = "is_backlog")\n'
        "    private Boolean isReceivable = false;",

        "    // Boolean (object not primitive) so existing DB rows with NULL don't crash\n"
        "    //\n"
        "    // NOTE (Stage 5 cleanup pass): the 4 raw column names below (is_backlog,\n"
        "    // backlog_start_date, backlog_start_override, backlog_months_billed) are\n"
        "    // the only place in the whole app still saying \"backlog\" instead of\n"
        "    // \"receivable\" -- the Java fields themselves were already renamed in\n"
        "    // c858569. Left as-is on purpose: ddl-auto=update makes Hibernate sync\n"
        "    // its schema from these @Column names BEFORE DataInitializer's raw-JDBC\n"
        "    // migrations ever run, so renaming the annotation would make Hibernate\n"
        "    // silently create a new empty column at boot and strand all the real\n"
        "    // historical data in the old column name. Do not rename these without a\n"
        "    // manual, out-of-band migration run directly against the live DB first.\n"
        "    @Builder.Default\n"
        '    @Column(name = "is_backlog")\n'
        "    private Boolean isReceivable = false;",
    ),
]


def apply_patches():
    ok = 0
    missing = []
    for label, rel_path, old, new in PATCHES:
        full_path = os.path.join(ROOT, rel_path)
        if not os.path.exists(full_path):
            print("[STAGE 5] " + label + " ... MISSING (file not found: " + rel_path + ")")
            missing.append(label)
            continue

        content = read_file(full_path)
        if old not in content:
            if new in content:
                print("[STAGE 5] " + label + " ... OK (already applied)")
                ok += 1
            else:
                print("[STAGE 5] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
                missing.append(label)
            continue

        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("[STAGE 5] " + label + " ... OK")
        ok += 1

    return ok, missing


def main():
    print("=" * 70)
    print("STAGE 5 -- NAMING CONSISTENCY CLEANUP")
    print("=" * 70)
    ok, missing = apply_patches()
    print("-" * 70)
    print("Applied/confirmed: " + str(ok) + " / " + str(len(PATCHES)))
    if missing:
        print("MISSING (" + str(len(missing)) + "):")
        for m in missing:
            print("  - " + m)
    else:
        print("Nothing missing.")
    print("=" * 70)
    print("Next: git add -A && git commit -m 'Stage 5: naming consistency cleanup' && git push")


if __name__ == "__main__":
    main()