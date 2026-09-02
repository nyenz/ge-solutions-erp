# fix.py — GE Solutions ERP: Folder Page Redesign (safe, self-verifying)
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
BE = os.path.join(ROOT, "erp-backend", "src", "main", "java", "com", "gesolutions", "erp")
BACKUP = os.path.join(ROOT, ".fix_backup")
report = []

def log(m): report.append(m); print(m)
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
def find(name, base):
    for r, d, fs in os.walk(base):
        if name in fs: return os.path.join(r, name)
    return None
def rel_import(from_dir, to_file):
    a, b = os.path.dirname(to_file), from_dir
    rel = os.path.relpath(a, b).replace(os.sep, "/")
    return rel if rel.startswith(".") else "./" + rel

# ---------- BACKUP ----------
os.makedirs(BACKUP, exist_ok=True)

# ---------- LOCATE FILES ----------
folder_jsx = find("FolderPage.jsx", FE)
folder_css = find("FolderPage.module.css", FE)
land_svc = find("landService.js", FE) or find("landService.jsx", FE)
useauth_hook = find("useAuth.js", FE) or find("useAuth.jsx", FE)
if not (folder_jsx and folder_css and land_svc):
    log("ABORT: core files not found."); sys.exit(1)
for p in (folder_jsx, folder_css, land_svc):
    shutil.copy2(p, BACKUP)

PAGE_DIR = os.path.dirname(folder_jsx)
SVC_DIR = os.path.dirname(land_svc)

# ---------- BACKEND: new controller (brand-new file, no patching) ----------
ctrl = '''package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/v1/land/portal")
@RequiredArgsConstructor
public class FolderPortalController {

    private final LandProjectRepository projectRepository;
    private final AuditService auditService;

    private String op() {
        var a = SecurityContextHolder.getContext().getAuthentication();
        return a != null ? a.getName() : "SYSTEM";
    }

    @GetMapping("/{id}/receivable")
    @Transactional(readOnly = true)
    public Map<String, Object> receivable(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        Map<String, Object> m = new HashMap<>();
        m.put("receivable", p.isReceivable());
        m.put("actual", p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO);
        m.put("storage", p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO);
        m.put("paid", p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        m.put("total", p.receivableTotalOwed());
        m.put("rate", p.getStorageFeeOverride());
        m.put("deadline", p.getNegotiationDeadline());
        m.put("startDate", p.getReceivableStartDate());
        m.put("backlog", p.getLandTitle() == null);
        return m;
    }

    @GetMapping("/{id}/portfolio")
    @Transactional(readOnly = true)
    public List<Map<String, Object>> portfolio(@PathVariable UUID id) {
        LandProject current = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        List<Map<String, Object>> out = new ArrayList<>();
        if (current.getProprietors() == null) return out;
        for (LandProject other : projectRepository.findAll()) {
            if (other.getId().equals(id) || other.getProprietors() == null) continue;
            for (var owner : current.getProprietors()) {
                if (other.getProprietors().stream().anyMatch(c -> c.getId().equals(owner.getId()))) {
                    Map<String, Object> m = new HashMap<>();
                    m.put("projectId", other.getId());
                    m.put("index", other.getProjectIndex());
                    m.put("plot", other.getLandTitle() != null ? other.getLandTitle().getPlotNumber() : null);
                    m.put("titled", other.getLandTitle() != null);
                    m.put("receivable", other.isReceivable());
                    m.put("sharedOwner", owner.getFullName());
                    out.add(m);
                    break;
                }
            }
        }
        return out;
    }

    @PostMapping("/{id}/receivable/enter")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> enter(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setReceivable(true);
        if (p.getReceivableStartDate() == null) p.setReceivableStartDate(LocalDateTime.now());
        BigDecimal owed = (p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO)
                .add(p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO)
                .subtract(p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        p.setOriginalDebt(owed.max(BigDecimal.ZERO));
        p.setStatus("RECEIVABLE");
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_ENTER", "Operator [" + op() + "] moved project #" + p.getProjectIndex() + " into receivables.");
        return receivable(id);
    }

    @PostMapping("/{id}/receivable/exit")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> exit(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        String action = body.getOrDefault("action", "SET_ASIDE");
        BigDecimal fees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        if ("WAIVE".equals(action)) {
            auditService.logAction("FEES_WAIVED", "Operator [" + op() + "] waived UGX " + fees + " on #" + p.getProjectIndex() + ".");
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
        } else if ("CAPITALIZE".equals(action)) {
            p.setTotalCost((p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO).add(fees));
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
            auditService.logAction("FEES_CAPITALIZED", "Operator [" + op() + "] capitalized UGX " + fees + " into total cost on #" + p.getProjectIndex() + ".");
        } else {
            auditService.logAction("RECEIVABLE_SET_ASIDE", "Operator [" + op() + "] set aside #" + p.getProjectIndex() + " (fees UGX " + fees + " retained, billing stopped).");
        }
        p.setReceivable(false);
        p.setStatus("ACTIVE");
        projectRepository.save(p);
        return receivable(id);
    }

    @PostMapping("/{id}/receivable/settings")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> settings(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        if (body.containsKey("rate")) {
            p.setStorageFeeOverride(body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate")));
        }
        if (body.containsKey("deadline")) {
            p.setNegotiationDeadline(body.get("deadline") == null || body.get("deadline").isBlank() ? null : LocalDateTime.parse(body.get("deadline")));
        }
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex() + ".");
        return receivable(id);
    }
}
'''
ctrl_path = os.path.join(BE, "modules", "land", "controller", "FolderPortalController.java")
shutil.copy2(ctrl_path, BACKUP) if os.path.exists(ctrl_path) else None
write(ctrl_path, ctrl)
log("BACKEND: FolderPortalController.java written.")

# ---------- FRONTEND: new service (header cloned from landService) ----------
ls = read(land_svc)
m = re.search(r"([\s\S]*?)(export|const|function)", ls)
header = m.group(1) if m else ""
svc = header + '''
export const folderPortalService = {
  getReceivable: (id) => api.get(`/land/portal/${id}/receivable`).then(r => r.data),
  getPortfolio: (id) => api.get(`/land/portal/${id}/portfolio`).then(r => r.data),
  enter: (id) => api.post(`/land/portal/${id}/receivable/enter`).then(r => r.data),
  exit: (id, action) => api.post(`/land/portal/${id}/receivable/exit`, { action }).then(r => r.data),
  settings: (id, payload) => api.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),
};
export default folderPortalService;
'''
svc_path = os.path.join(SVC_DIR, "folderPortalService.js")
write(svc_path, svc)
log("FRONTEND: folderPortalService.js written.")

# ---------- FRONTEND: transform FolderPage.jsx ----------
src = read(folder_jsx)

# 1) Remove Pipeline HUD
new_src, n = re.subn(r"<nav className=\{styles\.pipelineHUD\}[\s\S]*?</nav>", "", src)
if n == 0: log("WARN: pipeline HUD not found (already removed?).")
src = new_src

# 2) Ensure imports (folderPortalService + useAuth)
imp_svc = "import folderPortalService from '" + rel_import(PAGE_DIR, svc_path) + "';"
if "folderPortalService" not in src:
    src = re.sub(r"(\n)(export default)", r"\1" + imp_svc + r"\n\2", src, count=1)
if "useAuth" not in src:
    if not useauth_hook: log("ABORT: useAuth not found."); sys.exit(1)
    src = re.sub(r"(\n)(export default)", r"\1import { useAuth } from '" + rel_import(PAGE_DIR, useauth_hook) + "';\n\2", src, count=1)

# 3) Insert FolderExtras component before export default
EXTRAS = '''
function FolderExtras({ id, toast }) {
  const auth = useAuth();
  const role = String(auth?.user?.role || auth?.role || "").toUpperCase();
  const isAdmin = role.includes("ADMIN") || role.includes("PROGRAMMER");
  const isDirector = isAdmin || role.includes("DIRECTOR");
  const isManager = isDirector || role.includes("MANAGER");
  const canMoney = isDirector, canEdit = isManager;
  const [data, setData] = useState(null);
  const [portfolio, setPortfolio] = useState([]);
  const [fee, setFee] = useState(""); const [deadline, setDeadline] = useState("");
  const load = async () => { try {
    const [d, p] = await Promise.all([folderPortalService.getReceivable(id), folderPortalService.getPortfolio(id)]);
    setData(d); setPortfolio(p); setFee(d.rate ? String(d.rate) : ""); setDeadline(d.deadline ? String(d.deadline).slice(0,16) : "");
  } catch (e) { toast && toast("Failed to load receivables", "error"); } };
  useEffect(() => { load(); }, [id]);
  if (!data) return null;
  return (<>
    <section className={styles.hwPanel} aria-label="Receivables and Portfolio">
      <div className={styles.panelBody + " " + styles.bodyOpen}><div className={styles.panelInner}>
        <h3 className={styles.xTitle}>RECEIVABLES</h3>
        {data.backlog && <span className={styles.badgeBacklog}>BACKLOG — NOT TITLED</span>}
        {data.receivable && <span className={styles.badgeRecv}>IN RECEIVABLES</span>}
        <div className={styles.xGrid}>
          <div><label>Actual Debt</label><strong>UGX {Number(data.actual).toLocaleString()}</strong></div>
          <div><label>Storage Fees</label><strong>UGX {Number(data.storage).toLocaleString()}</strong></div>
          <div><label>Total Owed</label><strong>UGX {Number(data.total).toLocaleString()}</strong></div>
        </div>
        {canMoney && (<div className={styles.xRow}>
          <input type="number" value={fee} onChange={e=>setFee(e.target.value)} placeholder="Monthly rate (default 50000)" />
          <input type="datetime-local" value={deadline} onChange={e=>setDeadline(e.target.value)} />
          <button className={styles.btnGhost} onClick={async()=>{ setData(await folderPortalService.settings(id,{rate:fee,deadline:deadline})); toast&&toast("Settings saved");}}>Save Settings</button>
        </div>)}
        <div className={styles.xRow}>
          {!data.receivable
            ? canEdit && <button className={styles.btnPrimary} onClick={async()=>{ setData(await folderPortalService.enter(id)); toast&&toast("Moved to receivables");}}>Add to Receivables</button>
            : canMoney && (<>
                <button className={styles.btnGhost} onClick={async()=>{ setData(await folderPortalService.exit(id,"SET_ASIDE")); toast&&toast("Set aside");}}>Set Aside</button>
                <button className={styles.btnGhost} onClick={async()=>{ setData(await folderPortalService.exit(id,"CAPITALIZE")); toast&&toast("Fees capitalized");}}>Capitalize</button>
                <button className={styles.btnDanger} onClick={async()=>{ setData(await folderPortalService.exit(id,"WAIVE")); toast&&toast("Fees waived");}}>Waive</button>
              </>)}
        </div>
        <h3 className={styles.xTitle}>OWNER PORTFOLIO</h3>
        {portfolio.length === 0 ? <p className={styles.xEmpty}>No other projects for these owners.</p> : (
          <table className={styles.xTable}><thead><tr><th>#</th><th>Plot</th><th>Owner</th><th>Status</th></tr></thead>
          <tbody>{portfolio.map((r,i)=>(<tr key={i}><td>{r.index}</td><td>{r.plot||"—"}</td><td>{r.sharedOwner}</td><td>{r.receivable?"RECEIVABLE":(r.titled?"TITLED":"BACKLOG")}</td></tr>))}</tbody></table>
        )}
      </div></div>
    </section>
  </>);
}
'''
src = re.sub(r"(\n)(export default)", r"\1" + EXTRAS + r"\2", src, count=1)

# 4) Mount <FolderExtras> before the Stage Checklist section (verbatim anchor)
anchor = '<section className={styles.hwPanel} aria-label="Stage Checklist"'
if anchor in src:
    src = src.replace(anchor, '<FolderExtras id={id} toast={toast} />\n                ' + anchor, 1)
    log("FRONTEND: FolderExtras mounted.")
else:
    log("ABORT: Stage Checklist anchor not found — refusing to guess."); sys.exit(1)

write(folder_jsx, src)
log("FRONTEND: FolderPage.jsx transformed.")

# ---------- FRONTEND: append CSS ----------
css = read(folder_css)
css += '''
/* Folder redesign tokens */
.xTitle{font-family:Cinzel,serif;color:var(--navy,#0b1f3a);margin:14px 0 8px;letter-spacing:.06em}
.badgeBacklog{background:#7c2d12;color:#fff;border-radius:4px;padding:2px 8px;font-size:11px;margin-right:6px}
.badgeRecv{background:#b91c1c;color:#fff;border-radius:4px;padding:2px 8px;font-size:11px}
.xGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0}
.xGrid label{display:block;font-size:11px;color:#64748b}
.xRow{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.xRow input{border:1px solid #cbd5e1;border-radius:6px;padding:6px 8px;font-family:'Space Mono',monospace}
.btnPrimary{background:#f97316;color:#fff;border:none;border-radius:6px;padding:8px 12px;cursor:pointer}
.btnGhost{background:transparent;border:1px solid #0b1f3a;color:#0b1f3a;border-radius:6px;padding:8px 12px;cursor:pointer}
.btnDanger{background:#b91c1c;color:#fff;border:none;border-radius:6px;padding:8px 12px;cursor:pointer}
.xEmpty{color:#64748b;font-size:13px}
.xTable{width:100%;border-collapse:collapse;font-size:13px}
.xTable th,.xTable td{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left}
'''
write(folder_css, css)
log("FRONTEND: CSS appended.")

# ---------- GIT ----------
try:
    subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","Folder page redesign: receivables panel, portfolio, backlog badge, remove pipeline HUD"],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    log("GIT: committed and pushed.")
except Exception as e:
    log("GIT WARN: " + str(e))

log("DONE. Review the diff; backups are in .fix_backup/")
print("\n".join(report))