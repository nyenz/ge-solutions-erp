#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix152: Audit dark redesign + popup X + app-wide date picker + Expenses cream cards darker.
#
# 1. UnsavedChangesModal: the X is back in the header (same closeBtn as the Recovery CALL LOG popup). X = KEEP EDITING.
# 2. Audit list is DARK again: zebra rows, orange chevrons / clock icons / icon frames, Cinzel orange action titles.
#    Every action gets its OWN left-rail colour (auditCatalog.actionColor). The opened readout text
#    (e.g. "Operator session established") takes that same colour.
# 3. ALL STAFF and ALL ACTIONS are always in the active orange state, like a chosen filter.
# 4. AuditPage.module.css rewritten from scratch (the old file was stacked overrides); unused tray/card wrappers,
#    unused classes and the unused FiShield import are gone.
# 5. NEW HardwareDatePicker (dark card, Cinzel month, orange selected day). Used by Audit, Report Studio and
#    Intake, so every date field in the app matches. The browser's own calendar cannot be themed.
# 6. Expenses: cream sections a little darker, zebra rows, stronger row separators. The cream boundary is now a
#    solid 2px frame on BOTH the Log-an-expense box and the Recent-entries table.
#
# NOT in this fix: the one datetime-local field (Folder page negotiation deadline) stays native -- it needs
# date + time and cannot be themed.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix152"
COMMIT_MSG = "fix152: audit dark redesign + per-action colours, popup X, app-wide date picker, expenses cream cards darker"
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
UCM_JSX = os.path.join(SRC, "components", "common", "UnsavedChangesModal.jsx")
DP_JSX = os.path.join(SRC, "components", "common", "HardwareDatePicker.jsx")
DP_CSS = os.path.join(SRC, "components", "common", "HardwareDatePicker.module.css")
REPORT_JSX = os.path.join(SRC, "pages", "Reports", "ReportStudio.jsx")
INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
EXP_CSS = os.path.join(SRC, "pages", "Financials", "ExpensesPage.module.css")
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
DP_JSX_TEXT = r'''// PATH: erp-frontend/src/components/common/HardwareDatePicker.jsx
import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
    FiCalendar, FiChevronLeft, FiChevronRight, FiChevronsLeft, FiChevronsRight
} from 'react-icons/fi';
import styles from './HardwareDatePicker.module.css';

/**
 * GOLDEN SEED -- DATE PICKER (fix152)
 *
 * The browser's own calendar cannot be themed (it is drawn by the OS), so every date field in the
 * app uses this one instead. It looks like the popup standard: dark gradient card, orange border,
 * Cinzel month title, orange selected day.
 *
 * Contract is the same as <input type="date">:
 *   value     -- 'yyyy-mm-dd' or ''
 *   onChange  -- called with the NEW VALUE STRING (not an event)
 * Extra props:
 *   className -- put on the visible field, so each page keeps its own field styling
 *   block     -- true = field fills its parent's width (forms); false = shrink to fit (filter rows)
 *   ariaLabel -- accessible name
 */
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DOW = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
const POP_W = 288;
const POP_H = 352;

const pad = (n) => String(n).padStart(2, '0');
const toValue = (y, m, d) => y + '-' + pad(m + 1) + '-' + pad(d);
const parse = (v) => {
    const hit = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || '');
    return hit ? { y: +hit[1], m: +hit[2] - 1, d: +hit[3] } : null;
};
const show = (v) => {
    const p = parse(v);
    return p ? pad(p.d) + '/' + pad(p.m + 1) + '/' + p.y : '';
};
const todayParts = () => {
    const t = new Date();
    return { y: t.getFullYear(), m: t.getMonth(), d: t.getDate() };
};

const HardwareDatePicker = ({ value = '', onChange, className = '', block = false, ariaLabel = 'Date', placeholder = 'dd/mm/yyyy' }) => {
    const [open, setOpen] = useState(false);
    const [view, setView] = useState(() => {
        const p = parse(value) || todayParts();
        return { y: p.y, m: p.m };
    });
    const [pos, setPos] = useState({ top: 0, left: 0 });
    const wrapRef = useRef(null);
    const inputRef = useRef(null);
    const popRef = useRef(null);

    // open the card under the field (or above it when there is no room below)
    const openPicker = () => {
        const p = parse(value) || todayParts();
        setView({ y: p.y, m: p.m });
        if (inputRef.current) {
            const r = inputRef.current.getBoundingClientRect();
            const left = Math.max(8, Math.min(r.left, window.innerWidth - POP_W - 8));
            let top = r.bottom + 6;
            if (top + POP_H > window.innerHeight - 8 && r.top - POP_H - 6 > 8) top = r.top - POP_H - 6;
            setPos({ top, left });
        }
        setOpen(true);
    };

    useEffect(() => {
        if (!open) return;
        const onDown = (e) => {
            if (wrapRef.current && wrapRef.current.contains(e.target)) return;
            if (popRef.current && popRef.current.contains(e.target)) return;
            setOpen(false);
        };
        const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
        const onMove = (e) => {
            if (popRef.current && popRef.current.contains(e.target)) return;
            setOpen(false);
        };
        document.addEventListener('mousedown', onDown);
        document.addEventListener('keydown', onKey);
        window.addEventListener('resize', onMove);
        window.addEventListener('scroll', onMove, true);
        return () => {
            document.removeEventListener('mousedown', onDown);
            document.removeEventListener('keydown', onKey);
            window.removeEventListener('resize', onMove);
            window.removeEventListener('scroll', onMove, true);
        };
    }, [open]);

    const pick = (v) => { onChange(v); setOpen(false); };
    const shiftMonth = (n) => setView((v) => {
        const d = new Date(v.y, v.m + n, 1);
        return { y: d.getFullYear(), m: d.getMonth() };
    });
    const shiftYear = (n) => setView((v) => ({ y: v.y + n, m: v.m }));

    const sel = parse(value);
    const now = todayParts();
    const lead = (new Date(view.y, view.m, 1).getDay() + 6) % 7; // week starts on Monday
    const cells = [];
    for (let i = 0; i < 42; i++) {
        const dt = new Date(view.y, view.m, 1 - lead + i);
        cells.push({ y: dt.getFullYear(), m: dt.getMonth(), d: dt.getDate(), out: dt.getMonth() !== view.m });
    }

    return (
        <div className={`${styles.wrap} ${block ? styles.wrapBlock : ''}`} ref={wrapRef}>
            <input
                ref={inputRef}
                type="text"
                readOnly
                size={10}
                className={`${styles.field} ${className}`}
                value={show(value)}
                placeholder={placeholder}
                aria-label={ariaLabel}
                aria-haspopup="dialog"
                aria-expanded={open}
                onClick={() => (open ? setOpen(false) : openPicker())}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') { e.preventDefault(); if (!open) openPicker(); }
                }}
            />
            <FiCalendar className={styles.fieldIcon} aria-hidden="true" />

            {open && createPortal(
                <div ref={popRef} className={styles.pop} style={{ top: pos.top, left: pos.left, width: POP_W }} role="dialog" aria-label="Choose a date">
                    <div className={styles.nav}>
                        <button type="button" className={styles.navBtn} onClick={() => shiftYear(-1)} aria-label="Previous year"><FiChevronsLeft /></button>
                        <button type="button" className={styles.navBtn} onClick={() => shiftMonth(-1)} aria-label="Previous month"><FiChevronLeft /></button>
                        <span className={styles.navTitle}>{MONTHS[view.m]} {view.y}</span>
                        <button type="button" className={styles.navBtn} onClick={() => shiftMonth(1)} aria-label="Next month"><FiChevronRight /></button>
                        <button type="button" className={styles.navBtn} onClick={() => shiftYear(1)} aria-label="Next year"><FiChevronsRight /></button>
                    </div>

                    <div className={styles.dowRow}>
                        {DOW.map((d) => <span key={d}>{d}</span>)}
                    </div>

                    <div className={styles.grid}>
                        {cells.map((c) => {
                            const isSel = !!sel && sel.y === c.y && sel.m === c.m && sel.d === c.d;
                            const isNow = now.y === c.y && now.m === c.m && now.d === c.d;
                            return (
                                <button
                                    type="button"
                                    key={c.y + '-' + c.m + '-' + c.d}
                                    className={`${styles.day} ${c.out ? styles.dayOut : ''} ${isNow ? styles.dayNow : ''} ${isSel ? styles.daySel : ''}`}
                                    onClick={() => pick(toValue(c.y, c.m, c.d))}
                                    aria-label={c.d + ' ' + MONTHS[c.m] + ' ' + c.y}
                                    aria-pressed={isSel}
                                >
                                    {c.d}
                                </button>
                            );
                        })}
                    </div>

                    <div className={styles.foot}>
                        <button type="button" className={styles.footBtn} onClick={() => pick('')}>Clear</button>
                        <button type="button" className={`${styles.footBtn} ${styles.footBtnHot}`} onClick={() => pick(toValue(now.y, now.m, now.d))}>Today</button>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
};

export default HardwareDatePicker;
'''

DP_CSS_TEXT = r'''/* PATH: erp-frontend/src/components/common/HardwareDatePicker.module.css */
/* fix152: the app's one date picker. Card = the HardwareModal popup standard (dark gradient, orange border,
   Cinzel title). Selected day = solid orange, today = orange ring, hover = orange wash. */

.wrap { position: relative; display: inline-flex; align-items: center; min-width: 0; }
.wrapBlock { display: flex; width: 100%; }

/* the visible field: each page styles it through the className it passes in */
.field { cursor: pointer; text-overflow: ellipsis; padding-right: 30px !important; box-sizing: border-box; }
.wrapBlock .field { width: 100%; }
.fieldIcon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #EE8C3A; font-size: 14px; pointer-events: none; }

.pop {
    position: fixed;
    z-index: 100000;
    box-sizing: border-box;
    padding: 14px;
    background: linear-gradient(160deg, #1c3335 0%, #213e40 100%);
    border: 2px solid rgba(238, 140, 58, 0.4);
    border-radius: 12px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    font-family: 'DM Sans', sans-serif;
    animation: popIn 0.18s cubic-bezier(0.2, 1, 0.3, 1);
}
@keyframes popIn {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
}

.nav {
    display: flex; align-items: center; gap: 4px;
    padding-bottom: 10px; margin-bottom: 8px;
    border-bottom: 1px solid rgba(238, 140, 58, 0.25);
}
.navTitle {
    flex: 1; text-align: center;
    font-family: 'Cinzel', serif; font-weight: 700; font-size: 12px;
    letter-spacing: 1.5px; text-transform: uppercase; color: #EE8C3A;
}
.navBtn {
    width: 26px; height: 26px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px; color: rgba(255, 255, 255, 0.7); font-size: 14px; cursor: pointer;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.navBtn:hover { background: rgba(238, 140, 58, 0.16); border-color: #EE8C3A; color: #EE8C3A; }
.navBtn:focus-visible, .day:focus-visible, .footBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 1px; }

.dowRow, .grid { display: grid; grid-template-columns: repeat(7, 1fr); }
.dowRow { margin-bottom: 4px; }
.dowRow span {
    text-align: center; padding: 4px 0;
    font-size: 9px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
    color: rgba(255, 255, 255, 0.5);
}

.grid { gap: 2px; }
.day {
    height: 32px; display: flex; align-items: center; justify-content: center;
    background: transparent; border: 1.5px solid transparent; border-radius: 6px;
    font-family: 'Space Mono', monospace; font-size: 12px; font-weight: 700;
    color: #fff; cursor: pointer;
    transition: background 0.12s, border-color 0.12s, color 0.12s;
}
.day:hover { background: rgba(238, 140, 58, 0.18); border-color: rgba(238, 140, 58, 0.5); }
.dayOut { color: rgba(255, 255, 255, 0.28); }
.dayNow { border-color: #EE8C3A; color: #EE8C3A; }
.daySel, .daySel:hover { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; font-weight: 900; box-shadow: 0 0 12px rgba(238, 140, 58, 0.4); }

.foot {
    display: flex; justify-content: space-between; align-items: center;
    margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.footBtn {
    background: transparent; border: none; cursor: pointer; padding: 6px 8px; border-radius: 6px;
    font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 900;
    letter-spacing: 1.5px; text-transform: uppercase; color: rgba(255, 255, 255, 0.6);
    transition: background 0.15s, color 0.15s;
}
.footBtn:hover { background: rgba(255, 255, 255, 0.08); color: #fff; }
.footBtnHot { color: #EE8C3A; }
.footBtnHot:hover { background: rgba(238, 140, 58, 0.16); color: #f0a050; }
'''

AUDIT_CSS_TEXT = r'''/* PATH: erp-frontend/src/pages/Audit/AuditPage.module.css */
/* fix152: whole file rewritten. The old file was 570 lines of stacked overrides (pill styles overridden by
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

/* ---- THE LIST: dark, zebra rows, one coloured rail per action ---- */
.timelineFrame { overflow: hidden; background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); box-shadow: 0 10px 36px rgba(0, 0, 0, 0.25); }
.timelineStream { display: flex; flex-direction: column; }

.logRow {
    --rail: #06b6d4;
    border-left: clamp(3px, 0.4vw, 5px) solid var(--rail);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: transparent;
    cursor: pointer; outline: none;
    transition: background 0.18s ease;
}
.logRow:last-child { border-bottom: none; }
.logRow:nth-child(even) { background: rgba(0, 0, 0, 0.18); }
.logRow:hover { background: rgba(255, 255, 255, 0.05); background: color-mix(in srgb, var(--rail) 10%, transparent); }
.logRow:focus-visible { outline: 2px solid var(--rail); outline-offset: -2px; }

.logMain {
    display: grid; align-items: start;
    grid-template-columns: clamp(90px, 9vw, 115px) clamp(170px, 20vw, 230px) 1fr clamp(24px, 2.8vw, 32px);
    gap: clamp(12px, 1.6vw, 22px);
    padding: clamp(9px, 1.1vw, 12px) clamp(12px, 1.5vw, 18px);
}

.timeMark { display: flex; flex-direction: column; padding-top: 1px; }
.clockPair { display: flex; align-items: center; gap: clamp(5px, 0.6vw, 7px); font-family: 'Space Mono', monospace; font-size: var(--fs-time); font-weight: 900; color: #fff; }
.clockPair svg { flex-shrink: 0; color: var(--orange); }
.timeMark small { margin: clamp(2px, 0.3vw, 4px) 0 0 clamp(16px, 2vw, 22px); font-family: 'Space Mono', monospace; font-size: var(--fs-label); font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: rgba(255, 255, 255, 0.5); }

.actionMark { display: flex; align-items: flex-start; gap: clamp(10px, 1.3vw, 16px); }
.iconChassis { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: clamp(28px, 3.2vw, 36px); height: clamp(28px, 3.2vw, 36px); background: var(--orange-dim); border: 1px solid var(--orange-border); border-radius: var(--radius-sm); color: var(--orange); font-size: clamp(13px, 1.4vw, 16px); }
.actionMeta { display: flex; flex-direction: column; gap: clamp(2px, 0.3vw, 3px); min-width: 0; }
.actionMeta strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: 'Cinzel', serif; font-size: var(--fs-action); font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: var(--orange); }
.actionMeta span { font-family: 'Space Mono', monospace; font-size: var(--fs-label); font-weight: 700; text-transform: uppercase; color: rgba(255, 255, 255, 0.5); }

.targetMark { min-width: 0; }
.targetMark p { margin: 0; overflow-wrap: break-word; word-break: break-word; font-size: var(--fs-target); font-weight: 700; line-height: 1.45; color: rgba(255, 255, 255, 0.82); }

.inspectIcon { justify-self: end; align-self: start; margin-top: 1px; color: var(--orange); font-size: clamp(14px, 1.6vw, 18px); opacity: 0.75; transition: transform 0.2s ease, opacity 0.18s ease; }
.logRow:hover .inspectIcon { opacity: 1; }

/* SELECTED row: head takes a wash of the row's own colour, chevron flips */
.logRow.expanded, .logRow.expanded:hover { background: transparent; }
.logRow.expanded .logMain { background: rgba(255, 255, 255, 0.05); background: color-mix(in srgb, var(--rail) 12%, transparent); }
.logRow.expanded .inspectIcon { transform: rotate(180deg); opacity: 1; }

/* the extension: near-black readout. Its text shares the row's rail colour. The rail itself runs down through it. */
.traceDetails { overflow: hidden; background: #0a1214; transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.traceClosed { max-height: 0; }
.traceOpen { max-height: clamp(200px, 30vw, 400px); overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--rail) transparent; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.rawBox { margin: 0; padding: clamp(10px, 1.3vw, 14px) clamp(12px, 1.5vw, 18px); }
.rawHeader { display: flex; align-items: center; gap: clamp(7px, 0.9vw, 10px); margin-bottom: clamp(10px, 1.3vw, 14px); font-size: var(--fs-label); font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: var(--rail); opacity: 0.85; }
.rawOutput { margin: 0; white-space: pre-wrap; word-break: break-all; font-family: 'Space Mono', monospace; font-size: clamp(10px, 1.05vw, 12px); line-height: 1.6; color: var(--rail); }

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

CAT_BLOCK = "\n/* fix152: one colour per action. The catalogue order gives every known action its own hue (golden-angle\n   spacing so neighbours never look alike); an unlisted code gets a stable colour from its own name. */\nconst RAIL = {};\nObject.keys(INDEX).forEach((code, i) => {\n    RAIL[code] = 'hsl(' + Math.round((i * 137.508 + 18) % 360) + ', 72%, 64%)';\n});\nexport const actionColor = (code) => {\n    const key = String(code || '');\n    if (RAIL[key]) return RAIL[key];\n    let h = 0;\n    for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) % 360;\n    return 'hsl(' + h + ', 72%, 64%)';\n};\n\nexport default ACTION_GROUPS;"

GUIDE_OLD = '### Audit list + unsaved-changes popup (fix151)\n- Audit log rows sit as one white card (`.logCard`) on a cream `#f2ede4` tray (`.logTray`), hairline dividers, navy text -- the Report Catalogue look WITHOUT its orange. Hover = navy tint. The SELECTED (open) row head is solid navy `#1a2e30` with light text and a flipped chevron; the extension uses the catalogue readout colour `#28383a`.\n- One left line only: the severity rail on `.logRow` (red/orange/green/cyan) runs through the extension. `.rawBox` has no border-left. Do not add one back.\n- `UnsavedChangesModal` is built from `HardwareModal.module.css` classes (backdrop, modalBody, header, title, modalInfoBox, modalFooter, modalBtnPrimary/Secondary). No X (DESIGN RULE 1); two buttons; Esc / backdrop = KEEP EDITING. Props unchanged.\n'

GUIDE_NEW = '### Audit list, popup X, date picker, Expenses cream cards (fix152)\n- Audit list is DARK (panel gradient, zebra rows). Small parts use the app orange: clock icons, icon frames, chevrons, and the Cinzel action titles. The cream tray / white card of fix151 is gone.\n- Every action has its OWN left-rail colour: `actionColor(code)` in `auditCatalog.js` (golden-angle hues by catalogue order, hash for unlisted codes). The page sets it as `--rail` on the row; the rail, the hover / selected wash and the opened readout text (`.rawHeader`, `.rawOutput`) all read `var(--rail)`. Do not re-add severity buckets.\n- OPERATOR and PROTOCOL dropdowns on Audit are ALWAYS in the active orange state (All Staff / All Actions included). It is pure CSS on `.hwSelectWrap`.\n- `AuditPage.module.css` was rewritten in fix152: one rule per class, no stacked overrides. Keep it that way.\n- `UnsavedChangesModal` has the X (`modal.closeBtn`, X = KEEP EDITING) plus DISCARD & LEAVE / KEEP EDITING. Those two are decisions, not a CANCEL, so DESIGN RULE 1 is not broken. Esc / backdrop = KEEP EDITING.\n- ONE DATE PICKER: `components/common/HardwareDatePicker.jsx`. The browser calendar cannot be themed, so never use `<input type="date">`. Props: `value` (\'yyyy-mm-dd\'), `onChange(value)` (a string, NOT an event), `className` (styles the visible field), `block` (fill the parent), `ariaLabel`. Used by Audit, Report Studio, Intake. The one `datetime-local` (Folder page deadline) is still native.\n- Expenses: the Log-an-expense box and the Recent-entries table share one look: darker cream inside `#e3dac8`, a solid 2px cream `#f2ede4` frame, zebra rows, row separators at 20%. Orange text on that cream is `#9a4407`.\n'

# ============================ EDIT PART 2 START ============================
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (AUDIT_JSX, AUDIT_CAT, UCM_JSX, REPORT_JSX, INTAKE_JSX, EXP_CSS, GUIDE)
for _p in LOAD_FILES:
    load(_p)

def L(*lines):
    return "\n".join(lines)

# ---- 1. New date picker + rewritten Audit stylesheet (whole files) ----
newfile(DP_JSX, DP_JSX_TEXT, "HardwareDatePicker.jsx", "fix152")
newfile(DP_CSS, DP_CSS_TEXT, "HardwareDatePicker.module.css", "fix152")
newfile(AUDIT_CSS, AUDIT_CSS_TEXT, "AuditPage.module.css (rewritten, dark)", "fix152: whole file rewritten")

# ---- 2. Popup gets its X back ----
patch(UCM_JSX,
      "import { FiAlertTriangle, FiSave, FiLogOut } from 'react-icons/fi';",
      "import { FiAlertTriangle, FiSave, FiLogOut, FiX } from 'react-icons/fi';",
      "Popup: import the X icon")
patch(UCM_JSX,
      " * DESIGN RULE 1 (X is the closer) -> no X here, two explicit buttons instead.",
      " * fix152: the X is back (same closeBtn as the Recovery CALL LOG popup). X = KEEP EDITING, the safe choice.\n * The two buttons are real decisions (leave / stay), not a CANCEL, so DESIGN RULE 1 still holds.",
      "Popup: comment")
patch(UCM_JSX,
      L("                    <span id=\"ucm-title\" className={modal.title}>UNSAVED CHANGES</span>",
        "                </header>"),
      L("                    <span id=\"ucm-title\" className={modal.title}>UNSAVED CHANGES</span>",
        "                    <button type=\"button\" className={modal.closeBtn} onClick={onStay} aria-label=\"Close and keep editing\">",
        "                        <FiX aria-hidden=\"true\" />",
        "                    </button>",
        "                </header>"),
      "Popup: X button in the header")

# ---- 3. Per-action colours ----
patch(AUDIT_CAT,
      "export default ACTION_GROUPS;",
      CAT_BLOCK,
      "Catalogue: actionColor() -- one colour per action")

# ---- 4. Audit page JSX ----
patch(AUDIT_JSX,
      L("import {",
        "    FiShield, FiSearch, FiActivity, FiClock,",
        "    FiDatabase, FiChevronDown, FiX, FiFilter,",
        "    FiChevronLeft, FiChevronRight, FiPhoneCall, FiUser, FiDownloadCloud",
        "} from 'react-icons/fi';"),
      L("import {",
        "    FiSearch, FiActivity, FiClock, FiRefreshCw,",
        "    FiDatabase, FiChevronDown, FiX, FiFilter,",
        "    FiChevronLeft, FiChevronRight, FiPhoneCall, FiUser, FiDownloadCloud",
        "} from 'react-icons/fi';"),
      "Audit JSX: imports (drop unused FiShield, merge FiRefreshCw)")
patch(AUDIT_JSX,
      L("import { FiRefreshCw } from 'react-icons/fi';",
        "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';"),
      L("import HardwareDatePicker from '../../components/common/HardwareDatePicker';",
        "import { actionColor } from './auditCatalog';",
        "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';"),
      "Audit JSX: import date picker + actionColor")
patch(AUDIT_JSX,
      L("    const getSeverityClass = action => {",
        "        const a = action?.toUpperCase() || '';",
        "        if (a.includes('DELETE') || a.includes('OVERRIDE') || a.includes('SUSPEND')) return styles.severityHigh;",
        "        if (a.includes('REWRITE') || a.includes('UPDATE')  || a.includes('PAYMENT')) return styles.severityMed;",
        "        if (a.includes('RECOVERY') || a.includes('MISSION'))                          return styles.severityIntel;",
        "        return styles.severityLow;",
        "    };",
        "",
        "    const getFriendlyAction = action => {"),
      L("    // Row colour: every action has its own, see actionColor() in auditCatalog.js",
        "    const getFriendlyAction = action => {"),
      "Audit JSX: remove the 4-bucket severity function")
patch(AUDIT_JSX,
      L("                    <div className={`${styles.hwSelectWrap} ${(filters.operator && filters.operator !== 'ALL STAFF') ? styles.hwSelectWrapActive : ''}`}>",
        "                        <HardwareSelect",
        "                            label=\"OPERATOR ID\""),
      L("                    <div className={styles.hwSelectWrap}>",
        "                        <HardwareSelect",
        "                            label=\"OPERATOR ID\""),
      "Audit JSX: staff dropdown always active (styled in CSS)")
patch(AUDIT_JSX,
      L("                    <div className={`${styles.hwSelectWrap} ${(filters.action && filters.action !== 'ALL ACTIONS') ? styles.hwSelectWrapActive : ''}`}>",
        "                        <HardwareSelect",
        "                            label=\"PROTOCOL CLASS\""),
      L("                    <div className={styles.hwSelectWrap}>",
        "                        <HardwareSelect",
        "                            label=\"PROTOCOL CLASS\""),
      "Audit JSX: action dropdown always active (styled in CSS)")
patch(AUDIT_JSX,
      L("                        <input type=\"date\" value={filters.from} aria-label=\"From date\"",
        "                            onChange={e => setFilters({...filters, from: e.target.value})} />"),
      "                        <HardwareDatePicker value={filters.from} ariaLabel=\"From date\" onChange={v => setFilters({...filters, from: v})} />",
      "Audit JSX: FROM date uses the app date picker")
patch(AUDIT_JSX,
      L("                        <input type=\"date\" value={filters.to} aria-label=\"To date\"",
        "                            onChange={e => setFilters({...filters, to: e.target.value})} />"),
      "                        <HardwareDatePicker value={filters.to} ariaLabel=\"To date\" onChange={v => setFilters({...filters, to: v})} />",
      "Audit JSX: TO date uses the app date picker")
patch(AUDIT_JSX,
      L("                    {!loading && visibleLogs.length > 0 && (<div className={styles.logTray}><div className={styles.logCard}>",
        "                    {visibleLogs.map(log => ("),
      "                    {!loading && visibleLogs.map(log => (",
      "Audit JSX: remove the cream tray + card wrapper (open)")
patch(AUDIT_JSX,
      L("                    ))}",
        "                    </div></div>)}",
        "                </div>"),
      L("                    ))}",
        "                </div>"),
      "Audit JSX: remove the cream tray + card wrapper (close)")
patch(AUDIT_JSX,
      "className={`${styles.logRow} ${getSeverityClass(log.action)} ${expandedId === log.id ? styles.expanded : ''}`}",
      L("className={`${styles.logRow} ${expandedId === log.id ? styles.expanded : ''}`}",
        "                            style={{ '--rail': actionColor(log.action) }}"),
      "Audit JSX: each row carries its own rail colour")
patch(AUDIT_JSX,
      "<p>{log.details.length > 85 ? log.details.substring(0, 85) + '...' : log.details}</p>",
      "<p>{(log.details || '').length > 85 ? log.details.substring(0, 85) + '...' : (log.details || '')}</p>",
      "Audit JSX: a log with no details no longer crashes the list")

# ---- 5. Report Studio + Intake use the same picker ----
patch(REPORT_JSX,
      "import CornerDecor from '../../components/ui/CornerDecor';",
      L("import CornerDecor from '../../components/ui/CornerDecor';",
        "import HardwareDatePicker from '../../components/common/HardwareDatePicker';"),
      "Report Studio: import the date picker")
patch(REPORT_JSX,
      "<input type=\"date\" value={from} onChange={e => setFrom(e.target.value)} aria-label=\"From date\" />",
      "<HardwareDatePicker value={from} onChange={setFrom} ariaLabel=\"From date\" />",
      "Report Studio: FROM date")
patch(REPORT_JSX,
      "<input type=\"date\" value={to} onChange={e => setTo(e.target.value)} aria-label=\"To date\" />",
      "<HardwareDatePicker value={to} onChange={setTo} ariaLabel=\"To date\" />",
      "Report Studio: TO date")
patch(INTAKE_JSX,
      "import CollapsibleSection from '../../components/ui/CollapsibleSection';",
      L("import CollapsibleSection from '../../components/ui/CollapsibleSection';",
        "import HardwareDatePicker from '../../components/common/HardwareDatePicker';"),
      "Intake: import the date picker")
patch(INTAKE_JSX,
      L("<input type=\"date\" className={styles.input} value={projectStartDate}",
        "                                onChange={e => { setProjectStartDate(e.target.value); markDirty(); }} />"),
      "<HardwareDatePicker block className={styles.input} value={projectStartDate} ariaLabel=\"Date started\" onChange={v => { setProjectStartDate(v); markDirty(); }} />",
      "Intake: Date Started")
patch(INTAKE_JSX,
      "<input type=\"date\" className={styles.input} value={titleIssueDate} onChange={e => { setTitleIssueDate(e.target.value); markDirty(); }} />",
      "<HardwareDatePicker block className={styles.input} value={titleIssueDate} ariaLabel=\"Title date\" onChange={v => { setTitleIssueDate(v); markDirty(); }} />",
      "Intake: Title Date")

# ---- 6. Expenses: darker cream sections, white frame on both, zebra, stronger separators ----
patch(EXP_CSS,
      L(".presetRow {",
        "  background: #f2ede4; border: 1px solid rgba(26,46,48,0.14);"),
      L(".presetRow {",
        "  background: #e3dac8; border: 2px solid #f2ede4; /* fix152: darker inside, cream frame outside */"),
      "Expenses CSS: Log-an-expense box darker inside + cream frame")
patch(EXP_CSS,
      ".tableScroll { background: #f2ede4; border: 1px solid rgba(26,46,48,0.14); border-radius: var(--radius-sm); }",
      ".tableScroll { background: #e3dac8; border: 2px solid #f2ede4; border-radius: var(--radius-sm); }",
      "Expenses CSS: Recent-entries table darker inside + cream frame")
patch(EXP_CSS,
      L(".ledgerTable tbody td { color: #1a2e30; border-bottom: 1px solid rgba(26,46,48,0.1); }",
        ".ledgerTable tbody tr:last-child td { border-bottom: none; }"),
      L(".ledgerTable tbody td { color: #1a2e30; border-bottom: 1px solid rgba(26,46,48,0.2); }",
        ".ledgerTable tbody tr:last-child td { border-bottom: none; }",
        "/* fix152: every second row a shade darker, so a row can be followed across the table */",
        ".ledgerTable tbody tr.row:nth-child(even) td { background: rgba(26,46,48,0.075); }"),
      "Expenses CSS: stronger separators + zebra rows")
patch(EXP_CSS,
      ".ledgerTable tbody tr.row:hover { background: rgba(26,46,48,0.07); }",
      ".ledgerTable tbody tr.row:hover td { background: rgba(26,46,48,0.14); }",
      "Expenses CSS: hover paints the cells (so it shows over the zebra)")
patch(EXP_CSS,
      ".ledgerTable tbody td.dateCell  { color: rgba(26,46,48,0.68); }",
      ".ledgerTable tbody td.dateCell  { color: rgba(26,46,48,0.78); }",
      "Expenses CSS: date text keeps contrast on the darker cream")
patch(EXP_CSS,
      ".categoryTag { color: #b45309; }",
      ".categoryTag { color: #9a4407; }",
      "Expenses CSS: category text keeps contrast")
patch(EXP_CSS,
      ".editedBadge { color: #b45309; }",
      ".editedBadge { color: #9a4407; }",
      "Expenses CSS: edited badge keeps contrast")
patch(EXP_CSS,
      ".editIconBtn { background: rgba(238,140,58,0.2); color: #b45309; }",
      ".editIconBtn { background: rgba(238,140,58,0.2); color: #9a4407; }",
      "Expenses CSS: edit icon keeps contrast")

# ---- 7. guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix151: Audit list from Report Catalogue + unsaved-changes popup on HardwareModal standard, Section 7)",
      "# Last updated: September 2026 (fix152: Audit dark redesign + per-action colours, popup X, HardwareDatePicker, Expenses cream cards, Section 7)",
      "Guide: header line")
patch(GUIDE,
      GUIDE_OLD,
      GUIDE_NEW,
      "Guide: replace the fix151 audit note with the fix152 truth")

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