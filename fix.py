import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING in {path}: {repr(old[:80])}")
        return
    content = content.replace(old, new, 1)
    write(path, content)
    print(f"PATCHED: {path}")

FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# ================================================================
# PATCH 1: addDocBtn in FolderPage.module.css
# The previous fix.py had the single-line version already in the file.
# We replace what's actually there now.
# ================================================================
patch(
    FOLDER_CSS,
    '''.addDocBtn { display: flex; align-items: center; justify-content: center; width: 100% !important; padding: clamp(7px, 1vw, 9px); margin-top: clamp(6px, 0.8vw, 8px); border: 2px dashed var(--orange); color: var(--orange); font-family: 'DM Sans', sans-serif; font-size: var(--fs-tag); font-weight: 900; cursor: pointer; background: rgba(238,140,58,0.04); text-transform: uppercase; letter-spacing: 1px; text-align: center; border-radius: 4px; transition: background 0.2s, border-style 0.15s; box-sizing: border-box; }
.addDocBtn:hover { background: var(--orange-dim); border-style: solid; }
.addDocBtn:focus-visible { outline: 2px solid var(--orange); }''',
    '''.addDocBtn {
    display: inline-flex; align-items: center; justify-content: center;
    gap: clamp(4px, 0.5vw, 6px);
    height: clamp(30px, 3.8vw, 36px);
    padding: 0 clamp(12px, 1.5vw, 16px);
    margin-top: clamp(6px, 0.8vw, 8px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(238, 140, 58, 0.45);
    color: #EE8C3A;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.85vw, 10px);
    font-weight: 900;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    box-sizing: border-box;
    width: 100%;
}
.addDocBtn:hover { background: #EE8C3A; color: #1a2e30; border-color: #EE8C3A; box-shadow: 0 0 10px rgba(238,140,58,0.3); }
.addDocBtn:focus-visible { outline: 2px solid var(--orange); }'''
)

# ================================================================
# PATCH 2: addNoteBtn in FolderPage.module.css
# ================================================================
patch(
    FOLDER_CSS,
    '''.addNoteBtn { display: flex; align-items: center; justify-content: center; width: 100% !important; padding: clamp(7px, 1vw, 9px); margin-top: clamp(6px, 0.8vw, 8px); border: 2px dashed var(--orange); color: var(--orange); font-family: 'DM Sans', sans-serif; font-size: var(--fs-tag); font-weight: 900; cursor: pointer; background: rgba(238,140,58,0.04); text-transform: uppercase; letter-spacing: 1px; text-align: center; border-radius: 4px; transition: background 0.2s, border-style 0.15s; box-sizing: border-box; }
.addNoteBtn:hover  { background: var(--orange-dim); border-style: solid; }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }''',
    '''.addNoteBtn {
    display: inline-flex; align-items: center; justify-content: center;
    gap: clamp(4px, 0.5vw, 6px);
    height: clamp(30px, 3.8vw, 36px);
    padding: 0 clamp(12px, 1.5vw, 16px);
    margin-top: clamp(6px, 0.8vw, 8px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(238, 140, 58, 0.45);
    color: #EE8C3A;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.85vw, 10px);
    font-weight: 900;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    box-sizing: border-box;
    width: auto;
    align-self: flex-end;
}
.addNoteBtn:hover { background: #EE8C3A; color: #1a2e30; border-color: #EE8C3A; box-shadow: 0 0 10px rgba(238,140,58,0.3); }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }'''
)

# ================================================================
# PATCH 3: Remove backlog banner from top of FolderPage.jsx
# The banner is already partially removed, but the PIPELINE HUD
# comment block may still be there with the banner. Let's check
# what the JSX currently has after the previous partial patch.
# The JSX patch succeeded in adding the notice INSIDE financials.
# The banner removal MISSED. So we need to remove the remaining banner.
# After the previous run, the file has the financials notice added
# but the top banner still present (since that patch said MISSING).
# Let's remove it now with the exact current text.
# ================================================================
patch(
    FOLDER_JSX,
    '''        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing || paying} />

            {/* BACKLOG BANNER */}
            {isBacklog && (
                <div style={{
                    background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)',
                    borderRadius: 8, padding: '12px 20px', marginBottom: 16,
                    display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap'
                }}>
                    <FiAlertOctagon style={{ color: '#ef4444', flexShrink: 0 }} size={20} />
                    <div style={{ flex: 1 }}>
                        <strong style={{ color: '#ef4444' }}>BACKLOG STATUS — STORAGE FEES ACTIVE</strong>
                        <div style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: 2 }}>
                            UGX 50,000 is added to this plot every month until the full balance is cleared.
                        </div>
                    </div>
                    {isAdmin && (
                        <button onClick={handleExitBacklog}
                            style={{ background: 'rgba(239,68,68,0.2)', border: '1px solid #ef4444',
                                color: '#ef4444', borderRadius: 6, padding: '6px 14px',
                                cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700 }}>
                            EXIT BACKLOG
                        </button>
                    )}
                </div>
            )}

            {/* PIPELINE HUD */}''',
    '''        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing || paying} />

            {/* PIPELINE HUD */}'''
)

print("\nAll 3 missing patches applied.")
print("Run: git add -A && git commit -m 'fix missing patches: addDocBtn/addNoteBtn unified, backlog banner removed from top' && git push")