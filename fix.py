#!/usr/bin/env python3
# PATH: fix169.py
# GOLDEN SEED -- fix169: light Settings-style calendar, filter colours stop recolouring borders/corners, and every filter now runs over the FULL data (Ledger CRITICAL glitch + Audit + Recovery counts).
#
#   1. CALENDAR: the date picker popup (Intake "Date started", Audit, Report Studio) is now a LIGHT cream card
#      (#f2ede4, same as the Settings Appearance cards): dark navy text, orange 2px rule under the month title,
#      white-ish nav buttons, orange wash on hover, solid orange selected day, orange ring on today.
#   2. FILTER COLOURS vs FRAMES: picking a coloured filter pill (CRITICAL red, TITLED green, ...) used to recolour
#      the panel border, the bottom corner brackets, the bottom pins, the table header rule and the row hover edge.
#      Now those stay the normal orange on Ledger, Clients, Payments, Recovery and every HardwarePanel/CornerDecor,
#      exactly like the Settings page. The pill itself, the header text and the dots still follow the pill colour.
#   3. LEDGER FILTERS (the real glitch): the Project Ledger only fetched ONE server page of 15 rows and then ran
#      CRITICAL / PAID / TITLED / search / sort on just those 15, so most matches never appeared and NEXT was
#      disabled. It now loads every page (200 per request), then filters, sorts and pages in the browser.
#      Also: the CRITICAL filter and the red CRITICAL tag on a row now use ONE shared rule (before, receivables
#      showed the tag but were left out of the filter), and the backend ledger endpoint gets a stable sort so
#      pages never repeat or skip rows.
#   4. SAME GLITCH ELSEWHERE: Audit sent its keyword to an endpoint that ignored operator/action and never sent the
#      dates, so date filtering only trimmed one page of 50 (and NEXT turned off at 20). Now keyword, operator,
#      action and dates all go to the server together, a filter change returns to the first sector, and stale
#      replies are dropped. Recovery: the tab counts used to jump back to the UNFILTERED numbers whenever the queue
#      reloaded while a search was typed; they now keep the search.
#
# NOT in this fix: the expanded sidebar, the Payments / Clients data loading (already full-load), any page copy,
# any database change.
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
FIX_NO = "fix169"
COMMIT_MSG = "fix169: light Settings-style calendar, filter colours no longer recolour borders/corners, Ledger/Audit/Recovery filters run over the full data (CRITICAL glitch)"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

F_LEDGER_JSX = os.path.join(SRC, "pages", "Ledger", "LedgerPage.jsx")
F_LEDGER_CSS = os.path.join(SRC, "pages", "Ledger", "LedgerPage.module.css")
F_CLIENTS_CSS = os.path.join(SRC, "pages", "Clients", "ClientLedgerPage.module.css")
F_PAYMENTS_CSS = os.path.join(SRC, "pages", "Payments", "PaymentsPage.module.css")
F_RECOVERY_JSX = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.jsx")
F_RECOVERY_CSS = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.module.css")
F_AUDIT_JSX = os.path.join(SRC, "pages", "Audit", "AuditPage.jsx")
F_CORNER_CSS = os.path.join(SRC, "components", "ui", "CornerDecor.module.css")
F_DATEPICKER_CSS = os.path.join(SRC, "components", "common", "HardwareDatePicker.module.css")
F_LAND_CONTROLLER = os.path.join(JAVA, "modules", "land", "controller", "LandController.java")
F_GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
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
LOAD_FILES = (F_LEDGER_JSX, F_LAND_CONTROLLER, F_LEDGER_CSS, F_CLIENTS_CSS, F_PAYMENTS_CSS, F_CORNER_CSS, F_RECOVERY_CSS, F_RECOVERY_JSX, F_AUDIT_JSX, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_LEDGER_JSX,
      "\n".join([
          "const PAGE_SIZE = 15;",
          "const PaymentDot = ({ proj }) => {"
      ]),
      "\n".join([
          "const PAGE_SIZE = 15;",
          "// fix169: the WHOLE ledger is loaded (200 rows per request, every page) and then filtered, sorted and paged",
          "// here in the browser. Before, only one server page of 15 rows was fetched and the filters ran on those 15.",
          "const LOAD_SIZE = 200;",
          "// fix169: ONE rule for CRITICAL, used by the filter AND by the red tag on each row (they used to disagree:",
          "// receivables showed the tag but were left out of the filter).",
          "const isCriticalProject = (p) => (p.totalCost || 0) > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25;",
          "const PaymentDot = ({ proj }) => {"
      ]),
      "Ledger: load size + one shared CRITICAL rule")

patch(F_LEDGER_JSX,
      "\n".join([
          "    const fetchLedger = useCallback(async (attempt = 0) => {",
          "        setLoading(true); setLoadError(false);",
          "        try {",
          "            const data = await landService.getGlobalLedger(page, PAGE_SIZE);",
          "            setProjects(data.content || []); setLoading(false);",
          "        } catch {",
          "            if (attempt < 1) { setTimeout(() => fetchLedger(attempt + 1), 5000); return; }",
          "            setLoadError(true); setLoading(false);",
          "        }",
          "    }, [page]);",
          "    useEffect(() => { fetchLedger(); }, [fetchLedger]);"
      ]),
      "\n".join([
          "    const fetchLedger = useCallback(async (attempt = 0) => {",
          "        setLoading(true); setLoadError(false);",
          "        try {",
          "            // fix169: walk every server page so filters / search / sort see ALL projects, not 15 of them.",
          "            const all = [];",
          "            const seen = new Set();",
          "            for (let p = 0; p < 60; p += 1) {",
          "                const data = await landService.getGlobalLedger(p, LOAD_SIZE);",
          "                const rows = (data && data.content) || [];",
          "                rows.forEach(r => { if (!seen.has(r.id)) { seen.add(r.id); all.push(r); } });",
          "                if (rows.length < LOAD_SIZE || (data && data.last)) break;",
          "            }",
          "            setProjects(all); setLoading(false);",
          "        } catch {",
          "            if (attempt < 1) { setTimeout(() => fetchLedger(attempt + 1), 5000); return; }",
          "            setLoadError(true); setLoading(false);",
          "        }",
          "    }, []);",
          "    useEffect(() => { fetchLedger(); }, [fetchLedger]);",
          "    // fix169: a new search / filter / sort always starts from the first page of results",
          "    useEffect(() => { setPage(0); }, [searchTerm, activeFilter, sortConfig]);"
      ]),
      "Ledger: load every page once, reset to page 1 when search / filter / sort changes")

patch(F_LEDGER_JSX,
      "\n".join([
          "        landService.getStagesBulk(ids)",
          "            .then(list => {",
          "                const m = {};"
      ]),
      "\n".join([
          "        const chunks = [];",
          "        for (let i = 0; i < ids.length; i += 400) chunks.push(ids.slice(i, i + 400));",
          "        Promise.all(chunks.map(c => landService.getStagesBulk(c)))",
          "            .then(lists => {",
          "                const list = lists.flat();",
          "                const m = {};"
      ]),
      "Ledger: load stages for every project in chunks of 400")

patch(F_LEDGER_JSX,
      "\n".join([
          "        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && ((p.amountPaid || 0) / p.totalCost) < 0.25);"
      ]),
      "\n".join([
          "        if (activeFilter === 'CRITICAL')    filtered = filtered.filter(isCriticalProject);"
      ]),
      "Ledger: CRITICAL filter uses the same rule as the row tag")

patch(F_LEDGER_JSX,
      "\n".join([
          "    }, [projects, searchTerm, activeFilter, sortConfig, stageMap]);"
      ]),
      "\n".join([
          "    }, [projects, searchTerm, activeFilter, sortConfig, stageMap]);",
          "",
          "    // fix169: pages are cut from the FILTERED list, so every filter spans the whole ledger",
          "    const pageData = useMemo(() => processedData.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE), [processedData, page]);"
      ]),
      "Ledger: page the filtered list in the browser")

patch(F_LEDGER_JSX,
      "\n".join([
          "                            {!loading && !loadError && processedData.map((proj, i) => {"
      ]),
      "\n".join([
          "                            {!loading && !loadError && pageData.map((proj, i) => {"
      ]),
      "Ledger: table rows come from the current page of the filtered list")

patch(F_LEDGER_JSX,
      "\n".join([
          "                                const isCritical = pct < 25 && proj.totalCost > 0;"
      ]),
      "\n".join([
          "                                const isCritical = isCriticalProject(proj);"
      ]),
      "Ledger: row CRITICAL tag uses the shared rule")

patch(F_LEDGER_JSX,
      "\n".join([
          "disabled={processedData.length < PAGE_SIZE} aria-label=\"Next page\""
      ]),
      "\n".join([
          "disabled={(page + 1) * PAGE_SIZE >= processedData.length} aria-label=\"Next page\""
      ]),
      "Ledger: NEXT is enabled whenever more filtered rows exist")

patch(F_LAND_CONTROLLER,
      "\n".join([
          "import org.springframework.data.domain.PageRequest;"
      ]),
      "\n".join([
          "import org.springframework.data.domain.PageRequest;",
          "import org.springframework.data.domain.Sort;"
      ]),
      "Backend: import Sort for the ledger endpoint")

patch(F_LAND_CONTROLLER,
      "\n".join([
          "        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(page, size)));"
      ]),
      "\n".join([
          "        // fix169: an unsorted findAll can repeat or skip rows between pages; sort by id so paging is stable.",
          "        // Size is capped so one call cannot ask for the whole table in one go.",
          "        int safeSize = Math.min(Math.max(size, 1), 500);",
          "        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(Math.max(page, 0), safeSize, Sort.by(\"id\"))));"
      ]),
      "Backend: ledger endpoint pages with a stable sort and a size cap")

patch(F_LEDGER_CSS,
      "\n".join([
          "border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;isolation:isolate;"
      ]),
      "\n".join([
          "border:1.5px solid rgba(238,140,58,0.28);border-radius:var(--radius);padding:0;isolation:isolate;"
      ]),
      "Ledger CSS: panel border stays orange whatever filter is picked")

patch(F_LEDGER_CSS,
      "\n".join([
          ".decorBl,.decorBr{position:absolute;width:14px;height:14px;border:1.5px solid var(--orange);opacity:.55;pointer-events:none;z-index:20;}"
      ]),
      "\n".join([
          ".decorBl,.decorBr{position:absolute;width:14px;height:14px;border:1.5px solid #EE8C3A;opacity:.55;pointer-events:none;z-index:20;}"
      ]),
      "Ledger CSS: corner brackets stay orange")

patch(F_LEDGER_CSS,
      "\n".join([
          ".pin{width:3px;height:5px;background:var(--orange);border-radius:1px;box-shadow:0 0 5px rgba(238,140,58,.4);}"
      ]),
      "\n".join([
          ".pin{width:3px;height:5px;background:#EE8C3A;border-radius:1px;box-shadow:0 0 5px rgba(238,140,58,.4);}"
      ]),
      "Ledger CSS: pins stay orange")

patch(F_LEDGER_CSS,
      "\n".join([
          "    border-bottom:3px solid var(--orange);white-space:nowrap;user-select:none;",
          "    box-shadow:0 1px 0 var(--orange);"
      ]),
      "\n".join([
          "    border-bottom:3px solid #EE8C3A;white-space:nowrap;user-select:none;",
          "    box-shadow:0 1px 0 #EE8C3A;"
      ]),
      "Ledger CSS: table header rule stays orange")

patch(F_LEDGER_CSS,
      "\n".join([
          ".ledgerTable tbody tr:hover{background:rgba(255,255,255,0.04);border-left-color:var(--orange);}"
      ]),
      "\n".join([
          ".ledgerTable tbody tr:hover{background:rgba(255,255,255,0.04);border-left-color:#EE8C3A;}"
      ]),
      "Ledger CSS: row hover edge stays orange")

patch(F_CLIENTS_CSS,
      "\n".join([
          "border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;isolation:isolate;"
      ]),
      "\n".join([
          "border:1.5px solid rgba(238,140,58,0.28);border-radius:var(--radius);padding:0;isolation:isolate;"
      ]),
      "Clients CSS: panel border stays orange whatever filter is picked")

patch(F_CLIENTS_CSS,
      "\n".join([
          ".decorBl,.decorBr{position:absolute;width:14px;height:14px;border:1.5px solid var(--orange);opacity:.55;pointer-events:none;z-index:20;}"
      ]),
      "\n".join([
          ".decorBl,.decorBr{position:absolute;width:14px;height:14px;border:1.5px solid #EE8C3A;opacity:.55;pointer-events:none;z-index:20;}"
      ]),
      "Clients CSS: corner brackets stay orange")

patch(F_CLIENTS_CSS,
      "\n".join([
          ".pin{width:3px;height:5px;background:var(--orange);border-radius:1px;box-shadow:0 0 5px rgba(238,140,58,.4);}"
      ]),
      "\n".join([
          ".pin{width:3px;height:5px;background:#EE8C3A;border-radius:1px;box-shadow:0 0 5px rgba(238,140,58,.4);}"
      ]),
      "Clients CSS: pins stay orange")

patch(F_CLIENTS_CSS,
      "\n".join([
          "    border-bottom:3px solid var(--orange);white-space:nowrap;user-select:none;",
          "    box-shadow:0 1px 0 var(--orange);"
      ]),
      "\n".join([
          "    border-bottom:3px solid #EE8C3A;white-space:nowrap;user-select:none;",
          "    box-shadow:0 1px 0 #EE8C3A;"
      ]),
      "Clients CSS: table header rule stays orange")

patch(F_CLIENTS_CSS,
      "\n".join([
          ".ledgerTable tbody tr:hover{background:rgba(255,255,255,0.04);border-left-color:var(--orange);}"
      ]),
      "\n".join([
          ".ledgerTable tbody tr:hover{background:rgba(255,255,255,0.04);border-left-color:#EE8C3A;}"
      ]),
      "Clients CSS: row hover edge stays orange")

patch(F_PAYMENTS_CSS,
      "\n".join([
          ".accentWrap[data-tab-accent] > section[class] { border-color: var(--orange-border); }",
          ".accentWrap[data-tab-accent] > section[class]:hover { border-color: var(--orange); }"
      ]),
      "\n".join([
          ".accentWrap[data-tab-accent] > section[class] { border-color: rgba(238, 140, 58, 0.2); }",
          ".accentWrap[data-tab-accent] > section[class]:hover { border-color: #EE8C3A; }"
      ]),
      "Payments CSS: panel border stays orange whatever filter is picked")

patch(F_PAYMENTS_CSS,
      "\n".join([
          "    border-bottom: 3px solid var(--orange);",
          "    white-space: nowrap;"
      ]),
      "\n".join([
          "    border-bottom: 3px solid #EE8C3A;",
          "    white-space: nowrap;"
      ]),
      "Payments CSS: table header rule stays orange")

patch(F_PAYMENTS_CSS,
      "\n".join([
          ".ledgerTable th { z-index: 5; box-shadow: 0 1px 0 var(--orange); }"
      ]),
      "\n".join([
          ".ledgerTable th { z-index: 5; box-shadow: 0 1px 0 #EE8C3A; }"
      ]),
      "Payments CSS: header underline shadow stays orange")

patch(F_PAYMENTS_CSS,
      "\n".join([
          ".dataRow:hover {",
          "    background: rgba(255, 255, 255, 0.05);",
          "    border-left-color: var(--orange);",
          "}"
      ]),
      "\n".join([
          ".dataRow:hover {",
          "    background: rgba(255, 255, 255, 0.05);",
          "    border-left-color: #EE8C3A;",
          "}"
      ]),
      "Payments CSS: row hover edge stays orange")

patch(F_CORNER_CSS,
      "\n".join([
          "    border: 1.5px solid var(--orange);",
          "    opacity: 0.55;"
      ]),
      "\n".join([
          "    border: 1.5px solid #EE8C3A;",
          "    opacity: 0.55;"
      ]),
      "CornerDecor: corner brackets always orange")

patch(F_CORNER_CSS,
      "\n".join([
          "    background: var(--orange);",
          "    box-shadow: 0 0 5px rgba(238, 140, 58, 0.4);"
      ]),
      "\n".join([
          "    background: #EE8C3A;",
          "    box-shadow: 0 0 5px rgba(238, 140, 58, 0.4);"
      ]),
      "CornerDecor: pins always orange")

patch(F_RECOVERY_CSS,
      "\n".join([
          ".list[data-tab-accent] .rowCard { border-color: var(--orange-border); }",
          ".list[data-tab-accent] .rowCard:hover, .list[data-tab-accent] .rowOpen { border-color: var(--orange); }"
      ]),
      "\n".join([
          ".list[data-tab-accent] .rowCard { border-color: rgba(238, 140, 58, 0.2); }",
          ".list[data-tab-accent] .rowCard:hover, .list[data-tab-accent] .rowOpen { border-color: #EE8C3A; }",
          ".list[data-tab-accent] .rowOpen .rowHead { border-bottom-color: #EE8C3A; }"
      ]),
      "Recovery CSS: card borders stay orange whatever tab is picked")

patch(F_RECOVERY_JSX,
      "\n".join([
          "  const loadedOnce = useRef(false);"
      ]),
      "\n".join([
          "  const loadedOnce = useRef(false);",
          "  const searchRef = useRef('');"
      ]),
      "Recovery: remember the current search for the counts call")

patch(F_RECOVERY_JSX,
      "\n".join([
          "    Promise.all([recoveryService.getQueues(), recoveryService.getQueue(tab),"
      ]),
      "\n".join([
          "    Promise.all([recoveryService.getQueues(searchRef.current), recoveryService.getQueue(tab),"
      ]),
      "Recovery: tab counts keep the typed search when the queue reloads")

patch(F_RECOVERY_JSX,
      "\n".join([
          "  useEffect(() => {",
          "    const t = setTimeout(() => {",
          "      recoveryService.getQueues(search)"
      ]),
      "\n".join([
          "  useEffect(() => {",
          "    searchRef.current = search;",
          "    const t = setTimeout(() => {",
          "      recoveryService.getQueues(search)"
      ]),
      "Recovery: keep the search ref in step with the box")

patch(F_AUDIT_JSX,
      "\n".join([
          "import React, { useState, useEffect, useCallback, useMemo } from 'react';"
      ]),
      "\n".join([
          "import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';"
      ]),
      "Audit: import useRef")

patch(F_AUDIT_JSX,
      "\n".join([
          "    const fetchForensics = useCallback(async () => {",
          "        setLoading(true);"
      ]),
      "\n".join([
          "    const reqRef = useRef(0);",
          "    const fetchForensics = useCallback(async () => {",
          "        const myReq = ++reqRef.current;   // fix169: only the newest request may update the screen",
          "        setLoading(true);"
      ]),
      "Audit: ignore stale replies")

patch(F_AUDIT_JSX,
      "\n".join([
          "            const data = filters.search",
          "                ? await auditService.investigateKeyword(filters.search, page)",
          "                : await auditService.searchForensics({ operator: activeOperator, action: activeAction }, page);",
          "            setLogs(data.content || []);",
          "        } catch { console.error('FORENSIC_SIGNAL_LOST'); }",
          "        finally  { setLoading(false); }",
          "    }, [page, filters]);"
      ]),
      "\n".join([
          "            // fix169: keyword, operator, action and dates all go to the server TOGETHER. The keyword used to go",
          "            // to a different endpoint that ignored the other filters, and the dates were never sent at all.",
          "            const data = await auditService.searchForensics({",
          "                operator: activeOperator,",
          "                action: activeAction,",
          "                keyword: filters.search,",
          "                start: filters.from ? filters.from + 'T00:00:00' : null,",
          "                end: filters.to ? filters.to + 'T23:59:59' : null,",
          "            }, page);",
          "            if (myReq !== reqRef.current) return;",
          "            setLogs(data.content || []);",
          "        } catch { if (myReq === reqRef.current) console.error('FORENSIC_SIGNAL_LOST'); }",
          "        finally  { if (myReq === reqRef.current) setLoading(false); }",
          "    }, [page, filters]);",
          "",
          "    // fix169: any filter change starts again from the first sector",
          "    useEffect(() => { setPage(0); }, [filters]);"
      ]),
      "Audit: one server query for keyword + operator + action + dates, back to sector 1 on change")

patch(F_AUDIT_JSX,
      "\n".join([
          "    // WHEN, which is the first question anyone asks of an audit trail and the",
          "    // one filter the page did not have. The search endpoint takes operator and",
          "    // action but no date window, so this narrows the page in hand rather than",
          "    // the query -- honest about its scope in the hint under the controls."
      ]),
      "\n".join([
          "    // WHEN, which is the first question anyone asks of an audit trail.",
          "    // fix169: the dates now travel to the server with every other filter, so this",
          "    // only stays as a harmless safety net on the page in hand."
      ]),
      "Audit: comment now true")

patch(F_AUDIT_JSX,
      "\n".join([
          "disabled={logs.length < 20} aria-label=\"Newer logs\""
      ]),
      "\n".join([
          "disabled={logs.length < 50} aria-label=\"Newer logs\""
      ]),
      "Audit: NEWER LOGS stays on while a full page of 50 came back")

patch(F_GUIDE,
      "\n".join([
          "use `accent: 'red'` for danger filters (CRITICAL, PROBLEM)."
      ]),
      "\n".join([
          "use `accent: 'red'` for danger filters (CRITICAL, PROBLEM). fix169: the picked pill colour must NOT recolour panel borders, corner brackets, pins, header rules or row-hover edges -- those stay orange (`#EE8C3A`), like the Settings page; only the pill, header text, dots and soft hover washes may follow it. RULE: a filter must always run over the FULL data set, never over one server page -- the Project Ledger loads every page (200 per request) and then filters, sorts and pages in the browser; Audit sends keyword, operator, action and dates to the server together."
      ]),
      "Guide: filter colour + full-data filter rules")

patch(F_GUIDE,
      "\n".join([
          "The one `datetime-local` (Folder page deadline) is still native."
      ]),
      "\n".join([
          "The one `datetime-local` (Folder page deadline) is still native. fix169: the popup is a LIGHT cream card (`#f2ede4`, the Settings Appearance card colour) with dark navy text, a 2px orange rule under the month title, solid orange selected day and an orange ring on today."
      ]),
      "Guide: light calendar")

newfile(F_DATEPICKER_CSS,
        "\n".join([
          "/* PATH: erp-frontend/src/components/common/HardwareDatePicker.module.css */",
          "/* fix169: the app's one date picker, now LIGHT. Card = the Settings Appearance cream card (#f2ede4) with dark navy",
          "   text; a 2px orange rule sits under the month title like the Settings group labels. Selected day = solid orange,",
          "   today = orange ring, hover = soft orange wash. Orange TEXT on cream is too faint, so text accents use #b45a12. */",
          "",
          ".wrap { position: relative; display: inline-flex; align-items: center; min-width: 0; }",
          ".wrapBlock { display: flex; width: 100%; }",
          "",
          "/* the visible field: each page styles it through the className it passes in */",
          ".field { cursor: pointer; text-overflow: ellipsis; padding-right: 30px !important; box-sizing: border-box; }",
          ".wrapBlock .field { width: 100%; }",
          ".fieldIcon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #EE8C3A; font-size: 14px; pointer-events: none; }",
          "",
          ".pop {",
          "    position: fixed;",
          "    z-index: 100000;",
          "    box-sizing: border-box;",
          "    padding: 14px;",
          "    background: #f2ede4;",
          "    border: 1.5px solid rgba(238, 140, 58, 0.45);",
          "    border-radius: 12px;",
          "    box-shadow: 0 18px 48px rgba(26, 46, 48, 0.32), 0 0 0 1px rgba(255, 255, 255, 0.5) inset;",
          "    font-family: 'DM Sans', sans-serif;",
          "    animation: popIn 0.18s cubic-bezier(0.2, 1, 0.3, 1);",
          "}",
          "@keyframes popIn {",
          "    from { opacity: 0; transform: translateY(-6px); }",
          "    to   { opacity: 1; transform: translateY(0); }",
          "}",
          "",
          ".nav {",
          "    display: flex; align-items: center; gap: 4px;",
          "    padding-bottom: 10px; margin-bottom: 10px;",
          "    border-bottom: 2px solid #EE8C3A;",
          "}",
          ".navTitle {",
          "    flex: 1; text-align: center;",
          "    font-family: 'Cinzel', serif; font-weight: 700; font-size: 12px;",
          "    letter-spacing: 1.5px; text-transform: uppercase; color: #1a2e30;",
          "}",
          ".navBtn {",
          "    width: 26px; height: 26px; flex-shrink: 0;",
          "    display: flex; align-items: center; justify-content: center;",
          "    background: rgba(255, 255, 255, 0.65); border: 1.5px solid rgba(26, 46, 48, 0.2);",
          "    border-radius: 6px; color: rgba(26, 46, 48, 0.85); font-size: 14px; cursor: pointer;",
          "    transition: background 0.15s, color 0.15s, border-color 0.15s;",
          "}",
          ".navBtn:hover { background: rgba(238, 140, 58, 0.16); border-color: #EE8C3A; color: #b45a12; }",
          ".navBtn:focus-visible, .day:focus-visible, .footBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 1px; }",
          "",
          ".dowRow, .grid { display: grid; grid-template-columns: repeat(7, 1fr); }",
          ".dowRow { margin-bottom: 4px; }",
          ".dowRow span {",
          "    text-align: center; padding: 4px 0;",
          "    font-size: 9px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;",
          "    color: rgba(26, 46, 48, 0.6);",
          "}",
          "",
          ".grid { gap: 2px; }",
          ".day {",
          "    height: 32px; display: flex; align-items: center; justify-content: center;",
          "    background: transparent; border: 1.5px solid transparent; border-radius: 6px;",
          "    font-family: 'Space Mono', monospace; font-size: 12px; font-weight: 700;",
          "    color: #1a2e30; cursor: pointer;",
          "    transition: background 0.12s, border-color 0.12s, color 0.12s;",
          "}",
          ".day:hover { background: rgba(238, 140, 58, 0.16); border-color: #EE8C3A; }",
          ".dayOut { color: rgba(26, 46, 48, 0.32); }",
          ".dayNow { border-color: #EE8C3A; color: #b45a12; background: rgba(255, 255, 255, 0.65); }",
          ".daySel, .daySel:hover { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; font-weight: 900; box-shadow: 0 3px 10px rgba(238, 140, 58, 0.4); }",
          "",
          ".foot {",
          "    display: flex; justify-content: space-between; align-items: center;",
          "    margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(26, 46, 48, 0.14);",
          "}",
          ".footBtn {",
          "    background: transparent; border: none; cursor: pointer; padding: 6px 8px; border-radius: 6px;",
          "    font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 900;",
          "    letter-spacing: 1.5px; text-transform: uppercase; color: rgba(26, 46, 48, 0.65);",
          "    transition: background 0.15s, color 0.15s;",
          "}",
          ".footBtn:hover { background: rgba(26, 46, 48, 0.08); color: #1a2e30; }",
          ".footBtnHot { color: #b45a12; }",
          ".footBtnHot:hover { background: rgba(238, 140, 58, 0.16); color: #8f4509; }"
      ]),
        "light Settings-style calendar popup (HardwareDatePicker.module.css)",
        "fix169: the app's one date picker, now LIGHT")

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