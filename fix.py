#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix151: Audit page redecorated from the Report Catalogue + unsaved-changes popup on the app popup standard.
#
# 1. Audit log list: the rows now sit as ONE white card on a cream #f2ede4 tray (same as the Report Catalogue list),
#    hairline dividers between records, navy text. NO orange on the list: hover is a soft navy tint.
# 2. Opened row (the extension) uses the catalogue's dark readout colour #28383a. The second left line is gone:
#    the severity rail on the row is the only one and it now runs straight down the extension.
# 3. SELECTED row is obvious: its head turns solid navy with white text and the chevron flips (no orange), flowing
#    into the dark readout so the pair reads as one opened block.
# 4. UnsavedChangesModal is rebuilt on the HardwareModal popup standard (same backdrop, card, Cinzel title with the
#    orange hairline under it, modalFooter + modalBtnPrimary/Secondary). Props are unchanged, so every caller works.
#    Per DESIGN RULE 1 the X is gone (two explicit buttons instead); backdrop click and Esc still mean KEEP EDITING.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix151"
COMMIT_MSG = "fix151: audit page redecorated from report catalogue (no orange, single rail, selected state); unsaved-changes popup on app popup standard"
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
UCM_JSX = os.path.join(SRC, "components", "common", "UnsavedChangesModal.jsx")
UCM_CSS = os.path.join(SRC, "components", "common", "UnsavedChangesModal.module.css")
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
UCM_JSX_TEXT = r'''// PATH: erp-frontend/src/components/common/UnsavedChangesModal.jsx
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiAlertTriangle, FiSave, FiLogOut } from 'react-icons/fi';
import modal from './HardwareModal.module.css';
import styles from './UnsavedChangesModal.module.css';

/**
 * GOLDEN SEED -- UNSAVED CHANGES GUARD (fix151)
 *
 * Built on the HardwareModal popup standard: same backdrop, card, Cinzel title
 * with the orange hairline, modalFooter and modalBtnPrimary / modalBtnSecondary.
 * DESIGN RULE 1 (X is the closer) -> no X here, two explicit buttons instead.
 * Backdrop click and Esc both mean KEEP EDITING (the safe choice).
 *
 * Props:
 *   isOpen   -- whether to show the modal
 *   onStay   -- user chose to stay and keep editing
 *   onLeave  -- user confirmed they want to leave (lose changes)
 *   context  -- what will be lost (e.g. "Audit Filters")
 */
const UnsavedChangesModal = ({ isOpen, onStay, onLeave, context = 'this form' }) => {
    useEffect(() => {
        if (!isOpen) return;
        const handler = (e) => { if (e.key === 'Escape') onStay(); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [isOpen, onStay]);

    if (!isOpen || typeof document === 'undefined') return null;

    return createPortal(
        <div className={modal.backdrop} onClick={onStay} role="dialog" aria-modal="true" aria-labelledby="ucm-title">
            <div className={modal.modalBody} onClick={(e) => e.stopPropagation()}>
                <header className={modal.header}>
                    <FiAlertTriangle className={styles.warnIcon} aria-hidden="true" />
                    <span id="ucm-title" className={modal.title}>UNSAVED CHANGES</span>
                </header>

                <div className={`${modal.modalInfoBox} ${styles.warnBox}`}>
                    You have unsaved changes in <strong>{context}</strong>.
                    If you leave now, everything you entered will be permanently lost.
                </div>

                <div className={modal.modalFooter}>
                    <button className={`${modal.modalBtnSecondary} ${styles.leaveBtn}`} onClick={onLeave}
                        aria-label="Leave page and discard changes">
                        <FiLogOut aria-hidden="true" /> DISCARD &amp; LEAVE
                    </button>
                    <button className={modal.modalBtnPrimary} onClick={onStay} autoFocus
                        aria-label="Stay on page and keep editing">
                        <FiSave aria-hidden="true" /> KEEP EDITING
                    </button>
                </div>

                <div className={modal.footerGlow} />
            </div>
        </div>,
        document.body
    );
};

export default UnsavedChangesModal;
'''

UCM_CSS_TEXT = r'''/* PATH: erp-frontend/src/components/common/UnsavedChangesModal.module.css */
/* fix151: the card, backdrop, header, footer and buttons come from HardwareModal.module.css.
   Only the amber warning accents live here. */

.warnIcon {
    flex-shrink: 0;
    margin-right: clamp(8px, 1vw, 12px);
    font-size: clamp(18px, 2vw, 22px);
    color: #f59e0b;
}

/* div.warnBox beats the single-class .modalInfoBox regardless of stylesheet order */
div.warnBox {
    background: rgba(245, 158, 11, 0.08);
    border-color: rgba(245, 158, 11, 0.3);
    margin-bottom: 0;
}
div.warnBox strong { color: #fff; font-weight: 900; }

/* DISCARD & LEAVE: same secondary button, red on hover */
button.leaveBtn:hover {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.5);
    color: #fca5a5;
}
button.leaveBtn:focus-visible { outline-color: #ef4444; }
'''

AUDIT_CSS_BLOCK = r'''

/* ================= fix151: AUDIT LIST FROM THE REPORT CATALOGUE =================
   Same idea as ReportStudio .catList / .groupBody / .row / .readout: the rows sit as ONE white card on a
   cream #f2ede4 tray with hairline dividers, and an opened row drops into the dark #28383a readout.
   DIFFERENCES ON PURPOSE: no orange anywhere on the list (hover = navy tint, selected = solid navy), and ONE
   left line only -- the severity rail on .logRow, which now runs down through the readout. */
.logTray { background: #f2ede4; padding: 10px; }
.logCard { border-radius: 10px; overflow: hidden; background: #fff; box-shadow: 0 2px 8px rgba(26,46,48,0.14); }

.logRow { border-bottom: 1.5px solid rgba(26,46,48,0.16); }
.logRow:last-child { border-bottom: none; }
.logRow:hover { background: rgba(26,46,48,0.06); }
.logRow:focus-visible { background: rgba(26,46,48,0.06); outline: 2px solid #1a2e30; outline-offset: -2px; }

/* text on the white card is navy */
.clockPair { color: #1a2e30; }
.clockPair svg { color: #5b6f70; }
.timeMark small { color: #1a2e30; opacity: 0.6; }
.iconChassis { background: rgba(26,46,48,0.06); border-color: rgba(26,46,48,0.16); color: #5b6f70; }
.actionMeta strong { color: #1a2e30; }
.actionMeta span { color: rgba(26,46,48,0.55); }
.severityHigh  .actionMeta strong { color: #b91c1c; }
.severityIntel .actionMeta strong { color: #047857; }
.targetMark p { color: rgba(26,46,48,0.8); }
.inspectIcon { color: rgba(26,46,48,0.4); transition: transform 0.2s ease, color 0.15s ease; }
.logRow:hover .inspectIcon { color: #1a2e30; }

/* SELECTED (the open row): solid navy head, light text, flipped chevron -- no orange */
.logRow.expanded, .logRow.expanded:hover { background: transparent; }
.logRow.expanded .logMain { background: #1a2e30; }
.logRow.expanded .clockPair { color: #fff; }
.logRow.expanded .clockPair svg { color: #f2ede4; }
.logRow.expanded .timeMark small { color: #fff; opacity: 0.65; }
.logRow.expanded .iconChassis { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.2); color: #f2ede4; }
.logRow.expanded .actionMeta strong { color: #fff; }
.logRow.expanded .actionMeta span { color: rgba(255,255,255,0.6); }
.logRow.expanded.severityHigh  .actionMeta strong { color: #fca5a5; }
.logRow.expanded.severityIntel .actionMeta strong { color: #6ee7b7; }
.logRow.expanded .targetMark p { color: #fff; }
.logRow.expanded .inspectIcon { color: #f2ede4; transform: rotate(180deg); }

/* the extension: the catalogue's readout colour, and no second left line */
.traceDetails { background: #28383a; }
.traceOpen { border-top: 1px solid rgba(255,255,255,0.08); overflow-y: auto; scrollbar-width: thin; }
.rawBox { border-left: none; margin: 0; padding: clamp(10px,1.3vw,14px) clamp(12px,1.5vw,18px); }
'''

# ============================ EDIT PART 2 START ============================
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (AUDIT_JSX, AUDIT_CSS, GUIDE)
for _p in LOAD_FILES:
    load(_p)

def L(*lines):
    return "\n".join(lines)

# ---- 1. Popup: whole-file rebuild on the HardwareModal standard ----
newfile(UCM_JSX, UCM_JSX_TEXT, "UnsavedChangesModal.jsx (HardwareModal standard)", "fix151")
newfile(UCM_CSS, UCM_CSS_TEXT, "UnsavedChangesModal.module.css (amber accents only)", "fix151")

# ---- 2. Audit page JSX ----
patch(AUDIT_JSX,
      "    FiDatabase, FiMaximize2, FiX, FiFilter,",
      "    FiDatabase, FiChevronDown, FiX, FiFilter,",
      "Audit JSX: import chevron instead of maximize icon")
patch(AUDIT_JSX,
      "                    {!loading && visibleLogs.map(log => (",
      L("                    {!loading && visibleLogs.length > 0 && (<div className={styles.logTray}><div className={styles.logCard}>",
        "                    {visibleLogs.map(log => ("),
      "Audit JSX: open the tray + card wrapper")
patch(AUDIT_JSX,
      L("                        </div>",
        "                    ))}",
        "                </div>",
        "",
        "                <footer className={styles.pagination}"),
      L("                        </div>",
        "                    ))}",
        "                    </div></div>)}",
        "                </div>",
        "",
        "                <footer className={styles.pagination}"),
      "Audit JSX: close the tray + card wrapper")
patch(AUDIT_JSX,
      "{expandedId === log.id ? <FiX /> : <FiMaximize2 />}",
      "<FiChevronDown />",
      "Audit JSX: chevron replaces maximize/X (flips when selected)")

# ---- 3. Audit page CSS (appended last so it wins) ----
patch(AUDIT_CSS,
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}"),
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}") + AUDIT_CSS_BLOCK,
      "Audit CSS: catalogue-style card, selected state, single rail")

# ---- 4. guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix150: Settings inner boxes darker + Expenses cream inner cards, Section 7)",
      "# Last updated: September 2026 (fix151: Audit list from Report Catalogue + unsaved-changes popup on HardwareModal standard, Section 7)",
      "Guide: header line")
patch(GUIDE,
      "### Settings inner boxes + Expenses cream cards (fix150)",
      L("### Audit list + unsaved-changes popup (fix151)",
        "- Audit log rows sit as one white card (`.logCard`) on a cream `#f2ede4` tray (`.logTray`), hairline dividers, navy text -- the Report Catalogue look WITHOUT its orange. Hover = navy tint. The SELECTED (open) row head is solid navy `#1a2e30` with light text and a flipped chevron; the extension uses the catalogue readout colour `#28383a`.",
        "- One left line only: the severity rail on `.logRow` (red/orange/green/cyan) runs through the extension. `.rawBox` has no border-left. Do not add one back.",
        "- `UnsavedChangesModal` is built from `HardwareModal.module.css` classes (backdrop, modalBody, header, title, modalInfoBox, modalFooter, modalBtnPrimary/Secondary). No X (DESIGN RULE 1); two buttons; Esc / backdrop = KEEP EDITING. Props unchanged.",
        "",
        "### Settings inner boxes + Expenses cream cards (fix150)"),
      "Guide: fix151 note")

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