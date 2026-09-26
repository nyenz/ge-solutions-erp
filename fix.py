#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix112: Reports page's Scope + Report Catalogue headers now
# match Intake's CollapsibleSection panels, and the catalogue list gets real
# contrast between rows without leaning on dark fills.
#
# What this fixes, and why:
#   1. Design drift. The Scope and Report Catalogue panels on the Reports
#      page had their own flat teal card + separate little chevron button,
#      which didn't match the gradient card + orange "wake up" hover that
#      every CollapsibleSection on the Intake page already uses. They now
#      share that exact look: gradient body, border warms to orange and the
#      shadow deepens on hover, content fades/slides in on open.
#   2. Reactivity. Collapsing either panel only worked if you hit the small
#      chevron dead-on -- clicking the rest of the header row did nothing.
#      Both headers are now click-anywhere-to-toggle (plus Enter/Space when
#      focused), same as Intake. The Catalogue header's search box stops
#      that click from bubbling up, so typing/clearing search still works
#      without collapsing the panel. The Catalogue header's own dimensions
#      are left alone -- it still needs the room for the search field.
#   3. Catalogue list contrast. Report rows sat flush against a plain white
#      list with only a 1px hairline between them, so nothing stood out.
#      The list now sits on a soft warm tray instead of white, so each
#      report renders as its own lifted card (shadow, lifts further on
#      hover), and each card picks up a thin left-edge colour by its group
#      (Work In / In Process / Money In / Money Out / Clients-Recovery /
#      Compliance-Archive) -- distinct at a glance, no dark backgrounds.
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

REPORT_STUDIO_JSX = os.path.join(SRC, "pages", "Reports", "ReportStudio.jsx")
REPORT_STUDIO_CSS = os.path.join(SRC, "pages", "Reports", "ReportStudio.module.css")


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


# ═══ 1. ReportStudio.jsx -- click-anywhere headers + per-group data hook ═══
apply_patches(REPORT_STUDIO_JSX, [
    (
        "        <div className={styles.panelHeadRow}>\n"
        "          <span className={styles.scopeTitle}>SCOPE</span>\n"
        "          <button className={styles.headToggle} onClick={() => setScopeOpen(o => !o)} aria-expanded={scopeOpen} aria-label=\"Collapse or expand scope panel\">\n"
        "            <FiChevronDown className={scopeOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
        "          </button>\n"
        "        </div>",
        "        <div\n"
        "          className={styles.panelHeadRow}\n"
        "          role=\"button\"\n"
        "          tabIndex={0}\n"
        "          onClick={() => setScopeOpen(o => !o)}\n"
        "          onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setScopeOpen(o => !o); } }}\n"
        "          aria-expanded={scopeOpen}\n"
        "          aria-label=\"Collapse or expand scope panel\"\n"
        "        >\n"
        "          <span className={styles.scopeTitle}>SCOPE</span>\n"
        "          <span className={styles.headToggle}>\n"
        "            <FiChevronDown className={scopeOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
        "          </span>\n"
        "        </div>",
        "Scope panel head: whole row is now the collapse toggle, not just the chevron",
    ),
    (
        "  const catRowNode = (def) => (\n"
        "    <div key={def.id} className={styles.catWrap}>",
        "  const catRowNode = (def) => (\n"
        "    <div key={def.id} className={styles.catWrap} data-group={def.group}>",
        "catalogue row wrap carries its report's group, for the CSS colour accent",
    ),
    (
        "      <div className={(catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.catPanelClosed + ' ' + styles.panelCollapsed)}>\n"
        "        {catOpen && <CornerDecor hideTop />}\n"
        "        <div className={styles.panelHeadRow}>\n"
        "          <span className={styles.scopeTitle}>REPORT CATALOGUE</span>\n"
        "          <span className={styles.badge}>{searched.length} MATCHES</span>\n"
        "          <div className={styles.searchBox}>\n"
        "            <FiSearch className={styles.searchIcon} aria-hidden=\"true\" />\n"
        "            <input value={search} onChange={e => setSearch(e.target.value)} placeholder=\"Search reports...\" aria-label=\"Search reports\" style={{ paddingLeft: 40 }} />\n"
        "            {search && <button className={styles.searchClear} onClick={() => setSearch('')} aria-label=\"Clear search\"><FiX size={13} aria-hidden=\"true\" /></button>}\n"
        "          </div>\n"
        "          <button className={styles.headToggle} onClick={() => setCatOpen(o => !o)} aria-expanded={catOpen} aria-label=\"Collapse or expand catalogue panel\">\n"
        "            <FiChevronDown className={catOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
        "          </button>\n"
        "        </div>\n"
        "        <div className={styles.tabRow}>\n"
        "          <button className={groupTab === 'ALL' ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab('ALL')}>\n"
        "            ALL<span className={styles.gcnt}>{searched.length}</span>\n"
        "          </button>\n"
        "          {GROUPS.map(g => {\n"
        "            const n = searched.filter(d => d.group === g).length;\n"
        "            if (!n && g !== groupTab) return null;\n"
        "            return (\n"
        "              <button key={g} className={groupTab === g ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab(g)}>\n"
        "                {g}<span className={styles.gcnt}>{n}</span>\n"
        "              </button>\n"
        "            );\n"
        "          })}\n"
        "        </div>\n"
        "        {recentDefs.length > 0 && (\n"
        "          <div className={styles.recentRow}>\n"
        "            <span className={styles.recentLabel}>RECENTLY USED</span>\n"
        "            {recentDefs.map(d => (\n"
        "              <button key={d.id} className={styles.rchip} onClick={() => applyDef(d)}>{d.title}</button>\n"
        "            ))}\n"
        "          </div>\n"
        "        )}\n"
        "        <div className={styles.catList}>\n"
        "          {defaultDef && (\n"
        "            <div className={styles.catWrap}>\n"
        "              <button className={styles.catRow + ' ' + styles.catRowDef + (appliedId === defaultDef.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === defaultDef.id ? null : defaultDef.id)} aria-expanded={readId === defaultDef.id}>\n"
        "                <span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.liveCount}>{liveCount(defaultDef)} ROWS</span><span className={styles.tag}>{defaultDef.chart !== 'NONE' ? defaultDef.chart : 'TABLE'} &middot; {defaultDef.group}</span><span className={styles.toggleHint}>{readId === defaultDef.id ? 'CLOSE \\u25B2' : 'WHAT IS THIS? \\u25BC'}</span></span>\n"
        "                <span className={styles.r2}>{defaultDef.desc}</span>\n"
        "              </button>\n"
        "              {readId === defaultDef.id && (\n"
        "                <div className={styles.readout}>\n"
        "                  <div className={styles.readoutText}>{readout(defaultDef)}</div>\n"
        "                  <button className={styles.useBtn} onClick={() => applyDef(defaultDef)}>USE THIS REPORT</button>\n"
        "                </div>\n"
        "              )}\n"
        "            </div>\n"
        "          )}\n"
        "          {restList.length === 0 && !defaultDef && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}\n"
        "          {groupTab === 'ALL'\n"
        "            ? GROUPS.filter(g => restList.some(d => d.group === g)).map(g => (\n"
        "              <div key={g}>\n"
        "                <div className={styles.ddSec}>{g} ({restList.filter(d => d.group === g).length})</div>\n"
        "                {restList.filter(d => d.group === g).map(catRowNode)}\n"
        "              </div>\n"
        "            ))\n"
        "            : restList.map(catRowNode)}\n"
        "        </div>\n"
        "        <div className={styles.foot}>\n"
        "          {listed.length} report{listed.length === 1 ? '' : 's'} in {groupTab === 'ALL' ? 'all groups' : groupTab}{defaultDef ? ' (+1 default)' : ''}\n"
        "          {search ? ' matching \"' + search + '\"' : ''}\n"
        "          {entity ? ' for ' + entity.label.toLowerCase() + ' ' + entity.value : ' for the whole company'}\n"
        "          {' · ' + scopeRows.length + ' of ' + rows.length + ' rows in scope'}\n"
        "        </div>\n"
        "      </div>",
        "      <div className={(catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.panelCollapsed)}>\n"
        "        {catOpen && <CornerDecor hideTop />}\n"
        "        <div\n"
        "          className={styles.panelHeadRow}\n"
        "          role=\"button\"\n"
        "          tabIndex={0}\n"
        "          onClick={() => setCatOpen(o => !o)}\n"
        "          onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setCatOpen(o => !o); } }}\n"
        "          aria-expanded={catOpen}\n"
        "          aria-label=\"Collapse or expand catalogue panel\"\n"
        "        >\n"
        "          <span className={styles.scopeTitle}>REPORT CATALOGUE</span>\n"
        "          <span className={styles.badge}>{searched.length} MATCHES</span>\n"
        "          <div className={styles.searchBox} onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()}>\n"
        "            <FiSearch className={styles.searchIcon} aria-hidden=\"true\" />\n"
        "            <input value={search} onChange={e => setSearch(e.target.value)} placeholder=\"Search reports...\" aria-label=\"Search reports\" style={{ paddingLeft: 40 }} />\n"
        "            {search && <button className={styles.searchClear} onClick={() => setSearch('')} aria-label=\"Clear search\"><FiX size={13} aria-hidden=\"true\" /></button>}\n"
        "          </div>\n"
        "          <span className={styles.headToggle}>\n"
        "            <FiChevronDown className={catOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
        "          </span>\n"
        "        </div>\n"
        "        <div className={catOpen ? styles.catBody : styles.panelClosed}>\n"
        "          <div className={styles.tabRow}>\n"
        "            <button className={groupTab === 'ALL' ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab('ALL')}>\n"
        "              ALL<span className={styles.gcnt}>{searched.length}</span>\n"
        "            </button>\n"
        "            {GROUPS.map(g => {\n"
        "              const n = searched.filter(d => d.group === g).length;\n"
        "              if (!n && g !== groupTab) return null;\n"
        "              return (\n"
        "                <button key={g} className={groupTab === g ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab(g)}>\n"
        "                  {g}<span className={styles.gcnt}>{n}</span>\n"
        "                </button>\n"
        "              );\n"
        "            })}\n"
        "          </div>\n"
        "          {recentDefs.length > 0 && (\n"
        "            <div className={styles.recentRow}>\n"
        "              <span className={styles.recentLabel}>RECENTLY USED</span>\n"
        "              {recentDefs.map(d => (\n"
        "                <button key={d.id} className={styles.rchip} onClick={() => applyDef(d)}>{d.title}</button>\n"
        "              ))}\n"
        "            </div>\n"
        "          )}\n"
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
        "          </div>\n"
        "          <div className={styles.foot}>\n"
        "            {listed.length} report{listed.length === 1 ? '' : 's'} in {groupTab === 'ALL' ? 'all groups' : groupTab}{defaultDef ? ' (+1 default)' : ''}\n"
        "            {search ? ' matching \"' + search + '\"' : ''}\n"
        "            {entity ? ' for ' + entity.label.toLowerCase() + ' ' + entity.value : ' for the whole company'}\n"
        "            {' · ' + scopeRows.length + ' of ' + rows.length + ' rows in scope'}\n"
        "          </div>\n"
        "        </div>\n"
        "      </div>",
        "Catalogue panel: whole head row toggles (search box stops that bubbling), "
        "body wrapped so it can fade/slide in like Intake's sections, group divs "
        "tagged so rows can be styled per group",
    ),
])

# ═══ 2. ReportStudio.module.css -- Intake-matching cards + list contrast ═══
apply_patches(REPORT_STUDIO_CSS, [
    (
        ".studio { display: flex; flex-direction: column; gap: clamp(10px, 1.4vw, 16px); }\n"
        ".scopePanel, .catPanel, .viewerPanel {\n"
        "  background: #4a6a6c;\n"
        "  border: 1.5px solid rgba(255, 255, 255, 0.10);\n"
        "  border-radius: 12px;\n"
        "  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);\n"
        "  overflow: visible;\n"
        "}\n"
        ".panelHeadRow {\n"
        "  display: flex; flex-wrap: wrap; align-items: center; gap: 10px;\n"
        "  background: #162a2c; border-bottom: 1.5px solid #EE8C3A;\n"
        "  border-radius: 11px 11px 0 0; padding: 10px 14px;\n"
        "}",
        ".studio { display: flex; flex-direction: column; gap: clamp(10px, 1.4vw, 16px); }\n"
        ".scopePanel, .catPanel, .viewerPanel {\n"
        "  border: 1.5px solid rgba(255, 255, 255, 0.10);\n"
        "  border-radius: 12px;\n"
        "  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);\n"
        "  overflow: visible;\n"
        "}\n"
        ".viewerPanel { background: #4a6a6c; }\n"
        "/* Scope + Catalogue containers now match Intake's CollapsibleSection card:\n"
        "   same gradient body and the same wake-up hover -- border warms to\n"
        "   orange and the shadow deepens, telling you the whole card is live. */\n"
        ".scopePanel, .catPanel {\n"
        "  background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%);\n"
        "  border-color: rgba(238, 140, 58, 0.2);\n"
        "  transition: border-color 0.3s ease, box-shadow 0.3s ease;\n"
        "}\n"
        ".scopePanel:hover, .catPanel:hover {\n"
        "  border-color: #EE8C3A;\n"
        "  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);\n"
        "}\n"
        ".panelHeadRow {\n"
        "  display: flex; flex-wrap: wrap; align-items: center; gap: 10px;\n"
        "  background: #162a2c; border-bottom: 1.5px solid #EE8C3A;\n"
        "  border-radius: 11px 11px 0 0; padding: 10px 14px;\n"
        "  width: 100%; box-sizing: border-box; text-align: left;\n"
        "  transition: border-bottom-color 0.25s ease, border-radius 0.25s ease;\n"
        "}\n"
        "/* Only the Scope + Catalogue heads are clickable toggles (like Intake's\n"
        "   CollapsibleSection); the Preview head reuses this class but stays\n"
        "   inert, so it keeps the default cursor. */\n"
        ".scopePanel .panelHeadRow, .catPanel .panelHeadRow { cursor: pointer; }\n"
        ".scopePanel .panelHeadRow:focus-visible, .catPanel .panelHeadRow:focus-visible { outline: 2px solid #EE8C3A; outline-offset: -2px; }",
        "panel cards get Intake's gradient + hover glow; header row becomes a full click target",
    ),
    (
        ".scopeBody { padding: clamp(12px, 1.6vw, 18px); display: flex; flex-direction: column; gap: clamp(10px, 1.3vw, 14px); }",
        ".scopeBody { padding: clamp(12px, 1.6vw, 18px); display: flex; flex-direction: column; gap: clamp(10px, 1.3vw, 14px); animation: panelExpand 0.2s ease-out; }\n"
        ".catBody { animation: panelExpand 0.2s ease-out; }\n"
        "@keyframes panelExpand {\n"
        "  from { opacity: 0; transform: translateY(-4px); }\n"
        "  to   { opacity: 1; transform: translateY(0); }\n"
        "}",
        "opening a panel now fades/slides its body in, matching Intake's expand animation",
    ),
    (
        ".catList { max-height: 340px; overflow-y: auto; background: #fff; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }\n"
        ".catList::-webkit-scrollbar { width: 6px; }\n"
        ".catList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }\n"
        ".catWrap { border-bottom: 1px solid #f1eeea; }\n"
        ".catWrap:last-child { border-bottom: none; }\n"
        ".catRow { display: flex; flex-direction: column; gap: 3px; width: 100%; text-align: left; border: none; background: #fff; padding: 9px 14px; cursor: pointer; transition: background 0.15s; }\n"
        ".catRow:hover { background: #EE8C3A; color: #fff; }\n"
        ".catRowOn { background: #d97e2f; color: #1a2e30; }",
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
        ".catRowOn { background: #d97e2f; color: #1a2e30; }",
        "catalogue rows become distinct lifted cards on a warm tray, with a per-group colour edge",
    ),
    (
        ".ddSec { position: sticky; top: 0; background: #f6f3ef; color: rgba(26,46,48,0.55); font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; padding: 6px 14px; border-bottom: 1px solid #dfd9d1; z-index: 1; }",
        ".ddSec { position: sticky; top: -10px; background: #f2ede4; color: rgba(26,46,48,0.55); font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; padding: 6px 4px 2px; z-index: 1; }",
        "group section label matches the new tray background instead of its own near-identical grey bar",
    ),
    (
        ".panelClosed { display: none; }\n"
        ".catPanelClosed > *:not(.panelHeadRow) { display: none; }",
        ".panelClosed { display: none; }",
        "catPanelClosed no longer needed -- catalogue body now hides via panelClosed like scope's body does",
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
git("commit", "-m", "fix112: Reports Scope + Catalogue headers match Intake's CollapsibleSection style (gradient card, click-anywhere collapse, hover glow), catalogue list gets per-group colour contrast")
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