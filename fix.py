import os
import re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

print("=== STARTING ROBUST REGEX FIXES ===")

# ============================================================
# 1. RECOVERY PORTAL - Navigation & Text Fixes
# ============================================================
path_recovery = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
content_rec = read(path_recovery)

# Regex to forcefully rewrite the "PAY" title button navigation
content_rec = re.sub(
    r"navigate\(\`/folder/\$\{plot\.projectId\}(#record-payment|#storage-fees|#financials)`\)(.*?)<FiDollarSign", 
    r"navigate(`/folder/${plot.projectId}?action=pay#financials`)\g<2><FiDollarSign", 
    content_rec, flags=re.DOTALL
)

# Regex to forcefully rewrite the "INSTALMENT" button navigation
content_rec = re.sub(
    r"navigate\(\`/folder/\$\{plot\.projectId\}(#record-payment|#storage-fees|#financials)`\)(.*?)<FiRepeat", 
    r"navigate(`/folder/${plot.projectId}?action=storage#financials`)\g<2><FiRepeat", 
    content_rec, flags=re.DOTALL
)

# Regex to forcefully rewrite the "BACKLOG PAY" button navigation
content_rec = re.sub(
    r"navigate\(\`/folder/\$\{plot\.projectId\}(#record-payment|#storage-fees|#financials)`\)(.*?)<FiZap", 
    r"navigate(`/folder/${plot.projectId}?action=pay#financials`)\g<2><FiZap", 
    content_rec, flags=re.DOTALL
)

# Text cleanup in Recovery Portal
content_rec = content_rec.replace("CALL LOGGED — 14-DAY CLOCK RESET", "Call logged. 14-day timer reset.")
content_rec = content_rec.replace("DATA STREAM LOST", "Failed to load recovery data")

write(path_recovery, content_rec)


# ============================================================
# 2. FOLDER PAGE JSX - Hooks & Text Formatting
# ============================================================
path_folder = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
content_fol = read(path_folder)

# Ensure useLocation is imported
if "useLocation" not in content_fol:
    content_fol = content_fol.replace("useNavigate }", "useNavigate, useLocation }")

if "const location = useLocation()" not in content_fol:
    content_fol = content_fol.replace("const navigate = useNavigate();", "const navigate = useNavigate();\n    const location = useLocation();")

# Text replacements (safe to run multiple times, won't crash if already applied)
text_replacements = [
    ("toast('STAGE SET: ' + STAGE_LABELS[num-1], 'info', 3000)", "toast('Stage updated: ' + STAGE_LABELS[num-1], 'info', 3000)"),
    ("toast('INTERACTION LOGGED', 'success', 3000)", "toast('Note saved', 'success', 3000)"),
    ("toast('NOTE DELETED', 'warn', 3000)", "toast('Note deleted', 'warn', 3000)"),
    ("toast('DOCUMENT REMOVED', 'warn', 3000)", "toast('Document removed', 'warn', 3000)"),
    ("toast('PAYMENT RECORDED', 'success')", "toast('Payment recorded successfully', 'success')"),
    ("toast('PLOT MOVED TO BACKLOG — STORAGE FEES NOW ACTIVE', 'warn')", "toast('Plot moved to backlog. Storage fees are now active.', 'warn')"),
    ("toast('PLOT REMOVED FROM BACKLOG', 'success')", "toast('Plot removed from backlog', 'success')"),
    ("toast('ARCHIVE REWRITTEN SUCCESSFULLY', 'success')", "toast('Changes saved successfully', 'success')"),
    ("toast(files.length + ' DOCUMENT(S) INGESTED', 'success', 3000)", "toast(files.length + ' document(s) uploaded', 'success', 3000)"),
    ("toast('ASSET PURGED', 'warn', 3000)", "toast('Record permanently deleted', 'warn', 3000)"),
    ("toast('PURGE REJECTED', 'error')", "toast('Delete failed', 'error')"),
    ("BACKLOG CONTROLS", "BACKLOG MANAGEMENT"),
    (">REAL-TIME TRACKING ACTIVE<", ">LIVE STATUS<"),
    ("COMMIT &amp; RESET CLOCK", "LOG CALL &amp; RESET CLOCK")
]

for old_text, new_text in text_replacements:
    content_fol = content_fol.replace(old_text, new_text)

write(path_folder, content_fol)


# ============================================================
# 3. FOLDER PAGE CSS - Force TabBar & Sticky UI overrides
# ============================================================
path_css = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
content_css = read(path_css)

# Forcefully overwrite the entire .tabBar block, erasing any previous messed up versions
content_css = re.sub(r'\.tabBar\s*\{[^}]*\}', 
'''.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 4px;
    padding-top: clamp(6px, 0.8vw, 10px);
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: clamp(100px, 16vw, 136px);
    z-index: 48;
    background: rgba(244, 242, 239, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 0 0 var(--radius-sm) var(--radius-sm);
    padding-left: 2px;
    padding-right: 2px;
}''', content_css)

# Ensure Desktop/Mobile Tab logic is correctly placed before media queries
if ".tabFull  { display: inline; }" not in content_css:
    content_css = re.sub(r'@media\s*\(\s*max-width:\s*600px\s*\)\s*\{',
    '''/* ── TAB BAR - desktop: show full, mobile: show short ── */
.tabFull  { display: inline; }
.tabShort { display: none; }

@media (max-width: 600px) {''', content_css, count=1)

# Remove the broken mobile .tabBar overrides from the other script
content_css = re.sub(r'\.tabBar\s*\{\s*top:\s*[^}]*\}', '.tabBar { padding-left: 15px; padding-right: 15px; }', content_css)

write(path_css, content_css)

print("\n=== ALL FIXES APPLIED VIA REGEX ===")
print("Run: git add -A && git commit -m 'fix: force recovery routing and sticky layouts' && git push")