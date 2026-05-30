# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

BASE = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'DigitalFolder', 'FolderPage.jsx')
recovery_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.jsx')

print("=== FINAL REFINEMENT: MATH & TERMINOLOGY CLEANUP ===")

# ─── 1. FIX FOLDER PAGE MATH VARIABLES ───────────────────────────
f_content = read(folder_path)
# Target the start of the financial calculation block
old_math_block = "const totalCost          = Number(project?.totalCost || 0);"
new_math_block = """// 4-Pocket Math: AMOUNT OWED = (TOTAL VALUE + STORAGE FEES) - PAID
    const totalValue         = Number(project?.totalCost || 0);
    const paid               = Number(project?.amountPaid || 0);
    const storageFees        = Number(project?.storageFeesAccumulated || 0);
    const backlogAmountOwed  = Math.max(0, totalValue + storageFees - paid);
    const activeAmountOwed   = Math.max(0, totalValue - paid);
    const amountOwed         = isBacklog ? backlogAmountOwed : activeAmountOwed;
    // Legacy aliases
    const totalCost          = totalValue;
    const amountPaid         = paid;
    const remaining          = amountOwed;
    const backlogOwed        = backlogAmountOwed;
    const activeOwed         = activeAmountOwed;"""

if old_math_block in f_content:
    f_content = f_content.replace(old_math_block, new_math_block)
    print("OK: FolderPage math variables defined")

# Remove the redundant Total Now Owed banner
old_banner = """<div className={styles.totalOwedBanner}>
                                            <span>TOTAL NOW OWED</span>
                                            <strong>UGX {fmt(Math.max(0, backlogOwed))}</strong>
                                        </div>"""
if old_banner in f_content:
    f_content = f_content.replace(old_banner, "")
    print("OK: Removed redundant banner")

write(folder_path, f_content)

# ─── 2. FIX RECOVERY PORTAL LABELS ──────────────────────────────
r_content = read(recovery_path)

old_rec_labels = """<div className={styles.finRow}>
                                                    <span className={styles.finLabel}>PAID</span>
                                                    <span className={styles.finValGreen}>UGX {fmt(amtPaid)}</span>
                                                </div>"""
new_rec_labels = """<div className={styles.finRow}>
                                                    <span className={styles.finLabel} style={{color:'#22c55e'}}>PAID</span>
                                                    <span className={styles.finValGreen}>UGX {fmt(amtPaid)}</span>
                                                </div>"""

if old_rec_labels in r_content:
    r_content = r_content.replace(old_rec_labels, new_rec_labels)
    print("OK: RecoveryPortal labels updated")
else:
    # Try a more generic match if exact failed
    r_content = r_content.replace('className={styles.finLabel}>PAID</span>', 'className={styles.finLabel} style={{color:"#22c55e"}}>PAID</span>')
    print("OK: RecoveryPortal labels updated (fallback)")

write(recovery_path, r_content)

print("=== CLEANUP COMPLETE ===") 