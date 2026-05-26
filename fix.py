import os

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old in content:
        write_file(path, content.replace(old, new, 1))
        print(f'OK: {label}')
    else:
        print(f'MISSING: {label}')

# =============================================================================
# 1. SHELL — Make scrollArea overflow-y: scroll so header scrolls away,
#    but pages that need internal scroll can opt out by setting overflow:hidden
# =============================================================================
SHELL_CSS = 'erp-frontend/src/components/layout/Shell.module.css'

patch(SHELL_CSS,
    '''/* THE SCROLLABLE BODY (As per directive) */
.scrollArea {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 30px;
    scroll-behavior: smooth;
    display: flex;
    flex-direction: column;
    
    /* Industrial scrollbar styling */
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}''',
    '''/* THE SCROLLABLE BODY
   Pages that self-scroll (Ledger, Audit, Payments, Recovery, FolderPage)
   set overflow:hidden on their container so the outer scroll is disabled
   and their own internal list scroll takes over.
   All other pages (Dashboard, Reports, Intake, Settings) scroll naturally here. */
.scrollArea {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0;
    scroll-behavior: smooth;
    display: flex;
    flex-direction: column;

    /* Industrial scrollbar styling */
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}''',
    'Shell scrollArea padding 0 (pages own their padding)'
)

# =============================================================================
# 2. LEDGER PAGE — page-level outer scroll for header+filters, then list scrolls
#    Pattern: container is overflow:hidden (no outer scroll), but we want the
#    header+controls to be part of a natural scroll THEN the table sticks.
#    Better approach: container scrolls normally, table has a fixed max-height.
# =============================================================================
LEDGER_CSS = 'erp-frontend/src/pages/Ledger/LedgerPage.module.css'

# Container: allow outer scroll (remove overflow:hidden, use normal flow)
patch(LEDGER_CSS,
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) 0;
    position: relative;
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;
}''',
    '''    max-width: 1400px;
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(24px, 3vw, 36px);
    position: relative;
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}''',
    'LedgerPage container natural scroll'
)

# tableScroll: fixed height so it scrolls independently
patch(LEDGER_CSS,
    '''    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    flex: 1;
    min-height: 0;
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}
.tableScroll::-webkit-scrollbar { width: 5px; height: 4px; }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }
.tableScroll::-webkit-scrollbar { height: 4px; }
.tableScroll::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 2px; }''',
    '''    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    max-height: clamp(340px, 55vh, 700px);
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}
.tableScroll::-webkit-scrollbar { width: 5px; height: 4px; }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }
.tableScroll::-webkit-scrollbar { height: 4px; }
.tableScroll::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 2px; }''',
    'LedgerPage tableScroll max-height for internal scroll'
)

# Fix pagination margin
patch(LEDGER_CSS,
    '''.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(10px, 1.4vw, 16px) clamp(14px, 2vw, 22px);
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 0;
    flex-shrink: 0;
}''',
    '''.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(10px, 1.4vw, 16px) clamp(14px, 2vw, 22px);
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 0 -30px -30px -30px;
}''',
    'LedgerPage pagination margin restored'
)

# Remove the flex wrappers from JSX since we no longer need them
LEDGER_JSX = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'

patch(LEDGER_JSX,
    '''            <div style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
            <HardwarePanel variant="dark" style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
                <div className={styles.tableScroll}>''',
    '''            <HardwarePanel variant="dark">
                <div className={styles.tableScroll}>''',
    'LedgerPage JSX remove flex wrappers'
)

patch(LEDGER_JSX,
    '''                </footer>
            </HardwarePanel>
            </div>''',
    '''                </footer>
            </HardwarePanel>''',
    'LedgerPage JSX remove closing flex wrapper'
)

# =============================================================================
# 3. PAYMENTS PAGE — same pattern as Ledger
# =============================================================================
PAYMENTS_CSS = 'erp-frontend/src/pages/Payments/PaymentsPage.module.css'

patch(PAYMENTS_CSS,
    '''    max-width: 1400px;
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) 0;
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;
}''',
    '''    max-width: 1400px;
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(24px, 3vw, 36px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}''',
    'PaymentsPage container natural scroll'
)

patch(PAYMENTS_CSS,
    '''    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    flex: 1;
    min-height: 0;
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}
.tableScroll::-webkit-scrollbar { width: 5px; height: 4px; }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }
.tableScroll::-webkit-scrollbar { height: 4px; }
.tableScroll::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 2px; }''',
    '''    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    max-height: clamp(340px, 55vh, 700px);
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}
.tableScroll::-webkit-scrollbar { width: 5px; height: 4px; }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }
.tableScroll::-webkit-scrollbar { height: 4px; }
.tableScroll::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 2px; }''',
    'PaymentsPage tableScroll max-height'
)

PAYMENTS_JSX = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'

patch(PAYMENTS_JSX,
    '''            <div style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
            <HardwarePanel variant="dark" style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
                <div className={styles.tableScroll}>''',
    '''            <HardwarePanel variant="dark">
                <div className={styles.tableScroll}>''',
    'PaymentsPage JSX remove flex wrappers'
)

patch(PAYMENTS_JSX,
    '''                </table>
                </div>
                </HardwarePanel>
                </div>''',
    '''                </table>
                </div>
                </HardwarePanel>''',
    'PaymentsPage JSX remove closing flex wrapper'
)

# =============================================================================
# 4. AUDIT PAGE — same pattern
# =============================================================================
AUDIT_CSS = 'erp-frontend/src/pages/Audit/AuditPage.module.css'

patch(AUDIT_CSS,
    '''    max-width: 1450px;
    width: 100%;
    padding: clamp(8px, 2vw, 16px) clamp(8px, 1.6vw, 16px) 0;
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: terminalBoot 0.7s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;
}''',
    '''    max-width: 1450px;
    width: 100%;
    padding: clamp(8px, 2vw, 16px) clamp(8px, 1.6vw, 16px) clamp(24px, 3vw, 36px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: terminalBoot 0.7s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}''',
    'AuditPage container natural scroll'
)

patch(AUDIT_CSS,
    '''.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: hidden; box-shadow: 0 10px 36px rgba(0,0,0,0.2); flex: 1; min-height: 0; display: flex; flex-direction: column; }
.timelineStream { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--orange) transparent; }''',
    '''.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: hidden; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }
.timelineStream { display: flex; flex-direction: column; max-height: clamp(340px, 55vh, 700px); overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--orange) transparent; }''',
    'AuditPage timelineStream max-height'
)

# =============================================================================
# 5. RECOVERY PORTAL — natural scroll, remove count row redundancy, add card gap
# =============================================================================
RECOVERY_CSS = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'

patch(RECOVERY_CSS,
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px,1.5vw,16px) clamp(8px,1.5vw,16px) 0;
    font-family: 'DM Sans',sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;
}''',
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px,1.5vw,16px) clamp(8px,1.5vw,16px) clamp(40px,6vw,60px);
    font-family: 'DM Sans',sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}''',
    'RecoveryPortal container natural scroll'
)

patch(RECOVERY_CSS,
    '''.missionGrid { display:flex; flex-direction:column; gap:var(--gap-lg); flex:1; min-height:0; overflow-y:auto; padding-bottom: clamp(24px,4vw,48px); scrollbar-width:thin; scrollbar-color:var(--orange) transparent; }
.missionGrid::-webkit-scrollbar { width:5px; }
.missionGrid::-webkit-scrollbar-thumb { background:rgba(238,140,58,0.4); border-radius:2px; }''',
    '''.missionGrid { display:flex; flex-direction:column; gap:clamp(12px,1.6vw,18px); }''',
    'RecoveryPortal missionGrid normal flow with larger gap'
)

# Hide the count row (redundant with section headers)
patch(RECOVERY_CSS,
    '''/* ── COUNT ROW ── */
.countRow {
    display:flex; gap:16px; margin-bottom:clamp(8px,1vw,12px);
    font-family:'Space Mono',monospace; font-size:clamp(8px,0.82vw,10px);
    font-weight:900; color:rgba(255,255,255,0.45); text-transform:uppercase;
    flex-shrink:0;
}
.countBacklog { color:rgba(239,68,68,0.8); }''',
    '''/* ── COUNT ROW — hidden, redundant with section group headers ── */
.countRow { display:none; }
.countBacklog { display:none; }''',
    'RecoveryPortal countRow hidden'
)

# =============================================================================
# 6. FOLDER PAGE — remove bg from filter/tab area, make tabs sticky
#    Tab bar already has sticky positioning in CSS; we just ensure no bg box
# =============================================================================
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'

# Remove the background from the tab bar (the sticky strip)
patch(FOLDER_CSS,
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
}''',
    '''.tabBar {
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
    background: transparent;
    /* No backdrop, no border-radius — clean tabs that blend with page bg */
}''',
    'FolderPage tabBar transparent bg, sticky top:0'
)

# Also fix the mobile duplicate tabBar rule
patch(FOLDER_CSS,
    '''@media (max-width: 600px) {
    .tabBar {
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
}''',
    '''@media (max-width: 600px) {
    .tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: clamp(8px, 2vw, 10px);
    padding-top: clamp(8px, 2vw, 10px);
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: 0;
    z-index: 100;
    background: transparent;
}''',
    'FolderPage tabBar mobile transparent bg'
)

# FolderPage container — allow natural outer scroll (remove overflow:hidden)
patch(FOLDER_CSS,
    '''    /* NO z-index — warmBoot uses filter+transform which traps fixed children */
    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px, 1.2vw, 14px) clamp(10px, 1.8vw, 20px) clamp(40px, 5vw, 60px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    width: 100%;
    box-sizing: border-box;
    position: relative;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}''',
    '''    /* NO z-index — warmBoot uses filter+transform which traps fixed children */
    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px, 1.2vw, 14px) clamp(10px, 1.8vw, 20px) clamp(40px, 5vw, 60px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    width: 100%;
    box-sizing: border-box;
    position: relative;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    /* Natural outer scroll — tab bar sticks via position:sticky */
}''',
    'FolderPage container comment for clarity'
)

# =============================================================================
# 7. SHELL scrollArea — add padding back for pages that don't manage their own
#    Actually pages now own their padding, shell has none. But we need to ensure
#    the scrollArea itself has a proper scrollbar.
# =============================================================================
patch(SHELL_CSS,
    '''.scrollArea::-webkit-scrollbar {
    width: 6px;
}

.scrollArea::-webkit-scrollbar-thumb {
    background-color: var(--orange);
    border-radius: 10px;
}

/* Allow flex-column pages to fill the scroll area height */
.scrollArea > * {
    width: 100%;
}''',
    '''.scrollArea::-webkit-scrollbar {
    width: 6px;
}

.scrollArea::-webkit-scrollbar-thumb {
    background-color: var(--orange);
    border-radius: 10px;
}

/* All pages own their padding and width */
.scrollArea > * {
    width: 100%;
    box-sizing: border-box;
}''',
    'Shell scrollArea children box-sizing'
)

print('\nAll patches complete.')