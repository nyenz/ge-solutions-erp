#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix116: Report Catalogue header padding tightened, but
# stops short of Scope's/Intake's exact numbers on purpose.
#
# fix113 gave Scope its own clamp() padding matched to Intake's
# CollapsibleSection and deliberately left Catalogue on the old shared
# fixed 10px/14px, because Catalogue's header also carries the 36px-tall
# search box and a MATCHES badge that Scope's header doesn't -- squeezing
# it to Intake's exact tightness would leave that search box looking
# cramped rather than merely tidy. fix115 then found the real source of
# Scope's extra height (a boxed 28x28 chevron, not the padding) and fixed
# that too, which is also shared with Catalogue via .headToggle.
#
# This fix gives Catalogue its own modest reduction -- padding 10px/14px
# ->9px/12px, gap 10px->8px -- a visible trim without matching Scope's
# clamp(8,1.1vw,12)/clamp(10,1.4vw,16) numbers. The 36px search box itself
# is untouched; it's a functional input, not decorative spacing, and stays
# the actual height floor for this header regardless of padding.
#
# Surgical find/replace against known-good source text, not a full rewrite.
# Runs `npm run build` before committing if node_modules is installed and
# refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

REPORT_STUDIO_CSS = os.path.join(SRC, "pages", "Reports", "ReportStudio.module.css")


def apply_patches(path, patches):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    rel = os.path.relpath(path, ROOT)
    applied = 0
    for old, new, desc in patches:
        if old not in text:
            if new in text:
                print("skip: " + rel + " -- '" + desc + "' already applied")
            else:
                print("WARN: " + rel + " -- '" + desc + "' did not match expected text, check manually")
            continue
        text = text.replace(old, new, 1)
        applied += 1

    if applied:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("written: " + rel + " (" + str(applied) + "/" + str(len(patches)) + " patch(es) applied)")
    else:
        print("skip: " + rel + " -- no patches applied")
    return applied


# ═══ ReportStudio.module.css -- Catalogue header gets its own, smaller-but-not-tiny padding ═══
apply_patches(REPORT_STUDIO_CSS, [
    (
        "/* fix113: Scope's header row is the one directly comparable to an\n"
        "   Intake CollapsibleSection header (no search box competing for room),\n"
        "   so it gets Intake's exact clamp() padding/gap instead of the shared\n"
        "   fixed 10px/14px -- otherwise it reads shorter than every Intake\n"
        "   section header at normal desktop widths. Catalogue keeps the fixed\n"
        "   padding; it still needs the extra width for the search field. */\n"
        ".scopePanel .panelHeadRow {\n"
        "  padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 16px);\n"
        "  gap: clamp(6px, 1vw, 12px);\n"
        "}",
        "/* fix113: Scope's header row is the one directly comparable to an\n"
        "   Intake CollapsibleSection header (no search box competing for room),\n"
        "   so it gets Intake's exact clamp() padding/gap instead of the shared\n"
        "   fixed 10px/14px -- otherwise it reads shorter than every Intake\n"
        "   section header at normal desktop widths. */\n"
        ".scopePanel .panelHeadRow {\n"
        "  padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 16px);\n"
        "  gap: clamp(6px, 1vw, 12px);\n"
        "}\n"
        "/* fix116: Catalogue trims down from the original shared 10px/14px too,\n"
        "   but stops well short of Scope's numbers above -- it still carries a\n"
        "   36px-tall search box and a MATCHES badge Scope's header doesn't have,\n"
        "   so squeezing it to Intake's exact tightness would crowd the search\n"
        "   field rather than just tidy the header up. */\n"
        ".catPanel .panelHeadRow {\n"
        "  padding: 9px 12px;\n"
        "  gap: 8px;\n"
        "}",
        "Catalogue header gets its own, moderately-tightened padding/gap -- reduced from the old 10px/14px/10px, but not down to Scope's Intake-matched numbers",
    ),
])

# ═══ build gate (fix76) ═══
if os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True)
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

git("add", "-A")
git("commit", "-m", "fix116: Report Catalogue header padding/gap tightened (10px/14px/10px -> 9px/12px/8px), deliberately short of Scope's Intake-matched numbers since Catalogue still carries a 36px search box and MATCHES badge Scope's header doesn't")
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