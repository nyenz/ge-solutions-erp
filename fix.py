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

print("=== STARTING RECOVERY UI & NAVIGATION FIXES ===")

# ============================================================
# 1. RECOVERY PORTAL FIXES
# ============================================================
path_recovery = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
content_rec = read(path_recovery)

# FIX A: Remove the [BACKLOG] tag from next to the Owner's Name
content_rec = re.sub(
    r'\{\s*mission\.hasBacklogPlots\s*&&\s*\(\s*<span\s+className=\{styles\.backlogOwnerTag\}>[\s\S]*?</span>\s*\)\s*\}', 
    '', 
    content_rec
)

# FIX B: Remove the "INSTALMENT" button completely
content_rec = re.sub(
    r'\{\s*isAdmin\s*&&\s*\(\s*<button[^>]+payBtnMonthly[\s\S]*?INSTALMENT\s*</button>\s*\)\s*\}', 
    '', 
    content_rec
)

# FIX C: Map the "PAY" buttons directly to the ?action=pay url hook
content_rec = re.sub(
    r'onClick=\{\(\)\s*=>\s*navigate\(`\/folder/\$\{plot\.projectId\}[^`]*`\)\}(\s*>\s*<(FiDollarSign|FiZap))', 
    r'onClick={() => navigate(`/folder/${plot.projectId}?action=pay#financials`)}\1', 
    content_rec
)

write(path_recovery, content_rec)


# ============================================================
# 2. FOLDER PAGE FIXES (To Auto-Open the Modal)
# ============================================================
path_folder = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
content_fol = read(path_folder)

# Inject useLocation into imports if missing
if "useLocation" not in content_fol:
    content_fol = re.sub(r'import\s+\{([^}]*useNavigate[^}]*)\}\s+from\s+[\'"]react-router-dom[\'"];', r"import {\1, useLocation } from 'react-router-dom';", content_fol)

# Define location variable if missing
if "location = useLocation()" not in content_fol:
    content_fol = content_fol.replace("const navigate = useNavigate();", "const navigate = useNavigate();\n    const location = useLocation();")

# Inject the trigger logic to auto-open the Payment Modal when routed from Recovery
if "?action=pay" not in content_fol and "action === 'pay'" not in content_fol:
    trigger_code = """
    // Auto-open payment modal when routed directly from Recovery Portal
    useEffect(() => {
        if (!binder) return;
        const params = new URLSearchParams(location.search);
        if (params.get('action') === 'pay') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                setPayModal({ open: true });
                setPayAmount('');
                setPayNotes('');
            }, 300);
        }
    }, [location.search, binder]);
"""
    content_fol = content_fol.replace("useEffect(() => { loadFolderData(); }, [loadFolderData]);", "useEffect(() => { loadFolderData(); }, [loadFolderData]);\n" + trigger_code)

write(path_folder, content_fol)


# ============================================================
# 3. CSS FIXES (ONLY the Tab bar is sticky)
# ============================================================
path_css = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
content_css = read(path_css)

# Strip stickiness from pipelineHUD
content_css = re.sub(r'(?<=pipelineHUD \{)([\s\S]*?)position:\s*sticky;[\s\S]*?-webkit-backdrop-filter:[^;]+;', r'\1', content_css)

# Strip stickiness from terminalHeader 
content_css = re.sub(r'(?<=terminalHeader \{)([\s\S]*?)position:\s*sticky;[\s\S]*?z-index:\s*49;', r'\1', content_css)

# Remove any rogue scroll margins
content_css = re.sub(r'scroll-margin-top:\s*clamp[^;]+;', '', content_css)
content_css = re.sub(r'scroll-margin-top:\s*\d+px;', '', content_css)

# Apply sticky ONLY to tabBar
content_css = re.sub(r'\.tabBar\s*\{[^}]*\}', 
'''.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 8px;
    padding-top: 8px;
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: -10px; /* Sticks to the very top */
    z-index: 100;
    background: rgba(244, 242, 239, 0.98);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-radius: 0 0 8px 8px;
}''', content_css)

# Offset scroll-margin so jumping to the payment section doesn't hide behind tabs
content_css = re.sub(r'(\.hwPanel\s*\{[^}]*)', r'\1\n    scroll-margin-top: 60px;', content_css)
content_css = re.sub(r'(scroll-margin-top:\s*60px;\s*){2,}', 'scroll-margin-top: 60px;\n', content_css)

write(path_css, content_css)

print("\n=== ALL FIXES APPLIED VIA REGEX ===")
print("Run: git add -A && git commit -m 'fix: recovery layout, payment router, and sticky tabs' && git push")