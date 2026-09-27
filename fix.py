#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix117: Settings' page LAYOUT matched to Reports, not just
# its panel styling.
#
# fix114 already brought Settings' panels onto Report Studio's gradient
# card / click-anywhere-header language. What it didn't touch was the
# arrangement: Settings still laid its five panels out in a responsive
# two-up grid (workstationGrid), while Reports never does that anywhere --
# ReportHub's .pillarStack and Report Studio's own .studio wrapper are both
# a plain vertical flex column, full width, one panel after another. That
# was the one structural way Settings still didn't match the page it was
# meant to be based on.
#
# This fix:
#   1. .workstationGrid becomes a vertical stack (flex column) instead of
#      an auto-fit grid -- Appearance, Personal Security, Staff Governance,
#      Danger Zone and Recently Deleted Plots now run full-width, top to
#      bottom, the same way Scope/Catalogue/Viewer do on Reports.
#   2. Container max-width trimmed from 1450px to Reports' 1400px so the
#      two pages cap out at the same width.
#   3. The now-dead `.workstationGrid { grid-template-columns: 1fr; }`
#      rule inside the 900px media query is removed -- grid-template-
#      columns has no effect on a flex container, so it was inert as soon
#      as (1) landed.
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

SETTINGS_CSS = os.path.join(SRC, "pages", "settings", "SettingsPage.module.css")


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


# ═══ SettingsPage.module.css -- stacked layout + matched container width ═══
apply_patches(SETTINGS_CSS, [
    (
        "    max-width: 1450px;\n"
        "    margin: 0 auto;\n"
        "    padding: clamp(8px, 2vw, 18px) clamp(8px, 1.6vw, 18px) clamp(32px, 5vw, 56px);\n"
        "    font-family: 'DM Sans', sans-serif;\n"
        "    color: #fff;\n"
        "    animation: secureBoot 0.7s cubic-bezier(0.2, 1, 0.3, 1) both;\n"
        "}",
        "    max-width: 1400px;\n"
        "    margin: 0 auto;\n"
        "    padding: clamp(8px, 2vw, 18px) clamp(8px, 1.6vw, 18px) clamp(32px, 5vw, 56px);\n"
        "    font-family: 'DM Sans', sans-serif;\n"
        "    color: #fff;\n"
        "    animation: secureBoot 0.7s cubic-bezier(0.2, 1, 0.3, 1) both;\n"
        "}",
        "container max-width matched to Reports' 1400px (was 1450px)",
    ),
    (
        "/* ── LAYOUT ─────────────────────────────────────────────────────── */\n"
        ".workstationGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(clamp(280px, 45vw, 500px), 1fr)); gap: var(--gap-xl); align-items: start; }",
        "/* ── LAYOUT ─────────────────────────────────────────────────────── */\n"
        "/* fix117: Reports never lays panels out in a grid -- ReportHub's\n"
        "   .pillarStack and Report Studio's own .studio wrapper are both a\n"
        "   plain vertical flex column, full width, one panel after another.\n"
        "   This used to run two-up above ~1000px, the one structural mismatch\n"
        "   left after fix114 matched the panels' own styling to Report Studio. */\n"
        ".workstationGrid { display: flex; flex-direction: column; gap: var(--gap-xl); align-items: stretch; }",
        "workstationGrid switched from a two-up auto-fit grid to a full-width vertical stack, matching Reports' pillarStack/studio layout",
    ),
    (
        "@media (max-width: 900px) {\n"
        "    .workstationGrid { grid-template-columns: 1fr; }\n"
        "    .dualRow         { grid-template-columns: 1fr 1fr; }\n"
        "}",
        "@media (max-width: 900px) {\n"
        "    .dualRow         { grid-template-columns: 1fr 1fr; }\n"
        "}",
        "dead grid-template-columns rule removed -- workstationGrid is a flex column now, this line had no effect",
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
git("commit", "-m", "fix117: Settings panels stacked full-width (matching Reports' pillarStack/studio layout) instead of running two-up in a grid; container max-width matched to Reports' 1400px")
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