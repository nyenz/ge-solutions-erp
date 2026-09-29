#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix148: ledger decor clean-up + one stat-card spec across pages.
#
# 1. Ledger pages: the TOP border pins ("....") are gone from the Project Ledger and the
#    Client Ledger. Payments Records no longer draws the top corner brackets or top pins
#    either (HardwarePanel gets a `hideTop` prop). All three ledgers now carry the same
#    decor: bottom corner brackets + bottom pins only.
# 2. Stat cards match the Payment Records card: solid coloured border, coloured label and
#    value (green / red / cyan / orange), no hover-lift, no drop shadow, same label font.
#    - Recovery Cockpit: TODAY'S CALLS green, MONTH'S CALLS cyan, LONGEST WAIT orange,
#      MONTH'S MISS red (they were all plain white before).
#    - Expenses: PRESETS + CATEGORIES USED cyan; existing green / orange borders now solid.
#    - Client dossier: PROJECTS + OWNERSHIP cyan; existing red / green / orange now solid.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix148"
COMMIT_MSG = "fix148: ledger top decor removed (Ledger, Clients, Payments) + one stat-card spec (Recovery, Expenses, Client dossier)"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")
TESTJAVA = os.path.join(BACKEND, "src", "test", "java", "com", "gesolutions", "erp")
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")

HWPANEL_JSX = os.path.join(SRC, "components", "ui", "HardwarePanel.jsx")
LEDGER_JSX = os.path.join(SRC, "pages", "Ledger", "LedgerPage.jsx")
CLIENTLEDGER_JSX = os.path.join(SRC, "pages", "Clients", "ClientLedgerPage.jsx")
PAY_JSX = os.path.join(SRC, "pages", "Payments", "PaymentsPage.jsx")
RECOVERY_JSX = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.jsx")
RECOVERY_CSS = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.module.css")
EXP_JSX = os.path.join(SRC, "pages", "Financials", "ExpensesPage.jsx")
EXP_CSS = os.path.join(SRC, "pages", "Financials", "ExpensesPage.module.css")
PORTFOLIO_JSX = os.path.join(SRC, "pages", "Clients", "ClientPortfolioPage.jsx")
PORTFOLIO_CSS = os.path.join(SRC, "pages", "Clients", "ClientPortfolioPage.module.css")
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
LOAD_FILES = (HWPANEL_JSX, LEDGER_JSX, CLIENTLEDGER_JSX, PAY_JSX,
              RECOVERY_JSX, RECOVERY_CSS, EXP_JSX, EXP_CSS,
              PORTFOLIO_JSX, PORTFOLIO_CSS, GUIDE)
for _p in LOAD_FILES:
    load(_p)

def L(*lines):
    return "\n".join(lines)

# ---- 1. Project Ledger + Client Ledger: no top pins ----
# (bottom pins and both bottom corner brackets stay)
for _path, _name in ((LEDGER_JSX, "Ledger"), (CLIENTLEDGER_JSX, "Clients")):
    patch(_path,
          L("data-tab-accent={accentOf(FILTERS, activeFilter)}>",
            "                <Pins pos=\"top\" />"),
          L("data-tab-accent={accentOf(FILTERS, activeFilter)}>",
            "                {/* fix148: no top pins -- bottom pins + bottom corners only */}"),
          _name + ": top pins removed")

# ---- 2. Payments: HardwarePanel hideTop (no top corners, no top pins) ----
patch(HWPANEL_JSX,
      "const HardwarePanel = ({ title, icon: Icon, children, variant = \"dark\" }) => {",
      "const HardwarePanel = ({ title, icon: Icon, children, variant = \"dark\", hideTop = false }) => {",
      "HardwarePanel: hideTop prop")
patch(HWPANEL_JSX,
      "<CornerDecor hidePins={variant === \"light\"} />",
      "<CornerDecor hidePins={variant === \"light\"} hideTop={hideTop} />",
      "HardwarePanel: pass hideTop to CornerDecor")
patch(PAY_JSX,
      "<HardwarePanel variant=\"dark\">",
      "<HardwarePanel variant=\"dark\" hideTop>",
      "Payments: table panel without top decor")

# ---- 3. Recovery: stat cards use the Payment Records spec ----
patch(RECOVERY_JSX,
      "<div className={styles.countCard}><label>TODAY'S CALLS</label>",
      "<div className={`${styles.countCard} ${styles.statGreen}`}><label>TODAY'S CALLS</label>",
      "Recovery: TODAY'S CALLS green")
patch(RECOVERY_JSX,
      "<div className={styles.countCard}><label>MONTH'S CALLS</label>",
      "<div className={`${styles.countCard} ${styles.statCyan}`}><label>MONTH'S CALLS</label>",
      "Recovery: MONTH'S CALLS cyan")
patch(RECOVERY_JSX,
      "<div className={styles.countCard}><label>LONGEST WAIT</label>",
      "<div className={`${styles.countCard} ${styles.statAmber}`}><label>LONGEST WAIT</label>",
      "Recovery: LONGEST WAIT orange")
patch(RECOVERY_JSX,
      "<div className={styles.countCard}><label>MONTH'S MISS</label>",
      "<div className={`${styles.countCard} ${styles.statRed}`}><label>MONTH'S MISS</label>",
      "Recovery: MONTH'S MISS red")
# .countsHUD .countCard (2 classes) out-ranks every earlier single-class .countCard rule
patch(RECOVERY_CSS,
      ".countsHUD   { margin: 0; }",
      L(".countsHUD   { margin: 0; }",
        "",
        "/* fix148: count cards = the Payment Records stat card. No drop shadow, no hover-lift,",
        "   same label type; colour comes from statGreen / statCyan / statAmber / statRed. */",
        ".countsHUD .countCard { box-shadow: none; transform: none; }",
        ".countsHUD .countCard:hover { transform: none; border-color: var(--orange-border); }",
        ".countsHUD .countCard label { font-family: 'DM Sans', sans-serif; letter-spacing: 1px; color: rgba(255,255,255,0.5); }",
        ".countsHUD .statGreen, .countsHUD .statGreen:hover { border-color: #22c55e; }",
        ".countsHUD .statGreen label, .countsHUD .statGreen strong { color: #22c55e; }",
        ".countsHUD .statCyan, .countsHUD .statCyan:hover { border-color: #06b6d4; }",
        ".countsHUD .statCyan label, .countsHUD .statCyan strong { color: #06b6d4; }",
        ".countsHUD .statAmber, .countsHUD .statAmber:hover { border-color: var(--orange); }",
        ".countsHUD .statAmber label, .countsHUD .statAmber strong { color: var(--orange); }",
        ".countsHUD .statRed, .countsHUD .statRed:hover { border-color: #ef4444; }",
        ".countsHUD .statRed label, .countsHUD .statRed strong { color: #ef4444; }"),
      "Recovery CSS: count card spec + colours")

# ---- 4. Expenses: cyan on the two plain cards, solid borders ----
patch(EXP_JSX,
      L("<div className={styles.statCard}>", "                    <label>PRESETS</label>"),
      L("<div className={`${styles.statCard} ${styles.statCyan}`}>", "                    <label>PRESETS</label>"),
      "Expenses: PRESETS cyan")
patch(EXP_JSX,
      L("<div className={styles.statCard}>", "                    <label>CATEGORIES USED</label>"),
      L("<div className={`${styles.statCard} ${styles.statCyan}`}>", "                    <label>CATEGORIES USED</label>"),
      "Expenses: CATEGORIES USED cyan")
patch(EXP_CSS,
      ".statAmber { border-color: rgba(238,140,58,0.55); }",
      ".statAmber { border-color: var(--orange); }",
      "Expenses CSS: amber border solid")
patch(EXP_CSS,
      L(".statGreen { border-color: rgba(34,197,94,0.55); }",
        ".statGreen label, .statGreen strong { color: #22c55e; }"),
      L(".statGreen { border-color: #22c55e; }",
        ".statGreen label, .statGreen strong { color: #22c55e; }",
        ".statCyan { border-color: #06b6d4; }",
        ".statCyan label, .statCyan strong { color: #06b6d4; }"),
      "Expenses CSS: green solid + cyan")

# ---- 5. Client dossier: cyan on the two plain cards, solid borders ----
patch(PORTFOLIO_JSX,
      L("          <div className={`${styles.statCard} ${styles.statClickable}`} role=\"button\" tabIndex={0}",
        "            onClick={() => scrollToSection('portfolio-panel')}",
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>",
        "            <label>PROJECTS</label>"),
      L("          <div className={`${styles.statCard} ${styles.statCyan} ${styles.statClickable}`} role=\"button\" tabIndex={0}",
        "            onClick={() => scrollToSection('portfolio-panel')}",
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>",
        "            <label>PROJECTS</label>"),
      "Dossier: PROJECTS cyan")
patch(PORTFOLIO_JSX,
      L("          <div className={`${styles.statCard} ${styles.statClickable}`} role=\"button\" tabIndex={0}",
        "            onClick={() => scrollToSection('portfolio-panel')}",
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>",
        "            <label>OWNERSHIP</label>"),
      L("          <div className={`${styles.statCard} ${styles.statCyan} ${styles.statClickable}`} role=\"button\" tabIndex={0}",
        "            onClick={() => scrollToSection('portfolio-panel')}",
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>",
        "            <label>OWNERSHIP</label>"),
      "Dossier: OWNERSHIP cyan")
patch(PORTFOLIO_CSS,
      ".statRed   { border-color: rgba(239,68,68,0.55); }",
      ".statRed   { border-color: #ef4444; }",
      "Dossier CSS: red border solid")
patch(PORTFOLIO_CSS,
      ".statAmber { border-color: rgba(238,140,58,0.55); }",
      ".statAmber { border-color: var(--orange); }",
      "Dossier CSS: amber border solid")
patch(PORTFOLIO_CSS,
      L(".statGreen { border-color: rgba(34,197,94,0.55); }",
        ".statGreen label, .statGreen strong { color: #22c55e; }"),
      L(".statGreen { border-color: #22c55e; }",
        ".statGreen label, .statGreen strong { color: #22c55e; }",
        ".statCyan  { border-color: #06b6d4; }",
        ".statCyan  label, .statCyan  strong { color: #06b6d4; }"),
      "Dossier CSS: green solid + cyan")

# ---- 6. guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix147: selection-based tab + panel accent colours, Section 7)",
      "# Last updated: September 2026 (fix148: ledger top decor removed + one stat-card spec, Section 7)",
      "Guide: header line")
patch(GUIDE,
      "### Selection-based accent colours (fix147)",
      L("### Ledger decor + stat cards (fix148)",
        "- Ledger tables (Project Ledger, Client Ledger, Payment Records) carry bottom corner brackets + bottom pins ONLY. No top pins, no top corners. `HardwarePanel` takes `hideTop` (forwarded to `CornerDecor`); Payments passes it. Do not re-add `<Pins pos=\"top\" />` to the two ledger pages.",
        "- One stat-card spec (Payment Records `.sumCard`): 1.5px solid coloured border, label + value in the same colour, no drop shadow, no hover-lift. Palette: green #22c55e, red #ef4444, cyan #06b6d4, orange var(--orange); white/plain only for a neutral grand total. Recovery `.countCard` uses `statGreen | statCyan | statAmber | statRed` (scoped under `.countsHUD`); Expenses and the Client dossier use `.statCard` + `statGreen | statRed | statAmber | statCyan`.",
        "- New stat card: pick a colour class -- do not leave a card white-on-white unless it is a neutral total.",
        "",
        "### Selection-based accent colours (fix147)"),
      "Guide: fix148 note")

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