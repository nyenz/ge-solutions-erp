# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

print("=== RESOLVING MOBILITY CLIPPING & SCROLL CONSTRAINTS ===")

# 1. RecoveryPortal.module.css - Remove height and overflow blockages
path_recovery_css = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'
data_recovery_css = read(path_recovery_css)
old_recovery_container = """    font-family: 'DM Sans',sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;"""
new_recovery_container = """    font-family: 'DM Sans',sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;"""

if old_recovery_container in data_recovery_css:
    data_recovery_css = data_recovery_css.replace(old_recovery_container, new_recovery_container)
    write(path_recovery_css, data_recovery_css)
    print("OK: RecoveryPortal.module.css scroll constraints removed")
else:
    print("WARNING: RecoveryPortal.module.css target container styles not found")

# 2. LedgerPage.module.css - Remove height and overflow blockages
path_ledger_css = 'erp-frontend/src/pages/Ledger/LedgerPage.module.css'
data_ledger_css = read(path_ledger_css)
old_ledger_container = """    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;"""
new_ledger_container = """    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;"""

if old_ledger_container in data_ledger_css:
    data_ledger_css = data_ledger_css.replace(old_ledger_container, new_ledger_container)
    write(path_ledger_css, data_ledger_css)
    print("OK: LedgerPage.module.css scroll constraints removed")
else:
    print("WARNING: LedgerPage.module.css target container styles not found")

# 3. AuditPage.module.css - Remove static z-index stacking trap
path_audit_css = 'erp-frontend/src/pages/Audit/AuditPage.module.css'
data_audit_css = read(path_audit_css)
old_audit_select_wrap = """.hwSelectWrap {
    flex: 1 1 140px;
    max-width: 240px;
    min-width: 120px;
    position: relative;
    z-index: 9000;
    overflow: visible !important;
}"""
new_audit_select_wrap = """.hwSelectWrap {
    flex: 1 1 140px;
    max-width: 240px;
    min-width: 120px;
    position: relative;
    overflow: visible !important;
}"""

if old_audit_select_wrap in data_audit_css:
    data_audit_css = data_audit_css.replace(old_audit_select_wrap, new_audit_select_wrap)
    write(path_audit_css, data_audit_css)
    print("OK: AuditPage.module.css z-index stacking trap resolved")
else:
    print("WARNING: AuditPage.module.css z-index target not found")

print("=== FIXES APPLIED SUCCESSFULLY ===")
