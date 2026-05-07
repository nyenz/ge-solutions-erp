# PATH: fix.py
import os

# The unified style for all filter buttons
UNIFIED_CSS = """
.filterBtn {
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    padding: 8px 16px;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}

.filterBtn:hover {
    background: rgba(238, 140, 58, 0.12) !important;
    color: #EE8C3A !important;
    border-color: var(--orange) !important;
}

.filterActive {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    box-shadow: 0 0 15px rgba(238, 140, 58, 0.4) !important;
}
"""

def update_css(path):
    if not os.path.exists(path):
        print(f"  FILE NOT FOUND: {path}")
        return
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    inside_old_filter = False
    
    for line in lines:
        # Check if we are starting a block we want to replace
        if ".filterBtn {" in line or ".filterBtn:hover" in line or ".filterActive {" in line:
            inside_old_filter = True
            continue
        
        # If we were inside a block, wait for the closing brace
        if inside_old_filter:
            if "}" in line:
                inside_old_filter = False
            continue
            
        new_lines.append(line)
    
    # Append the new unified styles at the end of the file
    final_content = "".join(new_lines) + "\n" + UNIFIED_CSS
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"  OK: Updated {path}")

print("=== UNIFYING FILTER STYLES ===")
update_css("erp-frontend/src/pages/Ledger/LedgerPage.module.css")
update_css("erp-frontend/src/pages/Payments/PaymentsPage.module.css")
print("=== FINISHED ===")