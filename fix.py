import subprocess
import pathlib
import sys

# True  = preview only, changes nothing, no git commit/push
# False = apply fixes, then auto git add/commit/push
DRY_RUN = False

# If True, script stops before git if any file is missing
# or any search pattern is not found.
STRICT = True

MSG = 'fix86: reports top section matches prototype (drop dupe reload, data sources own panel, search field resized, dropdown restyle)'


FIXES = [
    # KEEP YOUR EXISTING FIXES LIST HERE EXACTLY AS YOU WROTE IT.
    # Example format:
    #
    # (
    #     "erp-frontend/src/pages/Reports/ReportStudio.jsx",
    #     "old code string",
    #     "new code string",
    # ),
]


print("fix.py: start")
print("DRY_RUN:", DRY_RUN)
print("STRICT:", STRICT)
print("fix count:", len(FIXES))

changed_files = []
problems = []

for i, (path, old, new) in enumerate(FIXES, start=1):
    p = pathlib.Path(path)

    if not p.exists():
        print(f"[{i}] missing file: {path}")
        problems.append(path)
        continue

    txt = p.read_text(encoding="utf-8")

    if old not in txt:
        print(f"[{i}] pattern not found: {path}")
        problems.append(path)
        continue

    if DRY_RUN:
        print(f"[{i}] would fix: {path}")
    else:
        p.write_text(txt.replace(old, new, 1), encoding="utf-8")
        print(f"[{i}] fixed: {path}")
        changed_files.append(path)


if DRY_RUN:
    print("")
    print("fix.py: dry run only, nothing changed")
    print("git commands skipped")
    sys.exit(0)


if STRICT and problems:
    print("")
    print("fix.py: stopping before git because some fixes failed:")
    for p in problems:
        print(" -", p)
    sys.exit(1)


def run(cmd):
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


# Check if git sees any changes.
status = subprocess.run(
    ["git", "status", "--porcelain"],
    capture_output=True,
    text=True,
    check=True,
)

if not status.stdout.strip():
    print("")
    print("fix.py: no git changes to commit")
    sys.exit(0)


print("")
print("git: staging, committing, pushing...")

# Stage changes.
run(["git", "add", "-A"])

# Commit.
run(["git", "commit", "-m", MSG])

# Get current branch name.
branch_result = subprocess.run(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    capture_output=True,
    text=True,
    check=True,
)
branch = branch_result.stdout.strip()

# Check if current branch already has an upstream.
upstream = subprocess.run(
    ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
    capture_output=True,
    text=True,
)

if upstream.returncode == 0:
    # Branch already tracks a remote branch.
    run(["git", "push"])
else:
    # No upstream yet, so set it while pushing.
    if branch == "HEAD":
        # Detached HEAD fallback.
        run(["git", "push", "origin", "HEAD"])
    else:
        run(["git", "push", "-u", "origin", branch])

print("")
print("fix.py: done")