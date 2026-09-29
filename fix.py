#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix150: Settings inner boxes a touch darker + Expenses page lightened with the Settings cream-card idea.
#
# 1. Settings > Appearance: the inner boxes that surround each setting's text (.prefGroupBox .prefRow)
#    go a tiny bit darker -- fill 5% -> 7.5%, border 14% -> 18%, hover 9% -> 12% (navy tint on the cream card).
# 2. Expenses: the two big panels stay navy, but what sits INSIDE them now borrows the Settings
#    light-group look (cream #f2ede4 card, soft navy border, white-ish buttons with orange hover):
#      - LOG AN EXPENSE: the preset buttons sit on a cream card (NEW PRESET stays solid orange)
#      - RECENT ENTRIES: the table sits on a cream card; header row stays navy/orange, body rows are
#        navy text on cream, with darker orange / red text so it stays readable on the light surface.
#    Stat cards, page header, hints and modals are untouched.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix150"
COMMIT_MSG = "fix150: settings inner boxes slightly darker; expenses panels lightened with cream inner cards"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")
TESTJAVA = os.path.join(BACKEND, "src", "test", "java", "com", "gesolutions", "erp")
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")

SETTINGS_CSS = os.path.join(SRC, "pages", "settings", "SettingsPage.module.css")
EXP_CSS = os.path.join(SRC, "pages", "Financials", "ExpensesPage.module.css")
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
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (SETTINGS_CSS, EXP_CSS, GUIDE)
for _p in LOAD_FILES:
    load(_p)

def L(*lines):
    return "\n".join(lines)

# ---- 1. Settings: inner boxes a tiny bit darker ----
patch(SETTINGS_CSS,
      L("  border: 1px solid rgba(26,46,48,0.14); border-radius: 6px;",
        "  background: rgba(26,46,48,0.05);"),
      L("  border: 1px solid rgba(26,46,48,0.18); border-radius: 6px;",
        "  background: rgba(26,46,48,0.075);"),
      "Settings CSS: inner box fill + border a touch darker")
patch(SETTINGS_CSS,
      ".prefGroupBox .prefRow:hover { background: rgba(26,46,48,0.09); border-color: rgba(26,46,48,0.22); }",
      ".prefGroupBox .prefRow:hover { background: rgba(26,46,48,0.12); border-color: rgba(26,46,48,0.26); }",
      "Settings CSS: inner box hover a touch darker")

# ---- 2. Expenses: cream inner cards (Settings light-group idea) ----
patch(EXP_CSS,
      "/* -- RESPONSIVE -- same breakpoints the dossier uses -- */",
      L("/* ================= fix150: LIGHTER INNER SURFACES =================",
        "   Idea taken from Settings > Appearance (.prefGroupBox): the outer panel stays navy, but the",
        "   content sits on a cream #f2ede4 card with a soft navy border. Text on cream is navy; orange /",
        "   red TEXT uses the darker #b45309 / #b91c1c so it keeps its contrast on the light surface.",
        "   Cell rules carry `td.` so they beat `.ledgerTable tbody td` (which sets white). */",
        "",
        "/* LOG AN EXPENSE: the preset buttons live on a cream card */",
        ".presetRow {",
        "  background: #f2ede4; border: 1px solid rgba(26,46,48,0.14);",
        "  border-radius: var(--radius-sm); padding: clamp(10px,1.3vw,14px) clamp(12px,1.5vw,16px);",
        "}",
        ".presetRow .presetBtn, .presetRow .presetBtnOther {",
        "  border: 1.5px solid rgba(26,46,48,0.2); background: rgba(255,255,255,0.65); color: rgba(26,46,48,0.85);",
        "}",
        ".presetRow .presetBtnOther { border-style: dashed; }",
        ".presetRow .presetBtn:hover, .presetRow .presetBtnOther:hover {",
        "  background: rgba(238,140,58,0.16); border-color: #EE8C3A; color: #EE8C3A;",
        "}",
        "",
        "/* RECENT ENTRIES: the table lives on a cream card (header row stays navy + orange) */",
        ".tableScroll { background: #f2ede4; border: 1px solid rgba(26,46,48,0.14); border-radius: var(--radius-sm); }",
        ".ledgerTable tbody td { color: #1a2e30; border-bottom: 1px solid rgba(26,46,48,0.1); }",
        ".ledgerTable tbody tr:last-child td { border-bottom: none; }",
        ".ledgerTable tbody tr.row:hover { background: rgba(26,46,48,0.07); }",
        ".ledgerTable tbody td.dateCell  { color: rgba(26,46,48,0.68); }",
        ".ledgerTable tbody td.moneyCell { color: #b91c1c; }",
        ".ledgerTable tbody td.metaCell  { color: rgba(26,46,48,0.82); }",
        ".ledgerTable tbody td.notesCell { color: rgba(26,46,48,0.72); }",
        ".ledgerTable tbody td.emptyCell { color: rgba(26,46,48,0.7); }",
        ".noNote { color: rgba(26,46,48,0.45); }",
        ".categoryTag { color: #b45309; }",
        ".editedBadge { color: #b45309; }",
        ".spentByTag { color: rgba(26,46,48,0.72); }",
        ".lockedTag { color: rgba(26,46,48,0.66); }",
        ".editIconBtn { background: rgba(238,140,58,0.2); color: #b45309; }",
        ".editIconBtn:hover { background: rgba(238,140,58,0.34); border-color: #EE8C3A; }",
        ".deleteIconBtn { background: rgba(239,68,68,0.14); color: #b91c1c; }",
        ".deleteIconBtn:hover { background: rgba(239,68,68,0.28); border-color: #ef4444; }",
        "",
        "/* -- RESPONSIVE -- same breakpoints the dossier uses -- */"),
      "Expenses CSS: cream inner cards for presets + table")

# ---- 3. guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix149: stat-card hover borders + app-wide skeleton loader, Section 7)",
      "# Last updated: September 2026 (fix150: Settings inner boxes darker + Expenses cream inner cards, Section 7)",
      "Guide: header line")
patch(GUIDE,
      "### Stat-card borders + skeleton loader (fix149)",
      L("### Settings inner boxes + Expenses cream cards (fix150)",
        "- Settings > Appearance: `.prefGroupBox .prefRow` (the boxes around each setting's text) is a navy tint on the cream card: fill 7.5%, border 18%, hover 12%. Nudge these three numbers to go lighter/darker.",
        "- Expenses: the LOG AN EXPENSE preset row and the RECENT ENTRIES table sit on a cream `#f2ede4` card inside the navy panel (the Settings light-group idea). Text on cream is navy; orange/red text is the darker `#b45309` / `#b91c1c`. Table cell colour rules must be written `.ledgerTable tbody td.xCell` or they lose to the white `td` rule. Stat cards and modals stay navy.",
        "",
        "### Stat-card borders + skeleton loader (fix149)"),
      "Guide: fix150 note")

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