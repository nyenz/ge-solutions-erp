#!/usr/bin/env python3
# PATH: fix130.py
# GOLDEN SEED -- fix130: SIGNALS dropdown re-skinned onto the same
#   backbone fix127/fix128 gave the Settings page -- one shared cream
#   baseline, bounded mini-cards with a real border (not just a
#   shadow), and a 2px accent rule under the heading instead of a
#   near-invisible one. Nothing about the panel's own identity changes
#   (light glass card, per-group icon/left-edge/dot tinting, pinned
#   Recovery row) -- just its construction details brought in line with
#   the rest of the app instead of predating that language.
#     1. Tray cream unified to #f2ede4 -- the exact value Report
#        Catalogue's catList and Settings' prefGroupBox already use.
#        Was #f4efe8, close enough to look like a mismatch, not a
#        second intentional tone.
#     2. SIGNALS heading's border-bottom was 1px at 10% black --
#        barely there. Now a 2px solid orange rule, the same
#        heading-divider Settings' prefGroupLabel uses under DISPLAY /
#        INTERACTION / NOTIFICATIONS.
#     3. Notification rows relied on box-shadow alone for definition,
#        no border -- inconsistent with every bounded mini-card
#        Settings now uses. Rows get the same rgba(26,46,48,0.12)
#        border (shadow kept, for the hover lift); the pinned Recovery
#        row's border tints orange instead of neutral, since it's
#        already visually special.
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
        # 1. tray cream unified to the app-wide baseline.
        "background: #f4efe8;",
        "background: #f2ede4; /* fix130: unified cream baseline w/ Settings + Report Catalogue */",
        "notifList background unified to #f2ede4",
    ),
    (
        # 2. heading divider -> Settings' 2px accent-rule language.
        "    border-bottom: 1px solid rgba(26, 46, 48, 0.1);\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 2px;\n"
        "    color: #1a2e30;\n"
        "    flex-shrink: 0;\n"
        "}\n"
        ".notifReadAll {",

        "    border-bottom: 2px solid #EE8C3A; /* fix130: Settings' prefGroupLabel divider language */\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 2px;\n"
        "    color: #1a2e30;\n"
        "    flex-shrink: 0;\n"
        "}\n"
        ".notifReadAll {",

        "notifHead heading divider strengthened to a 2px accent rule",
    ),
    (
        # 3. rows get a real border, matching Settings' bounded
        # mini-cards, alongside the existing hover shadow/lift.
        ".notifRow, .notifRowPinned {\n"
        "    display: flex;\n"
        "    align-items: flex-start;\n"
        "    gap: 10px;\n"
        "    width: 100%;\n"
        "    text-align: left;\n"
        "    background: #ffffff;\n"
        "    border: none;\n"
        "    border-left: 4px solid transparent;\n"
        "    border-radius: 9px;\n"
        "    padding: 10px 12px;\n"
        "    cursor: pointer;\n"
        "    box-shadow: 0 2px 7px rgba(26, 46, 48, 0.1);\n"
        "    transition: box-shadow 0.2s ease, transform 0.2s ease;\n"
        "}",

        ".notifRow, .notifRowPinned {\n"
        "    display: flex;\n"
        "    align-items: flex-start;\n"
        "    gap: 10px;\n"
        "    width: 100%;\n"
        "    text-align: left;\n"
        "    background: #ffffff;\n"
        "    border: 1px solid rgba(26, 46, 48, 0.12); /* fix130: bounded mini-card, matches Settings' prefRow */\n"
        "    border-left: 4px solid transparent;\n"
        "    border-radius: 9px;\n"
        "    padding: 10px 12px;\n"
        "    cursor: pointer;\n"
        "    box-shadow: 0 2px 7px rgba(26, 46, 48, 0.1);\n"
        "    transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;\n"
        "}",

        "notifRow/notifRowPinned gained a real border, not shadow-only",
    ),
    (
        # 4. pinned row's border tints orange to match its already
        # special treatment instead of the neutral default.
        ".notifRowPinned {\n"
        "    background: #fff7ed;\n"
        "    border-left: 4px solid #EE8C3A;\n"
        "}",

        ".notifRowPinned {\n"
        "    background: #fff7ed;\n"
        "    border-color: rgba(238, 140, 58, 0.3);\n"
        "    border-left: 4px solid #EE8C3A;\n"
        "}",

        "notifRowPinned border tinted orange",
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
git("commit", "-m", "fix130: SIGNALS dropdown re-skinned onto the Settings-page backbone -- unified #f2ede4 cream, 2px accent heading divider, bordered mini-card rows (pinned row's border tinted orange)")
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