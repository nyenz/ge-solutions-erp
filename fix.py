#!/usr/bin/env python3
# PATH: fix138.py
# GOLDEN SEED -- fix138: white dropdown in UPLOAD DOCUMENTS, receipt on every
# payment, styled PROBLEM window.
#
#   1. UPLOAD DOCUMENTS DROPDOWN = THE APP'S WHITE DROPDOWN. fix137 made the
#      category list dark. It now copies HardwareSelect (Intake, Settings,
#      Audit): white box, orange edge, white list, ORANGE row with white text
#      on hover, orange row for the chosen category, same 0.2s timing, same
#      hidden scrollbar. The list is still drawn on top of the window (never
#      clipped) and the keyboard keys still work. Only the CSS file changes.
#
#   2. RECEIPT ON EVERY PAYMENT. The RECORD PAYMENT window (title payment AND
#      storage fee -- both go through the same CONFIRM) now has a PAYMENT
#      RECEIPT field. Pick a scan (pdf / jpg / png / webp). When CONFIRM is
#      pressed the payment is recorded, then the receipt is filed in the
#      folder's Documents under "Payment Receipts", named
#      "Receipt - Title Payment - UGX 2050000 - 2026-09-28.pdf".
#      - Receipt is REQUIRED (no receipt = no payment). To make it optional
#        change RECEIPT_REQUIRED to false at the top of FolderPage.jsx.
#      - If the payment saves but the receipt upload fails, the payment
#        stays, and a warning says to add the receipt from Documents.
#
#   3. PROBLEM WINDOW. The plain browser box ("golden-seed.onrender.com says
#      Describe the problem") is gone. PROBLEM now opens a proper Golden Seed
#      window: red info strip, a note box for WHAT THE PROBLEM IS (500 chars,
#      counter), CANCEL and FLAG PROBLEM buttons. The text goes to the bell
#      notification, the notes list and the audit line exactly as before.
#      Clearing a problem is still one click, no window.
#
# Frontend only. No backend change (the PAYMENT_RECEIPT category and the
# upload endpoint already exist from fix136).
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

SELECT_CSS = os.path.join(COMMON, "HardwareModalSelect.module.css")
FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")

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


REWRITES = []  # (path, text, label)


def rewrite(path, text, label, marker):
    """Replace a whole file. SKIP if the file already carries `marker`."""
    if not os.path.exists(path):
        print("MISSING: " + label + " -- file not found")
        MISSING.append(label)
        return
    if marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (rewritten)")
    REWRITES.append((path, text, label))


# ======================================================================
# HardwareModalSelect.module.css -- the app's white dropdown
# (copied from HardwareSelect.module.css; class names unchanged so the
#  component and FolderPage need no edit for this part)
# ======================================================================
rewrite(SELECT_CSS, r'''/* PATH: erp-frontend/src/components/common/HardwareModalSelect.module.css
   fix138 -- the app's WHITE dropdown (same as HardwareSelect on Intake /
   Settings / Audit) for use inside HardwareModal. White box, orange edge,
   white list, orange row + white text on hover, orange chosen row.
   The list is fixed-position on document.body so a window can never clip it. */

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
    height: var(--input-height, clamp(34px, 4.3vw, 40px));
    padding: 0 var(--input-px, clamp(9px, 1.2vw, 13px));
    border-radius: var(--input-radius, 6px);
    background: #ffffff;
    border: 1.5px solid rgba(238, 140, 58, 0.3);
    color: var(--navy, #213E40);
    font-family: 'Inter', sans-serif;
    font-size: var(--input-font, clamp(11px, 1.05vw, 13px));
    font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    user-select: none;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.trigger:hover,
.trigger:focus-visible,
.triggerOpen {
    border-color: var(--orange, #EE8C3A);
    box-shadow: 0 0 0 2px rgba(238, 140, 58, 0.15);
}

/* the smaller box used on each file row */
.compact {
    margin-top: 0;
    height: clamp(30px, 3.6vw, 36px);
}

.disabled { opacity: 0.35; cursor: not-allowed; }

.value {
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.placeholder { color: rgba(26, 46, 48, 0.45); font-weight: 700; }

.chevron {
    flex-shrink: 0;
    font-size: 14px;
    color: var(--orange, #EE8C3A);
    transition: transform 0.3s;
}
.triggerOpen .chevron { transform: rotate(180deg); }

/* -- the open list -------------------------------------------------- */
.panel {
    position: fixed;
    z-index: 100001;
    box-sizing: border-box;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: #ffffff;
    border: 1.5px solid var(--orange, #EE8C3A);
    border-radius: 6px;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5), 0 6px 16px rgba(0, 0, 0, 0.3);
    scrollbar-width: none;
    -ms-overflow-style: none;
    animation: msOpen 0.2s ease-out;
}
.panel::-webkit-scrollbar { width: 4px; display: none !important; }

.option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: clamp(8px, 1vw, 11px) clamp(12px, 1.4vw, 16px);
    background: #ffffff;
    border-bottom: 1px solid #f1f5f9;
    color: var(--navy, #213E40);
    font-family: 'Inter', sans-serif;
    font-size: clamp(11px, 1.05vw, 13px);
    font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
}
.option:last-child { border-bottom: none; }
.optionText {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.optionActive,
.optionSelected,
.optionSelected.optionActive {
    background: var(--orange, #EE8C3A);
    color: #ffffff;
    border-bottom-color: transparent;
}
.check { flex-shrink: 0; font-size: 14px; }

.empty {
    padding: clamp(10px, 1.2vw, 14px) clamp(12px, 1.6vw, 16px);
    color: rgba(26, 46, 48, 0.55);
    font-family: 'Inter', sans-serif;
    font-size: clamp(11px, 1.05vw, 13px);
    font-weight: 700;
}

@keyframes msOpen {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}

@media (max-width: 480px) {
    .trigger { height: 38px; font-size: 12px; }
    .compact { height: 34px; }
    .option { padding: 9px 12px; font-size: 12px; }
}

@media (prefers-reduced-motion: reduce) {
    .panel { animation: none; }
    .trigger, .chevron, .option { transition: none; }
}
''', "components/common/HardwareModalSelect.module.css (white + orange hover)", "fix138")

# ======================================================================
# FolderPage.module.css -- receipt field + problem window styles
# ======================================================================
css0 = read(FOLDER_CSS)
css = css0

CSS_ANCHOR = ".upCatActions .addDocBtn{flex:1;}"
css = sub(css,
          CSS_ANCHOR,
          CSS_ANCHOR + r'''

/* fix138: payment receipt field (RECORD PAYMENT window) + PROBLEM window */
.recFile{display:flex;align-items:center;gap:8px;min-width:0;margin-top:clamp(5px,0.6vw,7px);padding:clamp(8px,1vw,11px) clamp(10px,1.3vw,14px);background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.28);border-radius:6px;color:rgba(255,255,255,0.9);font-size:clamp(11px,1.05vw,13px);font-weight:700;}
.recFile svg{flex-shrink:0;color:#22c55e;}
.recName{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.recRemove{flex-shrink:0;display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;background:transparent;border:1.5px solid rgba(255,255,255,0.18);border-radius:6px;color:rgba(255,255,255,0.7);cursor:pointer;transition:background 0.2s,border-color 0.2s,color 0.2s;}
.recRemove:hover{background:rgba(239,68,68,0.15);border-color:#ef4444;color:#ef4444;}
.recRemove:focus-visible{outline:2px solid var(--orange);outline-offset:2px;}
.recHint{display:block;margin-top:6px;font-size:clamp(9px,0.9vw,11px);font-weight:700;letter-spacing:0.5px;color:rgba(255,255,255,0.45);}
.probCount{display:block;margin-top:5px;text-align:right;font-family:'Space Mono',monospace;font-size:clamp(9px,0.9vw,11px);font-weight:700;color:rgba(255,255,255,0.4);}
.probBox{min-height:clamp(96px,16vh,140px);resize:vertical;}
''',
          "css: receipt field + problem window styles")

# ======================================================================
# FolderPage.jsx
# ======================================================================
fol0 = read(FOLDER_JSX)
fol = fol0

# --- imports / constant
fol = sub(fol,
          "FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp\n} from 'react-icons/fi';",
          "FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp, FiPaperclip\n} from 'react-icons/fi';",
          "folder: import FiPaperclip")

MS_IMPORT = "import modalStyles from '../../components/common/HardwareModal.module.css';"
fol = sub(fol,
          MS_IMPORT,
          MS_IMPORT + "\n\n"
          "// fix138: every payment needs its receipt scan filed under Payment Receipts.\n"
          "// Set to false to make the receipt optional.\n"
          "const RECEIPT_REQUIRED = true;",
          "folder: RECEIPT_REQUIRED switch")

# --- state
PAY_STATE = "const [payType, setPayType] = useState('TITLE'); const [paying, setPaying] = useState(false);"
fol = sub(fol,
          PAY_STATE,
          PAY_STATE + "\n"
          "    // fix138: receipt for the payment being recorded + the PROBLEM window\n"
          "    const [payReceipt, setPayReceipt] = useState(null);\n"
          "    const payReceiptRef = useRef(null);\n"
          "    useEffect(() => { if (!payModal.open) setPayReceipt(null); }, [payModal.open]);\n"
          "    const [problemModal, setProblemModal] = useState({ open: false, note: '' });\n"
          "    const [probBusy, setProbBusy] = useState(false);",
          "folder: receipt + problem window state")

# --- problem handler (replaces the browser prompt)
OLD_PROBLEM = "const handleToggleProblem = async () => { const was = project.problem; let note = ''; if (!was) { note = window.prompt('Describe the problem (optional):') || ''; } try { await folderPortalService.toggleProblem(id, note); if (!was && note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };"
NEW_PROBLEM = (
    "const runToggleProblem = async (text) => { const was = project.problem; const note = (text || '').trim(); try { await folderPortalService.toggleProblem(id, note); if (!was && note) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); return true; } catch { toast('FLAG FAILED', 'error'); return false; } };\n"
    "    // fix138: flagging opens the Golden Seed PROBLEM window (no browser prompt); clearing stays one click\n"
    "    const handleToggleProblem = () => { if (project.problem) { runToggleProblem(''); } else { setProblemModal({ open: true, note: '' }); } };\n"
    "    const closeProblemModal = () => { if (!probBusy) setProblemModal({ open: false, note: '' }); };\n"
    "    const handleProblemConfirm = async () => { if (probBusy) return; setProbBusy(true); const ok = await runToggleProblem(problemModal.note); setProbBusy(false); if (ok) setProblemModal({ open: false, note: '' }); };"
)
fol = sub(fol, OLD_PROBLEM, NEW_PROBLEM, "folder: PROBLEM handler uses a window, not window.prompt")

# --- payment: require receipt, then file it under Payment Receipts
fol = sub(fol,
          "if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }\n        setPaying(true);",
          "if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }\n"
          "        if (RECEIPT_REQUIRED && !payReceipt) { toast('ATTACH THE PAYMENT RECEIPT', 'error'); return; }\n"
          "        setPaying(true);",
          "folder: payment needs a receipt")

fol = sub(fol,
          "await recoveryService.recordPayment(id, payAmount, fullNotes);\n"
          "            await loadFolderData(); setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE');\n"
          "            toast('Payment recorded successfully', 'success');",
          "await recoveryService.recordPayment(id, payAmount, fullNotes);\n"
          "            // fix138: file the receipt in Documents > Payment Receipts (payment is already saved at this point)\n"
          "            let receiptOk = true;\n"
          "            if (payReceipt) {\n"
          "                try {\n"
          "                    const ext = (payReceipt.name.match(/\\.[A-Za-z0-9]{1,6}$/) || [''])[0];\n"
          "                    const stamp = new Date().toISOString().slice(0, 10);\n"
          "                    const receiptName = 'Receipt - ' + (payType === 'STORAGE' ? 'Storage Fee' : 'Title Payment') + ' - UGX ' + Number(payAmount) + ' - ' + stamp + ext;\n"
          "                    await landService.addExtraDocuments(id, [new File([payReceipt], receiptName, { type: payReceipt.type })], ['PAYMENT_RECEIPT']);\n"
          "                } catch { receiptOk = false; }\n"
          "            }\n"
          "            await loadFolderData(); setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE');\n"
          "            if (receiptOk) toast(payReceipt ? 'Payment recorded. Receipt filed under Payment Receipts.' : 'Payment recorded successfully', 'success', 4500);\n"
          "            else toast('Payment recorded, but the RECEIPT DID NOT UPLOAD. Add it from Documents > Payment Receipts.', 'warn', 9000);",
          "folder: upload the receipt after the payment saves")

# --- payment window: receipt field (after the notes box)
PAY_NOTES_TA = "<textarea className={modalStyles.modalTextarea} value={payNotes} onChange={e => setPayNotes(e.target.value)} /></div>"
fol = sub(fol,
          PAY_NOTES_TA,
          PAY_NOTES_TA + "\n"
          "                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>PAYMENT RECEIPT{RECEIPT_REQUIRED ? ' (REQUIRED)' : ' (OPTIONAL)'}</label>\n"
          "                    <input ref={payReceiptRef} type=\"file\" accept=\".pdf,.jpg,.jpeg,.png,.webp\" style={{ display: 'none' }} aria-hidden=\"true\" tabIndex={-1} onChange={e => { const f = e.target.files && e.target.files[0]; if (f) setPayReceipt(f); e.target.value = ''; }} />\n"
          "                    {payReceipt ? (<div className={styles.recFile}><FiFileText aria-hidden=\"true\" /><span className={styles.recName} title={payReceipt.name}>{payReceipt.name}</span><button type=\"button\" className={styles.recRemove} onClick={() => setPayReceipt(null)} aria-label=\"Remove receipt\"><FiX aria-hidden=\"true\" /></button></div>)\n"
          "                        : (<button type=\"button\" className={styles.addDocBtn} onClick={() => payReceiptRef.current && payReceiptRef.current.click()}><FiPaperclip aria-hidden=\"true\" />&nbsp;ATTACH RECEIPT SCAN</button>)}\n"
          "                    <span className={styles.recHint}>Saved in this folder's Documents under Payment Receipts.</span></div>",
          "folder: receipt field in the RECORD PAYMENT window")

# --- the PROBLEM window (before the back-to-top button)
TOP_BTN = "{showTopBtn && (<button type=\"button\" className={styles.scrollTopBtn}"
PROBLEM_MODAL = (
    "<HardwareModal isOpen={problemModal.open} onClose={closeProblemModal} title={'FLAG PROBLEM - ' + (project.landTitle?.plotNumber || project.projectIndex || 'FOLDER')}>\n"
    "                <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>This flags the plot as a <strong>PROBLEM</strong> and notifies staff. What you write below goes into the notes and the audit trail.</div>\n"
    "                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>WHAT IS THE PROBLEM? (OPTIONAL)</label>\n"
    "                    <textarea className={`${modalStyles.modalTextarea} ${styles.probBox}`} value={problemModal.note} maxLength={500} autoFocus placeholder=\"e.g. Owner name on the deed plan does not match the ID...\" aria-label=\"Problem description\" onChange={e => setProblemModal(m => ({ ...m, note: e.target.value }))} />\n"
    "                    <span className={styles.probCount}>{problemModal.note.length}/500</span></div>\n"
    "                <div className={modalStyles.modalFooter}>\n"
    "                    <button type=\"button\" className={modalStyles.modalBtnSecondary} onClick={closeProblemModal} disabled={probBusy}>CANCEL</button>\n"
    "                    <HardwareButton type=\"button\" variant=\"danger\" onClick={handleProblemConfirm} loading={probBusy} icon={FiAlertTriangle}>FLAG PROBLEM</HardwareButton>\n"
    "                </div>\n"
    "            </HardwareModal>\n"
    "            "
)
fol = sub(fol, TOP_BTN, PROBLEM_MODAL + TOP_BTN, "folder: PROBLEM window")

# ======================================================================
# write (atomic) + build gate + commit
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix137).")
    sys.exit(1)

changed = False
for path, text, label in REWRITES:
    write(path, text)
    print("written: " + label)
    changed = True

for path, before, after, label in [
    (FOLDER_JSX, fol0, fol, "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"),
    (FOLDER_CSS, css0, css, "erp-frontend/src/pages/DigitalFolder/FolderPage.module.css"),
]:
    if after != before:
        write(path, after)
        print("written: " + label)
        changed = True
if not changed:
    print("note: nothing changed -- fix138 already applied")

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
git("commit", "-m", "fix138: upload window dropdown uses the app's white + orange-hover list; every payment needs a receipt scan filed under Payment Receipts; PROBLEM button opens a styled window for what the problem is")
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