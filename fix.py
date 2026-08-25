#!/usr/bin/env python3
"""
fix.py — Refined Ledger consistency pass.
- Corner brackets only on expanded body (animated)
- Orange separator fades in/out with expand
- Curved corner brackets
- Smaller fields + tighter spacing
- Red delete icons on hover
- File upload fixed
Run: py fix.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WROTE, FAILED = [], []

def write(rel: str, content: str):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(content, encoding="utf-8")
        WROTE.append(rel)
    except Exception as e:
        FAILED.append((rel, str(e)))

# =====================================================================
# 1) CollapsibleSection.jsx — CornerDecor only in body, animated separator
# =====================================================================
write("erp-frontend/src/components/ui/CollapsibleSection.jsx", r"""// PATH: erp-frontend/src/components/ui/CollapsibleSection.jsx
import React, { useState } from 'react';
import { FiChevronDown } from 'react-icons/fi';
import CornerDecor from './CornerDecor';
import styles from './CollapsibleSection.module.css';

const CollapsibleSection = ({
    icon,
    title,
    right,
    defaultOpen = true,
    open: controlledOpen,
    onToggle,
    accent = false,
    className = '',
    children,
}) => {
    const [internalOpen, setInternalOpen] = useState(defaultOpen);
    const isControlled = controlledOpen !== undefined;
    const open = isControlled ? controlledOpen : internalOpen;

    const toggle = () => {
        if (isControlled) onToggle?.(!open);
        else setInternalOpen(o => !o);
    };

    return (
        <section className={`${styles.section} ${accent ? styles.accent : ''} ${className}`}>
            <button
                type="button"
                className={`${styles.header} ${open ? styles.headerOpen : ''}`}
                onClick={toggle}
                aria-expanded={open}
            >
                <span className={styles.headerLeft}>
                    {icon}
                    <h2 className={styles.title}>{title}</h2>
                </span>
                <span className={styles.headerRight}>
                    {right && <span onClick={e => e.stopPropagation()}>{right}</span>}
                    <FiChevronDown
                        aria-hidden="true"
                        className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`}
                    />
                </span>
            </button>
            {open && (
                <div className={styles.body}>
                    <CornerDecor />
                    {children}
                </div>
            )}
        </section>
    );
};

export default CollapsibleSection;
""")

# =====================================================================
# 2) CollapsibleSection.module.css — animated separator, tighter spacing
# =====================================================================
write("erp-frontend/src/components/ui/CollapsibleSection.module.css", r"""/* PATH: erp-frontend/src/components/ui/CollapsibleSection.module.css */
.section {
    --orange: #EE8C3A;
    --orange-dim: rgba(238, 140, 58, 0.18);
    position: relative;
    background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);
    border: 1px solid rgba(238, 140, 58, 0.2);
    border-radius: 10px;
    overflow: visible;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.section:hover {
    border-color: var(--orange);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
.section.accent { border: 2px solid var(--orange); }

/* Header - no border decoration when closed */
.header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(6px, 1vw, 12px);
    padding: clamp(10px, 1.4vw, 16px) clamp(11px, 1.6vw, 18px);
    background: #162a2c;
    border: none;
    border-bottom: 3px solid transparent; /* hidden when closed */
    cursor: pointer;
    text-align: left;
    font: inherit;
    color: inherit;
    transition: border-bottom-color 0.25s ease;
}
.header:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }

/* Animated orange separator - only visible when open */
.headerOpen {
    border-bottom-color: var(--orange);
    box-shadow: 0 3px 0 rgba(238, 140, 58, 0.15);
}

.headerLeft {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    color: var(--orange);
    font-size: clamp(13px, 1.5vw, 17px);
    filter: drop-shadow(0 0 4px rgba(238, 140, 58, 0.4));
}

.title {
    font-family: 'Cinzel', serif;
    font-size: clamp(11px, 1.4vw, 14px);
    font-weight: 700;
    color: var(--orange);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0;
    transition: color 0.18s ease;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.header:hover .title { color: #fff; }

.headerRight {
    display: flex;
    align-items: center;
    gap: clamp(6px, 1vw, 12px);
    flex-shrink: 0;
}

.chevron {
    color: rgba(255, 255, 255, 0.4);
    font-size: 15px;
    transition: transform 0.2s ease, color 0.2s ease;
    flex-shrink: 0;
}
.chevronOpen { transform: rotate(180deg); color: var(--orange); }

/* Body - relative for CornerDecor positioning */
.body {
    position: relative;
    padding: 0 clamp(12px, 1.6vw, 18px) clamp(12px, 1.6vw, 18px);
    padding-top: clamp(12px, 1.6vw, 18px);
    display: flex;
    flex-direction: column;
    gap: clamp(8px, 1.3vw, 16px);
    animation: expand 0.2s ease-out;
}

@keyframes expand {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
    .header { padding: 10px 12px; }
    .body { padding: 10px 12px 12px; }
}
""")

# =====================================================================
# 3) CornerDecor.module.css — curved brackets
# =====================================================================
write("erp-frontend/src/components/ui/CornerDecor.module.css", r"""/* PATH: erp-frontend/src/components/ui/CornerDecor.module.css */
/* CURVED CORNER BRACKETS - softer, more refined */
.cornerAccent {
    position: absolute;
    width: 14px;
    height: 14px;
    border: 1.5px solid var(--orange);
    opacity: 0.55;
    pointer-events: none;
}

.cornerAccent::after {
    content: '';
    position: absolute;
    width: 4px;
    height: 4px;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(255, 255, 255, 0.4);
}

/* CURVED - larger border-radius for softer corners */
.topLeft { top: 8px; left: 8px; border-right: none; border-bottom: none; border-radius: 6px 0 0 0; }
.topLeft::after { top: -2px; left: -2px; }

.topRight { top: 8px; right: 8px; border-left: none; border-bottom: none; border-radius: 0 6px 0 0; }
.topRight::after { top: -2px; right: -2px; }

.bottomLeft { bottom: 8px; left: 8px; border-right: none; border-top: none; border-radius: 0 0 0 6px; }
.bottomLeft::after { bottom: -2px; left: -2px; }

.bottomRight { bottom: 8px; right: 8px; border-left: none; border-top: none; border-radius: 0 0 6px 0; }
.bottomRight::after { bottom: -2px; right: -2px; }

/* Border pins */
.pins {
    position: absolute;
    display: flex;
    gap: 7px;
    pointer-events: none;
}

.pins.top { top: -3px; left: 50%; transform: translateX(-50%); }
.pins.bottom { bottom: -3px; left: 50%; transform: translateX(-50%); }

.pin {
    width: 3px;
    height: 5px;
    background: var(--orange);
    box-shadow: 0 0 5px rgba(238, 140, 58, 0.4);
    border-radius: 1px;
}
""")

# =====================================================================
# 4) IntakePage.module.css — smaller fields, tighter spacing, red deletes
# =====================================================================
write("erp-frontend/src/pages/Intake/IntakePage.module.css", r"""/* PATH: erp-frontend/src/pages/Intake/IntakePage.module.css
   Refined: smaller fields, tighter spacing, red delete icons,
   curved corner brackets, animated separator. */
:root {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #213E40;
    --navy-deep:     #1a2e30;
    --red:           #ef4444;
    --green:         #10b981;

    --gap-xl:    clamp(12px, 1.8vw, 20px);
    --gap-lg:    clamp(8px,  1.3vw, 16px);
    --gap-md:    clamp(6px,  1vw,   12px);
    --radius:    10px;
    --radius-sm: 6px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(8px,  0.85vw, 10px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-td:     clamp(10px, 1.05vw, 12px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-input:  clamp(10px, 1vw,   12px); /* smaller input font */
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);
}

.container {
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) 0;
    font-family: 'Inter', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    gap: var(--gap-xl);
    box-sizing: border-box;
}

@keyframes warmBoot {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* -- PAGE HEADER -- */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
    flex-shrink: 0;
}
.headerLeft { display: flex; flex-direction: column; gap: clamp(3px, 0.4vw, 5px); min-width: 0; flex: 1; }

.title {
    font-family: 'Cinzel', serif;
    color: var(--navy-deep);
    font-size: var(--fs-h1);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    line-height: 1.1;
    margin: 0;
}
.subtitle {
    font-family: 'Inter', sans-serif;
    color: #64748b;
    font-size: var(--fs-sub);
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 0;
}

.actions { display: flex; gap: var(--gap-md); flex-shrink: 0; }
.sections { display: flex; flex-direction: column; gap: var(--gap-lg); }

.splitRow {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--gap-lg);
    align-items: start;
}

/* -- BUTTONS -- */
.btn {
    font-family: 'Inter', sans-serif;
    font-size: var(--fs-btn);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: clamp(6px, 0.9vw, 9px) clamp(10px, 1.4vw, 16px);
    border-radius: var(--radius-sm);
    border: 1.5px solid rgba(255, 255, 255, 0.1);
    background: transparent;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    display: flex;
    align-items: center;
    gap: 5px;
}
.btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.07); border-color: rgba(255, 255, 255, 0.22); color: #fff; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.btn.primary { background: var(--orange); color: #fff; border-color: var(--orange); }
.btn.primary:hover { background: #d97a2b; border-color: #d97a2b; color: #fff; }
.btn:disabled { opacity: 0.18; cursor: not-allowed; }

/* RED DELETE ICONS */
.btn.deleteBtn {
    border-color: rgba(239, 68, 68, 0.3);
    color: rgba(239, 68, 68, 0.7);
}
.btn.deleteBtn:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.15);
    border-color: var(--red);
    color: var(--red);
}

.legacyBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(6px, 0.9vw, 9px) clamp(10px, 1.4vw, 16px);
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-size: clamp(9px, 0.95vw, 11px);
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
}
.legacyBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }

/* -- FIELDS (smaller) -- */
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--gap-lg); }
.grid3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: var(--gap-lg); }

.field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }

.label {
    font-family: 'Inter', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    letter-spacing: 2px;
}
.required::after { content: '*'; color: var(--red); margin-left: 4px; }

.hint {
    font-size: var(--fs-meta);
    font-weight: 700;
    color: rgba(255, 255, 255, 0.35);
    letter-spacing: 0.5px;
    margin: 0;
}

/* SMALLER INPUTS - reduced padding and height */
.input, .textarea {
    font-family: 'Inter', sans-serif;
    font-size: var(--fs-input);
    font-weight: 600;
    padding: clamp(6px, 0.9vw, 10px) clamp(8px, 1.2vw, 14px);
    border: 2px solid rgba(238, 140, 58, 0.3);
    border-radius: var(--radius-sm);
    background: #ffffff;
    color: var(--navy);
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
    height: clamp(36px, 4.5vw, 42px); /* explicit smaller height */
    line-height: 1.2;
}
.textarea { height: auto; min-height: 90px; resize: vertical; }
.input:hover, .textarea:hover { border-color: var(--orange); }
.input:focus, .textarea:focus {
    outline: none;
    border-color: var(--orange);
    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.18);
}
.input:disabled { color: rgba(33, 62, 64, 0.5); cursor: not-allowed; }
.input.indexValue {
    font-family: 'Space Mono', monospace;
    font-weight: 900;
    letter-spacing: 1px;
    color: var(--orange);
}
.input.indexValue:disabled { color: var(--orange); opacity: 1; }

/* -- TYPE TOGGLE -- */
.typeGroup { display: flex; gap: clamp(6px, 1vw, 12px); flex-wrap: wrap; }
.typeBtn {
    display: flex;
    align-items: center;
    gap: 5px;
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(6px, 0.9vw, 9px) clamp(10px, 1.4vw, 16px);
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.95vw, 11px);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}
.typeBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.typeBtnActive,
.typeBtnActive:hover {
    background: #EE8C3A;
    color: #1a2e30;
    border-color: #EE8C3A;
    font-weight: 900;
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.4);
}
.typeHint { font-size: var(--fs-meta); color: rgba(255, 255, 255, 0.35); margin: 2px 0 0 0; letter-spacing: 0.5px; }

/* -- INNER WELLS (tighter) -- */
.ownerRow {
    display: grid;
    grid-template-columns: 1.2fr 2fr 1fr 1.5fr auto;
    gap: var(--gap-md);
    align-items: end;
    padding: clamp(6px, 1vw, 10px);
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 3px solid transparent;
    border-radius: var(--radius-sm);
    transition: background 0.18s, border-left-color 0.18s;
}
.ownerRow:hover { background: rgba(255, 255, 255, 0.04); border-left-color: var(--orange); }

.subheading {
    font-family: 'Cinzel', serif;
    font-size: clamp(12px, 1.4vw, 14px);
    font-weight: 700;
    color: var(--orange);
    letter-spacing: 2px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 5px;
    margin: 2px 0 0 0;
}

.inlineAddRow {
    display: flex;
    gap: var(--gap-md);
    align-items: center;
    flex-wrap: wrap;
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid var(--orange-border);
    border-radius: var(--radius-sm);
    padding: var(--gap-md);
}
.inlineAddRow .input { width: auto; flex: 1 1 180px; }

/* -- STAGES -- */
.stageList { display: flex; flex-direction: column; gap: var(--gap-md); }
.stageItem {
    display: flex;
    align-items: center;
    gap: var(--gap-md);
    padding: clamp(6px, 1vw, 10px);
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 3px solid transparent;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background 0.18s, border-left-color 0.18s;
}
.stageItem:hover { background: rgba(255, 255, 255, 0.04); border-left-color: var(--orange); }
.stageItem.checked { border-left-color: var(--orange); background: rgba(238, 140, 58, 0.07); }
.stageItem.stageLocked { cursor: not-allowed; background: rgba(0, 0, 0, 0.25); }
.checkbox { width: 16px; height: 16px; accent-color: var(--orange); cursor: pointer; flex-shrink: 0; }
.stageName { font-weight: 700; color: #fff; font-size: var(--fs-td); letter-spacing: 0.5px; }
.lockedTag {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 1px;
}

.presetList { display: flex; gap: var(--gap-md); flex-wrap: wrap; }
.presetChip {
    display: flex;
    align-items: center;
    gap: 5px;
    background: var(--orange-dim);
    color: var(--orange);
    border: 1px solid var(--orange-border);
    border-radius: 999px;
    padding: 3px 9px;
    font-size: var(--fs-meta);
    font-weight: 700;
}
.presetChipRemove {
    background: none; border: none; color: inherit; cursor: pointer;
    display: flex; align-items: center; padding: 0;
}

/* -- FINANCIALS -- */
.financialsSummary {
    background: rgba(0, 0, 0, 0.15);
    padding: var(--gap-lg);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
}
.finRow { display: flex; justify-content: space-between; font-weight: 700; color: rgba(255, 255, 255, 0.85); font-size: var(--fs-td); letter-spacing: 0.5px; }
.finRow.total { color: var(--orange); font-size: clamp(14px, 1.5vw, 18px); border-top: 1px solid rgba(238, 140, 58, 0.25); padding-top: var(--gap-md); }

/* -- DOCUMENTS -- */
.dropzone {
    border: 2px dashed rgba(238, 140, 58, 0.4);
    border-radius: var(--radius);
    padding: var(--gap-lg);
    text-align: center;
    color: rgba(255, 255, 255, 0.45);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
}
.dropzone:hover { background: var(--orange-dim); border-color: var(--orange); color: var(--orange); }

.fileList { display: flex; flex-direction: column; gap: var(--gap-md); }
.fileItem {
    display: flex; justify-content: space-between; align-items: center;
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 3px solid transparent;
    color: #fff;
    font-size: var(--fs-td);
    font-weight: 600;
    padding: clamp(6px, 1vw, 10px);
    border-radius: var(--radius-sm);
    transition: background 0.18s, border-left-color 0.18s;
}
.fileItem:hover { background: rgba(255, 255, 255, 0.04); border-left-color: var(--orange); }

/* -- TOASTS -- */
.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--navy-deep);
    color: #fff;
    border: 1px solid var(--orange-border);
    padding: 12px 20px;
    border-radius: var(--radius-sm);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    z-index: 9999;
    animation: slideIn 0.3s ease-out;
}
.toast.error { background: var(--red); border-color: var(--red); }
.toast.success { background: var(--green); border-color: var(--green); }
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }

@media (max-width: 900px) {
    .splitRow { grid-template-columns: 1fr; }
    .ownerRow { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
    .pageHeader { flex-direction: column; align-items: flex-start; gap: var(--gap-lg); border-radius: 0; }
    .actions { width: 100%; }
    .actions .btn { flex: 1; justify-content: center; }
}
""")

# =====================================================================
# 5) IntakePage.jsx — add deleteBtn class, fix file input click
# =====================================================================
write("erp-frontend/src/pages/Intake/IntakePage.jsx", r"""// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiLock, FiEdit3, FiBookmark, FiX
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareSelect from '../../components/common/HardwareSelect';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import styles from './IntakePage.module.css';

const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const PROJECT_TYPES = [
    { value: 'NEW_FOLDER',   label: 'New Folder',   icon: <FiFolderPlus aria-hidden="true" />, hint: 'No title yet' },
    { value: 'NEW_TITLE',    label: 'New Title',    icon: <FiFilePlus aria-hidden="true" />,   hint: 'Title captured now' },
    { value: 'LEGACY_TITLE', label: 'Legacy Title', icon: <FiArchive aria-hidden="true" />,    hint: 'Existing title, receivable' },
];

const TENURE_OPTIONS = ['FREEHOLD', 'MAILO', 'LEASEHOLD', 'CUSTOMARY'];
const todayISO = () => new Date().toISOString().slice(0, 10);

const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';
const loadPresets = () => {
    try {
        const raw = localStorage.getItem(PRESET_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch { return []; }
};
const savePresets = (presets) => {
    try { localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(presets)); } catch {}
};

export default function IntakePage() {
    const navigate = useNavigate();
    const fileInputRef = useRef(null);
    const [saving, setSaving] = useState(false);
    const [nextIndex, setNextIndex] = useState('');
    const [projectType, setProjectType] = useState('NEW_FOLDER');
    const [projectStartDate, setProjectStartDate] = useState(todayISO);
    const [owners, setOwners] = useState([EMPTY_OWNER()]);

    const [district, setDistrict] = useState('');
    const [county, setCounty] = useState('');
    const [subCounty, setSubCounty] = useState('');
    const [parish, setParish] = useState('');
    const [village, setVillage] = useState('');
    const [area, setArea] = useState('');

    const [templates, setTemplates] = useState([]);
    const [checkedStages, setCheckedStages] = useState({});
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [newStageCost, setNewStageCost] = useState('');
    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState('');
    const [showSavePreset, setShowSavePreset] = useState(false);

    const [titleId, setTitleId] = useState('');
    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');
    const [titleIssueDate, setTitleIssueDate] = useState('');

    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);
    const [initialStorageFee, setInitialStorageFee] = useState(0);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState(0);

    const [fileQueue, setFileQueue] = useState([]);
    const [notes, setNotes] = useState('');

    const [toasts, setToasts] = useState([]);
    const toast = useCallback((msg, type = 'info') => {
        const id = Date.now();
        setToasts(p => [...p, { id, msg, type }]);
        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    }, []);

    const fetchTemplates = useCallback(() => {
        stageTemplateService.getTemplate().then(t => setTemplates(t || [])).catch(() => {});
    }, []);
    useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

    useEffect(() => {
        landService.getNextIndex().then(idx => setNextIndex(idx || '')).catch(() => {});
    }, []);

    const sortedTemplates = useMemo(
        () => [...templates].sort((a, b) => (a.displayOrder ?? 0) - (b.displayOrder ?? 0)),
        [templates]
    );
    const firstStageId = sortedTemplates[0]?.id;
    const lastStageId = sortedTemplates[sortedTemplates.length - 1]?.id;

    useEffect(() => {
        if (!sortedTemplates.length) return;
        setCheckedStages(prev => {
            const next = { ...prev };
            if (firstStageId && next[firstStageId] === undefined) next[firstStageId] = true;
            if (lastStageId && next[lastStageId] === undefined) next[lastStageId] = true;
            return next;
        });
    }, [sortedTemplates.length, firstStageId, lastStageId]);

    const finalStageChecked = lastStageId ? !!checkedStages[lastStageId] : false;
    const isLegacy = projectType === 'LEGACY_TITLE';
    const titleAtIntake = projectType === 'NEW_TITLE';
    const isTitleSectionVisible = isLegacy || titleAtIntake || finalStageChecked;

    const handleProjectTypeChange = (value) => {
        setProjectType(value);
        if (value === 'LEGACY_TITLE') {
            const allChecked = {};
            sortedTemplates.forEach(t => { allChecked[t.id] = true; });
            setCheckedStages(allChecked);
        }
    };

    const toggleStage = (id) => {
        if (id === firstStageId || id === lastStageId) return;
        setCheckedStages(p => ({ ...p, [id]: !p[id] }));
    };

    const handleAddStage = async () => {
        if (!newStageName.trim()) { toast('Enter a stage name first.', 'error'); return; }
        try {
            const last = sortedTemplates[sortedTemplates.length - 1];
            const lastOrder = last?.displayOrder ?? sortedTemplates.length;
            if (last) {
                await stageTemplateService.updateTemplateStage(last.id, last.stageName, last.defaultCost, lastOrder + 1);
            }
            const created = await stageTemplateService.addTemplateStage(
                newStageName.trim(),
                newStageCost ? Number(newStageCost) : 0,
                last ? lastOrder : undefined,
            );
            setNewStageName('');
            setNewStageCost('');
            setAddingStage(false);
            fetchTemplates();
            if (created?.id) setCheckedStages(p => ({ ...p, [created.id]: true }));
            toast('Stage added to checklist.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not add stage.', 'error');
        }
    };

    const handleSavePreset = () => {
        if (!presetName.trim()) { toast('Name the preset first.', 'error'); return; }
        const stageNames = sortedTemplates.filter(t => checkedStages[t.id]).map(t => t.stageName);
        const next = [...presets.filter(p => p.name !== presetName.trim()), { name: presetName.trim(), stageNames }];
        setPresets(next);
        savePresets(next);
        setPresetName('');
        setShowSavePreset(false);
        toast('Stage preset saved.', 'success');
    };

    const applyPreset = (name) => {
        if (!name) return;
        const preset = presets.find(p => p.name === name);
        if (!preset) return;
        const next = {};
        sortedTemplates.forEach(t => {
            next[t.id] = t.id === firstStageId || t.id === lastStageId || preset.stageNames.includes(t.stageName);
        });
        setCheckedStages(next);
    };

    const deletePreset = (name) => {
        const next = presets.filter(p => p.name !== name);
        setPresets(next);
        savePresets(next);
    };

    const updateOwner = (idx, field, val) => {
        setOwners(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o));
    };

    const handleFileUpload = (e) => {
        const files = Array.from(e.target.files);
        setFileQueue(p => [...p, ...files]);
        e.target.value = ''; // reset so same file can be re-added
    };

    const triggerFileInput = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const handleSubmit = async () => {
        if (!district.trim() || !county.trim()) {
            toast('District and County are required.', 'error'); return;
        }
        for (let o of owners) {
            if (!o.nationalId.trim()) {
                toast('NIN is required for all owners.', 'error'); return;
            }
        }
        if (isTitleSectionVisible) {
            if (!plotNumber.trim()) { toast('Plot Number is required for a title record.', 'error'); return; }
            if (!area.trim()) { toast('Area is required for Title details.', 'error'); return; }
        }

        setSaving(true);
        try {
            const payload = {
                district: district.trim().toUpperCase(),
                county: county.trim().toUpperCase(),
                subCounty: subCounty.trim().toUpperCase(),
                parish: parish.trim().toUpperCase(),
                village: village.trim().toUpperCase(),
                area: area.trim(),
                totalCost: Number(totalCost) || 0,
                initialPayment: Number(initialPayment) || 0,
                isLegacy: isLegacy,
                titleAtIntake: titleAtIntake,
                projectStartDate: projectStartDate || todayISO(),
                owners: owners.map(o => ({
                    fullName: o.fullName.trim().toUpperCase(),
                    phone: o.phone.trim(),
                    email: o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address: o.address.trim(),
                })),
                selectedStages: Object.entries(checkedStages).filter(([, v]) => v).map(([id]) => {
                    const t = templates.find(x => x.id === id);
                    return {
                        stageTemplateId: id,
                        stageName: t ? t.stageName : '',
                        isCustom: false,
                        isCompleted: true
                    };
                }),
                notes: notes.trim() ? [{ content: notes.trim() }] : [],
            };

            if (isTitleSectionVisible) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.blockRoad = blockRoad.trim().toUpperCase();
                payload.titleId = titleId.trim().toUpperCase();
                payload.titleIssueDate = titleIssueDate || null;
            }

            if (isLegacy) {
                payload.isStartAsReceivable = true;
                payload.initialStorageFee = Number(initialStorageFee) || 0;
                payload.monthlyStorageFee = Number(monthlyStorageFee) || 0;
            }

            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Project registered successfully!', 'success');
            setTimeout(() => navigate('/land/projects'), 1500);
        } catch (err) {
            toast(err.response?.data?.message || 'Save failed', 'error');
        } finally {
            setSaving(false);
        }
    };

    const amountOwed = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));

    let n = 0;
    const nIndex = ++n;
    const nOwners = ++n;
    const nTitle = isTitleSectionVisible ? ++n : null;
    const nLocation = ++n;
    const nStages = ++n;
    const nFinancials = ++n;
    const nDocuments = ++n;
    const nNotes = ++n;

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Project</h1>
                    <p className={styles.subtitle}>Intake Form</p>
                </div>
                <div className={styles.actions}>
                    <button className={styles.btn} onClick={() => navigate(-1)}>Cancel</button>
                    <button className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> {saving ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </header>

            <div className={styles.sections}>

                <CollapsibleSection icon={<FiHash />} title={`${nIndex}. Entry Mode`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={styles.label}>Index</label>
                            <input className={`${styles.input} ${styles.indexValue}`} value={nextIndex} placeholder="--" disabled />
                            <p className={styles.hint}>Next available index, assigned on save</p>
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Date Started</label>
                            <input type="date" className={styles.input} value={projectStartDate} onChange={e => setProjectStartDate(e.target.value)} />
                            <p className={styles.hint}>Auto-filled with today. Edit if started earlier.</p>
                        </div>
                    </div>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${styles.required}`}>Type</label>
                        <div className={styles.typeGroup}>
                            {PROJECT_TYPES.map(pt => (
                                <button
                                    key={pt.value}
                                    type="button"
                                    className={`${styles.typeBtn} ${projectType === pt.value ? styles.typeBtnActive : ''}`}
                                    onClick={() => handleProjectTypeChange(pt.value)}
                                >
                                    {pt.icon}
                                    <span>{pt.label}</span>
                                </button>
                            ))}
                        </div>
                        <p className={styles.typeHint}>{PROJECT_TYPES.find(pt => pt.value === projectType)?.hint}</p>
                    </div>
                </CollapsibleSection>

                <CollapsibleSection icon={<FiUsers />} title={`${nOwners}. Owners`}>
                    {owners.map((o, idx) => (
                        <div key={idx} className={styles.ownerRow}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>NIN</label>
                                <input className={styles.input} value={o.nationalId} onChange={e => updateOwner(idx, 'nationalId', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Full Name</label>
                                <input className={styles.input} value={o.fullName} onChange={e => updateOwner(idx, 'fullName', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Phone</label>
                                <input className={styles.input} value={o.phone} onChange={e => updateOwner(idx, 'phone', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Email</label>
                                <input className={styles.input} value={o.email} onChange={e => updateOwner(idx, 'email', e.target.value)} />
                            </div>
                            <button
                                type="button"
                                className={`${styles.btn} ${styles.deleteBtn}`}
                                onClick={() => setOwners(p => p.filter((_, i) => i !== idx))}
                                disabled={owners.length === 1}
                                aria-label="Remove owner"
                            >
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                    <button type="button" className={styles.btn} onClick={() => setOwners(p => [...p, EMPTY_OWNER()])}>
                        <FiPlus /> Add joint owner
                    </button>
                </CollapsibleSection>

                {isTitleSectionVisible && (
                    <CollapsibleSection icon={<FiFileText />} title={`${nTitle}. Title & Plot`} accent>
                        <div className={styles.grid3}>
                            <div className={styles.field}>
                                <label className={styles.label}>Title ID</label>
                                <input className={styles.input} value={titleId} onChange={e => setTitleId(e.target.value)} />
                            </div>
                            <HardwareSelect
                                label="Tenure"
                                required
                                options={TENURE_OPTIONS}
                                value={tenure}
                                onChange={setTenure}
                            />
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Plot Number</label>
                                <input className={styles.input} value={plotNumber} onChange={e => setPlotNumber(e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Block</label>
                                <input className={styles.input} value={blockRoad} onChange={e => setBlockRoad(e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Title Date</label>
                                <input type="date" className={styles.input} value={titleIssueDate} onChange={e => setTitleIssueDate(e.target.value)} />
                                <p className={styles.hint}>Leave blank if not yet received.</p>
                            </div>
                        </div>
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiMap />} title={`${nLocation}. Location`}>
                    <div className={styles.grid3}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>District</label>
                            <input className={styles.input} value={district} onChange={e => setDistrict(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>County</label>
                            <input className={styles.input} value={county} onChange={e => setCounty(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Sub-county</label>
                            <input className={styles.input} value={subCounty} onChange={e => setSubCounty(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Parish</label>
                            <input className={styles.input} value={parish} onChange={e => setParish(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Village</label>
                            <input className={styles.input} value={village} onChange={e => setVillage(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${isTitleSectionVisible ? styles.required : ''}`}>Area{!isTitleSectionVisible ? ' (Optional)' : ''}</label>
                            <input className={styles.input} value={area} onChange={e => setArea(e.target.value)} />
                        </div>
                    </div>
                </CollapsibleSection>

                <CollapsibleSection
                    icon={<FiCheckSquare />}
                    title={`${nStages}. Stages`}
                    right={
                        <div style={{ display: 'flex', gap: 'var(--gap-md)', flexWrap: 'wrap', alignItems: 'center' }}>
                            {presets.length > 0 && (
                                <HardwareSelect
                                    compact
                                    placeholder="Apply preset..."
                                    value=""
                                    options={presets.map(p => p.name)}
                                    onChange={applyPreset}
                                />
                            )}
                            <button type="button" className={styles.legacyBtn} onClick={() => setShowSavePreset(s => !s)}>
                                <FiBookmark /> Save Preset
                            </button>
                            <button type="button" className={styles.legacyBtn} onClick={() => setAddingStage(s => !s)}>
                                <FiPlus /> Add Stage
                            </button>
                        </div>
                    }
                >
                    {showSavePreset && (
                        <div className={styles.inlineAddRow}>
                            <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                            <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                            <button type="button" className={styles.btn} onClick={() => { setShowSavePreset(false); setPresetName(''); }}><FiX /></button>
                        </div>
                    )}
                    {addingStage && (
                        <div className={styles.inlineAddRow}>
                            <input className={styles.input} placeholder="New stage name" value={newStageName} onChange={e => setNewStageName(e.target.value)} />
                            <input className={styles.input} type="number" placeholder="Default cost" value={newStageCost} onChange={e => setNewStageCost(e.target.value)} style={{ maxWidth: 160 }} />
                            <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleAddStage}>Add</button>
                            <button type="button" className={styles.btn} onClick={() => { setAddingStage(false); setNewStageName(''); setNewStageCost(''); }}><FiX /></button>
                        </div>
                    )}
                    <div className={styles.stageList}>
                        {sortedTemplates.map(t => {
                            const locked = t.id === firstStageId || t.id === lastStageId;
                            return (
                                <label key={t.id} className={`${styles.stageItem} ${checkedStages[t.id] ? styles.checked : ''} ${locked ? styles.stageLocked : ''}`}>
                                    <input type="checkbox" className={styles.checkbox} checked={!!checkedStages[t.id]}
                                        disabled={locked}
                                        onChange={() => toggleStage(t.id)} />
                                    <span className={styles.stageName}>{t.stageName}</span>
                                    {locked && <span className={styles.lockedTag}><FiLock size={11} /> Required</span>}
                                </label>
                            );
                        })}
                    </div>
                    {presets.length > 0 && (
                        <div className={styles.presetList}>
                            {presets.map(p => (
                                <span key={p.name} className={styles.presetChip}>
                                    {p.name}
                                    <button
                                        type="button"
                                        className={styles.presetChipRemove}
                                        onClick={() => deletePreset(p.name)}
                                        aria-label={`Delete preset ${p.name}`}
                                    >
                                        <FiX size={12} />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                </CollapsibleSection>

                <CollapsibleSection icon={<FiDollarSign />} title={`${nFinancials}. Financials`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={styles.label}>Total Cost</label>
                            <input type="number" className={styles.input} value={totalCost} onChange={e => setTotalCost(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Initial Payment</label>
                            <input type="number" className={styles.input} value={initialPayment} onChange={e => setInitialPayment(e.target.value)} />
                        </div>
                    </div>
                    {isLegacy && (
                        <>
                            <h3 className={styles.subheading}><FiArchive size={13} /> Storage Fees</h3>
                            <div className={styles.grid2}>
                                <div className={styles.field}>
                                    <label className={styles.label}>Initial Storage Fee</label>
                                    <input type="number" className={styles.input} value={initialStorageFee} onChange={e => setInitialStorageFee(e.target.value)} />
                                </div>
                                <div className={styles.field}>
                                    <label className={styles.label}>Monthly Storage Fee</label>
                                    <input type="number" className={styles.input} value={monthlyStorageFee} onChange={e => setMonthlyStorageFee(e.target.value)} placeholder="System default" />
                                </div>
                            </div>
                        </>
                    )}
                    <div className={styles.financialsSummary}>
                        <div className={styles.finRow}><span>Total Cost</span><span>{Number(totalCost) || 0}</span></div>
                        <div className={styles.finRow}><span>Initial Payment</span><span>{Number(initialPayment) || 0}</span></div>
                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}
                        <div className={`${styles.finRow} ${styles.total}`}><span>Amount Owed</span><span>{amountOwed}</span></div>
                    </div>
                </CollapsibleSection>

                <div className={styles.splitRow}>
                    <CollapsibleSection icon={<FiUploadCloud />} title={`${nDocuments}. Documents`}>
                        <div
                            className={styles.dropzone}
                            onClick={triggerFileInput}
                            role="button"
                            tabIndex={0}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); } }}
                        >
                            <FiUploadCloud size={24} />
                            <p>Click to upload</p>
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            onChange={handleFileUpload}
                            style={{ display: 'none' }}
                        />
                        <div className={styles.fileList}>
                            {fileQueue.map((f, i) => (
                                <div key={i} className={styles.fileItem}>
                                    <span>{f.name}</span>
                                    <button
                                        type="button"
                                        className={`${styles.btn} ${styles.deleteBtn}`}
                                        onClick={() => setFileQueue(p => p.filter((_, idx) => idx !== i))}
                                        aria-label="Remove file"
                                    >
                                        <FiTrash2 />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </CollapsibleSection>

                    <CollapsibleSection icon={<FiEdit3 />} title={`${nNotes}. Notes`}>
                        <div className={styles.field}>
                            <textarea className={styles.textarea} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Shared project notes..." />
                        </div>
                    </CollapsibleSection>
                </div>

            </div>

            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles[t.type] || ''}`}>{t.msg}</div>
            ))}
        </div>
    );
}
""")

# =====================================================================
# Report
# =====================================================================
print(f"\n=== fix.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)} file(s)")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

# =====================================================================
# Auto-commit + push
# =====================================================================
if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)

        commit_msg = """style: refine intake page — animated separator, smaller fields, red deletes

- Corner brackets only render on expanded body (not collapsed header)
- Orange separator line animates in/out with section expand/collapse
- Corner brackets now curved (6px radius) instead of sharp
- Reduced field sizes: smaller font, padding, explicit 42px height
- Tighter spacing: reduced gap values throughout
- Delete buttons (owners, files) turn red on hover
- File upload fixed: uses ref + onClick instead of label wrapping
- Removed border decorations from header section"""

        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed all changes")

        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed to remote")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit code {e.returncode})")
        if e.output:
            print(f"    {e.output.decode('utf-8', errors='replace').strip()}")
    except FileNotFoundError:
        print("\n  Git: git not found in PATH")

print()