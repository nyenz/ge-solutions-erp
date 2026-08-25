#!/usr/bin/env python3
"""
fix.py — Ledger-consistency pass for the New Project page.
Updates 4 frontend files, then auto-commits + pushes.
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
# 1) CollapsibleSection.jsx — inject CornerDecor like HardwarePanel
# =====================================================================
write("erp-frontend/src/components/ui/CollapsibleSection.jsx", r"""// PATH: erp-frontend/src/components/ui/CollapsibleSection.jsx
import React, { useState } from 'react';
import { FiChevronDown } from 'react-icons/fi';
import CornerDecor from './CornerDecor';
import styles from './CollapsibleSection.module.css';

/**
 * Generic expand/contract card - dark hardware panel treatment.
 * Injects CornerDecor brackets/pins exactly like HardwarePanel does,
 * so every section matches the Ledger table shell.
 */
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
            <CornerDecor />
            <button
                type="button"
                className={styles.header}
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
            {open && <div className={styles.body}>{children}</div>}
        </section>
    );
};

export default CollapsibleSection;
""")

# =====================================================================
# 2) CollapsibleSection.module.css — Ledger table-head band + separator
# =====================================================================
write("erp-frontend/src/components/ui/CollapsibleSection.module.css", r"""/* PATH: erp-frontend/src/components/ui/CollapsibleSection.module.css */
/* Dark hardware panel - mirrors HardwarePanel.dark shell and the
   Ledger table head (#162a2c band + 3px orange separator). */
.section {
    --orange: #EE8C3A;
    --orange-dim: rgba(238, 140, 58, 0.18);
    position: relative; /* anchor for CornerDecor brackets/pins */
    background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);
    border: 1px solid rgba(238, 140, 58, 0.2);
    border-radius: 12px;
    overflow: visible;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.section:hover {
    border-color: var(--orange);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}
.section.accent { border: 2px solid var(--orange); }

/* Header band - same shade + orange separator as the Ledger table head */
.header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(7px, 1.1vw, 13px);
    padding: clamp(11px, 1.5vw, 18px) clamp(12px, 1.8vw, 20px);
    background: #162a2c;
    border: none;
    border-bottom: 3px solid var(--orange);
    box-shadow: 0 3px 0 rgba(238, 140, 58, 0.15);
    cursor: pointer;
    text-align: left;
    font: inherit;
    color: inherit;
}
.header:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }

.headerLeft {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
    color: var(--orange);
    font-size: clamp(14px, 1.6vw, 18px);
    filter: drop-shadow(0 0 5px rgba(238, 140, 58, 0.4));
}

.title {
    font-family: 'Cinzel', serif;
    font-size: clamp(12px, 1.5vw, 15px);
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
.header:hover .title { color: #fff; } /* same as Ledger sortable hover */

.headerRight {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1.2vw, 14px);
    flex-shrink: 0;
}

.chevron {
    color: rgba(255, 255, 255, 0.4);
    font-size: 16px;
    transition: transform 0.2s ease, color 0.2s ease;
    flex-shrink: 0;
}
.chevronOpen { transform: rotate(180deg); color: var(--orange); }

.body {
    padding: 0 clamp(14px, 1.8vw, 20px) clamp(14px, 1.8vw, 20px);
    padding-top: clamp(14px, 1.8vw, 20px);
    display: flex;
    flex-direction: column;
    gap: clamp(10px, 1.5vw, 18px);
    animation: expand 0.18s ease-out;
}

@keyframes expand {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
    .header { padding: 12px 14px; }
    .body { padding: 12px 14px 14px; }
}
""")

# =====================================================================
# 3) IntakePage.module.css — full Ledger consistency pass
# =====================================================================
write("erp-frontend/src/pages/Intake/IntakePage.module.css", r"""/* PATH: erp-frontend/src/pages/Intake/IntakePage.module.css
   Ledger-consistency pass - dull labels (50% white, 900, 2px tracking),
   Ledger hover language (white 4% + orange left border), filter-style
   segmented buttons, pageBtn-style secondary buttons, 3px orange focus
   ring, 1400px container, rgba(0,0,0,0.15) inner wells. */
:root {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #213E40;
    --navy-deep:     #1a2e30;
    --red:           #ef4444;
    --green:         #10b981;

    --gap-xl:    clamp(14px, 2vw, 22px);
    --gap-lg:    clamp(10px, 1.5vw, 18px);
    --gap-md:    clamp(7px,  1.1vw, 13px);
    --radius:    12px;
    --radius-sm: 6px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(8px,  0.85vw, 10px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-td:     clamp(10px, 1.05vw, 12px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-input:  clamp(11px, 1.1vw, 13px);
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);
}

.container {
    max-width: 1400px; /* same as Ledger */
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

/* -- PAGE HEADER - identical glass treatment to the Ledger page -- */
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

/* -- BUTTONS - pageBtn language: transparent, white border, white hover -- */
.btn {
    font-family: 'Inter', sans-serif;
    font-size: var(--fs-btn);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: clamp(7px, 1vw, 10px) clamp(12px, 1.6vw, 18px);
    border-radius: var(--radius-sm);
    border: 1.5px solid rgba(255, 255, 255, 0.1);
    background: transparent;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
}
.btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.07); border-color: rgba(255, 255, 255, 0.22); color: #fff; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.btn.primary { background: var(--orange); color: #fff; border-color: var(--orange); }
.btn.primary:hover { background: #d97a2b; border-color: #d97a2b; color: #fff; }
.btn:disabled { opacity: 0.18; cursor: not-allowed; }

/* filterBtn language for toolbar buttons */
.legacyBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(12px, 1.5vw, 18px);
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
    gap: 6px;
    white-space: nowrap;
}
.legacyBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }

/* -- FIELDS -- */
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--gap-lg); }
.grid3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--gap-lg); }

.field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }

/* DULL LABELS - Ledger muted metrics: 50% white, 900, 2px tracking */
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

/* Inputs - white hardware inputs, Ledger 3px focus ring */
.input, .textarea {
    font-family: 'Inter', sans-serif;
    font-size: var(--fs-input);
    font-weight: 600;
    padding: clamp(8px, 1vw, 12px) clamp(10px, 1.4vw, 15px);
    border: 2px solid rgba(238, 140, 58, 0.3);
    border-radius: var(--radius-sm);
    background: #ffffff;
    color: var(--navy);
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
}
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
.textarea { min-height: 110px; resize: vertical; }

/* -- TYPE TOGGLE - filterBtn / activeFilter language -- */
.typeGroup { display: flex; gap: clamp(6px, 1vw, 12px); flex-wrap: wrap; }
.typeBtn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(12px, 1.5vw, 18px);
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

/* -- INNER WELLS - Ledger table-shell shade -- */
.ownerRow {
    display: grid;
    grid-template-columns: 1.2fr 2fr 1fr 1.5fr auto;
    gap: var(--gap-md);
    align-items: end;
    padding: var(--gap-md);
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
    gap: 6px;
    margin: 4px 0 0 0;
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
.inlineAddRow .input { width: auto; flex: 1 1 200px; }

/* -- STAGES - Ledger row hover language -- */
.stageList { display: flex; flex-direction: column; gap: var(--gap-md); }
.stageItem {
    display: flex;
    align-items: center;
    gap: var(--gap-md);
    padding: var(--gap-md);
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
.checkbox { width: 18px; height: 18px; accent-color: var(--orange); cursor: pointer; flex-shrink: 0; }
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
    gap: 6px;
    background: var(--orange-dim);
    color: var(--orange);
    border: 1px solid var(--orange-border);
    border-radius: 999px;
    padding: 4px 10px;
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
    padding: var(--gap-xl);
    text-align: center;
    color: rgba(255, 255, 255, 0.45);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
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
    padding: var(--gap-md);
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
# 4) HardwareSelect.module.css — dull labels + fixed dropdown sizing
# =====================================================================
write("erp-frontend/src/components/common/HardwareSelect.module.css", r""".fieldWrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    position: relative;
    margin-bottom: 15px;
}

.openWrapper {
    z-index: 9999 !important;
    overflow: visible !important;
    position: relative !important;
}

/* Dull label - same metrics as every other label on dark panels */
.label {
    color: rgba(255, 255, 255, 0.5) !important;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 2px;
}
.requiredMark { color: #ef4444; margin-left: 4px; }

.placeholder { color: rgba(26, 46, 48, 0.45); }

.selectBox {
    background: #ffffff;
    border-radius: var(--input-radius, 8px);
    border: 2px solid rgba(238, 140, 58, 0.3);
    padding: 0 clamp(10px, 1.4vw, 18px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
    height: var(--input-height, 44px);
    position: relative;
    z-index: 1;
}
.selectBox:hover, .active {
    border-color: var(--orange);
    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.18);
}

.currentValue {
    color: var(--navy);
    font-weight: 700;
    font-size: var(--input-font, 14px);
}

.icon {
    color: var(--orange);
    transition: 0.3s;
    flex-shrink: 0;
}
.active .icon { transform: rotate(180deg); }

/* ABSOLUTE (not fixed) so the panel sizes to its field, not the viewport */
.dropdown {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    min-width: 100%;
    width: max-content;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 8px 20px rgba(0,0,0,0.3);
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
    z-index: 99999 !important;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
}

.option {
    padding: 14px 20px;
    color: var(--navy);
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.5px;
    background: #ffffff;
    border-bottom: 1px solid #f1f5f9;
    cursor: pointer;
    transition: 0.2s;
}
.option:last-child { border-bottom: none; }
.option:hover {
    background: var(--orange);
    color: white;
}
.selected {
    background: var(--orange);
    color: white;
}

.compactWrapper { margin-bottom: 0; width: auto; }
.compactBox { height: clamp(34px, 4vw, 40px); min-width: clamp(150px, 15vw, 200px); }

@media (max-width: 480px) {
    .selectBox { height: var(--input-height, 40px); font-size: 12px; }
    .option { padding: 12px 14px; font-size: 13px; }
}

.dropdown {
    max-height: 250px;
    overflow-y: auto;
}
.dropdown::-webkit-scrollbar { width: 4px; display: none !important; }
.dropdown::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }
@media (max-width: 480px) {
    .dropdown { max-height: 200px; }
    .option { padding: 10px 14px; font-size: 12px; }
}
.dropdown {
    -ms-overflow-style: none !important;
    scrollbar-width: none !important;
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

        commit_msg = """style: unify New Project page with Ledger reference design

- Section headers: #162a2c band + 3px orange separator (Ledger table head)
- CornerDecor brackets + pins on every section (same as HardwarePanel)
- Duller labels: 50% white, 900 weight, 2px letter-spacing (Ledger metrics)
- Ledger hover language: white 4% + orange left border on rows/items
- Type toggle now uses filterBtn/activeFilter styling (solid orange active)
- Secondary buttons use pageBtn styling; focus = 3px orange ring
- HardwareSelect dropdown absolute-positioned (fixes viewport-wide panel),
  selected row solid orange like the reference
- Container width 1400px to match Ledger"""

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