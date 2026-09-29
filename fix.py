#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix154: Audit opened row takes the Report Catalogue orange.
#
# 1. Opened audit row (head AND "FORENSIC DATA READOUT" part) is the catalogue's active-row orange #EE8C3A.
#    Same look as "NEW TITLES ENTERED" in the Report Catalogue: white head text on orange.
# 2. The readout part (label + text) is navy #1a2e30 so it stays readable on the orange.
# 3. Left action-colour rail is untouched.
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix154"
COMMIT_MSG = "fix154: audit opened row + readout use the report catalogue orange"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

AUDIT_CSS = os.path.join(SRC, "pages", "Audit", "AuditPage.module.css")
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
LOAD_FILES = (AUDIT_CSS,)
for _p in LOAD_FILES:
    load(_p)

def L(*lines):
    return "\n".join(lines)

CSS_OLD_OPEN = L(
"/* OPEN ROW: head and readout are the SAME dark (#1a2e30), no wash, no seam */",
".logRow.expanded, .logRow.expanded:hover { background: #1a2e30; }",
".logRow.expanded .clockPair { color: #fff; }",
".logRow.expanded .clockPair svg { color: #f2ede4; }",
".logRow.expanded .timeMark small { color: #fff; opacity: 0.65; }",
".logRow.expanded .iconChassis { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); color: #f2ede4; }",
".logRow.expanded .actionMeta strong { color: #fff; }",
".logRow.expanded .actionMeta span { color: rgba(255, 255, 255, 0.6); }",
".logRow.expanded .targetMark p { color: #fff; }",
".logRow.expanded .inspectIcon { color: #f2ede4; transform: rotate(180deg); }",
"",
".traceDetails { overflow: hidden; background: #1a2e30; transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1); }",
".traceClosed { max-height: 0; }",
".traceOpen { max-height: clamp(200px, 30vw, 400px); overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.3) transparent; }",
)

CSS_NEW_OPEN = L(
"/* OPEN ROW (fix154): head and readout are the Report Catalogue active-row orange (#EE8C3A), no wash, no seam */",
".logRow.expanded, .logRow.expanded:hover { background: #EE8C3A; }",
".logRow.expanded .clockPair { color: #fff; }",
".logRow.expanded .clockPair svg { color: #fff; }",
".logRow.expanded .timeMark small { color: #fff; opacity: 0.85; }",
".logRow.expanded .iconChassis { background: rgba(255, 255, 255, 0.18); border-color: rgba(255, 255, 255, 0.45); color: #fff; }",
".logRow.expanded .actionMeta strong { color: #fff; }",
".logRow.expanded .actionMeta span { color: rgba(255, 255, 255, 0.88); }",
".logRow.expanded .targetMark p { color: #fff; }",
".logRow.expanded .inspectIcon { color: #fff; transform: rotate(180deg); }",
"",
".traceDetails { overflow: hidden; background: #EE8C3A; transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1); }",
".traceClosed { max-height: 0; }",
".traceOpen { max-height: clamp(200px, 30vw, 400px); overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(26, 46, 48, 0.45) transparent; }",
)

CSS_OLD_RAW = L(
"/* the label takes the action colour; the readout text itself is app orange */",
)
CSS_NEW_RAW = L(
"/* fix154: on the orange readout the label and the text are navy */",
)

RAWHEADER_OLD = "letter-spacing: 2px; text-transform: uppercase; color: var(--rail); }"
RAWHEADER_NEW = "letter-spacing: 2px; text-transform: uppercase; color: #1a2e30; }"

RAWOUT_OLD = "line-height: 1.6; color: #EE8C3A; }"
RAWOUT_NEW = "line-height: 1.6; color: #1a2e30; }"

patch(AUDIT_CSS, CSS_OLD_OPEN, CSS_NEW_OPEN, "Audit CSS: opened row + readout use catalogue orange")
patch(AUDIT_CSS, CSS_OLD_RAW, CSS_NEW_RAW, "Audit CSS: readout comment")
patch(AUDIT_CSS, RAWHEADER_OLD, RAWHEADER_NEW, "Audit CSS: readout label navy")
patch(AUDIT_CSS, RAWOUT_OLD, RAWOUT_NEW, "Audit CSS: readout text navy")

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