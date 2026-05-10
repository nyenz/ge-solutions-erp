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

# ================================================================
# INTAKEPAGE.MODULE.CSS
# ================================================================
INTAKE_CSS = 'erp-frontend/src/pages/Intake/IntakePage.module.css'

# 1. ARREARS diagBox - make it a clean dark-bg read-only input style (standard)
patch(
    INTAKE_CSS,
    '''.diagBox {
    background: rgba(16, 185, 129, 0.12);
    border: 2px solid var(--green);
    padding: 0 clamp(14px, 1.8vw, 20px); border-radius: var(--radius-sm);
    display: flex; align-items: center; gap: clamp(10px, 1.2vw, 15px);
    height: var(--input-h); color: var(--green);
    font-size: clamp(11px, 1.2vw, 13px); font-weight: 800;
    font-family: 'Space Mono', monospace; min-width: 0;
}''',
    '''.diagBox {
    background: #000;
    border: 1.5px solid rgba(16, 185, 129, 0.5);
    padding: 0 clamp(10px, 1.4vw, 14px); border-radius: var(--radius-sm);
    display: flex; align-items: center; gap: clamp(10px, 1.2vw, 15px);
    height: var(--input-h); color: #10b981;
    font-size: clamp(11px, 1.2vw, 13px); font-weight: 800;
    font-family: 'Space Mono', monospace; min-width: 0;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.15);
}'''
)

# 2. Add Note button - match other action buttons (same height as primary)
patch(
    INTAKE_CSS,
    '''.addNoteBtn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100% !important;
    padding: clamp(8px, 1vw, 10px);
    border: 2px dashed var(--orange);
    color: var(--orange);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    cursor: pointer;
    background: rgba(238,140,58,0.04);
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: 4px;
    transition: background 0.2s, border-style 0.15s;
    box-sizing: border-box;
}
.addNoteBtn:hover { background: rgba(238,140,58,0.1); border-style: solid; }''',
    '''.addNoteBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(5px, 0.6vw, 7px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(14px, 1.8vw, 20px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 900;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    box-sizing: border-box;
    width: auto;
    align-self: flex-end;
}
.addNoteBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }'''
)

# 3. primaryCommitBtn - make it match "Save Entry" style: dark bg, orange border/text -> fills orange on hover
patch(
    INTAKE_CSS,
    '''.primaryCommitBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 9px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(16px, 2vw, 24px);
    background: #EE8C3A;
    border: 1.5px solid #EE8C3A;
    color: #1a2e30;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s;
    white-space: nowrap;
}
.primaryCommitBtn:hover:not(:disabled) {
    background: #f0a050;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}
.primaryCommitBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.primaryCommitBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }''',
    '''.primaryCommitBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 9px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(16px, 2vw, 24px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(238, 140, 58, 0.6);
    color: #EE8C3A;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    white-space: nowrap;
}
.primaryCommitBtn:hover:not(:disabled) {
    background: #EE8C3A;
    border-color: #EE8C3A;
    color: #1a2e30;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}
.primaryCommitBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.primaryCommitBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }'''
)

print("IntakePage CSS done")

# ================================================================
# FOLDERPAGE.MODULE.CSS
# ================================================================
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'

# 4. EDIT badge -> cyan-green (matching arrears green)
patch(
    FOLDER_CSS,
    '''/* EDIT MODE badge -- cyan accent, pulsing */
.editBadge {
    background: rgba(6, 182, 212, 0.12);
    border: 1.5px solid rgba(6, 182, 212, 0.4);
    color: #67e8f9;''',
    '''/* EDIT MODE badge -- green accent, pulsing */
.editBadge {
    background: rgba(16, 185, 129, 0.12);
    border: 1.5px solid rgba(16, 185, 129, 0.4);
    color: #34d399;'''
)

# 5. ARREARS calcInput in folder page - same as intake diagBox (dark bg, green glow)
patch(
    FOLDER_CSS,
    '.calcInput { background: #000; color: var(--cyan); border: 2px solid rgba(6,182,212,0.4) !important; opacity: 1; cursor: not-allowed; text-shadow: 0 0 8px rgba(6,182,212,0.4); font-family: \'Space Mono\', monospace; }',
    '.calcInput { background: #000; color: #10b981; border: 1.5px solid rgba(16,185,129,0.5) !important; opacity: 1; cursor: not-allowed; box-shadow: 0 0 8px rgba(16,185,129,0.15); font-family: \'Space Mono\', monospace; }'
)

# 6. autoCalcBadge -> green to match
patch(
    FOLDER_CSS,
    '.autoCalcBadge { font-size: clamp(6px, 0.7vw, 8px); font-weight: 900; color: var(--cyan); background: rgba(6,182,212,0.1); border: 1px solid rgba(6,182,212,0.25); padding: clamp(1px, 0.2vw, 2px) clamp(4px, 0.6vw, 6px); border-radius: 3px; letter-spacing: 1px; margin-left: auto; }',
    '.autoCalcBadge { font-size: clamp(6px, 0.7vw, 8px); font-weight: 900; color: #10b981; background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); padding: clamp(1px, 0.2vw, 2px) clamp(4px, 0.6vw, 6px); border-radius: 3px; letter-spacing: 1px; margin-left: auto; }'
)

# 7. Unify all ctrl-zone buttons: EDIT = same as save (orange outline -> fills orange)
# PAYMENT = grey -> green on hover/active
# BACKLOG = grey -> full red on hover/active  
# ABORT = grey -> full red on hover/active
# DELETE (purge) = grey -> full red on hover/active
# SAVE = orange (standard)
# PRINT = grey icon-only

patch(
    FOLDER_CSS,
    '''/* ── BASE PILL (used by all ctrl-zone buttons) ── */
.ctrlBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.08);
    border: 1.5px solid rgba(26, 46, 48, 0.22);
    color: var(--navy);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
    line-height: 1;
}
.ctrlBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── DARK BG PILL BASE (inside the terminal header dark panels) ── */
.darkCtrlBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
    line-height: 1;
}
.darkCtrlBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: var(--orange); }
.darkCtrlBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.darkCtrlBtn:disabled { opacity: 0.45; cursor: not-allowed; }

/* EDIT -- orange tint inactive, orange-filled active (same as Ledger activeFilter) */
.unlockMasterBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(238, 140, 58, 0.12);
    border: 1.5px solid rgba(238, 140, 58, 0.45);
    color: var(--orange);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, color 0.2s;
}
.unlockMasterBtn:hover, .unlockMasterBtn:focus-visible {
    background: #EE8C3A;
    color: #1a2e30;
    border-color: #EE8C3A;
    box-shadow: 0 0 14px rgba(238,140,58,0.35);
    outline: none;
}

/* SAVE -- orange filled (primary action) */
.btn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(12px, 1.6vw, 18px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    border: 1.5px solid transparent;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, color 0.2s;
    line-height: 1;
}
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

.btnPrimary {
    background: #EE8C3A;
    color: #1a2e30;
    border-color: #EE8C3A;
}
.btnPrimary:not(:disabled):hover {
    background: #f0a050;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}

/* ABORT -- muted transparent with red on hover */
.btnDanger {
    background: rgba(26, 46, 48, 0.75);
    border-color: rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.75);
}
.btnDanger:hover {
    background: rgba(239,68,68,0.15);
    border-color: rgba(239,68,68,0.5);
    color: #fca5a5;
}

/* DELETE (nuclear purge) -- red tint, stronger than abort */
.purgeBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(239, 68, 68, 0.10);
    border: 1.5px solid rgba(239, 68, 68, 0.35);
    color: #fca5a5;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}
.purgeBtn:hover { background: #ef4444; color: #fff; border-color: #ef4444; box-shadow: 0 0 12px rgba(239,68,68,0.35); }
.purgeBtn:focus-visible { outline: 2px solid #ef4444; outline-offset: 2px; }

/* PAYMENT -- green tint (money action) */
.ctrlBtnPay {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(16, 185, 129, 0.10);
    border: 1.5px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}
.ctrlBtnPay:hover { background: #10b981; color: #1a2e30; border-color: #10b981; box-shadow: 0 0 12px rgba(16,185,129,0.3); }
.ctrlBtnPay:focus-visible { outline: 2px solid #10b981; outline-offset: 2px; }

/* BACKLOG -- red tint (danger/warning action) */
.ctrlBtnBacklog {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(239, 68, 68, 0.10);
    border: 1.5px solid rgba(239, 68, 68, 0.30);
    color: #fca5a5;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
}
.ctrlBtnBacklog:hover { background: rgba(239,68,68,0.20); border-color: rgba(239,68,68,0.55); }
.ctrlBtnBacklog:focus-visible { outline: 2px solid #ef4444; outline-offset: 2px; }

/* PRINT icon-only */
.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    background: rgba(26, 46, 48, 0.08);
    border: 1.5px solid rgba(26, 46, 48, 0.20);
    color: var(--navy);
    border-radius: var(--radius-sm);
    font-size: clamp(14px, 1.6vw, 17px);
    cursor: pointer;
    transition: 0.2s;
    flex-shrink: 0;
}
.printBtn:hover { background: var(--navy); color: var(--orange); border-color: var(--navy); }

/* Ctrl group layout */
.ctrlGroup { display: flex; align-items: center; gap: clamp(6px, 0.9vw, 10px); flex-wrap: wrap; flex-shrink: 0; }
.handshakeActions { display: flex; gap: clamp(7px, 1vw, 10px); flex-wrap: wrap; }

/* icon buttons (trash, edit inside notes/docs) */''',
    '''/* ── STANDARD BUTTON BASE -- all buttons same height, same base shape ── */
/* Standard: grey bg + colored border/text -> fills color on hover */

/* EDIT -- same design as Save (orange outline -> fills orange) */
.unlockMasterBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(238, 140, 58, 0.6);
    color: #EE8C3A;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, color 0.2s;
    line-height: 1;
}
.unlockMasterBtn:hover, .unlockMasterBtn:focus-visible {
    background: #EE8C3A;
    color: #1a2e30;
    border-color: #EE8C3A;
    box-shadow: 0 0 14px rgba(238,140,58,0.35);
    outline: none;
}

/* SAVE -- grey + orange border -> fills orange (same pattern as edit) */
.btn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(12px, 1.6vw, 18px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    border: 1.5px solid transparent;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, color 0.2s;
    line-height: 1;
}
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

.btnPrimary {
    background: rgba(26, 46, 48, 0.75);
    border-color: rgba(238, 140, 58, 0.6);
    color: #EE8C3A;
}
.btnPrimary:not(:disabled):hover {
    background: #EE8C3A;
    border-color: #EE8C3A;
    color: #1a2e30;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}

/* ABORT -- grey -> full red on hover */
.btnDanger {
    background: rgba(26, 46, 48, 0.75);
    border-color: rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.75);
}
.btnDanger:hover {
    background: #ef4444;
    border-color: #ef4444;
    color: #fff;
    box-shadow: 0 0 12px rgba(239,68,68,0.35);
}

/* DELETE (nuclear purge) -- grey -> full red on hover */
.purgeBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(239, 68, 68, 0.45);
    color: #fca5a5;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    line-height: 1;
}
.purgeBtn:hover { background: #ef4444; color: #fff; border-color: #ef4444; box-shadow: 0 0 12px rgba(239,68,68,0.35); }
.purgeBtn:focus-visible { outline: 2px solid #ef4444; outline-offset: 2px; }

/* PAYMENT -- grey -> full green on hover */
.ctrlBtnPay {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(16, 185, 129, 0.45);
    color: #34d399;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    line-height: 1;
}
.ctrlBtnPay:hover { background: #10b981; color: #1a2e30; border-color: #10b981; box-shadow: 0 0 12px rgba(16,185,129,0.3); }
.ctrlBtnPay:focus-visible { outline: 2px solid #10b981; outline-offset: 2px; }

/* BACKLOG -- grey -> full red on hover */
.ctrlBtnBacklog {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(239, 68, 68, 0.45);
    color: #fca5a5;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    line-height: 1;
}
.ctrlBtnBacklog:hover { background: #ef4444; color: #fff; border-color: #ef4444; box-shadow: 0 0 12px rgba(239,68,68,0.35); }
.ctrlBtnBacklog:focus-visible { outline: 2px solid #ef4444; outline-offset: 2px; }

/* PRINT icon-only */
.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.6);
    border-radius: var(--radius-sm);
    font-size: clamp(14px, 1.6vw, 17px);
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    flex-shrink: 0;
    line-height: 1;
}
.printBtn:hover { background: rgba(255,255,255,0.12); color: #fff; border-color: rgba(255,255,255,0.35); }

/* ctrlBtn unused but kept for legacy */
.ctrlBtn { display: inline-flex; align-items: center; gap: 6px; height: clamp(32px, 4vw, 38px); padding: 0 clamp(10px, 1.3vw, 15px); background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px,0.9vw,11px); text-transform: uppercase; letter-spacing: 1px; cursor: pointer; white-space: nowrap; flex-shrink: 0; transition: all 0.2s; line-height: 1; }
.ctrlBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: var(--orange); }
.ctrlBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* Ctrl group layout */
.ctrlGroup { display: flex; align-items: center; gap: clamp(6px, 0.9vw, 10px); flex-wrap: wrap; flex-shrink: 0; }
.handshakeActions { display: flex; gap: clamp(7px, 1vw, 10px); flex-wrap: wrap; }
.darkCtrlBtn { display: inline-flex; align-items: center; gap: 6px; height: clamp(32px, 4vw, 38px); padding: 0 clamp(10px,1.3vw,15px); background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px,0.9vw,11px); text-transform: uppercase; letter-spacing: 1px; cursor: pointer; transition: all 0.2s; line-height: 1; white-space: nowrap; flex-shrink: 0; }
.darkCtrlBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: var(--orange); }
.darkCtrlBtn:disabled { opacity: 0.45; cursor: not-allowed; }

/* icon buttons (trash, edit inside notes/docs) */'''
)

print("FolderPage CSS button section done")

# 8. Remove backlog banner from top of FolderPage JSX, add it inside Financials
FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Remove the standalone backlog banner div from top of main content
patch(
    FOLDER_JSX,
    '''            {/* BACKLOG BANNER */}
            {isBacklog && (
                <div style={{
                    background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)',
                    borderRadius: 8, padding: '12px 20px', marginBottom: 16,
                    display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap'
                }}>
                    <FiAlertOctagon style={{ color: '#ef4444', flexShrink: 0 }} size={20} />
                    <div style={{ flex: 1 }}>
                        <strong style={{ color: '#ef4444' }}>BACKLOG STATUS -- STORAGE FEES ACTIVE</strong>
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
    '''            {/* PIPELINE HUD */}'''
)

# Now add the backlog notice inside the Financials section (inside the non-editing view)
patch(
    FOLDER_JSX,
    '''                            ) : isBacklog ? (
                                /* BACKLOG FINANCIAL BREAKDOWN */
                                <div>''',
    '''                            ) : isBacklog ? (
                                /* BACKLOG FINANCIAL BREAKDOWN */
                                <div>
                                    {/* Backlog notice at top of financials */}
                                    <div style={{
                                        background: 'rgba(239,68,68,0.10)', border: '1px solid rgba(239,68,68,0.35)',
                                        borderRadius: 7, padding: '10px 14px', marginBottom: 14,
                                        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap'
                                    }}>
                                        <FiAlertOctagon style={{ color: '#ef4444', flexShrink: 0 }} size={16} />
                                        <div style={{ flex: 1 }}>
                                            <strong style={{ color: '#ef4444', fontSize: '0.8rem', fontFamily: 'DM Sans,sans-serif', fontWeight: 900, textTransform: 'uppercase', letterSpacing: 1 }}>BACKLOG STATUS — STORAGE FEES ACTIVE</strong>
                                            <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', marginTop: 2, fontFamily: 'DM Sans,sans-serif' }}>
                                                UGX 50,000 is added every month until the full balance is cleared.
                                            </div>
                                        </div>
                                        {isAdmin && (
                                            <button onClick={handleExitBacklog} className={styles.ctrlBtnBacklog} style={{ height: 30, fontSize: 10, padding: '0 10px' }}>
                                                EXIT BACKLOG
                                            </button>
                                        )}
                                    </div>'''
)

print("FolderPage JSX backlog banner moved to financials")

# 9. Also update the pipeline HUD protocol readout for backlog to not duplicate info
# The pipeline HUD already shows BACKLOG in protocolReadout, that's fine

# ================================================================
# INTAKEPAGE.JSX - fix the addNoteBtn wrapper to be flex-end aligned
# ================================================================
INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Fix the addNoteBtn placement to be right-aligned like other action buttons
patch(
    INTAKE_JSX,
    '''                                <button type="button" className={styles.addNoteBtn}
                                    onClick={() => { setEditingNoteIdx(null); setNoteModalText(''); setNoteModalOpen(true); }}>
                                    + ADD NOTE
                                </button>''',
    '''                                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                                    <button type="button" className={styles.addNoteBtn}
                                        onClick={() => { setEditingNoteIdx(null); setNoteModalText(''); setNoteModalOpen(true); }}>
                                        + ADD NOTE
                                    </button>
                                </div>'''
)

print("IntakePage JSX add note button aligned")

# ================================================================
# FOLDERPAGE.MODULE.CSS - also fix the add note / add doc buttons
# inside the folder page to be consistent
# ================================================================

patch(
    FOLDER_CSS,
    '''.addDocBtn { display: flex; align-items: center; justify-content: center; width: 100% !important; padding: clamp(7px, 1vw, 9px); margin-top: clamp(6px, 0.8vw, 8px); border: 2px dashed var(--orange); color: var(--orange); font-family: 'DM Sans', sans-serif; font-size: var(--fs-tag); font-weight: 900; cursor: pointer; background: rgba(238,140,58,0.04); text-transform: uppercase; letter-spacing: 1px; text-align: center; border-radius: 4px; transition: background 0.2s, border-style 0.15s; box-sizing: border-box; }
.addDocBtn:hover        { background: var(--orange-dim); border-style: solid; }
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

print("FolderPage add doc/note buttons unified")

# Also fix the metaTags to use the standard uniform design
patch(
    FOLDER_CSS,
    '''/* COLLECTION % -- muted navy pill (matches ledger tagStandard) */
.tagBlue {
    background: rgba(26, 46, 48, 0.75);
    border-color: rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
}
/* ACTIVE status -- muted with orange tint (matches ledger tagStandard + hint) */
.tagOrange {
    background: rgba(238, 140, 58, 0.10);
    border-color: rgba(238, 140, 58, 0.35);
    color: var(--orange);
}''',
    '''/* COLLECTION % -- muted pill */
.tagBlue {
    background: rgba(26, 46, 48, 0.6);
    border-color: rgba(255, 255, 255, 0.15);
    color: rgba(255, 255, 255, 0.8);
}
/* ACTIVE status */
.tagOrange {
    background: rgba(26, 46, 48, 0.6);
    border-color: rgba(238, 140, 58, 0.5);
    color: #EE8C3A;
}'''
)

print("All patches complete!")
print("\nRun: git add -A && git commit -m 'unify button/badge design: save=standard, edit=orange, payment/backlog=grey->color, abort/delete=grey->red, arrears=green, backlog warning in financials' && git push")