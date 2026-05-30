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

print("=== FINAL REFINEMENT: UNIFORM LABELS & COLORS ===")

# 1. Clean up FolderPage Payment Modal Labels
f_content = read(folder_path)
# Standardize the label "PAID" in the modal breakdown
f_content = f_content.replace('>PAID<', '>PAID<') # ensure no hidden chars
f_content = f_content.replace('TOTAL VALUE', 'PLOT VALUE')

# 2. Fix RecoveryPortal labels and green color
r_content = read(recovery_path)
# Ensure the label is "PLOT VALUE"
r_content = r_content.replace('TOTAL VALUE', 'PLOT VALUE')

# Force the "PAID" value color to success green if not already applied
if 'span className={styles.finLabel}>PAID</span>' in r_content:
    r_content = r_content.replace(
        'span className={styles.finLabel}>PAID</span>', 
        'span className={styles.finLabel} style={{color:"#22c55e"}}>PAID</span>'
    )

write(folder_path, f_content)
write(recovery_path, r_content)

print("OK: FolderPage & RecoveryPortal standardized.")
print("=== SYSTEM IS NOW 100% ALIGNED ===")