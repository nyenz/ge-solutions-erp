#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix110: sidebar auto-collapse moved to content click,
# notification centre re-tinted by group instead of severity, Report
# Studio's SCOPE / REPORT CATALOGUE panels matched to Intake's
# CollapsibleSection (corner deco, curved collapse, header hover).
#
# What this fixes, and why:
#   1. Sidebar auto-collapse (fix109) fired on the nav link's own onClick,
#      so the panel vanished the instant you picked a destination -- before
#      the new page had even rendered. Moved to Shell: the sidebar now
#      stays open through the navigation, and only collapses on the FIRST
#      click inside the page content itself. Expand it, pick a link, land
#      on the page still open, then the next click anywhere in the content
#      area (not the sidebar) is what tucks it away.
#   2. Notification centre: every row was tinted by SEVERITY, and most of
#      the catalog's ~25 types fall into only two severities (INFO / WARN),
#      so a payment, a new intake and a document upload all rendered in the
#      same cyan chip -- "different types, same colour" was true. Rows are
#      now tinted by GROUP (MONEY / PIPELINE / RECOVERY / STAFF / SYSTEM),
#      five real colour families instead of two, with a CRITICAL severity
#      still adding its own ring so a plot deletion or system wipe stands
#      out regardless of which group it landed in. The dropdown's own
#      background was also a near-black gradient distinct from every other
#      panel in the app -- it now reuses the exact teal gradient Intake's
#      CollapsibleSection panels use, and the head bar goes solid
#      #162a2c (that panel family's own header colour) instead of a black
#      overlay, so the bell reads as the same system as everything else
#      instead of a darker box bolted on top of it.
#   3. Report Studio's SCOPE and REPORT CATALOGUE panels diverged from
#      Intake's CollapsibleSection in three ways once you collapsed them:
#      the corner-deco brackets and pins were mounted unconditionally at
#      the panel root, so they kept floating at the bottom of the (now
#      short) collapsed panel instead of disappearing with the body; the
#      head row stayed rounded on top only, so a collapsed panel had a
#      flat bottom edge instead of reading as one closed, fully-curved
#      box; and the toggle button itself had its own hover halo, a hover
#      state Intake's plain chevron never had. All three are now brought
#      in line with Intake: the corner deco only renders while the panel
#      is open, a shared .panelCollapsed marker gives the collapsed head
#      row full corner rounding and drops its now-orphaned orange
#      underline, and the toggle's hover halo is gone in favour of the
#      same feedback Intake gives -- hovering the head turns its title
#      white.
#
# Every edit below is a surgical find/replace against known-good source
# text (fix109's shape) rather than a full-file rewrite.
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
SHELL_JSX = os.path.join(SRC, "components", "layout", "Shell.jsx")
NOTIF_CATALOG = os.path.join(SRC, "components", "common", "notificationCatalog.js")
REPORTS_JSX = os.path.join(SRC, "pages", "Reports", "ReportStudio.jsx")
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


# ═══ 1. Sidebar.jsx -- drop the collapse-on-nav-click side effect ═══
apply_patches(SIDEBAR_JSX, [
    (
        "    /* Picking a destination is the end of a sidebar interaction -- the panel\n"
        "       should get out of the page's way the moment you commit to somewhere,\n"
        "       on desktop as well as mobile, instead of sitting open until someone\n"
        "       remembers to collapse it by hand. */\n"
        "    const handleNavClick = () => {\n"
        "        if (!isCollapsed && typeof onToggle === 'function') onToggle();\n"
        "    };\n"
        "\n"
        "    const showBackdrop = isMobile() && !isCollapsed;",
        "    /* Collapsing here, on the nav link's own click, used to make the panel\n"
        "       vanish before the new page had even rendered. That auto-collapse now\n"
        "       lives in Shell instead, keyed off the first click INSIDE the page\n"
        "       content -- so picking a link still shows you where you landed with\n"
        "       the panel open, and it only gets out of the way once you start\n"
        "       actually working the page. */\n"
        "    const showBackdrop = isMobile() && !isCollapsed;",
        "remove collapse-on-nav-click, moved to Shell's content click",
    ),
    (
        "                                        onClick={locked ? (e) => handleLockedClick(e, item) : handleNavClick}>",
        "                                        onClick={locked ? (e) => handleLockedClick(e, item) : undefined}>",
        "unlocked nav links: plain navigation, no side effect",
    ),
])

# ═══ 2. Shell.jsx -- auto-collapse on the first click inside page content ═══
apply_patches(SHELL_JSX, [
    (
        "    const handleSidebarToggle = () => setIsCollapsed(prev => !prev);\n"
        "\n"
        "    return (",
        "    const handleSidebarToggle = () => setIsCollapsed(prev => !prev);\n"
        "\n"
        "    /* The sidebar no longer collapses itself the instant a nav link is\n"
        "       clicked -- picking a destination should still leave the panel open\n"
        "       while the new page loads. It's the first click INSIDE the page\n"
        "       content itself, once you're actually there working the page, that\n"
        "       clears the panel out of the way. */\n"
        "    const handleContentClick = () => {\n"
        "        if (!isCollapsed) setIsCollapsed(true);\n"
        "    };\n"
        "\n"
        "    return (",
        "add handleContentClick",
    ),
    (
        "                {/*\n"
        "                  onToggle is passed to Sidebar so it can collapse itself\n"
        "                  on mobile when the user navigates to a new page — without\n"
        "                  needing the user to manually press the hamburger again.\n"
        "                */}\n"
        "                <Sidebar\n"
        "                    isCollapsed={isCollapsed}\n"
        "                    onToggle={handleSidebarToggle}\n"
        "                />\n"
        "\n"
        "                <main className={styles.mainContent}>",
        "                {/*\n"
        "                  onToggle is passed to Sidebar purely for its mobile backdrop\n"
        "                  -- tapping outside the open drawer still closes it right\n"
        "                  away. Auto-collapse on navigation now lives below instead,\n"
        "                  on the content area itself (handleContentClick).\n"
        "                */}\n"
        "                <Sidebar\n"
        "                    isCollapsed={isCollapsed}\n"
        "                    onToggle={handleSidebarToggle}\n"
        "                />\n"
        "\n"
        "                <main className={styles.mainContent} onClick={handleContentClick}>",
        "wire handleContentClick onto <main>",
    ),
])

# ═══ 3. notificationCatalog.js -- add a GROUP colour family ═══
apply_patches(NOTIF_CATALOG, [
    (
        "/* Tinted icon chips, not the same flat grey square for every row -- the\n"
        "   colour is the fastest way to tell \"money came in\" from \"something is\n"
        "   overdue\" without reading the label first. */\n"
        "export const SEVERITY_BG = {\n"
        "    POSITIVE: 'rgba(16, 185, 129, 0.16)',\n"
        "    WARN:     'rgba(245, 158, 11, 0.16)',\n"
        "    CRITICAL: 'rgba(239, 68, 68, 0.16)',\n"
        "    INFO:     'rgba(6, 182, 212, 0.16)',\n"
        "};\n"
        "\n"
        "/* Ordered loosely by how often the office sees them. */",
        "/* Tinted icon chips, not the same flat grey square for every row -- the\n"
        "   colour is the fastest way to tell \"money came in\" from \"something is\n"
        "   overdue\" without reading the label first. */\n"
        "export const SEVERITY_BG = {\n"
        "    POSITIVE: 'rgba(16, 185, 129, 0.16)',\n"
        "    WARN:     'rgba(245, 158, 11, 0.16)',\n"
        "    CRITICAL: 'rgba(239, 68, 68, 0.16)',\n"
        "    INFO:     'rgba(6, 182, 212, 0.16)',\n"
        "};\n"
        "\n"
        "/* Severity alone collapses most of the catalog onto two colours -- the\n"
        "   large majority of types below are either INFO or WARN, so a payment,\n"
        "   a new intake and a document upload all rendered in the same cyan chip.\n"
        "   GROUP gives five real colour families (money / pipeline / recovery /\n"
        "   staff / system) that line up with how the bell is already filtered,\n"
        "   so the tint tells you the same story the filter chips do. */\n"
        "export const GROUP_COLOR = {\n"
        "    MONEY:    '#22c55e',\n"
        "    PIPELINE: '#38bdf8',\n"
        "    RECOVERY: '#f97316',\n"
        "    STAFF:    '#a78bfa',\n"
        "    SYSTEM:   '#f43f5e',\n"
        "};\n"
        "\n"
        "export const GROUP_BG = {\n"
        "    MONEY:    'rgba(34, 197, 94, 0.16)',\n"
        "    PIPELINE: 'rgba(56, 189, 248, 0.16)',\n"
        "    RECOVERY: 'rgba(249, 115, 22, 0.16)',\n"
        "    STAFF:    'rgba(167, 139, 250, 0.16)',\n"
        "    SYSTEM:   'rgba(244, 63, 94, 0.16)',\n"
        "};\n"
        "\n"
        "/* Ordered loosely by how often the office sees them. */",
        "add GROUP_COLOR / GROUP_BG",
    ),
])

# ═══ 4. Header.jsx -- tint notification icons by group, not severity ═══
apply_patches(HEADER_JSX, [
    (
        "import { describe, routeFor, relativeTime, SEVERITY_COLOR, SEVERITY_BG, FILTERS } from '../common/notificationCatalog';",
        "import { describe, routeFor, relativeTime, GROUP_COLOR, GROUP_BG, SEVERITY_COLOR, FILTERS } from '../common/notificationCatalog';",
        "import GROUP_COLOR / GROUP_BG, drop unused SEVERITY_BG",
    ),
    (
        "                                        <span className={styles.notifIcon} style={{ color: 'var(--warn)', background: 'var(--warn-soft)' }}>\n"
        "                                            <FiPhoneCall aria-hidden=\"true\" />\n"
        "                                        </span>",
        "                                        <span className={styles.notifIcon} style={{ color: GROUP_COLOR.RECOVERY, background: GROUP_BG.RECOVERY }}>\n"
        "                                            <FiPhoneCall aria-hidden=\"true\" />\n"
        "                                        </span>",
        "pinned recovery-queue icon: RECOVERY group colour",
    ),
    (
        "                                            <span className={styles.notifIcon}\n"
        "                                                style={{\n"
        "                                                    color: SEVERITY_COLOR[meta.severity] || 'var(--info)',\n"
        "                                                    background: SEVERITY_BG[meta.severity] || SEVERITY_BG.INFO,\n"
        "                                                }}>\n"
        "                                                <Icon aria-hidden=\"true\" />\n"
        "                                            </span>",
        "                                            <span className={styles.notifIcon}\n"
        "                                                style={{\n"
        "                                                    color: GROUP_COLOR[meta.group] || SEVERITY_COLOR[meta.severity] || 'var(--info)',\n"
        "                                                    background: GROUP_BG[meta.group] || 'rgba(6, 182, 212, 0.16)',\n"
        "                                                    boxShadow: meta.severity === 'CRITICAL' ? '0 0 0 1.5px rgba(244, 63, 94, 0.6)' : 'none',\n"
        "                                                }}>\n"
        "                                                <Icon aria-hidden=\"true\" />\n"
        "                                            </span>",
        "tint every notification row's icon by GROUP, CRITICAL keeps its own ring",
    ),
])

# ═══ 5. Header.module.css -- dropdown rejoins the app's real panel palette ═══
apply_patches(HEADER_CSS, [
    (
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
        "    max-height: min(560px, calc(100vh - var(--header-height, 64px) - 24px));\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    /* Same teal gradient Intake's CollapsibleSection panels use -- this used\n"
        "       to be its own near-black gradient, the one panel in the app that\n"
        "       didn't share the family. */\n"
        "    background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);\n"
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
        "    /* That same panel family's own header colour, not a black overlay. */\n"
        "    background: #162a2c;\n"
        "    border-bottom: 1px solid var(--panel-edge);",
        "notification dropdown + head: rejoin the Intake panel palette",
    ),
])

# ═══ 6. ReportStudio.jsx -- corner deco only while open ═══
apply_patches(REPORTS_JSX, [
    (
        "      <div className={styles.scopePanel}>\n"
        "        <CornerDecor hideTop />\n"
        "        <div className={styles.panelHeadRow}>\n"
        "          <span className={styles.scopeTitle}>SCOPE</span>",
        "      <div className={scopeOpen ? styles.scopePanel : styles.scopePanel + ' ' + styles.panelCollapsed}>\n"
        "        {scopeOpen && <CornerDecor hideTop />}\n"
        "        <div className={styles.panelHeadRow}>\n"
        "          <span className={styles.scopeTitle}>SCOPE</span>",
        "SCOPE panel: corner deco only while open, closed marker for CSS",
    ),
    (
        "      <div className={(catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.catPanelClosed)}>\n"
        "        <CornerDecor hideTop />\n"
        "        <div className={styles.panelHeadRow}>\n"
        "          <span className={styles.scopeTitle}>REPORT CATALOGUE</span>",
        "      <div className={(catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.catPanelClosed + ' ' + styles.panelCollapsed)}>\n"
        "        {catOpen && <CornerDecor hideTop />}\n"
        "        <div className={styles.panelHeadRow}>\n"
        "          <span className={styles.scopeTitle}>REPORT CATALOGUE</span>",
        "REPORT CATALOGUE panel: corner deco only while open, same closed marker",
    ),
])

# ═══ 7. ReportStudio.module.css -- collapsed curve, no arrow hover, header hover ═══
apply_patches(REPORTS_CSS, [
    (
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
        "/* Matches the Intake page's CollapsibleSection chevron: a plain rotating\n"
        "   glyph, not a boxed button -- was the odd one out, styled as a separate\n"
        "   orange square unlike every other collapse control in the app. No hover\n"
        "   state of its own either, same as Intake's chevron -- the head row's\n"
        "   hover (below) is the only feedback hovering this corner gives. */\n"
        ".headToggle {\n"
        "  margin-left: auto; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; flex-shrink: 0; border: none; background: transparent; color: rgba(255, 255, 255, 0.45); transition: color 0.2s ease;\n"
        "}\n"
        ".headToggle svg {\n"
        "  width: 16px; height: 16px; transition: transform 0.2s ease;\n"
        "}\n"
        ".headToggle .pickIconOpen { color: #EE8C3A; }",
        "drop headToggle's own hover halo",
    ),
    (
        ".catPanel .searchBox { margin-left: auto; }\n"
        ".catPanel .headToggle { margin-left: 10px; }\n"
        ".panelClosed { display: none; }\n"
        ".catPanelClosed > *:not(.panelHeadRow) { display: none; }",
        ".catPanel .searchBox { margin-left: auto; }\n"
        ".catPanel .headToggle { margin-left: 10px; }\n"
        "/* Collapsed, the head row IS the whole visible panel -- it should read as\n"
        "   one complete, fully-curved box, not a shelf with a flat bottom hanging\n"
        "   off nothing, and the orange underline has nothing left to separate. */\n"
        ".panelCollapsed .panelHeadRow { border-radius: 11px; border-bottom-color: transparent; }\n"
        "/* Matches Intake's CollapsibleSection: hovering the head turns the title\n"
        "   white -- the only hover feedback the head row gives. */\n"
        ".scopePanel .panelHeadRow:hover .scopeTitle,\n"
        ".catPanel .panelHeadRow:hover .scopeTitle { color: #fff; }\n"
        ".panelClosed { display: none; }\n"
        ".catPanelClosed > *:not(.panelHeadRow) { display: none; }",
        "collapsed panel: full curve + no orphaned underline; add header hover",
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
git("commit", "-m", "fix110: sidebar auto-collapse moved to content click, notifications re-tinted by group, Report Studio panels matched to Intake collapse behaviour")
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
print("fix110 done.")