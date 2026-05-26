# PATH: fix.py
import os, re

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK: {label}")
    else:
        print(f"MISSING: {label}")

# This dynamically detects the folder where fix.py is located
BASE = os.path.dirname(os.path.abspath(__file__))

# ─── FIX 1: AuditPage.module.css ───────────────────────────────────
AUDIT_CSS = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Audit', 'AuditPage.module.css')

# Fix filterGrid: remove z-index:9000, use isolation instead
patch(
    AUDIT_CSS,
    '''.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: wrap;
    overflow: visible;
    width: 100%;
    padding-bottom: 4px;
    padding-top: 4px;
    position: relative;
    z-index: 9000;
}''',
    '''.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: wrap;
    overflow: visible;
    width: 100%;
    padding-bottom: 4px;
    padding-top: 4px;
    position: relative;
}''',
    'AuditPage: remove z-index from filterGrid (was creating stacking context)'
)

# Fix hwSelectWrap: give it isolation:isolate so each wrapper is its own
# stacking context, and the open one can climb above siblings via openWrapper.
patch(
    AUDIT_CSS,
    '''/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 1 1 140px;
    max-width: 240px;
    min-width: 120px;
    position: relative;
    overflow: visible !important;
}
.hwSelectWrap:focus-within {
    z-index: 10000 !important;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }
/* Force the inner fieldWrapper to overflow visible too */
.hwSelectWrap > div { overflow: visible !important; z-index: 9000 !important; }''',
    '''/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 1 1 140px;
    max-width: 240px;
    min-width: 120px;
    position: relative;
    overflow: visible !important;
    isolation: isolate;
}
/* When the HardwareSelect inside is open, elevate this wrapper above siblings */
.hwSelectWrap:focus-within,
.hwSelectWrap:has([class*="openWrapper"]) {
    isolation: auto;
    z-index: 10000 !important;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }
/* Force the inner fieldWrapper to overflow visible too */
.hwSelectWrap > div { overflow: visible !important; }''',
    'AuditPage: fix hwSelectWrap stacking so open dropdown escapes siblings'
)

# Also fix the mobile @media block that resets filterGrid z-index
patch(
    AUDIT_CSS,
    '''    .filterGrid  {
        flex-direction: row;
        flex-wrap: wrap;
        overflow: visible;
        width: 100%;
        gap: 6px;
        padding-bottom: 6px;
        padding-top: 4px;
        z-index: 9000;
    }''',
    '''    .filterGrid  {
        flex-direction: row;
        flex-wrap: wrap;
        overflow: visible;
        width: 100%;
        gap: 6px;
        padding-bottom: 6px;
        padding-top: 4px;
    }''',
    'AuditPage mobile: remove z-index from filterGrid in @media block'
)

patch(
    AUDIT_CSS,
    '''    .filterGrid  {
        flex-direction: row;
        flex-wrap: wrap;
        overflow: visible;
        gap: 5px;
        z-index: 9000;
    }''',
    '''    .filterGrid  {
        flex-direction: row;
        flex-wrap: wrap;
        overflow: visible;
        gap: 5px;
    }''',
    'AuditPage 480px: remove z-index from filterGrid'
)

# ─── FIX 2: HardwareSelect.module.css ──────────────────────────────
HS_CSS = os.path.join(BASE, 'erp-frontend', 'src', 'components', 'common', 'HardwareSelect.module.css')

patch(
    HS_CSS,
    '''.fieldWrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    position: relative;
    margin-bottom: 15px;
    z-index: 1;
}''',
    '''.fieldWrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    position: relative;
    margin-bottom: 15px;
}''',
    'HardwareSelect: remove z-index:1 from .fieldWrapper (was trapping all dropdowns equally)'
)

# ─── FIX 3: AuditPage.module.css bottom overrides ──────────────────
patch(
    AUDIT_CSS,
    '''/* Override previous Pill styles - strictly enforce Payments Filter Button design */
.hwSelectWrap {
    flex: 1 1 140px !important;
    min-width: 130px !important;
    max-width: 260px !important;
}''',
    '''/* Override previous Pill styles - strictly enforce Payments Filter Button design */
.hwSelectWrap {
    flex: 1 1 140px !important;
    min-width: 130px !important;
    max-width: 260px !important;
    position: relative !important;
    overflow: visible !important;
}''',
    'AuditPage: ensure hwSelectWrap in final polish block keeps overflow visible'
)

# Fix the dropdown z-index in HardwareSelect to be very high
patch(
    HS_CSS,
    '''.dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 8px 20px rgba(0,0,0,0.3);
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
    z-index: 99999 !important;
    min-width: 100%;
}''',
    '''.dropdown {
    position: fixed;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 8px 20px rgba(0,0,0,0.3);
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
    z-index: 99999 !important;
    min-width: 100%;
}''',
    'HardwareSelect: use position:fixed for dropdown so it escapes ALL stacking contexts'
)

print("\nAll patches applied.")git add -A && git commit -m "new change correction" && git push