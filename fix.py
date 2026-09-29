#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix159: basic colours, unsaved-changes popup without the duplicate button, tray = frame dark.
#
# 1. Action colours are simple basics: blue, purple, yellow, cyan, orange, green, pink for the everyday actions;
#    rare actions share one colour per type (red / brown / teal / grey).
# 2. Unsaved-changes popup: the X stays, the KEEP EDITING button is removed (only DISCARD & LEAVE remains).
# 3. The band between the outer border and the inner table is now the frame's own dark colour.
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix159"
COMMIT_MSG = "fix159: basic action colours, unsaved popup keeps X only, tray takes frame dark"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

AUDIT_CSS = os.path.join(SRC, "pages", "Audit", "AuditPage.module.css")
AUDIT_JSX = os.path.join(SRC, "pages", "Audit", "AuditPage.jsx")
MODAL_JSX = os.path.join(SRC, "components", "common", "UnsavedChangesModal.jsx")
AUDIT_CAT = os.path.join(SRC, "pages", "Audit", "auditCatalog.js")
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
LOAD_FILES = (AUDIT_CSS, AUDIT_CAT, MODAL_JSX)
for _p in LOAD_FILES:
    load(_p)

# ---- 1. Simple basic colours ----
CAT_OLD = '/* fix158: colour by how often an action happens.\n   COMMON  = the actions staff do all day. Each one has its OWN obvious colour.\n   RARE    = everything else. Rare actions share a colour per TYPE (severity), so a red row always means\n             "destructive / privileged", amber = "changes money or a record", violet = contact history, slate = minor.\n   Orange is kept out on purpose (the opened readout text is orange). An unlisted code counts as rare / minor. */\nconst COMMON_COLOR = {\n    RECORD_UPDATED:          \'#3b82f6\',  // blue\n    EDIT_MODE_OPENED:        \'#ec4899\',  // pink\n    DOCUMENT_UPLOADED:       \'#06b6d4\',  // cyan\n    DOCUMENT_CATEGORY_ADDED: \'#84cc16\',  // lime\n    RECEIVABLE_ENTER:        \'#d946ef\',  // fuchsia\n    PAYMENT_RECORDED:        \'#22c55e\',  // green\n    EXPENSE_LOGGED:          \'#6366f1\',  // indigo\n    RECOVERY_NOTE:           \'#14b8a6\',  // teal\n};\nconst RARE_COLOR = {\n    high:  \'#ef4444\',  // red    -- destructive / privileged\n    med:   \'#f59e0b\',  // amber  -- changes money or a record\n    intel: \'#a78bfa\',  // violet -- contact history\n    low:   \'#64748b\',  // slate  -- minor\n};\nexport const actionColor = (code) => {\n    const key = String(code || \'\');\n    if (COMMON_COLOR[key]) return COMMON_COLOR[key];\n    return RARE_COLOR[severityOf(key)] || RARE_COLOR.low;\n};\n'
CAT_NEW = "/* fix159: simple basic colours. Colour by how often an action happens.\n   COMMON = the actions staff do all day, each with its OWN basic colour (blue, green, yellow, purple, orange, cyan, pink).\n   RARE   = everything else, one shared colour per TYPE: red = destructive / privileged, brown = changes money or a\n            record, teal = contact history, grey = minor. An unlisted code counts as rare / minor. */\nconst COMMON_COLOR = {\n    RECORD_UPDATED:          '#2563eb',  // blue\n    EDIT_MODE_OPENED:        '#9333ea',  // purple\n    DOCUMENT_UPLOADED:       '#eab308',  // yellow\n    DOCUMENT_CATEGORY_ADDED: '#06b6d4',  // cyan\n    RECEIVABLE_ENTER:        '#f97316',  // orange\n    PAYMENT_RECORDED:        '#16a34a',  // green\n    EXPENSE_LOGGED:          '#ec4899',  // pink\n};\nconst RARE_COLOR = {\n    high:  '#dc2626',  // red\n    med:   '#92400e',  // brown\n    intel: '#0d9488',  // teal\n    low:   '#6b7280',  // grey\n};\nexport const actionColor = (code) => {\n    const key = String(code || '');\n    if (COMMON_COLOR[key]) return COMMON_COLOR[key];\n    return RARE_COLOR[severityOf(key)] || RARE_COLOR.low;\n};\n"
patch(AUDIT_CAT, CAT_OLD, CAT_NEW, "Catalogue: simple basic colours")

# ---- 2. The band between the outer border and the inner table = the frame's own dark ----
patch(AUDIT_CSS,
      ".logTray { background: #c6bba4; padding: 10px;",
      ".logTray { background: transparent; padding: 10px;",
      "Audit CSS: tray takes the dark of the outer frame")

# ---- 3. Unsaved-changes popup: X stays, KEEP EDITING button goes ----
patch(MODAL_JSX,
      "import { FiAlertTriangle, FiSave, FiLogOut, FiX } from 'react-icons/fi';",
      "import { FiAlertTriangle, FiLogOut, FiX } from 'react-icons/fi';",
      "Modal: drop unused FiSave import")
patch(MODAL_JSX,
      " * The two buttons are real decisions (leave / stay), not a CANCEL, so DESIGN RULE 1 still holds.",
      " * fix159: the KEEP EDITING button is gone (it duplicated the X). The only button left is DISCARD & LEAVE.",
      "Modal: header note")
patch(MODAL_JSX,
      "onClick={onStay} aria-label=\"Close and keep editing\">",
      "onClick={onStay} autoFocus aria-label=\"Close and keep editing\">",
      "Modal: X takes the default focus (safe choice)")
patch(MODAL_JSX,
      "DISCARD &amp; LEAVE\n                    </button>\n                    <button className={modal.modalBtnPrimary} onClick={onStay} autoFocus\n                        aria-label=\"Stay on page and keep editing\">\n                        <FiSave aria-hidden=\"true\" /> KEEP EDITING\n                    </button>\n                </div>\n\n                <div className={modal.footerGlow} />",
      "DISCARD &amp; LEAVE\n                    </button>\n                </div>\n\n                <div className={modal.footerGlow} />",
      "Modal: remove KEEP EDITING button")

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