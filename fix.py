#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix118: Report Catalogue list rebuilt to the "Option 1,
# Refined" prototype (report-catalogue-option1-refined.html). Only the
# list BELOW "Recently Used" changes -- the header (title/badge/search),
# category tabs and the Recently Used row itself are untouched.
#
# What changes, and why:
#   1. One card per group, not one card per report. Every record in a
#      group used to be its own individually-shadowed, hover-lifting
#      .catWrap card. Now a group's records share ONE elevated white
#      card (.groupBody) with thin hairline dividers between rows --
#      matches the prototype's "records get lifted onto the white
#      upper level, group heading stays flat on the tray" language.
#   2. Group heading drops from a solid sticky band (.ddSec, same bg as
#      the tray so it barely registered as a heading) to flat, uncarded
#      text (.groupLabel) sitting directly on the tray.
#   3. Row states: an OPEN row (not applied) gets the same full-orange
#      fill hover already gave it, but now it *persists* while open
#      instead of only showing while the mouse is over it. An APPLIED
#      row gets a real, visible soft-orange wash (not just a left rail)
#      and keeps that wash even when hovered -- it no longer flips to
#      the open row's solid fill. An "APPLIED" tag appears next to the
#      title. Both states share a 3px left rail.
#   4. The expanded readout drops its own border-left/margin and sits
#      flush against the row's own rail, background lightened from pure
#      black to the prototype's #28383a.
#   5. Use button matched to the real HeaderButton .primary spec: 34px
#      tall, hover recolors only (no lift/transform), and now actually
#      disables + reads "Applied ✓" once that report is applied instead
#      of staying a clickable "USE THIS REPORT" forever.
#   6. The single default report keeps its own always-visible highlight
#      (was .catRowDef) as .rowDefault, restated for the shared-card
#      layout; a non-"ALL" group tab now also gets a plain, label-less
#      card (.ungrouped) instead of loose unwrapped rows.
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

STUDIO_JSX = os.path.join(SRC, "pages", "Reports", "ReportStudio.jsx")
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


# ═══ ReportStudio.jsx -- catalogue row markup rebuilt around shared group cards ═══
apply_patches(STUDIO_JSX, [
    (
        "  const catRowNode = (def) => (\n"
        "    <div key={def.id} className={styles.catWrap} data-group={def.group}>\n"
        "      <button className={styles.catRow + (appliedId === def.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === def.id ? null : def.id)} aria-expanded={readId === def.id}>\n"
        "        <span className={styles.r1}>{def.title}<span className={styles.liveCount}>{liveCount(def)} ROWS</span><span className={styles.tag}>{def.chart !== 'NONE' ? def.chart : 'TABLE'} &middot; {def.group}</span><span className={styles.toggleHint}>{readId === def.id ? 'CLOSE \\u25B2' : 'WHAT IS THIS? \\u25BC'}</span></span>\n"
        "        <span className={styles.r2}>{def.desc}</span>\n"
        "      </button>\n"
        "      {readId === def.id && (\n"
        "        <div className={styles.readout}>\n"
        "          <div className={styles.readoutText}>{readout(def)}</div>\n"
        "          <button className={styles.useBtn} onClick={() => applyDef(def)}>USE THIS REPORT</button>\n"
        "        </div>\n"
        "      )}\n"
        "    </div>\n"
        "  );\n",
        "  const catRowNode = (def, isDefault) => {\n"
        "    const isApplied = appliedId === def.id;\n"
        "    const isOpen = readId === def.id;\n"
        "    const rowCls = styles.row\n"
        "      + (isOpen ? ' ' + styles.rowOpen : '')\n"
        "      + (isApplied ? ' ' + styles.rowApplied : '')\n"
        "      + (isDefault ? ' ' + styles.rowDefault : '');\n"
        "    return (\n"
        "      <div key={def.id} className={rowCls}>\n"
        "        <button className={styles.rowHead} onClick={() => setReadId(isOpen ? null : def.id)} aria-expanded={isOpen}>\n"
        "          <span className={styles.rowMain}>\n"
        "            <span className={styles.name}>{isDefault ? 'DEFAULT VIEW: ' : ''}{def.title}{isApplied && <span className={styles.appliedTag}>APPLIED</span>}</span>\n"
        "            <span className={styles.desc}>{def.desc}</span>\n"
        "          </span>\n"
        "          <span className={styles.rightMeta}>\n"
        "            <span className={styles.rows}>{liveCount(def)} ROWS</span>\n"
        "            <span className={styles.tag}>{def.chart !== 'NONE' ? def.chart : 'TABLE'} &middot; {def.group}</span>\n"
        "            <FiChevronDown className={styles.chev} aria-hidden=\"true\" />\n"
        "          </span>\n"
        "        </button>\n"
        "        {isOpen && (\n"
        "          <div className={styles.readout}>\n"
        "            <div className={styles.readoutText}>{readout(def)}</div>\n"
        "            <button className={styles.useBtn} onClick={() => applyDef(def)} disabled={isApplied}>{isApplied ? 'Applied \\u2713' : 'Use This Report'}</button>\n"
        "          </div>\n"
        "        )}\n"
        "      </div>\n"
        "    );\n"
        "  };\n",
        "catRowNode rebuilt: shared row/rowHead markup, APPLIED tag, chevron instead of text toggle hint, Use button now disables + relabels once applied",
    ),
    (
        "          <div className={styles.catList}>\n"
        "            {defaultDef && (\n"
        "              <div className={styles.catWrap}>\n"
        "                <button className={styles.catRow + ' ' + styles.catRowDef + (appliedId === defaultDef.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === defaultDef.id ? null : defaultDef.id)} aria-expanded={readId === defaultDef.id}>\n"
        "                  <span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.liveCount}>{liveCount(defaultDef)} ROWS</span><span className={styles.tag}>{defaultDef.chart !== 'NONE' ? defaultDef.chart : 'TABLE'} &middot; {defaultDef.group}</span><span className={styles.toggleHint}>{readId === defaultDef.id ? 'CLOSE \\u25B2' : 'WHAT IS THIS? \\u25BC'}</span></span>\n"
        "                  <span className={styles.r2}>{defaultDef.desc}</span>\n"
        "                </button>\n"
        "                {readId === defaultDef.id && (\n"
        "                  <div className={styles.readout}>\n"
        "                    <div className={styles.readoutText}>{readout(defaultDef)}</div>\n"
        "                    <button className={styles.useBtn} onClick={() => applyDef(defaultDef)}>USE THIS REPORT</button>\n"
        "                  </div>\n"
        "                )}\n"
        "              </div>\n"
        "            )}\n"
        "            {restList.length === 0 && !defaultDef && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}\n"
        "            {groupTab === 'ALL'\n"
        "              ? GROUPS.filter(g => restList.some(d => d.group === g)).map(g => (\n"
        "                <div key={g} className={styles.groupBlock}>\n"
        "                  <div className={styles.ddSec}>{g} ({restList.filter(d => d.group === g).length})</div>\n"
        "                  {restList.filter(d => d.group === g).map(catRowNode)}\n"
        "                </div>\n"
        "              ))\n"
        "              : restList.map(catRowNode)}\n"
        "          </div>\n",
        "          <div className={styles.catList}>\n"
        "            {defaultDef && (\n"
        "              <div className={styles.ungrouped}>\n"
        "                <div className={styles.groupBody}>\n"
        "                  {catRowNode(defaultDef, true)}\n"
        "                </div>\n"
        "              </div>\n"
        "            )}\n"
        "            {restList.length === 0 && !defaultDef && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}\n"
        "            {groupTab === 'ALL'\n"
        "              ? GROUPS.filter(g => restList.some(d => d.group === g)).map(g => (\n"
        "                <div key={g} className={styles.group}>\n"
        "                  <div className={styles.groupLabel}><span>{g} ({restList.filter(d => d.group === g).length})</span></div>\n"
        "                  <div className={styles.groupBody}>\n"
        "                    {restList.filter(d => d.group === g).map(d => catRowNode(d))}\n"
        "                  </div>\n"
        "                </div>\n"
        "              ))\n"
        "              : restList.length > 0 && (\n"
        "                <div className={styles.ungrouped}>\n"
        "                  <div className={styles.groupBody}>\n"
        "                    {restList.map(d => catRowNode(d))}\n"
        "                  </div>\n"
        "                </div>\n"
        "              )}\n"
        "          </div>\n",
        "default report + group listing rewired onto shared ungrouped/groupBody cards (was one .catWrap card per report)",
    ),
])

# ═══ ReportStudio.module.css -- shared-card list styling ═══
apply_patches(STUDIO_CSS, [
    (
        "/* Catalogue list: a soft warm tray behind white report cards. The tray\n"
        "   supplies the contrast (instead of dark panels) so every card reads as\n"
        "   a distinct, liftable object -- creative + professional, no dark fills. */\n"
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 9px;\n"
        "  scrollbar-width: thin; scrollbar-color: #EE8C3A transparent;\n"
        "}\n"
        ".catList::-webkit-scrollbar { width: 6px; }\n"
        ".catList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }\n"
        ".groupBlock { display: flex; flex-direction: column; gap: 9px; }\n"
        ".catWrap {\n"
        "  border-radius: 9px; overflow: hidden; border-left: 4px solid transparent;\n"
        "  box-shadow: 0 2px 7px rgba(26,46,48,0.12);\n"
        "  transition: box-shadow 0.2s ease, transform 0.2s ease;\n"
        "}\n"
        ".catWrap:hover { box-shadow: 0 8px 22px rgba(26,46,48,0.2); transform: translateY(-2px); }\n"
        "/* Per-group accent colour, so the list reads at a glance without leaning\n"
        "   on dark backgrounds -- each category gets its own light-safe hue. */\n"
        ".catWrap[data-group=\"WORK IN\"] { border-left-color: #EE8C3A; }\n"
        ".catWrap[data-group=\"IN PROCESS\"] { border-left-color: #4C9CD1; }\n"
        ".catWrap[data-group=\"MONEY IN\"] { border-left-color: #16a37a; }\n"
        ".catWrap[data-group=\"MONEY OUT\"] { border-left-color: #d9694a; }\n"
        ".catWrap[data-group=\"CLIENTS / RECOVERY\"] { border-left-color: #9b7fc7; }\n"
        ".catWrap[data-group=\"COMPLIANCE / ARCHIVE\"] { border-left-color: #64748b; }\n"
        ".catRow { display: flex; flex-direction: column; gap: 3px; width: 100%; text-align: left; border: none; background: #fff; padding: 10px 14px; cursor: pointer; transition: background 0.15s; }\n"
        ".catRow:hover { background: #EE8C3A; color: #fff; }\n"
        ".catRowOn { background: #d97e2f; color: #1a2e30; }\n"
        ".r1 { display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #5b6f70; }\n"
        ".r2 { font-size: 10px; font-weight: 600; color: rgba(26,46,48,0.55); }\n"
        ".catRow:hover .r1 { color: #fff; }\n"
        ".catRowOn .r1 { color: #1a2e30; }\n"
        ".catRow:hover .r2 { color: rgba(255,255,255,0.85); }\n"
        ".catRowOn .r2 { color: rgba(26,46,48,0.72); }\n"
        ".tag { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; opacity: 0.75; white-space: nowrap; }\n"
        ".readout { display: flex; align-items: center; gap: 12px; background: #0a0a0a; border-left: 3px solid #EE8C3A; padding: 8px 12px; }\n"
        ".readoutText { flex: 1; min-width: 0; font-family: 'Inter', sans-serif; font-size: 10.5px; font-weight: 600; line-height: 1.5; color: #c9f7d6; }\n"
        ".useBtn {\n"
        "  flex-shrink: 0; cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);\n"
        "  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 14px;\n"
        "  border-radius: 6px; border: none; background: #EE8C3A; color: #1a2e30; transition: all 0.2s;\n"
        "}\n"
        ".useBtn:hover:not(:disabled) { background: #f0a050; transform: translateY(-1px); }\n"
        ".useBtn:disabled { opacity: 0.45; cursor: not-allowed; }\n"
        ".emptyCell { text-align: center; padding: 24px 16px; font-family: 'Space Mono', monospace; font-size: 11px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(26,46,48,0.5); }\n"
        ".foot { padding: 8px 14px; background: #f6f3ef; color: rgba(26,46,48,0.55); font-size: 9px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; border-radius: 0 0 11px 11px; }\n",

        "/* fix118: prototype parity (report-catalogue-option1-refined.html).\n"
        "   Groups no longer render as a stack of individually-shadowed,\n"
        "   hover-lifting cards (one per report) -- each group now shares ONE\n"
        "   elevated white card (.groupBody) with hairline dividers between its\n"
        "   records. Only .groupBody/.ungrouped get the tray-lift shadow now;\n"
        "   the group label drops to flat, uncarded text sitting on the tray. */\n"
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; background: #f2ede4;\n"
        "  padding: 14px; display: flex; flex-direction: column; gap: 10px;\n"
        "  scrollbar-width: thin; scrollbar-color: #EE8C3A transparent;\n"
        "}\n"
        ".catList::-webkit-scrollbar { width: 6px; }\n"
        ".catList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }\n"
        ".group { display: flex; flex-direction: column; gap: 6px; }\n"
        ".ungrouped, .groupBody { border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(26,46,48,0.14); background: #fff; }\n"
        ".groupLabel { padding: 2px 4px; }\n"
        ".groupLabel span { font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: #162a2c; transition: color 0.18s ease; }\n"
        ".groupLabel span:hover { color: #EE8C3A; }\n"
        "/* the row itself carries the left rail, so an expanded readout can\n"
        "   share it, and the hairline divider between records. */\n"
        ".row { border-left: 3px solid transparent; border-bottom: 1.5px solid rgba(26,46,48,0.16); transition: border-left-color 0.16s ease; }\n"
        ".row:last-child { border-bottom: none; }\n"
        ".row.rowOpen, .row.rowApplied { border-left-color: #EE8C3A; }\n"
        "/* applied: a real, visible orange wash rather than just the rail --\n"
        "   text stays ink, and it keeps its own fill even on hover instead of\n"
        "   flipping to the open row's solid orange. */\n"
        ".row.rowApplied .rowHead { background: rgba(238,140,58,0.26); }\n"
        ".row.rowApplied .name, .row.rowApplied .rows, .row.rowApplied .tag, .row.rowApplied .chev { color: #1a2e30; }\n"
        ".row.rowApplied .desc { color: rgba(26,46,48,0.65); }\n"
        ".rowHead { display: flex; align-items: center; gap: 14px; width: 100%; text-align: left; border: none; background: transparent; padding: 14px 15px; cursor: pointer; transition: background 0.15s ease; }\n"
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
        ".rowHead:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }\n"
        ".rowMain { flex: 1; min-width: 0; display: flex; flex-direction: column; }\n"
        ".name { font-size: 13px; font-weight: 800; letter-spacing: 0.3px; text-transform: uppercase; color: #1a2e30; transition: color 0.15s ease; }\n"
        ".desc { font-size: 11px; font-weight: 600; color: rgba(26,46,48,0.55); margin-top: 3px; transition: color 0.15s ease; }\n"
        ".rightMeta { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }\n"
        ".rows { font-family: 'Space Mono', monospace; font-size: 10px; color: rgba(26,46,48,0.4); white-space: nowrap; transition: color 0.15s ease; }\n"
        ".tag { font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; color: rgba(26,46,48,0.4); white-space: nowrap; transition: color 0.15s ease; }\n"
        ".chev { color: rgba(26,46,48,0.35); font-size: 12px; flex-shrink: 0; transition: transform 0.2s ease, color 0.15s ease; }\n"
        ".row.rowOpen .chev { transform: rotate(180deg); color: #EE8C3A; }\n"
        ".row.rowApplied.rowOpen .chev { color: #1a2e30; }\n"
        ".appliedTag { font-family: 'Space Mono', monospace; font-size: 8px; font-weight: 700; letter-spacing: 1px; color: #a8551c; background: rgba(255,255,255,0.5); border-radius: 4px; padding: 2px 6px; margin-left: 8px; }\n"
        "/* rowDefault: the one row that should still stand out with nothing\n"
        "   applied or open yet -- a light permanent wash, restating the old\n"
        "   .catRowDef for the shared-card layout. Open/applied rules above\n"
        "   this in the cascade still win once either happens. */\n"
        ".row.rowDefault { border-left-color: rgba(238,140,58,0.6); }\n"
        ".row.rowDefault .rowHead { background: #fdf3e7; }\n"
        "/* readout sits flush against the row's own left rail with zero extra\n"
        "   margin -- the rail stops exactly where the readout stops. */\n"
        ".readout { display: flex; align-items: center; gap: 12px; padding: 12px 15px; margin: 0; background: #28383a; }\n"
        ".readoutText { flex: 1; min-width: 0; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; line-height: 1.5; color: rgba(242,237,228,0.85); }\n"
        "/* real HeaderButton .primary spec: ~34px tall, recolor-only hover (no\n"
        "   lift/transform), disabled/applied reuses the same colors at 0.5\n"
        "   opacity instead of the old 0.45. */\n"
        ".useBtn {\n"
        "  flex-shrink: 0; cursor: pointer; height: 34px; padding: 0 16px; border-radius: 6px;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);\n"
        "  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;\n"
        "  border: 1.5px solid #EE8C3A; background: #EE8C3A; color: #1a2e30; transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;\n"
        "}\n"
        ".useBtn:hover:not(:disabled) { background: #d97a2b; border-color: #d97a2b; color: #1a2e30; }\n"
        ".useBtn:disabled { opacity: 0.5; cursor: not-allowed; }\n"
        ".emptyCell { text-align: center; padding: 24px 16px; font-family: 'Space Mono', monospace; font-size: 11px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(26,46,48,0.5); }\n"
        ".foot { padding: 10px 14px; background: #f6f3ef; color: rgba(26,46,48,0.55); font-size: 9px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; border-radius: 0 0 11px 11px; }\n",
        "catalogue list rebuilt onto shared group cards (.group/.groupLabel/.groupBody/.ungrouped/.row/.rowHead), applied-wash + persistent-open row states, flush readout, real HeaderButton-spec Use button",
    ),
    (
        ".catRowDef { border-left: 3px solid #EE8C3A; background: #fdf3e7; }\n"
        ".catRowDef:hover { background: #EE8C3A; }\n"
        ".catRowDef.catRowOn { background: #d97e2f; }\n"
        ".ddSec { position: sticky; top: -10px; background: #f2ede4; color: rgba(26,46,48,0.55); font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; padding: 6px 4px 2px; z-index: 1; }\n"
        ".toggleHint { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; opacity: 0.75; white-space: nowrap; }\n"
        ".tag + .toggleHint { margin-left: 8px; }\n",
        "",
        "dead rules removed: .catRowDef/.ddSec/.toggleHint superseded by .rowDefault/.groupLabel/.chev above",
    ),
    (
        ".liveCount { margin-left: 8px; font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; color: rgba(26,46,48,0.55); white-space: nowrap; }\n"
        ".catRow:hover .liveCount, .catRowOn .liveCount { color: rgba(255,255,255,0.85); }\n",
        "",
        "dead rule removed: .liveCount superseded by .rows above (row count now lives in .rightMeta with the same hover/open/applied color rules as .tag/.chev)",
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
git("commit", "-m", "fix118: Report Catalogue list rebuilt to the Option 1 Refined prototype -- shared group cards, applied wash, persistent open fill, flush readout, real HeaderButton-spec Use button")
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