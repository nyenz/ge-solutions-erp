# PATH: fix.py
import os

def patch_file(path, patches):
    if not os.path.exists(path):
        print(f"  FILE NOT FOUND: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    for target, replacement in patches:
        content = content.replace(target, replacement)
    
    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  OK: Patched {path}")
    else:
        print(f"  NO CHANGE: {path} (targets not found)")

print("=== STARTING UI REFINEMENT PHASE ===\n")

# 1. UNIFY HEADERS (Applying Dashboard style to others)
SHARED_HEADER_CSS = """    background: rgba(255, 255, 255, 0.62);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    border-radius: 0 15px 15px 0;
    padding: 24px 32px;
    margin-bottom: 32px;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);"""

# --- Patch Ledger Header ---
patch_file("erp-frontend/src/pages/Ledger/LedgerPage.module.css", [
    (".header {", ".header {\n" + SHARED_HEADER_CSS),
    ("min-width: 140px;", "min-width: clamp(160px, 15vw, 200px);"), # Widening Plot ID col
    ("display: flex;\n    align-items: center;", "display: flex;\n    flex-direction: column;\n    gap: 4px;") # Wrap ID and Tag
])

# --- Patch Intake Header & Responsive Inputs ---
patch_file("erp-frontend/src/pages/Intake/IntakePage.module.css", [
    (".header {", ".header {\n" + SHARED_HEADER_CSS),
    ("grid-template-columns: repeat(3, 1fr);", "grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));"),
    ("width: 100%;", "width: 100% !important;") # Force responsive inputs
])

# --- Patch Audit Header & Filter Alignment ---
patch_file("erp-frontend/src/pages/Audit/AuditPage.module.css", [
    (".header {", ".header {\n" + SHARED_HEADER_CSS),
    ("display: flex;\n    gap: 20px;\n    margin-bottom: 25px;", "display: flex;\n    gap: 20px;\n    margin-bottom: 25px;\n    align-items: flex-end;\n    flex-wrap: wrap;"),
    (".resetBtn {", ".resetBtn {\n    height: 52px; /* Matches dropdown height */")
])

# --- Patch Payments Header & Horizontal Mobile Filters ---
patch_file("erp-frontend/src/pages/Payments/PaymentsPage.module.css", [
    (".header {", ".header {\n" + SHARED_HEADER_CSS),
    (".filterRow {", ".filterRow {\n    display: flex;\n    overflow-x: auto;\n    padding-bottom: 8px;\n    gap: 12px;\n    scrollbar-width: none;"),
    (".filterRow::-webkit-scrollbar { display: none; }", "")
])

# --- Patch Recovery Header & Empty State Visibility ---
patch_file("erp-frontend/src/pages/Recovery/RecoveryPortal.module.css", [
    (".header {", ".header {\n" + SHARED_HEADER_CSS),
    ("color: rgba(255, 255, 255, 0.2);", "color: var(--orange); font-weight: 900; opacity: 0.8;"), # Better contrast for "No Targets"
    (".emptyState {", ".emptyState {\n    background: rgba(33, 62, 64, 0.4);\n    padding: 60px;\n    border-radius: 20px;\n    border: 1px dashed var(--orange);")
])

# 2. SIDEBAR OPTIMIZATION (Shrinking footer and fitting content)
patch_file("erp-frontend/src/components/layout/Sidebar.module.css", [
    (".sidebar {", ".sidebar {\n    height: 100vh;\n    overflow-y: hidden;"),
    (".nav {", ".nav {\n    flex: 1;\n    overflow-y: auto;\n    padding: 10px 0;"),
    (".footer {", ".footer {\n    padding: 10px 20px;\n    border-top: 1px solid rgba(255,255,255,0.05);"),
    (".brand {", ".brand {\n    font-size: 10px !important;\n    letter-spacing: 2px;"),
    (".version {", ".version {\n    font-size: 8px !important; opacity: 0.5;")
])

# 3. GLOBAL INPUT RESPONSIVENESS
patch_file("erp-frontend/src/index.css", [
    ("input, select, textarea {", "input, select, textarea {\n    max-width: 100%;\n    width: 100%;")
])

print("\n=== UI REFINEMENT COMPLETE ===")