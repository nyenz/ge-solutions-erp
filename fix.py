#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix108: header bar clean rewrite (replaces fix103->fix107 chain).
#
# Root causes found and fixed at the source instead of patched again:
#   1. .header lost `justify-content: space-between` somewhere in the
#      fix104/106 churn. Without it, headerRight (bell / operator card /
#      exit) rendered bunched right next to the logo instead of pinned
#      to the right edge -- which is also why the notification dropdown
#      (anchored to the bell with `right: 0`) rendered near the left
#      edge, on top of the sidebar.
#   2. .header's z-index (80) sat below the sidebar's mobile overlay
#      (100); bumped to 200 so the header (and its dropdown) is always
#      the top-most chrome layer.
#   3. --panel-edge was referenced by six rules but never actually
#      defined (dangling since fix103) -- defined once in :root.
#   4. The bell was two nested boxes: .notificationGroup's own
#      border+background, PLUS an identical border+background on the
#      inner .bellIcon. .bellIcon is now icon-only.
#   5. ROOT OWNER now renders as a distinct solid-orange chip with a
#      shield glyph instead of the same faint grey label every other
#      role gets.
#
# Header.module.css is replaced whole (the fix103-107 patch chain left
# it fragile -- rewriting from one clean source is safer than another
# regex patch). Header.jsx gets two surgical edits: the FiShield import,
# and the ROOT OWNER badge markup.
#
# Runs `npm run build` before committing if node_modules is installed
# (fix76's build-gate rule) and refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HEADER_CSS = os.path.join(ROOT, "erp-frontend", "src", "components", "layout", "Header.module.css")
HEADER_JSX = os.path.join(ROOT, "erp-frontend", "src", "components", "layout", "Header.jsx")

NEW_CSS = """/* PATH: erp-frontend/src/components/layout/Header.module.css */
/* ERP Standard V1 — clamp() everywhere, DM Sans/Space Mono/Cinzel,
   font-weight 800-900 minimum, focus-visible on all interactive.

   fix108: clean rewrite, replacing the fix103->fix107 patch chain.
   Root causes fixed at the source instead of patched again:
     1. .header never had `justify-content: space-between`, so
        headerRight (bell / operator card / exit) rendered bunched
        directly against the logo instead of pinned to the right --
        which is also why the notification dropdown (anchored to the
        bell with `right: 0`) rendered near the left edge, on top of
        the sidebar.
     2. .header's z-index (80) sat BELOW the sidebar's mobile overlay
        (100), so on narrow widths the sidebar drawer could paint over
        the header and its dropdown. Header is now the top-most chrome
        layer (200) — nothing in the app should render above it.
     3. --panel-edge was referenced by six rules but never defined
        (dangling since fix103); defined once, here, in :root.
     4. The bell was two nested boxes (.notificationGroup's own
        border/background PLUS an identical border/background on
        the inner .bellIcon) -- .bellIcon is now icon-only.
     5. ROOT OWNER now reads as a distinct tier (solid orange chip),
        not the same faint grey label as every other role.
   ─────────────────────────────────────────────────────────────────── */

:root {
    /* Header sits outside every page's .container, so it can't inherit
       their page-scoped tokens -- these are the same literal values the
       rest of the app already uses. */
    --panel-bg: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --panel-header: #162a2c;
    --panel-edge: rgba(255, 255, 255, 0.10);
    --accent: var(--orange);
    --accent-ink: var(--text-on-light, #1a2e30);
    --accent-soft: rgba(238, 140, 58, 0.14);
    --ok: #10b981;
    --warn: #f59e0b;
    --warn-soft: rgba(245, 158, 11, 0.12);
    --bad: #ef4444;
    --info: #06b6d4;
    --on-panel: var(--text-on-dark, rgba(244, 242, 239, 0.82));
    --on-panel-soft: var(--text-on-dark-soft, rgba(244, 242, 239, 0.72));
    --on-panel-faint: rgba(244, 242, 239, 0.45);
}

/* ── BAR ──────────────────────────────────────────────────────────── */
.header {
    position: sticky;
    top: 0; left: 0; right: 0;
    z-index: 200; /* fix108: top of the whole chrome stack -- was 80,
                     which lost to the sidebar's mobile overlay (100) */
    display: flex;
    align-items: center;
    justify-content: space-between; /* fix108: the missing rule --
                     this alone is what pins headerRight to the right */
    gap: 12px;
    min-height: 64px;
    padding: 8px 18px;
    background: #162a2c;
    border-bottom: 1.5px solid rgba(238, 140, 58, 0.35);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
}

/* Orange under-glow accent */
.header::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #EE8C3A, transparent);
    opacity: 0.6;
}

.headerLeft,
.headerRight {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1.2vw, 18px);
    flex-shrink: 0;
}

/* ── SIDEBAR TOGGLE ─────────────────────────────────────────────── */
.sidebarToggle {
    width:  clamp(34px, 4vw, 42px);
    height: clamp(34px, 4vw, 42px);
    background: rgba(255, 255, 255, 0.05);
    border: 1.5px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: border-color 0.25s, background 0.25s, color 0.25s;
    color: #fff;
    font-size: clamp(17px, 2vw, 22px);
    flex-shrink: 0;
}
.sidebarToggle:hover {
    border-color: #EE8C3A;
    background: rgba(238, 140, 58, 0.1);
    color: #EE8C3A;
}
.sidebarToggle:focus-visible {
    outline: 2px solid #EE8C3A;
    outline-offset: 2px;
}

/* ── LOGO SECTION ───────────────────────────────────────────────── */
.logoSection {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
}

.logoSmallPulse {
    width:  clamp(28px, 3.2vw, 36px);
    height: clamp(28px, 3.2vw, 36px);
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.pulseInner {
    position: relative;
    z-index: 2;
    font-size: clamp(16px, 2vw, 22px);
    line-height: 1;
}

.pulseRing {
    position: absolute;
    inset: 0;
    border: 1.5px solid #EE8C3A;
    border-radius: 50%;
    animation: hardwarePulse 2.5s infinite ease-out;
}

@keyframes hardwarePulse {
    0%   { transform: scale(1);   opacity: 0.8; }
    100% { transform: scale(1.7); opacity: 0; }
}

/* Cinzel 700 — brand name, per typography standard */
.brandName {
    font-family: 'Cinzel', serif;
    color: #EE8C3A;
    font-size: clamp(13px, 1.4vw, 20px);
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-shadow: 0 0 10px rgba(238, 140, 58, 0.3);
    white-space: nowrap;
}

/* ── NOTIFICATION / RECOVERY SENSOR ────────────────────────────── */
.notifWrap { position: relative; }

/* Single box. fix108: this used to also carry a border+background on
   the icon glyph inside it (.bellIcon), so the bell rendered as two
   stacked squares -- one box now, the glyph is just the glyph. */
.notificationGroup {
    position: relative;
    width:  clamp(34px, 3.8vw, 42px);
    height: clamp(34px, 3.8vw, 42px);
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.03);
    border: 1.5px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    cursor: pointer;
    transition: border-color 0.25s, background 0.25s;
    flex-shrink: 0;
}
.notificationGroup:hover {
    border-color: #EE8C3A;
    background: rgba(238, 140, 58, 0.08);
}
.notificationGroup:focus-visible {
    outline: 2px solid #EE8C3A;
    outline-offset: 2px;
}

/* activeSensor — orange glow when signals are pending */
.activeSensor {
    border-color: rgba(238, 140, 58, 0.4);
    box-shadow: 0 0 12px rgba(238, 140, 58, 0.2);
    animation: sensorPulse 2s ease-in-out infinite;
}
@keyframes sensorPulse {
    0%, 100% { box-shadow: 0 0 12px rgba(238, 140, 58, 0.2); }
    50%       { box-shadow: 0 0 20px rgba(238, 140, 58, 0.45); }
}

.bellIcon {
    font-size: clamp(16px, 1.9vw, 20px);
    color: #EE8C3A;
    opacity: 0.85;
    flex-shrink: 0;
}
.activeSensor .bellIcon { opacity: 1; }

/* Red badge counter */
.badge {
    position: absolute; top: -5px; right: -5px;
    min-width: 18px; height: 18px;
    border-radius: 9px;
    background: #e5484d;
    color: #fff;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    border: 1.5px solid #162a2c;
}

/* ── OPERATOR CARD ──────────────────────────────────────────────── */
.userCard {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    background: rgba(0, 0, 0, 0.25);
    padding: clamp(4px, 0.5vw, 7px) clamp(10px, 1.4vw, 18px);
    border-radius: 10px;
    border: 1.5px solid rgba(255, 255, 255, 0.1);
}

/* Avatar square — orange fill, navy text, always legible */
.avatar {
    width:  clamp(24px, 2.8vw, 32px);
    height: clamp(24px, 2.8vw, 32px);
    background: #EE8C3A;
    color: #1a2e30;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(11px, 1.2vw, 15px);
    box-shadow: 0 0 10px rgba(238, 140, 58, 0.3);
    flex-shrink: 0;
}

.userMeta {
    display: flex;
    flex-direction: column;
    gap: clamp(2px, 0.3vw, 4px);
}

/* DM Sans 800 — UI label per standard */
.userName {
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    font-size: clamp(10px, 1.1vw, 13px);
    font-weight: 800;
    line-height: 1;
    white-space: nowrap;
}

/* Space Mono 900 — metadata tag per standard, for STAFF/MANAGER/DIRECTOR/ADMIN */
.roleTag {
    display: inline-flex;
    align-items: center;
    font-family: 'Space Mono', monospace;
    color: rgba(255, 255, 255, 0.45);
    font-size: clamp(7px, 0.78vw, 9px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1px;
    white-space: nowrap;
}

/* fix108: ROOT OWNER is the top of the role hierarchy -- it now reads
   as a distinct solid chip instead of the same faint grey text every
   other role gets. */
.roleTagRoot {
    color: var(--accent-ink);
    background: linear-gradient(135deg, #EE8C3A, #f5a35c);
    padding: 1px clamp(5px, 0.6vw, 7px);
    border-radius: 4px;
    gap: 3px;
    box-shadow: 0 0 8px rgba(238, 140, 58, 0.35);
}
.roleTagRoot svg { font-size: 9px; }

/* ── SESSION EXIT ───────────────────────────────────────────────── */
.logoutTrigger {
    width:  clamp(34px, 3.8vw, 42px);
    height: clamp(34px, 3.8vw, 42px);
    background: rgba(239, 68, 68, 0.1);
    border: 1.5px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: clamp(15px, 1.8vw, 19px);
    transition: background 0.25s, color 0.25s, box-shadow 0.25s;
    flex-shrink: 0;
}
.logoutTrigger:hover {
    background: #ef4444;
    color: #fff;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.35);
}
.logoutTrigger:focus-visible {
    outline: 2px solid #ef4444;
    outline-offset: 2px;
}

/* ── RESPONSIVE ─────────────────────────────────────────────────── */
@media (max-width: 850px) {
    /* Brand name hides on tablet — logo pulse remains */
    .brandName { display: none; }
}

@media (max-width: 600px) {
    .userCard  { padding: clamp(3px, 1vw, 5px) clamp(6px, 2vw, 10px); }
    .roleTag   { display: none; }
    .header    { padding: 0 clamp(10px, 3vw, 15px); }
}

/* ═══════════════════════════════════════════════════════════════════
   NOTIFICATION CENTRE

   Filters across the top, one icon per type, a relative timestamp on
   every row, and an unread marker that is a shape as well as an
   opacity so it survives the high-contrast setting.
   ═══════════════════════════════════════════════════════════════════ */

.notifDrop {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    z-index: 10;
    min-width: 320px;
    max-width: 380px;
    max-height: min(560px, calc(100vh - var(--header-height, 64px) - 24px));
    display: flex;
    flex-direction: column;
    background: #162a2c;
    border: 1.5px solid rgba(238, 140, 58, 0.35);
    border-radius: 10px;
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
    overflow: hidden;
}

.notifHead {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    padding: 11px 13px;
    background: #101f21;
    border-bottom: 1px solid var(--panel-edge);
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 2px;
    color: #EE8C3A;
    flex-shrink: 0;
}
.notifHeadBtns { display: inline-flex; gap: 5px; }

.notifReadAll {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: transparent;
    border: 1px solid var(--panel-edge);
    color: rgba(255, 255, 255, 0.72);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.16s ease;
}
.notifReadAll:hover { color: #EE8C3A; border-color: #EE8C3A; }

/* ── filters ───────────────────────────────────────────────────────── */
.notifFilters {
    display: flex;
    gap: 5px;
    padding: 9px 11px;
    overflow-x: auto;
    border-bottom: 1px solid var(--panel-edge);
    flex-shrink: 0;
    scrollbar-width: none;
}
.notifFilters::-webkit-scrollbar { display: none; }

.notifChip, .notifChipActive {
    white-space: nowrap;
    border-radius: 20px;
    padding: 4px 11px;
    font-family: 'Inter', sans-serif;
    font-size: 8.5px;
    font-weight: 900;
    letter-spacing: 1.1px;
    cursor: pointer;
    transition: all 0.16s ease;
    border: 1px solid var(--panel-edge);
    background: transparent;
    color: rgba(255, 255, 255, 0.45);
}
.notifChip:hover { color: #EE8C3A; border-color: #EE8C3A; }
.notifChipActive {
    background: #EE8C3A;
    border-color: #EE8C3A;
    color: var(--accent-ink);
}

/* ── list ──────────────────────────────────────────────────────────── */
.notifList {
    overflow-y: auto;
    flex: 1;
    min-height: 0;
}

.notifRow, .notifRowPinned {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--panel-edge);
    padding: 11px 13px;
    cursor: pointer;
    transition: background 0.15s ease;
}
.notifRow:hover, .notifRowPinned:hover { background: rgba(238, 140, 58, 0.14); }
.notifRow:focus-visible, .notifRowPinned:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }

/* The recovery queue is pinned and is not a stored row, so it is marked
   as different rather than pretending to be one of the list. */
.notifRowPinned {
    background: var(--warn-soft);
    border-left: 3px solid #EE8C3A;
}

/* Read rows dim, but the unread ones also carry a dot -- opacity alone
   disappears under the high-contrast setting. */
.notifRead { opacity: 0.5; }

.notifIcon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 7px;
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.07);
    font-size: 13px;
}

.notifBody {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
    flex: 1;
}

.notifType {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #EE8C3A;
}

.notifTime {
    font-family: 'Space Mono', monospace;
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: none;
    color: rgba(255, 255, 255, 0.45);
    flex-shrink: 0;
}

.notifMsg {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: #ffffff;
    line-height: 1.45;
    word-break: break-word;
}

.notifUnreadDot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #EE8C3A;
    flex-shrink: 0;
    margin-top: 6px;
}

.notifEmpty {
    padding: 20px 13px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 2px;
    color: rgba(255, 255, 255, 0.45);
}

@media (max-width: 480px) {
    .notifDrop {
        position: fixed;
        top: var(--header-height);
        left: 8px;
        right: 8px;
        width: auto;
        max-width: none;
        max-height: calc(100vh - var(--header-height) - 16px);
    }
}
"""

with open(HEADER_CSS, "w", encoding="utf-8", newline="\n") as f:
    f.write(NEW_CSS)
print("written: " + os.path.relpath(HEADER_CSS, ROOT))

with open(HEADER_JSX, "r", encoding="utf-8") as f:
    jsx = f.read()

OLD_IMPORT = "import { FiMenu, FiBell, FiLogOut, FiCheck, FiRefreshCw, FiPhoneCall } from 'react-icons/fi';"
NEW_IMPORT = "import { FiMenu, FiBell, FiLogOut, FiCheck, FiRefreshCw, FiPhoneCall, FiShield } from 'react-icons/fi';"

OLD_BADGE = (
    "                        <span className={styles.userName}>{user?.username}</span>\n"
    "                        <span className={styles.roleTag}>{displayRole}</span>"
)
NEW_BADGE = (
    "                        <span className={styles.userName}>{user?.username}</span>\n"
    "                        <span className={`${styles.roleTag} ${isRoot ? styles.roleTagRoot : ''}`}>\n"
    "                            {isRoot && <FiShield aria-hidden=\"true\" />}\n"
    "                            {displayRole}\n"
    "                        </span>"
)

changed = 0
if OLD_IMPORT in jsx:
    jsx = jsx.replace(OLD_IMPORT, NEW_IMPORT, 1)
    changed += 1
elif "FiShield" not in jsx:
    print("WARN: Header.jsx import line did not match expected text -- import not patched, check manually")

if OLD_BADGE in jsx:
    jsx = jsx.replace(OLD_BADGE, NEW_BADGE, 1)
    changed += 1
elif "roleTagRoot" not in jsx:
    print("WARN: Header.jsx role-tag block did not match expected text -- badge not patched, check manually")

if changed:
    with open(HEADER_JSX, "w", encoding="utf-8", newline="\n") as f:
        f.write(jsx)
    print("written: " + os.path.relpath(HEADER_JSX, ROOT) + " (" + str(changed) + " edit(s) applied)")
else:
    print("skip: Header.jsx already matches (or diverged) -- no changes written")

# ═══ build gate (fix76) ═══
FRONTEND = os.path.join(ROOT, "erp-frontend")
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
git("commit", "-m", "fix108: header bar clean rewrite -- right-alignment restored (justify-content: space-between), z-index above sidebar overlay, --panel-edge defined, bell de-duplicated, ROOT OWNER badge")
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
print("fix108 done.")