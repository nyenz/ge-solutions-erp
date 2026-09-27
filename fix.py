#!/usr/bin/env python3
# PATH: fix129.py
# GOLDEN SEED -- fix129: SIGNALS dropdown -- filter chips were 7 wide
#   (ALL/UNREAD/MONEY/PIPELINE/RECOVERY/STAFF/SYSTEM) inside a 320-380px
#   panel with overflow-x: auto and a hidden scrollbar (scrollbar-width:
#   none). Only 5 fit on screen and nothing hinted the row scrolled --
#   no fade, no arrow, no partial chip left visibly cut off enough to
#   read as "more here." STAFF and SYSTEM were functionally invisible.
#   Filters now wrap onto a second row instead: every chip is on screen
#   at once, nothing to discover, no scroll gesture required inside an
#   already-small dropdown.
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

HEADER_CSS = os.path.join(SRC, "components", "layout", "Header.module.css")


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


# ═══ Header.module.css ═══
apply_patches(HEADER_CSS, [
    (
        # 1. wrap instead of a silently-scrollable, cut-off row.
        ".notifFilters {\n"
        "    display: flex;\n"
        "    gap: 5px;\n"
        "    padding: 9px 11px;\n"
        "    overflow-x: auto;\n"
        "    border-bottom: 1px solid rgba(26, 46, 48, 0.08);\n"
        "    flex-shrink: 0;\n"
        "    scrollbar-width: none;\n"
        "}\n"
        ".notifFilters::-webkit-scrollbar { display: none; }",

        "/* fix129: wraps instead of scrolling -- 7 filters (ALL/UNREAD/\n"
        "   MONEY/PIPELINE/RECOVERY/STAFF/SYSTEM) in a 320-380px panel\n"
        "   used to hide 2 of them behind an overflow-x scroll with no\n"
        "   scrollbar and no fade to hint it was there. Every chip is now\n"
        "   on screen at once. */\n"
        ".notifFilters {\n"
        "    display: flex;\n"
        "    flex-wrap: wrap;\n"
        "    gap: 5px;\n"
        "    padding: 9px 11px;\n"
        "    border-bottom: 1px solid rgba(26, 46, 48, 0.08);\n"
        "    flex-shrink: 0;\n"
        "}",

        "notifFilters switched from hidden-scroll to wrap",
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
git("commit", "-m", "fix129: SIGNALS dropdown filter chips wrap onto a second row instead of hiding STAFF/SYSTEM behind an unhinted horizontal scroll")
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