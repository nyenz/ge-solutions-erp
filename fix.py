# PATH: fix.py
import os

def force_master_style(path):
    if not os.path.exists(path): return

    # THE ABSOLUTE MASTER HEADER STYLE (Matching Dashboard exactly)
    MASTER_CSS = """
/* --- MASTER HARDWARE HEADER (DASHBOARD ALIGNMENT) --- */
.header {
    background: rgba(255, 255, 255, 0.62) !important;
    border-left: clamp(4px, 0.5vw, 6px) solid var(--orange) !important;
    border-radius: 0 15px 15px 0 !important;
    padding: clamp(16px, 4vw, 24px) clamp(20px, 5vw, 32px) !important;
    margin-bottom: 32px !important;
    backdrop-filter: blur(15px) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07) !important;
    display: flex !important;
    flex-direction: column !important; /* Forces Stacked Layout */
    align-items: flex-start !important;
    justify-content: center !important;
    width: 100% !important;
    position: relative !important;
    min-height: 100px !important;
}

.header h1 {
    font-family: 'Cinzel', serif !important;
    font-weight: 900 !important; /* MAX THICKNESS */
    color: #213E40 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.1 !important;
    /* Responsive sizing: gets smaller on mobile automatically */
    font-size: clamp(18px, 6vw, 28px) !important; 
}

.header p {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 900 !important; /* Heavy Subtitle */
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    margin: 8px 0 0 0 !important;
    padding: 0 !important;
    font-size: clamp(9px, 3vw, 11px) !important;
}

/* Fix for right-side buttons (Sync/Refresh) to stay out of the way */
.header button, .header .syncInfo {
    position: absolute !important;
    right: 20px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
}

@media (max-width: 600px) {
    .header { padding: 15px 20px !important; min-height: 80px !important; }
    .header button { position: static !important; margin-top: 10px !important; transform: none !important; }
}
"""

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Clean out ALL existing header-related CSS
    lines = content.splitlines()
    clean_lines = []
    skip = False
    for line in lines:
        if any(x in line for x in [".header {", ".header h1", ".header p"]):
            skip = True
        if not skip: clean_lines.append(line)
        if skip and "}" in line: skip = False

    # Insert the Master Style
    final_content = "\n".join(clean_lines) + "\n" + MASTER_CSS
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"  OK: Master Alignment applied to {path}")

# --- Special fix for Recovery Portal buttons ---
def fix_recovery_buttons():
    path = "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css"
    if not os.path.exists(path): return
    
    RECOVERY_BTN_FIX = """
.controlTabs {
    display: flex !important;
    flex-wrap: wrap !important; /* Allows wrap on tiny screens */
    gap: 10px !important;
    margin-bottom: 20px !important;
}
.tabBtn {
    flex: 1 !important; /* Equal width buttons */
    min-width: 140px !important;
    white-space: nowrap !important;
}
"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(RECOVERY_BTN_FIX)
    print(f"  OK: Recovery Buttons fixed.")

print("=== STARTING HEAVY-WEIGHT UI ALIGNMENT ===\n")

pages = [
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    "erp-frontend/src/pages/Intake/IntakePage.module.css",
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",
    "erp-frontend/src/pages/Reports/ReportHub.module.css",
    "erp-frontend/src/pages/settings/SettingsPage.module.css",
    "erp-frontend/src/pages/DigitalFolder/FolderPage.module.css"
]

for p in pages:
    force_master_style(p)

fix_recovery_buttons()

print("\n=== SYSTEM ALIGNED. HEADERS ARE NOW HEAVY & RESPONSIVE. ===")