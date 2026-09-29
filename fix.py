#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix153: Audit list back on the light card (slightly darker), one hover colour, palette action colours.
#
# 1. Audit list returns to the light catalogue card, a little darker. Navy text and icons as before (no orange on the list).
# 2. Hover is ONE colour (navy tint) on every row.
# 3. Action colour uses the app palette only (red, green, cyan, amber, violet) and paints ONLY the left border
#    and the "FORENSIC DATA READOUT [SECURE]" label in the opened part.
# 4. Opened row: head and readout are the SAME dark (#1a2e30). The readout text is orange.
# 5. Kept from fix152: dropdowns always orange, popup X, date picker, Expenses changes.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix153"
COMMIT_MSG = "fix153: audit list back on light card (darker), one hover colour, palette action colours on border + readout label only, one dark for open row"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")
TESTJAVA = os.path.join(BACKEND, "src", "test", "java", "com", "gesolutions", "erp")
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")

AUDIT_JSX = os.path.join(SRC, "pages", "Audit", "AuditPage.jsx")
AUDIT_CSS = os.path.join(SRC, "pages", "Audit", "AuditPage.module.css")
AUDIT_CAT = os.path.join(SRC, "pages", "Audit", "auditCatalog.js")
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

# ---- file bodies (edit here if you want to tweak) ----
AUDIT_CSS_TEXT = r'''/* PATH: erp-frontend/src/pages/Audit/AuditPage.module.css */
/* fix153: list back on the light catalogue card (slightly darker). fix152: whole file rewritten. The old file was 570 lines of stacked overrides (pill styles overridden by
   "final polish" overridden by fix151). Every rule below is the ONLY rule for its class.
   Look: dark list, orange accents on the small parts, one colour per action (--rail, set by the page). */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --gap-md:        clamp(5px, 0.8vw, 8px);
    --radius:        12px;
    --radius-sm:     6px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-label:  clamp(7px, 0.75vw, 9px);
    --fs-meta:   clamp(8px, 0.85vw, 10px);
    --fs-time:   clamp(11px, 1.1vw, 13px);
    --fs-action: clamp(10px, 1.05vw, 12.5px);
    --fs-target: clamp(10px, 1.05vw, 12px);
    --fs-btn:    clamp(8px, 0.85vw, 10px);
    --fs-input:  clamp(11px, 1.1vw, 13px);

    max-width: 1450px;
    width: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: terminalBoot 0.7s cubic-bezier(0.2, 1, 0.3, 1) both;
}
@keyframes terminalBoot {
    from { opacity: 0; filter: brightness(0.5); transform: translateY(14px); }
    to   { opacity: 1; filter: brightness(1);   transform: translateY(0); }
}

/* ---- PAGE HEADER (same glass bar as Dashboard) ---- */
.pageHeader {
    display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap;
    gap: clamp(6px, 1vw, 12px);
    margin-bottom: var(--block-gap);
    padding: var(--hdr-pad);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
.title { margin: 0; font-family: 'Cinzel', serif; font-size: var(--fs-h1); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--navy); }
.subtitle { margin: 0; font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px); font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: #64748b; }

.diagHUD { display: flex; gap: var(--gap-md); flex-shrink: 0; align-self: flex-end; }
.diagItem {
    display: flex; align-items: center; gap: clamp(4px, 0.5vw, 7px); white-space: nowrap;
    padding: clamp(3px, 0.4vw, 6px) clamp(6px, 0.9vw, 12px);
    background: var(--navy); color: #fff;
    border: 1px solid var(--orange-border); border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif; font-size: var(--stat-label); font-weight: 900;
    letter-spacing: 0.5px; text-transform: uppercase;
}
.diagItem svg { color: var(--orange); font-size: 10px; }
.diagItem strong { font-family: 'Space Mono', monospace; font-size: var(--stat-value-sm); }

/* ---- CONTROL HUB ---- */
.controlHub {
    position: sticky; top: 0; z-index: 200;
    display: flex; flex-direction: column; gap: var(--gap-md);
    width: 100%; flex-shrink: 0;
    margin: 0 clamp(-8px, -1.6vw, -16px) var(--block-gap);
    padding: clamp(8px, 1vw, 12px) clamp(8px, 1.6vw, 16px);
    background: transparent;
}

.searchPill {
    position: relative; display: flex; align-items: center;
    width: 100%; max-width: clamp(320px, 50vw, 600px); height: clamp(36px, 4.5vw, 44px);
    background: #fff; border: 1.5px solid #c8d6d7; border-radius: var(--radius-sm);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.searchPill:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.18); }
.searchIcon { position: absolute; left: clamp(10px, 1.2vw, 14px); top: 50%; transform: translateY(-50%); display: flex; align-items: center; color: var(--orange); font-size: clamp(14px, 1.5vw, 18px); pointer-events: none; }
.searchInput {
    width: 100%; border: none; outline: none; background: transparent;
    padding-left: 42px !important; padding-right: clamp(34px, 4.5vw, 42px) !important;
    font-family: 'DM Sans', sans-serif; font-size: var(--fs-input); font-weight: 800; color: var(--navy);
    -webkit-appearance: none; appearance: none; transition: padding 0.2s ease;
}
.searchInputActive { padding-left: clamp(14px, 1.5vw, 18px) !important; }
.searchInput::placeholder { font-weight: 500; color: rgba(26, 46, 48, 0.3); }
.searchClear { position: absolute; right: clamp(8px, 1vw, 12px); display: flex; align-items: center; padding: clamp(3px, 0.4vw, 5px); background: transparent; border: none; border-radius: 4px; cursor: pointer; color: rgba(26, 46, 48, 0.4); font-size: clamp(13px, 1.4vw, 16px); transition: color 0.15s, background 0.15s; }
.searchClear:hover { color: var(--navy); background: rgba(26, 46, 48, 0.08); }
.searchClear:focus-visible { outline: 2px solid var(--orange); }

.filterGrid { display: flex; flex-wrap: wrap; align-items: flex-start; gap: clamp(6px, 1vw, 10px); width: 100%; padding: 4px 0; position: relative; overflow: visible; }

/* ---- FILTER DROPDOWNS: ALWAYS in the active (orange) state, All Staff / All Actions included ---- */
.hwSelectWrap { position: relative; isolation: isolate; overflow: visible; flex: 1 1 140px; min-width: 130px; max-width: 260px; }
.hwSelectWrap:focus-within,
.hwSelectWrap:has([class*="openWrapper"]) { isolation: auto; z-index: 10000; }
.hwSelectWrap > * { margin-bottom: 0 !important; }
.hwSelectWrap > div { overflow: visible !important; }
.hwSelectWrap label { display: none !important; }

.hwSelectWrap [class*="selectBox"] {
    position: relative !important; z-index: 9000 !important; overflow: visible !important;
    height: clamp(34px, 4vw, 40px) !important;
    padding: 0 clamp(10px, 1.3vw, 16px) !important;
    background: #EE8C3A !important;
    border: 1.5px solid #EE8C3A !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 0 12px rgba(238, 140, 58, 0.35) !important;
    color: #1a2e30 !important;
}
.hwSelectWrap [class*="selectBox"]:hover { background: #f0a050 !important; border-color: #f0a050 !important; box-shadow: 0 0 18px rgba(238, 140, 58, 0.5) !important; }
.hwSelectWrap [class*="currentValue"] {
    color: #1a2e30 !important; font-size: clamp(9px, 0.9vw, 11px) !important; font-weight: 900 !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
}
.hwSelectWrap [class*="icon"] { color: #1a2e30 !important; }
.hwSelectWrap [class*="dropdown"] { position: absolute !important; z-index: 99999 !important; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.7) !important; }

/* ---- BUTTONS + DATE FIELDS ---- */
.resetBtn {
    flex: 0 0 auto; display: inline-flex; align-items: center; justify-content: center; gap: clamp(4px, 0.6vw, 6px);
    height: clamp(34px, 4vw, 40px); padding: 0 clamp(10px, 1.3vw, 16px);
    background: rgba(26, 46, 48, 0.75); color: rgba(255, 255, 255, 0.85);
    border: 1.5px solid rgba(255, 255, 255, 0.18); border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px); font-weight: 900;
    letter-spacing: 1.5px; text-transform: uppercase; white-space: nowrap; cursor: pointer;
    transition: all 0.2s ease;
}
.resetBtn:hover:not(:disabled) { background: rgba(238, 140, 58, 0.12); border-color: var(--orange); color: var(--orange); }
.resetBtn:disabled { opacity: 0.4; cursor: not-allowed; }
.resetBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

.dateField {
    display: flex; align-items: center; gap: 7px;
    height: clamp(36px, 4.4vw, 44px); padding: 0 10px;
    background: #fff; border: 1.5px solid #c8d6d7; border-radius: var(--radius-sm);
}
.dateField span { font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: #5b6f70; }
.dateField input { min-width: 108px; border: none; outline: none; background: transparent; font-family: 'Inter', sans-serif; font-size: clamp(10px, 1vw, 12px); font-weight: 700; color: var(--navy); }
.dateField:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.16); }

/* ---- THE LIST (fix153): the light catalogue card, a little darker; ONE hover colour; ONE dark for the open row ---- */
.timelineFrame { overflow: hidden; background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); box-shadow: 0 10px 36px rgba(0, 0, 0, 0.25); }
.timelineStream { display: flex; flex-direction: column; }

.logTray { background: #d8cfbd; padding: 10px; }
.logCard { overflow: hidden; background: #ebe5d8; border-radius: 10px; box-shadow: 0 2px 8px rgba(26, 46, 48, 0.2); }

/* --rail is the action's colour (set by the page). It paints ONLY the left border and, when open, the readout label. */
.logRow {
    --rail: #06b6d4;
    border-left: clamp(3px, 0.4vw, 5px) solid var(--rail);
    border-bottom: 1.5px solid rgba(26, 46, 48, 0.22);
    background: transparent;
    cursor: pointer; outline: none;
    transition: background 0.18s ease;
}
.logRow:last-child { border-bottom: none; }
.logRow:hover { background: rgba(26, 46, 48, 0.09); }
.logRow:focus-visible { outline: 2px solid #1a2e30; outline-offset: -2px; }

.logMain {
    display: grid; align-items: start;
    grid-template-columns: clamp(90px, 9vw, 115px) clamp(170px, 20vw, 230px) 1fr clamp(24px, 2.8vw, 32px);
    gap: clamp(12px, 1.6vw, 22px);
    padding: clamp(9px, 1.1vw, 12px) clamp(12px, 1.5vw, 18px);
}

.timeMark { display: flex; flex-direction: column; padding-top: 1px; }
.clockPair { display: flex; align-items: center; gap: clamp(5px, 0.6vw, 7px); font-family: 'Space Mono', monospace; font-size: var(--fs-time); font-weight: 900; color: #1a2e30; }
.clockPair svg { flex-shrink: 0; color: #5b6f70; }
.timeMark small { margin: clamp(2px, 0.3vw, 4px) 0 0 clamp(16px, 2vw, 22px); font-family: 'DM Sans', sans-serif; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; color: #1a2e30; opacity: 0.62; }

.actionMark { display: flex; align-items: flex-start; gap: clamp(10px, 1.3vw, 16px); }
.iconChassis { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: clamp(28px, 3.2vw, 36px); height: clamp(28px, 3.2vw, 36px); background: rgba(26, 46, 48, 0.07); border: 1px solid rgba(26, 46, 48, 0.18); border-radius: var(--radius-sm); color: #5b6f70; font-size: clamp(13px, 1.4vw, 16px); }
.actionMeta { display: flex; flex-direction: column; gap: clamp(2px, 0.3vw, 3px); min-width: 0; }
.actionMeta strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: 'DM Sans', sans-serif; font-size: var(--fs-action); font-weight: 900; letter-spacing: 0.5px; text-transform: uppercase; color: #1a2e30; }
.actionMeta span { font-family: 'Space Mono', monospace; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; color: rgba(26, 46, 48, 0.6); }

.targetMark { min-width: 0; }
.targetMark p { margin: 0; overflow-wrap: break-word; word-break: break-word; font-size: var(--fs-target); font-weight: 800; line-height: 1.45; color: rgba(26, 46, 48, 0.82); }

.inspectIcon { justify-self: end; align-self: start; margin-top: 1px; color: rgba(26, 46, 48, 0.45); font-size: clamp(14px, 1.6vw, 18px); transition: transform 0.2s ease, color 0.15s ease; }
.logRow:hover .inspectIcon { color: #1a2e30; }

/* OPEN ROW: head and readout are the SAME dark (#1a2e30), no wash, no seam */
.logRow.expanded, .logRow.expanded:hover { background: #1a2e30; }
.logRow.expanded .clockPair { color: #fff; }
.logRow.expanded .clockPair svg { color: #f2ede4; }
.logRow.expanded .timeMark small { color: #fff; opacity: 0.65; }
.logRow.expanded .iconChassis { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); color: #f2ede4; }
.logRow.expanded .actionMeta strong { color: #fff; }
.logRow.expanded .actionMeta span { color: rgba(255, 255, 255, 0.6); }
.logRow.expanded .targetMark p { color: #fff; }
.logRow.expanded .inspectIcon { color: #f2ede4; transform: rotate(180deg); }

.traceDetails { overflow: hidden; background: #1a2e30; transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.traceClosed { max-height: 0; }
.traceOpen { max-height: clamp(200px, 30vw, 400px); overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.3) transparent; }
.rawBox { margin: 0; padding: clamp(4px, 0.6vw, 8px) clamp(12px, 1.5vw, 18px) clamp(12px, 1.5vw, 16px); }
/* the label takes the action colour; the readout text itself is app orange */
.rawHeader { display: flex; align-items: center; gap: clamp(7px, 0.9vw, 10px); margin-bottom: clamp(8px, 1.1vw, 12px); font-size: var(--fs-label); font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: var(--rail); }
.rawOutput { margin: 0; white-space: pre-wrap; word-break: break-all; font-family: 'Space Mono', monospace; font-size: clamp(10px, 1.05vw, 12px); line-height: 1.6; color: #EE8C3A; }

/* ---- PAGINATION ---- */
.pagination { display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; padding: clamp(8px, 1vw, 11px) clamp(12px, 1.5vw, 18px); background: rgba(0, 0, 0, 0.25); border-top: 1px solid rgba(255, 255, 255, 0.08); }
.pgBtn { display: flex; align-items: center; gap: clamp(5px, 0.6vw, 8px); padding: clamp(6px, 0.8vw, 9px) clamp(11px, 1.4vw, 16px); background: transparent; border: 1.5px solid rgba(255, 255, 255, 0.14); border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif; font-size: var(--fs-btn); font-weight: 900; letter-spacing: 1px; text-transform: uppercase; white-space: nowrap; color: rgba(255, 255, 255, 0.8); cursor: pointer; transition: border-color 0.2s, color 0.2s, background 0.2s; }
.pgBtn:hover:not(:disabled) { border-color: var(--orange); color: var(--orange); background: rgba(238, 140, 58, 0.08); }
.pgBtn:disabled { opacity: 0.25; cursor: not-allowed; }
.pgBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.pageLabel { font-family: 'Space Mono', monospace; font-size: var(--fs-label); font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: rgba(255, 255, 255, 0.45); }

.emptySignal { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; margin: 8px; padding: clamp(28px, 5vw, 50px) 20px; background: rgba(255, 255, 255, 0.02); border: 1px dashed rgba(255, 255, 255, 0.12); border-radius: 8px; font-family: 'Space Mono', monospace; font-size: var(--fs-meta); font-weight: 900; letter-spacing: 2px; text-transform: uppercase; text-align: center; color: rgba(244, 242, 239, 0.72); }

/* ---- RESPONSIVE ---- */
@media (max-width: 1000px) {
    .logMain { grid-template-columns: clamp(90px, 10vw, 120px) clamp(150px, 20vw, 200px) 1fr; }
    .inspectIcon { display: none; }
}
@media (max-width: 768px) {
    .pageHeader { border-radius: 0; }
    .controlHub { margin-left: 0; margin-right: 0; padding-left: clamp(8px, 2vw, 12px); padding-right: clamp(8px, 2vw, 12px); }
    .timelineFrame { border-radius: 0; }
    .filterGrid { gap: 6px; padding-bottom: 6px; }
    .hwSelectWrap { flex: 1 1 120px; min-width: 110px; max-width: 100%; }
    .resetBtn { padding: 0 10px; }
    .logMain { grid-template-columns: 1fr 1fr; gap: var(--gap-md); }
    .timeMark { grid-column: 1; }
    .actionMark { grid-column: 2; justify-self: end; text-align: right; }
    .targetMark { grid-column: 1 / span 2; margin-top: var(--gap-md); }
    .iconChassis { display: none; }
    .actionMeta { align-items: flex-end; }
}
@media (max-width: 640px) {
    .container { padding: 0 0 clamp(24px, 3vw, 36px); }
}
@media (max-width: 480px) {
    .container { --fs-h1: 15px; --fs-time: 10px; --fs-action: 9px; --fs-target: 9px; --fs-btn: 8px; }
    .filterGrid { gap: 5px; }
    .hwSelectWrap { flex: 1 1 110px; min-width: 100px; }
    .resetBtn { height: 32px; padding: 0 10px; font-size: 8px; }
    .diagItem { height: 24px; padding: 4px 8px; gap: 4px; font-size: 7px; border-radius: 4px; }
    .diagItem svg { font-size: 8px; }
    .searchPill { max-width: 100%; height: 36px; }
    .searchInput { font-size: 12px; }
    .logMain { padding: 8px 11px; gap: 8px; }
    .pagination { padding: 7px 11px; }
    .pgBtn { padding: 5px 10px; font-size: 8px; }
    .rawBox { padding: 8px 11px; }
    .rawOutput { font-size: 10px; }
    .emptySignal { padding: 22px 0; font-size: 9px; }
}
'''

CAT_OLD = "/* fix152: one colour per action. The catalogue order gives every known action its own hue (golden-angle\n   spacing so neighbours never look alike); an unlisted code gets a stable colour from its own name. */\nconst RAIL = {};\nObject.keys(INDEX).forEach((code, i) => {\n    RAIL[code] = 'hsl(' + Math.round((i * 137.508 + 18) % 360) + ', 72%, 64%)';\n});\nexport const actionColor = (code) => {\n    const key = String(code || '');\n    if (RAIL[key]) return RAIL[key];\n    let h = 0;\n    for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) % 360;\n    return 'hsl(' + h + ', 72%, 64%)';\n};\n\n"

CAT_NEW = "/* fix153: one colour per action, taken from the app palette only (red, green, cyan, amber, violet; orange is\n   kept out because the opened readout text is orange). Colours are dealt out in catalogue order so neighbours\n   differ; an unlisted code gets a stable colour from its own name. */\nconst PALETTE = ['#ef4444', '#10b981', '#06b6d4', '#f59e0b', '#a78bfa'];\nconst RAIL = {};\nObject.keys(INDEX).forEach((code, i) => { RAIL[code] = PALETTE[i % PALETTE.length]; });\nexport const actionColor = (code) => {\n    const key = String(code || '');\n    if (RAIL[key]) return RAIL[key];\n    let h = 0;\n    for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) % PALETTE.length;\n    return PALETTE[h];\n};\n\n"

GUIDE_OLD = '- Audit list is DARK (panel gradient, zebra rows). Small parts use the app orange: clock icons, icon frames, chevrons, and the Cinzel action titles. The cream tray / white card of fix151 is gone.\n- Every action has its OWN left-rail colour: `actionColor(code)` in `auditCatalog.js` (golden-angle hues by catalogue order, hash for unlisted codes). The page sets it as `--rail` on the row; the rail, the hover / selected wash and the opened readout text (`.rawHeader`, `.rawOutput`) all read `var(--rail)`. Do not re-add severity buckets.\n- OPERATOR and PROTOCOL dropdowns on Audit are ALWAYS in the active orange state (All Staff / All Actions included). It is pure CSS on `.hwSelectWrap`.\n- `AuditPage.module.css` was rewritten in fix152: one rule per class, no stacked overrides. Keep it that way.\n'

GUIDE_NEW = '- Audit list is the LIGHT catalogue card again (`.logTray` #d8cfbd, `.logCard` #ebe5d8, navy text). Hover is ONE navy tint for every row.\n- OPEN row: head AND readout are the same dark `#1a2e30` (no wash, no seam). Readout text is app orange; the `FORENSIC DATA READOUT` label takes the action colour.\n- Action colour (`actionColor(code)` in `auditCatalog.js`, palette red / green / cyan / amber / violet, dealt out in catalogue order) is set as `--rail` on the row and paints ONLY the left border and the readout label. Nothing else is tinted. Orange is kept out of the palette.\n- OPERATOR and PROTOCOL dropdowns on Audit are ALWAYS in the active orange state (All Staff / All Actions included). Pure CSS on `.hwSelectWrap`.\n'

# ============================ EDIT PART 2 START ============================
LOAD_FILES = (AUDIT_JSX, AUDIT_CAT, GUIDE)
for _p in LOAD_FILES:
    load(_p)

def L(*lines):
    return "\n".join(lines)

# ---- 1. Audit stylesheet (whole file) ----
newfile(AUDIT_CSS, AUDIT_CSS_TEXT, "AuditPage.module.css (light list, one hover, one dark for open row)", "fix153: list back")

# ---- 2. JSX: the light tray + card wrapper comes back ----
patch(AUDIT_JSX,
      "                    {!loading && visibleLogs.map(log => (",
      L("                    {!loading && visibleLogs.length > 0 && (<div className={styles.logTray}><div className={styles.logCard}>",
        "                    {visibleLogs.map(log => ("),
      "Audit JSX: tray + card wrapper (open)")
patch(AUDIT_JSX,
      L("                    ))}",
        "                </div>",
        "",
        "                <footer className={styles.pagination}"),
      L("                    ))}",
        "                    </div></div>)}",
        "                </div>",
        "",
        "                <footer className={styles.pagination}"),
      "Audit JSX: tray + card wrapper (close)")

# ---- 3. Palette colours ----
patch(AUDIT_CAT, CAT_OLD, CAT_NEW, "Catalogue: actionColor() uses the app palette")

# ---- 4. guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix152: Audit dark redesign + per-action colours, popup X, HardwareDatePicker, Expenses cream cards, Section 7)",
      "# Last updated: September 2026 (fix153: Audit light list darker, palette action colours, HardwareDatePicker, Expenses cream cards, Section 7)",
      "Guide: header line")
patch(GUIDE, GUIDE_OLD, GUIDE_NEW, "Guide: audit notes match fix153")

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


def working_tree_dirty():
    r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return bool((r.stdout or "").strip())


# active = this script wrote something, OR files were already changed by hand (commit-only mode)
active = changed or working_tree_dirty()
if not changed and active:
    print("note: commit-only mode -- no patches defined, committing the changes already in the working tree")
if not active:
    print("note: nothing changed and the working tree is clean -- nothing to do")


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
    print("Every file this script touched was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if active and RUN_GATES:
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
if active and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif active and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif active:
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

if not active:
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