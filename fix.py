#!/usr/bin/env python3
# PATH: fix145.py
# DESIGN PASS -- fix145: one tab/filter control for the whole app, and one spacing scale for every list page.
#
#   1. NEW COMPONENT TabDock (components/common/TabDock.jsx + .module.css). It is the Settings-page tab bar
#      turned into a component: one dark tray, pill buttons inside it, the active pill solid orange. Optional
#      per-item count, icon and accent (orange / red / green / yellow / cyan). mode="filter" (aria-pressed)
#      or mode="tab" (role=tablist). Colours and sizes live only in TabDock.module.css.
#   2. TabDock REPLACES the hand-rolled buttons on Ledger, Clients, Payments and Recovery. CRITICAL and
#      PROBLEM filters get the red accent.
#   3. PAGE RHYTHM. index.css gets six variables (--page-pad-top/x/bottom, --hdr-pad, --block-gap, --ctl-gap).
#      Ledger, Clients, Recovery and Expenses already used those numbers; Payments, Audit and Reports had
#      drifted roomier, which is why their top sections looked unevenly spaced. All of them now read from the
#      variables (Ledger, Clients, Recovery, Payments, Audit, Reports, Expenses, Portfolio, Settings CSS).
#   4. Guide Section 7 gets two notes: TabDock is the only filter/tab control, and the page-rhythm variables.
#
# NOT in this fix: the backend, the seed data, the schema, and any page not listed above.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
# Names, and one variable per file this fix touches.
FIX_NO = "fix145"
COMMIT_MSG = "fix145: design pass -- shared TabDock tab/filter control (Ledger, Clients, Payments, Recovery) and one page-rhythm spacing scale in index.css applied across Ledger, Clients, Recovery, Payments, Audit, Reports, Expenses, Settings; guide Section 7 notes"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
TABDOCK_JSX = os.path.join(FRONTEND, "src", "components", "common", "TabDock.jsx")
TABDOCK_CSS = os.path.join(FRONTEND, "src", "components", "common", "TabDock.module.css")
INDEX_CSS = os.path.join(FRONTEND, "src", "index.css")
AUDIT_CSS = os.path.join(FRONTEND, "src", "pages", "Audit", "AuditPage.module.css")
CLIENTLEDGER_JSX = os.path.join(FRONTEND, "src", "pages", "Clients", "ClientLedgerPage.jsx")
CLIENTLEDGER_CSS = os.path.join(FRONTEND, "src", "pages", "Clients", "ClientLedgerPage.module.css")
PORTFOLIO_CSS = os.path.join(FRONTEND, "src", "pages", "Clients", "ClientPortfolioPage.module.css")
EXPENSES_CSS = os.path.join(FRONTEND, "src", "pages", "Financials", "ExpensesPage.module.css")
LEDGER_JSX = os.path.join(FRONTEND, "src", "pages", "Ledger", "LedgerPage.jsx")
LEDGER_CSS = os.path.join(FRONTEND, "src", "pages", "Ledger", "LedgerPage.module.css")
PAYMENTS_JSX = os.path.join(FRONTEND, "src", "pages", "Payments", "PaymentsPage.jsx")
PAYMENTS_CSS = os.path.join(FRONTEND, "src", "pages", "Payments", "PaymentsPage.module.css")
RECOVERY_JSX = os.path.join(FRONTEND, "src", "pages", "Recovery", "RecoveryPortal.jsx")
RECOVERY_CSS = os.path.join(FRONTEND, "src", "pages", "Recovery", "RecoveryPortal.module.css")
REPORTHUB_CSS = os.path.join(FRONTEND, "src", "pages", "Reports", "ReportHub.module.css")
SETTINGS_CSS = os.path.join(FRONTEND, "src", "pages", "settings", "SettingsPage.module.css")
# ============================= EDIT PART 1 END =============================

# ================== DO NOT EDIT: helpers (copy exactly) ====================
MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# sub = exact find/replace of the FIRST match. Prints OK / SKIP / MISSING.
def sub(text, old, new, desc):
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


# newfile = create (or replace) a whole file. SKIP if it already holds `marker`.
def newfile(path, text, label, marker):
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)


# ============================ EDIT PART 2 START ============================
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (
    INDEX_CSS, AUDIT_CSS, CLIENTLEDGER_JSX, CLIENTLEDGER_CSS,
    PORTFOLIO_CSS, EXPENSES_CSS, LEDGER_JSX, LEDGER_CSS,
    PAYMENTS_JSX, PAYMENTS_CSS, RECOVERY_JSX, RECOVERY_CSS,
    REPORTHUB_CSS, SETTINGS_CSS, GUIDE,
)
for _p in LOAD_FILES:
    load(_p)

# ---- new file: TabDock.jsx (new shared tab / filter component) ----
newfile(TABDOCK_JSX,
        "\n".join([
            "// PATH: erp-frontend/src/components/common/TabDock.jsx",
            "import React from 'react';",
            "import styles from './TabDock.module.css';",
            "",
            "/**",
            " * TabDock -- THE tab / filter control for the whole app.",
            " *",
            " * One tray, pill buttons inside it, the active pill solid orange. This is",
            " * the Settings page tab bar (and Report Studio's dataset row) turned into a",
            " * component, so Ledger, Clients, Payments and Recovery all look identical.",
            " * Do NOT hand-roll filter buttons on a page any more -- use this.",
            " *",
            " * items    [{ key, label, count?, icon?, accent?, title? }]",
            " *            count  -> small Space Mono number after the label",
            " *            icon   -> a react-icons / lucide component (optional)",
            " *            accent -> 'orange' (default) | 'red' | 'green' | 'yellow' | 'cyan'",
            " *                      tints the hover + active colour, like Settings does",
            " * value    the active key",
            " * onChange (key) => void",
            " * mode     'filter' (default: buttons, aria-pressed)  |  'tab' (role=tablist)",
            " * label    accessible name for the group",
            " * end      optional node shown after the tray (e.g. a \"5 SECTIONS\" badge)",
            " */",
            "const TabDock = ({ items, value, onChange, mode = 'filter', label, end = null, className = '' }) => {",
            "    const isTab = mode === 'tab';",
            "    return (",
            "        <div className={`${styles.dockRow} ${className}`}>",
            "            <div className={styles.tabDock}>",
            "                <div",
            "                    className={styles.tabRow}",
            "                    role={isTab ? 'tablist' : 'group'}",
            "                    aria-label={label}",
            "                >",
            "                    {items.map(({ key, label: text, count, icon: Icon, accent = 'orange', title }) => {",
            "                        const on = value === key;",
            "                        return (",
            "                            <button",
            "                                key={key}",
            "                                type=\"button\"",
            "                                className={on ? styles.tabOn : styles.tab}",
            "                                data-accent={accent}",
            "                                title={title}",
            "                                onClick={() => onChange(key)}",
            "                                {...(isTab",
            "                                    ? { role: 'tab', 'aria-selected': on }",
            "                                    : { 'aria-pressed': on })}",
            "                            >",
            "                                {Icon && <Icon aria-hidden=\"true\" />}",
            "                                <span>{text}</span>",
            "                                {count !== undefined && count !== null && (",
            "                                    <span className={styles.tabCount}>{count}</span>",
            "                                )}",
            "                            </button>",
            "                        );",
            "                    })}",
            "                </div>",
            "            </div>",
            "            {end}",
            "        </div>",
            "    );",
            "};",
            "",
            "export default TabDock;",
            "",
        ]),
        "TabDock.jsx (new shared tab / filter component)",
        "TabDock")

# ---- new file: TabDock.module.css (new) ----
newfile(TABDOCK_CSS,
        "\n".join([
            "/* PATH: erp-frontend/src/components/common/TabDock.module.css",
            "   Shared tab / filter dock. Values are copied 1:1 from the Settings page",
            "   \".tabDock / .tab / .tabOn\" block so both always look the same.",
            "   The tray is the ONLY box; pills inside it have no box of their own until",
            "   they are the active one.",
            "",
            "   CONTRAST: the tray is dark (#4d5c5a) so pill text is white-ish on it, and",
            "   the active pill is navy text on solid orange -- same as Settings. */",
            ".dockRow {",
            "    display: flex; flex-wrap: wrap; align-items: center; gap: 10px;",
            "    max-width: 100%; min-width: 0;",
            "}",
            ".tabDock {",
            "    flex: 0 1 auto; min-width: 0; max-width: 100%;",
            "    display: flex; align-items: center;",
            "    background: #4d5c5a;",
            "    border: none; border-radius: 8px;",
            "    padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);",
            "    /* Many filters on a narrow screen: the tray scrolls sideways instead of",
            "       breaking the pills onto extra rows. */",
            "    overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none;",
            "}",
            ".tabDock::-webkit-scrollbar { display: none; }",
            ".tabRow { display: flex; flex-wrap: nowrap; gap: 6px; align-items: center; }",
            "",
            ".tab, .tabOn {",
            "    --accent: #EE8C3A;",
            "    --accent-glow: rgba(238, 140, 58, 0.32);",
            "    display: inline-flex; align-items: center; gap: 8px; flex-shrink: 0;",
            "    white-space: nowrap; cursor: pointer;",
            "    font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;",
            "    letter-spacing: 1.5px; text-transform: uppercase;",
            "    padding: 8px 12px; border-radius: 6px; outline: none;",
            "    border: 1.5px solid transparent; background: transparent;",
            "    color: rgba(255, 255, 255, 0.92);",
            "    transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;",
            "}",
            ".tab[data-accent=\"red\"],    .tabOn[data-accent=\"red\"]    { --accent: #ef4444; --accent-glow: rgba(239, 68, 68, 0.32); }",
            ".tab[data-accent=\"green\"],  .tabOn[data-accent=\"green\"]  { --accent: #34d399; --accent-glow: rgba(52, 211, 153, 0.32); }",
            ".tab[data-accent=\"yellow\"], .tabOn[data-accent=\"yellow\"] { --accent: #eab308; --accent-glow: rgba(234, 179, 8, 0.32); }",
            ".tab[data-accent=\"cyan\"],   .tabOn[data-accent=\"cyan\"]   { --accent: #22d3ee; --accent-glow: rgba(34, 211, 238, 0.32); }",
            "",
            ".tab:hover { color: var(--accent); }",
            ".tabOn {",
            "    color: #1a2e30;",
            "    background: var(--accent); border-color: var(--accent);",
            "    box-shadow: 0 4px 16px var(--accent-glow);",
            "}",
            ".tabOn[data-accent=\"red\"] { color: #fff; }",
            ".tab:focus-visible, .tabOn:focus-visible { outline: 2px solid rgba(255, 255, 255, 0.4); outline-offset: -2px; }",
            ".tabCount { font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.8vw, 9px); opacity: 0.75; }",
            "",
            "@media (max-width: 480px) {",
            "    .tab, .tabOn { padding: 7px 10px; font-size: 8px; }",
            "}",
            "",
        ]),
        "TabDock.module.css (new)",
        ".tabDock")

# ---- index.css ----
patch(INDEX_CSS,
      "\n".join([
          "    --stat-value:    clamp(13px, 1.45vw, 16.5px);",
          "    --stat-value-sm: clamp(11px, 1.2vw,  13px);",
          "    --stat-note:     clamp(7px,  0.8vw,  9px);",
          "}",
          "",
          "* {",
      ]),
      "\n".join([
          "    --stat-value:    clamp(13px, 1.45vw, 16.5px);",
          "    --stat-value-sm: clamp(11px, 1.2vw,  13px);",
          "    --stat-note:     clamp(7px,  0.8vw,  9px);",
          "",
          "    /* ===== PAGE RHYTHM (design pass) ================================",
          "       ONE spacing scale for the stack every list page shares:",
          "           page title bar -> stat cards -> search -> tabs/filters -> table",
          "       Ledger, Clients, Recovery and Expenses already used these exact",
          "       numbers; Payments, Audit and Reports had drifted roomier, which",
          "       is why their top sections looked unevenly spaced. Every page now",
          "       reads from here -- change a number once, every page moves.",
          "         --page-pad-*   space between the page content and the screen edge",
          "         --hdr-pad      inside the title bar",
          "         --block-gap    between two stacked blocks (title bar, stat row,",
          "                        control cluster, table)",
          "         --ctl-gap      inside the control cluster (search / tabs / legend)",
          "       ============================================================== */",
          "    --page-pad-top:    clamp(12px, 2vh, 22px);",
          "    --page-pad-x:      clamp(12px, 2vw, 24px);",
          "    --page-pad-bottom: 28px;",
          "    --hdr-pad:         clamp(8px, 1.2vw, 14px) clamp(14px, 1.8vw, 22px);",
          "    --block-gap:       clamp(10px, 1.5vh, 16px);",
          "    --ctl-gap:         10px;",
          "}",
          "",
          "* {",
      ]),
      "index.css: change 1 of 1")

# ---- AuditPage.module.css ----
patch(AUDIT_CSS,
      "\n".join([
          "  min-width: 108px;",
          "}",
          ".dateField:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.16); }",
      ]),
      "\n".join([
          "  min-width: 108px;",
          "}",
          ".dateField:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.16); }",
          "",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Tokens live in index.css. Last rule wins. */",
          ".pageHeader { padding: var(--hdr-pad); margin-bottom: var(--block-gap); }",
          "@media (min-width: 641px) {",
          "    .container { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); }",
          "}",
          ".controlHub { margin-bottom: var(--block-gap); }",
          "",
          "/* title bar: same type scale and title/subtitle gap as every other page */",
          ".headerLeft { gap: 3px; }",
          ".title { line-height: normal; margin: 0; letter-spacing: 2px; }",
          "@media (min-width: 481px) {",
          "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
          "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
          "}",
      ]),
      "AuditPage.module.css: change 1 of 1")

# ---- ClientLedgerPage.jsx ----
patch(CLIENTLEDGER_JSX,
      "\n".join([
          "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';",
          "import styles from './ClientLedgerPage.module.css';",
          "import { LoadingRow } from '../../components/common/LoadingState';",
          "",
          "const matchesSearch = (c, term) => {",
          "    if (!term) return true;",
      ]),
      "\n".join([
          "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';",
          "import styles from './ClientLedgerPage.module.css';",
          "import { LoadingRow } from '../../components/common/LoadingState';",
          "import TabDock from '../../components/common/TabDock';",
          "",
          "const matchesSearch = (c, term) => {",
          "    if (!term) return true;",
      ]),
      "ClientLedgerPage.jsx: change 1 of 3")

patch(CLIENTLEDGER_JSX,
      "\n".join([
          "",
          "    const FILTERS = [",
          "        { key: 'ALL', label: 'ALL CLIENTS' }, { key: 'OWING', label: 'OWING' },",
          "        { key: 'RECEIVABLES', label: 'IN RECEIVABLES' }, { key: 'CRITICAL', label: 'CRITICAL' },",
          "        { key: 'PAID', label: 'PAID UP' }, { key: 'NOPLOTS', label: 'NO PROJECTS' },",
          "    ];",
          "",
      ]),
      "\n".join([
          "",
          "    const FILTERS = [",
          "        { key: 'ALL', label: 'ALL CLIENTS' }, { key: 'OWING', label: 'OWING' },",
          "        { key: 'RECEIVABLES', label: 'IN RECEIVABLES' }, { key: 'CRITICAL', label: 'CRITICAL', accent: 'red' },",
          "        { key: 'PAID', label: 'PAID UP' }, { key: 'NOPLOTS', label: 'NO PROJECTS' },",
          "    ];",
          "",
      ]),
      "ClientLedgerPage.jsx: change 2 of 3")

patch(CLIENTLEDGER_JSX,
      "\n".join([
          "                        {searchTerm && (<button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label=\"Clear search\" type=\"button\"><FiX aria-hidden=\"true\" /></button>)}",
          "                    </div>",
          "                </div>",
          "                <div className={styles.filterRail} role=\"group\" aria-label=\"Filter clients\">",
          "                    {FILTERS.map(f => (",
          "                        <button key={f.key} onClick={() => setActiveFilter(f.key)}",
          "                            className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}",
          "                            aria-pressed={activeFilter === f.key} aria-label={f.label}>{f.label}</button>",
          "                    ))}",
          "                </div>",
          "                <div className={styles.legendRow} aria-label=\"Legend\">",
          "                    {Object.entries(BADGE_COLORS).map(([k, c]) => (",
          "                        <span key={k} className={styles.legendItem}>",
      ]),
      "\n".join([
          "                        {searchTerm && (<button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label=\"Clear search\" type=\"button\"><FiX aria-hidden=\"true\" /></button>)}",
          "                    </div>",
          "                </div>",
          "                <TabDock items={FILTERS} value={activeFilter} onChange={setActiveFilter} label=\"Filter clients\" />",
          "                <div className={styles.legendRow} aria-label=\"Legend\">",
          "                    {Object.entries(BADGE_COLORS).map(([k, c]) => (",
          "                        <span key={k} className={styles.legendItem}>",
      ]),
      "ClientLedgerPage.jsx: change 3 of 3")

# ---- ClientLedgerPage.module.css ----
patch(CLIENTLEDGER_CSS,
      "\n".join([
          ".searchInput::placeholder{color:rgba(26,46,48,0.35);font-weight:500;}",
          ".searchInput::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none;}",
          ".searchClearBtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--orange);cursor:pointer;display:flex;}",
          ".filterRail{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;}",
          ".filterRail::-webkit-scrollbar{display:none;}",
          ".filterBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:8px 16px;border-radius:6px;font-weight:900;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;white-space:nowrap;transition:all .2s;}",
          ".filterBtn:hover{background:rgba(238,140,58,0.12);color:var(--orange);border-color:var(--orange);}",
          ".activeFilter{background:var(--orange) !important;color:#1a2e30 !important;border-color:var(--orange) !important;}",
          ".legendRow{display:flex;flex-wrap:nowrap;gap:14px;padding:4px 0 2px clamp(6px,1vw,12px);overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;margin-bottom:clamp(10px,1.2vw,14px);}",
          ".legendRow::-webkit-scrollbar{display:none;}",
          ".legendItem{display:flex;align-items:center;gap:6px;font-size:10px;font-weight:700;color:rgba(26,46,48,0.6);white-space:nowrap;flex-shrink:0;}",
      ]),
      "\n".join([
          ".searchInput::placeholder{color:rgba(26,46,48,0.35);font-weight:500;}",
          ".searchInput::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none;}",
          ".searchClearBtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--orange);cursor:pointer;display:flex;}",
          ".legendRow{display:flex;flex-wrap:nowrap;gap:14px;padding:4px 0 2px clamp(6px,1vw,12px);overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;margin-bottom:clamp(10px,1.2vw,14px);}",
          ".legendRow::-webkit-scrollbar{display:none;}",
          ".legendItem{display:flex;align-items:center;gap:6px;font-size:10px;font-weight:700;color:rgba(26,46,48,0.6);white-space:nowrap;flex-shrink:0;}",
      ]),
      "ClientLedgerPage.module.css: change 1 of 2")

patch(CLIENTLEDGER_CSS,
      "\n".join([
          "@media (max-width: 700px) {",
          "    .ledgerTable{min-width:640px;}",
          "    .ledgerTable thead th{font-size:7px;letter-spacing:1px;}",
          "    .filterBtn{padding:6px 10px;font-size:9px;letter-spacing:1px;}",
          "}",
      ]),
      "\n".join([
          "@media (max-width: 700px) {",
          "    .ledgerTable{min-width:640px;}",
          "    .ledgerTable thead th{font-size:7px;letter-spacing:1px;}",
          "}",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Tokens live in index.css (--page-pad-*, --hdr-pad, --block-gap,",
          "   --ctl-gap) so every list page spaces title bar -> controls -> table",
          "   the same way. Tabs/filters are the shared <TabDock/>. Kept at the",
          "   END of the file on purpose: last rule wins. */",
          ".container   { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); }",
          ".pageHeader  { padding: var(--hdr-pad); margin-bottom: var(--block-gap); }",
          ".controlHub  { padding: 0; gap: var(--ctl-gap); margin-bottom: var(--block-gap); }",
          ".searchBlock { padding: 0; }",
          ".legendRow   { margin: 0; padding: 0 0 0 4px; }",
      ]),
      "ClientLedgerPage.module.css: change 2 of 2")

# ---- ClientPortfolioPage.module.css ----
patch(PORTFOLIO_CSS,
      "\n".join([
          "  .headerActions { width: 100%; }",
          "  .backBtn { flex: 1; justify-content: center; }",
          "}",
      ]),
      "\n".join([
          "  .headerActions { width: 100%; }",
          "  .backBtn { flex: 1; justify-content: center; }",
          "}",
          "",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Tokens live in index.css. Last rule wins. */",
          ".container  { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); gap: var(--block-gap); }",
          ".pageHeader { padding: var(--hdr-pad); }",
          "",
          "/* title bar: same type scale and title/subtitle gap as every other page */",
          ".headerLeft { gap: 3px; }",
          ".title { line-height: normal; margin: 0; letter-spacing: 2px; }",
          "@media (min-width: 481px) {",
          "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
          "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
          "}",
      ]),
      "ClientPortfolioPage.module.css: change 1 of 1")

# ---- ExpensesPage.module.css ----
patch(EXPENSES_CSS,
      "\n".join([
          "  .ledgerTable tbody td { padding: 8px; }",
          "  .presetRow { gap: 6px; }",
          "}",
      ]),
      "\n".join([
          "  .ledgerTable tbody td { padding: 8px; }",
          "  .presetRow { gap: 6px; }",
          "}",
          "",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Tokens live in index.css. Last rule wins. */",
          ".container  { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); gap: var(--block-gap); }",
          ".pageHeader { padding: var(--hdr-pad); }",
          "",
          "/* title bar: same type scale and title/subtitle gap as every other page */",
          ".headerLeft { gap: 3px; }",
          ".title { line-height: normal; margin: 0; letter-spacing: 2px; }",
          "@media (min-width: 481px) {",
          "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
          "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
          "}",
      ]),
      "ExpensesPage.module.css: change 1 of 1")

# ---- LedgerPage.jsx ----
patch(LEDGER_JSX,
      "\n".join([
          "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';",
          "import styles from './LedgerPage.module.css';",
          "import { LoadingRow } from '../../components/common/LoadingState';",
          "",
          "const matchesSearch = (proj, term, stages) => {",
          "    if (!term) return true;",
      ]),
      "\n".join([
          "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';",
          "import styles from './LedgerPage.module.css';",
          "import { LoadingRow } from '../../components/common/LoadingState';",
          "import TabDock from '../../components/common/TabDock';",
          "",
          "const matchesSearch = (proj, term, stages) => {",
          "    if (!term) return true;",
      ]),
      "LedgerPage.jsx: change 1 of 3")

patch(LEDGER_JSX,
      "\n".join([
          "    const FILTERS = [",
          "        { key: 'ALL', label: 'ALL PROJECTS' }, { key: 'BACKLOG', label: 'PROCESSING' },",
          "        { key: 'TITLED', label: 'TITLED' }, { key: 'LEGACY', label: 'LEGACY' },",
          "        { key: 'RECEIVABLES', label: 'RECEIVABLES' }, { key: 'CRITICAL', label: 'CRITICAL' },",
          "        { key: 'PAID', label: 'PAID' }, { key: 'PROBLEM', label: 'PROBLEM' },",
          "    ];",
          "",
          "    return (",
      ]),
      "\n".join([
          "    const FILTERS = [",
          "        { key: 'ALL', label: 'ALL PROJECTS' }, { key: 'BACKLOG', label: 'PROCESSING' },",
          "        { key: 'TITLED', label: 'TITLED' }, { key: 'LEGACY', label: 'LEGACY' },",
          "        { key: 'RECEIVABLES', label: 'RECEIVABLES' }, { key: 'CRITICAL', label: 'CRITICAL', accent: 'red' },",
          "        { key: 'PAID', label: 'PAID' }, { key: 'PROBLEM', label: 'PROBLEM', accent: 'red' },",
          "    ];",
          "",
          "    return (",
      ]),
      "LedgerPage.jsx: change 2 of 3")

patch(LEDGER_JSX,
      "\n".join([
          "                        {searchTerm && (<button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label=\"Clear search\" type=\"button\"><FiX aria-hidden=\"true\" /></button>)}",
          "                    </div>",
          "                </div>",
          "                <div className={styles.filterRail} role=\"group\" aria-label=\"Filter records\">",
          "                    {FILTERS.map(f => (",
          "                        <button key={f.key} onClick={() => setActiveFilter(f.key)}",
          "                            className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}",
          "                            aria-pressed={activeFilter === f.key} aria-label={f.label}>{f.label}</button>",
          "                    ))}",
          "                </div>",
          "                <div className={styles.legendRow} aria-label=\"Payment health legend\">",
          "                    {Object.entries(BADGE_COLORS).map(([k, c]) => (",
          "                        <span key={k} className={styles.legendItem}>",
      ]),
      "\n".join([
          "                        {searchTerm && (<button className={styles.searchClearBtn} onClick={() => setSearchTerm('')} aria-label=\"Clear search\" type=\"button\"><FiX aria-hidden=\"true\" /></button>)}",
          "                    </div>",
          "                </div>",
          "                <TabDock items={FILTERS} value={activeFilter} onChange={setActiveFilter} label=\"Filter records\" />",
          "                <div className={styles.legendRow} aria-label=\"Payment health legend\">",
          "                    {Object.entries(BADGE_COLORS).map(([k, c]) => (",
          "                        <span key={k} className={styles.legendItem}>",
      ]),
      "LedgerPage.jsx: change 3 of 3")

# ---- LedgerPage.module.css ----
patch(LEDGER_CSS,
      "\n".join([
          ".searchInput::placeholder{color:rgba(26,46,48,0.35);font-weight:500;}",
          ".searchInput::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none;}",
          ".searchClearBtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--orange);cursor:pointer;display:flex;}",
          ".filterRail{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;}",
          ".filterRail::-webkit-scrollbar{display:none;}",
          ".filterBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:8px 16px;border-radius:6px;font-weight:900;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;white-space:nowrap;transition:all .2s;}",
          ".filterBtn:hover{background:rgba(238,140,58,0.12);color:var(--orange);border-color:var(--orange);}",
          ".activeFilter{background:var(--orange) !important;color:#1a2e30 !important;border-color:var(--orange) !important;}",
          "/* Legend row: stays on ONE line at every viewport width -- no wrap. If it",
          "   doesn't fit, it scrolls sideways instead (same pattern .filterRail",
          "   already uses), so a dot never gets separated from its label. */",
          ".legendRow{display:flex;flex-wrap:nowrap;gap:14px;padding:2px 0 0;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;}",
          ".legendRow::-webkit-scrollbar{display:none;}",
      ]),
      "\n".join([
          ".searchInput::placeholder{color:rgba(26,46,48,0.35);font-weight:500;}",
          ".searchInput::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none;}",
          ".searchClearBtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--orange);cursor:pointer;display:flex;}",
          "/* Legend row: stays on ONE line at every viewport width -- no wrap. If it",
          "   doesn't fit, it scrolls sideways instead (same pattern the old filter rail",
          "   already uses), so a dot never gets separated from its label. */",
          ".legendRow{display:flex;flex-wrap:nowrap;gap:14px;padding:2px 0 0;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;}",
          ".legendRow::-webkit-scrollbar{display:none;}",
      ]),
      "LedgerPage.module.css: change 1 of 2")

patch(LEDGER_CSS,
      "\n".join([
          ".legendRow { margin-bottom: clamp(10px, 1.2vw, 14px); }",
          "/* fix124: dot-definition legend sits a little inside, matching Recovery dotLegend indent */",
          ".legendRow { padding: 4px 0 2px clamp(6px, 1vw, 12px); }",
      ]),
      "\n".join([
          ".legendRow { margin-bottom: clamp(10px, 1.2vw, 14px); }",
          "/* fix124: dot-definition legend sits a little inside, matching Recovery dotLegend indent */",
          ".legendRow { padding: 4px 0 2px clamp(6px, 1vw, 12px); }",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Tokens live in index.css (--page-pad-*, --hdr-pad, --block-gap,",
          "   --ctl-gap) so every list page spaces title bar -> controls -> table",
          "   the same way. Tabs/filters are the shared <TabDock/>. Kept at the",
          "   END of the file on purpose: last rule wins. */",
          ".container   { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); }",
          ".pageHeader  { padding: var(--hdr-pad); margin-bottom: var(--block-gap); }",
          ".controlHub  { padding: 0; gap: var(--ctl-gap); margin-bottom: var(--block-gap); }",
          ".searchBlock { padding: 0; }",
          ".legendRow   { margin: 0; padding: 0 0 0 4px; }",
      ]),
      "LedgerPage.module.css: change 2 of 2")

# ---- PaymentsPage.jsx ----
patch(PAYMENTS_JSX,
      "\n".join([
          "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';",
          "import styles from './PaymentsPage.module.css';",
          "import { LoadingState } from '../../components/common/LoadingState';",
          "",
          "const fmt = (n) => Number(n || 0).toLocaleString();",
          "",
      ]),
      "\n".join([
          "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';",
          "import styles from './PaymentsPage.module.css';",
          "import { LoadingState } from '../../components/common/LoadingState';",
          "import TabDock from '../../components/common/TabDock';",
          "",
          "const fmt = (n) => Number(n || 0).toLocaleString();",
          "",
      ]),
      "PaymentsPage.jsx: change 1 of 3")

patch(PAYMENTS_JSX,
      "\n".join([
          "    RECEIVABLE_PARTIAL: '#ef4444',",
          "};",
          "",
          "const PaymentsPage = () => {",
          "    const navigate = useNavigate();",
          "    const [payments,   setPayments]   = useState([]);",
          "    const [loading,    setLoading]    = useState(true);",
          "    const [searchTerm, setSearchTerm] = useState('');",
          "    const [isSearchFocused, setIsSearchFocused] = useState(false);",
          "    const [typeFilter, setTypeFilter] = useState('ALL');",
          "    const [sortKey,    setSortKey]    = useState('date');",
          "    const [sortDir,    setSortDir]    = useState('desc');",
      ]),
      "\n".join([
          "    RECEIVABLE_PARTIAL: '#ef4444',",
          "};",
          "",
          "const TYPE_FILTERS = [",
          "    { key: 'ALL',                label: 'ALL TYPES' },",
          "    { key: 'STANDARD',           label: TYPE_LABELS.STANDARD.toUpperCase() },",
          "    { key: 'INITIAL_DEPOSIT',    label: TYPE_LABELS.INITIAL_DEPOSIT.toUpperCase() },",
          "    { key: 'RECEIVABLE_PARTIAL', label: TYPE_LABELS.RECEIVABLE_PARTIAL.toUpperCase(), accent: 'red' },",
          "];",
          "",
          "const PaymentsPage = () => {",
          "    const navigate = useNavigate();",
          "    const [payments,   setPayments]   = useState([]);",
          "    const [loading,    setLoading]    = useState(true);",
          "    const [searchTerm, setSearchTerm] = useState('');",
          "    const [typeFilter, setTypeFilter] = useState('ALL');",
          "    const [sortKey,    setSortKey]    = useState('date');",
          "    const [sortDir,    setSortDir]    = useState('desc');",
      ]),
      "PaymentsPage.jsx: change 2 of 3")

patch(PAYMENTS_JSX,
      "\n".join([
          "                </div>",
          "            </div>",
          "",
          "            <div className={styles.controls}>",
          "                <div className={styles.searchWrap}>",
          "                    {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} />}",
          "                    <input type=\"search\"",
          "                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}",
          "                        placeholder=\"Search plot ID, owner name, recorded by...\"",
          "                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)}",
          "                        onFocus={() => setIsSearchFocused(true)}",
          "                        onBlur={() => setIsSearchFocused(false)} />",
          "                    {searchTerm && (",
          "                        <button className={styles.clearBtn} onClick={() => setSearchTerm('')}>",
          "                            <FiX size={14} />",
          "                        </button>",
          "                    )}",
          "                </div>",
          "                <div className={styles.filterRow}>",
          "                    {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'RECEIVABLE_PARTIAL'].map(t => (",
          "                        <button key={t}",
          "                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}",
          "                            onClick={() => setTypeFilter(t)}>",
          "                            {t === 'ALL' ? 'ALL TYPES' : TYPE_LABELS[t]}",
          "                        </button>",
          "                    ))}",
          "                </div>",
          "            </div>",
          "",
          "            {loading ? (",
      ]),
      "\n".join([
          "                </div>",
          "            </div>",
          "",
          "            {/* Control cluster -- same structure as the Ledger and Clients pages:",
          "                search, then the shared TabDock. Only the search bar is sticky. */}",
          "            <div className={styles.controlHub}>",
          "                <div className={styles.searchBlock}>",
          "                    <div className={styles.searchWrap}>",
          "                        <input type=\"search\"",
          "                            className={styles.searchInput}",
          "                            placeholder=\"Search plot ID, owner name, recorded by...\"",
          "                            aria-label=\"Search payment records\" autoComplete=\"off\"",
          "                            value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />",
          "                        <FiSearch className={styles.searchIcon} aria-hidden=\"true\" />",
          "                        {searchTerm && (",
          "                            <button type=\"button\" className={styles.clearBtn} onClick={() => setSearchTerm('')} aria-label=\"Clear search\">",
          "                                <FiX size={14} />",
          "                            </button>",
          "                        )}",
          "                    </div>",
          "                </div>",
          "                <TabDock items={TYPE_FILTERS} value={typeFilter} onChange={setTypeFilter} label=\"Filter by payment type\" />",
          "            </div>",
          "",
          "            {loading ? (",
      ]),
      "PaymentsPage.jsx: change 3 of 3")

# ---- PaymentsPage.module.css ----
patch(PAYMENTS_CSS,
      "\n".join([
          ".sumCard strong { font-family: 'Space Mono', monospace; font-size: var(--stat-value); color: #fff; font-weight: 700; word-break: break-all; }",
          ".sumCard span { font-size: var(--stat-note); color: rgba(255,255,255,0.35); }",
          "",
          "/* CONTROLS */",
          ".controls {",
          "    display: flex;",
          "    flex-direction: column;",
          "    gap: var(--gap-md);",
          "    margin-bottom: clamp(14px, 2vw, 20px);",
          "    flex-shrink: 0;",
          "    position: sticky;",
          "    top: 0;",
          "    z-index: 200;",
          "    background: transparent;",
          "    padding: clamp(8px, 1vw, 12px) 0;",
          "    margin-left: clamp(-12px, -2vw, -24px);",
          "    margin-right: clamp(-12px, -2vw, -24px);",
          "    padding-left: clamp(12px, 2vw, 24px);",
          "    padding-right: clamp(12px, 2vw, 24px);",
          "}",
          "",
          ".searchWrap {",
          "    position: relative;",
          "    display: flex;",
      ]),
      "\n".join([
          ".sumCard strong { font-family: 'Space Mono', monospace; font-size: var(--stat-value); color: #fff; font-weight: 700; word-break: break-all; }",
          ".sumCard span { font-size: var(--stat-note); color: rgba(255,255,255,0.35); }",
          "",
          ".searchWrap {",
          "    position: relative;",
          "    display: flex;",
      ]),
      "PaymentsPage.module.css: change 1 of 5")

patch(PAYMENTS_CSS,
      "\n".join([
          "    height: 100%;",
          "    transition: padding 0.2s ease;",
          "}",
          ".searchInputActive { padding-left: 14px !important; }",
          ".searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }",
          ".clearBtn {",
          "    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);",
      ]),
      "\n".join([
          "    height: 100%;",
          "    transition: padding 0.2s ease;",
          "}",
          ".searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }",
          ".clearBtn {",
          "    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);",
      ]),
      "PaymentsPage.module.css: change 2 of 5")

patch(PAYMENTS_CSS,
      "\n".join([
          "}",
          ".clearBtn:hover { color: #1a2e30; background: rgba(26,46,48,0.08); }",
          "",
          "/* FILTER ROW */",
          ".filterRow {",
          "    display: flex;",
          "    flex-wrap: nowrap;",
          "    overflow-x: auto;",
          "    gap: clamp(6px, 1vw, 10px);",
          "    padding-bottom: 4px;",
          "    scrollbar-width: none;",
          "}",
          ".filterRow::-webkit-scrollbar { display: none; }",
          "",
          ".filterBtn {",
          "    background: rgba(26, 46, 48, 0.75);",
          "    border: 1.5px solid rgba(255, 255, 255, 0.18);",
          "    color: rgba(255, 255, 255, 0.85);",
          "    padding: clamp(7px, 0.9vw, 9px) clamp(12px, 1.5vw, 18px);",
          "    border-radius: var(--radius-sm);",
          "    font-family: 'DM Sans', sans-serif;",
          "    font-weight: 900;",
          "    font-size: clamp(9px, 0.95vw, 11px);",
          "    letter-spacing: 1.5px;",
          "    text-transform: uppercase;",
          "    cursor: pointer;",
          "    transition: all 0.2s ease;",
          "    display: inline-flex;",
          "    align-items: center;",
          "    gap: 5px;",
          "    white-space: nowrap;",
          "    flex-shrink: 0;",
          "}",
          ".filterBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }",
          ".filterActive {",
          "    background: #EE8C3A !important;",
          "    color: #1a2e30 !important;",
          "    border-color: #EE8C3A !important;",
          "    box-shadow: 0 0 12px rgba(238, 140, 58, 0.35);",
          "}",
          "",
          "/* TABLE SHELL */",
          ".tableScroll {",
      ]),
      "\n".join([
          "}",
          ".clearBtn:hover { color: #1a2e30; background: rgba(26,46,48,0.08); }",
          "",
          "",
          "",
          "/* TABLE SHELL */",
          ".tableScroll {",
      ]),
      "PaymentsPage.module.css: change 3 of 5")

patch(PAYMENTS_CSS,
      "\n".join([
          "    .pageHeader {",
          "        border-radius: 0;",
          "    }",
          "    .controls {",
          "        margin-left: 0;",
          "        margin-right: 0;",
          "        padding-left: clamp(8px, 2vw, 12px);",
          "        padding-right: clamp(8px, 2vw, 12px);",
          "    }",
          "    .summaryRow {",
          "        grid-template-columns: 1fr;",
          "        gap: 8px;",
          "        padding: 0 clamp(8px, 2vw, 12px);",
          "    }",
          "    .searchWrap { max-width: 100%; }",
          "    .filterRow { gap: 6px; }",
          "    .tableScroll { margin: 0; border-radius: 0; }",
          "    .ledgerTable { min-width: 650px; }",
          "}",
      ]),
      "\n".join([
          "    .pageHeader {",
          "        border-radius: 0;",
          "    }",
          "    .summaryRow {",
          "        grid-template-columns: 1fr;",
          "        gap: 8px;",
          "        padding: 0 clamp(8px, 2vw, 12px);",
          "    }",
          "    .searchWrap { max-width: 100%; }",
          "    .tableScroll { margin: 0; border-radius: 0; }",
          "    .ledgerTable { min-width: 650px; }",
          "}",
      ]),
      "PaymentsPage.module.css: change 4 of 5")

patch(PAYMENTS_CSS,
      "\n".join([
          "    .ledgerTable { min-width: 600px; }",
          "    .ledgerTable th { font-size: 7px; letter-spacing: 1px; }",
          "    .ledgerTable td { padding: 8px; }",
          "    .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }",
          "}",
      ]),
      "\n".join([
          "    .ledgerTable { min-width: 600px; }",
          "    .ledgerTable th { font-size: 7px; letter-spacing: 1px; }",
          "    .ledgerTable td { padding: 8px; }",
          "}",
          "",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Payments used its own, roomier numbers (bigger title-bar padding, bigger",
          "   gaps, full-bleed phone layout, a sticky filter block with negative",
          "   margins). It now reads the same tokens as Ledger and Clients, so the",
          "   title bar -> stat cards -> search -> tabs -> table spacing matches.",
          "   Kept at the END of the file on purpose: last rule wins. */",
          ".container   { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); }",
          ".pageHeader  { padding: var(--hdr-pad); margin-bottom: var(--block-gap); }",
          ".summaryRow  { gap: var(--block-gap); margin-bottom: var(--block-gap); }",
          "",
          ".controlHub  { display: flex; flex-direction: column; gap: var(--ctl-gap); margin-bottom: var(--block-gap); }",
          "/* Search: identical to the Ledger search (sticky, same width, same type). */",
          ".searchBlock { position: sticky; top: 0; z-index: 30; width: min(100%, clamp(220px, 38vw, 420px)); }",
          ".searchWrap  { max-width: none; width: 100%; height: clamp(36px, 4.5vw, 44px); }",
          ".searchIcon  { left: 12px; font-size: 16px; }",
          ".searchInput {",
          "    font-family: 'Inter', sans-serif; font-weight: 600; font-size: 12px;",
          "    padding: 0 34px 0 41px !important;",
          "}",
          ".searchInput::placeholder { color: rgba(26, 46, 48, 0.35); }",
          "",
          "@media (max-width: 640px) {",
          "    .container  { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); }",
          "    .pageHeader { border-radius: 0 12px 12px 0; }",
          "    .summaryRow { padding: 0; gap: var(--block-gap); }",
          "}",
          "@media (max-width: 480px) {",
          "    .container  { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); }",
          "    .summaryRow { padding: 0; }",
          "}",
          "",
          "/* index.css has a global [class*=\"searchInput\"] { text-indent: 26px !important }",
          "   that stacks on top of the padding above and pushed the placeholder far from",
          "   its icon. The padding already clears the icon, so cancel the indent here. */",
          ".searchWrap .searchInput { text-indent: 0 !important; }",
          "",
          ".title { line-height: normal; }",
          "",
          "/* title bar: same type scale and title/subtitle gap as every other page */",
          ".headerLeft { gap: 3px; }",
          ".title { line-height: normal; margin: 0; letter-spacing: 2px; }",
          "@media (min-width: 481px) {",
          "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
          "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
          "}",
      ]),
      "PaymentsPage.module.css: change 5 of 5")

# ---- RecoveryPortal.jsx ----
patch(RECOVERY_JSX,
      "\n".join([
          "import styles from './RecoveryPortal.module.css';",
          "import { LoadingState } from '../../components/common/LoadingState';",
          "import modalStyles from '../../components/common/HardwareModal.module.css';",
          "const TABS = [",
          "  { key: 'ALL', label: 'ALL DUE' },",
          "  { key: 'CONTACTED', label: 'CONTACTED' },",
      ]),
      "\n".join([
          "import styles from './RecoveryPortal.module.css';",
          "import { LoadingState } from '../../components/common/LoadingState';",
          "import modalStyles from '../../components/common/HardwareModal.module.css';",
          "import TabDock from '../../components/common/TabDock';",
          "const TABS = [",
          "  { key: 'ALL', label: 'ALL DUE' },",
          "  { key: 'CONTACTED', label: 'CONTACTED' },",
      ]),
      "RecoveryPortal.jsx: change 1 of 2")

patch(RECOVERY_JSX,
      "\n".join([
          "        <div className={styles.countCard}><label>MONTH'S MISS</label><strong>{stats ? stats.missMonth : '-'}</strong></div>",
          "      </div>",
          "      <div className={styles.stickyRail}>",
          "      <div className={styles.stickyTabs} role=\"tablist\" aria-label=\"Recovery queues\">",
          "        <div className={styles.tabSearch}>",
          "          <FiSearch className={styles.searchIcon} aria-hidden=\"true\" />",
          "          <input type=\"search\" className={styles.searchInput} placeholder=\"Search name, NIN, phone, index, location...\" value={search} onChange={(e) => setSearch(e.target.value)} aria-label=\"Search recovery queue\" autoComplete=\"off\" />",
          "          {search && (<button type=\"button\" className={styles.searchClearBtn} onClick={() => setSearch('')} aria-label=\"Clear search\"><FiX aria-hidden=\"true\" /></button>)}",
          "        </div>",
          "        <div className={styles.tabRow}>",
          "          {TABS.map((t) => (",
          "            <button key={t.key} role=\"tab\" aria-selected={tab === t.key} className={`${styles.qTab} ${tab === t.key ? styles.qTabActive : ''}`} onClick={() => setTab(t.key)}>",
          "              {t.label} ({counts ? counts[t.key] : '-'})",
          "            </button>",
          "          ))}",
          "        </div>",
          "      </div>",
          "      </div>",
          "      <div className={styles.dotLegend} aria-label=\"Payment dot legend\">",
      ]),
      "\n".join([
          "        <div className={styles.countCard}><label>MONTH'S MISS</label><strong>{stats ? stats.missMonth : '-'}</strong></div>",
          "      </div>",
          "      <div className={styles.stickyRail}>",
          "      <div className={styles.stickyTabs}>",
          "        <div className={styles.tabSearch}>",
          "          <FiSearch className={styles.searchIcon} aria-hidden=\"true\" />",
          "          <input type=\"search\" className={styles.searchInput} placeholder=\"Search name, NIN, phone, index, location...\" value={search} onChange={(e) => setSearch(e.target.value)} aria-label=\"Search recovery queue\" autoComplete=\"off\" />",
          "          {search && (<button type=\"button\" className={styles.searchClearBtn} onClick={() => setSearch('')} aria-label=\"Clear search\"><FiX aria-hidden=\"true\" /></button>)}",
          "        </div>",
          "        <TabDock",
          "          className={styles.dockSlot} mode=\"tab\" label=\"Recovery queues\"",
          "          items={TABS.map((t) => ({ key: t.key, label: t.label, count: counts ? counts[t.key] : '-' }))}",
          "          value={tab} onChange={setTab}",
          "        />",
          "      </div>",
          "      </div>",
          "      <div className={styles.dotLegend} aria-label=\"Payment dot legend\">",
      ]),
      "RecoveryPortal.jsx: change 2 of 2")

# ---- RecoveryPortal.module.css ----
patch(RECOVERY_CSS,
      "\n".join([
          ".searchInput::-webkit-search-cancel-button { -webkit-appearance: none; appearance: none; }",
          ".searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--orange); cursor: pointer; display: flex; padding: 4px; border-radius: 4px; }",
          ".searchClearBtn:hover { background: rgba(238,140,58,0.15); }",
          ".filterRail { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; }",
          ".filterRail::-webkit-scrollbar { display: none; }",
          ".filterBtn { background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 8px 16px; border-radius: 6px; font-weight: 900; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; white-space: nowrap; transition: all .2s; font-family: 'Inter',sans-serif; }",
          ".filterBtn:hover { background: rgba(238,140,58,0.12); color: var(--orange); border-color: var(--orange); }",
          ".activeFilter { background: var(--orange) !important; color: #1a2e30 !important; border-color: var(--orange) !important; }",
          ".filterBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }",
          "",
          "/* cards */",
          ".grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(300px,1fr)); gap: clamp(10px,1.4vw,16px); }",
      ]),
      "\n".join([
          ".searchInput::-webkit-search-cancel-button { -webkit-appearance: none; appearance: none; }",
          ".searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--orange); cursor: pointer; display: flex; padding: 4px; border-radius: 4px; }",
          ".searchClearBtn:hover { background: rgba(238,140,58,0.15); }",
          "",
          "/* cards */",
          ".grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(300px,1fr)); gap: clamp(10px,1.4vw,16px); }",
      ]),
      "RecoveryPortal.module.css: change 1 of 8")

patch(RECOVERY_CSS,
      "\n".join([
          "",
          ".stickyTabs { position: sticky; top: 0; z-index: 200; display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding: 10px clamp(12px, 2vw, 24px); background: #f4efe8; margin-left: clamp(-12px, -2vw, -24px); margin-right: clamp(-12px, -2vw, -24px); border-bottom: 1px solid rgba(26, 46, 48, 0.08); }",
          ".stickyTabs::-webkit-scrollbar { display: none; }",
          ".qTab { background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 8px 14px; border-radius: 6px; font-weight: 900; font-size: 10px; letter-spacing: 1.5px; cursor: pointer; white-space: nowrap; font-family: 'Inter',sans-serif; }",
          ".qTabActive { background: var(--orange) !important; color: #1a2e30 !important; border-color: var(--orange) !important; }",
          ".qTab:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }",
          ".list { display: flex; flex-direction: column; gap: 8px; }",
          ".rowCard { background: linear-gradient(160deg, #1c3335, #213E40); border: 1.5px solid rgba(255,255,255,0.12); border-radius: 10px; overflow: hidden; }",
          ".rowOpen { border-color: var(--orange); }",
      ]),
      "\n".join([
          "",
          ".stickyTabs { position: sticky; top: 0; z-index: 200; display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding: 10px clamp(12px, 2vw, 24px); background: #f4efe8; margin-left: clamp(-12px, -2vw, -24px); margin-right: clamp(-12px, -2vw, -24px); border-bottom: 1px solid rgba(26, 46, 48, 0.08); }",
          ".stickyTabs::-webkit-scrollbar { display: none; }",
          ".list { display: flex; flex-direction: column; gap: 8px; }",
          ".rowCard { background: linear-gradient(160deg, #1c3335, #213E40); border: 1.5px solid rgba(255,255,255,0.12); border-radius: 10px; overflow: hidden; }",
          ".rowOpen { border-color: var(--orange); }",
      ]),
      "RecoveryPortal.module.css: change 2 of 8")

patch(RECOVERY_CSS,
      "\n".join([
          "/* fix82: unified type scale - 3 text sizes + HUD display number only */",
          ".cname { font-size: clamp(13px, 1.6vw, 16px); }",
          ".nin, .mono, .loc, .coLine, .attemptLine, .histText, .lockBanner, .projLink { font-size: clamp(10px, 1.1vw, 12px); }",
          ".callPos, .reason, .dayChip, .chipPos, .chipNeg, .chipNone, .wallLabel, .histMeta, .qTab, .countCard label { font-size: clamp(8px, 0.9vw, 10px); }",
          ".countCard strong { font-size: clamp(15px, 1.8vw, 21px); }",
          "",
          "/* fix83: standard search width, transparent sticky bar, boxed scrolling list, Ledger type scale */",
      ]),
      "\n".join([
          "/* fix82: unified type scale - 3 text sizes + HUD display number only */",
          ".cname { font-size: clamp(13px, 1.6vw, 16px); }",
          ".nin, .mono, .loc, .coLine, .attemptLine, .histText, .lockBanner, .projLink { font-size: clamp(10px, 1.1vw, 12px); }",
          ".callPos, .reason, .dayChip, .chipPos, .chipNeg, .chipNone, .wallLabel, .histMeta, .countCard label { font-size: clamp(8px, 0.9vw, 10px); }",
          ".countCard strong { font-size: clamp(15px, 1.8vw, 21px); }",
          "",
          "/* fix83: standard search width, transparent sticky bar, boxed scrolling list, Ledger type scale */",
      ]),
      "RecoveryPortal.module.css: change 3 of 8")

patch(RECOVERY_CSS,
      "\n".join([
          ".list::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.5); border-radius: 4px; }",
          ".refreshing { opacity: 0.55; }",
          ".dotLegend span { font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: rgba(26,46,48,0.65); }",
          ".qTab { font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; }",
          ".countCard label { font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px); letter-spacing: 1px; }",
          ".countCard strong { font-family: 'Space Mono', monospace; font-size: clamp(15px, 1.8vw, 21px); }",
          ".cname { font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(13px, 1.6vw, 16px); letter-spacing: 0.3px; }",
      ]),
      "\n".join([
          ".list::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.5); border-radius: 4px; }",
          ".refreshing { opacity: 0.55; }",
          ".dotLegend span { font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: rgba(26,46,48,0.65); }",
          ".countCard label { font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px); letter-spacing: 1px; }",
          ".countCard strong { font-family: 'Space Mono', monospace; font-size: clamp(15px, 1.8vw, 21px); }",
          ".cname { font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(13px, 1.6vw, 16px); letter-spacing: 0.3px; }",
      ]),
      "RecoveryPortal.module.css: change 4 of 8")

patch(RECOVERY_CSS,
      "\n".join([
          ".tabSearch .searchInput { width: 100%; padding: 8px 30px; border-radius: 6px; border: 1.5px solid rgba(26, 46, 48, 0.15); background: #ffffff; font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 600; color: #1a2e30; }",
          ".tabSearch .searchInput:focus { outline: 2px solid var(--orange); outline-offset: 1px; border-color: var(--orange); }",
          ".tabSearch .searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgba(26, 46, 48, 0.4); cursor: pointer; }",
          ".qTab { padding: 8px 14px; border-radius: 6px; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; }",
          ".qTab:hover { background: rgba(238, 140, 58, 0.12); color: var(--orange); border-color: var(--orange); transform: none; }",
          ".dotLegend { padding: 4px 2px 6px; gap: 14px; }",
          ".dotLegend span { gap: 6px; font-size: 10px; font-weight: 700; letter-spacing: normal; color: rgba(26, 46, 48, 0.6); }",
          ".dotLegend i { box-shadow: none !important; width: 8px; height: 8px; }",
      ]),
      "\n".join([
          ".tabSearch .searchInput { width: 100%; padding: 8px 30px; border-radius: 6px; border: 1.5px solid rgba(26, 46, 48, 0.15); background: #ffffff; font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 600; color: #1a2e30; }",
          ".tabSearch .searchInput:focus { outline: 2px solid var(--orange); outline-offset: 1px; border-color: var(--orange); }",
          ".tabSearch .searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgba(26, 46, 48, 0.4); cursor: pointer; }",
          ".dotLegend { padding: 4px 2px 6px; gap: 14px; }",
          ".dotLegend span { gap: 6px; font-size: 10px; font-weight: 700; letter-spacing: normal; color: rgba(26, 46, 48, 0.6); }",
          ".dotLegend i { box-shadow: none !important; width: 8px; height: 8px; }",
      ]),
      "RecoveryPortal.module.css: change 5 of 8")

patch(RECOVERY_CSS,
      "\n".join([
          ".tabSearch .searchInput { width: 100%; padding: 8px 30px; border-radius: 6px; border: 1.5px solid rgba(26, 46, 48, 0.15); background: #ffffff; font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 600; color: #1a2e30; }",
          ".tabSearch .searchInput:focus { outline: 2px solid var(--orange); outline-offset: 1px; border-color: var(--orange); }",
          ".tabSearch .searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgba(26, 46, 48, 0.4); cursor: pointer; }",
          ".qTab { padding: 8px 14px; border-radius: 6px; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; }",
          ".dotLegend { padding: 4px 2px 6px; gap: 14px; }",
          ".dotLegend span { gap: 6px; font-size: 10px; font-weight: 700; letter-spacing: normal; text-transform: none; color: rgba(26, 46, 48, 0.6); }",
          ".dotLegend i { width: 8px; height: 8px; box-shadow: none !important; }",
      ]),
      "\n".join([
          ".tabSearch .searchInput { width: 100%; padding: 8px 30px; border-radius: 6px; border: 1.5px solid rgba(26, 46, 48, 0.15); background: #ffffff; font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 600; color: #1a2e30; }",
          ".tabSearch .searchInput:focus { outline: 2px solid var(--orange); outline-offset: 1px; border-color: var(--orange); }",
          ".tabSearch .searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgba(26, 46, 48, 0.4); cursor: pointer; }",
          ".dotLegend { padding: 4px 2px 6px; gap: 14px; }",
          ".dotLegend span { gap: 6px; font-size: 10px; font-weight: 700; letter-spacing: normal; text-transform: none; color: rgba(26, 46, 48, 0.6); }",
          ".dotLegend i { width: 8px; height: 8px; box-shadow: none !important; }",
      ]),
      "RecoveryPortal.module.css: change 6 of 8")

patch(RECOVERY_CSS,
      "\n".join([
          ".dotLegend::-webkit-scrollbar { display: none; }",
          ".dotLegend span { white-space: nowrap; flex-shrink: 0; }",
          "/* pill row scrolls horizontally inside the rail */",
          ".tabRow { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; flex: 1 1 auto; min-width: 0; }",
          ".tabRow::-webkit-scrollbar { display: none; }",
          "/* mobile: search on its own line, filters on their own line */",
          "@media (max-width: 640px) {",
          "  .stickyTabs { flex-direction: column; align-items: stretch; gap: 6px; }",
          "  .tabSearch { width: 100%; margin-right: 0; flex: none; }",
          "  .tabRow { width: 100%; flex: none; }",
          "  .countsHUD { grid-template-columns: repeat(2, 1fr); }",
          "  .rowHead { flex-wrap: wrap; gap: 6px 8px; }",
          "  .rowBody { grid-template-columns: 1fr; }",
      ]),
      "\n".join([
          ".dotLegend::-webkit-scrollbar { display: none; }",
          ".dotLegend span { white-space: nowrap; flex-shrink: 0; }",
          "/* pill row scrolls horizontally inside the rail */",
          "/* mobile: search on its own line, filters on their own line */",
          "@media (max-width: 640px) {",
          "  .stickyTabs { flex-direction: column; align-items: stretch; gap: 6px; }",
          "  .tabSearch { width: 100%; margin-right: 0; flex: none; }",
          "  .countsHUD { grid-template-columns: repeat(2, 1fr); }",
          "  .rowHead { flex-wrap: wrap; gap: 6px 8px; }",
          "  .rowBody { grid-template-columns: 1fr; }",
      ]),
      "RecoveryPortal.module.css: change 7 of 8")

patch(RECOVERY_CSS,
      "\n".join([
          "   source order. */",
          ".countCard label  { font-size: var(--stat-label); }",
          ".countCard strong { font-size: var(--stat-value); }",
      ]),
      "\n".join([
          "   source order. */",
          ".countCard label  { font-size: var(--stat-label); }",
          ".countCard strong { font-size: var(--stat-value); }",
          "",
          "",
          "/* ══ DESIGN PASS: shared page rhythm + TabDock ═════════════════════",
          "   Recovery's title -> counters -> tabs -> legend gaps had been squeezed",
          "   to 4-8px (fix102-104), so this page felt tighter than Ledger and",
          "   Clients. Same tokens as every other list page now. The queue tabs are",
          "   the shared <TabDock/> (Settings tab-bar spec). Last rule wins. */",
          ".container   { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); gap: var(--block-gap); }",
          ".pageHeader  { padding: var(--hdr-pad); margin: 0; }",
          ".countsHUD   { margin: 0; }",
          ".stickyRail  { margin: 0; padding: 0; }",
          ".stickyTabs  { padding: 0 !important; margin: 0 !important; gap: var(--ctl-gap); align-items: center; }",
          ".dockSlot    { flex: 1 1 auto; min-width: 0; }",
          ".dotLegend   { margin: calc(var(--ctl-gap) - var(--block-gap)) 0 0; padding: 0 0 0 4px; }",
          ".list        { margin: 0; }",
          "",
          "/* Search: identical to the Ledger search box */",
          ".tabSearch { width: clamp(220px, 38vw, 420px); margin-right: 0; }",
          ".tabSearch .searchIcon { left: 12px; width: 16px; height: 16px; color: var(--orange); }",
          ".tabSearch .searchInput {",
          "    height: clamp(36px, 4.5vw, 44px) !important; padding: 0 34px 0 41px !important; border: 1.5px solid #c8d6d7;",
          "    font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; color: #1a2e30;",
          "}",
          ".tabSearch .searchInput::placeholder { color: rgba(26, 46, 48, 0.35); font-weight: 500; }",
          ".tabSearch .searchInput:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.18); }",
          ".tabSearch .searchClearBtn { color: var(--orange); }",
          "",
          "@media (max-width: 640px) {",
          "    .stickyTabs { flex-direction: column; align-items: stretch; gap: var(--ctl-gap); }",
          "    .tabSearch  { width: 100%; }",
          "    .dockSlot   { flex: none; width: 100%; }",
          "}",
          "",
          "/* cancel the global [class*=\"searchInput\"] text-indent (see index.css) -- the",
          "   41px left padding above already clears the icon */",
          ".tabSearch .searchInput { text-indent: 0 !important; }",
          "",
          "/* title block: same 3px title/subtitle gap and line-height as the other pages */",
          ".pageHeader .headerLeft { gap: 3px; }",
          ".pageHeader .title { line-height: normal; }",
          "",
          "/* title bar: same type scale and title/subtitle gap as every other page */",
          ".pageHeader .headerLeft { gap: 3px; }",
          ".pageHeader .title { line-height: normal; margin: 0; letter-spacing: 2px; }",
          "@media (min-width: 481px) {",
          "    .pageHeader .title { font-size: clamp(18px, 2.5vw, 24px); }",
          "    .pageHeader .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
          "}",
      ]),
      "RecoveryPortal.module.css: change 8 of 8")

# ---- ReportHub.module.css ----
patch(REPORTHUB_CSS,
      "\n".join([
          "}",
          ".libChip:hover:not(:disabled) { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }",
          ".libChip:disabled { opacity: 0.45; cursor: wait; }",
      ]),
      "\n".join([
          "}",
          ".libChip:hover:not(:disabled) { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }",
          ".libChip:disabled { opacity: 0.45; cursor: wait; }",
          "",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Tokens live in index.css. Last rule wins. */",
          ".pageHeader { padding: var(--hdr-pad); margin-bottom: var(--block-gap); }",
          "@media (min-width: 641px) {",
          "    .container { padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom); }",
          "}",
          "",
          "/* title bar: same type scale and title/subtitle gap as every other page */",
          ".headerLeft { gap: 3px; }",
          ".title { line-height: normal; margin: 0; letter-spacing: 2px; }",
          "@media (min-width: 481px) {",
          "    .title { font-size: clamp(18px, 2.5vw, 24px); }",
          "    .subtitle   { font-size: clamp(9px, 0.9vw, 11px); }",
          "}",
      ]),
      "ReportHub.module.css: change 1 of 1")

# ---- SettingsPage.module.css ----
patch(SETTINGS_CSS,
      "\n".join([
          "    .commitBtn     { padding: 8px 14px; font-size: 8px; letter-spacing: 0.5px; }",
          "    .eyeBtn        { font-size: 13px; right: 8px; top: clamp(24px, 6vw, 30px); }",
          "}",
      ]),
      "\n".join([
          "    .commitBtn     { padding: 8px 14px; font-size: 8px; letter-spacing: 0.5px; }",
          "    .eyeBtn        { font-size: 13px; right: 8px; top: clamp(24px, 6vw, 30px); }",
          "}",
          "",
          "",
          "/* ══ DESIGN PASS: shared page rhythm ═══════════════════════════════",
          "   Settings is the reference for the tab dock; it now also shares the",
          "   page rhythm (title bar size, gaps, top offset) with the list pages. */",
          ".pageHeader { padding: var(--hdr-pad); margin-bottom: var(--block-gap); }",
          ".pageHeaderLeft { gap: 3px; }",
          ".title { line-height: normal; margin: 0; letter-spacing: 2px; }",
          "@media (min-width: 481px) {",
          "    .title    { font-size: clamp(18px, 2.5vw, 24px); }",
          "    .subtitle { font-size: clamp(9px, 0.9vw, 11px); }",
          "}",
          "@media (min-width: 641px) {",
          "    .container { padding-top: var(--page-pad-top); padding-left: var(--page-pad-x); padding-right: var(--page-pad-x); }",
          "}",
      ]),
      "SettingsPage.module.css: change 1 of 1")

# ---- guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix144: seed load fixed, Section 19)",
      "# Last updated: September 2026 (fix145: design pass -- TabDock + page rhythm, Section 7)",
      "guide: last-updated line")

patch(GUIDE,
      "### Filter Button Style (CONFIRMED STANDARD -- ALL pages)\n",
      "\n".join([
          "### Filter Button Style (CONFIRMED STANDARD -- ALL pages)",
          "> **fix145: filters and tabs are now ONE shared component, `src/components/common/TabDock.jsx`.** Ledger, Clients, Payments and Recovery all render it. Do NOT hand-roll filter or tab buttons on a page (no per-page `.filterBtn` / `.qTab`); import `TabDock` instead. It is the Settings-page tab bar turned into a component: one dark tray (`#4d5c5a`, radius 8px, padding 6px), pill buttons inside it, no box of their own until active, the active pill solid accent colour with navy text. Props: `items [{ key, label, count?, icon?, accent?, title? }]`, `value`, `onChange(key)`, `mode` (`'filter'` = aria-pressed buttons, default; `'tab'` = role=tablist), `label` (accessible name), `end` (optional node after the tray), `className`. Per-item `accent` is `orange` (default) | `red` | `green` | `yellow` | `cyan`; use `accent: 'red'` for danger filters (CRITICAL, PROBLEM). Colours and sizes live only in `TabDock.module.css`; change them there and every page follows. The older list below is the historic spec for the look; where it says text-only, TabDock now allows an optional icon.",
          "",
      ]) + "\n",
      "guide: Section 7 -- TabDock replaces hand-rolled filter buttons")

patch(GUIDE,
      "### Table Design Standard\n",
      "\n".join([
          "### Page Rhythm (fix145) -- ONE spacing scale for every list page",
          "The stack every list page shares is: page title bar -> stat cards -> search -> tabs/filters -> table. Its spacing comes from CSS variables at the top of `src/index.css`, so no page invents its own numbers:",
          "```",
          "--page-pad-top:    clamp(12px, 2vh, 22px)      /* content to top of screen */",
          "--page-pad-x:      clamp(12px, 2vw, 24px)      /* content to left/right edge */",
          "--page-pad-bottom: 28px",
          "--hdr-pad:         clamp(8px, 1.2vw, 14px) clamp(14px, 1.8vw, 22px)   /* inside the title bar */",
          "--block-gap:       clamp(10px, 1.5vh, 16px)    /* between two stacked blocks */",
          "--ctl-gap:         10px                        /* inside the search / tabs / legend cluster */",
          "```",
          "Ledger, Clients, Recovery and Expenses already used these numbers; Payments, Audit and Reports had drifted roomier and now read from the same variables. When adding a list page, use the variables (`padding: var(--page-pad-top) var(--page-pad-x) var(--page-pad-bottom)`, `gap: var(--block-gap)`), do not type new pixel values. Change a number once in `index.css` and every page moves.",
          "",
          "### Table Design Standard",
      ]) + "\n",
      "guide: Section 7 -- page rhythm variables")
# ============================= EDIT PART 2 END =============================

# ================= DO NOT EDIT: gates, rollback, git (copy exactly) ========
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since the last fix).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True

if not changed:
    print("note: nothing changed -- " + FIX_NO + " already applied")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed and RUN_GATES:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate ----
if changed and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif changed:
    print("note: RUN_GATES is False (docs-only fix) -- compile and build skipped")


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

if not changed:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", COMMIT_MSG)
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
print("")
print("DONE: " + FIX_NO + " applied.")