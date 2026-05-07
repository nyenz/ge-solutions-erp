# PATH: fix.py
import os

def rewrite_styles(path):
    if not os.path.exists(path):
        return

    # THE DASHBOARD STANDARD
    NEW_STYLES = """
/* --- DASHBOARD HEADER STANDARD --- */
.header {
    background: rgba(255, 255, 255, 0.62) !important;
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange) !important;
    border-radius: 0 15px 15px 0 !important;
    padding: 24px 32px !important;
    margin-bottom: 32px !important;
    backdrop-filter: blur(15px) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07) !important;
    display: grid !important;
    grid-template-areas: 
        "title action"
        "subtitle action" !important;
    grid-template-columns: 1fr auto !important;
    align-items: center !important;
    gap: 0 20px !important;
}

.header h1 {
    grid-area: title !important;
    font-family: 'Cinzel', serif !important;
    font-weight: 900 !important;
    color: #213E40 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    margin: 0 !important;
    font-size: clamp(20px, 2.5vw, 28px) !important;
}

.header p {
    grid-area: subtitle !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    margin: 6px 0 0 0 !important;
}

/* Any buttons or sync text go to the right area */
.header button, .header span, .header .metaGroup {
    grid-area: action !important;
}

/* --- DASHBOARD SUBHEADING STANDARD --- */
/* Matches "PIPELINE BOTTLENECKS" and "FINANCIAL LIQUIDITY" */
.sectionTitle, .plotDetailsTitle, h3, h4 {
    color: var(--orange) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    margin-bottom: 20px !important;
}

@media (max-width: 768px) {
    .header {
        grid-template-areas: "title" "subtitle" "action" !important;
        grid-template-columns: 1fr !important;
        padding: 20px !important;
    }
    .header p { margin-bottom: 15px !important; }
}
"""

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Clean up old header styles before adding the new unified block
    lines = content.splitlines()
    filtered = []
    skip = False
    for line in lines:
        if any(x in line for x in [".header {", ".header h1", ".header p", ".sectionTitle", "h3 {"]):
            skip = True
        if not skip: filtered.append(line)
        if skip and "}" in line: skip = False
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered) + "\n" + NEW_STYLES)
    print(f"  OK: Unified style in {path}")

print("=== CONFORMING ALL PAGES TO DASHBOARD STANDARD ===\n")

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
    rewrite_styles(p)

print("\n=== SYSTEM ALIGNED. READY TO DEPLOY. ===")