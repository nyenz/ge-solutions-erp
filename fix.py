#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix161: Folder page wording + feedback: RELEASE / PROBLEM / stage ticks / Financials / Storage.
#
# 1. RELEASE -> HAND OVER TITLE. Greyed out (with the reason on hover) until the title is fully paid, instead of
#    letting you press it and get a hidden "Arrears Detected" error. Done state reads HANDED OVER.
# 2. PROBLEM -> FLAG PROBLEM / CLEAR PROBLEM (the old "PROBLEM v" looked like "all good"). PAYMENT -> RECORD PAYMENT.
# 3. Stage ticks: a hint says they save the instant you click and CANCEL does not undo them; the CANCEL popup says the same.
# 4. Financials: "PLOT VALUE" -> "TOTAL COST" (same word as edit mode), "COMBINED TOTAL" -> "COST + FEES".
# 5. Storage: plain-words buttons, hints, and confirm texts (all three exits also END the receivable).
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix161"
COMMIT_MSG = "fix161: folder page wording (hand over title, flag problem), stage tick hint, financial + storage clarity"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")
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
LOAD_FILES = (FOLDER_JSX, FOLDER_CSS)
for _p in LOAD_FILES:
    load(_p)

J = FOLDER_JSX

# ---- 1. RELEASE -> HAND OVER TITLE ----
patch(J, "confirm('RELEASE TITLE', 'Mark this title as released to the client? This records the handover.', 'warn')",
         "confirm('HAND OVER TITLE', 'Confirm the client has received the title deed. This marks the plot RELEASED and is recorded in the audit log. It cannot be undone from this page.', 'warn')",
         "Release: confirm popup")
patch(J, "toast('Title released.', 'success');", "toast('Title handed over. Plot is now RELEASED.', 'success');", "Release: success toast")
patch(J, "'RELEASE FAILED'", "'HAND OVER FAILED'", "Release: error toast")
patch(J,
"""                            ? <button className={`${styles.releaseBtn} ${styles.releaseBtnDone}`} disabled><FiCheckCircle aria-hidden="true" /> RELEASED</button>
                            : <button className={styles.releaseBtn} onClick={handleRelease}><FiCheckCircle aria-hidden="true" /> RELEASE</button>)}""",
"""                            ? <button className={`${styles.releaseBtn} ${styles.releaseBtnDone}`} disabled title="The client has received the title deed."><FiCheckCircle aria-hidden="true" /> HANDED OVER</button>
                            : <button className={styles.releaseBtn} onClick={handleRelease} disabled={amountPaid < totalValue}
                                title={amountPaid < totalValue ? 'Cannot hand over yet: UGX ' + fmt(totalValue - amountPaid) + ' is still owed.' : 'Record that the client has received the title deed.'}><FiCheckCircle aria-hidden="true" /> HAND OVER TITLE</button>)}""",
"Release: button (greyed until fully paid, reason on hover)")
patch(FOLDER_CSS, ".releaseBtn:hover{background:#06b6d4;color:#1a2e30;}",
      ".releaseBtn:hover:not(:disabled){background:#06b6d4;color:#1a2e30;}\n.releaseBtn:disabled:not(.releaseBtnDone){opacity:0.45;cursor:not-allowed;border-style:dashed;}",
      "Release: greyed-out style")

# ---- 2. PROBLEM + PAYMENT wording ----
patch(J, "onClick={handleToggleProblem}><FiAlertTriangle aria-hidden=\"true\" /> {project.problem ? 'PROBLEM ✓' : 'PROBLEM'}</button>",
         "onClick={handleToggleProblem} title={project.problem ? 'Remove the problem flag from this plot.' : 'Flag this plot as having a problem and alert staff.'}><FiAlertTriangle aria-hidden=\"true\" /> {project.problem ? 'CLEAR PROBLEM' : 'FLAG PROBLEM'}</button>",
         "Problem: button wording")
patch(J, "<FiDollarSign aria-hidden=\"true\" /> PAYMENT</button>", "<FiDollarSign aria-hidden=\"true\" /> RECORD PAYMENT</button>", "Payment: button wording")

# ---- 3. Stage ticks: tell the truth ----
patch(J, "<FiRefreshCw aria-hidden=\"true\" /> RESTORE DEFAULTS</button>\n        </div>)}",
         "<FiRefreshCw aria-hidden=\"true\" /> RESTORE DEFAULTS</button>\n            <span className={styles.inputHint}>Ticks save the moment you click them. CANCEL does not undo them.</span>\n        </div>)}",
         "Stages: save-instantly hint")
patch(J, "confirm('DISCARD CHANGES', 'All unsaved changes will be lost.', 'warn')",
         "confirm('DISCARD CHANGES', 'Unsaved field changes will be lost. Stage ticks are saved the moment you click them, so they stay as they are.', 'warn')",
         "Stages: cancel popup tells the truth")

# ---- 4. Financials: one word for one thing ----
patch(J, "<label>PLOT VALUE</label><strong>UGX {fmt(totalValue)}</strong></div>\n                                <div className={styles.statBox}><label style={{ color: 'var(--fs-red)' }}>+ STORAGE FEES</label>",
         "<label>TOTAL COST</label><strong>UGX {fmt(totalValue)}</strong></div>\n                                <div className={styles.statBox}><label style={{ color: 'var(--fs-red)' }}>+ STORAGE FEES</label>",
         "Financials: receivable card label")
patch(J, "<label>PLOT VALUE</label><strong>UGX {fmt(totalValue)}</strong></div>\n                                <div className={styles.statBox}><label style={{ color: 'var(--fs-green)' }}>PAID</label>",
         "<label>TOTAL COST</label><strong>UGX {fmt(totalValue)}</strong></div>\n                                <div className={styles.statBox}><label style={{ color: 'var(--fs-green)' }}>PAID</label>",
         "Financials: active card label")
patch(J, "<label>COMBINED TOTAL</label>", "<label>COST + FEES</label>", "Financials: storage card label")

# ---- 5. Storage: plain words ----
patch(J, "onClick={() => askReceivable('ENTER')}>+ RECEIVABLES</HardwareButton>", "onClick={() => askReceivable('ENTER')}>MOVE TO RECEIVABLES</HardwareButton>", "Storage: enter button")
patch(J, "Storage fees apply only after a project is moved to receivables.",
         "Receivables = clients who still owe after the work is done. Moving this project there freezes the balance and starts a monthly storage fee (UGX 50,000 unless you set another rate), added every 30 days.",
         "Storage: what receivables means")
patch(J, ">SET ASIDE</HardwareButton>", ">SET ASIDE (KEEP FEES)</HardwareButton>", "Storage: set aside label")
patch(J, "<FiCreditCard aria-hidden=\"true\" /> CAPITALIZE</button>", "<FiCreditCard aria-hidden=\"true\" /> ADD FEES TO COST</button>", "Storage: capitalize label")
patch(J, "<FiTrash2 aria-hidden=\"true\" /> WAIVE</button>\n                                </>)}\n                            </div>",
         "<FiTrash2 aria-hidden=\"true\" /> WAIVE FEES</button>\n                                </>)}\n                            </div>\n                            {canMoney && <div className={styles.inputHint}>SET ASIDE, ADD FEES TO COST and WAIVE FEES each take this project OUT of receivables.</div>}",
         "Storage: waive label + exits hint")
patch(J, "SET_ASIDE: ['SET ASIDE', 'Stop fee accumulation but KEEP the fee record so the client can be re-entered later. Continue?', 'warn'],",
         "SET_ASIDE: ['SET ASIDE', 'Take this project out of receivables and stop new fees. The fee record is KEPT (hidden) so the project can be moved back later. Continue?', 'warn'],",
         "Storage: set aside popup")
patch(J, "CAPITALIZE: ['CAPITALIZE FEES', 'Add accumulated storage fees to the total plot value. Continue?', 'warn'],",
         "CAPITALIZE: ['ADD FEES TO COST', 'Add the accumulated storage fees to the total cost and take this project out of receivables. Continue?', 'warn'],",
         "Storage: capitalize popup")
patch(J, "WAIVE: ['WAIVE FEES', 'Permanently forgive the accumulated storage fees. This cannot be undone. Continue?', 'danger'],",
         "WAIVE: ['WAIVE FEES', 'Permanently forgive the accumulated storage fees and take this project out of receivables. This cannot be undone. Continue?', 'danger'],",
         "Storage: waive popup")
patch(J, "FROZEN UNTIL {String(project.negotiationDeadline).slice(0, 10)}", "FEES PAUSED UNTIL {String(project.negotiationDeadline).slice(0, 10)}", "Storage: paused chip")
patch(J, "<FiUnlock aria-hidden=\"true\" /> UNFREEZE</button>", "<FiUnlock aria-hidden=\"true\" /> RESUME FEES</button>", "Storage: resume button")
patch(J, "onClick={() => askReceivable('SETTINGS')}>CONFIRM FREEZE</HardwareButton>", "onClick={() => askReceivable('SETTINGS')}>PAUSE FEES</HardwareButton>", "Storage: confirm pause")
patch(J, "<FiClock aria-hidden=\"true\" /> FREEZE FEES</button>", "<FiClock aria-hidden=\"true\" /> PAUSE FEES UNTIL A DATE</button>", "Storage: pause button")
patch(J, "toast('Fees unfrozen.', 'info')", "toast('Fees resumed.', 'info')", "Storage: resume toast")
patch(J, "toast('UNFREEZE FAILED', 'error')", "toast('RESUME FAILED', 'error')", "Storage: resume error")
patch(J, ">NEGOTIATION</span>", ">FEES PAUSED</span>", "Header badge: NEGOTIATION -> FEES PAUSED")

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