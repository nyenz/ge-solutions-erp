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
# 1. SHELL — scrollArea scrolls normally (pages own their padding).
#    The key change: scrollArea is overflow-y: auto (natural scroll).
#    Pages that want internal-only scroll set overflow:hidden on their container.
# =============================================================================
SHELL_CSS = 'erp-frontend/src/components/layout/Shell.module.css'

patch(SHELL_CSS,
    '''/* THE SCROLLABLE BODY — pages manage their own internal scrolling */
.scrollArea {
    flex: 1;
    overflow: hidden;
    padding: 0;
    display: flex;
    flex-direction: column;
}

/* Pages fill the scroll area */
.scrollArea > * {
    width: 100%;
    height: 100%;
    overflow: hidden;
}''',
    '''/* THE SCROLLABLE BODY
   Scrolls naturally so the page header scrolls away.
   Pages that need internal list-scroll (Ledger, Audit, Payments, Recovery)
   just set a max-height on their table/list — not overflow:hidden here. */
.scrollArea {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0;
    display: flex;
    flex-direction: column;
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}

.scrollArea::-webkit-scrollbar { width: 6px; }
.scrollArea::-webkit-scrollbar-thumb { background: var(--orange); border-radius: 10px; }

.scrollArea > * {
    width: 100%;
    box-sizing: border-box;
}''',
    'Shell scrollArea natural outer scroll'
)

# =============================================================================
# 2. LEDGER — container allows outer scroll (header scrolls away),
#    tableScroll has fixed max-height for internal list scroll.
#    Sticky th headers stay visible inside the table.
# =============================================================================
LEDGER_CSS = 'erp-frontend/src/pages/Ledger/LedgerPage.module.css'

patch(LEDGER_CSS,
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
    /* Outer scroll: header+search scroll away, then table list scrolls internally */
}''',
    'Ledger container comment'
)

# controlHub — make it sticky so filters stay visible after header scrolls
patch(LEDGER_CSS,
    '''.controlHub {
    display: flex;
    flex-direction: column;
    gap: var(--gap-lg);
    margin-bottom: var(--gap-xl);
    flex-shrink: 0;
}''',
    '''.controlHub {
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
    -webkit-backdrop-filter: blur(12px);
    padding: clamp(8px, 1vw, 12px) 0;
    margin-left: clamp(-12px, -2vw, -24px);
    margin-right: clamp(-12px, -2vw, -24px);
    padding-left: clamp(12px, 2vw, 24px);
    padding-right: clamp(12px, 2vw, 24px);
}''',
    'Ledger controlHub sticky after header scrolls away'
)

# =============================================================================
# 3. PAYMENTS — same sticky pattern
# =============================================================================
PAYMENTS_CSS = 'erp-frontend/src/pages/Payments/PaymentsPage.module.css'

patch(PAYMENTS_CSS,
    '''/* CONTROLS */
.controls {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: clamp(14px, 2vw, 20px);
    flex-shrink: 0;
}''',
    '''/* CONTROLS — sticky so filters stay accessible after header scrolls */
.controls {
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
    -webkit-backdrop-filter: blur(12px);
    padding: clamp(8px, 1vw, 12px) 0;
    margin-left: clamp(-12px, -2vw, -24px);
    margin-right: clamp(-12px, -2vw, -24px);
    padding-left: clamp(12px, 2vw, 24px);
    padding-right: clamp(12px, 2vw, 24px);
}''',
    'PaymentsPage controls sticky'
)

# =============================================================================
# 4. AUDIT — sticky filterGrid
# =============================================================================
AUDIT_CSS = 'erp-frontend/src/pages/Audit/AuditPage.module.css'

patch(AUDIT_CSS,
    '''.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; flex-shrink: 0; }''',
    '''.controlHub {
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
    -webkit-backdrop-filter: blur(12px);
    padding: clamp(8px, 1vw, 12px) 0;
    margin-left: clamp(-8px, -1.6vw, -16px);
    margin-right: clamp(-8px, -1.6vw, -16px);
    padding-left: clamp(8px, 1.6vw, 16px);
    padding-right: clamp(8px, 1.6vw, 16px);
}''',
    'AuditPage controlHub sticky'
)

# =============================================================================
# 5. RECOVERY — remove countRow from JSX, add card spacing, natural scroll,
#    remove the bg from the filter section for uniformity
# =============================================================================
RECOVERY_CSS = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'

# Natural outer scroll
patch(RECOVERY_CSS,
    '''    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px,1.5vw,16px) clamp(8px,1.5vw,16px) clamp(40px,6vw,60px);
    font-family: 'DM Sans',sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
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
    /* Natural outer scroll: header scrolls away, filters become sticky */
}''',
    'Recovery container comment'
)

# filterBar — make it sticky
patch(RECOVERY_CSS,
    '''/* ── FILTER BAR ── */
.filterBar {
    display:flex; flex-direction:column; gap:var(--gap-md);
    margin-bottom:clamp(8px,1vw,12px);
    flex-shrink:0;
}''',
    '''/* ── FILTER BAR — sticky so search+filters stay accessible after header scrolls ── */
.filterBar {
    display:flex; flex-direction:column; gap:var(--gap-md);
    margin-bottom:clamp(8px,1vw,12px);
    flex-shrink:0;
    position:sticky;
    top:0;
    z-index:200;
    background:rgba(244,242,239,0.96);
    backdrop-filter:blur(12px);
    -webkit-backdrop-filter:blur(12px);
    padding:clamp(8px,1vw,12px) 0;
    margin-left:clamp(-8px,-1.5vw,-16px);
    margin-right:clamp(-8px,-1.5vw,-16px);
    padding-left:clamp(8px,1.5vw,16px);
    padding-right:clamp(8px,1.5vw,16px);
}''',
    'RecoveryPortal filterBar sticky'
)

# Add spacing between mission cards via sectionGroup
patch(RECOVERY_CSS,
    '''/* ── SECTION GROUPS ── */
.sectionGroup { margin-bottom:clamp(20px, 2.8vw, 32px); }''',
    '''/* ── SECTION GROUPS ── */
.sectionGroup { margin-bottom:clamp(24px, 3.2vw, 40px); }''',
    'Recovery sectionGroup more bottom margin'
)

# Increase gap between mission cards
patch(RECOVERY_CSS,
    '''.missionGrid { display:flex; flex-direction:column; gap:clamp(12px,1.6vw,18px); }''',
    '''.missionGrid { display:flex; flex-direction:column; gap:clamp(14px,2vw,22px); }''',
    'Recovery missionGrid larger gap between cards'
)

# Remove countRow from JSX
RECOVERY_JSX = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'

patch(RECOVERY_JSX,
    '''            {/* SUMMARY COUNTS */}
            <div className={styles.countRow}>
                <span>{filteredMissions.length} PLOTS SHOWN</span>
                {activeMissions.length > 0 && <span>{activeMissions.length} ACTIVE</span>}
                {backlogMissions.length > 0 && <span className={styles.countBacklog}>{backlogMissions.length} BACKLOG</span>}
            </div>

            <div className={styles.missionGrid}>''',
    '''            <div className={styles.missionGrid}>''',
    'RecoveryPortal remove redundant countRow from JSX'
)

# =============================================================================
# 6. FOLDER PAGE — remove bg from the filterBar / controlHub area,
#    tab bar stays sticky (it already is), container allows outer scroll.
# =============================================================================
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'

# Remove the orange-bg sticky strip above the tab bar if present,
# and ensure the tab bar background is transparent (already done in last fix).
# Now also remove bg from the pipelineHUD area so nothing looks boxed.

# Make the whole container scroll naturally (it already should after last fix).
# The tab bar is already sticky with transparent bg.
# Just ensure finPanelHeader is also sticky relative to the scrolling container.
patch(FOLDER_CSS,
    '''.finPanelHeader {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(9px, 1.2vw, 13px) clamp(12px, 1.5vw, 18px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.18);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    position: sticky;
    top: 24px;
    z-index: 90;
    background: var(--panel-bg);
    border-radius: 10.5px 10.5px 0 0;
}''',
    '''.finPanelHeader {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(9px, 1.2vw, 13px) clamp(12px, 1.5vw, 18px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.18);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    border-radius: 10.5px 10.5px 0 0;
    /* Not sticky — tab bar is sticky, that is enough for navigation */
}''',
    'FolderPage finPanelHeader not sticky (tab bar handles nav)'
)

# Tab bar — ensure it is sticky with correct offset (accounts for header height)
patch(FOLDER_CSS,
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
    background: rgba(244, 242, 239, 0.95);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    /* Sticks to top of scroll area so Overview/Financials/Owners/Documents always accessible */
}''',
    'FolderPage tabBar sticky with glass bg for accessibility'
)

# Fix mobile tabBar too
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
    padding-bottom: clamp(8px, 2vw, 10px);
    padding-top: clamp(8px, 2vw, 10px);
    margin-bottom: clamp(10px, 1.3vw, 14px);
    position: sticky;
    top: 0;
    z-index: 100;
    background: transparent;
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
    background: rgba(244, 242, 239, 0.95);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}''',
    'FolderPage tabBar mobile sticky glass bg'
)

print('\nAll patches complete.')