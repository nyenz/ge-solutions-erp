#!/usr/bin/env python3
# PATH: fix170.py
# GOLDEN SEED -- fix170: lighter calendar, stronger notification hover, and the SPEED glitches (Recovery tab switch, slow queries, slow page start).
#
#   1. CALENDAR: lighter again and calmer. Near-white warm card, soft slate text (not near-black), faint weekday and
#      out-of-month days, a thin soft orange rule, hairline button borders. Selected day is a soft solid orange,
#      today is a thin orange ring. Contrast is deliberately gentle but the text stays readable.
#   2. NOTIFICATION HOVER: hovering a bell row used to change the background by only a few percent. Unread rows now
#      take a clear tint of their own colour, read rows go visibly darker, and the coloured left edge appears on hover.
#   3. RECOVERY "LOCKED" GLITCH (the one you saw): clicking a tab switched the highlight at once but the OLD tab's cards
#      stayed on screen, fully clickable, until the server answered -- so CALL LOG opened on people who were really
#      locked. Now the cards on screen always belong to the tab you picked: the old ones are removed the moment you
#      click, a tab you have already opened shows instantly from memory (CALL LOG stays disabled until the fresh
#      answer lands), and an older slow answer can never overwrite a newer click.
#   4. WHY IT WAS SLOW: every tab click fired FOUR requests (queue, counts, tags, stats) and each one loaded every
#      project, with the owners and the title fetched one project at a time (hundreds of tiny queries each).
#      - tab click now asks for the queue only (counts / tags / stats load on first open, REFRESH and after a call);
#      - the project list (used by Recovery, Dashboard, Reports, Client Ledger) now fetches projects + owners + title in
#        ONE query; recovery notes come with their client in ONE query;
#      - the Project Ledger stage lists are fetched in ONE query per page instead of one per project (fix169 made
#        pages 200 rows, so this matters);
#      - the top bar's three background checks (stale count, unread count, notification list) run together instead of
#        one after another on every page load and every refresh; the first search-box counts call is no longer doubled.
#
# NOT in this fix: any screen layout, any wording, any database change.
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
FIX_NO = "fix170"
COMMIT_MSG = "fix170: lighter calendar, clearer notification hover, Recovery tab switch no longer shows stale clickable cards, big speed-up (one-query project/note loading, bulk ledger stages, queue-only tab loads, parallel top-bar checks)"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

F_RECOVERY_JSX = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.jsx")
F_HEADER_JSX = os.path.join(SRC, "components", "layout", "Header.jsx")
F_HEADER_CSS = os.path.join(SRC, "components", "layout", "Header.module.css")
F_DATEPICKER_CSS = os.path.join(SRC, "components", "common", "HardwareDatePicker.module.css")
F_PROJECT_REPO = os.path.join(JAVA, "modules", "land", "repository", "LandProjectRepository.java")
F_NOTE_REPO = os.path.join(JAVA, "modules", "client", "repository", "RecoveryNoteRepository.java")
F_NOTE_CTRL = os.path.join(JAVA, "modules", "client", "controller", "RecoveryNoteController.java")
F_LAND_SERVICE = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
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
LOAD_FILES = (F_HEADER_CSS, F_HEADER_JSX, F_RECOVERY_JSX, F_PROJECT_REPO, F_NOTE_REPO, F_NOTE_CTRL, F_LAND_SERVICE, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_HEADER_CSS,
      "\n".join([
          ".notifUnread:hover { background: #f6f9f9; background: color-mix(in srgb, var(--t) 17%, #ffffff); }",
          ".notifRead { border-left-color: transparent; background: #e4eaea; }",
          ".notifRead:hover { background: #dde4e4; }"
      ]),
      "\n".join([
          ".notifUnread:hover { background: #e3ede9; background: color-mix(in srgb, var(--t) 30%, #ffffff); }",
          ".notifRead { border-left-color: transparent; background: #e4eaea; }",
          ".notifRead:hover { background: #cbd8d8; border-left-color: var(--t, #EE8C3A); }"
      ]),
      "Notifications: clearer hover on unread and read rows")

patch(F_HEADER_JSX,
      "\n".join([
          "        try { setStaleCount((await recoveryService.getTaskCount()) ?? 0); } catch { /* offline */ }",
          "        try { setUnread((await recoveryService.getUnreadCount()) ?? 0); } catch { /* offline */ }",
          "        await pullList(true);"
      ]),
      "\n".join([
          "        // fix170: the three checks run together instead of one after another",
          "        await Promise.all([",
          "            recoveryService.getTaskCount().then((n) => setStaleCount(n ?? 0)).catch(() => { /* offline */ }),",
          "            recoveryService.getUnreadCount().then((n) => setUnread(n ?? 0)).catch(() => { /* offline */ }),",
          "            pullList(true),",
          "        ]);"
      ]),
      "Top bar: run the three background checks in parallel")

patch(F_RECOVERY_JSX,
      "\n".join([
          "  const loadedOnce = useRef(false);",
          "  const searchRef = useRef('');"
      ]),
      "\n".join([
          "  const loadedOnce = useRef(false);",
          "  const searchRef = useRef('');",
          "  // fix170: rowsTab = which tab the cards on screen belong to; syncing = a fresh answer is on its way;",
          "  // reqRef = newest request wins; cacheRef = last answer per tab so a revisited tab shows at once.",
          "  const [rowsTab, setRowsTab] = useState(null);",
          "  const [syncing, setSyncing] = useState(false);",
          "  const reqRef = useRef(0);",
          "  const cacheRef = useRef({});"
      ]),
      "Recovery: tab-owned rows, syncing flag, newest-request-wins, per-tab cache")

patch(F_RECOVERY_JSX,
      "\n".join([
          "  const load = useCallback((silent) => {",
          "    if (!silent) setLoading(!loadedOnce.current);",
          "    Promise.all([recoveryService.getQueues(searchRef.current), recoveryService.getQueue(tab), recoveryService.getTags(), recoveryService.getStats()])",
          "      .then((r) => {",
          "        setCounts(r[0].data || r[0]); setTags(r[2].data || r[2]); setStats(r[3].data || r[3]);",
          "        const list = r[1].data || r[1];",
          "        setRows(list);"
      ]),
      "\n".join([
          "  // fix170: a plain tab click asks for the queue ONLY; counts / tags / stats come on first open, REFRESH and after a call.",
          "  const load = useCallback((silent, forceMeta) => {",
          "    const myReq = ++reqRef.current;",
          "    const withMeta = !!forceMeta || !!silent || !loadedOnce.current;",
          "    if (!silent) { setLoading(!loadedOnce.current); setSyncing(true); }",
          "    const calls = [recoveryService.getQueue(tab)];",
          "    if (withMeta) calls.push(recoveryService.getQueues(searchRef.current), recoveryService.getTags(), recoveryService.getStats());",
          "    Promise.all(calls)",
          "      .then((r) => {",
          "        if (myReq !== reqRef.current) return;   // a newer click already replaced this request",
          "        if (withMeta) { setCounts(r[1].data || r[1]); setTags(r[2].data || r[2]); setStats(r[3].data || r[3]); }",
          "        const list = r[0].data || r[0];",
          "        cacheRef.current[tab] = list;",
          "        setRows(list); setRowsTab(tab);"
      ]),
      "Recovery: queue-only tab loads, stale answers dropped, rows tagged with their tab")

patch(F_RECOVERY_JSX,
      "\n".join([
          "        loadedOnce.current = true;",
          "        setLoading(false);",
          "      }).catch(() => { setLoading(false); toast('Could not load recovery queue.', 'error'); });",
          "  }, [tab, toast]);",
          "  useEffect(() => { load(); }, [load]);"
      ]),
      "\n".join([
          "        loadedOnce.current = true;",
          "        setLoading(false); setSyncing(false);",
          "      }).catch(() => { if (myReq !== reqRef.current) return; setLoading(false); setSyncing(false); toast('Could not load recovery queue.', 'error'); });",
          "  }, [tab, toast]);",
          "  useEffect(() => { load(); }, [load]);",
          "  // fix170: a tab already opened this visit shows at once; a tab never opened shows the loading panel, never the old tab's cards",
          "  useEffect(() => {",
          "    const cached = cacheRef.current[tab];",
          "    if (cached) { setRows(cached); setRowsTab(tab); setOpenId(null); }",
          "  }, [tab]);"
      ]),
      "Recovery: instant revisit from the per-tab cache")

patch(F_RECOVERY_JSX,
      "\n".join([
          "    searchRef.current = search;",
          "    const t = setTimeout(() => {"
      ]),
      "\n".join([
          "    searchRef.current = search;",
          "    if (!search && !loadedOnce.current) return undefined;   // fix170: the first load already fetched the counts",
          "    const t = setTimeout(() => {"
      ]),
      "Recovery: no doubled counts call on first open")

patch(F_RECOVERY_JSX,
      "\n".join([
          "  const rowsF = rows.filter("
      ]),
      "\n".join([
          "  const rowsF = (rowsTab !== tab ? [] : rows).filter("
      ]),
      "Recovery: never list another tab's cards")

patch(F_RECOVERY_JSX,
      "\n".join([
          "busy={loading}",
          "            tip=\"Reload the queues, counts and call stats\" onClick={() => load()} />"
      ]),
      "\n".join([
          "busy={loading || syncing}",
          "            tip=\"Reload the queues, counts and call stats\" onClick={() => load(false, true)} />"
      ]),
      "Recovery: REFRESH reloads counts and stats too")

patch(F_RECOVERY_JSX,
      "\n".join([
          "      {loading && rows.length === 0 ? ("
      ]),
      "\n".join([
          "      {(loading && rows.length === 0) || (syncing && rowsTab !== tab) ? ("
      ]),
      "Recovery: loading panel while the picked tab has nothing of its own yet")

patch(F_RECOVERY_JSX,
      "\n".join([
          "${styles.list} ${loading ? styles.refreshing : ''}"
      ]),
      "\n".join([
          "${styles.list} ${loading || syncing ? styles.refreshing : ''}"
      ]),
      "Recovery: dim the list while a fresh answer is on its way")

patch(F_RECOVERY_JSX,
      "\n".join([
          "onClick={() => open(c)} disabled={c.state === 'LOCKED'}>"
      ]),
      "\n".join([
          "onClick={() => open(c)} disabled={c.state === 'LOCKED' || tab === 'LOCKED' || syncing}>"
      ]),
      "Recovery: CALL LOG disabled for locked people and until the fresh answer lands")

patch(F_PROJECT_REPO,
      "\n".join([
          "    @Query(\"SELECT p FROM LandProject p WHERE p.deleted = false\")",
          "    List<LandProject> findAll();"
      ]),
      "\n".join([
          "    // fix170: owners + title come in the SAME query. Both are EAGER, and a plain JPQL query loads EAGER links one",
          "    // project at a time (hundreds of tiny queries per request) -- Recovery, Dashboard, Reports and Client Ledger all pay that.",
          "    @Query(\"SELECT DISTINCT p FROM LandProject p LEFT JOIN FETCH p.proprietors LEFT JOIN FETCH p.landTitle WHERE p.deleted = false\")",
          "    List<LandProject> findAll();"
      ]),
      "Backend: project list with owners + title in one query")

patch(F_NOTE_REPO,
      "\n".join([
          "    List<RecoveryNote> findByClientOrderByCreatedAtDesc(Client client);"
      ]),
      "\n".join([
          "    List<RecoveryNote> findByClientOrderByCreatedAtDesc(Client client);",
          "    // fix170: every note WITH its client in one query (the queue / counts / stats pages group notes by client)",
          "    @Query(\"SELECT n FROM RecoveryNote n JOIN FETCH n.client\")",
          "    List<RecoveryNote> findAllWithClient();"
      ]),
      "Backend: notes with their client in one query")

patch(F_NOTE_CTRL,
      "\n".join([
          "        for (RecoveryNote n : noteRepo.findAll()) m.computeIfAbsent(n.getClient().getId(), k -> new ArrayList<>()).add(n);"
      ]),
      "\n".join([
          "        for (RecoveryNote n : noteRepo.findAllWithClient()) m.computeIfAbsent(n.getClient().getId(), k -> new ArrayList<>()).add(n);"
      ]),
      "Backend: noteMap uses the one-query load")

patch(F_LAND_SERVICE,
      "\n".join([
          "        Page<LandProject> page = projectRepository.findAll(pageable);",
          "        page.getContent().forEach(p -> p.setStages(projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(p.getId())));",
          "        return page;"
      ]),
      "\n".join([
          "        Page<LandProject> page = projectRepository.findAll(pageable);",
          "        // fix170: ONE query for every stage on the page (it was one query per project)",
          "        List<UUID> ids = new ArrayList<>();",
          "        for (LandProject p : page.getContent()) ids.add(p.getId());",
          "        Map<UUID, List<ProjectStage>> byProject = new HashMap<>();",
          "        if (!ids.isEmpty()) for (ProjectStage s : projectStageRepository.findByProjectIdIn(ids)) byProject.computeIfAbsent(s.getProjectId(), k -> new ArrayList<>()).add(s);",
          "        for (LandProject p : page.getContent()) {",
          "            List<ProjectStage> l = byProject.getOrDefault(p.getId(), new ArrayList<>());",
          "            l.sort(Comparator.comparingInt(s -> s.getDisplayOrder() == null ? 0 : s.getDisplayOrder()));",
          "            p.setStages(l);",
          "        }",
          "        return page;"
      ]),
      "Backend: ledger stages in one query per page")

patch(F_GUIDE,
      "\n".join([
          "RULE: a filter must always run over the FULL data set, never over one server page"
      ]),
      "\n".join([
          "RULE (fix170): when a tab or filter changes what the server returns, the cards on screen must belong to the tab picked -- never leave the previous tab's cards clickable while the new answer loads (Recovery keeps `rowsTab` + `syncing`, a per-tab cache, and drops stale replies). Speed rule: never load an EAGER link inside a loop -- fetch it in the same query (`JOIN FETCH`) or in one `IN (...)` query. RULE: a filter must always run over the FULL data set, never over one server page"
      ]),
      "Guide: stale-cards + one-query speed rules")

newfile(F_DATEPICKER_CSS,
        "\n".join([
          "/* PATH: erp-frontend/src/components/common/HardwareDatePicker.module.css */",
          "/* fix170: lighter and calmer than fix169. Near-white warm card, soft slate text, faint weekday / out-of-month days,",
          "   thin soft orange rule, hairline borders. Selected day = soft solid orange, today = thin orange ring.",
          "   Orange TEXT on a light card is too faint, so text accents use the darker #b8651d. */",
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
          "    background: #faf7f2;",
          "    border: 1px solid rgba(238, 140, 58, 0.32);",
          "    border-radius: 12px;",
          "    box-shadow: 0 14px 38px rgba(26, 46, 48, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.7) inset;",
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
          "    border-bottom: 1.5px solid rgba(238, 140, 58, 0.55);",
          "}",
          ".navTitle {",
          "    flex: 1; text-align: center;",
          "    font-family: 'Cinzel', serif; font-weight: 700; font-size: 12px;",
          "    letter-spacing: 1.5px; text-transform: uppercase; color: #3d5254;",
          "}",
          ".navBtn {",
          "    width: 26px; height: 26px; flex-shrink: 0;",
          "    display: flex; align-items: center; justify-content: center;",
          "    background: rgba(255, 255, 255, 0.8); border: 1px solid rgba(26, 46, 48, 0.12);",
          "    border-radius: 6px; color: rgba(26, 46, 48, 0.6); font-size: 14px; cursor: pointer;",
          "    transition: background 0.15s, color 0.15s, border-color 0.15s;",
          "}",
          ".navBtn:hover { background: rgba(238, 140, 58, 0.12); border-color: rgba(238, 140, 58, 0.6); color: #b8651d; }",
          ".navBtn:focus-visible, .day:focus-visible, .footBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 1px; }",
          "",
          ".dowRow, .grid { display: grid; grid-template-columns: repeat(7, 1fr); }",
          ".dowRow { margin-bottom: 4px; }",
          ".dowRow span {",
          "    text-align: center; padding: 4px 0;",
          "    font-size: 9px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;",
          "    color: rgba(26, 46, 48, 0.42);",
          "}",
          "",
          ".grid { gap: 2px; }",
          ".day {",
          "    height: 32px; display: flex; align-items: center; justify-content: center;",
          "    background: transparent; border: 1px solid transparent; border-radius: 6px;",
          "    font-family: 'Space Mono', monospace; font-size: 12px; font-weight: 700;",
          "    color: #3d5254; cursor: pointer;",
          "    transition: background 0.12s, border-color 0.12s, color 0.12s;",
          "}",
          ".day:hover { background: rgba(238, 140, 58, 0.12); border-color: rgba(238, 140, 58, 0.45); }",
          ".dayOut { color: rgba(26, 46, 48, 0.22); }",
          ".dayNow { border-color: rgba(238, 140, 58, 0.7); color: #b8651d; background: transparent; }",
          ".daySel, .daySel:hover { background: #f2a257; border-color: #f2a257; color: #2a3b3d; font-weight: 800; box-shadow: 0 2px 8px rgba(238, 140, 58, 0.28); }",
          "",
          ".foot {",
          "    display: flex; justify-content: space-between; align-items: center;",
          "    margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(26, 46, 48, 0.09);",
          "}",
          ".footBtn {",
          "    background: transparent; border: none; cursor: pointer; padding: 6px 8px; border-radius: 6px;",
          "    font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 800;",
          "    letter-spacing: 1.5px; text-transform: uppercase; color: rgba(26, 46, 48, 0.5);",
          "    transition: background 0.15s, color 0.15s;",
          "}",
          ".footBtn:hover { background: rgba(26, 46, 48, 0.06); color: #3d5254; }",
          ".footBtnHot { color: #b8651d; }",
          ".footBtnHot:hover { background: rgba(238, 140, 58, 0.12); color: #8f4509; }"
      ]),
        "lighter, calmer calendar popup (HardwareDatePicker.module.css)",
        "fix170: lighter and calmer than fix169")

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