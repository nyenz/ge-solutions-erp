#!/usr/bin/env python3
"""
fix15.py — make land_projects.title_id nullable so FOLDER-type projects
(projects without titles yet) can be created.
Run: python3 fix15.py
"""
import os
import subprocess

PATCH = {
    "path": "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
    "old": '            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",\n',
    "new": (
        '            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",\n'
        '            // FIX (fix15): title_id was NOT NULL, blocking folder-type\n'
        '            // projects (no title yet) from being created. Make it nullable.\n'
        '            "ALTER TABLE land_projects ALTER COLUMN title_id DROP NOT NULL",\n'
    ),
}


def apply_patch(patch):
    path = patch["path"]
    if not os.path.exists(path):
        print("MISSING (file not found): " + path)
        return False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if patch["new"] in content:
        print("OK (already applied): " + path)
        return True

    if patch["old"] not in content:
        print("MISSING (patch target not found): " + path)
        return False

    content = content.replace(patch["old"], patch["new"], 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: " + path)
    return True


def main():
    if not apply_patch(PATCH):
        print("\nPatch did not apply. Review MISSING line above before deploying.")
        return

    subprocess.run(["git", "add", "-A"], check=False)
    subprocess.run(
        ["git", "commit", "-m", "fix15: make land_projects.title_id nullable for folder-type projects"],
        check=False,
    )
    subprocess.run(["git", "push"], check=False)
    print("\nDone. After deploy, the seed should complete and the Ledger will fill.")


if __name__ == "__main__":
    main()