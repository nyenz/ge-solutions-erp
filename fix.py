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

SETTINGS_JSX = 'erp-frontend/src/pages/settings/SettingsPage.jsx'
SETTINGS_CSS = 'erp-frontend/src/pages/settings/SettingsPage.module.css'
RECOVERY_CSS = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'

# ─────────────────────────────────────────────
# 1. Settings — add legend above staffStream
# ─────────────────────────────────────────────

patch(SETTINGS_JSX,
    '''                                <div className={styles.staffStream} role="list" aria-label="Operators">''',
    '''                                <div className={styles.statusLegend} aria-label="Status legend">
                                    <span className={styles.legendDot} style={{background:'#10b981',boxShadow:'0 0 6px #10b981'}} aria-hidden="true" />
                                    <span className={styles.legendText}>Active Operator</span>
                                    <span className={styles.legendSep} aria-hidden="true" />
                                    <span className={styles.legendDot} style={{background:'#ef4444'}} aria-hidden="true" />
                                    <span className={styles.legendText}>Suspended / Inactive</span>
                                </div>
                                <div className={styles.staffStream} role="list" aria-label="Operators">''',
    'SettingsPage — add status legend JSX'
)

patch(SETTINGS_CSS,
    '''.staffStream {
    display: flex; flex-direction: column; gap: var(--gap-md);
    max-height: clamp(300px, 40vh, 480px); overflow-y: auto;
    padding-right: clamp(3px,0.4vw,5px);
    scrollbar-width: thin; scrollbar-color: rgba(238,140,58,0.4) transparent;
}''',
    '''.statusLegend {
    display: flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 9px);
    margin-bottom: var(--gap-md);
    padding: clamp(6px, 0.8vw, 9px) clamp(10px, 1.2vw, 14px);
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-sm);
    flex-wrap: wrap;
}
.legendDot {
    width: clamp(8px, 1vw, 10px);
    height: clamp(8px, 1vw, 10px);
    border-radius: 50%;
    flex-shrink: 0;
}
.legendText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.82vw, 10px);
    font-weight: 800;
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.legendSep {
    width: 1px;
    height: clamp(10px, 1.2vw, 13px);
    background: rgba(255, 255, 255, 0.12);
    margin: 0 clamp(3px, 0.4vw, 5px);
    flex-shrink: 0;
}

.staffStream {
    display: flex; flex-direction: column; gap: var(--gap-md);
    max-height: clamp(300px, 40vh, 480px); overflow-y: auto;
    padding-right: clamp(3px,0.4vw,5px);
    scrollbar-width: thin; scrollbar-color: rgba(238,140,58,0.4) transparent;
}''',
    'SettingsPage — add statusLegend CSS'
)

# ─────────────────────────────────────────────
# 2. Recovery — increase spacing between mission cards
# ─────────────────────────────────────────────

patch(RECOVERY_CSS,
    '''.missionGrid { display:flex; flex-direction:column; gap:var(--gap-md); }''',
    '''.missionGrid { display:flex; flex-direction:column; gap:var(--gap-lg); }''',
    'RecoveryPortal — missionGrid gap increased'
)

patch(RECOVERY_CSS,
    '''.sectionGroup { margin-bottom:var(--gap-xl); }''',
    '''.sectionGroup { margin-bottom:clamp(20px, 2.8vw, 32px); }''',
    'RecoveryPortal — sectionGroup margin-bottom increased'
)

patch(RECOVERY_CSS,
    '''.missionCard {
    background:var(--panel-bg);
    border:1.5px solid rgba(238,140,58,0.2);
    border-radius:var(--radius);
    box-shadow:0 3px 12px rgba(0,0,0,0.2);
    transition:border-color 0.2s;
    overflow:hidden; width:100%;
}''',
    '''.missionCard {
    background:var(--panel-bg);
    border:1.5px solid rgba(238,140,58,0.2);
    border-radius:var(--radius);
    box-shadow:0 4px 18px rgba(0,0,0,0.22);
    transition:border-color 0.2s;
    overflow:hidden; width:100%;
}''',
    'RecoveryPortal — missionCard shadow depth'
)

print('\nAll patches complete.')