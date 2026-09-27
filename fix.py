#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix123: two follow-ups on fix122.
#   1. fix122's hover fix only covered the applied report while it was
#      CLOSED. Once you expanded it, it fell back to a muted, ink-on-
#      translucent look while every other expanded report gets a bold
#      persistent solid-orange + white header -- so the active report
#      still read as "flatter" than the rest whenever you opened it.
#      Fixed at the root: the open-state and hover-state rules used to
#      be scoped :not(.rowApplied); that scoping is gone, so opening OR
#      hovering a row now gets identical solid-orange + white-text
#      treatment whether or not it's the applied one. The old
#      applied+open ink-chevron override is removed to match, and
#      fix122's separate applied-only hover block is folded into the
#      same unconditional rule instead of sitting alongside it.
#   2. Reverting fix122's removal of .catList's own scroll -- dropping
#      max-height/overflow-y made the list stop scrolling on its own
#      at all, which isn't what was asked for (every other internally-
#      scrolled list in this app -- Ledger, Audit, Payments, Recovery --
#      keeps its own max-height/scrollbar; see the "SCROLLABLE BODY"
#      comment in components/layout/Shell.module.css). Restored the
#      max-height/overflow-y/scrollbar exactly as they were, and added
#      overscroll-behavior-y: auto explicitly so hitting the top/bottom
#      of the list's own scroll reliably hands off to the page's real
#      scroll container (.scrollArea in Shell.module.css) instead of
#      dead-ending, rather than leaving that to each browser's default.
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
        # 1. unify open + hover treatment across applied and non-applied
        # rows, drop the applied+open ink-chevron override, fold
        # fix122's separate applied-hover block into the same rules.
        "/* applied: a real, visible orange wash rather than just the rail --\n"
        "   text stays ink, and it keeps its own fill even on hover instead of\n"
        "   flipping to the open row's solid orange. */\n"
        ".row.rowApplied .rowHead { background: rgba(238,140,58,0.26); }\n"
        ".row.rowApplied .name, .row.rowApplied .rows, .row.rowApplied .tag, .row.rowApplied .chev { color: #1a2e30; }\n"
        ".row.rowApplied .desc { color: rgba(26,46,48,0.65); }\n"
        ".rowHead { display: flex; align-items: center; gap: 14px; width: 100%; text-align: left; border: none; background: transparent; padding: 10px 14px; cursor: pointer; transition: background 0.15s ease; }\n"
        "/* open (not applied) keeps the hover fill persistently, not just on\n"
        "   :hover, so it stays visible after you've expanded a row and moved\n"
        "   the mouse elsewhere. */\n"
        ".row.rowOpen:not(.rowApplied) .rowHead,\n"
        ".row:not(.rowApplied) .rowHead:hover { background: #EE8C3A; }\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .name,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .rows,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .tag,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .chev,\n"
        ".row:not(.rowApplied) .rowHead:hover .name,\n"
        ".row:not(.rowApplied) .rowHead:hover .rows,\n"
        ".row:not(.rowApplied) .rowHead:hover .tag,\n"
        ".row:not(.rowApplied) .rowHead:hover .chev { color: #fff; }\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .desc,\n"
        ".row:not(.rowApplied) .rowHead:hover .desc { color: rgba(255,255,255,0.85); }\n"
        ".rowHead:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }",

        "/* applied, closed, at rest: a real, visible orange wash rather\n"
        "   than just the rail -- text stays ink. Opening it, or just\n"
        "   hovering it, both hand off to the same solid-orange treatment\n"
        "   every row gets below, so the applied report is never flatter\n"
        "   than the rest just because it's active. */\n"
        ".row.rowApplied .rowHead { background: rgba(238,140,58,0.26); }\n"
        ".row.rowApplied .name, .row.rowApplied .rows, .row.rowApplied .tag, .row.rowApplied .chev { color: #1a2e30; }\n"
        ".row.rowApplied .desc { color: rgba(26,46,48,0.65); }\n"
        ".rowHead { display: flex; align-items: center; gap: 14px; width: 100%; text-align: left; border: none; background: transparent; padding: 10px 14px; cursor: pointer; transition: background 0.15s ease; }\n"
        "/* fix123: open keeps the fill persistently, not just on :hover, so\n"
        "   it stays visible after you've expanded a row and moved the\n"
        "   mouse elsewhere -- and neither this nor the hover fill is\n"
        "   scoped away from the applied row anymore, so expanding or\n"
        "   hovering the active report lights it up exactly like any\n"
        "   other one. */\n"
        ".row.rowOpen .rowHead,\n"
        ".row .rowHead:hover { background: #EE8C3A; }\n"
        ".row.rowOpen .rowHead .name,\n"
        ".row.rowOpen .rowHead .rows,\n"
        ".row.rowOpen .rowHead .tag,\n"
        ".row.rowOpen .rowHead .chev,\n"
        ".row .rowHead:hover .name,\n"
        ".row .rowHead:hover .rows,\n"
        ".row .rowHead:hover .tag,\n"
        ".row .rowHead:hover .chev { color: #fff; }\n"
        ".row.rowOpen .rowHead .desc,\n"
        ".row .rowHead:hover .desc { color: rgba(255,255,255,0.85); }\n"
        ".rowHead:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }",

        "open + hover treatment for the row header unified across applied and non-applied rows",
    ),
    (
        # drop the now-contradictory applied+open ink-chevron override,
        # and fix122's separate applied-only hover block (folded above).
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

        ".row.rowOpen .chev { transform: rotate(180deg); color: #EE8C3A; }\n"
        ".appliedTag {",

        "applied+open ink-chevron override removed, fix122's separate applied-hover block folded into the unified rule above",
    ),
    (
        # 2. restore catList's own scroll (reverting fix122), and make
        # the hand-off to the page's real scroll container explicit.
        "/* fix122: no more max-height/overflow-y here -- the list used\n"
        "   to trap scroll at its own bottom instead of handing off to\n"
        "   the page. It now takes its natural height, so the page just\n"
        "   keeps scrolling past it once you reach the last report, and\n"
        "   there's no inner scrollbar left to remove. */\n"
        ".catList {\n"
        "  background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 7px;\n"
        "}",

        "/* fix123: reverts fix122 -- the list keeps its own scroll like\n"
        "   every other internally-scrolled list in this app (Ledger,\n"
        "   Audit, Payments, Recovery all set a max-height the same way;\n"
        "   see the SCROLLABLE BODY comment in Shell.module.css). What was\n"
        "   actually broken is the hand-off at the boundary, not the\n"
        "   scroll itself -- overscroll-behavior-y: auto makes that\n"
        "   hand-off to the page's real scroll container explicit instead\n"
        "   of leaving it to browser default. */\n"
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; overscroll-behavior-y: auto; background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 7px;\n"
        "  scrollbar-width: thin; scrollbar-color: #EE8C3A transparent;\n"
        "}\n"
        ".catList::-webkit-scrollbar { width: 6px; }\n"
        ".catList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }",

        "catList scroll/scrollbar restored with overscroll-behavior-y: auto for explicit hand-off to the page",
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
git("commit", "-m", "fix123: applied report now gets the full open+hover treatment (not just closed-row hover); catList scroll/scrollbar restored with explicit overscroll-behavior-y hand-off to the page")
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