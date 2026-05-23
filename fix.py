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

# ─────────────────────────────────────────────────────────────────────
# LEDGER PAGE
# ─────────────────────────────────────────────────────────────────────
LEDGER_CSS = 'erp-frontend/src/pages/Ledger/LedgerPage.module.css'

# Make container fill remaining height without overflow
patch(LEDGER_CSS,
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    position: relative;
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}''',
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
}''',
    'LedgerPage container flex column'
)

# HardwarePanel should flex and allow inner scroll
patch(LEDGER_CSS,
    '''/* ── TABLE SHELL ────────────────────────────────────────────────── */
.tableScroll {
    overflow-x: auto;
    overflow-y: visible;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel's 30px padding to use full width */
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
}''',
    '''/* ── TABLE SHELL ────────────────────────────────────────────────── */
.tableScroll {
    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel's 30px padding to use full width */
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    flex: 1;
    min-height: 0;
}''',
    'LedgerPage tableScroll overflow-y auto + flex'
)

# Make the HardwarePanel wrapper flex so inner table can grow
# We do this by targeting the panel via a wrapper class approach
# Actually we patch the pagination to not have negative bottom margin
patch(LEDGER_CSS,
    '''.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(10px, 1.4vw, 16px) clamp(14px, 2vw, 22px);
    border-top: 1px solid rgba(255,255,255,0.06);
    /* Compensate for the negative margin on tableScroll */
    margin: 0 0 -30px 0;
}''',
    '''.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(10px, 1.4vw, 16px) clamp(14px, 2vw, 22px);
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 0;
    flex-shrink: 0;
}''',
    'LedgerPage pagination no negative margin'
)

# ─────────────────────────────────────────────────────────────────────
# LEDGER PAGE JSX — wrap HardwarePanel in flex container
# ─────────────────────────────────────────────────────────────────────
LEDGER_JSX = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'

patch(LEDGER_JSX,
    '''            <HardwarePanel variant="dark">
                <div className={styles.tableScroll}>''',
    '''            <div style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
            <HardwarePanel variant="dark" style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
                <div className={styles.tableScroll}>''',
    'LedgerPage JSX wrap panel in flex div'
)

patch(LEDGER_JSX,
    '''                </footer>
            </HardwarePanel>''',
    '''                </footer>
            </HardwarePanel>
            </div>''',
    'LedgerPage JSX close flex wrapper'
)

# ─────────────────────────────────────────────────────────────────────
# PAYMENTS PAGE
# ─────────────────────────────────────────────────────────────────────
PAYMENTS_CSS = 'erp-frontend/src/pages/Payments/PaymentsPage.module.css'

patch(PAYMENTS_CSS,
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}''',
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) 0;
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}''',
    'PaymentsPage container flex column'
)

patch(PAYMENTS_CSS,
    '''/* ─── TABLE SHELL - identical to Ledger ─────────────────────────── */
.tableScroll {
    overflow-x: auto;
    overflow-y: visible;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
}''',
    '''/* ─── TABLE SHELL - identical to Ledger ─────────────────────────── */
.tableScroll {
    overflow-x: auto;
    overflow-y: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
    flex: 1;
    min-height: 0;
}''',
    'PaymentsPage tableScroll overflow-y auto + flex'
)

PAYMENTS_JSX = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'

patch(PAYMENTS_JSX,
    '''            <HardwarePanel variant="dark">
                <div className={styles.tableScroll}>''',
    '''            <div style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
            <HardwarePanel variant="dark" style={{flex:'1',minHeight:0,display:'flex',flexDirection:'column'}}>
                <div className={styles.tableScroll}>''',
    'PaymentsPage JSX wrap panel in flex div'
)

patch(PAYMENTS_JSX,
    '''                </table>
                </div>
                </HardwarePanel>''',
    '''                </table>
                </div>
                </HardwarePanel>
                </div>''',
    'PaymentsPage JSX close flex wrapper'
)

# ─────────────────────────────────────────────────────────────────────
# AUDIT PAGE
# ─────────────────────────────────────────────────────────────────────
AUDIT_CSS = 'erp-frontend/src/pages/Audit/AuditPage.module.css'

patch(AUDIT_CSS,
    '''    max-width: 1450px;
    margin: 0 auto;
    padding: clamp(8px, 2vw, 16px) clamp(8px, 1.6vw, 16px) clamp(28px, 4.5vw, 52px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: terminalBoot 0.7s cubic-bezier(0.2, 1, 0.3, 1) both;
}''',
    '''    max-width: 1450px;
    margin: 0 auto;
    padding: clamp(8px, 2vw, 16px) clamp(8px, 1.6vw, 16px) 0;
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: terminalBoot 0.7s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}''',
    'AuditPage container flex column'
)

patch(AUDIT_CSS,
    '''.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: visible; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }
.timelineStream { display: flex; flex-direction: column; min-height: clamp(280px, 40vw, 420px); }''',
    '''.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: hidden; box-shadow: 0 10px 36px rgba(0,0,0,0.2); flex: 1; min-height: 0; display: flex; flex-direction: column; }
.timelineStream { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow-y: auto; }''',
    'AuditPage timelineFrame + timelineStream internal scroll'
)

patch(AUDIT_CSS,
    '''.pagination { display: flex; justify-content: space-between; align-items: center; padding: clamp(8px,1vw,11px) clamp(12px,1.5vw,18px); background: rgba(0,0,0,0.2); border-top: 1px solid rgba(255,255,255,0.05); }''',
    '''.pagination { display: flex; justify-content: space-between; align-items: center; padding: clamp(8px,1vw,11px) clamp(12px,1.5vw,18px); background: rgba(0,0,0,0.2); border-top: 1px solid rgba(255,255,255,0.05); flex-shrink: 0; }''',
    'AuditPage pagination flex-shrink 0'
)

# ─────────────────────────────────────────────────────────────────────
# RECOVERY PORTAL
# ─────────────────────────────────────────────────────────────────────
RECOVERY_CSS = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'

patch(RECOVERY_CSS,
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px,1.5vw,16px) clamp(8px,1.5vw,16px) clamp(24px,4vw,48px);
    font-family: 'DM Sans',sans-serif;
    color: #fff;
}''',
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px,1.5vw,16px) clamp(8px,1.5vw,16px) 0;
    font-family: 'DM Sans',sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}''',
    'RecoveryPortal container flex column'
)

patch(RECOVERY_CSS,
    '''.missionGrid { display:flex; flex-direction:column; gap:var(--gap-lg); }''',
    '''.missionGrid { display:flex; flex-direction:column; gap:var(--gap-lg); flex:1; min-height:0; overflow-y:auto; padding-bottom: clamp(24px,4vw,48px); }''',
    'RecoveryPortal missionGrid internal scroll'
)

# ─────────────────────────────────────────────────────────────────────
# SHELL — the scroll area needs to NOT scroll when these pages are shown
# Actually the Shell scrollArea is the parent. We need to make it pass
# height correctly. The key is Shell.module.css scrollArea must be
# flex column and pass height down.
# ─────────────────────────────────────────────────────────────────────
SHELL_CSS = 'erp-frontend/src/components/layout/Shell.module.css'

patch(SHELL_CSS,
    '''/* THE SCROLLABLE BODY (As per directive) */
.scrollArea {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 30px;
    scroll-behavior: smooth;
    
    /* Industrial scrollbar styling */
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}''',
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
    'Shell scrollArea flex column'
)

# The direct child of scrollArea (the page container) needs to be able to fill height
# We add a rule: direct child of scrollArea that is a flex column fills height
patch(SHELL_CSS,
    '''.scrollArea::-webkit-scrollbar {
    width: 6px;
}

.scrollArea::-webkit-scrollbar-thumb {
    background-color: var(--orange);
    border-radius: 10px;
}''',
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
    'Shell scrollArea children width 100%'
)

print('\nAll patches complete.')