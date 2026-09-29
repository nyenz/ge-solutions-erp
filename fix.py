#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix147: layout part 2 (selection-based tab + panel accent colours).
#
#   1. TabDock: new `accentOf(items, value)` helper -> the accent of the ACTIVE pill.
#   2. Tab colours (each pill already glows in its own colour when active):
#        Ledger    : PROCESSING amber, TITLED green, LEGACY cyan, RECEIVABLES red,
#                    CRITICAL red, PAID green, PROBLEM red
#        Payments  : TITLE PAYMENT green, INITIAL DEPOSIT cyan, RECEIVABLES red
#        Clients   : OWING amber, IN RECEIVABLES red, CRITICAL red, PAID UP green, NO PROJECTS cyan
#        Recovery  : CONTACTED green, MISSED red, SITE VISIT cyan, LOCKED amber
#   3. Panel accent: the table panel (Ledger, Clients ledger, Payments) and the Recovery
#      cards recolour their border, corner brackets, pins, header text/underline and
#      other orange chrome from the ACTIVE pill, exactly like Settings does with --accent.
#      Done with one global attribute, data-tab-accent, in index.css (it re-points
#      --orange / --orange-border / --orange-dim for that subtree only).
#      ALL / orange pills leave the page looking exactly as it does today.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix147"
COMMIT_MSG = "fix147: layout part 2 - selection-based tab colours + panel accent colours (Ledger, Clients, Payments, Recovery)"
RUN_GATES = True   # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")
TESTJAVA = os.path.join(BACKEND, "src", "test", "java", "com", "gesolutions", "erp")

GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
INDEX_CSS = os.path.join(SRC, "index.css")
TABDOCK_JSX = os.path.join(SRC, "components", "common", "TabDock.jsx")
LEDGER_JSX = os.path.join(SRC, "pages", "Ledger", "LedgerPage.jsx")
CLIENTLEDGER_JSX = os.path.join(SRC, "pages", "Clients", "ClientLedgerPage.jsx")
PAY_JSX = os.path.join(SRC, "pages", "Payments", "PaymentsPage.jsx")
PAY_CSS = os.path.join(SRC, "pages", "Payments", "PaymentsPage.module.css")
RECOVERY_JSX = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.jsx")
RECOVERY_CSS = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.module.css")
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
LOAD_FILES = (INDEX_CSS, TABDOCK_JSX, LEDGER_JSX, CLIENTLEDGER_JSX, PAY_JSX, PAY_CSS,
              RECOVERY_JSX, RECOVERY_CSS, GUIDE)
for _p in LOAD_FILES:
    load(_p)


def L(*lines):
    return "\n".join(lines)


IMPORT_OLD = "import TabDock from '../../components/common/TabDock';"
IMPORT_NEW = "import TabDock, { accentOf } from '../../components/common/TabDock';"

# ---- 1. global accent attribute (index.css) ----
patch(INDEX_CSS,
      L(":root {", "    --cream: #F4F2EF;"),
      L("/* fix147: selection-based panel accent. Put data-tab-accent=\"green|red|yellow|cyan\" on a",
        "   panel and everything inside that uses var(--orange) / var(--orange-border) / var(--orange-dim)",
        "   recolours -- the same idea as Settings' --accent. No attribute (orange) = unchanged. */",
        "[data-tab-accent=\"green\"]  { --orange: #34d399; --orange-dim: rgba(52,211,153,0.18);  --orange-border: rgba(52,211,153,0.36); }",
        "[data-tab-accent=\"red\"]    { --orange: #ef4444; --orange-dim: rgba(239,68,68,0.18);   --orange-border: rgba(239,68,68,0.36); }",
        "[data-tab-accent=\"yellow\"] { --orange: #eab308; --orange-dim: rgba(234,179,8,0.18);   --orange-border: rgba(234,179,8,0.36); }",
        "[data-tab-accent=\"cyan\"]   { --orange: #22d3ee; --orange-dim: rgba(34,211,238,0.18);  --orange-border: rgba(34,211,238,0.36); }",
        "",
        ":root {",
        "    --cream: #F4F2EF;"),
      "index.css: data-tab-accent colour sets")

# ---- 2. TabDock helper ----
patch(TABDOCK_JSX,
      "export default TabDock;",
      L("// fix147: accent of the ACTIVE pill, for tinting the panel below it.",
        "// 'orange' (or no accent) -> undefined, so the panel keeps its normal look.",
        "export const accentOf = (items, value) => {",
        "    const a = (items.find((i) => i.key === value) || {}).accent;",
        "    return a && a !== 'orange' ? a : undefined;",
        "};",
        "",
        "export default TabDock;"),
      "TabDock: accentOf helper")

# ---- 3. Ledger ----
patch(LEDGER_JSX, IMPORT_OLD, IMPORT_NEW, "Ledger: import accentOf")
patch(LEDGER_JSX, "{ key: 'BACKLOG', label: 'PROCESSING' }",
      "{ key: 'BACKLOG', label: 'PROCESSING', accent: 'yellow' }", "Ledger: PROCESSING amber")
patch(LEDGER_JSX, "{ key: 'TITLED', label: 'TITLED' }",
      "{ key: 'TITLED', label: 'TITLED', accent: 'green' }", "Ledger: TITLED green")
patch(LEDGER_JSX, "{ key: 'LEGACY', label: 'LEGACY' }",
      "{ key: 'LEGACY', label: 'LEGACY', accent: 'cyan' }", "Ledger: LEGACY cyan")
patch(LEDGER_JSX, "{ key: 'RECEIVABLES', label: 'RECEIVABLES' }",
      "{ key: 'RECEIVABLES', label: 'RECEIVABLES', accent: 'red' }", "Ledger: RECEIVABLES red")
patch(LEDGER_JSX, "{ key: 'PAID', label: 'PAID' }",
      "{ key: 'PAID', label: 'PAID', accent: 'green' }", "Ledger: PAID green")
patch(LEDGER_JSX, "<div className={styles.tablePanel}>",
      "<div className={styles.tablePanel} data-tab-accent={accentOf(FILTERS, activeFilter)}>",
      "Ledger: panel follows active pill")

# ---- 4. Clients ledger ----
patch(CLIENTLEDGER_JSX, IMPORT_OLD, IMPORT_NEW, "Clients: import accentOf")
patch(CLIENTLEDGER_JSX, "{ key: 'OWING', label: 'OWING' }",
      "{ key: 'OWING', label: 'OWING', accent: 'yellow' }", "Clients: OWING amber")
patch(CLIENTLEDGER_JSX, "{ key: 'RECEIVABLES', label: 'IN RECEIVABLES' }",
      "{ key: 'RECEIVABLES', label: 'IN RECEIVABLES', accent: 'red' }", "Clients: IN RECEIVABLES red")
patch(CLIENTLEDGER_JSX, "{ key: 'PAID', label: 'PAID UP' }",
      "{ key: 'PAID', label: 'PAID UP', accent: 'green' }", "Clients: PAID UP green")
patch(CLIENTLEDGER_JSX, "{ key: 'NOPLOTS', label: 'NO PROJECTS' }",
      "{ key: 'NOPLOTS', label: 'NO PROJECTS', accent: 'cyan' }", "Clients: NO PROJECTS cyan")
patch(CLIENTLEDGER_JSX, "<div className={styles.tablePanel}>",
      "<div className={styles.tablePanel} data-tab-accent={accentOf(FILTERS, activeFilter)}>",
      "Clients: panel follows active pill")

# ---- 5. Payments ----
patch(PAY_JSX, IMPORT_OLD, IMPORT_NEW, "Payments: import accentOf")
patch(PAY_JSX, "label: TYPE_LABELS.STANDARD.toUpperCase() }",
      "label: TYPE_LABELS.STANDARD.toUpperCase(), accent: 'green' }", "Payments: TITLE PAYMENT green")
patch(PAY_JSX, "label: TYPE_LABELS.INITIAL_DEPOSIT.toUpperCase() }",
      "label: TYPE_LABELS.INITIAL_DEPOSIT.toUpperCase(), accent: 'cyan' }", "Payments: INITIAL DEPOSIT cyan")
patch(PAY_JSX,
      L("                <div>", "                <HardwarePanel variant=\"dark\">"),
      L("                <div className={styles.accentWrap} data-tab-accent={accentOf(TYPE_FILTERS, typeFilter)}>",
        "                <HardwarePanel variant=\"dark\">"),
      "Payments: panel wrapper follows active pill")
patch(PAY_CSS,
      ".thSortable:hover { background: rgba(238, 140, 58, 0.07); color: #fff; }",
      L(".thSortable:hover { background: rgba(238, 140, 58, 0.07); color: #fff; }",
        "",
        "/* fix147: HardwarePanel hard-codes its orange border, so re-point it from the active pill */",
        ".accentWrap[data-tab-accent] > section[class] { border-color: var(--orange-border); }",
        ".accentWrap[data-tab-accent] > section[class]:hover { border-color: var(--orange); }",
        ".accentWrap[data-tab-accent] .thSortable:hover { background: var(--orange-dim); }"),
      "Payments CSS: panel border from active pill")

# ---- 6. Recovery ----
patch(RECOVERY_JSX, IMPORT_OLD, IMPORT_NEW, "Recovery: import accentOf")
patch(RECOVERY_JSX, "{ key: 'CONTACTED', label: 'CONTACTED' }",
      "{ key: 'CONTACTED', label: 'CONTACTED', accent: 'green' }", "Recovery: CONTACTED green")
patch(RECOVERY_JSX, "{ key: 'MISSED', label: 'MISSED' }",
      "{ key: 'MISSED', label: 'MISSED', accent: 'red' }", "Recovery: MISSED red")
patch(RECOVERY_JSX, "{ key: 'SITE', label: 'SITE VISIT' }",
      "{ key: 'SITE', label: 'SITE VISIT', accent: 'cyan' }", "Recovery: SITE VISIT cyan")
patch(RECOVERY_JSX, "{ key: 'LOCKED', label: 'LOCKED' }",
      "{ key: 'LOCKED', label: 'LOCKED', accent: 'yellow' }", "Recovery: LOCKED amber")
patch(RECOVERY_JSX,
      "items={TABS.map((t) => ({ key: t.key, label: t.label, count: counts ? counts[t.key] : '-' }))}",
      "items={TABS.map((t) => ({ key: t.key, label: t.label, accent: t.accent, count: counts ? counts[t.key] : '-' }))}",
      "Recovery: pass accent to TabDock")
patch(RECOVERY_JSX,
      "<div className={`${styles.list} ${loading ? styles.refreshing : ''}`}>",
      "<div className={`${styles.list} ${loading ? styles.refreshing : ''}`} data-tab-accent={accentOf(TABS, tab)}>",
      "Recovery: card list follows active pill")
patch(RECOVERY_CSS,
      ".list        { margin: 0; }",
      L(".list        { margin: 0; }",
        "",
        "/* fix147: the cards' border is hard-coded orange in the rules above, so re-point it from the active pill */",
        ".list[data-tab-accent] .rowCard { border-color: var(--orange-border); }",
        ".list[data-tab-accent] .rowCard:hover, .list[data-tab-accent] .rowOpen { border-color: var(--orange); }"),
      "Recovery CSS: card border from active pill")

# ---- 7. guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix145: design pass -- TabDock + page rhythm, Section 7)",
      "# Last updated: September 2026 (fix147: selection-based tab + panel accent colours, Section 7)",
      "Guide: header line")
patch(GUIDE,
      "### Table scroll + dot legend (fix146)",
      L("### Selection-based accent colours (fix147)",
        "- Each TabDock item can carry `accent` (`red` | `green` | `yellow` | `cyan`; orange = default). Current map: green = TITLED / PAID / PAID UP / TITLE PAYMENT / CONTACTED; red = CRITICAL / PROBLEM / RECEIVABLES / MISSED; amber = PROCESSING / OWING / LOCKED; cyan = LEGACY / NO PROJECTS / INITIAL DEPOSIT / SITE VISIT.",
        "- The panel under the tabs follows the ACTIVE pill: `data-tab-accent={accentOf(ITEMS, value)}` on the panel (`accentOf` is exported from `TabDock.jsx`; it returns `undefined` for orange). The four attribute rules in `index.css` re-point `--orange`, `--orange-border` and `--orange-dim` for that subtree only, so border, corner brackets, pins, header text/underline and anything using `var(--orange)` recolour together -- same idea as Settings' `--accent`. Hard-coded orange (rgba(238,140,58,..)) does NOT follow; use the variables in new CSS. Payments wraps `HardwarePanel` in `.accentWrap` and Recovery tints `.list .rowCard`, because their borders are hard-coded.",
        "- New page with a TabDock: give the items accents, then put `data-tab-accent` on the panel below it.",
        "",
        "### Table scroll + dot legend (fix146)"),
      "Guide: accent colours note")
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