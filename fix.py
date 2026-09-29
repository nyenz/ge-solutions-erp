#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix149: stat-card borders (orange rest, font-colour hover, no duplicate colours) + skeleton loader app-wide.
#
# 1. Stat cards (Recovery Cockpit, Payment Records, Expenses, Client dossier):
#    - every card RESTS on the orange border; the font colours stay exactly as they were
#    - on HOVER the border switches to that card's own font colour (green / red / cyan / orange / white)
#    - no two cards on a page share a colour: the duplicate cyan card gets the WHITE font
#      (Expenses: CATEGORIES USED, Dossier: OWNERSHIP) -- like TOTAL SHOWN on Payment Records
#    - Payment Records loses its inline border colours (they moved into sumGreen / sumRed classes)
# 2. Loading: the shimmering skeleton from the Folder page is now THE loading state everywhere.
#    LoadingState + LoadingRow (used by Dashboard, Recovery, Payments, Ledger, Client Ledger,
#    Client dossier, Expenses, Audit, Settings) draw skeleton bars instead of a spinner. The
#    label stays for screen readers. Folder page keeps its own skeleton (already the reference).
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix149"
COMMIT_MSG = "fix149: stat cards orange rest border + font-colour hover + no duplicate colours; skeleton loader app-wide"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")
TESTJAVA = os.path.join(BACKEND, "src", "test", "java", "com", "gesolutions", "erp")
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")

RECOVERY_CSS = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.module.css")
PAY_JSX = os.path.join(SRC, "pages", "Payments", "PaymentsPage.jsx")
PAY_CSS = os.path.join(SRC, "pages", "Payments", "PaymentsPage.module.css")
EXP_JSX = os.path.join(SRC, "pages", "Financials", "ExpensesPage.jsx")
EXP_CSS = os.path.join(SRC, "pages", "Financials", "ExpensesPage.module.css")
PORTFOLIO_JSX = os.path.join(SRC, "pages", "Clients", "ClientPortfolioPage.jsx")
PORTFOLIO_CSS = os.path.join(SRC, "pages", "Clients", "ClientPortfolioPage.module.css")
LOADING_JSX = os.path.join(SRC, "components", "common", "LoadingState.jsx")
LOADING_CSS = os.path.join(SRC, "components", "common", "LoadingState.module.css")
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
LOAD_FILES = (RECOVERY_CSS, PAY_JSX, PAY_CSS, EXP_JSX, EXP_CSS,
              PORTFOLIO_JSX, PORTFOLIO_CSS, LOADING_JSX, LOADING_CSS, GUIDE)
for _p in LOAD_FILES:
    load(_p)

def L(*lines):
    return "\n".join(lines)

# Literal hexes on purpose: --orange is re-mapped by [data-tab-accent] on some pages,
# and the REST border must always be the brand orange.

# ---- 1. Recovery Cockpit: orange rest, font-colour hover ----
patch(RECOVERY_CSS,
      ".countsHUD .countCard:hover { transform: none; border-color: var(--orange-border); }",
      L(".countsHUD .countCard { border-color: #EE8C3A; }",
        ".countsHUD .countCard:hover { transform: none; border-color: #EE8C3A; }"),
      "Recovery CSS: count cards rest on orange")
patch(RECOVERY_CSS,
      L(".countsHUD .statGreen, .countsHUD .statGreen:hover { border-color: #22c55e; }",
        ".countsHUD .statGreen label, .countsHUD .statGreen strong { color: #22c55e; }",
        ".countsHUD .statCyan, .countsHUD .statCyan:hover { border-color: #06b6d4; }",
        ".countsHUD .statCyan label, .countsHUD .statCyan strong { color: #06b6d4; }",
        ".countsHUD .statAmber, .countsHUD .statAmber:hover { border-color: var(--orange); }",
        ".countsHUD .statAmber label, .countsHUD .statAmber strong { color: var(--orange); }",
        ".countsHUD .statRed, .countsHUD .statRed:hover { border-color: #ef4444; }",
        ".countsHUD .statRed label, .countsHUD .statRed strong { color: #ef4444; }"),
      L("/* fix149: border = orange at rest, the card's own font colour on hover */",
        ".countsHUD .statGreen:hover { border-color: #22c55e; }",
        ".countsHUD .statGreen label, .countsHUD .statGreen strong { color: #22c55e; }",
        ".countsHUD .statCyan:hover { border-color: #06b6d4; }",
        ".countsHUD .statCyan label, .countsHUD .statCyan strong { color: #06b6d4; }",
        ".countsHUD .statAmber:hover { border-color: #EE8C3A; }",
        ".countsHUD .statAmber label, .countsHUD .statAmber strong { color: #EE8C3A; }",
        ".countsHUD .statRed:hover { border-color: #ef4444; }",
        ".countsHUD .statRed label, .countsHUD .statRed strong { color: #ef4444; }"),
      "Recovery CSS: hover border = font colour")

# ---- 2. Payment Records: TOTAL SHOWN white, TITLE green, RECEIVABLES red ----
patch(PAY_JSX,
      L("<div className={styles.sumCard}>", "                    <label>TOTAL SHOWN</label>"),
      L("<div className={`${styles.sumCard} ${styles.sumWhite}`}>", "                    <label>TOTAL SHOWN</label>"),
      "Payments: TOTAL SHOWN white class")
patch(PAY_JSX,
      "<div className={styles.sumCard} style={{ borderColor: '#22c55e' }}>",
      "<div className={`${styles.sumCard} ${styles.sumGreen}`}>",
      "Payments: TITLE PAYMENTS green class (inline border gone)")
patch(PAY_JSX,
      "<div className={styles.sumCard} style={{ borderColor: '#ef4444' }}>",
      "<div className={`${styles.sumCard} ${styles.sumRed}`}>",
      "Payments: RECEIVABLES red class (inline border gone)")
patch(PAY_CSS,
      L(".sumCard {",
        "    background: var(--panel-bg);",
        "    border: 1.5px solid var(--orange-border);"),
      L(".sumCard {",
        "    background: var(--panel-bg);",
        "    border: 1.5px solid #EE8C3A;",
        "    transition: border-color 0.2s ease;"),
      "Payments CSS: sum cards rest on orange")
patch(PAY_CSS,
      ".sumCard span { font-size: var(--stat-note); color: rgba(255,255,255,0.35); }",
      L(".sumCard span { font-size: var(--stat-note); color: rgba(255,255,255,0.35); }",
        "/* fix149: hover border = the card's font colour */",
        ".sumWhite:hover { border-color: #fff; }",
        ".sumGreen:hover { border-color: #22c55e; }",
        ".sumRed:hover   { border-color: #ef4444; }"),
      "Payments CSS: hover colours")

# ---- 3. Expenses: CATEGORIES USED goes white (PRESETS keeps cyan) ----
patch(EXP_JSX,
      L("<div className={`${styles.statCard} ${styles.statCyan}`}>", "                    <label>CATEGORIES USED</label>"),
      L("<div className={`${styles.statCard} ${styles.statWhite}`}>", "                    <label>CATEGORIES USED</label>"),
      "Expenses: CATEGORIES USED white")
patch(EXP_CSS,
      L(".statAmber { border-color: var(--orange); }",
        ".statAmber label, .statAmber strong { color: var(--orange); }",
        ".statGreen { border-color: #22c55e; }",
        ".statGreen label, .statGreen strong { color: #22c55e; }",
        ".statCyan { border-color: #06b6d4; }",
        ".statCyan label, .statCyan strong { color: #06b6d4; }"),
      L("/* fix149: every card rests on orange; hover swaps the border to the card's font colour */",
        ".statCard { border-color: #EE8C3A; transition: border-color 0.2s ease; }",
        ".statAmber:hover { border-color: #EE8C3A; }",
        ".statAmber label, .statAmber strong { color: #EE8C3A; }",
        ".statGreen:hover { border-color: #22c55e; }",
        ".statGreen label, .statGreen strong { color: #22c55e; }",
        ".statCyan:hover { border-color: #06b6d4; }",
        ".statCyan label, .statCyan strong { color: #06b6d4; }",
        ".statWhite:hover { border-color: #fff; }",
        ".statWhite label, .statWhite strong { color: #fff; }"),
      "Expenses CSS: orange rest + hover colours + white")

# ---- 4. Client dossier: OWNERSHIP goes white (PROJECTS keeps cyan) ----
patch(PORTFOLIO_JSX,
      L("          <div className={`${styles.statCard} ${styles.statCyan} ${styles.statClickable}`} role=\"button\" tabIndex={0}",
        "            onClick={() => scrollToSection('portfolio-panel')}",
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>",
        "            <label>OWNERSHIP</label>"),
      L("          <div className={`${styles.statCard} ${styles.statWhite} ${styles.statClickable}`} role=\"button\" tabIndex={0}",
        "            onClick={() => scrollToSection('portfolio-panel')}",
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>",
        "            <label>OWNERSHIP</label>"),
      "Dossier: OWNERSHIP white")
patch(PORTFOLIO_CSS,
      L(".statRed   { border-color: #ef4444; }",
        ".statRed   label, .statRed   strong { color: #ef4444; }",
        ".statGreen { border-color: #22c55e; }",
        ".statGreen label, .statGreen strong { color: #22c55e; }",
        ".statCyan  { border-color: #06b6d4; }",
        ".statCyan  label, .statCyan  strong { color: #06b6d4; }",
        ".statAmber { border-color: var(--orange); }",
        ".statAmber label, .statAmber strong { color: var(--orange); }"),
      L("/* fix149: every card rests on orange; hover swaps the border to the card's font colour.",
        "   These sit AFTER .statClickable:hover so they win at equal specificity. */",
        ".statCard { border-color: #EE8C3A; transition: border-color 0.2s ease; }",
        ".statCard.statClickable:hover { box-shadow: none; }",
        ".statRed:hover   { border-color: #ef4444; }",
        ".statRed   label, .statRed   strong { color: #ef4444; }",
        ".statGreen:hover { border-color: #22c55e; }",
        ".statGreen label, .statGreen strong { color: #22c55e; }",
        ".statCyan:hover  { border-color: #06b6d4; }",
        ".statCyan  label, .statCyan  strong { color: #06b6d4; }",
        ".statAmber:hover { border-color: #EE8C3A; }",
        ".statAmber label, .statAmber strong { color: #EE8C3A; }",
        ".statWhite:hover { border-color: #fff; }",
        ".statWhite label, .statWhite strong { color: #fff; }"),
      "Dossier CSS: orange rest + hover colours + white")

# ---- 5. Skeleton loader everywhere (LoadingState + LoadingRow) ----
patch(LOADING_JSX,
      L("            styles.shell,",
        "            tone === 'bare' ? styles.shellBare : styles.shellPanel,",
        "            size === 'page' ? styles.shellPage : '',"),
      L("            styles.shell,",
        "            styles.shellSkel,",
        "            tone === 'bare' ? styles.shellBare : styles.shellPanel,",
        "            size === 'page' ? styles.shellPage : '',"),
      "LoadingState: skeleton shell class")
patch(LOADING_JSX,
      L("        <div className={styles.spinner} aria-hidden=\"true\" />",
        "        <span className={styles.label}>{label}</span>",
        "    </div>",
        ");",
        "",
        "/** Same thing, but as a table row"),
      L("        {/* fix149: the Folder page skeleton is the loading look everywhere */}",
        "        <div className={styles.skelStack} aria-hidden=\"true\">",
        "            {size === 'page' && <div className={styles.skelHud} />}",
        "            <div className={styles.skelPanel}>",
        "                <div className={styles.skelHeader} />",
        "                <div className={styles.skelBody}>",
        "                    <div className={styles.skelLine} />",
        "                    <div className={styles.skelLine} />",
        "                    <div className={styles.skelLine} />",
        "                </div>",
        "            </div>",
        "            {size === 'page' && (",
        "                <div className={styles.skelPanel}>",
        "                    <div className={styles.skelHeader} />",
        "                    <div className={styles.skelBody}>",
        "                        <div className={styles.skelLine} />",
        "                        <div className={styles.skelLine} />",
        "                    </div>",
        "                </div>",
        "            )}",
        "        </div>",
        "        <span className={styles.srOnly}>{label}</span>",
        "    </div>",
        ");",
        "",
        "/** Same thing, but as a table row"),
      "LoadingState: skeleton bars replace the spinner")
patch(LOADING_JSX,
      L("export const LoadingRow = ({ colSpan = 1, label = 'LOADING...' }) => (",
        "    <tr>",
        "        <td colSpan={colSpan} className={styles.cell}>",
        "            <span className={styles.cellInner} role=\"status\" aria-live=\"polite\">",
        "                <span className={styles.spinnerSm} aria-hidden=\"true\" />",
        "                <span className={styles.label}>{label}</span>",
        "            </span>",
        "        </td>",
        "    </tr>",
        ");"),
      L("export const LoadingRow = ({ colSpan = 1, label = 'LOADING...' }) => (",
        "    <React.Fragment>",
        "        {['92%', '70%', '84%'].map((w, i) => (",
        "            <tr key={i}>",
        "                <td colSpan={colSpan} className={styles.skelCell}>",
        "                    <span className={styles.skelRowBar} style={{ width: w }} aria-hidden=\"true\" />",
        "                    {i === 0 && <span className={styles.srOnly} role=\"status\" aria-live=\"polite\">{label}</span>}",
        "                </td>",
        "            </tr>",
        "        ))}",
        "    </React.Fragment>",
        ");"),
      "LoadingRow: skeleton rows replace the spinner row")
patch(LOADING_CSS,
      "@keyframes lsSpin { to { transform: rotate(360deg); } }",
      L("@keyframes lsSpin { to { transform: rotate(360deg); } }",
        "",
        "/* ================= fix149: SKELETON LOADER (same look as the Folder page) =================",
        "   Dark base under a light shimmer, so it only ever reads on a dark surface -- LoadingState",
        "   always sits on its own navy card (tone=panel) or inside a navy panel (tone=bare). */",
        "@keyframes lsShimmer {",
        "    0%   { background-position: -600px 0; }",
        "    100% { background-position:  600px 0; }",
        "}",
        ".shellSkel { align-items: stretch; justify-content: flex-start; text-align: left; padding: clamp(14px, 2vw, 22px); }",
        ".skelStack { display: flex; flex-direction: column; gap: clamp(10px, 1.4vw, 16px); width: 100%; }",
        ".skelHud, .skelHeader, .skelLine, .skelRowBar {",
        "    background-color: #16292b;",
        "    background-image: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.10) 50%, rgba(255,255,255,0.04) 75%);",
        "    background-size: 1200px 100%;",
        "    animation: lsShimmer 1.4s infinite linear;",
        "}",
        ".skelHud    { height: clamp(60px, 9vw, 80px); border-radius: 10px; }",
        ".skelPanel  { border-radius: 10px; overflow: hidden; border: 1.5px solid var(--ls-panel-border); }",
        ".shellBare .skelPanel { border: none; }",
        ".skelHeader { height: clamp(36px, 5vw, 48px); border-radius: 0; }",
        ".skelBody   { padding: clamp(12px, 1.6vw, 18px); display: flex; flex-direction: column; gap: clamp(10px, 1.4vw, 16px); }",
        ".skelLine   { height: clamp(14px, 2vw, 18px); border-radius: 4px; }",
        ".skelLine:nth-child(odd)  { width: 75%; }",
        ".skelLine:nth-child(even) { width: 55%; }",
        ".skelCell   { padding: clamp(10px, 1.4vw, 14px) 16px !important; }",
        ".skelRowBar { display: block; height: clamp(14px, 2vw, 18px); border-radius: 4px; }",
        ".srOnly {",
        "    position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0;",
        "    overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;",
        "}",
        "@media (prefers-reduced-motion: reduce) {",
        "    .skelHud, .skelHeader, .skelLine, .skelRowBar { animation: none; }",
        "}"),
      "LoadingState CSS: skeleton styles")

# ---- 6. guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix148: ledger top decor removed + one stat-card spec, Section 7)",
      "# Last updated: September 2026 (fix149: stat-card hover borders + app-wide skeleton loader, Section 7)",
      "Guide: header line")
patch(GUIDE,
      "### Ledger decor + stat cards (fix148)",
      L("### Stat-card borders + skeleton loader (fix149)",
        "- Stat cards REST on the orange border (#EE8C3A, literal -- `--orange` is re-mapped by `data-tab-accent`). Font colours are unchanged. On HOVER the border becomes the card's own font colour. No two cards on a page share a colour: a duplicate cyan card takes the WHITE font (`statWhite` on Expenses + Client dossier, `sumWhite` on Payment Records). Colour hover rules must sit AFTER `.statClickable:hover`.",
        "- LOADING: `LoadingState` and `LoadingRow` draw the Folder-page skeleton (dark bars + shimmer), not a spinner. The `label` prop is kept as screen-reader text (`.srOnly`). Any new loading state must go through these two components; `HardwareButton loading` keeps its own small spinner.",
        "",
        "### Ledger decor + stat cards (fix148)"),
      "Guide: fix149 note")

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