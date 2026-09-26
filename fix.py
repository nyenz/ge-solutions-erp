#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix109: header/sidebar chrome pass + notification centre cleanup.
#
# What this fixes, and why:
#   1. Header and sidebar were both a flat, near-black solid colour --
#      #162a2c and a plain 180deg teal fade respectively. Both now carry a
#      proper diagonal gradient in the same palette/angle family, so the
#      two pieces of chrome read as one system instead of two different
#      darks bolted together.
#   2. Collapsed, the sidebar footer used to rotate the full "GOLDEN SEED"
#      wordmark 90 degrees to fit a 52px rail -- it either clipped or sat
#      right against the icon column above it. It now just shows "GS" at a
#      normal, upright, small size.
#   3. Sidebar auto-collapse used to be a mobile-only side effect keyed off
#      a pathname diff (so clicking the ALREADY-active route did nothing,
#      and desktop never collapsed at all). Replaced with a direct
#      onClick on every nav link: pick a destination, the panel gets out
#      of the way, on any screen size. IntakePage.jsx had its own
#      page-local copy of the same idea (faking a click on the sidebar's
#      toggle button the first time you touched the form) -- that's
#      redundant now the sidebar does it everywhere, so it's removed.
#   4. Report Studio's panel collapse buttons (SCOPE / REPORT CATALOGUE)
#      were a boxed orange-bordered square -- the only collapse control in
#      the app styled that way. Restyled to match the Intake page's
#      CollapsibleSection chevron: no box, a plain rotating glyph that
#      turns orange on hover/open.
#   5. Notification centre: every row's icon sat in the same flat grey
#      chip regardless of type, so MONEY and RECOVERY and CRITICAL signals
#      were only distinguishable by squinting at a 13px glyph. Icons now
#      sit in a tint of their own severity colour. The dropdown's REFRESH
#      button was also a second way to do what opening the bell already
#      does (openDrop calls pullList), so it's gone -- READ ALL stays.
#
# Every edit below is a surgical find/replace against known-good source
# text (fix108's shape) rather than a full-file rewrite -- the changes are
# small and localised, so a diff-sized patch is safer than reprinting
# whole files and risking a silent regression somewhere the diff didn't
# touch.
#
# Runs `npm run build` before committing if node_modules is installed
# (fix76's build-gate rule) and refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

HEADER_CSS = os.path.join(SRC, "components", "layout", "Header.module.css")
HEADER_JSX = os.path.join(SRC, "components", "layout", "Header.jsx")
SIDEBAR_JSX = os.path.join(SRC, "components", "layout", "Sidebar.jsx")
SIDEBAR_CSS = os.path.join(SRC, "components", "layout", "Sidebar.module.css")
NOTIF_CATALOG = os.path.join(SRC, "components", "common", "notificationCatalog.js")
INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
REPORTS_CSS = os.path.join(SRC, "pages", "Reports", "ReportStudio.module.css")


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


# ═══ 1. Header.module.css -- gradient chrome, dropdown to match ═══
apply_patches(HEADER_CSS, [
    (
        "    min-height: 64px;\n"
        "    padding: 8px 18px;\n"
        "    background: #162a2c;\n"
        "    border-bottom: 1.5px solid rgba(238, 140, 58, 0.35);\n"
        "    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);\n"
        "}",
        "    min-height: 64px;\n"
        "    padding: 8px 18px;\n"
        "    background: linear-gradient(115deg, #14262a 0%, #1c3335 42%, #24454a 78%, #2b5157 100%);\n"
        "    border-bottom: 1.5px solid rgba(238, 140, 58, 0.35);\n"
        "    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);\n"
        "}",
        "header bar: flat colour -> gradient",
    ),
    (
        "    max-height: min(560px, calc(100vh - var(--header-height, 64px) - 24px));\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    background: #162a2c;\n"
        "    border: 1.5px solid rgba(238, 140, 58, 0.35);\n"
        "    border-radius: 10px;\n"
        "    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);\n"
        "    overflow: hidden;\n"
        "}\n"
        "\n"
        ".notifHead {\n"
        "    display: flex;\n"
        "    justify-content: space-between;\n"
        "    align-items: center;\n"
        "    gap: 8px;\n"
        "    padding: 11px 13px;\n"
        "    background: #101f21;\n"
        "    border-bottom: 1px solid var(--panel-edge);",
        "    max-height: min(560px, calc(100vh - var(--header-height, 64px) - 24px));\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    background: linear-gradient(165deg, #182d2f 0%, #1c3335 55%, #213e40 100%);\n"
        "    border: 1.5px solid rgba(238, 140, 58, 0.35);\n"
        "    border-radius: 10px;\n"
        "    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);\n"
        "    overflow: hidden;\n"
        "}\n"
        "\n"
        ".notifHead {\n"
        "    display: flex;\n"
        "    justify-content: space-between;\n"
        "    align-items: center;\n"
        "    gap: 8px;\n"
        "    padding: 11px 13px;\n"
        "    background: rgba(0, 0, 0, 0.22);\n"
        "    border-bottom: 1px solid var(--panel-edge);",
        "notification dropdown + head: flat colours -> gradient",
    ),
    (
        ".notifHeadBtns { display: inline-flex; gap: 5px; }\n\n.notifReadAll {",
        ".notifReadAll {",
        "drop now-unused .notifHeadBtns rule (REFRESH button removed in Header.jsx)",
    ),
])

# ═══ 2. Header.jsx -- drop redundant REFRESH control, tint notif icons ═══
apply_patches(HEADER_JSX, [
    (
        "import { FiMenu, FiBell, FiLogOut, FiCheck, FiRefreshCw, FiPhoneCall, FiShield } from 'react-icons/fi';",
        "import { FiMenu, FiBell, FiLogOut, FiCheck, FiPhoneCall, FiShield } from 'react-icons/fi';",
        "drop unused FiRefreshCw import",
    ),
    (
        "import { describe, routeFor, relativeTime, SEVERITY_COLOR, FILTERS } from '../common/notificationCatalog';",
        "import { describe, routeFor, relativeTime, SEVERITY_COLOR, SEVERITY_BG, FILTERS } from '../common/notificationCatalog';",
        "import SEVERITY_BG for tinted icon chips",
    ),
    (
        "                            <div className={styles.notifHead}>\n"
        "                                <span>SIGNALS</span>\n"
        "                                <span className={styles.notifHeadBtns}>\n"
        "                                    <button type=\"button\" className={styles.notifReadAll} onClick={pullList} aria-label=\"Refresh notifications\">\n"
        "                                        <FiRefreshCw aria-hidden=\"true\" /> REFRESH\n"
        "                                    </button>\n"
        "                                    <button type=\"button\" className={styles.notifReadAll} onClick={readAll}>\n"
        "                                        <FiCheck aria-hidden=\"true\" /> READ ALL\n"
        "                                    </button>\n"
        "                                </span>\n"
        "                            </div>",
        "                            <div className={styles.notifHead}>\n"
        "                                <span>SIGNALS</span>\n"
        "                                {/* Refresh used to sit next to this, but opening the bell already\n"
        "                                    pulls a fresh list (see openDrop) -- a second control that does\n"
        "                                    the same fetch was just clutter. */}\n"
        "                                <button type=\"button\" className={styles.notifReadAll} onClick={readAll}>\n"
        "                                    <FiCheck aria-hidden=\"true\" /> READ ALL\n"
        "                                </button>\n"
        "                            </div>",
        "remove redundant REFRESH button",
    ),
    (
        "                                        <span className={styles.notifIcon} style={{ color: 'var(--warn)' }}>\n"
        "                                            <FiPhoneCall aria-hidden=\"true\" />\n"
        "                                        </span>",
        "                                        <span className={styles.notifIcon} style={{ color: 'var(--warn)', background: 'var(--warn-soft)' }}>\n"
        "                                            <FiPhoneCall aria-hidden=\"true\" />\n"
        "                                        </span>",
        "tint the pinned recovery-queue icon",
    ),
    (
        "                                            <span className={styles.notifIcon}\n"
        "                                                style={{ color: SEVERITY_COLOR[meta.severity] || 'var(--info)' }}>\n"
        "                                                <Icon aria-hidden=\"true\" />\n"
        "                                            </span>",
        "                                            <span className={styles.notifIcon}\n"
        "                                                style={{\n"
        "                                                    color: SEVERITY_COLOR[meta.severity] || 'var(--info)',\n"
        "                                                    background: SEVERITY_BG[meta.severity] || SEVERITY_BG.INFO,\n"
        "                                                }}>\n"
        "                                                <Icon aria-hidden=\"true\" />\n"
        "                                            </span>",
        "tint every notification row's icon by severity",
    ),
])

# ═══ 3. notificationCatalog.js -- add the SEVERITY_BG tint map ═══
apply_patches(NOTIF_CATALOG, [
    (
        "export const SEVERITY_COLOR = {\n"
        "    POSITIVE: 'var(--ok)',\n"
        "    WARN:     'var(--warn)',\n"
        "    CRITICAL: 'var(--bad)',\n"
        "    INFO:     'var(--info)',\n"
        "};\n",
        "export const SEVERITY_COLOR = {\n"
        "    POSITIVE: 'var(--ok)',\n"
        "    WARN:     'var(--warn)',\n"
        "    CRITICAL: 'var(--bad)',\n"
        "    INFO:     'var(--info)',\n"
        "};\n"
        "\n"
        "/* Tinted icon chips, not the same flat grey square for every row -- the\n"
        "   colour is the fastest way to tell \"money came in\" from \"something is\n"
        "   overdue\" without reading the label first. */\n"
        "export const SEVERITY_BG = {\n"
        "    POSITIVE: 'rgba(16, 185, 129, 0.16)',\n"
        "    WARN:     'rgba(245, 158, 11, 0.16)',\n"
        "    CRITICAL: 'rgba(239, 68, 68, 0.16)',\n"
        "    INFO:     'rgba(6, 182, 212, 0.16)',\n"
        "};\n",
        "add SEVERITY_BG tint map",
    ),
])

# ═══ 4. Sidebar.jsx -- collapse on nav click (any device), "GS" when collapsed ═══
apply_patches(SIDEBAR_JSX, [
    (
        "import React, { useEffect, useRef } from 'react';\n"
        "import { NavLink, useNavigate, useLocation } from 'react-router-dom';",
        "import React from 'react';\n"
        "import { NavLink, useNavigate } from 'react-router-dom';",
        "drop imports the mobile-only pathname-diff effect needed",
    ),
    (
        "    const { user }  = useAuth();\n"
        "    const navigate  = useNavigate();\n"
        "    const location  = useLocation();\n"
        "\n"
        "    const isCollapsedRef = useRef(isCollapsed);\n"
        "    const onToggleRef    = useRef(onToggle);\n"
        "    useEffect(() => { isCollapsedRef.current = isCollapsed; }, [isCollapsed]);\n"
        "    useEffect(() => { onToggleRef.current    = onToggle;    }, [onToggle]);\n"
        "\n"
        "    const isMobile = () => typeof window !== 'undefined' && window.innerWidth <= 768;\n"
        "    const prevPathRef = useRef(location.pathname);\n"
        "\n"
        "    useEffect(() => {\n"
        "        const currentPath = location.pathname;\n"
        "        const prevPath    = prevPathRef.current;\n"
        "        if (currentPath !== prevPath) {\n"
        "            prevPathRef.current = currentPath;\n"
        "            if (isMobile() && !isCollapsedRef.current && typeof onToggleRef.current === 'function') {\n"
        "                onToggleRef.current();\n"
        "            }\n"
        "        }\n"
        "    }, [location.pathname]);\n"
        "\n"
        "    const isLocked           = user?.mustChangePassword;",
        "    const { user }  = useAuth();\n"
        "    const navigate  = useNavigate();\n"
        "\n"
        "    const isMobile = () => typeof window !== 'undefined' && window.innerWidth <= 768;\n"
        "\n"
        "    const isLocked           = user?.mustChangePassword;",
        "replace mobile-only pathname-diff auto-collapse with a plain flag",
    ),
    (
        "        navigate('/settings');\n"
        "    };\n"
        "\n"
        "    const showBackdrop = isMobile() && !isCollapsed;",
        "        navigate('/settings');\n"
        "    };\n"
        "\n"
        "    /* Picking a destination is the end of a sidebar interaction -- the panel\n"
        "       should get out of the page's way the moment you commit to somewhere,\n"
        "       on desktop as well as mobile, instead of sitting open until someone\n"
        "       remembers to collapse it by hand. */\n"
        "    const handleNavClick = () => {\n"
        "        if (!isCollapsed && typeof onToggle === 'function') onToggle();\n"
        "    };\n"
        "\n"
        "    const showBackdrop = isMobile() && !isCollapsed;",
        "add handleNavClick",
    ),
    (
        "                                        onClick={locked ? (e) => handleLockedClick(e, item) : undefined}>",
        "                                        onClick={locked ? (e) => handleLockedClick(e, item) : handleNavClick}>",
        "wire handleNavClick onto every unlocked nav link",
    ),
    (
        '                    <div className={styles.branding} aria-hidden="true">GOLDEN SEED</div>',
        "                    <div className={styles.branding} aria-hidden=\"true\">{isCollapsed ? 'GS' : 'GOLDEN SEED'}</div>",
        "collapsed branding: 'GS' instead of the rotated full wordmark",
    ),
])

# ═══ 5. Sidebar.module.css -- gradient to match header, no more rotated branding ═══
apply_patches(SIDEBAR_CSS, [
    (
        "    background: linear-gradient(180deg, #1a2e30 0%, #162a2c 50%, #1a2e30 100%);",
        "    background: linear-gradient(165deg, #16292b 0%, #1c3335 45%, #213e40 100%);",
        "sidebar background: match header's gradient family",
    ),
    (
        "/* Space Mono 900 — brand serial number style */\n"
        ".branding {\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    color: #EE8C3A;\n"
        "    font-size: clamp(7px, 0.75vw, 9px);\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 3px;\n"
        "    text-transform: uppercase;\n"
        "    transition: transform 0.4s ease, font-size 0.4s ease;\n"
        "    white-space: nowrap;\n"
        "}\n"
        ".collapsed .branding {\n"
        "    transform: rotate(-90deg);\n"
        "    font-size: clamp(6px, 0.65vw, 7px);\n"
        "    letter-spacing: 6px;\n"
        "}",
        "/* Space Mono 900 — brand serial number style. Collapsed, this shrinks to\n"
        "   the initials rather than rotating the full wordmark -- rotated text at\n"
        "   52px wide either clipped or crowded the icon column above it. */\n"
        ".branding {\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    color: #EE8C3A;\n"
        "    font-size: clamp(7px, 0.75vw, 9px);\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 3px;\n"
        "    text-transform: uppercase;\n"
        "    transition: font-size 0.3s ease, letter-spacing 0.3s ease;\n"
        "    white-space: nowrap;\n"
        "}\n"
        ".collapsed .branding {\n"
        "    font-size: 12px;\n"
        "    letter-spacing: 1px;\n"
        "}",
        "branding: drop the 90deg rotate, shrink to 'GS' size instead",
    ),
])

# ═══ 6. IntakePage.jsx -- drop the now-redundant page-local auto-collapse ═══
apply_patches(INTAKE_JSX, [
    (
        "    const collapsedOnce = useRef(false);\n"
        "    useEffect(() => {\n"
        "        const el = topRef.current;\n"
        "        if (!el) return;\n"
        "        const handler = () => {\n"
        "            if (collapsedOnce.current) return;\n"
        "            collapsedOnce.current = true;\n"
        "            const aside = document.querySelector('aside');\n"
        "            const toggle = document.querySelector('[class*=\"sidebarToggle\"]');\n"
        "            if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();\n"
        "        };\n"
        "        el.addEventListener('focusin', handler);\n"
        "        el.addEventListener('input', handler);\n"
        "        el.addEventListener('click', handler);\n"
        "        return () => { el.removeEventListener('focusin', handler); el.removeEventListener('input', handler); el.removeEventListener('click', handler); };\n"
        "    }, []);\n"
        "\n"
        "    useEffect(() => {",
        "    /* This page used to fake a click on the sidebar's own toggle button the\n"
        "       first time you touched the form, as a one-off workaround so the panel\n"
        "       wasn't eating width while you filled this in. The sidebar now collapses\n"
        "       itself on any nav click, on every page, so the page-local version of\n"
        "       the same behaviour was just a second way of doing the same thing. */\n"
        "\n"
        "    useEffect(() => {",
        "remove redundant page-local sidebar auto-collapse hack",
    ),
])

# ═══ 7. ReportStudio.module.css -- panel toggles to match Intake's chevron ═══
apply_patches(REPORTS_CSS, [
    (
        ".headToggle {\n"
        "  margin-left: auto; display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 6px; cursor: pointer; flex-shrink: 0; border: 1.5px solid #EE8C3A; background: #162a2c; color: #EE8C3A; transition: all 0.2s ease;\n"
        "}\n"
        ".headToggle:hover { background: #EE8C3A; color: #1a2e30; }\n"
        ".headToggle svg {\n"
        "  width: 14px; height: 14px; transition: transform 0.2s;\n"
        "}",
        "/* Matches the Intake page's CollapsibleSection chevron: a plain rotating\n"
        "   glyph, not a boxed button -- was the odd one out, styled as a separate\n"
        "   orange square unlike every other collapse control in the app. */\n"
        ".headToggle {\n"
        "  margin-left: auto; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; flex-shrink: 0; border: none; background: transparent; color: rgba(255, 255, 255, 0.45); transition: color 0.2s ease, background 0.2s ease;\n"
        "}\n"
        ".headToggle:hover { background: rgba(238, 140, 58, 0.14); color: #EE8C3A; }\n"
        ".headToggle svg {\n"
        "  width: 16px; height: 16px; transition: transform 0.2s ease;\n"
        "}\n"
        ".headToggle .pickIconOpen { color: #EE8C3A; }",
        "restyle SCOPE/CATALOGUE panel toggles to match Intake's chevron",
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
git("commit", "-m", "fix109: header/sidebar gradient chrome, GS collapsed branding, sidebar auto-collapse on nav click, Report Studio panel toggles matched to Intake chevron, notification centre re-tinted + REFRESH removed")
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
print("fix109 done.")