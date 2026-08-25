#!/usr/bin/env python3
"""
fix.py — Dark-theme intake form revamp.
Writes/patches all 10 target files, then auto-commits.
Run: py fix.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WROTE, PATCHED, FAILED = [], [], []

def write(rel: str, content: str):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(content, encoding="utf-8")
        WROTE.append(rel)
    except Exception as e:
        FAILED.append((rel, str(e)))

def patch_append(rel: str, marker: str, insert: str):
    p = ROOT / rel
    try:
        original = p.read_text(encoding="utf-8")
    except Exception as e:
        FAILED.append((rel, f"read failed: {e}")); return
    if marker not in original:
        FAILED.append((rel, f"marker not found")); return
    if insert.strip() in original:
        PATCHED.append(f"{rel} (already applied)"); return
    try:
        p.write_text(original.replace(marker, marker + "\n" + insert, 1), encoding="utf-8")
        PATCHED.append(rel)
    except Exception as e:
        FAILED.append((rel, f"write failed: {e}"))

# =====================================================================
# 1) CollapsibleSection.module.css — FULL WRITE (dark hardware panel)
# =====================================================================
write("erp-frontend/src/components/ui/CollapsibleSection.module.css", r"""/* PATH: erp-frontend/src/components/ui/CollapsibleSection.module.css */
/* Dark "hardware panel" treatment - same language as HardwarePanel.dark,
   the Ledger table shell and the reference New Plot design. */
.section {
    --orange: #EE8C3A;
    --orange-dim: rgba(238, 140, 58, 0.18);
    background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);
    border: 1px solid rgba(238, 140, 58, 0.2);
    border-radius: 12px;
    overflow: visible;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.section:hover { border-color: var(--orange); }
.section.accent { border: 2px solid var(--orange); }

.header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(7px, 1.1vw, 13px);
    padding: clamp(12px, 1.6vw, 18px) clamp(14px, 1.8vw, 20px);
    background: transparent;
    border: none;
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
    font-size: clamp(15px, 1.8vw, 19px);
    filter: drop-shadow(0 0 5px rgba(238, 140, 58, 0.4));
}

.title {
    font-family: 'Cinzel', serif;
    font-size: clamp(13px, 1.6vw, 16px);
    font-weight: 700;
    color: var(--orange);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0;
    transition: color 0.15s ease;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.header:hover .title { color: #f59a4a; }

.headerRight {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1.2vw, 14px);
    flex-shrink: 0;
}

.chevron {
    color: rgba(255, 255, 255, 0.5);
    font-size: 16px;
    transition: transform 0.2s ease, color 0.2s ease;
    flex-shrink: 0;
}
.chevronOpen { transform: rotate(180deg); color: var(--orange); }

.body {
    padding: 0 clamp(14px, 1.8vw, 20px) clamp(14px, 1.8vw, 20px);
    display: flex;
    flex-direction: column;
    gap: clamp(10px, 1.5vw, 18px);
    border-top: 1px solid rgba(238, 140, 58, 0.25);
    padding-top: clamp(14px, 1.8vw, 20px);
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
# 2) HardwareSelect.jsx — FULL WRITE (adds required/placeholder/compact)
# =====================================================================
write("erp-frontend/src/components/common/HardwareSelect.jsx", r"""// PATH: erp-frontend/src/components/common/HardwareSelect.jsx
import React, { useState, useRef, useEffect } from 'react';
import { FiChevronDown } from 'react-icons/fi';
import styles from './HardwareSelect.module.css';

const HardwareSelect = ({ label, options, value, onChange, required = false, placeholder = '', compact = false }) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className={`${styles.fieldWrapper} ${isOpen ? styles.openWrapper : ''} ${compact ? styles.compactWrapper : ''}`} ref={containerRef}>
            {label && (
                <label className={styles.label}>
                    {label}
                    {required && <span className={styles.requiredMark}>*</span>}
                </label>
            )}
            <div className={`${styles.selectBox} ${compact ? styles.compactBox : ''} ${isOpen ? styles.active : ''}`} onClick={() => setIsOpen(!isOpen)}>
                <span className={`${styles.currentValue} ${!value ? styles.placeholder : ''}`}>{value || placeholder}</span>
                <FiChevronDown className={styles.icon} />

                {isOpen && (
                    <div className={styles.dropdown}>
                        {options.map(opt => (
                            <div
                                key={opt}
                                className={`${styles.option} ${value === opt ? styles.selected : ''}`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onChange(opt);
                                    setIsOpen(false);
                                }}
                            >
                                {opt}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default HardwareSelect;
""")

# =====================================================================
# 3) HardwareSelect.module.css — FULL WRITE (label 11px + new rules)
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

.label {
    color: #FFFFFF !important;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.5px;
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
    transition: 0.3s ease;
    height: var(--input-height, 44px);
    position: relative;
    z-index: 1;
}
.selectBox:hover, .active {
    border-color: var(--orange);
    box-shadow: 0 0 20px rgba(238, 140, 58, 0.2);
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

.dropdown {
    position: fixed;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 8px 20px rgba(0,0,0,0.3);
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
    z-index: 99999 !important;
    min-width: 100%;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
}

.option {
    padding: 14px 20px;
    color: var(--navy);
    font-weight: 600;
    font-size: 14px;
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
    background: #f1f5f9;
    border-left: 5px solid var(--orange);
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
# 4) IntakePage.module.css — FULL WRITE (dark hardware revamp)
# =====================================================================
write("erp-frontend/src/pages/Intake/IntakePage.module.css", r"""/* PATH: erp-frontend/src/pages/Intake/IntakePage.module.css
   Dark hardware revamp - same tokens as HardwarePanel/HardwareInput/
   HardwareSelect and the Ledger reference. */
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
    --radius-sm: 8px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(9px,  0.95vw, 11px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-input:  clamp(11px, 1.1vw, 13px);
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);
}

.container {
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px);
    font-family: 'Inter', sans-serif;
    color: #F4F2EF;
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

.btn {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-btn);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: clamp(8px, 1vw, 12px) clamp(14px, 2vw, 22px);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(0, 0, 0, 0.25);
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
}
.btn:hover { border-color: var(--orange); color: var(--orange); }
.btn.primary { background: var(--orange); color: #fff; border-color: var(--orange); }
.btn.primary:hover { background: #d97a2b; border-color: #d97a2b; color: #fff; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.legacyBtn {
    background: rgba(0, 0, 0, 0.3);
    color: #fff;
    border: 1px solid rgba(238, 140, 58, 0.35);
    padding: clamp(8px, 1vw, 12px) clamp(14px, 2vw, 22px);
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-btn);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
}
.legacyBtn:hover { border-color: var(--orange); color: var(--orange); }

.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--gap-lg); }
.grid3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--gap-lg); }

.field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }

.label {
    font-family: 'Inter', sans-serif;
    font-size: var(--fs-label);
    font-weight: 800;
    color: #FFFFFF;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
.required::after { content: '*'; color: var(--red); margin-left: 4px; }

.hint {
    font-size: var(--fs-meta);
    font-weight: 600;
    color: rgba(255, 255, 255, 0.45);
    letter-spacing: 0.3px;
    margin: 0;
}

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
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.input:hover, .textarea:hover,
.input:focus, .textarea:focus {
    outline: none;
    border-color: var(--orange);
    box-shadow: 0 0 15px rgba(238, 140, 58, 0.2);
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

.typeGroup { display: flex; gap: var(--gap-md); flex-wrap: wrap; }
.typeBtn {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-btn);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: clamp(10px, 1.2vw, 14px) clamp(16px, 2vw, 22px);
    border-radius: var(--radius-sm);
    border: 2px solid rgba(255, 255, 255, 0.15);
    background: rgba(0, 0, 0, 0.2);
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    transition: all 0.2s;
}
.typeBtn:hover { border-color: var(--orange-border); color: var(--orange); }
.typeBtnActive {
    border-color: var(--orange);
    background: var(--orange-dim);
    color: var(--orange);
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.25);
}
.typeHint { font-size: var(--fs-meta); color: rgba(255, 255, 255, 0.45); margin: 2px 0 0 0; }

.ownerRow {
    display: grid;
    grid-template-columns: 1.2fr 2fr 1fr 1.5fr auto;
    gap: var(--gap-md);
    align-items: end;
    padding: var(--gap-md);
    background: rgba(0, 0, 0, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-sm);
}

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
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--orange-border);
    border-radius: var(--radius-sm);
    padding: var(--gap-md);
}
.inlineAddRow .input { width: auto; flex: 1 1 200px; }

.stageList { display: flex; flex-direction: column; gap: var(--gap-md); }
.stageItem {
    display: flex;
    align-items: center;
    gap: var(--gap-md);
    padding: var(--gap-md);
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.2s;
}
.stageItem:hover { border-color: var(--orange); }
.stageItem.checked { border-color: var(--orange); background: var(--orange-dim); }
.stageItem.stageLocked { cursor: not-allowed; border-color: rgba(255, 255, 255, 0.2); background: rgba(0, 0, 0, 0.25); }
.checkbox { width: 18px; height: 18px; accent-color: var(--orange); cursor: pointer; flex-shrink: 0; }
.stageName { font-weight: 700; color: #fff; font-size: var(--fs-value); letter-spacing: 0.3px; }
.lockedTag {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: var(--fs-tag);
    font-weight: 800;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.5);
    letter-spacing: 0.5px;
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

.financialsSummary {
    background: rgba(0, 0, 0, 0.2);
    padding: var(--gap-lg);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
}
.finRow { display: flex; justify-content: space-between; font-weight: 700; color: #fff; font-size: var(--fs-value); }
.finRow.total { color: var(--orange); font-size: clamp(14px, 1.5vw, 18px); border-top: 1px solid rgba(238, 140, 58, 0.25); padding-top: var(--gap-md); }

.dropzone {
    border: 2px dashed rgba(238, 140, 58, 0.4);
    border-radius: var(--radius);
    padding: var(--gap-xl);
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
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
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #fff;
    font-size: var(--fs-value);
    font-weight: 600;
    padding: var(--gap-md);
    border-radius: var(--radius-sm);
}

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
# 5) IntakePage.jsx — FULL WRITE (index preview, dates, split row)
# =====================================================================
write("erp-frontend/src/pages/Intake/IntakePage.jsx", r"""// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
                            <button className={styles.btn} onClick={() => setOwners(p => p.filter((_, i) => i !== idx))} disabled={owners.length === 1}>
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                    <button className={styles.btn} onClick={() => setOwners(p => [...p, EMPTY_OWNER()])}>
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
                            <button className={styles.legacyBtn} onClick={() => setShowSavePreset(s => !s)}>
                                <FiBookmark /> Save Preset
                            </button>
                            <button className={styles.legacyBtn} onClick={() => setAddingStage(s => !s)}>
                                <FiPlus /> Add Stage
                            </button>
                        </div>
                    }
                >
                    {showSavePreset && (
                        <div className={styles.inlineAddRow}>
                            <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                            <button className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                            <button className={styles.btn} onClick={() => { setShowSavePreset(false); setPresetName(''); }}><FiX /></button>
                        </div>
                    )}
                    {addingStage && (
                        <div className={styles.inlineAddRow}>
                            <input className={styles.input} placeholder="New stage name" value={newStageName} onChange={e => setNewStageName(e.target.value)} />
                            <input className={styles.input} type="number" placeholder="Default cost" value={newStageCost} onChange={e => setNewStageCost(e.target.value)} style={{ maxWidth: 160 }} />
                            <button className={`${styles.btn} ${styles.primary}`} onClick={handleAddStage}>Add</button>
                            <button className={styles.btn} onClick={() => { setAddingStage(false); setNewStageName(''); setNewStageCost(''); }}><FiX /></button>
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
                                    <button className={styles.presetChipRemove} onClick={() => deletePreset(p.name)} aria-label={`Delete preset ${p.name}`}><FiX size={12} /></button>
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
                        <label className={styles.dropzone}>
                            <FiUploadCloud size={24} />
                            <p>Click to upload</p>
                            <input type="file" multiple style={{ display: 'none' }} onChange={handleFileUpload} />
                        </label>
                        <div className={styles.fileList}>
                            {fileQueue.map((f, i) => (
                                <div key={i} className={styles.fileItem}>
                                    <span>{f.name}</span>
                                    <button className={styles.btn} onClick={() => setFileQueue(p => p.filter((_, idx) => idx !== i))}><FiTrash2 /></button>
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
# 6) landService.js — PATCH: add getNextIndex method
# =====================================================================
patch_append(
    "erp-frontend/src/services/landService.js",
    "export default landService;",
    """    // INTAKE: preview the next project index (001A format) before saving
    getNextIndex: async () => {
        const response = await api.get('/land/next-index');
        return response.data;
    },

"""
)

# =====================================================================
# 7) ProjectIndexService.java — PATCH: add previewNextIndex
# =====================================================================
patch_append(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ProjectIndexService.java",
    "    // A -> B -> C ... Z -> AA -> AB",
    """    /**
     * Non-mutating preview of the index the next intake will receive.
     * Same math as generateNextIndex() but never writes the counter.
     */
    public synchronized String previewNextIndex() {
        try (Connection conn = dataSource.getConnection()) {
            int currentNumber;
            String currentLetter;
            try (PreparedStatement ps = conn.prepareStatement(
                    "SELECT current_number, current_letter FROM project_index_counter WHERE id = 1");
                 ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    currentNumber = rs.getInt("current_number");
                    currentLetter = rs.getString("current_letter");
                } else {
                    currentNumber = 0;
                    currentLetter = "A";
                }
            }
            currentNumber = currentNumber + 1;
            if (currentNumber > 999) {
                currentNumber = 1;
                currentLetter = nextLetter(currentLetter);
            }
            return String.format("%03d", currentNumber) + currentLetter;
        } catch (Exception e) {
            throw new RuntimeException("PROJECT_INDEX_FAULT: Could not preview project index", e);
        }
    }

"""
)

# =====================================================================
# 8) LandService.java — PATCH (a) previewNextIndex method
# =====================================================================
patch_append(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
    "    @Transactional(rollbackFor = Exception.class)",
    """    public String previewNextIndex() {
        return projectIndexService.previewNextIndex();
    }

"""
)

# =====================================================================
# 8) LandService.java — PATCH (b) .projectStartDate in builder chain
# =====================================================================
patch_append(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
    "            .projectIndex(projectIndex)",
    """            .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())"""
)

# =====================================================================
# 9) LandController.java — PATCH: /next-index endpoint
# =====================================================================
patch_append(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
    "    @PostMapping(\"/projects/{id}/unlock-log\")",
    """    // INTAKE: preview next project index
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

"""
)

# =====================================================================
# 10) LandProject.java — PATCH: projectStartDate field
# =====================================================================
patch_append(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java",
    "    private String projectIndex;",
    """
    /**
     * PROJECT START DATE — set at intake, exists even before any title does.
     * Maps to LandEntryRequest.projectStartDate from the frontend.
     */
    @Column(name = "project_start_date")
    private LocalDate projectStartDate;"""
)

# =====================================================================
# 10b) LandProject.java — PATCH: missing LocalDate import
# =====================================================================
patch_append(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java",
    "import java.time.LocalDateTime;",
    "import java.time.LocalDate;"
)

# =====================================================================
# Report
# =====================================================================
print(f"\n=== fix.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
print(f"  Patched: {len(PATCHED)} file(s)")
for f in PATCHED: print(f"    ~ {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)} file(s)")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

# =====================================================================
# Auto-commit + push all changes
# =====================================================================
if WROTE or PATCHED:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)

        commit_msg = """feat: Dark theme intake form revamp

- Convert all sections to dark hardware panel design (matches Ledger reference)
- Add HardwareSelect dropdown for Tenure (app-standard styling)
- Add live Index preview (shows next 001A format before save)
- Add Date Started field (auto-filled today, editable)
- Add Title Date field (optional, backdatable)
- Split Documents and Notes into side-by-side columns
- Unify typography: Cinzel headings, Inter labels, Space Mono buttons
- Backend: previewNextIndex endpoint, projectStartDate on LandProject"""

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