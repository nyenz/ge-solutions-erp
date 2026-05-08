import os

def patch(path, old, new, label=""):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    # Normalize line endings to avoid Git Bash Windows/Unix mismatch issues
    content = content.replace("\r\n", "\n")
    old = old.replace("\r\n", "\n")
    
    if old not in content:
        print(f"  MISSING: {label or path}")
        return
        
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label or path}")

css_path = "erp-frontend/src/pages/Audit/AuditPage.module.css"

old_filterGrid = """.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: visible;
    scrollbar-width: none;
    width: 100%;
    padding-bottom: 4px;
    padding-top: 4px;
    position: relative;
    z-index: 9000;
    isolation: isolate;
}"""

new_filterGrid = """.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: wrap;
    overflow: visible;
    width: 100%;
    padding-bottom: 4px;
    padding-top: 4px;
    position: relative;
    z-index: 9000;
}"""

old_hwSelectWrap = """.hwSelectWrap {
    flex: 0 0 auto;
    width: clamp(130px, 16vw, 200px);
    min-width: 0;
    position: relative;
    z-index: 9000;
    overflow: visible !important;
}"""

new_hwSelectWrap = """.hwSelectWrap {
    flex: 1 1 140px;
    max-width: 240px;
    min-width: 120px;
    position: relative;
    z-index: 9000;
    overflow: visible !important;
}"""

print("Applying final Audit CSS fixes...")
patch(css_path, old_filterGrid, new_filterGrid, "Fix filterGrid overflow and wrapping (desktop)")
patch(css_path, old_hwSelectWrap, new_hwSelectWrap, "Fix hwSelectWrap flexibility (desktop)")