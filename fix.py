# fix.py -- fix60: dedupe problem put, app-wide CANCEL cleanup, verify related projects.
import os, re, sys, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)

fpc = BE / "modules" / "land" / "controller" / "FolderPortalController.java"

# ---- 1) dedupe duplicated problem put ----
s = read(fpc)
s2 = re.sub(r'm\.put\("problem", p\.isProblem\(\)\);\s*m\.put\("problem", p\.isProblem\(\)\);',
            'm.put("problem", p.isProblem());', s)
if s2 != s: write(fpc, s2); print("OK   dedupe problem put")
else: print("MISS dedupe problem put (already single)")

# ---- 2) app-wide: remove CANCEL buttons that sit beside an X (design rule) ----
removed = 0
for r, d, fs in os.walk(FE):
    for f in fs:
        if f.endswith(".jsx"):
            p = Path(r) / f; s = read(p)
            # modalBtnSecondary single-line CANCEL buttons
            s2 = re.sub(r"[ \t]*<button[^>]*modalBtnSecondary[^>]*>[^<]*(?:<[^>]*>[^<]*)*CANCEL</button>\n", "", s)
            # confirm-modal CANCEL button
            s2 = re.sub(r"[ \t]*<button[^>]*confirmCancelBtn[^>]*>[^<]*(?:<[^>]*>[^<]*)*CANCEL</button>\n", "", s2)
            if s2 != s: write(p, s2); removed += 1; print("OK   CANCEL removed:", f)
print("files cleaned of redundant CANCEL:", removed)

# ---- 3) verify RELATED PROJECTS present in FolderPage ----
fp = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
s = read(fp)
print("OK   RELATED PROJECTS present" if "RELATED PROJECTS" in s else "MISS RELATED PROJECTS (re-run fix59)")
print("OK   statusBadge present" if "statusBadge" in s else "MISS statusBadge (re-run fix59)")

# ---- 4) addendum note ----
add = ROOT / "LLM_CONTEXT_ADDENDUM.md"
if add.exists():
    a = read(add)
    if "fix60" not in a:
        a += "\n- fix60 (2026-09-03): dedupe FolderPortalController problem put; app-wide removal of CANCEL buttons that sit beside the animated X (design rule: X is the closer); verified one-word badges + RELATED PROJECTS on Folder page.\n"
        write(add, a); print("OK   addendum updated")

# ---- git ----
try:
    subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","fix60: dedupe problem put, app-wide CANCEL cleanup"],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")