#!/usr/bin/env python3
# PATH: fix142.py
# GOLDEN SEED -- fix142: the guide gets REAL design code and the fix.py TEMPLATE.
#
#   1. SECTION 7: new "DESIGN REFERENCE CODE" block -- the actual CSS of the five
#      reference pages, copied from the code: Intake panels + dropdown + inputs,
#      Ledger table, Reports lists, Recovery popup + colour/font emphasis,
#      Settings tabs + section colours. (fix141 only described them in words.)
#   2. SECTION 9: new 9.1 "THE fix.py TEMPLATE" (the exact format this very file
#      uses) and 9.2 "FORMAT RULES". From now on David does NOT have to upload or
#      clone fix.py so an LLM can learn the format -- the guide carries it.
#   3. SECTION 9: the old rule "guide is a separate file, output separately" gets a
#      SUPERSEDED note (the guide is now changed by patches inside fix.py).
#
# NOT in this fix: no app code is touched, nothing is bought or moved.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Docs only, so the backend
# compile and frontend build are skipped (RUN_GATES = False). Needs fix141 first.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
# Names, and one variable per file this fix touches.
FIX_NO = "fix142"
COMMIT_MSG = "fix142: guide gets the real CSS of the five design reference pages and the fix.py template + format rules, so the fix.py file no longer needs to be uploaded for an LLM to learn the format"
RUN_GATES = False   # docs-only fix (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
# ============================= EDIT PART 1 END =============================

# ================== DO NOT EDIT: helpers (copy exactly) ====================
MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# sub = exact find/replace of the FIRST match. Prints OK / SKIP / MISSING.
def sub(text, old, new, desc):
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


# newfile = create (or replace) a whole file. SKIP if it already holds `marker`.
def newfile(path, text, label, marker):
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)


# ============================ EDIT PART 2 START ============================
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (GUIDE,)
for _p in LOAD_FILES:
    load(_p)

DESIGN_CODE = r'''### DESIGN REFERENCE CODE (copied from the code, September 2026)
**The CSS files always win if they differ from this copy.** Same numbering as the reference pages above. Use these as the starting point when you build or change an element. Colour tokens: orange `#EE8C3A`, navy `#1a2e30`. In the Recovery emphasis block several rules exist for one class -- the LAST one wins.

**1a. Panel (Intake sections)** (`components/ui/CollapsibleSection.module.css`)
```css
.section { --orange: #EE8C3A; --orange-dim: rgba(238, 140, 58, 0.18); position: relative; background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%); border: 1px solid rgba(238, 140, 58, 0.2); border-radius: 10px; overflow: visible; box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25); transition: border-color 0.3s ease, box-shadow 0.3s ease; }
.section:hover { border-color: var(--orange); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }
.section.accent { border: 2px solid var(--orange); }
.header { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: clamp(6px, 1vw, 12px); padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 16px); background: #162a2c; border: none; border-bottom: 1.5px solid transparent; border-radius: 9px; cursor: pointer; text-align: left; font: inherit; color: inherit; transition: border-bottom-color 0.25s ease, border-radius 0.25s ease; }
.headerOpen { border-radius: 9px 9px 0 0; border-bottom-color: var(--orange); }
.title { font-family: 'Cinzel', serif; font-size: clamp(10px, 1.3vw, 13px); font-weight: 700; color: var(--orange); letter-spacing: 2px; text-transform: uppercase; margin: 0; transition: color 0.18s ease; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.header:hover .title { color: #fff; }
.chevron { color: rgba(255, 255, 255, 0.4); font-size: 14px; transition: transform 0.2s ease, color 0.2s ease; flex-shrink: 0; }
.chevronOpen { transform: rotate(180deg); color: var(--orange); }
.body { position: relative; padding: 0 clamp(10px, 1.4vw, 16px) clamp(10px, 1.4vw, 16px); padding-top: clamp(10px, 1.4vw, 16px); display: flex; flex-direction: column; gap: clamp(7px, 1.1vw, 14px); animation: expand 0.2s ease-out; }
```

**1b. Panel corner brackets** (`components/ui/CornerDecor.module.css`)
```css
.cornerAccent { position: absolute; width: 14px; height: 14px; border: 1.5px solid var(--orange); opacity: 0.55; pointer-events: none; }
.cornerAccent::after { content: ''; position: absolute; width: 4px; height: 4px; background: rgba(255, 255, 255, 0.5); border-radius: 50%; box-shadow: 0 0 6px rgba(255, 255, 255, 0.4); }
```

**1c. Dropdown** (`components/common/HardwareSelect.module.css`)
```css
.selectBox { background: #ffffff; border-radius: var(--input-radius, 6px); border: 1.5px solid rgba(238, 140, 58, 0.3); padding: 0 var(--input-px, clamp(9px, 1.2vw, 13px)); display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: border-color 0.2s, box-shadow 0.2s; height: var(--input-height, clamp(34px, 4.3vw, 40px)); position: relative; z-index: 1; }
.selectBox:hover, .active { border-color: var(--orange); box-shadow: 0 0 0 2px rgba(238, 140, 58, 0.15); }
.currentValue { color: var(--navy); font-weight: 700; font-size: var(--input-font, clamp(11px, 1.05vw, 13px)); letter-spacing: 0.5px; }
.dropdown { position: absolute; top: calc(100% + 4px); left: 0; min-width: 100%; width: max-content; background: #ffffff; border: 1.5px solid var(--orange); border-radius: 6px; box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5), 0 6px 16px rgba(0,0,0,0.3); overflow: hidden; animation: slideIn 0.2s ease-out; z-index: 99999 !important; }
.option { padding: clamp(8px, 1vw, 11px) clamp(12px, 1.4vw, 16px); color: var(--navy); font-weight: 700; font-size: clamp(11px, 1.05vw, 13px); letter-spacing: 0.5px; background: #ffffff; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: 0.2s; }
.option:hover { background: var(--orange); color: white; }
.selected { background: var(--orange); color: white; }
```

**1d. Inputs and type buttons** (`pages/Intake/IntakePage.module.css`)
```css
.input, .textarea { font-family: 'Inter', sans-serif; font-weight: 600; border: 1.5px solid rgba(238,140,58,0.3); background: #ffffff; color: var(--navy); width: 100%; box-sizing: border-box; transition: border-color 0.2s, box-shadow 0.2s; }
.input:hover, .textarea:hover { border-color: var(--orange); }
.input:focus, .textarea:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 2px rgba(238,140,58,0.15); }
.typeBtn { display: flex; align-items: center; gap: 5px; background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: 6px; font-family: 'Inter', sans-serif; font-weight: 900; font-size: var(--fs-btn); letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; transition: all 0.2s ease; white-space: nowrap; }
.typeBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.typeBtnActive, .typeBtnActive:hover { background: #EE8C3A; color: #1a2e30; border-color: #EE8C3A; box-shadow: 0 0 14px rgba(238,140,58,0.4); }
.btn { font-family: 'Inter', sans-serif; font-size: var(--fs-btn); font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: var(--radius-sm); border: 1.5px solid rgba(255,255,255,0.1); background: transparent; color: rgba(255,255,255,0.7); cursor: pointer; transition: background 0.2s, border-color 0.2s, color 0.2s; display: inline-flex; align-items: center; gap: 5px; text-decoration: none; }
.btn.primary { background: var(--orange); color: #fff; border-color: var(--orange); }
.dropzone { border: 2px dashed rgba(238,140,58,0.4); border-radius: var(--radius); padding: clamp(12px,1.6vw,18px); text-align: center; color: rgba(255,255,255,0.55); cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.noteDateChip { align-self: flex-start; display: inline-flex; align-items: center; gap: 5px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.08); color: rgba(255,255,255,0.6); font-size: var(--fs-meta); font-weight: 800; letter-spacing: 1px; padding: 3px 8px; border-radius: 4px; }
```

**2. LEDGER table** (`pages/Ledger/LedgerPage.module.css`)
```css
.tablePanel { position:relative; background:linear-gradient(160deg,#1c3335 0%,#213E40 100%); border:1.5px solid var(--orange-border); border-radius:var(--radius); padding:0; isolation:isolate; }
.decorBl,.decorBr { position:absolute; width:14px; height:14px; border:1.5px solid var(--orange); opacity:.55; pointer-events:none; z-index:20; }
.tableScroll { max-height:calc(100vh - 220px); min-height:280px; overflow:auto; overscroll-behavior:contain; overflow-anchor:none; border-radius:var(--radius); scrollbar-width:none; -ms-overflow-style:none; transform:translateZ(0); }
.ledgerTable { width:100%; border-collapse:separate; border-spacing:0; min-width:700px; }
.ledgerTable thead th { position:sticky; top:0; z-index:5; background:#162a2c; color:var(--orange); font-size:var(--fs-th); font-weight:900; letter-spacing:2px; text-transform:uppercase; text-align:left; padding:clamp(11px,1.5vw,18px) clamp(12px,1.8vw,20px); border-bottom:3px solid var(--orange); white-space:nowrap; user-select:none; box-shadow:0 1px 0 var(--orange); }
.sortable { cursor:pointer; transition:background .18s,color .18s; }
.sortable:hover { background:linear-gradient(rgba(238,140,58,0.12),rgba(238,140,58,0.12)),#162a2c; color:#fff; }
.ledgerTable tbody td { padding:12px 14px; border-bottom:1px solid rgba(255,255,255,0.06); vertical-align:top; color:#fff; font-size:var(--fs-td); }
.ledgerTable tbody td.rowNum { font-family:'Space Mono',monospace; color:rgba(255,255,255,0.5); }
.ledgerTable tbody tr { cursor:pointer; transition:background .15s; border-left:3px solid transparent; }
.ledgerTable tbody tr:hover { background:rgba(255,255,255,0.04); border-left-color:var(--orange); }
.searchInner { position:relative; display:flex; align-items:center; background:#fff; border:1.5px solid #c8d6d7; border-radius:6px; height:clamp(36px,4.5vw,44px); transition:border-color .2s,box-shadow .2s; }
.searchInner:focus-within { border-color:var(--orange); box-shadow:0 0 0 3px rgba(238,140,58,0.18); }
.filterBtn { background:rgba(26,46,48,0.75); border:1.5px solid rgba(255,255,255,0.18); color:rgba(255,255,255,0.85); padding:8px 16px; border-radius:6px; font-weight:900; font-size:10px; letter-spacing:1.5px; text-transform:uppercase; cursor:pointer; white-space:nowrap; transition:all .2s; }
.filterBtn:hover { background:rgba(238,140,58,0.12); color:var(--orange); border-color:var(--orange); }
.activeFilter { background:var(--orange) !important; color:#1a2e30 !important; border-color:var(--orange) !important; }
.pageBtn { background:rgba(26,46,48,0.75); border:1.5px solid rgba(255,255,255,0.18); color:rgba(255,255,255,0.85); padding:7px 14px; border-radius:6px; font-weight:900; font-size:10px; cursor:pointer; display:inline-flex; gap:6px; align-items:center; transition:all .2s; }
.pageBtn:hover:not(:disabled) { background:rgba(255,255,255,0.07); border-color:rgba(255,255,255,0.22); color:#fff; }
.stageDot { width:7px; height:7px; border-radius:50%; background:rgba(255,255,255,0.18); flex-shrink:0; }
.stageDotDone { background:var(--green); box-shadow:0 0 4px var(--green); }
.stageDotCurrent { background:var(--orange); box-shadow:0 0 4px var(--orange); }
.stageDotPart { background: var(--orange); box-shadow: 0 0 4px var(--orange); }
```

**3. REPORTS lists** (`pages/Reports/ReportHub.module.css`) -- colour tokens
```css
.container {
  --orange: #EE8C3A;
  --orange-dim: rgba(238, 140, 58, 0.18);
  --orange-border: rgba(238, 140, 58, 0.28);
  --navy: #1a2e30;
  --panel-bg: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  --panel-border: rgba(238, 140, 58, 0.2);
  --red: #ef4444;
  --green: #4ade80;
  --gap-lg: clamp(10px, 1.5vw, 13px);
  --gap-md: clamp(7px, 1.1vw, 9px);
  --radius: 12px;
  --radius-sm: 6px;
  --fs-h1: clamp(18px, 2.5vw, 24px);
  --fs-sub: clamp(8px, 0.85vw, 10px);
  --fs-drawer:clamp(9px, 0.9vw, 11px);
  --fs-title: clamp(11px, 1.1vw, 13px);
  --fs-desc: clamp(10px, 1vw, 12px);
  --fs-btn: clamp(8px, 0.85vw, 10px);
  --fs-label: clamp(7px, 0.75vw, 9px);
}
```

**3. REPORTS panel and rows** (`pages/Reports/ReportHub.module.css`)
```css
.hwPanel { background: var(--panel-bg); border: 1.5px solid var(--panel-border); border-radius: var(--radius); overflow: visible; box-shadow: 0 8px 24px rgba(0,0,0,0.14); transition: border-color 0.2s; }
.hwPanel:hover { border-color: rgba(238,140,58,0.38); }
.reportRowWrap { border-bottom: 1px solid rgba(255,255,255,0.05); }
.reportRow { display: grid; grid-template-columns: clamp(36px,4vw,48px) 1fr clamp(24px,2.8vw,32px); align-items: center; gap: clamp(8px,1.2vw,13px); padding: clamp(11px,1.4vw,16px) clamp(12px,1.5vw,17px); cursor: pointer; user-select: none; outline: none; transition: background 0.18s; }
.reportRow:hover { background: rgba(255,255,255,0.035); }
.reportRowActive { background: rgba(238,140,58,0.06); border-left: 3px solid var(--orange); }
.iconFrame { width: clamp(28px,3.2vw,36px); height: clamp(28px,3.2vw,36px); background: var(--orange-dim); border: 1px solid var(--orange-border); border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; color: var(--orange); font-size: clamp(12px,1.3vw,15px); flex-shrink: 0; }
.rptTitle { font-family: 'Space Mono', monospace; font-weight: 900; color: #fff; font-size: var(--fs-title); letter-spacing: 0.5px; }
.rowChevron { color: rgba(255,255,255,0.3); font-size: clamp(14px,1.6vw,18px); transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), color 0.2s; flex-shrink: 0; justify-self: end; }
.reportRow:hover .rowChevron { color: var(--orange); }
.detailBox { background: #0a0a0a; border-top: 1px solid rgba(255,255,255,0.08); border-left: clamp(3px,0.4vw,4px) solid var(--orange); padding: clamp(14px,1.8vw,20px) clamp(16px,2vw,22px); page-break-inside: avoid; break-inside: avoid; }
.libLabel { font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(8px,0.85vw,10px); letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.6); }
.libList .reportRowWrap { border-bottom: none; background: #fff; border: 1.5px solid rgba(255,255,255,0.14); border-radius: 6px; overflow: hidden; }
.libList .reportRow { padding: clamp(9px,1.2vw,13px) clamp(10px,1.4vw,15px); }
.libList .reportRow:hover { background: rgba(238,140,58,0.07); }
.libList .reportRowActive { background: rgba(238,140,58,0.09); border-left: 3px solid var(--orange); }
.libList .rptTitle { color: #1a2e30; }
.libList .rowChevron { color: rgba(26,46,48,0.35); }
.libList .iconFrame { background: rgba(238,140,58,0.12); }
.libList .detailBox { border-top: 1px solid rgba(255,255,255,0.08); }
.libChip { font-family: 'Inter', sans-serif; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; font-size: clamp(8px,0.85vw,10px); padding: clamp(7px,0.95vw,10px) clamp(10px,1.4vw,16px); border-radius: 6px; border: 1.5px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.85); cursor: pointer; transition: all 0.2s ease; white-space: nowrap; }
```

**4a. RECOVERY popup (HardwareModal)** (`components/common/HardwareModal.module.css`)
```css
.backdrop { position: fixed; inset: 0; background: rgba(10, 20, 25, 0.80); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; z-index: 99999; animation: fadeIn 0.2s ease-out; padding: clamp(12px, 3vw, 24px); box-sizing: border-box; }
.modalBody { width: 100%; max-width: clamp(300px, 90vw, 520px); max-height: 90vh; overflow-y: auto; background: linear-gradient(160deg, #1c3335 0%, #213e40 100%); border: 2px solid rgba(238, 140, 58, 0.4); border-radius: 14px; padding: clamp(20px, 3vw, 32px); position: relative; box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255,255,255,0.04), inset 0 1px 0 rgba(255,255,255,0.06); animation: slideUp 0.25s cubic-bezier(0.2, 1, 0.3, 1); scrollbar-width: thin; scrollbar-color: rgba(238,140,58,0.4) transparent; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: clamp(16px, 2.5vw, 24px); padding-bottom: clamp(10px, 1.5vw, 14px); border-bottom: 1px solid rgba(238, 140, 58, 0.25); }
.title { font-family: 'Cinzel', serif; color: var(--orange, #EE8C3A); font-size: clamp(12px, 1.4vw, 16px); font-weight: 700; letter-spacing: clamp(1px, 0.2vw, 2.5px); text-transform: uppercase; line-height: 1.2; flex: 1; min-width: 0; word-break: break-word; }
.closeBtn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); color: rgba(255,255,255,0.5); font-size: clamp(16px, 2vw, 20px); cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; width: clamp(28px, 3.5vw, 36px); height: clamp(28px, 3.5vw, 36px); border-radius: 8px; flex-shrink: 0; margin-left: 12px; }
.closeBtn:hover { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.4); color: #ef4444; transform: rotate(90deg); }
.modalLabel { display: block; font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px); font-weight: 900; color: rgba(255, 255, 255, 0.5); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0; }
.modalFooter { display: flex; justify-content: flex-end; align-items: center; gap: clamp(8px, 1.2vw, 12px); margin-top: clamp(14px, 1.8vw, 20px); padding-top: clamp(12px, 1.5vw, 16px); border-top: 1px solid rgba(255, 255, 255, 0.08); flex-wrap: wrap; }
.modalBtnPrimary { display: inline-flex; align-items: center; gap: clamp(6px, 0.8vw, 9px); padding: 0 clamp(16px, 2vw, 24px); height: clamp(38px, 4.8vw, 46px); background: #EE8C3A; color: #1a2e30; border: none; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(10px, 1vw, 12px); text-transform: uppercase; letter-spacing: 1.5px; cursor: pointer; transition: background 0.2s, box-shadow 0.2s, transform 0.15s; white-space: nowrap; flex-shrink: 0; }
.modalBtnPrimary:hover:not(:disabled) { background: #f0a050; box-shadow: 0 0 20px rgba(238, 140, 58, 0.4); transform: translateY(-1px); }
.modalBtnSecondary { display: inline-flex; align-items: center; gap: clamp(5px, 0.7vw, 8px); padding: 0 clamp(14px, 1.8vw, 20px); height: clamp(38px, 4.8vw, 46px); background: rgba(255, 255, 255, 0.06); color: rgba(255, 255, 255, 0.7); border: 1.5px solid rgba(255, 255, 255, 0.2); border-radius: 8px; font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(10px, 1vw, 12px); text-transform: uppercase; letter-spacing: 1.5px; cursor: pointer; transition: background 0.2s, color 0.2s, border-color 0.2s; white-space: nowrap; flex-shrink: 0; }
.modalBtnSecondary:hover { background: rgba(255, 255, 255, 0.12); color: #fff; border-color: rgba(255, 255, 255, 0.35); }
.modalInput, .modalTextarea, [class*="modalInput"], [class*="modalTextarea"] { color: rgba(255, 255, 255, 0.95) !important; -webkit-text-fill-color: rgba(255, 255, 255, 0.95) !important; caret-color: #ffffff; background: rgba(255, 255, 255, 0.08) !important; }
.modalInput:focus, .modalTextarea:focus, [class*="modalInput"]:focus, [class*="modalTextarea"]:focus { color: rgba(255, 255, 255, 0.95) !important; -webkit-text-fill-color: rgba(255, 255, 255, 0.95) !important; background: rgba(255, 255, 255, 0.12) !important; }
```

**4b. RECOVERY colour and font emphasis (ALL rules in file order -- the LAST one wins)** (`pages/Recovery/RecoveryPortal.module.css`)
```css
.cname { font-size: var(--fs-td); font-weight: 800; margin: 0; text-transform: uppercase; letter-spacing: 0.3px; }
.cname { font-size: clamp(13px, 1.6vw, 16px); }
.cname { font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(13px, 1.6vw, 16px); letter-spacing: 0.3px; }
.cname { font-family: 'Cinzel', serif; font-size: clamp(10px, 1.3vw, 13px); font-weight: 700; color: var(--orange); letter-spacing: 2px; text-transform: uppercase; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: color 0.18s ease; }
.cname { text-align: left; }
.nin { font-family: 'Space Mono',monospace; font-size: 11px; color: var(--orange); }
.nin { color: #ffb46b; }
.chipPos { background: rgba(16,185,129,0.10); color: #34d399; border-color: rgba(16,185,129,0.35); }
.chipPos { color: #34d399; }
.chipNeg { background: rgba(239,68,68,0.12); color: #fca5a5; border-color: rgba(239,68,68,0.4); }
.chipNeg { color: #fca5a5; }
.chipNone { color: rgba(255,255,255,0.4); border: 1px dashed rgba(255,255,255,0.25); }
.chipNone { color: rgba(255, 255, 255, 0.5); }
.callPos { font-family: 'Space Mono',monospace; font-size: 10px; font-weight: 900; border-radius: 999px; padding: 3px 9px; border: 1px solid rgba(6,182,212,0.4); color: #67e8f9; background: rgba(6,182,212,0.12); white-space: nowrap; }
.callPos { background: none !important; border: none !important; padding: 0 !important; border-radius: 0; font-family: 'Space Mono', monospace; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1px; text-transform: uppercase; }
.secLabel { font-family: 'DM Sans', sans-serif; font-size: clamp(7px, 0.8vw, 9px); font-weight: 900; letter-spacing: 2px; color: var(--orange); text-transform: uppercase; }
.secLabel { color: #ffb46b; }
.coLine { font-size: 11px; color: rgba(255,255,255,0.7); display: flex; gap: 6px; align-items: center; }
.coLine { color: rgba(255, 255, 255, 0.85); }
.attemptLine { display: flex; align-items: center; gap: 8px; font-size: var(--fs-meta); font-weight: 800; color: rgba(255,255,255,0.5); margin-bottom: 8px; }
.attemptLine { grid-column: 1 / -1; }
.attemptLine { grid-column: 1 / -1; }
.attemptLine { color: rgba(255, 255, 255, 0.85); }
.histMeta { color: rgba(255,255,255,0.45); font-weight: 700; }
.histText { color: rgba(255,255,255,0.8); }
```

**5. SETTINGS tabs and section colours** (`pages/settings/SettingsPage.module.css`) -- colour tokens
```css
.container {
  --orange: #EE8C3A;
  --orange-dim: rgba(238, 140, 58, 0.18);
  --orange-border: rgba(238, 140, 58, 0.28);
  --cyan: #22d3ee;
  --violet: #34d399;
  --slate: #eab308;
  --navy: #1a2e30;
  --panel-bg: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  --panel-border: rgba(238, 140, 58, 0.2);
  --red: #ef4444;
  --green: #10b981;
  --gap-xl: clamp(12px, 1.6vw, 16px);
  --gap-lg: clamp(8px, 1.2vw, 12px);
  --gap-md: clamp(5px, 0.8vw, 8px);
  --pad: clamp(12px, 1.6vw, 18px);
  --radius: 12px;
  --radius-sm: 7px;
  --fs-h1: clamp(17px, 2.4vw, 23px);
  --fs-sub: clamp(8px, 0.85vw, 10px);
  --fs-drawer: clamp(9px, 0.9vw, 11px);
  --fs-label: clamp(7px, 0.75vw, 9px);
  --fs-btn: clamp(9px, 0.9vw, 11px);
  --fs-meta: clamp(8px, 0.85vw, 10px);
  --fs-value: clamp(11px, 1.1vw, 13px);
  --fs-op: clamp(11px, 1.2vw, 14px);
  --input-height: clamp(34px, 4vw, 38px);
  --input-px: clamp(10px, 1.3vw, 14px);
  --input-radius: 6px;
  --input-font: clamp(11px, 1.05vw, 13px);
  --label-font: clamp(8px, 0.85vw, 10px);
  --btn-height: clamp(36px, 4.6vw, 42px);
  --btn-px: clamp(14px, 1.8vw, 20px);
  --btn-font: clamp(9px, 0.9vw, 11px);
}
```

**5. SETTINGS tabs, card and light groups** (`pages/settings/SettingsPage.module.css`)
```css
.tabDock { flex: 0 0 auto; display: flex; align-items: center; background: #4d5c5a; border: none; border-radius: 8px; padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14); }
.tabRow { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.tab, .tabOn { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 12px; border-radius: 6px; outline: none; border: 1.5px solid transparent; background: transparent; color: rgba(255,255,255,0.92); transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease; }
.tab[data-accent="orange"]:hover { color: var(--orange); }
.tab[data-accent="cyan"]:hover { color: var(--cyan); }
.tab[data-accent="violet"]:hover { color: var(--violet); }
.tab[data-accent="red"]:hover { color: var(--red); }
.tab[data-accent="slate"]:hover { color: var(--slate); }
.tabOn { color: #1a2e30; }
.tabOn[data-accent="orange"] { background: var(--orange); border-color: var(--orange); box-shadow: 0 4px 16px rgba(238,140,58,0.32); }
.tabOn[data-accent="cyan"] { background: var(--cyan); border-color: var(--cyan); box-shadow: 0 4px 16px rgba(34,211,238,0.32); }
.tabOn[data-accent="violet"] { background: var(--violet); border-color: var(--violet); box-shadow: 0 4px 16px rgba(52,211,153,0.32); }
.tabOn[data-accent="red"] { background: var(--red); border-color: var(--red); color: #fff; box-shadow: 0 4px 16px rgba(239,68,68,0.32); }
.tabOn[data-accent="slate"] { background: var(--slate); border-color: var(--slate); box-shadow: 0 4px 16px rgba(234,179,8,0.32); }
.tabCount { font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.8vw, 9px); opacity: 0.75; }
.workstationCard { --accent: var(--orange); position: relative; background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%); border: 1.5px solid rgba(238, 140, 58, 0.2); border-radius: var(--radius); overflow: visible; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25); transition: border-color 0.3s ease, box-shadow 0.3s ease; }
.workstationCard:hover { border-color: var(--accent); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.32); }
.workstationCard[data-accent="cyan"] { --accent: var(--cyan); }
.workstationCard[data-accent="violet"] { --accent: var(--violet); }
.workstationCard[data-accent="red"] { --accent: var(--red); }
.workstationCard[data-accent="slate"] { --accent: var(--slate); }
.panelHeadRow { position: relative; z-index: 2; display: flex; flex-wrap: wrap; align-items: center; gap: 10px; background: #162a2c; border-bottom: 1.5px solid transparent; border-radius: 11px 11px 0 0; padding: clamp(8px,1.1vw,12px) clamp(10px,1.4vw,16px); width: 100%; box-sizing: border-box; text-align: left; cursor: pointer; transition: border-bottom-color 0.25s ease, border-radius 0.25s ease; }
.panelHeadRowOpen { border-bottom-color: var(--accent); }
.panelHeadTitle { display: flex; align-items: center; gap: clamp(6px,0.8vw,10px); font-family: 'Cinzel', serif; color: var(--accent); font-size: clamp(10px, 1.1vw, 13px); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; transition: color 0.18s ease; }
.panelHeadIcon { font-size: clamp(11px,1.15vw,14px); width: clamp(22px, 2.4vw, 27px); height: clamp(22px, 2.4vw, 27px); display: inline-flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 6px; flex-shrink: 0; }
.panelHeadRow:hover .panelHeadTitle { color: #fff; }
.prefGroupBox { background: #f2ede4; border: 1px solid rgba(26,46,48,0.14); border-radius: var(--radius-sm); padding: clamp(10px,1.3vw,14px) clamp(12px,1.5vw,16px); display: flex; flex-direction: column; }
.prefGroupBox .prefRow { border: 1px solid rgba(26,46,48,0.14); border-radius: 6px; background: rgba(26,46,48,0.05); margin: 0 0 clamp(7px,0.9vw,10px); padding: clamp(9px,1.2vw,12px); transition: background 0.18s ease, border-color 0.18s ease; }
.prefGroupBox .prefRow:hover { background: rgba(26,46,48,0.09); border-color: rgba(26,46,48,0.22); }
.prefGroupBox .prefBtn, .prefGroupBox .prefBtnActive { border: 1.5px solid rgba(26,46,48,0.2); background: rgba(255,255,255,0.65); color: rgba(26,46,48,0.85); }
.prefGroupBox .prefBtnActive { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
```

'''

SEC9 = r'''### 9.1 THE fix.py TEMPLATE -- COPY THIS EXACTLY
**David does NOT need to upload or clone fix.py any more.** The `fix.py` in the repo is only the LAST fix (every new fix overwrites it), so it is not a reference. This template IS the format. An LLM copies it, fills in the two EDIT parts, and copies every DO NOT EDIT part word for word. To write a fix the LLM needs only: this guide + the current text of the files being changed (David uploads just those files).

```python
#!/usr/bin/env python3
# PATH: fixNNN.py
# GOLDEN SEED -- fixNNN: <ONE-LINE SUMMARY IN PLAIN ENGLISH>.
#
#   1. <WHAT CHANGES -- plain English, one numbered item per change>
#   2. <...>
#
# NOT in this fix: <WHAT IS DELIBERATELY LEFT ALONE>.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
# Names, and one variable per file this fix touches.
FIX_NO = "fixNNN"
COMMIT_MSG = "fixNNN: <short plain-English summary of the whole fix>"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
EXAMPLE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
EXAMPLE_JAVA = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
# ============================= EDIT PART 1 END =============================

# ================== DO NOT EDIT: helpers (copy exactly) ====================
MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# sub = exact find/replace of the FIRST match. Prints OK / SKIP / MISSING.
def sub(text, old, new, desc):
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


# newfile = create (or replace) a whole file. SKIP if it already holds `marker`.
def newfile(path, text, label, marker):
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)


# ============================ EDIT PART 2 START ============================
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = ()   # example: (EXAMPLE_JSX, EXAMPLE_JAVA)
for _p in LOAD_FILES:
    load(_p)

# patch(EXAMPLE_JSX,
#       "exact old text copied from the real file (must appear once)",
#       "the new text",
#       "what this change does, in plain English")
#
# newfile(os.path.join(SRC, "utils", "example.js"),
#         "\n".join(["first line", "second line", ""]),
#         "new file utils/example.js", "text that is inside the new file")
# ============================= EDIT PART 2 END =============================

# ================= DO NOT EDIT: gates, rollback, git (copy exactly) ========
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since the last fix).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True

if not changed:
    print("note: nothing changed -- " + FIX_NO + " already applied")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed and RUN_GATES:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate ----
if changed and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif changed:
    print("note: RUN_GATES is False (docs-only fix) -- compile and build skipped")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

if not changed:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", COMMIT_MSG)
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip())
print("")
print("DONE: " + FIX_NO + " applied.")
```

### 9.2 fix.py FORMAT RULES (on top of the RULE lines above)
1. File name `fix.py` in the repo root, header line `# PATH: fixNNN.py`. NNN = the number in the latest commit message ("fix141: ..." means the next one is fix142). Each new fix overwrites the old fix.py.
2. Header comment = one-line summary, then a plain-English numbered list of what changes, then "NOT in this fix: ...".
3. Edit ONLY EDIT PART 1, EDIT PART 2 and the header comment. Everything marked DO NOT EDIT is copied word for word. This keeps every fix.py the same shape and short.
4. Every change is `patch(FILE, old, new, "plain-English description")`. `old` is text copied EXACTLY from the real file and must appear once. No regex, no line numbers. Whole new files use `newfile(...)` with a joined line list.
5. Safe to run twice: a patch whose new text is already there prints SKIP.
6. Atomic: if any patch is MISSING nothing is written or committed. The script never guesses.
7. Gates: the backend compile and `npm run build` run before the commit; red means every file is put back. Docs-only fixes (guide, markdown) set `RUN_GATES = False`.
8. `COMMIT_MSG` starts with `fixNNN:` and says in plain English what changed. The script commits and pushes itself.
9. If the LLM has not seen the CURRENT text of a file it must patch, it asks David for THAT file only. It never writes an `old` anchor from memory.
10. To change this guide, patch `GUIDE` inside a normal fix.py (same template). To change the template itself, patch 9.1 here.

'''

patch(GUIDE,
      "# Last updated: September 2026 (fix141: guide cleaned up to match the code)\n",
      "# Last updated: September 2026 (fix142: real design code and the fix.py template added)\n",
      "Guide: last-updated line")

patch(GUIDE,
      "**THE CODE IS THE TRUTH.** When you change or create any element, first find",
      "**THE CODE IS THE TRUTH.** (The actual code is copied in DESIGN REFERENCE CODE below.) When you change or create any element, first find",
      "Section 7: pointer to the design code")

patch(GUIDE,
      "### LAW: LEDGER PAGE IS THE REFERENCE DESIGN -- **This is the master rule everything else follows.**\n",
      DESIGN_CODE + "### LAW: LEDGER PAGE IS THE REFERENCE DESIGN -- **This is the master rule everything else follows.**\n",
      "Section 7: DESIGN REFERENCE CODE (real CSS of the five reference pages)")

patch(GUIDE,
      "### How David uses fix.py:\nSee Section 10 for the full step-by-step deploy flow.\n",
      "### How David uses fix.py:\nSee Section 10 for the full step-by-step deploy flow.\n\n" + SEC9,
      "Section 9: fix.py template (9.1) and format rules (9.2)")

patch(GUIDE,
      "**RULE: The LLM context guide is a SEPARATE file from fix.py. Output them separately.**",
      "**RULE: The LLM context guide is a SEPARATE file from fix.py. Output them separately.**\n"
      "*SUPERSEDED by Section 13 and 9.1: the guide is still its own file, but it is now changed by a patch inside fix.py, not by a separately delivered copy.*",
      "Section 9: separate-file rule marked superseded")
# ============================= EDIT PART 2 END =============================

# ================= DO NOT EDIT: gates, rollback, git (copy exactly) ========
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since the last fix).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True

if not changed:
    print("note: nothing changed -- " + FIX_NO + " already applied")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed and RUN_GATES:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate ----
if changed and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif changed:
    print("note: RUN_GATES is False (docs-only fix) -- compile and build skipped")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

if not changed:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", COMMIT_MSG)
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip())
print("")
print("DONE: " + FIX_NO + " applied.")