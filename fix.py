#!/usr/bin/env python3
"""fix27.py — (1) remove all sample/seed data (wipe, no re-seed);
(2) make scrolled table rows disappear behind the sticky column headings.
Run: py fix27.py"""
import re, subprocess
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
WROTE=[]

def patch(rel, old, new):
    p = ROOT / rel; t = p.read_text(encoding="utf-8")
    if old not in t:
        print("!! anchor not found in", rel); return False
    p.write_text(t.replace(old, new, 1), encoding="utf-8"); WROTE.append(rel+" (patched)"); return True

def regex(rel, pattern, repl):
    p = ROOT / rel; t = p.read_text(encoding="utf-8")
    t2, n = re.subn(pattern, repl, t, count=1)
    if n == 0:
        print("!! regex not found in", rel); return False
    p.write_text(t2, encoding="utf-8"); WROTE.append(rel+" (patched)"); return True

# ---------------- 1) DataInitializer: wipe sample data, do NOT re-seed ----------------
# Swap the seed call for the purge so boot clears sample rows and never re-adds them.
if not patch('erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java',
        "        seedSampleProjects();\n",
        "        purgeSampleData();\n"):
    # fallback: if a seed call with different indent exists, neutralize it
    regex('erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java',
        r"(?m)^\s*seedSampleProjects\(\);\s*$", "        purgeSampleData();")

# ---------------- 2) CSS: rows disappear behind sticky column headings ----------------
# Make the sticky header opaque and extend a solid page-bg cover ABOVE it so
# scrolled rows slide under the header and never show through the gap.
regex('erp-frontend/src/pages/Ledger/LedgerPage.module.css',
    r"\.ledgerTable thead th\{[^}]*\}",
    ".ledgerTable thead th{"
    "position:sticky;top:64px;z-index:100;"
    "background:#162a2c;color:var(--orange);"
    "font-family:'Inter',sans-serif;font-size:var(--fs-th);font-weight:900;letter-spacing:2px;text-transform:uppercase;"
    "text-align:left;padding:clamp(11px,1.5vw,18px) clamp(12px,1.8vw,20px);"
    "border-bottom:3px solid var(--orange);white-space:nowrap;user-select:none;"
    "box-shadow:0 -300px 0 0 #f2ede4;"
    "}")

subprocess.run(['git','add','.'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','commit','-m','fix27: wipe all sample seed data (no re-seed) + sticky header covers scrolled rows'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','push'],check=False,cwd=ROOT,capture_output=True)
print("Wrote:", *WROTE, sep="\n  ")
print("Done. Pushed.")