import os
import re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

print("=== STARTING RECOVERY & UI POLISH FIXES ===")

# ============================================================
# 1. RECOVERY PORTAL FIXES
# ============================================================
path_rec = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
content_rec = read(path_rec)

# FIX A: Java's Jackson parser drops the "is" from booleans during JSON serialization. 
# We update the filter logic so the frontend correctly checks for `p.backlog`.
content_rec = re.sub(r'\bp\.isBacklog\b', r'(p.isBacklog || p.backlog)', content_rec)
content_rec = re.sub(r'\bplot\.isBacklog\b', r'(plot.isBacklog || plot.backlog)', content_rec)

# FIX B: Completely obliterate the INSTALMENT button from the JSX.
content_rec = re.sub(
    r'\{\s*isAdmin\s*&&\s*\(\s*<button\s+className=\{styles\.payBtnMonthly\}[\s\S]*?INSTALMENT\s*</button>\s*\)\s*\}', 
    '', 
    content_rec
)

# FIX C: Strip out the BACKLOG tag from the owner's name.
content_rec = re.sub(
    r'\{\s*mission\.hasBacklogPlots\s*&&\s*\(\s*<span\s+className=\{styles\.backlogOwnerTag\}>[\s\S]*?</span>\s*\)\s*\}', 
    '', 
    content_rec
)

write(path_rec, content_rec)


# ============================================================
# 2. FOLDER PAGE CSS FIXES (Curved Sticky Headers)
# ============================================================
path_css = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
content_css = read(path_css)

# Inject border-radius into the sticky Financials header
if "border-radius: 10.5px" not in content_css:
    content_css = re.sub(
        r'(\.finPanelHeader\s*\{[^}]*)(\})', 
        r'\1    border-radius: 10.5px 10.5px 0 0;\n\2', 
        content_css
    )

    # Inject border-radius into the sticky Drawer header
    content_css = re.sub(
        r'(\.drawerHeader\s*\{[^}]*)(\})', 
        r'\1    border-radius: 10.5px 10.5px 0 0;\n\2', 
        content_css
    )

write(path_css, content_css)

print("\n=== RECOVERY LOGIC & FOLDER STYLES FIXED SUCCESSFULLY ===")
print("Run: git add -A && git commit -m 'fix: plot backlog mapping, remove instalment btn, and curve sticky headers' && git push")