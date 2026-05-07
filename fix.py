import os

def patch(path, old, new):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if old not in content:
        print(f"  WARNING: patch target not found in {path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"Patched: {path}")

LEDGER_CSS = "erp-frontend/src/pages/Ledger/LedgerPage.module.css"

# ── FIX 1: Table shell — small padding so rows don't touch the container edge ──
patch(LEDGER_CSS,
""".tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
}
.tableScroll::-webkit-scrollbar { height: 4px; }
.tableScroll::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 2px; }""",
""".tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Small breathing room — rows don't touch the container edges */
    padding: clamp(4px, 0.5vw, 6px) clamp(6px, 0.8vw, 10px);
}
.tableScroll::-webkit-scrollbar { height: 4px; }
.tableScroll::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 2px; }""")

# ── FIX 2: Search icon — vertically centered ──
patch(LEDGER_CSS,
""".searchIcon {
    position: absolute;
    left: clamp(10px, 1.2vw, 14px);
    color: var(--orange);
    font-size: clamp(14px, 1.5vw, 18px);
    pointer-events: none;
    flex-shrink: 0;
}""",
""".searchIcon {
    position: absolute;
    left: clamp(10px, 1.2vw, 14px);
    top: 50%;
    transform: translateY(-50%);
    color: var(--orange);
    font-size: clamp(14px, 1.5vw, 18px);
    pointer-events: none;
    flex-shrink: 0;
}""")

# ── FIX 3: Active filter style — orange bg + dark text (was dim/invisible) ──
# Previous patch already changed this but let's make sure the inactive
# buttons have a background dark enough to read on the cream page bg
patch(LEDGER_CSS,
"""/* Active/selected: orange bg + dark navy text — matches Payments "ALL TYPES" */
.activeFilter {
    background: var(--orange) !important;
    border-color: var(--orange) !important;
    color: #1a2e30 !important;
    font-weight: 900 !important;
    box-shadow: 0 2px 12px rgba(238, 140, 58, 0.35);
}""",
"""/* Active/selected: orange bg + dark navy text — same as Payments "ALL TYPES" */
.activeFilter {
    background: #EE8C3A !important;
    border-color: #EE8C3A !important;
    color: #1a2e30 !important;
    font-weight: 900 !important;
    box-shadow: 0 2px 12px rgba(238, 140, 58, 0.4);
}""")

print("All patches applied.")
print("Run: git add -A && git commit -m \"Ledger: table edge gap, search icon align, active filter orange\" && git push")