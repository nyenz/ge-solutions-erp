# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

print("=== REMOVING FILTER BACKGROUNDS AND CONSOLIDATING SCROLLS ===")

# 1. LedgerPage.jsx
path_ledger_jsx = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'
data_ledger_jsx = read(path_ledger_jsx)
old_ledger_jsx = """            <div style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column',overflow:'hidden'}}>
            <HardwarePanel variant="dark" style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column',overflow:'hidden'}}>"""
new_ledger_jsx = """            <div>
            <HardwarePanel variant="dark">"""
if old_ledger_jsx in data_ledger_jsx:
    data_ledger_jsx = data_ledger_jsx.replace(old_ledger_jsx, new_ledger_jsx)
    write(path_ledger_jsx, data_ledger_jsx)
    print("OK: LedgerPage.jsx inline styles removed")
else:
    print("WARNING: LedgerPage.jsx inline styles target not found")

# 2. PaymentsPage.jsx
path_payments_jsx = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'
data_payments_jsx = read(path_payments_jsx)
old_payments_jsx = """                <div style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column',overflow:'hidden'}}>
            <HardwarePanel variant="dark" style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column',overflow:'hidden'}}>"""
new_payments_jsx = """                <div>
            <HardwarePanel variant="dark">"""
if old_payments_jsx in data_payments_jsx:
    data_payments_jsx = data_payments_jsx.replace(old_payments_jsx, new_payments_jsx)
    write(path_payments_jsx, data_payments_jsx)
    print("OK: PaymentsPage.jsx inline styles removed")
else:
    print("WARNING: PaymentsPage.jsx inline styles target not found")

# 3. LedgerPage.module.css
path_ledger_css = 'erp-frontend/src/pages/Ledger/LedgerPage.module.css'
data_ledger_css = read(path_ledger_css)
old_ledger_hub = """.controlHub {
    display: flex;
    flex-direction: column;
    gap: var(--gap-lg);
    margin-bottom: var(--gap-xl);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: rgba(244, 242, 239, 0.96);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);"""
new_ledger_hub = """.controlHub {
    display: flex;
    flex-direction: column;
    gap: var(--gap-lg);
    margin-bottom: var(--gap-xl);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: transparent;"""
if old_ledger_hub in data_ledger_css:
    data_ledger_css = data_ledger_css.replace(old_ledger_hub, new_ledger_hub)
    print("OK: LedgerPage.module.css .controlHub background removed")
else:
    print("WARNING: LedgerPage.module.css .controlHub target not found")

old_ledger_scroll = """.tableScroll {
    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    max-height: clamp(340px, 55vh, 700px);"""
new_ledger_scroll = """.tableScroll {
    overflow-x: auto;
    overflow-y: visible;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    max-height: none;"""
if old_ledger_scroll in data_ledger_css:
    data_ledger_css = data_ledger_css.replace(old_ledger_scroll, new_ledger_scroll)
    print("OK: LedgerPage.module.css .tableScroll double scroll fixed")
else:
    print("WARNING: LedgerPage.module.css .tableScroll target not found")

write(path_ledger_css, data_ledger_css)

# 4. PaymentsPage.module.css
path_payments_css = 'erp-frontend/src/pages/Payments/PaymentsPage.module.css'
data_payments_css = read(path_payments_css)
old_payments_controls = """.controls {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: clamp(14px, 2vw, 20px);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: rgba(244, 242, 239, 0.96);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);"""
new_payments_controls = """.controls {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: clamp(14px, 2vw, 20px);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: transparent;"""
if old_payments_controls in data_payments_css:
    data_payments_css = data_payments_css.replace(old_payments_controls, new_payments_controls)
    print("OK: PaymentsPage.module.css .controls background removed")
else:
    print("WARNING: PaymentsPage.module.css .controls target not found")

old_payments_scroll = """.tableScroll {
    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: -30px;
    -webkit-overflow-scrolling: touch;
    flex: 1;
    min-height: 0;"""
new_payments_scroll = """.tableScroll {
    overflow-x: auto;
    overflow-y: visible;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: -30px;
    -webkit-overflow-scrolling: touch;
    flex: 1;
    min-height: auto;"""
if old_payments_scroll in data_payments_css:
    data_payments_css = data_payments_css.replace(old_payments_scroll, new_payments_scroll)
    print("OK: PaymentsPage.module.css .tableScroll double scroll fixed")
else:
    print("WARNING: PaymentsPage.module.css .tableScroll target not found")

write(path_payments_css, data_payments_css)

# 5. AuditPage.module.css
path_audit_css = 'erp-frontend/src/pages/Audit/AuditPage.module.css'
data_audit_css = read(path_audit_css)
old_audit_hub = """.controlHub {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: var(--gap-lg);
    width: 100%;
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: rgba(244, 242, 239, 0.96);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);"""
new_audit_hub = """.controlHub {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: var(--gap-lg);
    width: 100%;
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: transparent;"""
if old_audit_hub in data_audit_css:
    data_audit_css = data_audit_css.replace(old_audit_hub, new_audit_hub)
    print("OK: AuditPage.module.css .controlHub background removed")
else:
    print("WARNING: AuditPage.module.css .controlHub target not found")

old_audit_stream = """.timelineStream { display: flex; flex-direction: column; max-height: clamp(340px, 55vh, 700px); overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--orange) transparent; }"""
new_audit_stream = """.timelineStream { display: flex; flex-direction: column; max-height: none; overflow-y: visible; scrollbar-width: thin; scrollbar-color: var(--orange) transparent; }"""
if old_audit_stream in data_audit_css:
    data_audit_css = data_audit_css.replace(old_audit_stream, new_audit_stream)
    print("OK: AuditPage.module.css .timelineStream double scroll fixed")
else:
    print("WARNING: AuditPage.module.css .timelineStream target not found")

write(path_audit_css, data_audit_css)

# 6. RecoveryPortal.module.css
path_recovery_css = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'
data_recovery_css = read(path_recovery_css)
old_recovery_bar = """.filterBar {
    display:flex; flex-direction:column; gap:var(--gap-md);
    margin-bottom:clamp(8px,1vw,12px);
    flex-shrink:0;
    position:sticky;
    top:0;
    z-index:200;
    background:rgba(244,242,239,0.96);
    backdrop-filter:blur(12px);
    -webkit-backdrop-filter:blur(12px);"""
new_recovery_bar = """.filterBar {
    display:flex; flex-direction:column; gap:var(--gap-md);
    margin-bottom:clamp(8px,1vw,12px);
    flex-shrink:0;
    position:sticky;
    top:0;
    z-index:200;
    background:transparent;"""
if old_recovery_bar in data_recovery_css:
    data_recovery_css = data_recovery_css.replace(old_recovery_bar, new_recovery_bar)
    print("OK: RecoveryPortal.module.css .filterBar background removed")
else:
    print("WARNING: RecoveryPortal.module.css .filterBar target not found")

write(path_recovery_css, data_recovery_css)

# 7. FolderPage.module.css
path_folder_css = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
data_folder_css = read(path_folder_css)
old_folder_tabs = """.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: clamp(8px, 1vw, 10px);
    padding-top: clamp(8px, 1vw, 10px);
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(244, 242, 239, 0.95);
    backdrop-filter: blur(12px);"""
new_folder_tabs = """.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: clamp(8px, 1vw, 10px);
    padding-top: clamp(8px, 1vw, 10px);
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: 0;
    z-index: 100;
    background: transparent;"""
if old_folder_tabs in data_folder_css:
    data_folder_css = data_folder_css.replace(old_folder_tabs, new_folder_tabs)
    print("OK: FolderPage.module.css .tabBar background removed")
else:
    print("WARNING: FolderPage.module.css .tabBar target not found")

write(path_folder_css, data_folder_css)

print("=== RE-CONSOLIDATION APPLIED SUCCESSFULLY ===")