#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix120: three corrections to fix118/fix119's Report
# Catalogue list, straight off feedback on the live Render screenshots.
#
#   1. HOVER TEXT COLOR REVERTED. fix119 flipped the open/hover row's
#      name/meta/desc text from white to dark ink, reading that as
#      "reduce the tone." That was a misread -- the ask was the
#      opposite: the grey meta text (row count, tag) should go WHITE
#      on hover for contrast against the solid orange fill, same as
#      fix118 originally had it. Reverted.
#   2. "HOVER CURVE" / WHITE GAP FIXED. fix119 dropped overflow:hidden
#      on .ungrouped/.groupBody and rounded the first/last row's own
#      rowHead corners instead (to dodge a suspected clipping bug).
#      That rounding only applied to rowHead's background -- the row's
#      own left rail sits behind it as a plain square box, so on
#      hover/open the orange fill curved away from the rail's square
#      corner and exposed a sliver of the card's white background at
#      the top-left (and bottom-left on the last row). Back to a plain
#      overflow:hidden on the card -- simplest fix, no seams.
#   3. DEFAULT ROW NO LONGER LOOKS "ACTIVE" WHEN IT ISN'T. The default
#      view row carried its own permanent orange-tinted background +
#      left rail (fix118's .rowDefault) so it always looked selected,
#      even while a completely different report was the one actually
#      applied (shown by its own APPLIED tag). That's confusing --
#      two rows both reading as "current". The default row now looks
#      like any other row at rest; "DEFAULT VIEW: " in its own title
#      is the only thing that marks it as the default.
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
        ".group { display: flex; flex-direction: column; gap: 4px; }\n"
        "/* fix119: overflow:hidden removed -- it could clip a row's own\n"
        "   content (its description line) the moment layout shifted even a\n"
        "   pixel, which is what \"default row description sometimes missing\"\n"
        "   actually was. Rounded corners now live on the first/last row\n"
        "   instead, so nothing inside the card can ever be clipped. */\n"
        ".ungrouped, .groupBody { border-radius: 10px; box-shadow: 0 2px 8px rgba(26,46,48,0.14); background: #fff; }\n"
        ".groupBody .row:first-child .rowHead, .ungrouped .row:first-child .rowHead { border-top-left-radius: 10px; border-top-right-radius: 10px; }\n"
        ".groupBody .row:last-child:not(.rowOpen) .rowHead, .ungrouped .row:last-child:not(.rowOpen) .rowHead { border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }\n"
        ".groupBody .row:last-child.rowOpen .readout, .ungrouped .row:last-child.rowOpen .readout { border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }\n",
        ".group { display: flex; flex-direction: column; gap: 4px; }\n"
        "/* fix120: fix119's first/last-row radius workaround only rounded\n"
        "   rowHead's own background -- the row's left rail behind it stayed\n"
        "   a square box, so on hover/open the orange fill curved away from\n"
        "   the rail's corner and left a sliver of the card's white\n"
        "   background showing through at the top (and bottom on the last\n"
        "   row). Plain overflow:hidden back on the card -- no seams. */\n"
        ".ungrouped, .groupBody { border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(26,46,48,0.14); background: #fff; }\n",
        "fix119's per-row corner-radius workaround (was causing a white gap at the corner on hover) reverted to plain overflow:hidden on the card",
    ),
    (
        ".row.rowOpen:not(.rowApplied) .rowHead .name,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .rows,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .tag,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .chev,\n"
        ".row:not(.rowApplied) .rowHead:hover .name,\n"
        ".row:not(.rowApplied) .rowHead:hover .rows,\n"
        ".row:not(.rowApplied) .rowHead:hover .tag,\n"
        ".row:not(.rowApplied) .rowHead:hover .chev { color: #1a2e30; }\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .desc,\n"
        ".row:not(.rowApplied) .rowHead:hover .desc { color: rgba(26,46,48,0.7); }\n",
        ".row.rowOpen:not(.rowApplied) .rowHead .name,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .rows,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .tag,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .chev,\n"
        ".row:not(.rowApplied) .rowHead:hover .name,\n"
        ".row:not(.rowApplied) .rowHead:hover .rows,\n"
        ".row:not(.rowApplied) .rowHead:hover .tag,\n"
        ".row:not(.rowApplied) .rowHead:hover .chev { color: #fff; }\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .desc,\n"
        ".row:not(.rowApplied) .rowHead:hover .desc { color: rgba(255,255,255,0.85); }\n",
        "fix119's dark-ink hover/open text reverted back to white -- the grey meta text (row count, tag) is meant to turn white against the orange fill, not ink",
    ),
    (
        "/* rowDefault: the one row that should still stand out with nothing\n"
        "   applied or open yet -- a light permanent wash, restating the old\n"
        "   .catRowDef for the shared-card layout. Open/applied rules above\n"
        "   this in the cascade still win once either happens. */\n"
        ".row.rowDefault { border-left-color: rgba(238,140,58,0.6); }\n"
        ".row.rowDefault .rowHead { background: #fdf3e7; }\n",
        "/* fix120: the default row's permanent wash + rail is removed -- it\n"
        "   made the default view look \"active\"/selected at all times, even\n"
        "   while a completely different report was the one actually applied\n"
        "   (its own APPLIED tag showing elsewhere in the list). The default\n"
        "   row now sits at rest like any other row; \"DEFAULT VIEW: \" in its\n"
        "   own title is the only thing marking it as the default. */\n",
        "default row's permanent orange wash/rail removed -- it looked \"active\" even when a different report was actually applied",
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
git("commit", "-m", "fix120: Report Catalogue list -- hover text reverted to white (was wrongly darkened in fix119), fix119's corner-radius workaround reverted to plain overflow:hidden (was leaving a white gap at the corner on hover), default row's permanent active-looking wash/rail removed")
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