#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix113: Reports page's Scope panel header now measures the
# same as Intake's CollapsibleSection headers.
#
# What this fixes, and why:
#   Scope and Report Catalogue share one .panelHeadRow class with FIXED
#   padding (10px 14px) and a fixed 10px inner gap. Intake's CollapsibleSection
#   header uses viewport-scaled padding instead:
#       clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 16px), gap clamp(6px,1vw,12px)
#   At normal desktop widths that clamp settles at 12px 16px -- taller and
#   wider than the Reports header's fixed 10px 14px -- so the Scope panel
#   header reads visibly shorter/tighter than every Intake section header,
#   even though both are meant to be the same component style. The title
#   text itself also scales on a different curve (1.1vw vs Intake's 1.3vw),
#   compounding the height mismatch at mid-size viewports.
#
#   Fix: give ONLY .scopePanel's header row and title the same clamp values
#   Intake uses, via a more specific selector layered on top of the shared
#   .panelHeadRow rule. The Report Catalogue header is deliberately left on
#   its original fixed padding -- it still needs the extra horizontal room
#   for the search box, per fix112's note that "the Catalogue header's own
#   dimensions are left alone."
#
# Every edit below is a surgical find/replace against known-good source
# text rather than a full-file rewrite.
#
# Runs `npm run build` before committing if node_modules is installed
# (fix76's build-gate rule) and refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

REPORT_STUDIO_CSS = os.path.join(SRC, "pages", "Reports", "ReportStudio.module.css")


def apply_patches(path, patches):
    """Apply an ordered list of (old, new, description) surgical patches to
    a file. Each `old` must appear exactly once -- if it doesn't (because
    the file has already been patched, or has drifted from what this
    script expects), that one patch is skipped with a warning instead of
    corrupting the file or aborting the whole run."""
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


# ═══ ReportStudio.module.css -- Scope header matches Intake's header size ═══
apply_patches(REPORT_STUDIO_CSS, [
    (
        ".scopePanel .panelHeadRow, .catPanel .panelHeadRow { cursor: pointer; }\n"
        ".scopePanel .panelHeadRow:focus-visible, .catPanel .panelHeadRow:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }\n"
        ".scopeTitle { font-family: 'Cinzel', serif; color: #EE8C3A; font-size: clamp(10px, 1.1vw, 13px); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }",
        ".scopePanel .panelHeadRow, .catPanel .panelHeadRow { cursor: pointer; }\n"
        ".scopePanel .panelHeadRow:focus-visible, .catPanel .panelHeadRow:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }\n"
        "/* fix113: Scope's header row is the one directly comparable to an\n"
        "   Intake CollapsibleSection header (no search box competing for room),\n"
        "   so it gets Intake's exact clamp() padding/gap instead of the shared\n"
        "   fixed 10px/14px -- otherwise it reads shorter than every Intake\n"
        "   section header at normal desktop widths. Catalogue keeps the fixed\n"
        "   padding; it still needs the extra width for the search field. */\n"
        ".scopePanel .panelHeadRow {\n"
        "  padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 16px);\n"
        "  gap: clamp(6px, 1vw, 12px);\n"
        "}\n"
        ".scopeTitle { font-family: 'Cinzel', serif; color: #EE8C3A; font-size: clamp(10px, 1.1vw, 13px); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }\n"
        ".scopePanel .scopeTitle { font-size: clamp(10px, 1.3vw, 13px); }",
        "Scope header padding/gap/title-scale matched to Intake's CollapsibleSection header exactly",
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
git("commit", "-m", "fix113: Scope panel header padding/gap/title-scale matched to Intake's CollapsibleSection header (Catalogue header left as-is for its search box)")
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