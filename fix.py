#!/usr/bin/env python3
# PATH: fix168.py
# GOLDEN SEED -- fix168: collapsed sidebar polish (orange active bar on the LEFT, smaller GS footer, hamburger lined up with the icon column).
#
#   1. ACTIVE BAR: in the collapsed (icon-only) sidebar the thick orange bar on the active link now sits on the
#      LEFT edge, like the expanded sidebar, instead of the right edge. The icon stays centred on the column.
#   2. GS FOOTER: in the collapsed sidebar the "GS" footer takes much less height (smaller text, tighter
#      padding, no minimum height) so it no longer crowds the SETTINGS icon.
#   3. HAMBURGER: on desktop widths the top-bar menu button is now exactly as wide as the collapsed sidebar
#      column and sits directly above it, centred over the icons. Mobile layout is untouched.
#
# NOT in this fix: the expanded sidebar, the logo / title text, mobile layout, any page content.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
# Names, and one variable per file this fix touches.
FIX_NO = "fix168"
COMMIT_MSG = "fix168: collapsed sidebar polish (orange active bar on the left, smaller GS footer, hamburger aligned with the icon column)"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

F_SIDEBAR_CSS = os.path.join(SRC, "components", "layout", "Sidebar.module.css")
F_HEADER_CSS = os.path.join(SRC, "components", "layout", "Header.module.css")
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
LOAD_FILES = (F_SIDEBAR_CSS, F_HEADER_CSS)
for _p in LOAD_FILES:
    load(_p)

patch(F_SIDEBAR_CSS,
      "\n".join([
          ".collapsed .navItem {",
          "    padding: clamp(10px, 1.2vw, 13px) 0;",
          "    justify-content: center;",
          "    border-left-width: 0;",
          "    border-right: 3px solid transparent;",
          "}"]),
      "\n".join([
          ".collapsed .navItem {",
          "    /* 3px right padding balances the 3px left bar so the icon stays centred */",
          "    padding: clamp(10px, 1.2vw, 13px) 3px clamp(10px, 1.2vw, 13px) 0;",
          "    justify-content: center;",
          "    border-left: 3px solid transparent;",
          "    border-right-width: 0;",
          "}"]),
      "collapsed sidebar: reserve the bar on the LEFT of each icon, not the right")

patch(F_SIDEBAR_CSS,
      "\n".join([
          ".collapsed .active {",
          "    border-left-color: transparent;",
          "    border-right-color: #EE8C3A;",
          "}"]),
      "\n".join([
          ".collapsed .active {",
          "    border-left-color: #EE8C3A;",
          "}"]),
      "collapsed sidebar: orange active bar shows on the LEFT")

patch(F_SIDEBAR_CSS,
      "\n".join([
          ".collapsed .branding {",
          "    font-size: 12px;",
          "    letter-spacing: 1px;",
          "}"]),
      "\n".join([
          ".collapsed .branding {",
          "    font-size: 10px;",
          "    letter-spacing: 0.5px;",
          "    line-height: 1;",
          "}",
          ".collapsed .sidebarFooter {",
          "    min-height: 0;",
          "    padding: 5px 0;",
          "}"]),
      "collapsed sidebar: smaller GS footer so it stops crowding the SETTINGS icon")

patch(F_HEADER_CSS,
      "\n".join([
          ".sidebarToggle:focus-visible {",
          "    outline: 2px solid #EE8C3A;",
          "    outline-offset: 2px;",
          "}"]),
      "\n".join([
          ".sidebarToggle:focus-visible {",
          "    outline: 2px solid #EE8C3A;",
          "    outline-offset: 2px;",
          "}",
          "",
          "/* Desktop: the button sits right above the collapsed sidebar column (52px wide,",
          "   2px border, so the icon centre is 25px from the left edge) and is centred on it. */",
          "@media (min-width: 769px) {",
          "    .header { padding-left: 0; }",
          "    .sidebarToggle {",
          "        width: 40px;",
          "        height: 40px;",
          "        margin-left: 5px;",
          "        margin-right: 6px;",
          "    }",
          "}"]),
      "top bar: hamburger button lined up with the collapsed sidebar icon column")
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

if not changed:
    print("note: nothing changed -- " + FIX_NO + " already applied")


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
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed and RUN_GATES:
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
if changed and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif changed:
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

if not changed:
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