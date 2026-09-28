#!/usr/bin/env python3
# PATH: fix133.py
# GOLDEN SEED -- fix133: NOTIFICATION DRAWER -- match the approved prototype.
#   fix131 already built the hero / chips / day-grouped drawer. Diffed
#   against "GE ERP - Notification Drawer.html" three things still differ:
#
#     1. RECOVERY QUEUE ROW. It was a dark gradient "pinned" card. In the
#        prototype it is an ordinary unread row of the RECOVERY group
#        (orange tint, orange type heading, unread dot, time tag). It still
#        sits at the top of the list and still opens /recovery.
#     2. UNREAD DOT RING. The 3px ring around the dot was hard-coded orange
#        for every group. It now takes the row's own group colour (--t).
#     3. TIME TAG. Timestamp colour is the prototype's muted #5b6b69.
#
#   Deliberately NOT changed (prototype differs, app rules win):
#     - Scrollbar stays the app's orange thumb (UI uniformity rule,
#       Shell.scrollArea). The prototype's grey thumb is not used.
#     - Message font stays Inter (app body font). Prototype used DM Sans.
#     - Bell dot text stays dark ink (contrast on the light group colours).
#
# Frontend only (Header.jsx + Header.module.css), no backend.
#
# Atomic: every patch for both files is matched in memory first; if any
# one is MISSING nothing is written and nothing is committed. Runs
# `npm run build` before committing if node_modules is installed and
# refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

HEADER_JSX = os.path.join(SRC, "components", "layout", "Header.jsx")
HEADER_CSS = os.path.join(SRC, "components", "layout", "Header.module.css")

MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sub(text, old, new, desc):
    """Exact find/replace, first occurrence. Prints OK / SKIP / MISSING."""
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


def between(text, start, end, new, desc):
    """Replace everything from `start` up to (not including) `end`."""
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    i = text.find(start)
    j = text.find(end, i + 1) if i >= 0 else -1
    if i >= 0 and j > i:
        print("OK: " + desc)
        return text[:i] + new + text[j:]
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


# ======================================================================
# Header.jsx
# ======================================================================
jsx0 = read(HEADER_JSX)
jsx = jsx0

jsx = sub(jsx,
          " * fix131: the dropdown is now a hero",
          " * fix133: the recovery queue is a normal RECOVERY-tinted unread row (same\n"
          " * markup and classes as every other row), not a dark pinned card.\n"
          " *\n"
          " * fix131: the dropdown is now a hero",
          "Header.jsx doc comment")

jsx = between(jsx,
              "                                {hasPinned && (\n",
              "                                {loading && <div className={styles.notifEmpty}>SYNCING...</div>}",
              r'''                                {hasPinned && (
                                    <button
                                        type="button"
                                        data-group="RECOVERY"
                                        className={`${styles.notifRow} ${styles.notifUnread}`}
                                        style={{ '--t': GROUP_COLOR.RECOVERY }}
                                        onClick={() => { setNotifOpen(false); navigate('/recovery'); }}
                                    >
                                        <span className={styles.notifBody}>
                                            <span className={styles.notifType}>
                                                Recovery queue
                                                <time className={styles.notifTime}>NOW</time>
                                            </span>
                                            <span className={styles.notifMsg}>
                                                {staleCount} mission{staleCount > 1 ? 's' : ''} due now
                                            </span>
                                        </span>
                                        <span className={styles.notifUnreadDot} aria-label="Unread" />
                                    </button>
                                )}

''',
              "recovery queue: dark pinned card -> normal group-tinted unread row")

# ======================================================================
# Header.module.css
# ======================================================================
css0 = read(HEADER_CSS)
css = css0

css = sub(css,
          ".notifRow, .notifRowPinned {\n",
          ".notifRow {\n",
          "row base selector (pinned class gone)")

css = sub(css,
          ".notifRow:focus-visible,\n.notifRowPinned:focus-visible, .notifFoot:focus-visible",
          ".notifRow:focus-visible,\n.notifFoot:focus-visible",
          "focus-visible list (pinned class gone)")

css = between(css,
              "/* The recovery queue is pinned and is not a stored row",
              ".notifEmpty {",
              "/* fix133: the recovery queue row reuses .notifRow / .notifUnread -- no\n"
              "   separate pinned styling. */\n\n",
              "remove dark pinned-row CSS")

css = sub(css,
          "    text-transform: none;\n    color: rgba(26, 46, 48, 0.55);\n",
          "    text-transform: none;\n    color: #5b6b69;\n",
          "time tag colour -> prototype muted")

css = sub(css,
          "    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.22);\n",
          "    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.22);\n"
          "    box-shadow: 0 0 0 3px color-mix(in srgb, var(--t, #EE8C3A) 24%, transparent);\n",
          "unread dot ring follows the group colour")

# ======================================================================
# write (atomic) + build gate + commit
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix131).")
    sys.exit(1)

if jsx != jsx0:
    write(HEADER_JSX, jsx)
    print("written: erp-frontend/src/components/layout/Header.jsx")
if css != css0:
    write(HEADER_CSS, css)
    print("written: erp-frontend/src/components/layout/Header.module.css")
if jsx == jsx0 and css == css0:
    print("note: nothing changed -- fix133 already applied")

# build gate (fix76)
if os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
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
git("commit", "-m", "fix133: notification drawer matches prototype -- recovery queue is a normal RECOVERY-tinted unread row (no dark pinned card), unread dot ring follows group colour, muted time tag")
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip() or "pushed")