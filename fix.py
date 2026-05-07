# PATH: fix.py
import os

def rewrite_header_css(path):
    if not os.path.exists(path):
        print(f"  FILE NOT FOUND: {path}")
        return

    # This is the exact style from the Dashboard, made responsive
    UNIFIED_HEADER_CSS = """
/* --- UNIFIED HARDWARE HEADER --- */
.header {
    background: rgba(255, 255, 255, 0.62) !important;
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange) !important;
    border-radius: 0 15px 15px 0 !important;
    padding: clamp(16px, 3vw, 24px) clamp(20px, 4vw, 32px) !important;
    margin-bottom: clamp(20px, 4vw, 32px) !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    backdrop-filter: blur(15px) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07) !important;
    width: 100% !important;
    gap: 20px !important;
}

.header h1 {
    font-family: 'Cinzel', serif !important;
    font-weight: 900 !important;
    color: #213E40 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    margin: 0 !important;
    font-size: clamp(18px, 2.5vw, 28px) !important;
    line-height: 1.2 !important;
}

.header p {
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    font-size: clamp(9px, 1vw, 11px) !important;
    letter-spacing: 1.5px !important;
    margin: 4px 0 0 0 !important;
}

@media (max-width: 600px) {
    .header {
        flex-direction: column !important;
        align-items: flex-start !important;
        border-radius: 0 10px 10px 0 !important;
    }
}
"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # We remove any existing .header, .header h1, or .header p blocks to avoid duplicates
    lines = content.splitlines()
    filtered_lines = []
    skip = False
    for line in lines:
        if ".header {" in line or ".header h1 {" in line or ".header p {" in line:
            skip = True
        if not skip:
            filtered_lines.append(line)
        if skip and "}" in line:
            skip = False
    
    # Write the cleaned file + the new unified header
    new_content = "\n".join(filtered_lines) + "\n" + UNIFIED_HEADER_CSS
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  OK: Unified Header in {path}")

print("=== STARTING HEADER UNIFICATION (ALL PAGES) ===\n")

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
    rewrite_header_css(p)

print("\n=== HEADERS ALIGNED. READY TO DEPLOY. ===")