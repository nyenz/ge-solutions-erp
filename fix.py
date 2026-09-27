#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix122: two Report Catalogue fixes.
#   1. Hovering the APPLIED report used to do nothing -- .rowApplied
#      carried its own fixed translucent wash and the hover-to-solid-
#      orange rule was scoped :not(.rowApplied), so the currently
#      active report felt dead under the cursor. It now gets the same
#      solid-orange + white-text hover feedback as every other row.
#   2. .catList (the report list itself) had its own max-height:340 +
#      overflow-y:auto -- a nested scroll box that trapped the wheel
#      at its own bottom, so scrolling down through the list never
#      handed off to the page even once you'd reached the last
#      report. Dropping the inner scroll (list takes its natural
#      height) fixes the trap AND removes the inner scrollbar in one
#      change -- no JS scroll-chaining hack needed, the page just
#      keeps scrolling normally once the list runs out of rows.
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

STUDIO_CSS = os.path.join(SRC, "pages", "Reports", "ReportStudio.module.css")


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


# ═══ ReportStudio.module.css ═══
apply_patches(STUDIO_CSS, [
    (
        # 1. applied-report hover feedback -- inserted right after the
        # existing rowOpen/rowApplied chev rules so its equal-specificity
        # (4 classes) selectors win by cascade order in every applied
        # state, including an applied row that's also open.
        ".row.rowOpen .chev { transform: rotate(180deg); color: #EE8C3A; }\n"
        ".row.rowApplied.rowOpen .chev { color: #1a2e30; }\n"
        ".appliedTag {",

        ".row.rowOpen .chev { transform: rotate(180deg); color: #EE8C3A; }\n"
        ".row.rowApplied.rowOpen .chev { color: #1a2e30; }\n"
        "/* fix122: the applied report now reacts to hover too, same\n"
        "   solid-orange fill + white text as any other row -- it no\n"
        "   longer sits inert under the cursor just because it's active. */\n"
        ".row.rowApplied .rowHead:hover { background: #EE8C3A; }\n"
        ".row.rowApplied .rowHead:hover .name,\n"
        ".row.rowApplied .rowHead:hover .rows,\n"
        ".row.rowApplied .rowHead:hover .tag,\n"
        ".row.rowApplied .rowHead:hover .chev { color: #fff; }\n"
        ".row.rowApplied .rowHead:hover .desc { color: rgba(255,255,255,0.85); }\n"
        ".appliedTag {",

        "applied-report row now gets solid-orange + white-text hover feedback instead of staying inert",
    ),
    (
        # 2. drop catList's own scroll box so it can't trap the wheel at
        # its bottom, and so there's no inner scrollbar left to hide.
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 7px;\n"
        "  scrollbar-width: thin; scrollbar-color: #EE8C3A transparent;\n"
        "}\n"
        ".catList::-webkit-scrollbar { width: 6px; }\n"
        ".catList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }",

        "/* fix122: no more max-height/overflow-y here -- the list used\n"
        "   to trap scroll at its own bottom instead of handing off to\n"
        "   the page. It now takes its natural height, so the page just\n"
        "   keeps scrolling past it once you reach the last report, and\n"
        "   there's no inner scrollbar left to remove. */\n"
        ".catList {\n"
        "  background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 7px;\n"
        "}",

        "catList internal scroll/scrollbar removed -- list now flows naturally with the page",
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
git("commit", "-m", "fix122: applied-report row now gets hover feedback too; Report Catalogue list scroll trap + inner scrollbar removed so the page scrolls through it naturally")
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