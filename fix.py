#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix146: layout part 1 (Payments controls + dots, legend spacing, shared table scroll).
#
#   1. Payments: search box and TabDock filters now sit on ONE line (like Recovery).
#   2. Payments: new dots legend (title / deposit / receivables) + a dot in each row's Type cell.
#   3. Dot legends on Ledger, Clients ledger, Recovery and Payments start a little inside the
#      left edge and have more room before the table (two tokens in index.css).
#   4. The Project Ledger scroll behaviour is now a shared hook (useTableScrollHandoff) and
#      applied to Payments, Client portfolio (both tables) and Expenses (recent entries):
#      table scrolls in its own box, header pinned to that box, page-first-down / table-first-up.
#
# NOT in this fix: tab colours + panel accent colours (that is part 2).
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix146"
COMMIT_MSG = "fix146: layout part 1 - payments search+tabs one line + dots legend, legend inset/spacing, shared table scroll behaviour"
RUN_GATES = True   # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")
TESTJAVA = os.path.join(BACKEND, "src", "test", "java", "com", "gesolutions", "erp")

GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
INDEX_CSS = os.path.join(SRC, "index.css")
HOOK = os.path.join(SRC, "hooks", "useTableScrollHandoff.js")
PAY_JSX = os.path.join(SRC, "pages", "Payments", "PaymentsPage.jsx")
PAY_CSS = os.path.join(SRC, "pages", "Payments", "PaymentsPage.module.css")
LEDGER_CSS = os.path.join(SRC, "pages", "Ledger", "LedgerPage.module.css")
CLIENTLEDGER_CSS = os.path.join(SRC, "pages", "Clients", "ClientLedgerPage.module.css")
RECOVERY_CSS = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.module.css")
PORT_JSX = os.path.join(SRC, "pages", "Clients", "ClientPortfolioPage.jsx")
PORT_CSS = os.path.join(SRC, "pages", "Clients", "ClientPortfolioPage.module.css")
EXP_JSX = os.path.join(SRC, "pages", "Financials", "ExpensesPage.jsx")
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
LOAD_FILES = (INDEX_CSS, PAY_JSX, PAY_CSS, LEDGER_CSS, CLIENTLEDGER_CSS, RECOVERY_CSS,
              PORT_JSX, PORT_CSS, EXP_JSX, EXP_CSS, GUIDE)
for _p in LOAD_FILES:
    load(_p)


def L(*lines):
    return "\n".join(lines)


# ---- 1. shared scroll hook (the Ledger behaviour, as a reusable callback ref) ----
newfile(HOOK,
        L(
            "// PATH: erp-frontend/src/hooks/useTableScrollHandoff.js",
            "// fix146: the Project Ledger scroll behaviour as ONE shared hook.",
            "//   scrolling DOWN -> the page scrolls first, the table takes over at the page bottom",
            "//   scrolling UP   -> the table scrolls first, the page takes over at the table top",
            "// Usage:  const tableRef = useTableScrollHandoff();  <div className={styles.tableScroll} ref={tableRef}>",
            "// It is a callback ref, so it also works when the table only appears after loading.",
            "// Pair it with CSS: .tableScroll { max-height; overflow:auto; overscroll-behavior:contain }",
            "// and a sticky <th> (see LedgerPage.module.css).",
            "import { useCallback, useRef } from 'react';",
            "",
            "function findScrollParent(el) {",
            "    let node = el ? el.parentElement : null;",
            "    while (node && node !== document.body && node !== document.documentElement) {",
            "        const overflowY = window.getComputedStyle(node).overflowY;",
            "        if (overflowY === 'auto' || overflowY === 'scroll') return node;",
            "        node = node.parentElement;",
            "    }",
            "    return document.scrollingElement || document.documentElement;",
            "}",
            "",
            "function attach(tableScroll) {",
            "    const pageScroll = findScrollParent(tableScroll);",
            "    const EDGE_TOLERANCE = 2;",
            "    const MAX_STEP_PX = 120;",
            "    const pageAtTop = () => pageScroll.scrollTop <= EDGE_TOLERANCE;",
            "    const pageAtBottom = () =>",
            "        pageScroll.scrollTop + pageScroll.clientHeight >= pageScroll.scrollHeight - EDGE_TOLERANCE;",
            "    const tableAtTop = () => tableScroll.scrollTop <= EDGE_TOLERANCE;",
            "    const tableAtBottom = () =>",
            "        tableScroll.scrollTop + tableScroll.clientHeight >= tableScroll.scrollHeight - EDGE_TOLERANCE;",
            "    const normalizeWheelDelta = (e) => {",
            "        if (e.deltaMode === 1) return e.deltaY * 16;",
            "        if (e.deltaMode === 2) return e.deltaY * window.innerHeight;",
            "        return e.deltaY;",
            "    };",
            "    const clampStep = (px) => Math.sign(px) * Math.min(Math.abs(px), MAX_STEP_PX);",
            "    const routeDelta = (deltaY, e) => {",
            "        if (deltaY > 0) {",
            "            if (!pageAtBottom()) { pageScroll.scrollTop += clampStep(deltaY); e.preventDefault(); return; }",
            "            if (tableAtBottom()) return;",
            "            tableScroll.scrollTop += clampStep(deltaY);",
            "            e.preventDefault();",
            "        } else if (deltaY < 0) {",
            "            if (!tableAtTop()) { tableScroll.scrollTop += clampStep(deltaY); e.preventDefault(); return; }",
            "            if (pageAtTop()) return;",
            "            pageScroll.scrollTop += clampStep(deltaY);",
            "            e.preventDefault();",
            "        }",
            "    };",
            "    const handleWheel = (e) => routeDelta(normalizeWheelDelta(e), e);",
            "    let touchLastY = 0;",
            "    const handleTouchStart = (e) => { touchLastY = e.touches[0].clientY; };",
            "    const handleTouchMove = (e) => {",
            "        const currentY = e.touches[0].clientY;",
            "        const deltaY = touchLastY - currentY;",
            "        touchLastY = currentY;",
            "        routeDelta(deltaY, e);",
            "    };",
            "    tableScroll.addEventListener('wheel', handleWheel, { passive: false });",
            "    tableScroll.addEventListener('touchstart', handleTouchStart, { passive: true });",
            "    tableScroll.addEventListener('touchmove', handleTouchMove, { passive: false });",
            "    return () => {",
            "        tableScroll.removeEventListener('wheel', handleWheel);",
            "        tableScroll.removeEventListener('touchstart', handleTouchStart);",
            "        tableScroll.removeEventListener('touchmove', handleTouchMove);",
            "    };",
            "}",
            "",
            "export default function useTableScrollHandoff() {",
            "    const cleanupRef = useRef(null);",
            "    return useCallback((node) => {",
            "        if (cleanupRef.current) { cleanupRef.current(); cleanupRef.current = null; }",
            "        if (node) cleanupRef.current = attach(node);",
            "    }, []);",
            "}",
            "",
        ),
        "shared table scroll hook", "useTableScrollHandoff")

# ---- 2. two shared spacing tokens for the dot legend ----
patch(INDEX_CSS,
      "    --ctl-gap:         10px;\n}",
      L("    --ctl-gap:         10px;",
        "    --legend-inset:    clamp(6px, 1vw, 12px);   /* dot legend starts a little inside the left edge */",
        "    --legend-after:    clamp(8px, 1.2vw, 14px); /* extra breathing room between the dots and the table */",
        "}"),
      "index.css: legend inset + spacing tokens")

# ---- 3. bring back the inset + spacing on Ledger, Clients, Recovery ----
patch(LEDGER_CSS,
      ".legendRow   { margin: 0; padding: 0 0 0 4px; }",
      ".legendRow   { margin: 0 0 var(--legend-after); padding: 0 0 0 var(--legend-inset); }",
      "Ledger: legend inset + spacing before the table")
patch(CLIENTLEDGER_CSS,
      ".legendRow   { margin: 0; padding: 0 0 0 4px; }",
      ".legendRow   { margin: 0 0 var(--legend-after); padding: 0 0 0 var(--legend-inset); }",
      "Clients ledger: legend inset + spacing before the table")
patch(RECOVERY_CSS,
      ".dotLegend   { margin: calc(var(--ctl-gap) - var(--block-gap)) 0 0; padding: 0 0 0 4px; }",
      ".dotLegend   { margin: calc(var(--ctl-gap) - var(--block-gap)) 0 var(--legend-after); padding: 0 0 0 var(--legend-inset); }",
      "Recovery: legend inset + spacing before the list")

# ---- 4. Payments page JSX: search + tabs on one line, dots legend, dot in Type column, scroll hook ----
patch(PAY_JSX,
      "import TabDock from '../../components/common/TabDock';",
      L("import TabDock from '../../components/common/TabDock';",
        "import useTableScrollHandoff from '../../hooks/useTableScrollHandoff';"),
      "Payments: import scroll hook")
patch(PAY_JSX,
      L("const PaymentsPage = () => {", "    const navigate = useNavigate();"),
      L("const PaymentsPage = () => {", "    const navigate = useNavigate();",
        "    const tableHandoffRef = useTableScrollHandoff();"),
      "Payments: use scroll hook")
patch(PAY_JSX,
      L("            <div className={styles.controlHub}>",
        "                <div className={styles.searchBlock}>"),
      L("            <div className={styles.controlHub}>",
        "                <div className={styles.controlRow}>",
        "                <div className={styles.searchBlock}>"),
      "Payments: open one-line control row")
patch(PAY_JSX,
      L("                <TabDock items={TYPE_FILTERS} value={typeFilter} onChange={setTypeFilter} label=\"Filter by payment type\" />",
        "            </div>"),
      L("                <TabDock className={styles.dockSlot} items={TYPE_FILTERS} value={typeFilter} onChange={setTypeFilter} label=\"Filter by payment type\" />",
        "                </div>",
        "                <div className={styles.legendRow} aria-label=\"Payment type legend\">",
        "                    {Object.entries(TYPE_COLORS).map(([k, c]) => (",
        "                        <span key={k} className={styles.legendItem}>",
        "                            <span className={styles.legendDot} style={{ background: c, boxShadow: `0 0 4px ${c}` }} /> {TYPE_LABELS[k]}",
        "                        </span>",
        "                    ))}",
        "                </div>",
        "            </div>"),
      "Payments: close control row + dots legend")
patch(PAY_JSX,
      "<span className={styles.typeBadge} style={{ color: TYPE_COLORS[pay.paymentType] || '#888' }}>",
      L("<span className={styles.typeBadge} style={{ color: TYPE_COLORS[pay.paymentType] || '#888' }}>",
        "                                                <i className={styles.legendDot} style={{ background: TYPE_COLORS[pay.paymentType] || '#888', boxShadow: `0 0 4px ${TYPE_COLORS[pay.paymentType] || '#888'}` }} aria-hidden=\"true\" />"),
      "Payments: dot in the Type column")
patch(PAY_JSX,
      "<div className={styles.tableScroll}>",
      "<div className={styles.tableScroll} ref={tableHandoffRef}>",
      "Payments: table scroll ref")

# ---- 5. Payments CSS ----
patch(PAY_CSS,
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}"),
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}",
        "",
        "/* == fix146: Recovery-style control row, dots legend, Ledger scroll box == */",
        ".controlRow { display: flex; align-items: center; gap: var(--ctl-gap); min-width: 0; }",
        ".controlRow .searchBlock { flex: 0 0 auto; }",
        ".dockSlot { flex: 1 1 auto; min-width: 0; }",
        "@media (max-width: 640px) {",
        "    .controlRow { flex-direction: column; align-items: stretch; }",
        "    .controlRow .searchBlock { width: 100%; }",
        "    .dockSlot { flex: none; width: 100%; }",
        "}",
        "",
        "/* dots legend: one line, scrolls sideways, sits a little inside, breathes before the table */",
        ".legendRow { display: flex; flex-wrap: nowrap; gap: 14px; margin: 0 0 var(--legend-after); padding: 0 0 0 var(--legend-inset); overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none; }",
        ".legendRow::-webkit-scrollbar { display: none; }",
        ".legendItem { display: flex; align-items: center; gap: 6px; font-size: 10px; font-weight: 700; color: rgba(26, 46, 48, 0.6); white-space: nowrap; flex-shrink: 0; }",
        ".legendDot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }",
        "",
        "/* Ledger table behaviour: table scrolls inside its own box, header pinned to that box */",
        ".tableScroll { max-height: calc(100vh - 220px); min-height: 280px; overflow: auto; overscroll-behavior: contain; overflow-anchor: none; scrollbar-width: none; -ms-overflow-style: none; }",
        ".tableScroll::-webkit-scrollbar { display: none; width: 0; height: 0; }",
        ".ledgerTable th { z-index: 5; box-shadow: 0 1px 0 var(--orange); }"),
      "Payments CSS: control row, legend, scroll box")

# ---- 6. Client portfolio (2 tables) and Expenses (recent entries): same scroll behaviour ----
patch(PORT_JSX,
      "import styles from './ClientPortfolioPage.module.css';",
      L("import styles from './ClientPortfolioPage.module.css';",
        "import useTableScrollHandoff from '../../hooks/useTableScrollHandoff';"),
      "Portfolio: import scroll hook")
patch(PORT_JSX,
      "const ClientPortfolioPage = () => {",
      L("const ClientPortfolioPage = () => {",
        "  const projectTableRef = useTableScrollHandoff();",
        "  const healthTableRef = useTableScrollHandoff();"),
      "Portfolio: use scroll hooks")
patch(PORT_JSX,
      L("        <div className={styles.tableScroll}>", "          <table className={styles.ledgerTable}>"),
      L("        <div className={styles.tableScroll} ref={projectTableRef}>", "          <table className={styles.ledgerTable}>"),
      "Portfolio: project table scroll ref")
patch(PORT_JSX,
      L("          <div className={styles.tableScroll}>", "            <table className={styles.ledgerTable}>"),
      L("          <div className={styles.tableScroll} ref={healthTableRef}>", "            <table className={styles.ledgerTable}>"),
      "Portfolio: health table scroll ref")
patch(PORT_CSS,
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}"),
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}",
        "",
        "/* fix146: same table scroll behaviour as the Project Ledger */",
        ".tableScroll { max-height: calc(100vh - 220px); overflow: auto; overscroll-behavior: contain; overflow-anchor: none; }",
        ".ledgerTable thead th { position: sticky; top: 0; z-index: 5; box-shadow: 0 1px 0 var(--orange); }"),
      "Portfolio CSS: scroll box + sticky header")

patch(EXP_JSX,
      "import styles from './ExpensesPage.module.css';",
      L("import styles from './ExpensesPage.module.css';",
        "import useTableScrollHandoff from '../../hooks/useTableScrollHandoff';"),
      "Expenses: import scroll hook")
patch(EXP_JSX,
      "const ExpensesPage = () => {",
      L("const ExpensesPage = () => {",
        "    const recentTableRef = useTableScrollHandoff();"),
      "Expenses: use scroll hook")
patch(EXP_JSX,
      "<div className={styles.tableScroll}>",
      "<div className={styles.tableScroll} ref={recentTableRef}>",
      "Expenses: table scroll ref")
patch(EXP_CSS,
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}"),
      L("@media (min-width: 481px) {",
        "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
        "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
        "}",
        "",
        "/* fix146: same table scroll behaviour as the Project Ledger */",
        ".tableScroll { max-height: calc(100vh - 220px); overflow: auto; overscroll-behavior: contain; overflow-anchor: none; }",
        ".ledgerTable thead th { position: sticky; top: 0; z-index: 5; box-shadow: 0 1px 0 var(--orange); }"),
      "Expenses CSS: scroll box + sticky header")

# ---- 7. guide note ----
patch(GUIDE,
      "### Table Design Standard",
      L("### Table scroll + dot legend (fix146)",
        "- Every list table scrolls inside its own box: `.tableScroll { max-height: calc(100vh - 220px); overflow: auto; overscroll-behavior: contain }`, header cells `position: sticky; top: 0` (pinned to that box), and the shared hook `src/hooks/useTableScrollHandoff.js` (`const ref = useTableScrollHandoff(); <div ref={ref} className={styles.tableScroll}>`). Down = page first, up = table first. Ledger and ClientLedger still carry their own inline copy of the same logic.",
        "- Dot legends sit slightly inside (`--legend-inset`) and have extra room before the table (`--legend-after`); both tokens live in `index.css`. Payments now has a legend for its three payment-type dots, and its search + TabDock share one line (`.controlRow`), like Recovery.",
        "",
        "### Table Design Standard"),
      "Guide: table scroll + legend note")
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