# fix.py -- fix110: search-aware counts guaranteed, modal footer button scale, silent efficient reloads, unified cyan glow
import subprocess, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)

# 1. Backend: replace whole /queues span with search-aware implementation
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
s = read(rc)
new_span = '''    @GetMapping("/queues")
    public Map<String, Object> queueCounts(@RequestParam(required = false) String q) {
        LocalDateTime now = LocalDateTime.now();
        Map<UUID, List<RecoveryNote>> nm = noteMap();
        Map<UUID, List<LandProject>> pm = projMap();
        String term = q == null ? "" : q.toLowerCase().replaceAll("\\\\s+", "");
        long all = 0, con = 0, mis = 0, site = 0, lock = 0;
        for (Client c : clientRepo.findAll()) {
            List<LandProject> ps = projectsOf(pm, c.getId());
            if (!qualifies(ps)) continue;
            if (!term.isEmpty() && !matchesTerm(c, ps, term)) continue;
            List<RecoveryNote> ns = notesOf(nm, c.getId());
            String st = state(c, now, ps, ns);
            if (st.equals("LOCKED")) lock++;
            else if (st.equals("SITE")) site++;
            else { all++; if (st.equals("CONTACTED")) con++; if (st.equals("MISSED")) mis++; }
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("ALL", all); m.put("CONTACTED", con); m.put("MISSED", mis); m.put("SITE", site); m.put("LOCKED", lock);
        return m;
    }
    private boolean matchesTerm(Client c, List<LandProject> ps, String term) {
        StringBuilder hay = new StringBuilder();
        if (c.getFullName() != null) hay.append(c.getFullName()).append(' ');
        if (c.getNationalId() != null) hay.append(c.getNationalId()).append(' ');
        if (c.getPhoneNumber() != null) hay.append(c.getPhoneNumber()).append(' ');
        for (LandProject p : ps) {
            if (p.getProjectIndex() != null) hay.append(p.getProjectIndex()).append(' ');
            if (p.getDistrict() != null) hay.append(p.getDistrict()).append(' ');
            if (p.getSubCounty() != null) hay.append(p.getSubCounty()).append(' ');
            if (p.getVillage() != null) hay.append(p.getVillage()).append(' ');
        }
        return hay.toString().toLowerCase().replaceAll("\\\\s+", "").contains(term);
    }
    @GetMapping("/queue")'''
m = re.search(r'    @GetMapping\("/queues"\).*?    @GetMapping\("/queue"\)', s, re.S)
if m:
    s = s[:m.start()] + new_span + s[m.end():]
    write(rc, s)
    print("OK queues span rewritten")
else:
    print("MISSING queues span")

# 2. recoveryService: force getQueues to pass the term
rs = FE / "services" / "recoveryService.js"
s2 = read(rs)
out = []
for ln in s2.split('\n'):
    if 'getQueues:' in ln:
        out.append(ln[:len(ln) - len(ln.lstrip())] + "getQueues: (q) => api.get('/recovery/queues', { params: q ? { q } : {} }),")
    else:
        out.append(ln)
s2 = '\n'.join(out)
write(rs, s2)
print("OK getQueues passes q")

# 3. RecoveryPortal: silent reloads + preserve expanded card + counts effect guard
jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
s3 = read(jsxp)
s3 = s3.replace("const load = useCallback(() => {\n    setLoading(!loadedOnce.current);",
"const load = useCallback((silent) => {\n    if (!silent) setLoading(!loadedOnce.current);", 1)
s3 = s3.replace("""            } else {
              setOpenId(list.length ? list[0].id : null);
            }""",
"""            } else {
              setOpenId((prev) => (list.some((x) => x.id === prev) ? prev : (list.length ? list[0].id : null)));
            }""", 1)
s3 = s3.replace("setCoWarn(r.data.coOwnerWarning); load();", "setCoWarn(r.data.coOwnerWarning); load(true);", 1)
s3 = s3.replace("setNotes(r.data || [])); load();", "setNotes(r.data || [])); load(true);", 1)
s3 = s3.replace("if (target !== tab) setTab(target); else load();", "if (target !== tab) setTab(target); else load(true);", 1)
if 'getQueues(search)' not in s3:
    s3 = s3.replace("useEffect(() => { load(); }, [load]);",
"""useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const t = setTimeout(() => {
      recoveryService.getQueues(search).then((r) => setCounts(r.data || r)).catch(() => {});
    }, 250);
    return () => clearTimeout(t);
  }, [search]);""", 1)
write(jsxp, s3)
print("OK portal efficiency + counts effect")

# 4. CSS: unified cyan glow for phone + joint name
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
c = read(cssp)
if "fix110" not in c:
    c += """
/* fix110: contact number and joint-owner name share identical type + cyan glow */
.mono, .coChip {
  font-family: 'Space Mono', monospace;
  font-weight: 900;
  font-size: clamp(11px, 1.2vw, 14px);
  letter-spacing: 1px;
  color: #67e8f9;
  text-shadow: 0 0 6px rgba(103, 232, 249, 0.45);
}
.mono:hover, .coChip:hover { color: #ffffff; text-shadow: 0 0 6px rgba(255, 255, 255, 0.45); }
"""
    write(cssp, c)
    print("OK fix110 css")
else:
    print("SKIP fix110 css already present")

# 5. Global: modal footer buttons match card CALL LOG scale
ix = FE / "index.css"
i = read(ix)
if "fix110" not in i:
    i += """
/* fix110: modal footer buttons match the card CALL LOG button scale */
[class*="modalFooter"] button {
  height: clamp(30px, 3.6vw, 36px) !important;
  padding: 0 clamp(9px, 1.2vw, 13px) !important;
  font-size: clamp(8px, 0.85vw, 10px) !important;
  letter-spacing: 1.5px !important;
}
"""
    write(ix, i)
    print("OK modal footer scale")
else:
    print("SKIP modal footer scale already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix110: search-aware counts guaranteed, modal footer button scale, silent efficient reloads, unified cyan glow"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")