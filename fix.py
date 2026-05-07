# PATH: fix.py
import os

def patch_ledger_column():
    path = "erp-frontend/src/pages/Ledger/LedgerPage.module.css"
    if not os.path.exists(path):
        print(f"  FILE NOT FOUND: {path}")
        return

    # NEW STYLES: Stacked layout for the Plot ID column
    PLOT_COLUMN_FIX = """
/* --- FIXED PLOT ID COLUMN --- */
.plotCell {
    min-width: clamp(140px, 12vw, 180px) !important;
    padding: 15px 20px !important;
    vertical-align: top !important;
}

.plotIdGroup {
    display: flex !important;
    flex-direction: column !important; /* Stack vertically */
    align-items: flex-start !important;
    gap: 6px !important; /* Gap between ID and Tags */
}

.plotNumber {
    font-weight: 800 !important;
    color: var(--orange) !important;
    font-size: 15px !important;
    letter-spacing: 1px !important;
    display: block !important;
}

.tagRow {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 4px !important;
}

.tenureTag, .districtTag {
    font-size: 10px !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    text-transform: uppercase !important;
    font-weight: 900 !important;
    white-space: nowrap !important;
}

.tenureTag {
    background: rgba(238, 140, 58, 0.2) !important;
    color: var(--orange) !important;
    border: 1px solid rgba(238, 140, 58, 0.3) !important;
}

.districtTag {
    background: rgba(255, 255, 255, 0.1) !important;
    color: rgba(255, 255, 255, 0.7) !important;
}
"""

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove old classes that might conflict
    lines = content.splitlines()
    filtered_lines = []
    skip = False
    targets = [".plotCell {", ".plotIdGroup {", ".plotNumber {", ".tenureTag {", ".districtTag {"]
    
    for line in lines:
        if any(t in line for t in targets):
            skip = True
        if not skip:
            filtered_lines.append(line)
        if skip and "}" in line:
            skip = False

    new_content = "\n".join(filtered_lines) + "\n" + PLOT_COLUMN_FIX

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  OK: Fixed Ledger Plot Column in {path}")

print("=== FIXING LEDGER TABLE COLUMN JAM ===\n")
patch_ledger_column()
print("\n=== COLUMN WIDENED. READY TO DEPLOY. ===")