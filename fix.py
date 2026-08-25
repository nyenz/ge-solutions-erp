#!/usr/bin/env python3
"""
fix.py — repair stage-delete ID type (Long -> UUID).
Run: py fix.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
PATCHED, FAILED = [], []

def fix_type(rel, old, new):
    p = ROOT / rel
    try:
        s = p.read_text(encoding="utf-8")
    except Exception as e:
        FAILED.append((rel, f"read failed: {e}")); return
    if old in s:
        p.write_text(s.replace(old, new, 1), encoding="utf-8")
        PATCHED.append(rel)
    elif new in s:
        PATCHED.append(f"{rel} (already fixed)")
    else:
        FAILED.append((rel, "pattern not found"))

# StageTemplate IDs are UUIDs - fix the inserted delete method + endpoint
fix_type(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java",
    "public void deleteTemplateStage(Long id)",
    "public void deleteTemplateStage(java.util.UUID id)"
)
fix_type(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java",
    "@org.springframework.web.bind.annotation.PathVariable Long id",
    "@org.springframework.web.bind.annotation.PathVariable java.util.UUID id"
)

print(f"\n=== fix.py completed ===")
print(f"  Patched: {len(PATCHED)} file(s)")
for f in PATCHED: print(f"    ~ {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)} file(s)")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if PATCHED:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(['git', 'commit', '-m',
            'fix: stage delete uses UUID id (StageTemplate PK is UUID, not Long)'],
            check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed all changes")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed to remote")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit code {e.returncode})")
        if e.output:
            print(f"    {e.output.decode('utf-8', errors='replace').strip()}")
    except FileNotFoundError:
        print("\n  Git: git not found in PATH")

print()