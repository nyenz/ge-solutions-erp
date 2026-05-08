import os

def patch_file(path, old_str, new_str, label):
    if not os.path.exists(path):
        print(f"  MISSING FILE: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Normalize line endings
    content = content.replace("\r\n", "\n")
    old_str = old_str.replace("\r\n", "\n")
    
    if old_str in content:
        content = content.replace(old_str, new_str, 1)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"  OK: {label}")
    else:
        print(f"  SKIP/NOT FOUND: {label}")

def append_file(path, text, label):
    if not os.path.exists(path):
        print(f"  MISSING FILE: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if text.strip() not in content:
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write("\n" + text + "\n")
        print(f"  OK: {label}")
    else:
        print(f"  ALREADY APPLIED: {label}")

print("\nExecuting Final UI Polish Fixes...")

# 1. FIX INDEX.CSS PADDING OVERRIDE (Solves Search Text Overlap)
patch_file(
    "erp-frontend/src/index.css",
    "padding-left: var(--input-px) !important;",
    "padding-left: var(--input-px);",
    "Removed !important from global input left padding"
)
patch_file(
    "erp-frontend/src/index.css",
    "padding-right: var(--input-px) !important;",
    "padding-right: var(--input-px);",
    "Removed !important from global input right padding"
)

search_fix = """
/* --- GLOBAL SEARCH ICON CLEARANCE --- */
[class*="searchInput"] {
    text-indent: 26px !important;
}
[class*="searchInputActive"] {
    text-indent: 0px !important;
}
"""
append_file("erp-frontend/src/index.css", search_fix, "Injected text-indent safety for all Search Inputs")

# 2. AUDIT FILTERS - Align design with Payments Pills
audit_css = """
/* --- PILL STYLE OVERRIDES FOR UNIFORMITY --- */
.hwSelectWrap [class*="selectBox"] {
    border-radius: 20px !important;
    background: transparent !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.8) !important;
}
.hwSelectWrap [class*="selectBox"]:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.35) !important;
    color: #fff !important;
}
.resetBtn {
    border-radius: 20px !important;
    background: transparent !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.8) !important;
}
.resetBtn:hover {
    background: rgba(238, 140, 58, 0.12) !important;
    border-color: #EE8C3A !important;
    color: #EE8C3A !important;
}
"""
append_file("erp-frontend/src/pages/Audit/AuditPage.module.css", audit_css, "Styled Audit dropdowns and buttons as uniform Pills")

# 3. DROPDOWN RESPONSIVENESS - Make it scrollable and capped height
dropdown_css = """
/* --- DROPDOWN RESPONSIVENESS --- */
.dropdown {
    max-height: 250px;
    overflow-y: auto;
}
.dropdown::-webkit-scrollbar { width: 4px; }
.dropdown::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }
@media (max-width: 480px) {
    .dropdown { max-height: 200px; }
    .option { padding: 10px 14px; font-size: 12px; }
}
"""
append_file("erp-frontend/src/components/common/HardwareSelect.module.css", dropdown_css, "Added scrolling to long Dropdown menus")

# 4. PAYMENTS TABLE MOBILE ALIGNMENT
payments_css = """
/* --- MOBILE TABLE RE-ALIGNMENT --- */
@media (max-width: 480px) {
    .tableScroll { 
        margin: -10px; 
        margin-bottom: 0; 
        border-radius: 0; 
        padding-bottom: 10px;
    }
    .ledgerTable th, .ledgerTable td { 
        font-size: 8.5px !important; 
        padding: 8px 6px !important; 
        white-space: nowrap; 
    }
}
"""
append_file("erp-frontend/src/pages/Payments/PaymentsPage.module.css", payments_css, "Aligned Payments mobile table layout with Ledger")

# 5. SIDEBAR ENLARGEMENT
sidebar_css = """
/* --- SIDEBAR LINK SIZE UPGRADE --- */
.navLink {
    font-size: clamp(11.5px, 1.4vw, 14px) !important;
    padding: clamp(10px, 1.5vw, 14px) clamp(16px, 2vw, 20px) !important;
    margin-bottom: 6px !important;
}
.navIcon {
    font-size: clamp(16px, 1.8vw, 20px) !important;
}
@media (max-height: 700px) {
    .navLink { padding: 8px 16px !important; margin-bottom: 2px !important; }
}
"""
append_file("erp-frontend/src/components/layout/Sidebar.module.css", sidebar_css, "Enlarged Sidebar navigation links")