#!/usr/bin/env python3
# PATH: fix135.py
# GOLDEN SEED -- fix135: THE PROBLEM FLAG -- reflected across the whole app.
#   The PROBLEM button on the Folder page only ever changed one thing: its own
#   colour. Nothing else in the app noticed. Checked against the code:
#
#     1. BELL. notificationCatalog.js already lists PROBLEM_FLAGGED
#        ("Flagged as a problem") but the backend never sent it, so the
#        drawer could never show it. Now toggle-problem sends it (to ALL
#        roles) when a plot is FLAGGED. Clicking that row already routes to
#        /folder/<id> (routeFor, entityType PROJECT), so it lands on the
#        right folder. It is sent as CRITICAL so the drawer tints it red,
#        the same red as the PROBLEM button.
#     2. NOTE. The prompt "Describe the problem" was sent to the server as
#        ?note= and thrown away. It is now read, written into the audit
#        line and into the bell message.
#     3. FOLDER HEADER. .badgeProblem existed in the CSS but nothing used
#        it. A flagged folder now shows a red PROBLEM badge next to the
#        other status badges.
#     4. LEDGER. A flagged plot now has a red PROBLEM tag under its project
#        index, a light red row tint, and a PROBLEM filter button.
#
#   Already correct, not touched: Reports (Flagged Problem field), Audit
#   (PROBLEM_FLAG code), Folder PROBLEM button + [PROBLEM] note tag.
#
#   Not done here (needs a Dashboard summary change, a separate batch):
#   a PROBLEM count card on the Director dashboard.
#
# Backend (FolderPortalController.java) + frontend (3 files + 1 css).
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
JAVA = os.path.join(ROOT, "erp-backend", "src", "main", "java", "com", "gesolutions", "erp")

PORTAL_JAVA = os.path.join(JAVA, "modules", "land", "controller", "FolderPortalController.java")
CATALOG_JS = os.path.join(SRC, "components", "common", "notificationCatalog.js")
FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
LEDGER_JSX = os.path.join(SRC, "pages", "Ledger", "LedgerPage.jsx")
LEDGER_CSS = os.path.join(SRC, "pages", "Ledger", "LedgerPage.module.css")

MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
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


# ======================================================================
# FolderPortalController.java  (backend)
# ======================================================================
java0 = read(PORTAL_JAVA)
java = java0

java = sub(java,
           "import com.gesolutions.erp.common.audit.AuditService;\n",
           "import com.gesolutions.erp.common.audit.AuditService;\n"
           "import com.gesolutions.erp.modules.notification.service.NotificationService;\n",
           "Java: import NotificationService")

java = sub(java,
           "    private final AuditService auditService;\n",
           "    private final AuditService auditService;\n"
           "    private final NotificationService notificationService;\n",
           "Java: inject NotificationService")

java = sub(java,
           "    public Map<String, Object> toggleProblem(@PathVariable UUID id) {\n",
           "    public Map<String, Object> toggleProblem(@PathVariable UUID id, @RequestParam(value = \"note\", required = false) String note) {\n",
           "Java: toggle-problem accepts the note")

java = sub(java,
           r'''        auditService.logAction("PROBLEM_FLAG", "Operator [" + op() + "] " + (p.isProblem() ? "flagged" : "cleared") + " PROBLEM on #" + p.getProjectIndex() + ".");
''',
           r'''        String why = (note != null && !note.isBlank()) ? note.trim() : "";
        String plot = (p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null)
                ? p.getLandTitle().getPlotNumber() : "project #" + p.getProjectIndex();
        auditService.logAction("PROBLEM_FLAG", "Operator [" + op() + "] " + (p.isProblem() ? "flagged" : "cleared") + " PROBLEM on #" + p.getProjectIndex() + (why.isEmpty() ? "" : ": " + why) + ".");
        if (p.isProblem()) {
            // fix135: only FLAGGING notifies (clearing is not news). emitRaw, not emit,
            // because emit() dedupes forever per type+entity and a plot can be flagged twice.
            notificationService.emitRaw("PROBLEM_FLAGGED", "CRITICAL",
                    "Plot " + plot + " flagged as a problem by " + op() + (why.isEmpty() ? "." : ": " + why),
                    "PROJECT", p.getId(), "ALL");
        }
''',
           "Java: audit line carries the note + PROBLEM_FLAGGED notification")

# ======================================================================
# notificationCatalog.js
# ======================================================================
cat0 = read(CATALOG_JS)
cat = cat0

cat = sub(cat,
          "PROBLEM_FLAGGED:       { label: 'Flagged as a problem',  group: GROUPS.PIPELINE, icon: FiFlag,        severity: 'WARN' },",
          "PROBLEM_FLAGGED:       { label: 'Flagged as a problem',  group: GROUPS.PIPELINE, icon: FiFlag,        severity: 'CRITICAL' },",
          "catalog: PROBLEM_FLAGGED is CRITICAL (red row, same red as the PROBLEM button)")

# ======================================================================
# FolderPage.jsx
# ======================================================================
fol0 = read(FOLDER_JSX)
fol = fol0

fol = sub(fol,
          "                        {project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}\n",
          "                        {project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}\n"
          "                        {project.problem && <span className={`${styles.textBadge} ${styles.badgeProblem}`}>PROBLEM</span>}\n",
          "folder header: red PROBLEM badge")

# ======================================================================
# LedgerPage.jsx
# ======================================================================
led0 = read(LEDGER_JSX)
led = led0

led = sub(led,
          "        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25);\n",
          "        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25);\n"
          "        if (activeFilter === 'PROBLEM')     filtered = filtered.filter(p => !!p.problem);\n",
          "ledger: PROBLEM filter logic")

led = sub(led,
          "        { key: 'PAID', label: 'PAID' },\n    ];",
          "        { key: 'PAID', label: 'PAID' }, { key: 'PROBLEM', label: 'PROBLEM' },\n    ];",
          "ledger: PROBLEM filter button")

led = sub(led,
          "className={isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>",
          "className={proj.problem ? styles.rowProblem : isReceivable ? styles.rowReceivable : isCritical ? styles.rowCritical : ''}>",
          "ledger: problem row tint")

led = sub(led,
          "                                                    <strong>#{proj.projectIndex || '---'}</strong>\n",
          "                                                    <strong>#{proj.projectIndex || '---'}</strong>\n"
          "                                                    {proj.problem && <span className={styles.problemTag}>PROBLEM</span>}\n",
          "ledger: PROBLEM tag under the project index")

# ======================================================================
# LedgerPage.module.css
# ======================================================================
lcss0 = read(LEDGER_CSS)
lcss = lcss0

lcss = sub(lcss,
           ".rowCritical{background:rgba(239,68,68,0.07);}\n",
           ".rowCritical{background:rgba(239,68,68,0.07);}\n"
           "/* fix135: flagged PROBLEM plots. Same red as the Folder page PROBLEM button/badge. */\n"
           ".rowProblem{background:rgba(239,68,68,0.10);}\n"
           ".problemTag{align-self:flex-start;display:inline-block;padding:1px clamp(5px,0.6vw,8px);"
           "border:1px solid rgba(239,68,68,0.4);border-radius:var(--radius-sm,6px);"
           "background:rgba(239,68,68,0.12);color:#ef4444;font-family:'Inter',sans-serif;font-weight:900;"
           "font-size:clamp(8px,0.8vw,10px);letter-spacing:1px;text-transform:uppercase;}\n",
           "ledger css: rowProblem + problemTag")

# ======================================================================
# write (atomic) + build gate + commit
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix134).")
    sys.exit(1)

changed = False
for path, before, after, label in [
    (PORTAL_JAVA, java0, java, "erp-backend/.../FolderPortalController.java"),
    (CATALOG_JS, cat0, cat, "erp-frontend/src/components/common/notificationCatalog.js"),
    (FOLDER_JSX, fol0, fol, "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"),
    (LEDGER_JSX, led0, led, "erp-frontend/src/pages/Ledger/LedgerPage.jsx"),
    (LEDGER_CSS, lcss0, lcss, "erp-frontend/src/pages/Ledger/LedgerPage.module.css"),
]:
    if after != before:
        write(path, after)
        print("written: " + label)
        changed = True
if not changed:
    print("note: nothing changed -- fix135 already applied")

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
git("commit", "-m", "fix135: PROBLEM flag reflected app-wide -- bell notification (with the note) when a plot is flagged, red PROBLEM badge in folder header, Ledger PROBLEM filter + row tint + tag, audit line carries the note")
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