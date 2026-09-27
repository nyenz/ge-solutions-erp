#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix114: Notification centre goes light (Recovery-glass
# style) with real colour variety per signal type -- icon chip, left edge,
# type label and unread dot all now pick up the same GROUP_COLOR instead of
# one orange for everything on a dark panel. Settings' five panels are
# rebuilt to Report Studio's exact CollapsibleSection language (gradient
# card, orange hover glow, click-anywhere header) and actually collapse now
# -- the chevron/bodyOpen CSS already existed but nothing in the JSX ever
# wired a toggle to it, so every panel was permanently pinned open. Settings
# also gains the one preference Header.jsx has been reading for years
# without anyone ever being able to set it: notification refresh interval.
#
# What this fixes, and why:
#   1. REFRESH BUTTON -- already gone. fix109 removed it; openDrop() already
#      pulls a fresh list every time the bell opens, so a second control
#      doing the same fetch was redundant clutter. Nothing to remove here --
#      confirmed no refresh control exists anywhere in the notif dropdown.
#   2. Notification panel was the one dark near-black panel left after
#      fix112 moved Reports onto the warm-tray treatment. It's now a light
#      glass card (Recovery's pageHeader language: white, blurred, left
#      orange accent) with a warm cream tray behind white row-cards, same
#      grammar as the Report Catalogue.
#   3. Colour variety per type. GROUP_COLOR already tinted the icon chip;
#      now the same colour drives the row's left edge, the type label text
#      AND the unread dot -- so a MONEY signal reads green top to bottom, a
#      STAFF signal violet, RECOVERY orange, etc, instead of one orange dot
#      no matter what fired it.
#   4. Settings panels (hwPanel) had their own near-identical-but-not-quite
#      version of the gradient card Report Studio and Intake share, and a
#      drawerHeader that LOOKED clickable (cursor: pointer, a .chevron CSS
#      class already existed) but had no onClick, no chevron rendered, and
#      panelBody was hard-pinned to style={{maxHeight: 2000}} in the JSX --
#      so nothing ever actually collapsed. Every panel now has a real
#      open/close state, a rendered rotating chevron, and the identical
#      gradient-card + click-anywhere-header + hover-glow treatment Report
#      Studio's Scope/Catalogue panels use.
#   5. Panel colour-coding. Appearance stays the app's default orange;
#      Personal Security picks up the cyan already used for contact numbers
#      on Recovery; Staff Governance reuses the violet STAFF already carries
#      in the bell and in rank badges; Recently Deleted Plots gets the same
#      slate Reports uses for its own archive group; Danger Zone's existing
#      red is preserved, just re-wired to the open/close state instead of
#      always showing.
#   6. notifPoll never had a home. Header.jsx has read
#      `prefs?.notifPoll ?? 300` since it was written, and its own comment
#      says the interval is "the user's choice (Settings -> Behaviour)" --
#      but DEFAULT_PREFS never defined notifPoll and Settings never offered
#      a control for it, so the bell always polled every five minutes no
#      matter what. It's now a real preference: 5 MIN / 15 MIN / MANUAL,
#      wired into the same PREF_GROUPS list every other appearance choice
#      already lives in.
#
# Every edit below is a surgical find/replace against known-good source
# text rather than a full-file rewrite.
#
# Runs `npm run build` before committing if node_modules is installed
# (fix76's build-gate rule) and refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

HEADER_JSX = os.path.join(SRC, "components", "layout", "Header.jsx")
HEADER_CSS = os.path.join(SRC, "components", "layout", "Header.module.css")
SETTINGS_JSX = os.path.join(SRC, "pages", "settings", "SettingsPage.jsx")
SETTINGS_CSS = os.path.join(SRC, "pages", "settings", "SettingsPage.module.css")
PREFS_CONTEXT = os.path.join(SRC, "context", "PreferencesContext.js")


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


# ═══ 1. Header.jsx -- per-group colour on the edge, label and unread dot ═══
apply_patches(HEADER_JSX, [
    (
        " * POLLING is the user's choice (Settings -> Behaviour). Five minutes is the\n"
        " * default; a phone on mobile data can drop to fifteen, and MANUAL stops the\n"
        " * timer entirely and leaves the refresh button. The old build hard-coded five\n"
        " * minutes with no way to change it.\n"
        " */",
        " * POLLING is the user's choice (Settings -> Notification refresh). Five\n"
        " * minutes is the default; a phone on mobile data can drop to fifteen, and\n"
        " * MANUAL stops the timer entirely. The old build hard-coded five minutes\n"
        " * with no way to change it, and the setting itself did not exist in\n"
        " * Settings until fix114 -- Header read prefs.notifPoll, nothing ever wrote it.\n"
        " */",
        "docstring: stale 'leaves the refresh button' reference (button was removed in fix109) + notifPoll now actually has a home",
    ),
    (
        "                                        <span className={styles.notifBody}>\n"
        "                                            <span className={styles.notifType}>RECOVERY QUEUE</span>\n"
        "                                            <span className={styles.notifMsg}>\n"
        "                                                {staleCount} mission{staleCount > 1 ? 's' : ''} due now\n"
        "                                            </span>\n"
        "                                        </span>",
        "                                        <span className={styles.notifBody}>\n"
        "                                            <span className={styles.notifType} style={{ color: GROUP_COLOR.RECOVERY }}>RECOVERY QUEUE</span>\n"
        "                                            <span className={styles.notifMsg}>\n"
        "                                                {staleCount} mission{staleCount > 1 ? 's' : ''} due now\n"
        "                                            </span>\n"
        "                                        </span>",
        "pinned recovery-queue row's label now carries its own group colour like every other row does",
    ),
    (
        "                                {!loading && shown.map(n => {\n"
        "                                    const meta = describe(n);\n"
        "                                    const Icon = meta.icon;\n"
        "                                    return (\n"
        "                                        <button\n"
        "                                            type=\"button\"\n"
        "                                            key={n.id}\n"
        "                                            className={`${styles.notifRow} ${n.read ? styles.notifRead : ''}`}\n"
        "                                            onClick={() => go(n)}\n"
        "                                        >\n"
        "                                            <span className={styles.notifIcon}\n"
        "                                                style={{\n"
        "                                                    color: GROUP_COLOR[meta.group] || SEVERITY_COLOR[meta.severity] || 'var(--info)',\n"
        "                                                    background: GROUP_BG[meta.group] || 'rgba(6, 182, 212, 0.16)',\n"
        "                                                    boxShadow: meta.severity === 'CRITICAL' ? '0 0 0 1.5px rgba(244, 63, 94, 0.6)' : 'none',\n"
        "                                                }}>\n"
        "                                                <Icon aria-hidden=\"true\" />\n"
        "                                            </span>\n"
        "                                            <span className={styles.notifBody}>\n"
        "                                                <span className={styles.notifType}>\n"
        "                                                    {meta.label}\n"
        "                                                    <time className={styles.notifTime}>{relativeTime(n.createdAt)}</time>\n"
        "                                                </span>\n"
        "                                                <span className={styles.notifMsg}>{n.message}</span>\n"
        "                                            </span>\n"
        "                                            {!n.read && <span className={styles.notifUnreadDot} aria-label=\"Unread\" />}\n"
        "                                        </button>\n"
        "                                    );\n"
        "                                })}",
        "                                {!loading && shown.map(n => {\n"
        "                                    const meta = describe(n);\n"
        "                                    const Icon = meta.icon;\n"
        "                                    /* Same colour that tints the icon chip now drives the row's left\n"
        "                                       edge, the type label and the unread dot -- one hue per group,\n"
        "                                       not one orange for every kind of signal. */\n"
        "                                    const tint = GROUP_COLOR[meta.group] || SEVERITY_COLOR[meta.severity] || '#94a3b8';\n"
        "                                    return (\n"
        "                                        <button\n"
        "                                            type=\"button\"\n"
        "                                            key={n.id}\n"
        "                                            data-group={meta.group}\n"
        "                                            className={`${styles.notifRow} ${n.read ? styles.notifRead : ''}`}\n"
        "                                            style={{ borderLeftColor: tint }}\n"
        "                                            onClick={() => go(n)}\n"
        "                                        >\n"
        "                                            <span className={styles.notifIcon}\n"
        "                                                style={{\n"
        "                                                    color: GROUP_COLOR[meta.group] || SEVERITY_COLOR[meta.severity] || 'var(--info)',\n"
        "                                                    background: GROUP_BG[meta.group] || 'rgba(6, 182, 212, 0.16)',\n"
        "                                                    boxShadow: meta.severity === 'CRITICAL' ? '0 0 0 1.5px rgba(244, 63, 94, 0.6)' : 'none',\n"
        "                                                }}>\n"
        "                                                <Icon aria-hidden=\"true\" />\n"
        "                                            </span>\n"
        "                                            <span className={styles.notifBody}>\n"
        "                                                <span className={styles.notifType} style={{ color: tint }}>\n"
        "                                                    {meta.label}\n"
        "                                                    <time className={styles.notifTime}>{relativeTime(n.createdAt)}</time>\n"
        "                                                </span>\n"
        "                                                <span className={styles.notifMsg}>{n.message}</span>\n"
        "                                            </span>\n"
        "                                            {!n.read && <span className={styles.notifUnreadDot} style={{ background: tint, boxShadow: `0 0 5px ${tint}` }} aria-label=\"Unread\" />}\n"
        "                                        </button>\n"
        "                                    );\n"
        "                                })}",
        "each row's left edge, type label and unread dot now share the same per-group tint as the icon chip",
    ),
])

# ═══ 2. Header.module.css -- notification centre goes light, Recovery-glass style ═══
apply_patches(HEADER_CSS, [
    (
        ".notifDrop {\n"
        "    position: absolute;\n"
        "    top: calc(100% + 8px);\n"
        "    right: 0;\n"
        "    z-index: 10;\n"
        "    min-width: 320px;\n"
        "    max-width: 380px;\n"
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
        "    border-bottom: 1px solid var(--panel-edge);\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 2px;\n"
        "    color: #EE8C3A;\n"
        "    flex-shrink: 0;\n"
        "}\n"
        ".notifReadAll {\n"
        "    display: inline-flex;\n"
        "    align-items: center;\n"
        "    gap: 4px;\n"
        "    background: transparent;\n"
        "    border: 1px solid var(--panel-edge);\n"
        "    color: rgba(255, 255, 255, 0.72);\n"
        "    border-radius: 6px;\n"
        "    padding: 4px 8px;\n"
        "    font-size: 8px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 1px;\n"
        "    cursor: pointer;\n"
        "    transition: all 0.16s ease;\n"
        "}\n"
        ".notifReadAll:hover { color: #EE8C3A; border-color: #EE8C3A; }\n"
        "\n"
        "/* ── filters ───────────────────────────────────────────────────────── */\n"
        ".notifFilters {\n"
        "    display: flex;\n"
        "    gap: 5px;\n"
        "    padding: 9px 11px;\n"
        "    overflow-x: auto;\n"
        "    border-bottom: 1px solid var(--panel-edge);\n"
        "    flex-shrink: 0;\n"
        "    scrollbar-width: none;\n"
        "}\n"
        ".notifFilters::-webkit-scrollbar { display: none; }\n"
        "\n"
        ".notifChip, .notifChipActive {\n"
        "    white-space: nowrap;\n"
        "    border-radius: 20px;\n"
        "    padding: 4px 11px;\n"
        "    font-family: 'Inter', sans-serif;\n"
        "    font-size: 8.5px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 1.1px;\n"
        "    cursor: pointer;\n"
        "    transition: all 0.16s ease;\n"
        "    border: 1px solid var(--panel-edge);\n"
        "    background: transparent;\n"
        "    color: rgba(255, 255, 255, 0.45);\n"
        "}\n"
        ".notifChip:hover { color: #EE8C3A; border-color: #EE8C3A; }\n"
        ".notifChipActive {\n"
        "    background: #EE8C3A;\n"
        "    border-color: #EE8C3A;\n"
        "    color: var(--accent-ink);\n"
        "}\n"
        "\n"
        "/* ── list ──────────────────────────────────────────────────────────── */\n"
        ".notifList {\n"
        "    overflow-y: auto;\n"
        "    flex: 1;\n"
        "    min-height: 0;\n"
        "}\n"
        "\n"
        ".notifRow, .notifRowPinned {\n"
        "    display: flex;\n"
        "    align-items: flex-start;\n"
        "    gap: 10px;\n"
        "    width: 100%;\n"
        "    text-align: left;\n"
        "    background: transparent;\n"
        "    border: none;\n"
        "    border-bottom: 1px solid var(--panel-edge);\n"
        "    padding: 11px 13px;\n"
        "    cursor: pointer;\n"
        "    transition: background 0.15s ease;\n"
        "}\n"
        ".notifRow:hover, .notifRowPinned:hover { background: rgba(238, 140, 58, 0.14); }\n"
        ".notifRow:focus-visible, .notifRowPinned:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }\n"
        "\n"
        "/* The recovery queue is pinned and is not a stored row, so it is marked\n"
        "   as different rather than pretending to be one of the list. */\n"
        ".notifRowPinned {\n"
        "    background: var(--warn-soft);\n"
        "    border-left: 3px solid #EE8C3A;\n"
        "}\n"
        "\n"
        "/* Read rows dim, but the unread ones also carry a dot -- opacity alone\n"
        "   disappears under the high-contrast setting. */\n"
        ".notifRead { opacity: 0.5; }\n"
        "\n"
        ".notifIcon {\n"
        "    display: flex;\n"
        "    align-items: center;\n"
        "    justify-content: center;\n"
        "    width: 26px;\n"
        "    height: 26px;\n"
        "    border-radius: 7px;\n"
        "    flex-shrink: 0;\n"
        "    background: rgba(255, 255, 255, 0.07);\n"
        "    font-size: 13px;\n"
        "}\n"
        "\n"
        ".notifBody {\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    gap: 3px;\n"
        "    min-width: 0;\n"
        "    flex: 1;\n"
        "}\n"
        "\n"
        ".notifType {\n"
        "    display: flex;\n"
        "    align-items: baseline;\n"
        "    justify-content: space-between;\n"
        "    gap: 8px;\n"
        "    font-family: 'Inter', sans-serif;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 1.2px;\n"
        "    text-transform: uppercase;\n"
        "    color: #EE8C3A;\n"
        "}\n"
        "\n"
        ".notifTime {\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 8px;\n"
        "    font-weight: 700;\n"
        "    letter-spacing: 0.5px;\n"
        "    text-transform: none;\n"
        "    color: rgba(255, 255, 255, 0.45);\n"
        "    flex-shrink: 0;\n"
        "}\n"
        "\n"
        ".notifMsg {\n"
        "    font-family: 'Inter', sans-serif;\n"
        "    font-size: 11px;\n"
        "    font-weight: 600;\n"
        "    color: #ffffff;\n"
        "    line-height: 1.45;\n"
        "    word-break: break-word;\n"
        "}\n"
        "\n"
        ".notifUnreadDot {\n"
        "    width: 7px;\n"
        "    height: 7px;\n"
        "    border-radius: 50%;\n"
        "    background: #EE8C3A;\n"
        "    flex-shrink: 0;\n"
        "    margin-top: 6px;\n"
        "}\n"
        "\n"
        ".notifEmpty {\n"
        "    padding: 20px 13px;\n"
        "    text-align: center;\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 2px;\n"
        "    color: rgba(255, 255, 255, 0.45);\n"
        "}",
        ".notifDrop {\n"
        "    position: absolute;\n"
        "    top: calc(100% + 8px);\n"
        "    right: 0;\n"
        "    z-index: 10;\n"
        "    min-width: 320px;\n"
        "    max-width: 380px;\n"
        "    max-height: min(560px, calc(100vh - var(--header-height, 64px) - 24px));\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    /* fix114: lighter, inspired by Recovery's glass pageHeader -- a warm\n"
        "       white card with a left orange accent stripe, instead of the same\n"
        "       near-black gradient every other panel in the app already moved off\n"
        "       of for anything meant to be scanned quickly rather than worked in. */\n"
        "    background: rgba(255, 255, 255, 0.97);\n"
        "    backdrop-filter: blur(18px);\n"
        "    border: 1.5px solid rgba(238, 140, 58, 0.3);\n"
        "    border-left: 4px solid #EE8C3A;\n"
        "    border-radius: 12px;\n"
        "    box-shadow: 0 18px 44px rgba(26, 46, 48, 0.22);\n"
        "    overflow: hidden;\n"
        "}\n"
        "\n"
        ".notifHead {\n"
        "    display: flex;\n"
        "    justify-content: space-between;\n"
        "    align-items: center;\n"
        "    gap: 8px;\n"
        "    padding: 11px 13px;\n"
        "    background: rgba(244, 239, 232, 0.6);\n"
        "    border-bottom: 1px solid rgba(26, 46, 48, 0.1);\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 2px;\n"
        "    color: #1a2e30;\n"
        "    flex-shrink: 0;\n"
        "}\n"
        ".notifReadAll {\n"
        "    display: inline-flex;\n"
        "    align-items: center;\n"
        "    gap: 4px;\n"
        "    background: transparent;\n"
        "    border: 1px solid rgba(26, 46, 48, 0.18);\n"
        "    color: rgba(26, 46, 48, 0.6);\n"
        "    border-radius: 6px;\n"
        "    padding: 4px 8px;\n"
        "    font-size: 8px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 1px;\n"
        "    cursor: pointer;\n"
        "    transition: all 0.16s ease;\n"
        "}\n"
        ".notifReadAll:hover { color: #fff; background: #EE8C3A; border-color: #EE8C3A; }\n"
        "\n"
        "/* ── filters ───────────────────────────────────────────────────────── */\n"
        ".notifFilters {\n"
        "    display: flex;\n"
        "    gap: 5px;\n"
        "    padding: 9px 11px;\n"
        "    overflow-x: auto;\n"
        "    border-bottom: 1px solid rgba(26, 46, 48, 0.08);\n"
        "    flex-shrink: 0;\n"
        "    scrollbar-width: none;\n"
        "}\n"
        ".notifFilters::-webkit-scrollbar { display: none; }\n"
        "\n"
        ".notifChip, .notifChipActive {\n"
        "    white-space: nowrap;\n"
        "    border-radius: 20px;\n"
        "    padding: 4px 11px;\n"
        "    font-family: 'Inter', sans-serif;\n"
        "    font-size: 8.5px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 1.1px;\n"
        "    cursor: pointer;\n"
        "    transition: all 0.16s ease;\n"
        "    border: 1px solid rgba(26, 46, 48, 0.16);\n"
        "    background: rgba(255, 255, 255, 0.7);\n"
        "    color: rgba(26, 46, 48, 0.55);\n"
        "}\n"
        ".notifChip:hover { color: #EE8C3A; border-color: #EE8C3A; background: rgba(238, 140, 58, 0.08); }\n"
        ".notifChipActive {\n"
        "    background: #EE8C3A;\n"
        "    border-color: #EE8C3A;\n"
        "    color: #fff;\n"
        "}\n"
        "\n"
        "/* ── list ──────────────────────────────────────────────────────────── */\n"
        "/* fix114: a warm tray behind white row-cards, same language as the Report\n"
        "   Catalogue -- the tray supplies the contrast, so each group's own colour\n"
        "   (left edge, icon chip, label, unread dot) is what actually stands out,\n"
        "   not a dark background every row shares regardless of type. */\n"
        ".notifList {\n"
        "    overflow-y: auto;\n"
        "    flex: 1;\n"
        "    min-height: 0;\n"
        "    background: #f4efe8;\n"
        "    padding: 7px;\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    gap: 6px;\n"
        "}\n"
        "\n"
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
        "}\n"
        ".notifRow:hover, .notifRowPinned:hover { box-shadow: 0 8px 20px rgba(26, 46, 48, 0.18); transform: translateY(-1px); }\n"
        ".notifRow:focus-visible, .notifRowPinned:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }\n"
        "\n"
        "/* The recovery queue is pinned and is not a stored row, so it is marked\n"
        "   as different rather than pretending to be one of the list. */\n"
        ".notifRowPinned {\n"
        "    background: #fff7ed;\n"
        "    border-left: 4px solid #EE8C3A;\n"
        "}\n"
        "\n"
        "/* Read rows dim, but the unread ones also carry a dot -- opacity alone\n"
        "   disappears under the high-contrast setting. */\n"
        ".notifRead { opacity: 0.6; }\n"
        "\n"
        ".notifIcon {\n"
        "    display: flex;\n"
        "    align-items: center;\n"
        "    justify-content: center;\n"
        "    width: 26px;\n"
        "    height: 26px;\n"
        "    border-radius: 7px;\n"
        "    flex-shrink: 0;\n"
        "    font-size: 13px;\n"
        "}\n"
        "\n"
        ".notifBody {\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    gap: 3px;\n"
        "    min-width: 0;\n"
        "    flex: 1;\n"
        "}\n"
        "\n"
        ".notifType {\n"
        "    display: flex;\n"
        "    align-items: baseline;\n"
        "    justify-content: space-between;\n"
        "    gap: 8px;\n"
        "    font-family: 'Inter', sans-serif;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 1.2px;\n"
        "    text-transform: uppercase;\n"
        "}\n"
        "\n"
        ".notifTime {\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 8px;\n"
        "    font-weight: 700;\n"
        "    letter-spacing: 0.5px;\n"
        "    text-transform: none;\n"
        "    color: rgba(26, 46, 48, 0.42);\n"
        "    flex-shrink: 0;\n"
        "}\n"
        "\n"
        ".notifMsg {\n"
        "    font-family: 'Inter', sans-serif;\n"
        "    font-size: 11px;\n"
        "    font-weight: 600;\n"
        "    color: #1a2e30;\n"
        "    line-height: 1.45;\n"
        "    word-break: break-word;\n"
        "}\n"
        "\n"
        "/* fix114: colour now comes from the row's own group (set inline in\n"
        "   Header.jsx from the same GROUP_COLOR map the icon chip reads) instead\n"
        "   of every dot being the same orange no matter what kind of signal it is. */\n"
        ".notifUnreadDot {\n"
        "    width: 7px;\n"
        "    height: 7px;\n"
        "    border-radius: 50%;\n"
        "    background: #EE8C3A;\n"
        "    flex-shrink: 0;\n"
        "    margin-top: 6px;\n"
        "}\n"
        "\n"
        ".notifEmpty {\n"
        "    padding: 20px 13px;\n"
        "    text-align: center;\n"
        "    font-family: 'Space Mono', monospace;\n"
        "    font-size: 9px;\n"
        "    font-weight: 900;\n"
        "    letter-spacing: 2px;\n"
        "    color: rgba(26, 46, 48, 0.4);\n"
        "}",
        "notification centre re-themed light (Recovery-glass card + warm tray + white row-cards) with per-group colour on edge/label/dot",
    ),
])

# ═══ 3. PreferencesContext.js -- notifPoll finally gets a default ═══
apply_patches(PREFS_CONTEXT, [
    (
        "export const DEFAULT_PREFS = {\n"
        "    theme: 'light',      // light | dark   -- page background and chrome\n"
        "    uiScale: '100',      // 90 | 100 | 110 | 125\n"
        "    statSize: 'standard',// small | standard | large\n"
        "    motion: 'full',      // full | reduced\n"
        "    tips: 'normal',      // normal | slow | off\n"
        "    contrast: 'normal',  // normal | high\n"
        "};",
        "export const DEFAULT_PREFS = {\n"
        "    theme: 'light',      // light | dark   -- page background and chrome\n"
        "    uiScale: '100',      // 90 | 100 | 110 | 125\n"
        "    statSize: 'standard',// small | standard | large\n"
        "    motion: 'full',      // full | reduced\n"
        "    tips: 'normal',      // normal | slow | off\n"
        "    contrast: 'normal',  // normal | high\n"
        "    notifPoll: '300',    // 300 | 900 | 0 (seconds) -- bell auto-refresh, 0 = manual only\n"
        "};",
        "notifPoll default added -- Header.jsx has read this key since it was written, Settings never set it",
    ),
])

# ═══ 4. SettingsPage.jsx -- real collapse + notifPoll control ═══
apply_patches(SETTINGS_JSX, [
    (
        "import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff, FiSliders, FiMonitor } from 'react-icons/fi';",
        "import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff, FiSliders, FiMonitor, FiChevronDown } from 'react-icons/fi';",
        "import FiChevronDown for the now-real collapse toggles",
    ),
    (
        "  { key: 'contrast', label: 'Table contrast', hint: 'Stronger row lines for low-quality monitors.',\n"
        "    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'high', label: 'HIGH' }] },\n"
        "];",
        "  { key: 'contrast', label: 'Table contrast', hint: 'Stronger row lines for low-quality monitors.',\n"
        "    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'high', label: 'HIGH' }] },\n"
        "  { key: 'notifPoll', label: 'Notification refresh', hint: 'How often the bell checks for new signals in the background.',\n"
        "    options: [{ value: '300', label: '5 MIN' }, { value: '900', label: '15 MIN' }, { value: '0', label: 'MANUAL' }] },\n"
        "];",
        "notifPoll preference row added -- the interval Header.jsx already reads now has a control",
    ),
    (
        "  const isRoot = !!user?.isRoot;\n"
        "  const [toasts, setToasts] = useState([]);",
        "  const isRoot = !!user?.isRoot;\n"
        "  /* Every hwPanel now genuinely collapses -- these five default open so\n"
        "     nothing changes for anyone who never touches a header, but a long\n"
        "     staff roster or deleted-plots list can be tucked away instead of\n"
        "     permanently occupying the full column. */\n"
        "  const [appOpen, setAppOpen] = useState(true);\n"
        "  const [secOpen, setSecOpen] = useState(true);\n"
        "  const [govOpen, setGovOpen] = useState(true);\n"
        "  const [dangerOpen, setDangerOpen] = useState(true);\n"
        "  const [delOpen, setDelOpen] = useState(true);\n"
        "  const [toasts, setToasts] = useState([]);",
        "per-panel open state added -- panelBody was previously pinned to a fixed maxHeight with no toggle at all",
    ),
    (
        "        <div className={styles.hwPanel}>\n"
        "          <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiSliders className={styles.drawerIcon} aria-hidden=\"true\" /> APPEARANCE</div></div>\n"
        "          <div className={styles.panelBody} style={{ maxHeight: 2000 }}><div className={styles.panelInner}>\n"
        "            <div className={styles.securityAlert}><FiMonitor aria-hidden=\"true\" /><span>These are saved on this device, not on your account -- the office shares logins across a desktop and two phones, and \"this screen is too small to read\" is a fact about the screen.</span></div>",
        "        <div className={styles.hwPanel} data-kind=\"appearance\">\n"
        "          <div\n"
        "            className={appOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}\n"
        "            role=\"button\" tabIndex={0}\n"
        "            onClick={() => setAppOpen(o => !o)}\n"
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setAppOpen(o => !o); } }}\n"
        "            aria-expanded={appOpen} aria-label=\"Collapse or expand appearance panel\"\n"
        "          >\n"
        "            <div className={styles.drawerTitle}><FiSliders className={styles.drawerIcon} aria-hidden=\"true\" /> APPEARANCE</div>\n"
        "            <FiChevronDown className={appOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden=\"true\" />\n"
        "          </div>\n"
        "          {appOpen && <div className={styles.panelBody}><div className={styles.panelInner}>\n"
        "            <div className={styles.securityAlert}><FiMonitor aria-hidden=\"true\" /><span>These are saved on this device, not on your account -- the office shares logins across a desktop and two phones, and \"this screen is too small to read\" is a fact about the screen.</span></div>",
        "Appearance panel: click-anywhere header, rendered chevron, real collapse",
    ),
    (
        "            <div className={styles.submitRow}>\n"
        "              <button type=\"button\" className={styles.commitBtn} onClick={resetPrefs}><FiRotateCcw aria-hidden=\"true\" /> RESET APPEARANCE</button>\n"
        "            </div>\n"
        "          </div></div>\n"
        "        </div>",
        "            <div className={styles.submitRow}>\n"
        "              <button type=\"button\" className={styles.commitBtn} onClick={resetPrefs}><FiRotateCcw aria-hidden=\"true\" /> RESET APPEARANCE</button>\n"
        "            </div>\n"
        "          </div></div>}\n"
        "        </div>",
        "Appearance panel body closes the new conditional render",
    ),
    (
        "        <div className={styles.hwPanel}>\n"
        "          <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiKey className={styles.drawerIcon} aria-hidden=\"true\" /> PERSONAL SECURITY</div></div>\n"
        "          <div className={styles.panelBody} style={{ maxHeight: 2000 }}><div className={styles.panelInner}>\n"
        "            <div className={styles.securityAlert}><FiShield aria-hidden=\"true\" /><span>Minimum 8 characters, one uppercase letter and one number. Changing your key unlocks full access.</span></div>",
        "        <div className={styles.hwPanel} data-kind=\"security\">\n"
        "          <div\n"
        "            className={secOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}\n"
        "            role=\"button\" tabIndex={0}\n"
        "            onClick={() => setSecOpen(o => !o)}\n"
        "            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSecOpen(o => !o); } }}\n"
        "            aria-expanded={secOpen} aria-label=\"Collapse or expand personal security panel\"\n"
        "          >\n"
        "            <div className={styles.drawerTitle}><FiKey className={styles.drawerIcon} aria-hidden=\"true\" /> PERSONAL SECURITY</div>\n"
        "            <FiChevronDown className={secOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden=\"true\" />\n"
        "          </div>\n"
        "          {secOpen && <div className={styles.panelBody}><div className={styles.panelInner}>\n"
        "            <div className={styles.securityAlert}><FiShield aria-hidden=\"true\" /><span>Minimum 8 characters, one uppercase letter and one number. Changing your key unlocks full access.</span></div>",
        "Personal Security panel: click-anywhere header, rendered chevron, real collapse, cyan accent",
    ),
    (
        "            <div className={styles.submitRow}>\n"
        "              <button type=\"button\" className={styles.commitBtn} onClick={changePw} disabled={savingPw || !oldPw || !newPw}><FiKey aria-hidden=\"true\" /> COMMIT NEW KEY</button>\n"
        "            </div>\n"
        "          </div></div>\n"
        "        </div>",
        "            <div className={styles.submitRow}>\n"
        "              <button type=\"button\" className={styles.commitBtn} onClick={changePw} disabled={savingPw || !oldPw || !newPw}><FiKey aria-hidden=\"true\" /> COMMIT NEW KEY</button>\n"
        "            </div>\n"
        "          </div></div>}\n"
        "        </div>",
        "Personal Security panel body closes the new conditional render",
    ),
    (
        "        {isRoot && (\n"
        "          <div className={styles.hwPanel}>\n"
        "            <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiShield className={styles.drawerIcon} aria-hidden=\"true\" /> STAFF GOVERNANCE</div></div>\n"
        "            <div className={styles.panelBody} style={{ maxHeight: 4000 }}><div className={styles.panelInner}>\n"
        "              <div className={styles.ledgerActions}>",
        "        {isRoot && (\n"
        "          <div className={styles.hwPanel} data-kind=\"governance\">\n"
        "            <div\n"
        "              className={govOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}\n"
        "              role=\"button\" tabIndex={0}\n"
        "              onClick={() => setGovOpen(o => !o)}\n"
        "              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setGovOpen(o => !o); } }}\n"
        "              aria-expanded={govOpen} aria-label=\"Collapse or expand staff governance panel\"\n"
        "            >\n"
        "              <div className={styles.drawerTitle}><FiShield className={styles.drawerIcon} aria-hidden=\"true\" /> STAFF GOVERNANCE</div>\n"
        "              <FiChevronDown className={govOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden=\"true\" />\n"
        "            </div>\n"
        "            {govOpen && <div className={styles.panelBody}><div className={styles.panelInner}>\n"
        "              <div className={styles.ledgerActions}>",
        "Staff Governance panel: click-anywhere header, rendered chevron, real collapse, violet accent",
    ),
    (
        "                    <div className={styles.opDetails}><p><FiInfo aria-hidden=\"true\" /> {op.email || 'no email on file'}</p></div>\n"
        "                  </div>\n"
        "                ))}\n"
        "              </div>\n"
        "            </div></div>\n"
        "          </div>\n"
        "        )}",
        "                    <div className={styles.opDetails}><p><FiInfo aria-hidden=\"true\" /> {op.email || 'no email on file'}</p></div>\n"
        "                  </div>\n"
        "                ))}\n"
        "              </div>\n"
        "            </div></div>}\n"
        "          </div>\n"
        "        )}",
        "Staff Governance panel body closes the new conditional render",
    ),
    (
        "        {isRoot && (\n"
        "          <div className={`${styles.hwPanel} ${styles.dangerPanel}`}>\n"
        "            <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiAlertTriangle className={styles.drawerIcon} aria-hidden=\"true\" /> DANGER ZONE</div></div>\n"
        "            <div className={styles.panelBody} style={{ maxHeight: 2000 }}><div className={styles.panelInner}>\n"
        "              <div className={styles.wipeField}>\n"
        "                <HardwareInput label={'TYPE \"WIPE-EVERYTHING\" TO ARM'} value={wipeText} onChange={e => setWipeText(e.target.value)} />\n"
        "              </div>\n"
        "              <button type=\"button\" className={styles.wipeBtn} disabled={wipeText !== 'WIPE-EVERYTHING' || wiping} onClick={wipe}>\n"
        "                <FiTrash2 aria-hidden=\"true\" /> {wiping ? 'WIPING...' : 'WIPE ALL BUSINESS DATA'}\n"
        "              </button>\n"
        "            </div></div>\n"
        "          </div>\n"
        "        )}",
        "        {isRoot && (\n"
        "          <div className={`${styles.hwPanel} ${styles.dangerPanel}`}>\n"
        "            <div\n"
        "              className={dangerOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}\n"
        "              role=\"button\" tabIndex={0}\n"
        "              onClick={() => setDangerOpen(o => !o)}\n"
        "              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDangerOpen(o => !o); } }}\n"
        "              aria-expanded={dangerOpen} aria-label=\"Collapse or expand danger zone panel\"\n"
        "            >\n"
        "              <div className={styles.drawerTitle}><FiAlertTriangle className={styles.drawerIcon} aria-hidden=\"true\" /> DANGER ZONE</div>\n"
        "              <FiChevronDown className={dangerOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden=\"true\" />\n"
        "            </div>\n"
        "            {dangerOpen && <div className={styles.panelBody}><div className={styles.panelInner}>\n"
        "              <div className={styles.wipeField}>\n"
        "                <HardwareInput label={'TYPE \"WIPE-EVERYTHING\" TO ARM'} value={wipeText} onChange={e => setWipeText(e.target.value)} />\n"
        "              </div>\n"
        "              <button type=\"button\" className={styles.wipeBtn} disabled={wipeText !== 'WIPE-EVERYTHING' || wiping} onClick={wipe}>\n"
        "                <FiTrash2 aria-hidden=\"true\" /> {wiping ? 'WIPING...' : 'WIPE ALL BUSINESS DATA'}\n"
        "              </button>\n"
        "            </div></div>}\n"
        "          </div>\n"
        "        )}",
        "Danger Zone panel: click-anywhere header, rendered chevron, real collapse (red accent already existed in CSS, now actually reachable)",
    ),
    (
        "        {isRoot && (\n"
        "          <div className={styles.hwPanel}>\n"
        "            <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiRotateCcw className={styles.drawerIcon} aria-hidden=\"true\" /> RECENTLY DELETED PLOTS</div></div>\n"
        "            <div className={styles.panelBody} style={{ maxHeight: 3000 }}><div className={styles.panelInner}>\n"
        "              {delLoading && <LoadingState label=\"SYNCING DELETED PLOTS...\" tone=\"bare\" />}",
        "        {isRoot && (\n"
        "          <div className={styles.hwPanel} data-kind=\"deleted\">\n"
        "            <div\n"
        "              className={delOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}\n"
        "              role=\"button\" tabIndex={0}\n"
        "              onClick={() => setDelOpen(o => !o)}\n"
        "              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDelOpen(o => !o); } }}\n"
        "              aria-expanded={delOpen} aria-label=\"Collapse or expand recently deleted plots panel\"\n"
        "            >\n"
        "              <div className={styles.drawerTitle}><FiRotateCcw className={styles.drawerIcon} aria-hidden=\"true\" /> RECENTLY DELETED PLOTS</div>\n"
        "              <FiChevronDown className={delOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden=\"true\" />\n"
        "            </div>\n"
        "            {delOpen && <div className={styles.panelBody}><div className={styles.panelInner}>\n"
        "              {delLoading && <LoadingState label=\"SYNCING DELETED PLOTS...\" tone=\"bare\" />}",
        "Recently Deleted Plots panel: click-anywhere header, rendered chevron, real collapse, slate accent",
    ),
    (
        "                    <button type=\"button\" className={styles.commitBtn} onClick={async () => { try { await landService.restoreProject(p.id); toast('Plot restored.', 'success'); loadDeleted(); } catch { toast('Restore failed.', 'error'); } }}>\n"
        "                      <FiRotateCcw aria-hidden=\"true\" /> RESTORE\n"
        "                    </button>\n"
        "                  </div>\n"
        "                </div>\n"
        "              ))}\n"
        "            </div></div>\n"
        "          </div>\n"
        "        )}",
        "                    <button type=\"button\" className={styles.commitBtn} onClick={async () => { try { await landService.restoreProject(p.id); toast('Plot restored.', 'success'); loadDeleted(); } catch { toast('Restore failed.', 'error'); } }}>\n"
        "                      <FiRotateCcw aria-hidden=\"true\" /> RESTORE\n"
        "                    </button>\n"
        "                  </div>\n"
        "                </div>\n"
        "              ))}\n"
        "            </div></div>}\n"
        "          </div>\n"
        "        )}",
        "Recently Deleted Plots panel body closes the new conditional render",
    ),
])

# ═══ 5. SettingsPage.module.css -- Report-Studio-matched cards + per-kind colour ═══
apply_patches(SETTINGS_CSS, [
    (
        "/* ── HARDWARE PANELS ────────────────────────────────────────────── */\n"
        ".hwPanel { background: var(--panel-bg); border: 1.5px solid var(--panel-border); border-radius: var(--radius); overflow: visible; box-shadow: 0 8px 24px rgba(0,0,0,0.14); transition: border-color 0.2s; }\n"
        ".hwPanel:hover { border-color: rgba(238,140,58,0.38); }\n"
        "\n"
        ".drawerHeader { display: flex; justify-content: space-between; align-items: center; padding: clamp(9px,1.2vw,13px) clamp(12px,1.5vw,18px); border-bottom: 1px solid rgba(238,140,58,0.12); cursor: pointer; user-select: none; outline: none; transition: background 0.2s; }\n"
        ".drawerHeader:hover { background: rgba(238,140,58,0.04); }\n"
        ".drawerHeader:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }\n"
        "\n"
        ".drawerTitle { display: flex; align-items: center; gap: clamp(6px,0.8vw,10px); font-family: 'DM Sans', sans-serif; color: var(--orange); font-weight: 900; font-size: var(--fs-drawer); letter-spacing: 2px; text-transform: uppercase; }\n"
        ".drawerIcon  { font-size: clamp(12px,1.3vw,15px); }\n"
        ".chevron     { color: var(--orange); font-size: clamp(15px,1.7vw,19px); transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); }\n"
        ".rotated     { transform: rotate(180deg); }\n"
        "\n"
        ".panelBody  { transition: max-height 0.45s cubic-bezier(0.4,0,0.2,1), opacity 0.35s; overflow: hidden; }\n"
        ".bodyOpen   { max-height: 1500px; opacity: 1; overflow: visible; }\n"
        ".bodyClosed { max-height: 0;      opacity: 0; }\n"
        ".panelInner { padding: var(--pad); }",
        "/* ── HARDWARE PANELS ────────────────────────────────────────────── */\n"
        "/* fix114: matched to Report Studio / Intake's CollapsibleSection exactly\n"
        "   -- gradient card, border warms to full orange and the shadow deepens\n"
        "   on hover, header is click-anywhere (not just a passive bar with a\n"
        "   pointer cursor) and genuinely collapses instead of every panel body\n"
        "   being pinned to a fixed max-height with no toggle wired to it. */\n"
        ".hwPanel {\n"
        "  background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);\n"
        "  border: 1px solid rgba(238, 140, 58, 0.2);\n"
        "  border-radius: var(--radius);\n"
        "  overflow: visible;\n"
        "  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);\n"
        "  transition: border-color 0.3s ease, box-shadow 0.3s ease;\n"
        "}\n"
        ".hwPanel:hover { border-color: var(--orange); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }\n"
        "\n"
        ".drawerHeader {\n"
        "  display: flex; justify-content: space-between; align-items: center;\n"
        "  padding: clamp(8px,1.1vw,12px) clamp(10px,1.4vw,16px);\n"
        "  background: #162a2c;\n"
        "  border: none; border-bottom: 1.5px solid transparent;\n"
        "  border-radius: 9px;\n"
        "  cursor: pointer; user-select: none; outline: none;\n"
        "  transition: border-bottom-color 0.25s ease, border-radius 0.25s ease;\n"
        "}\n"
        ".drawerHeader:hover .drawerTitle { color: #fff; }\n"
        ".drawerHeader:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }\n"
        ".drawerHeaderOpen { border-radius: 9px 9px 0 0; border-bottom-color: var(--orange); }\n"
        "\n"
        ".drawerTitle { display: flex; align-items: center; gap: clamp(6px,0.8vw,10px); font-family: 'DM Sans', sans-serif; color: var(--orange); font-weight: 900; font-size: var(--fs-drawer); letter-spacing: 2px; text-transform: uppercase; transition: color 0.18s ease; }\n"
        ".drawerIcon  { font-size: clamp(12px,1.3vw,15px); }\n"
        ".chevron     { color: rgba(255,255,255,0.4); font-size: clamp(15px,1.7vw,19px); transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), color 0.2s ease; }\n"
        ".rotated     { transform: rotate(180deg); color: var(--orange); }\n"
        "\n"
        ".panelBody  { overflow: visible; }\n"
        ".panelInner { padding: var(--pad); animation: panelExpand 0.2s ease-out; }\n"
        "@keyframes panelExpand {\n"
        "  from { opacity: 0; transform: translateY(-4px); }\n"
        "  to   { opacity: 1; transform: translateY(0); }\n"
        "}\n"
        "\n"
        "/* fix114: each panel's own colour, so the workstation grid reads by\n"
        "   purpose at a glance -- Appearance keeps the app's default orange,\n"
        "   Personal Security picks up the cyan Recovery already uses for contact\n"
        "   numbers, Staff Governance reuses the violet STAFF already carries in\n"
        "   the bell and in rank badges, and the archive panel gets the same\n"
        "   slate Reports uses for its own archive group. Danger Zone's red is\n"
        "   handled separately, further down this file. */\n"
        ".hwPanel[data-kind=\"security\"] .drawerTitle { color: #22d3ee; }\n"
        ".hwPanel[data-kind=\"security\"] .drawerHeaderOpen { border-bottom-color: #22d3ee; }\n"
        ".hwPanel[data-kind=\"security\"] .rotated { color: #22d3ee; }\n"
        ".hwPanel[data-kind=\"security\"]:hover { border-color: #22d3ee; }\n"
        ".hwPanel[data-kind=\"governance\"] .drawerTitle { color: #a78bfa; }\n"
        ".hwPanel[data-kind=\"governance\"] .drawerHeaderOpen { border-bottom-color: #a78bfa; }\n"
        ".hwPanel[data-kind=\"governance\"] .rotated { color: #a78bfa; }\n"
        ".hwPanel[data-kind=\"governance\"]:hover { border-color: #a78bfa; }\n"
        ".hwPanel[data-kind=\"deleted\"] .drawerTitle { color: #94a3b8; }\n"
        ".hwPanel[data-kind=\"deleted\"] .drawerHeaderOpen { border-bottom-color: #94a3b8; }\n"
        ".hwPanel[data-kind=\"deleted\"] .rotated { color: #94a3b8; }\n"
        ".hwPanel[data-kind=\"deleted\"]:hover { border-color: #94a3b8; }",
        "hwPanel/drawerHeader/chevron rebuilt to Report Studio's exact CollapsibleSection language, plus per-kind colour accents",
    ),
    (
        "/* -- DANGER ZONE -------------------------------------------------- */\n"
        ".dangerPanel { border-color: rgba(239,68,68,0.35); }\n"
        ".dangerPanel:hover { border-color: rgba(239,68,68,0.55); }\n"
        ".dangerPanel .drawerTitle, .dangerPanel .chevron { color: var(--red); }\n"
        ".dangerPanel .drawerHeader { border-bottom-color: rgba(239,68,68,0.18); }\n"
        ".dangerPanel .drawerHeader:hover { background: rgba(239,68,68,0.05); }",
        "/* -- DANGER ZONE -------------------------------------------------- */\n"
        ".dangerPanel { border-color: rgba(239,68,68,0.35); }\n"
        ".dangerPanel:hover { border-color: rgba(239,68,68,0.55); }\n"
        ".dangerPanel .drawerTitle, .dangerPanel .chevron { color: var(--red); }\n"
        ".dangerPanel .drawerHeaderOpen { border-bottom-color: var(--red); }",
        "Danger Zone's divider now colours the open state (drawerHeaderOpen) instead of a header that was always rendered as if open",
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
git("commit", "-m", "fix114: notification centre re-themed light with per-group colour on edge/label/dot (no refresh button existed to remove -- fix109 already dropped it); Settings panels rebuilt to Report Studio's CollapsibleSection language and genuinely collapse now, each colour-coded by purpose; notifPoll preference added so Header's polling interval is finally settable")
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