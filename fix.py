import os
import re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

print("=== STARTING MATHEMATICAL & UI CLEANUP FIXES ===")

# ============================================================
# 1. FIX BACKEND MATH (LandProject.java)
# ============================================================
path_land = 'erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java'
content_land = read(path_land)

# Swap originalDebt for totalCost in the backlog calculation
content_land = re.sub(
    r'BigDecimal base = originalDebt != null \? originalDebt : BigDecimal\.ZERO;',
    r'BigDecimal base = totalCost != null ? totalCost : BigDecimal.ZERO;',
    content_land
)
write(path_land, content_land)


# ============================================================
# 2. FIX BACKEND CONTROLLER (RecoveryController.java)
# ============================================================
path_rec_ctrl = 'erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java'
content_rec_ctrl = read(path_rec_ctrl)

content_rec_ctrl = re.sub(
    r'BigDecimal origDebt = plot\.getOriginalDebt\(\) != null\s*\n?\s*\?\s*plot\.getOriginalDebt\(\) : BigDecimal\.ZERO;',
    r'BigDecimal origDebt = plot.getTotalCost() != null ? plot.getTotalCost() : BigDecimal.ZERO;',
    content_rec_ctrl
)
write(path_rec_ctrl, content_rec_ctrl)


# ============================================================
# 3. FIX BACKEND REPORTS (ReportService.java)
# ============================================================
path_rep = 'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java'
content_rep = read(path_rep)

content_rep = re.sub(
    r'java\.math\.BigDecimal origDebt = p\.getOriginalDebt\(\) != null \? p\.getOriginalDebt\(\) : java\.math\.BigDecimal\.ZERO;',
    r'java.math.BigDecimal origDebt = p.getTotalCost() != null ? p.getTotalCost() : java.math.BigDecimal.ZERO;',
    content_rep
)
content_rep = content_rep.replace('ORIGINAL_DEBT,STORAGE_FEES_UGX', 'TITLE_COST_UGX,STORAGE_FEES_UGX')
write(path_rep, content_rep)


# ============================================================
# 4. FIX RECOVERY PORTAL UI (RecoveryPortal.jsx)
# ============================================================
path_rec_ui = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
content_rec_ui = read(path_rec_ui)

content_rec_ui = re.sub(
    r'<span className=\{styles\.bfbLabel\}>ORIGINAL TITLE DEBT</span>\s*<span className=\{styles\.bfbVal\}>UGX \{fmt\(plot\.originalDebt\)\}</span>',
    r'<span className={styles.bfbLabel}>TITLE COST</span>\n                                                    <span className={styles.bfbVal}>UGX {fmt(plot.totalCost)}</span>',
    content_rec_ui
)

content_rec_ui = re.sub(
    r'UGX \{fmt\(Math\.max\(0,\s*plot\.totalBacklogOwed\)\)\}',
    r'UGX {fmt(Math.max(0, (plot.totalCost || 0) + (plot.storageFeesAccumulated || 0) - (plot.amountPaid || 0)))}',
    content_rec_ui
)

content_rec_ui = re.sub(
    r'<span className=\{styles\.finPillLabel\}>BACKLOG DEBT</span>\s*<span className=\{styles\.finPillVal\}>UGX \{fmt\(backlogPlots\.reduce\(\(s,p\) => s \+ Number\(p\.originalDebt \|\| 0\), 0\)\)\}</span>',
    r'<span className={styles.finPillLabel}>BACKLOG DEBT</span>\n                                        <span className={styles.finPillVal}>UGX {fmt(backlogPlots.reduce((s,p) => s + Number(p.totalCost || 0) + Number(p.storageFeesAccumulated || 0) - Number(p.amountPaid || 0), 0))}</span>',
    content_rec_ui
)
write(path_rec_ui, content_rec_ui)


# ============================================================
# 5. FIX FOLDER PAGE UI (FolderPage.jsx)
# ============================================================
path_fol = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
content_fol = read(path_fol)

content_fol = re.sub(
    r'const backlogOwed\s*=\s*origDebt \+ storageFees - amountPaid;',
    r'const backlogOwed        = totalCost + storageFees - amountPaid;',
    content_fol
)

content_fol = re.sub(
    r'<span className=\{styles\.pbLabel\}>ORIGINAL TITLE DEBT</span>\s*<span className=\{styles\.pbVal\}>UGX \{fmt\(origDebt\)\}</span>',
    r'<span className={styles.pbLabel}>TITLE COST</span>\n                                    <span className={styles.pbVal}>UGX {fmt(totalCost)}</span>',
    content_fol
)
write(path_fol, content_fol)


# ============================================================
# 6. FIX PAYMENTS PAGE (Remove Instalment Filter)
# ============================================================
path_pay = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'
content_pay = read(path_pay)

content_pay = re.sub(r"MONTHLY_INSTALMENT:\s*'Monthly Instalment',?\n?", "", content_pay)
content_pay = re.sub(r"MONTHLY_INSTALMENT:\s*'#[a-f0-9]+',?\n?", "", content_pay)
content_pay = content_pay.replace(
    "['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL', 'MONTHLY_INSTALMENT']", 
    "['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL']"
)
write(path_pay, content_pay)


print("\n=== ALL MATH AND UI FIXES APPLIED SUCCESSFULLY ===")
print("Run: git add -A && git commit -m 'fix: correct backlog balance math and remove instalment filters' && git push")