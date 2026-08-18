# PATH: fix.py
# NAMING FIX - "Backlog" -> "Receivable"
# Run from project root: python fix.py   (or: py fix.py)
#
# WHAT THIS DOES:
# The app used two different terms for the same thing: pages/labels said
# "Legacy Receivable" in some places (Intake) and "Backlog" in others
# (Ledger, Payments, Recovery, Digital Folder, Reports, Dashboard, plus
# the matching backend fields/routes/enums). This script renames every
# occurrence of "Backlog" to "Receivable" (case-preserved: Backlog ->
# Receivable, backlog -> receivable, BACKLOG -> RECEIVABLE) across both
# erp-frontend and erp-backend, so the term is consistent everywhere the
# user can see it, and consistent in the code that talks to the API.
#
# WHAT IT DELIBERATELY DOES NOT TOUCH:
# The actual database column names (is_backlog, backlog_start_date,
# backlog_start_override, backlog_months_billed) are left exactly as-is
# in the @Column(...) annotations and in the ALTER TABLE bootstrap SQL
# in DataInitializer.java. Only the Java/JS-facing names change.
# --> NO DATABASE MIGRATION IS NEEDED to run this fix.
#
# It also renames two backend files to match:
#   BacklogSchedulerService.java -> ReceivableSchedulerService.java
#   BacklogSchedulerTest.java    -> ReceivableSchedulerTest.java
#
# Safe to re-run: if "backlog" is no longer found anywhere, it just says
# so and exits without touching anything.

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

SCAN_DIRS = [
    "erp-frontend/src",
    "erp-backend/src",
]
EXTRA_FILES = [
    "LLM_CONTEXT_GUIDE.md",
]

EXT_WHITELIST = {".java", ".jsx", ".js", ".css", ".md"}
SKIP_DIR_NAMES = {"node_modules", "dist", "build", "target", ".git"}

# These exact strings must stay as-is: they are live DB column names
# referenced from @Column(name="...") and from raw ALTER TABLE SQL.
# If we renamed these too, the entity mapping and the bootstrap SQL
# would go out of sync and the app would fail against an existing DB.
PROTECTED_LITERALS = [
    "is_backlog",
    "backlog_start_date",
    "backlog_start_override",
    "backlog_months_billed",
]

PLACEHOLDER_PREFIX = "\x00PROTECTED_LITERAL_"


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def rename_content(content):
    # Protect the DB column literals before the global rename, then
    # restore them afterwards untouched.
    placeholders = {}
    for i, literal in enumerate(PROTECTED_LITERALS):
        if literal in content:
            token = PLACEHOLDER_PREFIX + str(i) + "\x00"
            placeholders[token] = literal
            content = content.replace(literal, token)

    content = content.replace("Backlog", "Receivable")
    content = content.replace("backlog", "receivable")
    content = content.replace("BACKLOG", "RECEIVABLE")

    for token, literal in placeholders.items():
        content = content.replace(token, literal)

    return content


def collect_files():
    files = []
    for rel_dir in SCAN_DIRS:
        base = os.path.join(ROOT, rel_dir)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            for name in filenames:
                if os.path.splitext(name)[1] in EXT_WHITELIST:
                    files.append(os.path.join(dirpath, name))
    for rel_file in EXTRA_FILES:
        p = os.path.join(ROOT, rel_file)
        if os.path.isfile(p):
            files.append(p)
    return files


def rename_file_if_present(old_rel, new_rel, label):
    old_path = os.path.join(ROOT, old_rel)
    new_path = os.path.join(ROOT, new_rel)
    if os.path.isfile(old_path):
        os.rename(old_path, new_path)
        print("OK: renamed " + label)
        return new_path
    elif os.path.isfile(new_path):
        print("SKIP: " + label + " (already renamed)")
        return new_path
    else:
        print("MISSING: " + label + " (source file not found -- skipping)")
        return None


def main():
    print("Naming fix: Backlog -> Receivable")
    print("-" * 60)

    # 1) Rename the two files that carry the old term in their name,
    #    BEFORE the content pass, so the content pass also fixes their
    #    internal PATH header comment.
    scheduler_new = rename_file_if_present(
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerService.java",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerService.java",
        "BacklogSchedulerService.java -> ReceivableSchedulerService.java",
    )
    scheduler_test_new = rename_file_if_present(
        "erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerTest.java",
        "erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerTest.java",
        "BacklogSchedulerTest.java -> ReceivableSchedulerTest.java",
    )

    print("-" * 60)

    # 2) Sweep every source file and do the case-preserving rename.
    changed = 0
    scanned = 0
    for path in collect_files():
        scanned += 1
        content = read_file(path)
        if "backlog" not in content.lower():
            continue
        new_content = rename_content(content)
        if new_content != content:
            write_file(path, new_content)
            changed += 1
            print("OK: updated " + os.path.relpath(path, ROOT))

    print("-" * 60)
    print("Scanned " + str(scanned) + " files, updated " + str(changed) + ".")

    if changed == 0 and not scheduler_new and not scheduler_test_new:
        print("Nothing to do -- 'backlog' was not found anywhere. Already fixed?")
    else:
        print("Done. DB column names were left unchanged on purpose "
              "(is_backlog, backlog_start_date, backlog_start_override, "
              "backlog_months_billed) -- no migration needed.")


if __name__ == "__main__":
    main()