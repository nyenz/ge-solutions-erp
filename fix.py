# PATH: fix.py
import os

def append_to_file(path, text):
    if not os.path.exists(path):
        print(f"  FILE NOT FOUND: {path}")
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + text + "\n")
    print(f"  OK: Appended to {path}")

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
        print(f"  NO CHANGE: {path}")

print("=== FINALIZING RESPONSIVENESS & CONTRAST ===\n")

# 1. GLOBAL INPUT RESPONSIVENESS (Append to index.css)
append_to_file("erp-frontend/src/index.css", """
/* Force all inputs and selects to fill their hardware containers */
input, select, textarea, .HardwareSelect_selectBox__xxxx {
    width: 100% !important;
    box-sizing: border-box;
}
""")

# 2. AUDIT PAGE MOBILE STACKING
patch_file("erp-frontend/src/pages/Audit/AuditPage.module.css", [
    ("align-items: flex-end;", "align-items: flex-end;"), # Ensure baseline
    (".resetBtn {", """@media (max-width: 600px) {
    .filters { flex-direction: column; width: 100%; gap: 10px; }
    .filters > div, .resetBtn { width: 100% !important; }
}
.resetBtn {""")
])

# 3. INTAKE PAGE GRID COLLAPSE
patch_file("erp-frontend/src/pages/Intake/IntakePage.module.css", [
    ("grid-template-columns: repeat(3, 1fr);", "grid-template-columns: repeat(3, 1fr);"), # Anchor
    (".grid {", """.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}
@media (max-width: 1000px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
.grid_hidden {""") # Note: we just insert the media query logic here
])

# 4. RECOVERY CONTRAST BOOST
patch_file("erp-frontend/src/pages/Recovery/RecoveryPortal.module.css", [
    ("background: rgba(33, 62, 64, 0.4);", "background: rgba(10, 20, 25, 0.8);"), # Darker bg
    ("border: 1px dashed var(--orange);", "border: 2px dashed var(--orange); box-shadow: 0 0 20px rgba(238, 140, 58, 0.15);")
])

# 5. SIDEBAR FOOTER FIX (Avoid scroll)
patch_file("erp-frontend/src/components/layout/Sidebar.module.css", [
    ("padding: 10px 20px;", "padding: 5px 15px;"), # Tighten footer
    ("font-size: 10px !important;", "font-size: 9px !important;"), # Smaller Nyenz
    ("font-size: 8px !important;", "font-size: 7px !important;")   # Tiny version
])

print("\n=== ALL UI PATCHES APPLIED ===")