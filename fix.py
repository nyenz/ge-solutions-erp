#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix158: Audit list frame polish + colour by frequency.
#
# 1. The band between the outer border and the inner table (the tray) is a bit darker.
# 2. The inner table gets a thin white border.
# 3. Bottom decor like the other tables: corner brackets + the four orange pins on the bottom edge.
# 4. Row colours: the 8 everyday actions each have their own obvious colour; all rare actions share a colour per
#    type (red = destructive/privileged, amber = money/record change, violet = contact history, slate = minor).
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix158"
COMMIT_MSG = "fix158: audit darker tray, white inner border, bottom corner decor, colour by frequency"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

AUDIT_CSS = os.path.join(SRC, "pages", "Audit", "AuditPage.module.css")
AUDIT_JSX = os.path.join(SRC, "pages", "Audit", "AuditPage.jsx")
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
LOAD_FILES = (AUDIT_JSX, AUDIT_CSS, AUDIT_CAT)
for _p in LOAD_FILES:
    load(_p)

# ---- 1. CSS: darker tray, thin white border on the inner card, frame carries the corner decor ----
patch(AUDIT_CSS,
      ".timelineFrame { overflow: hidden; background: var(--panel-bg);",
      ".timelineFrame { position: relative; overflow: visible; background: var(--panel-bg);",
      "Audit CSS: frame can carry corner brackets + bottom pins")
patch(AUDIT_CSS,
      ".logTray { background: #d8cfbd; padding: 10px; }",
      ".logTray { background: #c6bba4; padding: 10px; border-radius: 10px 10px 0 0; }",
      "Audit CSS: tray a bit darker (+ round its top since the frame no longer clips)")
patch(AUDIT_CSS,
      ".logCard { overflow: hidden; background: #ebe5d8; border-radius: 10px; box-shadow: 0 2px 8px rgba(26, 46, 48, 0.2); }",
      ".logCard { overflow: hidden; background: #ebe5d8; border: 1px solid #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(26, 46, 48, 0.2); }",
      "Audit CSS: thin white border round the inner table")
patch(AUDIT_CSS,
      "padding: clamp(8px, 1vw, 11px) clamp(12px, 1.5vw, 18px); background: rgba(0, 0, 0, 0.25); border-top: 1px solid rgba(255, 255, 255, 0.08); }",
      "padding: clamp(10px, 1.2vw, 14px) clamp(22px, 2.4vw, 30px) clamp(14px, 1.6vw, 18px); background: rgba(0, 0, 0, 0.25); border-top: 1px solid rgba(255, 255, 255, 0.08); border-radius: 0 0 10px 10px; }",
      "Audit CSS: footer clear of the corner brackets, rounded bottom")

# ---- 2. JSX: same bottom decor the other tables use (corner brackets + orange pins) ----
patch(AUDIT_JSX,
      "import { actionColor } from './auditCatalog';",
      "import { actionColor } from './auditCatalog';\nimport CornerDecor from '../../components/ui/CornerDecor';",
      "Audit JSX: import CornerDecor")
patch(AUDIT_JSX,
      "                </footer>\n            </div>\n        </div>\n    );\n};",
      "                </footer>\n                <CornerDecor hideTop />\n            </div>\n        </div>\n    );\n};",
      "Audit JSX: bottom corner brackets + pins on the frame")

# ---- 3. Catalogue: own colour for frequent actions, shared type colours for rare ones ----
CAT_OLD = "/* fix153: one colour per action, taken from the app palette only (red, green, cyan, amber, violet; orange is\n   kept out because the opened readout text is orange). Colours are dealt out in catalogue order so neighbours\n   differ; an unlisted code gets a stable colour from its own name. */\nconst PALETTE = ['#ef4444', '#10b981', '#06b6d4', '#f59e0b', '#a78bfa'];\nconst RAIL = {};\nObject.keys(INDEX).forEach((code, i) => { RAIL[code] = PALETTE[i % PALETTE.length]; });\nexport const actionColor = (code) => {\n    const key = String(code || '');\n    if (RAIL[key]) return RAIL[key];\n    let h = 0;\n    for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) % PALETTE.length;\n    return PALETTE[h];\n};\n"
CAT_NEW = '/* fix158: colour by how often an action happens.\n   COMMON  = the actions staff do all day. Each one has its OWN obvious colour.\n   RARE    = everything else. Rare actions share a colour per TYPE (severity), so a red row always means\n             "destructive / privileged", amber = "changes money or a record", violet = contact history, slate = minor.\n   Orange is kept out on purpose (the opened readout text is orange). An unlisted code counts as rare / minor. */\nconst COMMON_COLOR = {\n    RECORD_UPDATED:          \'#3b82f6\',  // blue\n    EDIT_MODE_OPENED:        \'#ec4899\',  // pink\n    DOCUMENT_UPLOADED:       \'#06b6d4\',  // cyan\n    DOCUMENT_CATEGORY_ADDED: \'#84cc16\',  // lime\n    RECEIVABLE_ENTER:        \'#d946ef\',  // fuchsia\n    PAYMENT_RECORDED:        \'#22c55e\',  // green\n    EXPENSE_LOGGED:          \'#6366f1\',  // indigo\n    RECOVERY_NOTE:           \'#14b8a6\',  // teal\n};\nconst RARE_COLOR = {\n    high:  \'#ef4444\',  // red    -- destructive / privileged\n    med:   \'#f59e0b\',  // amber  -- changes money or a record\n    intel: \'#a78bfa\',  // violet -- contact history\n    low:   \'#64748b\',  // slate  -- minor\n};\nexport const actionColor = (code) => {\n    const key = String(code || \'\');\n    if (COMMON_COLOR[key]) return COMMON_COLOR[key];\n    return RARE_COLOR[severityOf(key)] || RARE_COLOR.low;\n};\n'
patch(AUDIT_CAT, CAT_OLD, CAT_NEW, "Catalogue: common actions own colour, rare actions type colour")

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