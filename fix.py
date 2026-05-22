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

# ─────────────────────────────────────────────
# LEDGER PAGE CSS
# ─────────────────────────────────────────────
LEDGER_CSS = 'erp-frontend/src/pages/Ledger/LedgerPage.module.css'

# 1. Make controlHub sticky
patch(LEDGER_CSS,
    '''.controlHub {
    display: flex;
    flex-direction: column;
    gap: var(--gap-lg);
    margin-bottom: var(--gap-xl);
}''',
    '''.controlHub {
    display: flex;
    flex-direction: column;
    gap: var(--gap-lg);
    margin-bottom: var(--gap-xl);
    position: sticky;
    top: 0;
    z-index: 200;
    background: rgba(244, 242, 239, 0.97);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding-top: clamp(6px, 1vw, 10px);
    padding-bottom: clamp(6px, 1vw, 10px);
    margin-left: clamp(-12px, -2vw, -24px);
    margin-right: clamp(-12px, -2vw, -24px);
    padding-left: clamp(12px, 2vw, 24px);
    padding-right: clamp(12px, 2vw, 24px);
}''',
    'LedgerPage — controlHub sticky'
)

# 2. Fix tableScroll — remove overflow hidden breakage, keep overflow-x auto
patch(LEDGER_CSS,
    '''.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel's 30px padding to use full width */
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
}''',
    '''.tableScroll {
    overflow-x: auto;
    overflow-y: visible;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel's 30px padding to use full width */
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
}''',
    'LedgerPage — tableScroll overflow-y visible'
)

# 3. Make thead th sticky — control hub is ~120px, use 120px as offset
patch(LEDGER_CSS,
    '''.ledgerTable th {
    background: #162a2c;
    padding: clamp(11px, 1.5vw, 18px) clamp(12px, 1.8vw, 20px);
    text-align: left;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-th);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 3px solid var(--orange);
    box-shadow: 0 3px 0 rgba(238,140,58,0.15);
    white-space: nowrap;
    user-select: none;
}''',
    '''.ledgerTable th {
    background: #162a2c;
    padding: clamp(11px, 1.5vw, 18px) clamp(12px, 1.8vw, 20px);
    text-align: left;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-th);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 3px solid var(--orange);
    box-shadow: 0 3px 0 rgba(238,140,58,0.15);
    white-space: nowrap;
    user-select: none;
    position: sticky;
    top: 0;
    z-index: 100;
}''',
    'LedgerPage — thead th sticky'
)

# ─────────────────────────────────────────────
# PAYMENTS PAGE CSS
# ─────────────────────────────────────────────
PAYMENTS_CSS = 'erp-frontend/src/pages/Payments/PaymentsPage.module.css'

# 1. Make controls sticky
patch(PAYMENTS_CSS,
    '''.controls {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: clamp(14px, 2vw, 20px);
}''',
    '''.controls {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: clamp(14px, 2vw, 20px);
    position: sticky;
    top: 0;
    z-index: 200;
    background: rgba(244, 242, 239, 0.97);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding-top: clamp(6px, 1vw, 10px);
    padding-bottom: clamp(6px, 1vw, 10px);
    margin-left: clamp(-12px, -2vw, -24px);
    margin-right: clamp(-12px, -2vw, -24px);
    padding-left: clamp(12px, 2vw, 24px);
    padding-right: clamp(12px, 2vw, 24px);
}''',
    'PaymentsPage — controls sticky'
)

# 2. Fix tableScroll overflow
patch(PAYMENTS_CSS,
    '''.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
}''',
    '''.tableScroll {
    overflow-x: auto;
    overflow-y: visible;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
}''',
    'PaymentsPage — tableScroll overflow-y visible'
)

# 3. Make thead th sticky
patch(PAYMENTS_CSS,
    '''.ledgerTable th {
    background: #162a2c;
    padding: clamp(11px, 1.5vw, 18px) clamp(12px, 1.8vw, 20px);
    text-align: left;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-th);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 3px solid var(--orange);
    box-shadow: 0 3px 0 rgba(238,140,58,0.15);
    white-space: nowrap;
    user-select: none;
}''',
    '''.ledgerTable th {
    background: #162a2c;
    padding: clamp(11px, 1.5vw, 18px) clamp(12px, 1.8vw, 20px);
    text-align: left;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-th);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 3px solid var(--orange);
    box-shadow: 0 3px 0 rgba(238,140,58,0.15);
    white-space: nowrap;
    user-select: none;
    position: sticky;
    top: 0;
    z-index: 100;
}''',
    'PaymentsPage — thead th sticky'
)

# Also fix the mobile override that resets margin
patch(PAYMENTS_CSS,
    '''@media (max-width: 480px) {
    .tableScroll {
        margin: 0 !important;
        border-radius: var(--radius) !important;
        padding-bottom: 0 !important;
    }
}''',
    '''@media (max-width: 480px) {
    .tableScroll {
        margin: 0 !important;
        border-radius: var(--radius) !important;
        padding-bottom: 0 !important;
        overflow-y: visible !important;
    }
}''',
    'PaymentsPage — mobile tableScroll overflow-y visible'
)

# ─────────────────────────────────────────────
# AUDIT PAGE CSS
# ─────────────────────────────────────────────
AUDIT_CSS = 'erp-frontend/src/pages/Audit/AuditPage.module.css'

# 1. Make controlHub sticky
patch(AUDIT_CSS,
    '''.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; position: relative; z-index: 9500; overflow: visible; }''',
    '''.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; position: sticky; top: 0; z-index: 9500; background: rgba(244, 242, 239, 0.97); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); padding-top: clamp(6px, 1vw, 10px); padding-bottom: clamp(6px, 1vw, 10px); margin-left: clamp(-8px, -1.6vw, -16px); margin-right: clamp(-8px, -1.6vw, -16px); padding-left: clamp(8px, 1.6vw, 16px); padding-right: clamp(8px, 1.6vw, 16px); }''',
    'AuditPage — controlHub sticky'
)

# 2. Fix timelineFrame to not trap sticky children
patch(AUDIT_CSS,
    '''.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: hidden; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }''',
    '''.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: visible; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }''',
    'AuditPage — timelineFrame overflow visible'
)

print('\nAll patches complete.')