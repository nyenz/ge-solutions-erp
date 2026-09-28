#!/usr/bin/env python3
# PATH: fix137.py
# GOLDEN SEED -- fix137: UPLOAD DOCUMENTS dropdown matches the app.
#   Before: the category boxes in the UPLOAD DOCUMENTS window were the
#   browser's own <select>. Click one and Chrome opens its plain white list --
#   default colours, default font, nothing from the app. Now:
#
#     1. NEW DROPDOWN. HardwareModalSelect (new component + css) draws its own
#        list: dark teal panel, orange edge, orange highlight under the mouse,
#        solid orange row with a tick for the chosen category. The closed box
#        is the same box as every other input in the window.
#     2. NOT CLIPPED. The list opens on top of everything, so the window's
#        scroll area and the file list can never cut it off. It opens upward
#        when there is no room below.
#     3. KEYBOARD. Up / Down / Home / End move, Enter or Space picks, Esc
#        closes. Click anywhere else closes it.
#     4. WHERE. The "category for all files" box and the small category box on
#        every file row both use it. Nothing else about uploading changes --
#        same categories, same rules, same UPLOAD button.
#
#   Not touched: HardwareSelect (the white form dropdown used on Intake,
#   Settings and Audit) and every other page.
#
# Frontend only (HardwareModalSelect.jsx + css new; FolderPage.jsx patched).
#
# Atomic: every patch for every file is matched in memory first; if any
# one is MISSING nothing is written and nothing is committed. Runs
# `npm run build` before committing if node_modules is installed and
# refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
COMMON = os.path.join(SRC, "components", "common")

SELECT_JSX = os.path.join(COMMON, "HardwareModalSelect.jsx")
SELECT_CSS = os.path.join(COMMON, "HardwareModalSelect.module.css")
FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")

MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sub(text, old, new, desc):
    """Exact find/replace, first occurrence. Prints OK / SKIP / MISSING."""
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEW_FILES = []  # (path, text, label)


def create(path, text, label):
    """New file. SKIP if it already exists."""
    if os.path.exists(path):
        print("SKIP: " + label + " -- already exists")
        return
    print("OK: " + label + " (new file)")
    NEW_FILES.append((path, text, label))


# ======================================================================
# NEW: HardwareModalSelect.jsx
# ======================================================================
create(SELECT_JSX, r'''// PATH: erp-frontend/src/components/common/HardwareModalSelect.jsx
import React, { useState, useRef, useEffect, useCallback, useId } from 'react';
import { createPortal } from 'react-dom';
import { FiChevronDown, FiCheck } from 'react-icons/fi';
import styles from './HardwareModalSelect.module.css';

/**
 * GOLDEN SEED - HARDWARE MODAL SELECT (fix137)
 *
 * The dropdown for use INSIDE a HardwareModal. It replaces the browser's own
 * <select>, whose white option list cannot be themed.
 *
 * The list is drawn on document.body (fixed position), so the modal's scroll
 * box and the file list can never clip it. It flips upward when there is no
 * room below.
 *
 * options = [{ value, label }]
 * onChange receives the chosen value.
 * Keyboard: Up/Down/Home/End move, Enter or Space picks, Esc closes.
 */
const GAP = 6;
const EDGE = 10;
const MAX_H = 260;
const MIN_W = 190;

const HardwareModalSelect = ({
    value,
    options,
    onChange,
    placeholder = 'Choose',
    emptyText = 'Nothing to choose from',
    ariaLabel,
    compact = false,
    disabled = false,
    className = '',
}) => {
    const [open, setOpen] = useState(false);
    const [active, setActive] = useState(-1);
    const [pos, setPos] = useState(null);
    const triggerRef = useRef(null);
    const panelRef = useRef(null);
    const listId = useId();

    const selectedIdx = options.findIndex(o => o.value === value);
    const selected = selectedIdx >= 0 ? options[selectedIdx] : null;

    const place = useCallback(() => {
        const el = triggerRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const width = Math.min(Math.max(r.width, MIN_W), vw - EDGE * 2);
        const left = Math.max(EDGE, Math.min(r.left, vw - width - EDGE));
        const below = vh - r.bottom - GAP - EDGE;
        const above = r.top - GAP - EDGE;
        const flip = below < 170 && above > below;
        const maxHeight = Math.max(120, Math.min(MAX_H, flip ? above : below));
        setPos(flip
            ? { left, width, bottom: vh - r.top + GAP, maxHeight }
            : { left, width, top: r.bottom + GAP, maxHeight });
    }, []);

    const openPanel = () => {
        if (disabled) return;
        place();
        setActive(selectedIdx >= 0 ? selectedIdx : (options.length ? 0 : -1));
        setOpen(true);
    };

    const choose = (opt) => {
        onChange(opt.value);
        setOpen(false);
        if (triggerRef.current) triggerRef.current.focus();
    };

    // close on outside click, follow the trigger on scroll / resize
    useEffect(() => {
        if (!open) return undefined;
        const onDown = (e) => {
            if (triggerRef.current && triggerRef.current.contains(e.target)) return;
            if (panelRef.current && panelRef.current.contains(e.target)) return;
            setOpen(false);
        };
        const onScroll = (e) => {
            if (panelRef.current && panelRef.current.contains(e.target)) return;
            place();
        };
        document.addEventListener('mousedown', onDown);
        window.addEventListener('resize', place);
        window.addEventListener('scroll', onScroll, true);
        return () => {
            document.removeEventListener('mousedown', onDown);
            window.removeEventListener('resize', place);
            window.removeEventListener('scroll', onScroll, true);
        };
    }, [open, place]);

    // keep the highlighted row inside the visible part of the list
    useEffect(() => {
        if (!open || active < 0) return;
        const panel = panelRef.current;
        if (!panel) return;
        const row = panel.querySelector('[data-idx="' + active + '"]');
        if (!row) return;
        if (row.offsetTop < panel.scrollTop) {
            panel.scrollTop = row.offsetTop;
        } else if (row.offsetTop + row.offsetHeight > panel.scrollTop + panel.clientHeight) {
            panel.scrollTop = row.offsetTop + row.offsetHeight - panel.clientHeight;
        }
    }, [open, active, pos]);

    const onKeyDown = (e) => {
        if (disabled) return;
        if (!open) {
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openPanel();
            }
            return;
        }
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            setOpen(false);
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActive(i => Math.min(options.length - 1, i + 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActive(i => Math.max(0, i - 1));
        } else if (e.key === 'Home') {
            e.preventDefault();
            setActive(options.length ? 0 : -1);
        } else if (e.key === 'End') {
            e.preventDefault();
            setActive(options.length - 1);
        } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (options[active]) choose(options[active]); else setOpen(false);
        } else if (e.key === 'Tab') {
            setOpen(false);
        }
    };

    return (
        <div className={`${styles.root} ${className}`}>
            <div
                ref={triggerRef}
                role="combobox"
                tabIndex={disabled ? -1 : 0}
                aria-haspopup="listbox"
                aria-expanded={open}
                aria-controls={open ? listId : undefined}
                aria-activedescendant={open && active >= 0 ? listId + '-' + active : undefined}
                aria-label={ariaLabel}
                aria-disabled={disabled || undefined}
                className={`${styles.trigger} ${compact ? styles.compact : ''} ${open ? styles.triggerOpen : ''} ${disabled ? styles.disabled : ''}`}
                onClick={() => (open ? setOpen(false) : openPanel())}
                onKeyDown={onKeyDown}
            >
                <span className={`${styles.value} ${selected ? '' : styles.placeholder}`}>
                    {selected ? selected.label : placeholder}
                </span>
                <FiChevronDown className={styles.chevron} aria-hidden="true" />
            </div>

            {open && pos && createPortal(
                <div
                    ref={panelRef}
                    id={listId}
                    role="listbox"
                    aria-label={ariaLabel}
                    className={styles.panel}
                    style={pos}
                    onMouseDown={(e) => e.preventDefault()}
                >
                    {options.length === 0 && <div className={styles.empty}>{emptyText}</div>}
                    {options.map((opt, i) => (
                        <div
                            key={opt.value}
                            id={listId + '-' + i}
                            data-idx={i}
                            role="option"
                            aria-selected={opt.value === value}
                            title={opt.label}
                            className={`${styles.option} ${i === active ? styles.optionActive : ''} ${opt.value === value ? styles.optionSelected : ''}`}
                            onMouseEnter={() => setActive(i)}
                            onClick={() => choose(opt)}
                        >
                            <span className={styles.optionText}>{opt.label}</span>
                            {opt.value === value && <FiCheck className={styles.check} aria-hidden="true" />}
                        </div>
                    ))}
                </div>,
                document.body
            )}
        </div>
    );
};

export default HardwareModalSelect;
''', "components/common/HardwareModalSelect.jsx")

# ======================================================================
# NEW: HardwareModalSelect.module.css
# ======================================================================
create(SELECT_CSS, r'''/* PATH: erp-frontend/src/components/common/HardwareModalSelect.module.css
   fix137 -- dropdown for use inside HardwareModal. The closed box is the
   same box as .modalInput (HardwareModal.module.css); the open list uses the
   modal's own dark teal, orange edge and orange selected row. */

.root { position: relative; min-width: 0; }

.trigger {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
    margin-top: clamp(5px, 0.6vw, 7px);
    padding: clamp(11px, 1.4vw, 14px) clamp(12px, 1.6vw, 16px);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.07);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.92);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(13px, 1.3vw, 15px);
    font-weight: 700;
    line-height: 1.25;
    cursor: pointer;
    user-select: none;
    outline: none;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}
.trigger:hover { border-color: rgba(238, 140, 58, 0.45); }
.trigger:focus-visible,
.triggerOpen {
    border-color: rgba(238, 140, 58, 0.7);
    background: rgba(238, 140, 58, 0.06);
    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.14);
}

/* the smaller box used on each file row */
.compact {
    margin-top: 0;
    padding: clamp(7px, 0.9vw, 9px) clamp(9px, 1.2vw, 12px);
    font-size: clamp(11px, 1.1vw, 13px);
}

.disabled { opacity: 0.35; cursor: not-allowed; }

.value {
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.placeholder {
    color: var(--text-on-dark-soft, rgba(244, 242, 239, 0.72));
    font-weight: 500;
}

.chevron {
    flex-shrink: 0;
    font-size: 16px;
    color: var(--orange, #EE8C3A);
    transition: transform 0.2s;
}
.triggerOpen .chevron { transform: rotate(180deg); }

/* ── the open list ───────────────────────────────────────────── */
.panel {
    position: fixed;
    z-index: 100001;
    box-sizing: border-box;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: var(--panel-surface-alt, #16292b);
    border: 1.5px solid rgba(238, 140, 58, 0.55);
    border-radius: 8px;
    box-shadow:
        0 18px 44px rgba(0, 0, 0, 0.6),
        0 0 0 1px rgba(255, 255, 255, 0.04),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    scrollbar-width: none;
    -ms-overflow-style: none;
    animation: msOpen 0.14s ease-out;
}
.panel::-webkit-scrollbar { display: none; }

.option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: clamp(9px, 1.1vw, 12px) clamp(12px, 1.6vw, 16px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    color: var(--text-on-dark, rgba(244, 242, 239, 0.82));
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 14px);
    font-weight: 700;
    cursor: pointer;
    transition: background 0.12s, color 0.12s;
}
.option:last-child { border-bottom: none; }
.optionText {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.optionActive {
    background: rgba(238, 140, 58, 0.16);
    color: #ffffff;
}
.optionSelected,
.optionSelected.optionActive {
    background: var(--orange, #EE8C3A);
    color: #1a2e30;
    border-bottom-color: transparent;
}
.check { flex-shrink: 0; font-size: 15px; }

.empty {
    padding: clamp(10px, 1.2vw, 14px) clamp(12px, 1.6vw, 16px);
    color: var(--text-on-dark-soft, rgba(244, 242, 239, 0.72));
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 14px);
    font-weight: 500;
}

@keyframes msOpen {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
    .panel { animation: none; }
    .trigger, .chevron, .option { transition: none; }
}
''', "components/common/HardwareModalSelect.module.css")

# ======================================================================
# FolderPage.jsx
# ======================================================================
fol0 = read(FOLDER_JSX)
fol = fol0

fol = sub(fol,
          "import HardwareButton from '../../components/common/HardwareButton';",
          "import HardwareButton from '../../components/common/HardwareButton';\n"
          "import HardwareModalSelect from '../../components/common/HardwareModalSelect';",
          "folder: import HardwareModalSelect")

CAT_LABEL = "    const catLabel = (code) => (docCats.find(c => c.code === code)?.label) || String(code).replace(/_/g, ' ');"
fol = sub(fol,
          CAT_LABEL,
          CAT_LABEL + "\n"
          "    const catOptions = docCats.map(c => ({ value: c.code, label: c.label }));",
          "folder: catOptions for the dropdown")

fol = sub(fol,
          r'''                        <select className={modalStyles.modalInput} value={uploadDraft.batch} onChange={e => setBatchCategory(e.target.value)} aria-label="Category for all files">
                            <option value="">-- choose category --</option>
                            {docCats.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
                        </select></div>''',
          r'''                        <HardwareModalSelect value={uploadDraft.batch} options={catOptions} onChange={setBatchCategory} placeholder="Choose category" emptyText="No categories available" ariaLabel="Category for all files" /></div>''',
          "folder: 'category for all files' dropdown")

fol = sub(fol,
          r'''                        <select className={`${modalStyles.modalInput} ${styles.upFileSelect}`} value={f.category} onChange={e => setFileCategory(i, e.target.value)} aria-label={'Category for ' + f.file.name}>
                            <option value="">-- category --</option>
                            {docCats.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
                        </select></div>))}</div>''',
          r'''                        <HardwareModalSelect compact className={styles.upFileSelect} value={f.category} options={catOptions} onChange={code => setFileCategory(i, code)} placeholder="Category" emptyText="No categories available" ariaLabel={'Category for ' + f.file.name} /></div>))}</div>''',
          "folder: per-file category dropdown")

# ======================================================================
# write (atomic) + build gate + commit
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix136).")
    sys.exit(1)

changed = False
for path, text, label in NEW_FILES:
    write(path, text)
    print("created: " + label)
    changed = True

for path, before, after, label in [
    (FOLDER_JSX, fol0, fol, "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"),
]:
    if after != before:
        write(path, after)
        print("written: " + label)
        changed = True
if not changed:
    print("note: nothing changed -- fix137 already applied")

# build gate (fix76)
if os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        print("FAIL: build is red -- aborting, nothing committed")
        sys.exit(1)
    print("build OK")
else:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")


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
git("commit", "-m", "fix137: upload window dropdown matches the app -- custom dark category dropdown (no browser default list) for the batch category and each file row, opens on top of the window, keyboard friendly")
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip() or "pushed")