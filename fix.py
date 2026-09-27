#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix125: "RECENTLY USED" chips in the Report Catalogue
#   were scoped to the whole app, not the current data source. `recent`
#   in localStorage is one global list of report ids shared across every
#   dataset (PROJECTS/CLIENTS/PAYMENTS/EXPENSES/COMPANY), and recentDefs
#   turned every one of those ids into a chip with no dataset filter --
#   so switching from PROJECTS to CLIENTS still showed whatever you'd
#   most recently applied back on PROJECTS. The localStorage list itself
#   still holds ids from all datasets (harmless, and keeps history if
#   you switch back), but recentDefs now filters that list down to
#   reports whose `.ds` matches the dataset you're currently viewing,
#   so the chip row only ever shows things actually recently used under
#   this data source.
#
# Surgical find/replace against known-good source text, not a full
# rewrite. Runs `npm run build` before committing if node_modules is
# installed and refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

STUDIO_JSX = os.path.join(SRC, "pages", "Reports", "ReportStudio.jsx")


def apply_patches(path, patches):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    rel = os.path.relpath(path, ROOT)
    applied = 0
    for old, new, desc in patches:
        if old not in text:
            if new and new in text:
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


# ═══ ReportStudio.jsx ═══
apply_patches(STUDIO_JSX, [
    (
        # 1. scope RECENTLY USED chips to the current dataset only.
        "  const recentDefs = recent.map(id => CATALOGUE.find(d => d.id === id)).filter(Boolean);",

        "  // fix125: recent ids are stored globally across all datasets,\n"
        "  // but the chip row should only reflect this data source --\n"
        "  // filter to reports whose .ds matches what's on screen.\n"
        "  const recentDefs = recent.map(id => CATALOGUE.find(d => d.id === id)).filter(Boolean).filter(d => d.ds === datasetKey);",

        "recentDefs filtered to d.ds === datasetKey so RECENTLY USED only shows chips for the current data source",
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
git("commit", "-m", "fix125: RECENTLY USED chips in Report Catalogue now scoped to the current data source instead of showing recents from every dataset")
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