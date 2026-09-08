# fix.py -- fix95: Intake-referenced card design, rail margin fix, legend scrolls away, project count + co-owner jump chips
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)
def append(p, marker, block, label):
    s = read(p)
    if marker not in s:
        write(p, s + block); print("OK", label)
    else:
        print("SKIP", label)

jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"

# 1. Move dot legend OUT of the sticky rail (it must scroll away)
patch(jsxp, """      </div>
      <div className={styles.dotLegend} aria-label="Payment dot legend">""",
"""      </div>
      </div>
      <div className={styles.dotLegend} aria-label="Payment dot legend">""", "close rail before legend")
patch(jsxp, """        <span><i className={styles.payDotRed} /> No recent payment</span>
      </div>
      </div>""",
"""        <span><i className={styles.payDotRed} /> No recent payment</span>
      </div>""", "remove extra rail close")

# 2. jump helper + pending open
patch(jsxp, "  const open = (c) => { setSel(c); setPicked(null); setText(''); recoveryService.getNotes(c.id).then((r) => setNotes(r.data || [])); };",
"""  const open = (c) => { setSel(c); setPicked(null); setText(''); recoveryService.getNotes(c.id).then((r) => setNotes(r.data || [])); };
  const pendingOpen = useRef(null);
  const jump = (co) => {
    const target = co.state === 'LOCKED' ? 'LOCKED' : co.state === 'SITE' ? 'SITE' : 'ALL';
    pendingOpen.current = co.id;
    if (target !== tab) setTab(target); else load();
  };""", "jump helper")
patch(jsxp, "        setOpenId(list.length ? list[0].id : null);",
"""        if (pendingOpen.current) {
          const hit = list.find((x) => x.id === pendingOpen.current);
          pendingOpen.current = null;
          if (hit) {
            setOpenId(hit.id);
            setTimeout(() => { const el = document.getElementById('rc-' + hit.id); if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' }); }, 80);
          } else setOpenId(list.length ? list[0].id : null);
        } else {
          setOpenId(list.length ? list[0].id : null);
        }""", "pending open after jump")

# 3. Card body redesign (Intake-referenced sections, decor, buttons, co-owner chips)
patch(jsxp, """              <article key={c.id} className={`${styles.rowCard} ${isOpen ? styles.rowOpen : ''}`}>""",
"""              <article key={c.id} id={'rc-' + c.id} className={`${styles.rowCard} ${isOpen ? styles.rowOpen : ''}`}>""", "article id")
patch(jsxp, """                {isOpen && (
                  <div className={styles.rowBody}>
                    <span className={styles.nin}>{c.nin}</span>
                    <span className={styles.mono}>{c.phone}</span>
                    <span className={styles.projLine}>
                      {(c.projectIds || []).map((pid, i) => (<a key={pid} className={styles.projLink} href={'/folder/' + pid} onClick={(e) => e.stopPropagation()}>#{c.indexes[i] || pid}</a>))}
                    </span>
                    {c.coNames && c.coNames.length > 0 && (<span className={styles.coLine}><FiUser aria-hidden="true" /> Joint with: {c.coNames.join(', ')}</span>)}
                    {c.district && (<span className={styles.loc}><FiMapPin aria-hidden="true" /> {c.district}{c.village ? ' - ' + c.village : ''}</span>)}
                    <span className={styles.attemptLine}><FiClock aria-hidden="true" /> Good calls this 30 days: {c.calls30}/2 - Misses: {c.miss30}</span>
                    {c.unlock && (<span className={styles.lockBanner}><FiClock aria-hidden="true" /> Resting until {fmtD(c.unlock)} - read only.</span>)}
                    <span className={styles.rowActions}>
                      <button type="button" className={styles.cardBtn} onClick={() => open(c)} disabled={c.state === 'LOCKED'}><FiPhone aria-hidden="true" /> OPEN CALL LOG</button>
                      {(c.projectIds || []).length > 0 && (<a className={styles.cardBtnLink} href={'/folder/' + c.projectIds[0]}><FiFolderPlus aria-hidden="true" /> OPEN FOLDER</a>)}
                    </span>
                  </div>
                )}""",
"""                {isOpen && (
                  <div className={styles.rowBody}>
                    <span className={styles.secBlock}>
                      <label className={styles.secLabel}>CONTACT</label>
                      <span className={styles.nin}>{c.nin}</span>
                      <span className={styles.mono}>{c.phone}</span>
                      {c.district && (<span className={styles.loc}><FiMapPin aria-hidden="true" /> {c.district}{c.village ? ' - ' + c.village : ''}</span>)}
                    </span>
                    <span className={styles.secBlock}>
                      <label className={styles.secLabel}>PROJECTS ({c.projectCount || (c.projectIds || []).length})</label>
                      <span className={styles.projLine}>
                        {(c.projectIds || []).map((pid, i) => (<a key={pid} className={styles.projLink} href={'/folder/' + pid} onClick={(e) => e.stopPropagation()}>#{c.indexes[i] || pid}</a>))}
                      </span>
                      {(c.coOwners || []).length > 0 && (
                        <span className={styles.coLine}>
                          <FiUser aria-hidden="true" /> Joint with:
                          {(c.coOwners || []).map((co) => (
                            <button key={co.id} type="button" className={styles.coChip} onClick={(e) => { e.stopPropagation(); jump(co); }}>
                              {co.name} ({co.projects})
                            </button>
                          ))}
                        </span>
                      )}
                    </span>
                    <span className={styles.secBlock}>
                      <label className={styles.secLabel}>CALL STATUS</label>
                      <span className={styles.attemptLine}><FiClock aria-hidden="true" /> Good calls this 30 days: {c.calls30}/2 - Misses: {c.miss30}</span>
                      {c.unlock && (<span className={styles.lockBanner}><FiClock aria-hidden="true" /> Resting until {fmtD(c.unlock)} - read only.</span>)}
                    </span>
                    <span className={styles.rowActions}>
                      <button type="button" className={styles.cardBtn} onClick={() => open(c)} disabled={c.state === 'LOCKED'}><FiPhone aria-hidden="true" /> OPEN CALL LOG</button>
                      {(c.projectIds || []).length > 0 && (<button type="button" className={styles.cardBtn2} onClick={() => { window.location.href = '/folder/' + c.projectIds[0]; }}><FiFolderPlus aria-hidden="true" /> OPEN FOLDER</button>)}
                    </span>
                    <span className={styles.decorBl} aria-hidden="true" />
                    <span className={styles.decorBr} aria-hidden="true" />
                  </div>
                )}""", "card body sections")

# 4. Backend: coOwners with ids, states, project counts + projectCount
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
patch(rc, """        List<String> idx = new ArrayList<>(); List<String> pids = new ArrayList<>(); List<String> co = new ArrayList<>();
        for (LandProject p : ps) {
            if (p.getProjectIndex() != null) idx.add(p.getProjectIndex());
            pids.add(p.getId().toString());
            if (p.getProprietors() != null) for (Client o : p.getProprietors()) if (!o.getId().equals(c.getId()) && !co.contains(o.getFullName())) co.add(o.getFullName());
        }
        m.put("indexes", idx); m.put("projectIds", pids); m.put("coNames", co);""",
"""        List<String> idx = new ArrayList<>(); List<String> pids = new ArrayList<>(); List<String> co = new ArrayList<>();
        List<Map<String, Object>> cos = new ArrayList<>();
        List<UUID> seen = new ArrayList<>();
        for (LandProject p : ps) {
            if (p.getProjectIndex() != null) idx.add(p.getProjectIndex());
            pids.add(p.getId().toString());
            if (p.getProprietors() != null) for (Client o : p.getProprietors()) {
                if (o.getId().equals(c.getId()) || seen.contains(o.getId())) continue;
                seen.add(o.getId());
                co.add(o.getFullName());
                List<LandProject> ops = projectsOf(pm, o.getId());
                List<RecoveryNote> ons = notesOf(nm, o.getId());
                Map<String, Object> cm = new LinkedHashMap<>();
                cm.put("id", o.getId()); cm.put("name", o.getFullName()); cm.put("projects", ops.size());
                cm.put("state", state(o, now, ops, ons));
                cos.add(cm);
            }
        }
        m.put("indexes", idx); m.put("projectIds", pids); m.put("coNames", co);
        m.put("coOwners", cos); m.put("projectCount", ps.size());""", "coOwners dto")

# 5. CSS: Intake-referenced themes + rail margin + button sizes
append(FE / "pages" / "Recovery" / "RecoveryPortal.module.css", "fix95", """
/* fix95: rail respects content margins on every screen */
.stickyRail { margin-left: 0; margin-right: 0; padding-left: 0; padding-right: 0; }
/* fix95: Intake-referenced card themes */
.rowCard { position: relative; border-bottom: 1.5px solid rgba(238, 140, 58, 0.25); }
.rowOpen .rowHead { border-bottom: 1.5px solid var(--orange); }
.rowBody { position: relative; display: flex; flex-direction: column; grid-template-columns: none; gap: 10px; padding: 10px 14px 20px; background: rgba(0, 0, 0, 0.16); }
.secBlock { display: flex; flex-direction: column; gap: 4px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 6px; padding: 8px 10px; }
.secLabel { font-family: 'DM Sans', sans-serif; font-size: clamp(7px, 0.8vw, 9px); font-weight: 900; letter-spacing: 2px; color: var(--orange); text-transform: uppercase; }
.decorBl, .decorBr { position: absolute; bottom: 6px; width: 14px; height: 14px; pointer-events: none; }
.decorBl { left: 8px; border-left: 1.5px solid rgba(238, 140, 58, 0.5); border-bottom: 1.5px solid rgba(238, 140, 58, 0.5); }
.decorBr { right: 8px; border-right: 1.5px solid rgba(238, 140, 58, 0.5); border-bottom: 1.5px solid rgba(238, 140, 58, 0.5); }
.cardBtn { height: clamp(30px, 3.6vw, 36px); }
.cardBtn2 { display: inline-flex; align-items: center; gap: 6px; height: clamp(30px, 3.6vw, 36px); padding: 0 clamp(12px, 1.5vw, 17px); margin-left: auto; background: rgba(255, 255, 255, 0.06); border: 1.5px solid rgba(255, 255, 255, 0.18); color: rgba(255, 255, 255, 0.85); border-radius: 6px; font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; transition: all 0.2s; }
.cardBtn2:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.cardBtn2:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.coChip { background: rgba(6, 182, 212, 0.10); border: 1px solid rgba(6, 182, 212, 0.35); color: #67e8f9; border-radius: 999px; padding: 2px 9px; font-family: 'DM Sans', sans-serif; font-size: clamp(8px, 0.85vw, 10px); font-weight: 900; letter-spacing: 0.5px; cursor: pointer; transition: all 0.2s; }
.coChip:hover { background: rgba(6, 182, 212, 0.2); color: #a5f3fc; }
.coChip:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
@media (max-width: 640px) { .rowActions { flex-wrap: wrap; } .cardBtn2 { margin-left: 0; } }
""", "recovery fix95 css")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix95: Intake-referenced card design, rail margin fix, legend scrolls away, project count + co-owner jump chips"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")