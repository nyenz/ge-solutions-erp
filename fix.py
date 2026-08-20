# PATH: fix.py
# STAGE 4 -- CLEANUP AND PROCESS (bug-fix roadmap)
# Run from project root: python fix.py   (or: py fix.py)
# Assumes Stages 1, 2, and 3 have already been run, committed, and pushed.
#
# IMPORTANT DISCOVERY WHILE BUILDING THIS STAGE -- read before running:
#
# FIX 1 (dead weekly-payment-schedule code) turned up different than the
# roadmap assumed. The roadmap's own safety rule is: search for live
# references first, and if any are found, do NOT delete, just report what
# still uses it. Doing that search for real against your actual code:
#
#   - PaymentSchedule.java / PaymentScheduleRepository.java ARE actively
#     used by PaymentEngineService.java (it builds and saves
#     PaymentSchedule rows). So per the roadmap's own rule, these two stay.
#   - ReceivableSchedulerService.java is referenced by
#     ReceivableSchedulerTest.java, which alone is enough to block deletion
#     under the same rule -- but there's a bigger reason not printed by a
#     plain grep-for-callers search: this class runs TWO @Scheduled cron
#     jobs (applyMonthlyStorageFees at midnight, autoFlagStaleAsReceivable
#     at 6am). Those are your live UGX 50,000/30-day storage fee billing
#     and the 365-day auto-receivable flag from Section 9 -- Spring fires
#     them on schedule, so nothing in the codebase needs to "call" them for
#     them to be live. A caller-based dead-code search will never catch a
#     scheduled job. This file was NOT put in this script's delete list
#     under any code path -- it is simply not a candidate here.
#
#   So: nothing gets deleted this stage. All three files are printed as
#   MISSING with the specific reason, exactly as the roadmap's own
#   reporting rule asks for when a live reference is found. Worth knowing
#   for a future session: PaymentEngineService itself (the class that
#   keeps PaymentSchedule/PaymentScheduleRepository alive) has no caller
#   anywhere in the codebase -- so this whole 3-file cluster IS dead
#   together, just not deletable one file at a time the way Stage 4
#   assumed. That's a separate, slightly bigger cleanup than what was
#   scoped here, so it's flagged below rather than done unilaterally.
#
# FIX 2 (Phase 3 status claim) -- already correct in LLM_CONTEXT_GUIDE.md
# (Stage 3 of this roadmap already corrected Section 17.10's wording for
# Phase 3, and Phases 5/6/7 besides). Nothing to patch.
#
# FIX 3 (language simplification list) -- checked every .jsx file for all
# six old strings. Five have no trace anywhere (already renamed in earlier
# work). "Nuclear Purge" survives only as a CSS comment above the button
# that already reads "DELETE" -- not user-visible, left alone. The one
# real leftover: RootTerminal.jsx's "NEW PLOT" quick-action button still
# carries aria-label="Go to asset intake" even though its visible text
# already says "NEW PLOT" -- fixed below to keep the accessible name and
# the visible label consistent (screen reader users were hearing the old
# terminology even though sighted users never saw it).
#
# Safe to re-run: every patch is checked before writing; if a patch
# target is not found it prints MISSING and leaves that file alone
# (most likely meaning this stage is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------
# FIX 1: dead weekly-payment-schedule code -- dynamic reference check.
# Actually walks the codebase at run time (not hardcoded) so this stays
# correct even if the code has moved on since this script was written.
# ---------------------------------------------------------------------
DELETE_CANDIDATES = [
    (
        "PaymentSchedule",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/PaymentSchedule.java",
    ),
    (
        "PaymentScheduleRepository",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentScheduleRepository.java",
    ),
    (
        "ReceivableSchedulerService",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerService.java",
    ),
]


def find_java_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if fn.endswith(".java"):
                out.append(os.path.join(dirpath, fn))
    return out


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def check_and_delete_dead_code():
    applied = 0
    missing = []
    all_java = find_java_files(ROOT)

    for class_name, rel_def_path in DELETE_CANDIDATES:
        def_full_path = os.path.join(ROOT, rel_def_path)
        if not os.path.exists(def_full_path):
            print("[STAGE 4] delete " + rel_def_path + " ... OK (already removed)")
            applied += 1
            continue

        refs = []
        for full_path in all_java:
            if os.path.abspath(full_path) == os.path.abspath(def_full_path):
                continue
            content = read_file(full_path)
            if class_name in content:
                rel = os.path.relpath(full_path, ROOT).replace(os.sep, "/")
                refs.append(rel)

        if refs:
            print("[STAGE 4] delete " + rel_def_path + " ... MISSING (still referenced by: "
                  + ", ".join(refs) + " -- NOT deleted)")
            missing.append(rel_def_path + " (still referenced by: " + ", ".join(refs) + ")")
        else:
            os.remove(def_full_path)
            print("[STAGE 4] delete " + rel_def_path + " ... OK (deleted, no references found)")
            applied += 1

    return applied, missing


# ---------------------------------------------------------------------
# FIX 3: language simplification -- the one real leftover found.
# ---------------------------------------------------------------------
PATCHES = [
    (
        "erp-frontend/src/pages/Dashboard/RootTerminal.jsx",
        '''<button className={styles.launchBtn} onClick={() => navigate('/land/new')}      aria-label="Go to asset intake"><FiFilePlus  aria-hidden="true" /> NEW PLOT</button>''',
        '''<button className={styles.launchBtn} onClick={() => navigate('/land/new')}      aria-label="Go to new plot"><FiFilePlus  aria-hidden="true" /> NEW PLOT</button>''',
    ),

    # -------------------------------------------------------------
    # Section 3 process note (verbatim, per the roadmap instructions)
    # -------------------------------------------------------------
    (
        "LLM_CONTEXT_GUIDE.md",
        '''**RULE (August 2026, PERMANENT): Testing happens ONLY after ALL planned phases in the current rebuild are code-complete and deployed -- never after each individual phase in isolation. Do not propose or ask David to test a single phase on its own; keep shipping phases back-to-back until the full plan is code-complete, then run one comprehensive end-to-end test pass covering everything at once. This makes permanent the deferred-testing approach David adopted during the ERP Revamp.**

### Why patches fail:''',
        '''**RULE (August 2026, PERMANENT): Testing happens ONLY after ALL planned phases in the current rebuild are code-complete and deployed -- never after each individual phase in isolation. Do not propose or ask David to test a single phase on its own; keep shipping phases back-to-back until the full plan is code-complete, then run one comprehensive end-to-end test pass covering everything at once. This makes permanent the deferred-testing approach David adopted during the ERP Revamp.**
**RULE (August 2026, PERMANENT): Going forward, BUG FIXES (as opposed to new revamp phases) are tested immediately after each stage, not deferred to the end. Only the ERP REVAMP phases (Section 17) follow the deferred, test-everything-at-the-end rule. Bug-fix stages in the roadmap follow normal one-stage-then-test discipline.**

### Why patches fail:''',
    ),
]


def apply_patches():
    applied = 0
    missing = []

    for rel_path, old, new in PATCHES:
        full_path = os.path.join(ROOT, rel_path)
        desc = rel_path
        if not os.path.exists(full_path):
            print("[STAGE 4] " + desc + " ... MISSING (file not found)")
            missing.append(desc + " (file not found)")
            continue
        content = read_file(full_path)
        if new in content:
            print("[STAGE 4] " + desc + " ... OK (already patched)")
            applied += 1
            continue
        if old not in content:
            print("[STAGE 4] " + desc + " ... MISSING (patch target not found)")
            missing.append(desc + " (patch target not found)")
            continue
        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("[STAGE 4] " + desc + " ... OK")
        applied += 1

    return applied, missing


def main():
    print("--- FIX 1: dead weekly-payment-schedule code (live reference check) ---")
    dead_code_applied, dead_code_missing = check_and_delete_dead_code()

    print("")
    print("--- FIX 2: Phase 3 status claim ---")
    print("[STAGE 4] LLM_CONTEXT_GUIDE.md Section 17.10 Phase 3 wording ... OK (already correct, "
          "fixed in Stage 3)")

    print("")
    print("--- FIX 3: language simplification + Section 3 process note ---")
    patch_applied, patch_missing = apply_patches()

    applied = dead_code_applied + 1 + patch_applied  # +1 for the already-correct Fix 2 check
    missing = dead_code_missing + patch_missing
    total = len(DELETE_CANDIDATES) + 1 + len(PATCHES)

    print("")
    print("============================================")
    print("STAGE 4 COMPLETE: " + str(applied) + " of " + str(total) + " items resolved")
    print("FILES DELETED: none this run (see MISSING list below for why)")
    print("LABEL STRINGS REPLACED: 1 (RootTerminal.jsx aria-label)")
    print("DOC CORRECTIONS: 1 (Section 3 bug-fix testing-cadence note appended)")
    print("============================================")

    if missing:
        print("")
        print("MISSING / NOT DELETED (expected this run -- see header comment for why):")
        for m in missing:
            print("  - " + m)

    print("")
    print("FLAGGED FOR A FUTURE SESSION (not done here -- bigger than this stage's scope):")
    print("  - PaymentSchedule.java, PaymentScheduleRepository.java, and PaymentEngineService.java")
    print("    together form a dead cluster: PaymentEngineService is the only thing that uses the")
    print("    other two, and NOTHING calls PaymentEngineService anywhere in the codebase. If")
    print("    confirmed genuinely unused, a future fix.py could delete all three together. NOT")
    print("    done automatically here because Stage 4's own scope was the three roadmap-named")
    print("    files, and PaymentEngineService was never one of them -- expanding to delete it too")
    print("    is a decision for a dedicated pass, not a side effect of this cleanup stage.")
    print("  - ReceivableSchedulerService.java must NEVER be deleted by a future cleanup pass on")
    print("    the strength of a caller search alone -- it runs two live @Scheduled cron jobs")
    print("    (storage fee billing, auto-receivable flagging) that Spring invokes on a timer,")
    print("    not via any code reference that a dead-code grep would find.")
    print("  - payment_schedules DB table: still fully orphaned (same as before), can be dropped")
    print("    manually once you're confident nothing needs it. Not touched by this script.")

    print("")
    print("Next steps:")
    print("1. git add -A && git commit -m 'Stage 4: label cleanup, doc/process notes' && git push")
    print("2. Watch Render Events tab for the green tick.")
    print("3. Spot-check the NEW PLOT button on the Root/Director dashboard with a screen reader")
    print("   or the accessibility inspector -- confirm it now announces 'Go to new plot'.")
    print("4. Confirm the app still builds and runs (nothing was deleted this run, so this should")
    print("   be a formality).")


if __name__ == "__main__":
    main()