#!/usr/bin/env python3
"""
fix.py — Intake pass 5: validation, duplicate-saves, unsaved-changes guard,
auto-collapse sidebar, insert-below stage, visible top arrow, dates on notes.
Run: py fix.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WROTE, FAILED = [], []

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(content, encoding="utf-8"); WROTE.append(rel)
    except Exception as e:
        FAILED.append((rel, str(e)))

# =====================================================================
# 1) CollapsibleSection.jsx — accent border only while section is FOCUSED
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
    const [active, setActive] = useState(false); // user is working inside
    const isControlled = controlledOpen !== undefined;
    const open = isControlled ? controlledOpen : internalOpen;

    const toggle = () => {
        if (isControlled) onToggle?.(!open);
        else setInternalOpen(o => !o);
    };

    const handleBlur = (e) => {
        // deactivate only when focus truly leaves the section
        if (!e.currentTarget.contains(e.relatedTarget)) setActive(false);
    };

    // orange "active" border only while the user is actually inside
    const showAccent = accent && active;

    return (
        <section
            className={`${styles.section} ${showAccent ? styles.accent : ''} ${className}`}
            onFocusCapture={() => setActive(true)}
            onBlurCapture={handleBlur}
        >
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
                    <CornerDecor hideTop />
                    {children}
                </div>
            )}
        </section>
    );
};

export default CollapsibleSection;
""")

# =====================================================================
# 2) HardwareSelect.module.css — sizes follow the scoped input vars
# =====================================================================
write("erp-frontend/src/components/common/HardwareSelect.module.css", r""".fieldWrapper {
    display: flex;
    flex-direction: column;
    gap: 5px;
    width: 100%;
    position: relative;
    margin-bottom: 0;
}

.openWrapper {
    z-index: 9999 !important;
    overflow: visible !important;
    position: relative !important;
}

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
    border-radius: var(--input-radius, 6px);
    border: 1.5px solid rgba(238, 140, 58, 0.3);
    padding: 0 var(--input-px, clamp(9px, 1.2vw, 13px));
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
    height: var(--input-height, clamp(34px, 4.3vw, 40px));
    position: relative;
    z-index: 1;
}
.selectBox:hover, .active {
    border-color: var(--orange);
    box-shadow: 0 0 0 2px rgba(238, 140, 58, 0.15);
}

.currentValue {
    color: var(--navy);
    font-weight: 700;
    font-size: var(--input-font, clamp(11px, 1.05vw, 13px));
    letter-spacing: 0.5px;
}

.icon {
    color: var(--orange);
    transition: 0.3s;
    flex-shrink: 0;
    font-size: 14px;
}
.active .icon { transform: rotate(180deg); }

.dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    min-width: 100%;
    width: max-content;
    background: #ffffff;
    border: 1.5px solid var(--orange);
    border-radius: 6px;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5), 0 6px 16px rgba(0,0,0,0.3);
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
    z-index: 99999 !important;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}

.option {
    padding: clamp(8px, 1vw, 11px) clamp(12px, 1.4vw, 16px);
    color: var(--navy);
    font-weight: 700;
    font-size: clamp(11px, 1.05vw, 13px);
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

.compactWrapper { width: auto; }
.compactBox { height: clamp(30px, 3.6vw, 36px); min-width: clamp(140px, 14vw, 190px); }

@media (max-width: 480px) {
    .selectBox { height: 38px; font-size: 12px; }
    .option { padding: 9px 12px; font-size: 12px; }
}

.dropdown {
    max-height: 220px;
    overflow-y: auto;
}
.dropdown::-webkit-scrollbar { width: 4px; display: none !important; }
@media (max-width: 480px) {
    .dropdown { max-height: 180px; }
}
.dropdown {
    -ms-overflow-style: none !important;
    scrollbar-width: none !important;
}
""")

# =====================================================================
# 3) IntakePage.module.css — visible top arrow, bigger fields, modal, xBtn
# =====================================================================
write("erp-frontend/src/pages/Intake/IntakePage.module.css", r"""/* PATH: erp-frontend/src/pages/Intake/IntakePage.module.css
   Pass 5 - slightly bigger fields, visible borderless top arrow,
   orange app-standard X buttons, unsaved-changes modal. */
:root {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #213E40;
    --navy-deep:     #1a2e30;
    --red:           #ef4444;
    --green:         #10b981;

    --gap-xl:    clamp(10px, 1.6vw, 18px);
    --gap-lg:    clamp(7px,  1.1vw, 14px);
    --gap-md:    clamp(5px,  0.9vw, 10px);
    --radius:    10px;
    --radius-sm: 6px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(8px,  0.85vw, 10px);
    --fs-value:  clamp(10px, 1.05vw, 12px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(8px,  0.85vw, 10px);
}

/* scoped global input vars - a touch bigger than pass 4 */
.container {
    --input-height: clamp(34px, 4.3vw, 40px);
    --input-font:   clamp(11px, 1.05vw, 13px);
    --input-px:     clamp(9px, 1.2vw, 13px);
    --input-radius: 6px;

    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    padding: clamp(12px, 2vh, 22px) clamp(12px, 2vw, 24px) 0;
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

.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(8px, 1.2vw, 14px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(8px, 1.2vw, 14px) clamp(14px, 1.8vw, 22px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
    flex-shrink: 0;
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }

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
    display: inline-flex;
    align-items: center;
    gap: 5px;
    text-decoration: none;
}
.btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.07); border-color: rgba(255, 255, 255, 0.22); color: #fff; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.btn.primary { background: var(--orange); color: #fff; border-color: var(--orange); }
.btn.primary:hover { background: #d97a2b; border-color: #d97a2b; color: #fff; }
.btn:disabled { opacity: 0.18; cursor: not-allowed; }
.btn.small { padding: clamp(4px, 0.7vw, 7px) clamp(8px, 1.1vw, 12px); }

.btn.deleteBtn { border-color: rgba(239, 68, 68, 0.3); color: rgba(239, 68, 68, 0.7); }
.btn.deleteBtn:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.15);
    border-color: var(--red);
    color: var(--red);
}

/* app-standard orange X (matches search clear etc.) */
.xBtn {
    background: transparent;
    border: none;
    color: var(--orange);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    padding: 5px;
    border-radius: 4px;
    transition: background 0.2s;
}
.xBtn:hover { background: var(--orange-dim); }

/* insert-below button on stage rows */
.plusBtn {
    background: transparent;
    border: 1px solid rgba(238, 140, 58, 0.3);
    color: var(--orange);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    padding: 4px 6px;
    border-radius: 4px;
    transition: all 0.2s;
}
.plusBtn:hover { background: var(--orange-dim); border-color: var(--orange); }

.addBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(6px, 0.9vw, 9px) clamp(10px, 1.4vw, 16px);
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-size: var(--fs-btn);
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    align-self: flex-start;
}
.addBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }

.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--gap-lg); }
.grid3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: var(--gap-lg); }

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

.input, .textarea {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    border: 1.5px solid rgba(238, 140, 58, 0.3);
    background: #ffffff;
    color: var(--navy);
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.textarea { min-height: 110px; resize: vertical; line-height: 1.5; }
.input:hover, .textarea:hover { border-color: var(--orange); }
.input:focus, .textarea:focus {
    outline: none;
    border-color: var(--orange);
    box-shadow: 0 0 0 2px rgba(238, 140, 58, 0.15);
}
.input:disabled { color: rgba(33, 62, 64, 0.5); cursor: not-allowed; }
.input.indexValue {
    font-family: 'Space Mono', monospace;
    font-weight: 900;
    letter-spacing: 1px;
    color: var(--orange);
}
.input.indexValue:disabled { color: var(--orange); opacity: 1; }

.typeGroup { display: flex; gap: clamp(5px, 0.9vw, 10px); flex-wrap: wrap; }
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
    font-size: var(--fs-btn);
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
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.4);
}
.typeHint { font-size: var(--fs-meta); color: rgba(255, 255, 255, 0.35); margin: 2px 0 0 0; letter-spacing: 0.5px; }

.ownerRow {
    display: grid;
    grid-template-columns: 1.2fr 2fr 1fr 1.5fr auto auto;
    gap: var(--gap-md);
    align-items: end;
    padding: clamp(6px, 0.9vw, 9px);
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-sm);
}

.subheading {
    font-family: 'Cinzel', serif;
    font-size: clamp(11px, 1.3vw, 13px);
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
.inlineAddRow .input { width: auto; flex: 1 1 160px; }
.insertCtx { font-size: var(--fs-meta); color: var(--orange); font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }

.stageList { display: flex; flex-direction: column; gap: var(--gap-md); }
.stageItem {
    display: flex;
    align-items: center;
    gap: var(--gap-md);
    padding: clamp(6px, 0.9vw, 9px);
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background 0.18s;
}
.stageItem:hover { background: rgba(255, 255, 255, 0.04); }
.stageItem.checked { background: rgba(238, 140, 58, 0.07); }
.checkbox { width: 15px; height: 15px; accent-color: var(--orange); cursor: pointer; flex-shrink: 0; }
.stageName { font-weight: 700; color: #fff; font-size: var(--fs-value); letter-spacing: 0.5px; }
.stageActions { margin-left: auto; display: flex; gap: var(--gap-md); align-items: center; }

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

.financialsSummary {
    background: rgba(0, 0, 0, 0.15);
    padding: var(--gap-lg);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
}
.finRow { display: flex; justify-content: space-between; font-weight: 700; color: rgba(255, 255, 255, 0.85); font-size: var(--fs-value); letter-spacing: 0.5px; }
.finRow.total { color: var(--orange); font-size: clamp(13px, 1.4vw, 17px); border-top: 1px solid rgba(238, 140, 58, 0.25); padding-top: var(--gap-md); }

.dropzone {
    border: 2px dashed rgba(238, 140, 58, 0.4);
    border-radius: var(--radius);
    padding: clamp(12px, 1.6vw, 18px);
    text-align: center;
    color: rgba(255, 255, 255, 0.55);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}
.dropzone:hover { background: var(--orange-dim); border-color: var(--orange); color: var(--orange); }
.dropzoneIcon {
    width: clamp(34px, 4vw, 44px);
    height: clamp(34px, 4vw, 44px);
    border-radius: 50%;
    background: rgba(238, 140, 58, 0.12);
    border: 1px solid var(--orange-border);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--orange);
    margin-bottom: 2px;
}
.dropzoneTitle { font-weight: 800; font-size: var(--fs-value); letter-spacing: 1px; text-transform: uppercase; }
.dropzoneTitle .reqMark { color: var(--red); margin-left: 3px; }
.dropzoneSub { font-size: var(--fs-meta); color: rgba(255, 255, 255, 0.35); font-weight: 700; letter-spacing: 0.5px; }

.fileList { display: flex; flex-direction: column; gap: var(--gap-md); }
.fileItem {
    display: flex; justify-content: space-between; align-items: center; gap: var(--gap-md);
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #fff;
    font-size: var(--fs-value);
    font-weight: 600;
    padding: clamp(6px, 0.9vw, 9px) clamp(8px, 1.1vw, 12px);
    border-radius: var(--radius-sm);
}
.fileMeta { display: flex; align-items: center; gap: 8px; min-width: 0; }
.fileIcon { color: var(--orange); flex-shrink: 0; }
.fileName { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fileSize { color: rgba(255, 255, 255, 0.35); font-size: var(--fs-meta); font-weight: 700; flex-shrink: 0; }
.fileActions { display: flex; gap: var(--gap-md); flex-shrink: 0; }

.notesWrap { display: flex; flex-direction: column; gap: 4px; }
.noteDateChip {
    align-self: flex-start;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.6);
    font-size: var(--fs-meta);
    font-weight: 800;
    letter-spacing: 1px;
    padding: 3px 8px;
    border-radius: 4px;
}

/* -- BOTTOM BAR: plain row; visible borderless single-arrow top button -- */
.bottomBar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--gap-md);
    padding: var(--gap-md) 0;
    margin-bottom: clamp(12px, 2vh, 22px);
}
.bottomBarRight { display: flex; gap: var(--gap-md); align-items: center; }

.topBtn {
    background: transparent;
    border: none;
    color: var(--orange);
    font-size: 20px;
    padding: 4px 8px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    filter: drop-shadow(0 0 4px rgba(238, 140, 58, 0.5));
    transition: transform 0.2s ease;
}
.topBtn:hover { transform: translateY(-2px); }

/* -- UNSAVED CHANGES MODAL -- */
.modalOverlay {
    position: fixed;
    inset: 0;
    background: rgba(10, 20, 22, 0.72);
    backdrop-filter: blur(4px);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
}
.modalCard {
    width: min(480px, 90vw);
    background: linear-gradient(135deg, #3a5a5c 0%, #213E40 100%);
    border: 1px solid var(--orange-border);
    border-radius: 12px;
    padding: clamp(16px, 2vw, 24px);
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
.modalTitle {
    font-family: 'Cinzel', serif;
    color: var(--orange);
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: clamp(12px, 1.4vw, 15px);
    margin: 0;
}
.modalText { color: rgba(255, 255, 255, 0.75); font-size: var(--fs-value); font-weight: 600; margin: 0; }
.modalBtns { display: flex; gap: var(--gap-md); justify-content: flex-end; flex-wrap: wrap; }

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
    .bottomBar { flex-wrap: wrap; }
}
""")

# =====================================================================
# 4) IntakePage.jsx — all pass-5 behavior
# =====================================================================
write("erp-frontend/src/pages/Intake/IntakePage.jsx", r"""// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useBlocker } from 'react-router-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiEdit3, FiBookmark, FiX, FiCopy, FiArrowUp, FiFile, FiEye, FiRefreshCw,
    FiCalendar
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

const DEFAULT_STAGES = [
    'Field Work',
    'Deed Plan',
    'LC Inspection',
    'District Land Board Approval',
    'Tax Assessment and Stamp Duty',
    'Registration and Title Issuance',
];

const todayISO = () => new Date().toISOString().slice(0, 10);
const todayDMY = () => {
    const d = new Date();
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
};
const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';

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
    const topRef = useRef(null);
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
    const [insertAfterId, setInsertAfterId] = useState('');
    const [restoring, setRestoring] = useState(false);
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

    const [dirty, setDirty] = useState(false);
    const dirtyRef = useRef(false);
    const markDirty = useCallback(() => { dirtyRef.current = true; setDirty(true); }, []);

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

    // STANDARD: sidebar auto-collapses once the user starts working on the form
    const collapsedOnce = useRef(false);
    useEffect(() => {
        const el = topRef.current;
        if (!el) return;
        const handler = () => {
            if (collapsedOnce.current) return;
            collapsedOnce.current = true;
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) {
                toggle.click();
            }
        };
        el.addEventListener('focusin', handler);
        el.addEventListener('input', handler);
        el.addEventListener('click', handler);
        return () => {
            el.removeEventListener('focusin', handler);
            el.removeEventListener('input', handler);
            el.removeEventListener('click', handler);
        };
    }, []);

    // STANDARD: warn before closing the tab with unsaved work
    useEffect(() => {
        const h = (e) => {
            if (dirtyRef.current) { e.preventDefault(); e.returnValue = ''; }
        };
        window.addEventListener('beforeunload', h);
        return () => window.removeEventListener('beforeunload', h);
    }, []);

    // Warn before navigating away inside the app with unsaved work
    const blocker = useBlocker(dirty && !saving);

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
            return next;
        });
    }, [sortedTemplates.length, firstStageId]);

    const finalStageChecked = lastStageId ? !!checkedStages[lastStageId] : false;
    const isLegacy = projectType === 'LEGACY_TITLE';
    const titleAtIntake = projectType === 'NEW_TITLE';
    const isTitleType = isLegacy || titleAtIntake;
    const isTitleSectionVisible = isTitleType || finalStageChecked;
    const showStages = !isTitleType;

    const allStagesChecked = () => {
        const all = {};
        sortedTemplates.forEach(t => { all[t.id] = true; });
        return all;
    };
    const defaultStages = () => {
        const d = {};
        if (firstStageId) d[firstStageId] = true;
        return d;
    };

    const handleProjectTypeChange = (value) => {
        setProjectType(value);
        markDirty();
        if (value === 'LEGACY_TITLE' || value === 'NEW_TITLE') {
            setCheckedStages(allStagesChecked());
        } else {
            setCheckedStages(defaultStages());
        }
    };

    const toggleStage = (id) => {
        markDirty();
        setCheckedStages(p => ({ ...p, [id]: !p[id] }));
    };

    // one parallel wave of order updates = fast, no lag
    const renumber = (ordered) => Promise.all(
        ordered.map((t, i) =>
            t?.id ? stageTemplateService.updateTemplateStage(t.id, t.stageName, t.defaultCost || 0, i + 1) : null
        )
    );

    const openInsertBelow = (stageId) => {
        setInsertAfterId(stageId);
        setAddingStage(true);
    };

    const handleAddStage = async () => {
        if (!newStageName.trim()) { toast('Enter a stage name first.', 'error'); return; }
        try {
            let k = sortedTemplates.length - 1; // default: just before last
            const idx = sortedTemplates.findIndex(t => t.id === insertAfterId);
            if (idx >= 0) k = idx + 1; // appears directly under the clicked stage
            k = Math.min(Math.max(k, 1), Math.max(1, sortedTemplates.length - 1));

            const created = await stageTemplateService.addTemplateStage(newStageName.trim(), 0);
            const item = { id: created?.id, stageName: newStageName.trim(), defaultCost: 0 };
            const next = sortedTemplates.filter(t => t.id !== created?.id);
            next.splice(k, 0, item);
            await renumber(next);

            setNewStageName('');
            setInsertAfterId('');
            setAddingStage(false);
            fetchTemplates();
            if (created?.id) setCheckedStages(p => ({ ...p, [created.id]: true }));
            toast('Stage inserted.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not add stage.', 'error');
        }
    };

    const handleDeleteStage = async (id) => {
        try {
            await stageTemplateService.deleteTemplateStage(id);
            setCheckedStages(p => { const n = { ...p }; delete n[id]; return n; });
            fetchTemplates();
            toast('Stage removed.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not delete stage.', 'error');
        }
    };

    const handleRestoreDefaults = async () => {
        setRestoring(true);
        try {
            const keep = sortedTemplates.filter(t => DEFAULT_STAGES.includes(t.stageName));
            await Promise.all(
                sortedTemplates
                    .filter(t => !DEFAULT_STAGES.includes(t.stageName))
                    .map(t => stageTemplateService.deleteTemplateStage(t.id))
            );
            const have = new Set(keep.map(t => t.stageName));
            const added = [];
            for (const name of DEFAULT_STAGES) {
                if (!have.has(name)) {
                    const c = await stageTemplateService.addTemplateStage(name, 0);
                    added.push({ id: c?.id, stageName: name, defaultCost: 0 });
                }
            }
            const byName = {};
            [...keep, ...added].forEach(t => { byName[t.stageName] = t; });
            await renumber(DEFAULT_STAGES.map(name => byName[name]).filter(Boolean));
            fetchTemplates();
            toast('Default stages restored.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Restore failed.', 'error');
        } finally {
            setRestoring(false);
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
            next[t.id] = preset.stageNames.includes(t.stageName);
        });
        setCheckedStages(next);
        markDirty();
    };

    const deletePreset = (name) => {
        const next = presets.filter(p => p.name !== name);
        setPresets(next);
        savePresets(next);
    };

    const updateOwner = (idx, field, val) => {
        markDirty();
        setOwners(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o));
    };

    const handleFileUpload = (e) => {
        const items = Array.from(e.target.files).map(f => ({
            name: f.name, size: f.size, file: f, url: URL.createObjectURL(f),
        }));
        if (items.length) {
            setFileQueue(p => [...p, ...items]);
            markDirty();
        }
        e.target.value = '';
    };

    const removeFile = (i) => {
        setFileQueue(p => {
            URL.revokeObjectURL(p[i].url);
            return p.filter((_, idx) => idx !== i);
        });
    };

    const triggerFileInput = () => fileInputRef.current && fileInputRef.current.click();

    const scrollTop = () => topRef.current && topRef.current.scrollIntoView({ behavior: 'smooth' });

    // ---- validation shared by Save and Duplicate ----
    const validate = () => {
        if (!district.trim() || !county.trim()) {
            toast('District and County are required.', 'error'); return false;
        }
        for (let i = 0; i < owners.length; i++) {
            const o = owners[i];
            if (!o.nationalId.trim()) { toast(`Owner ${i + 1}: NIN is required.`, 'error'); return false; }
            if (!o.fullName.trim()) { toast(`Owner ${i + 1}: Full Name is required.`, 'error'); return false; }
            if (!o.phone.trim()) { toast(`Owner ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }
        }
        if (isTitleSectionVisible) {
            if (!titleId.trim()) { toast('Title ID is required for a title record.', 'error'); return false; }
            if (!plotNumber.trim()) { toast('Plot Number is required for a title record.', 'error'); return false; }
            if (!area.trim()) { toast('Area is required for Title details.', 'error'); return false; }
        }
        if (!(Number(totalCost) > 0)) { toast('Total Cost must be greater than 0.', 'error'); return false; }
        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) {
            toast('Initial Payment is required (0 or more).', 'error'); return false;
        }
        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }
        return true;
    };

    // ---- the actual save (no navigation) ----
    const doSave = async () => {
        if (!validate()) return false;
        setSaving(true);
        try {
            let noteText = notes.trim();
            if (noteText && !/^\[\d{2}\/\d{2}\/\d{4}\]/.test(noteText)) {
                noteText = `[${todayDMY()}] ${noteText}`; // STANDARD: notes carry their date
            }

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
                selectedStages: Object.entries(checkedStages)
                    .filter(([id, v]) => v && templates.some(t => t.id === id))
                    .map(([id]) => {
                        const t = templates.find(x => x.id === id);
                        return {
                            stageTemplateId: id,
                            stageName: t ? t.stageName : '',
                            isCustom: false,
                            isCompleted: true
                        };
                    }),
                notes: noteText ? [{ content: noteText }] : [],
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

            await landService.createAtomicEntry(payload, fileQueue.map(q => q.file));
            dirtyRef.current = false;
            setDirty(false);
            return true;
        } catch (err) {
            toast(err.response?.data?.message || 'Save failed', 'error');
            return false;
        } finally {
            setSaving(false);
        }
    };

    const handleSubmit = async () => {
        const ok = await doSave();
        if (ok) {
            toast('Project registered successfully!', 'success');
            setTimeout(() => navigate('/land/projects'), 1200);
        }
    };

    // Duplicate = SAVE the current form first (same validations/warnings),
    // then carry owners + location into a fresh form.
    const handleDuplicate = async () => {
        const ok = await doSave();
        if (!ok) return;
        toast('Saved. Form duplicated for the next plot.', 'success');
        setProjectType('NEW_FOLDER');
        setTitleId(''); setTenure('FREEHOLD'); setPlotNumber(''); setBlockRoad(''); setTitleIssueDate('');
        setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0); setMonthlyStorageFee(0);
        setNotes('');
        setFileQueue(q => { q.forEach(x => URL.revokeObjectURL(x.url)); return []; });
        setCheckedStages(defaultStages());
        setProjectStartDate(todayISO);
        landService.getNextIndex().then(idx => setNextIndex(idx || '')).catch(() => {});
        scrollTop();
    };

    const amountOwed = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));

    let n = 0;
    const nIndex = ++n;
    const nOwners = ++n;
    const nTitle = isTitleSectionVisible ? ++n : null;
    const nLocation = ++n;
    const nStages = showStages ? ++n : null;
    const nFinancials = ++n;
    const nDocuments = ++n;
    const nNotes = ++n;

    const insertAfterName = sortedTemplates.find(t => t.id === insertAfterId)?.stageName;

    return (
        <div className={styles.container} ref={topRef}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Project</h1>
                    <p className={styles.subtitle}>Intake Form</p>
                </div>
                <div className={styles.actions}>
                    <button className={styles.btn} onClick={() => navigate(-1)}>Cancel</button>
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
                            <input type="date" className={styles.input} value={projectStartDate} onChange={e => { setProjectStartDate(e.target.value); markDirty(); }} />
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
                                <label className={`${styles.label} ${styles.required}`}>Phone</label>
                                <input className={styles.input} value={o.phone} onChange={e => updateOwner(idx, 'phone', e.target.value)} placeholder="0700 000 000 / 0788 000 000" />
                                <p className={styles.hint}>Multiple numbers: separate with /</p>
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
                    <button type="button" className={styles.addBtn} onClick={() => { setOwners(p => [...p, EMPTY_OWNER()]); markDirty(); }}>
                        <FiPlus /> Add Owner
                    </button>
                </CollapsibleSection>

                {isTitleSectionVisible && (
                    <CollapsibleSection icon={<FiFileText />} title={`${nTitle}. Title Details`} accent>
                        <div className={styles.grid3}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Title ID</label>
                                <input className={styles.input} value={titleId} onChange={e => { setTitleId(e.target.value); markDirty(); }} />
                            </div>
                            <HardwareSelect
                                label="Tenure"
                                required
                                options={TENURE_OPTIONS}
                                value={tenure}
                                onChange={(v) => { setTenure(v); markDirty(); }}
                            />
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Plot Number</label>
                                <input className={styles.input} value={plotNumber} onChange={e => { setPlotNumber(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Block</label>
                                <input className={styles.input} value={blockRoad} onChange={e => { setBlockRoad(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Title Date</label>
                                <input type="date" className={styles.input} value={titleIssueDate} onChange={e => { setTitleIssueDate(e.target.value); markDirty(); }} />
                                <p className={styles.hint}>Leave blank if not yet received.</p>
                            </div>
                        </div>
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiMap />} title={`${nLocation}. Location`}>
                    <div className={styles.grid3}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>District</label>
                            <input className={styles.input} value={district} onChange={e => { setDistrict(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>County</label>
                            <input className={styles.input} value={county} onChange={e => { setCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Sub-county</label>
                            <input className={styles.input} value={subCounty} onChange={e => { setSubCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Parish</label>
                            <input className={styles.input} value={parish} onChange={e => { setParish(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Village</label>
                            <input className={styles.input} value={village} onChange={e => { setVillage(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${isTitleSectionVisible ? styles.required : ''}`}>Area{!isTitleSectionVisible ? ' (Optional)' : ''}</label>
                            <input className={styles.input} value={area} onChange={e => { setArea(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                </CollapsibleSection>

                {showStages && (
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
                                <button type="button" className={styles.addBtn} onClick={() => setShowSavePreset(s => !s)}>
                                    <FiBookmark /> Save Preset
                                </button>
                                <button type="button" className={styles.addBtn} onClick={() => { setAddingStage(s => !s); setInsertAfterId(''); }}>
                                    <FiPlus /> Add Stage
                                </button>
                                <button type="button" className={styles.addBtn} disabled={restoring} onClick={handleRestoreDefaults}>
                                    <FiRefreshCw /> Restore Defaults
                                </button>
                            </div>
                        }
                    >
                        {showSavePreset && (
                            <div className={styles.inlineAddRow}>
                                <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setShowSavePreset(false); setPresetName(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        {addingStage && (
                            <div className={styles.inlineAddRow}>
                                <span className={styles.insertCtx}>
                                    {insertAfterName ? `Insert under: ${insertAfterName}` : 'Insert before last stage'}
                                </span>
                                <input className={styles.input} placeholder="New stage name" value={newStageName} onChange={e => setNewStageName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleAddStage}>Add</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setAddingStage(false); setNewStageName(''); setInsertAfterId(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        <div className={styles.stageList}>
                            {sortedTemplates.map((t, i) => {
                                const isLast = t.id === lastStageId;
                                return (
                                    <label key={t.id} className={`${styles.stageItem} ${checkedStages[t.id] ? styles.checked : ''}`}>
                                        <input type="checkbox" className={styles.checkbox} checked={!!checkedStages[t.id]}
                                            onChange={() => toggleStage(t.id)} />
                                        <span className={styles.stageName}>{t.stageName}</span>
                                        <span className={styles.stageActions}>
                                            {!isLast && (
                                                <button
                                                    type="button"
                                                    className={styles.plusBtn}
                                                    title="Insert a stage below this one"
                                                    aria-label={`Insert stage below ${t.stageName}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(t.id); }}
                                                >
                                                    <FiPlus size={12} />
                                                </button>
                                            )}
                                            {!isLast && t.id !== firstStageId && (
                                                <button
                                                    type="button"
                                                    className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDeleteStage(t.id); }}
                                                    aria-label={`Delete stage ${t.stageName}`}
                                                >
                                                    <FiTrash2 size={12} />
                                                </button>
                                            )}
                                        </span>
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
                )}

                <CollapsibleSection icon={<FiDollarSign />} title={`${nFinancials}. Financials`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Total Cost</label>
                            <input type="number" className={styles.input} value={totalCost} onChange={e => { setTotalCost(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Initial Payment</label>
                            <input type="number" className={styles.input} value={initialPayment} onChange={e => { setInitialPayment(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                    {isLegacy && (
                        <>
                            <h3 className={styles.subheading}><FiArchive size={13} /> Storage Fees</h3>
                            <div className={styles.grid2}>
                                <div className={styles.field}>
                                    <label className={styles.label}>Initial Storage Fee</label>
                                    <input type="number" className={styles.input} value={initialStorageFee} onChange={e => { setInitialStorageFee(e.target.value); markDirty(); }} />
                                </div>
                                <div className={styles.field}>
                                    <label className={styles.label}>Monthly Storage Fee</label>
                                    <input type="number" className={styles.input} value={monthlyStorageFee} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} placeholder="System default" />
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
                            <span className={styles.dropzoneIcon}><FiUploadCloud size={18} /></span>
                            <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>
                            <span className={styles.dropzoneSub}>Required - PDF, images, any file</span>
                        </div>
                        <input ref={fileInputRef} type="file" multiple onChange={handleFileUpload} style={{ display: 'none' }} />
                        <div className={styles.fileList}>
                            {fileQueue.map((f, i) => (
                                <div key={i} className={styles.fileItem}>
                                    <span className={styles.fileMeta}>
                                        <FiFile className={styles.fileIcon} size={14} />
                                        <span className={styles.fileName}>{f.name}</span>
                                        <span className={styles.fileSize}>{fmtSize(f.size)}</span>
                                    </span>
                                    <span className={styles.fileActions}>
                                        <a className={`${styles.btn} ${styles.small}`} href={f.url} target="_blank" rel="noreferrer" aria-label={`View ${f.name}`}>
                                            <FiEye size={12} /> View
                                        </a>
                                        <button
                                            type="button"
                                            className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                            onClick={() => removeFile(i)}
                                            aria-label={`Remove ${f.name}`}
                                        >
                                            <FiTrash2 size={12} />
                                        </button>
                                    </span>
                                </div>
                            ))}
                        </div>
                    </CollapsibleSection>

                    <CollapsibleSection icon={<FiEdit3 />} title={`${nNotes}. Notes`}>
                        <div className={styles.notesWrap}>
                            <span className={styles.noteDateChip}><FiCalendar size={11} /> {todayDMY()}</span>
                            <textarea className={styles.textarea} value={notes} onChange={e => { setNotes(e.target.value); markDirty(); }} placeholder="Shared project notes - visible to all staff on the folder page..." />
                            <p className={styles.hint}>Saved with today's date as an intake note.</p>
                        </div>
                    </CollapsibleSection>
                </div>

            </div>

            <div className={styles.bottomBar}>
                <button type="button" className={styles.topBtn} onClick={scrollTop} aria-label="Back to top">
                    <FiArrowUp />
                </button>
                <div className={styles.bottomBarRight}>
                    <button type="button" className={styles.addBtn} onClick={handleDuplicate} disabled={saving}>
                        <FiCopy /> Duplicate
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> Save Project
                    </button>
                </div>
            </div>

            {blocker.state === 'blocked' && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalCard}>
                        <h3 className={styles.modalTitle}>Unsaved work</h3>
                        <p className={styles.modalText}>
                            You have unsaved information on this form. Do you want to save it before leaving?
                        </p>
                        <div className={styles.modalBtns}>
                            <button type="button" className={styles.btn} onClick={() => blocker.reset()}>Stay</button>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`} onClick={() => blocker.proceed()}>Leave without saving</button>
                            <button
                                type="button"
                                className={`${styles.btn} ${styles.primary}`}
                                onClick={async () => {
                                    const ok = await doSave();
                                    if (ok) blocker.proceed(); else blocker.reset();
                                }}
                            >
                                <FiSave /> Save & Leave
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles[t.type] || ''}`}>{t.msg}</div>
            ))}
        </div>
    );
}
""")

# =====================================================================
# Report + commit + push
# =====================================================================
print(f"\n=== fix.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)} file(s)")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        commit_msg = """feat: intake pass 5 — validation, duplicate-saves, guards, stage insert

- Top arrow: single orange arrow, no border/outline, visible on tan bg
- Stage add: per-row + inserts directly under the clicked stage; order
  updates run in one parallel wave (no lag); delete middle-only
- Validation: owners need NIN+Name+Phone (email optional, / allowed for
  multiple numbers), Title ID + Plot required, Total Cost > 0,
  Initial Payment required, at least one document required
- Fields a touch bigger (34-40px) incl. dropdowns
- Notes carry a date chip and are saved as [dd/mm/yyyy] note text
- Sidebar auto-collapses on first interaction (standard)
- Stage X buttons use the app-standard orange X
- Title Details accent border only while the section has focus
- Cancel stays at top; Duplicate now SAVES first (same warnings) then
  carries owners+location into a fresh form
- Unsaved-changes guard: in-app router blocker modal (Save & Leave /
  Leave / Stay) + browser beforeunload warning"""
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