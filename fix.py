# fix.py -- fix120: Client Ledger page (Ledger formatting, client rows) + sidebar entry under Recovery + backend aggregate endpoint
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules"

PAGE = FE / "pages" / "Clients" / "ClientLedgerPage.jsx"
CSS = FE / "pages" / "Clients" / "ClientLedgerPage.module.css"
APP = FE / "App.jsx"
SVC = FE / "services" / "recoveryService.js"
CTRL = BE / "client" / "controller" / "RecoveryNoteController.java"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)
def find(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]: return i
    return -1

PAGE_JSX = """// PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUsers, FiSearch, FiX, FiPhoneCall, FiChevronDown, FiShield, FiMapPin } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './ClientLedgerPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const FILTERS = [
  { key: 'ALL', label: 'ALL CLIENTS' },
  { key: 'OWING', label: 'OWING' },
  { key: 'RECEIVABLES', label: 'IN RECEIVABLES' },
  { key: 'PAID', label: 'PAID UP' },
  { key: 'NOPLOTS', label: 'NO PLOTS' },
];

const ClientLedgerPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = String(user?.role || '').toUpperCase();
  const isRoot = !!user?.isRoot;
  const isAdmin = isRoot || role === 'ROLE_ADMIN';
  const isDirector = isAdmin || role === 'ROLE_DIRECTOR';
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [term, setTerm] = useState('');
  const [filter, setFilter] = useState('ALL');
  const [openId, setOpenId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await recoveryService.getClientLedger() || []); setLoadError(false); }
    catch { setLoadError(true); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    const t = term.toLowerCase().replace(/\\s+/g, '');
    return rows.filter(c => {
      if (t) {
        const hay = [c.name, c.nin, c.phone, ...(c.plots || []).map(p => String(p.plot))].join(' ').toLowerCase().replace(/\\s+/g, '');
        if (hay.indexOf(t) < 0) return false;
      }
      const owed = Number(c.owed || 0);
      const hasRec = (c.plots || []).some(p => p.receivable);
      if (filter === 'OWING') return owed > 0;
      if (filter === 'RECEIVABLES') return hasRec;
      if (filter === 'PAID') return (c.plotCount || 0) > 0 && owed <= 0;
      if (filter === 'NOPLOTS') return (c.plotCount || 0) === 0;
      return true;
    });
  }, [rows, term, filter]);

  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Client Ledger</h1>
          <p className={styles.subtitle}>Every client - identity, plots and live balance in one register</p>
        </div>
      </header>
      <div className={styles.searchBlock}>
        <div className={styles.searchWrap}>
          <FiSearch className={styles.searchIcon} aria-hidden="true" />
          <input className={styles.searchInput} value={term} onChange={e => setTerm(e.target.value)} placeholder="Search name, NIN, phone or plot..." aria-label="Search clients" />
          {term && <button type="button" className={styles.clearBtn} onClick={() => setTerm('')} aria-label="Clear search"><FiX aria-hidden="true" /></button>}
        </div>
        <div className={styles.filterRow}>
          {FILTERS.map(f => (<button key={f.key} type="button" className={`${styles.filterBtn} ${filter === f.key ? styles.filterBtnActive : ''}`} onClick={() => setFilter(f.key)}>{f.label}</button>))}
          <span className={styles.recordCount}>{filtered.length} CLIENT{filtered.length === 1 ? '' : 'S'}</span>
        </div>
      </div>
      {loading ? (<div className={styles.emptyState}><span>LOADING CLIENT REGISTER...</span></div>)
        : loadError ? (<div className={styles.emptyState}><span>COULD NOT LOAD CLIENTS - REFRESH TO RETRY</span></div>)
        : filtered.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO CLIENTS MATCH THIS VIEW</span></div>)
        : (
          <div className={styles.tableWrap}>
            <table className={styles.ledgerTable}>
              <thead>
                <tr>
                  <th>CLIENT</th><th>NIN</th><th>CONTACT</th><th>PLOTS</th><th>STATUS</th>
                  {isDirector && <th>OWED (UGX)</th>}
                  {isDirector && <th>PAID (UGX)</th>}
                  <th>LAST CONTACT</th><th>RELIABILITY</th><th aria-label="expand" />
                </tr>
              </thead>
              <tbody>
                {filtered.map(c => {
                  const open = openId === c.id;
                  const recCount = (c.plots || []).filter(p => p.receivable).length;
                  const titledCount = (c.plots || []).filter(p => p.titled && !p.receivable).length;
                  const folderCount = (c.plots || []).filter(p => !p.titled).length;
                  return (<React.Fragment key={c.id}>
                    <tr className={`${styles.row} ${open ? styles.rowOpen : ''}`} onClick={() => setOpenId(open ? null : c.id)} tabIndex={0}
                      onKeyDown={e => { if (e.key === 'Enter') setOpenId(open ? null : c.id); }}>
                      <td><span className={styles.clientName}>{c.name}</span></td>
                      <td><span className={styles.mono}>{c.nin || '---'}</span></td>
                      <td><span className={styles.mono}>{c.phone || '---'}</span></td>
                      <td>{c.plotCount || 0}</td>
                      <td>
                        <span className={styles.badgeCell}>
                          {recCount > 0 && <span className={`${styles.textBadge} ${styles.badgeRecv}`}>REC {recCount}</span>}
                          {titledCount > 0 && <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED {titledCount}</span>}
                          {folderCount > 0 && <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>FOLDER {folderCount}</span>}
                          {(c.plotCount || 0) === 0 && <span className={`${styles.textBadge} ${styles.badgeIdle}`}>NO PLOT</span>}
                        </span>
                      </td>
                      {isDirector && <td><span className={`${styles.mono} ${Number(c.owed) > 0 ? styles.moneyRed : styles.moneyGreen}`}>{fmt(c.owed)}</span></td>}
                      {isDirector && <td><span className={styles.mono}>{fmt(c.paid)}</span></td>}
                      <td>{c.lastContact ? String(c.lastContact).slice(0, 10) : 'NEVER'}{c.lastTag ? <span className={`${styles.toneDot} ${c.lastTone === 'POSITIVE' ? styles.tonePos : styles.toneNeg}`} title={c.lastTag} /> : null}</td>
                      <td><span className={styles.mono}>{c.reliability != null ? Number(c.reliability).toFixed(0) : '---'}</span></td>
                      <td><FiChevronDown className={`${styles.chev} ${open ? styles.chevOpen : ''}`} aria-hidden="true" /></td>
                    </tr>
                    {open && (
                      <tr className={styles.detailRow}>
                        <td colSpan={isDirector ? 10 : 8}>
                          <div className={styles.detailBox}>
                            <div className={styles.detailHead}>
                              <span><FiShield aria-hidden="true" /> {c.email || 'no email'}</span>
                              <button type="button" className={styles.jumpBtn} onClick={e => { e.stopPropagation(); navigate('/recovery'); }}><FiPhoneCall aria-hidden="true" /> OPEN IN RECOVERY</button>
                            </div>
                            {(c.plots || []).length === 0 ? (<span className={styles.detailEmpty}>NO PLOTS REGISTERED FOR THIS CLIENT</span>) : (
                              <div className={styles.plotList}>
                                {(c.plots || []).map((p, i) => (
                                  <button key={i} type="button" className={styles.plotRow} onClick={e => { e.stopPropagation(); navigate('/folder/' + p.projectId); }}>
                                    <span className={styles.plotName}>{p.plot || 'UNTITLED'}</span>
                                    <span className={styles.plotDistrict}><FiMapPin aria-hidden="true" /> {p.district || '---'}</span>
                                    <span className={`${styles.textBadge} ${p.receivable ? styles.badgeRecv : p.titled ? styles.badgeTitled : styles.badgeBacklog}`}>{p.receivable ? 'RECEIVABLE' : p.titled ? 'TITLED' : 'FOLDER'}</span>
                                    {isDirector && <span className={`${styles.mono} ${Number(p.owed) > 0 ? styles.moneyRed : styles.moneyGreen}`}>{fmt(p.owed)}</span>}
                                    <span className={styles.plotGo}>OPEN FOLDER</span>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>);
                })}
              </tbody>
            </table>
          </div>
        )}
      <BackToTopButton />
    </div>
  );
};
export default ClientLedgerPage;
"""

PAGE_CSS = """/* PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.module.css */
/* fix120: Client Ledger - Project Ledger formatting applied to client rows */
.container {
  --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981; --amber: #f59e0b;
  --panel-bg: linear-gradient(160deg,#1c3335 0%,#213E40 100%);
  --radius: 10px; --radius-sm: 6px;
  --fs-h1: clamp(18px,2.5vw,24px); --fs-sub: clamp(9px,0.9vw,11px);
  padding: clamp(16px,3vw,32px) clamp(14px,3vw,40px) 60px;
  min-height: 100vh; background: transparent;
}
.pageHeader { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: clamp(10px,1.6vw,18px); }
.title { font-family: 'Cinzel', serif; font-size: var(--fs-h1); color: #fff; letter-spacing: 1px; text-shadow: 0 0 12px rgba(238,140,58,0.35); }
.subtitle { font-family: 'DM Sans', sans-serif; font-size: var(--fs-sub); color: rgba(255,255,255,0.55); letter-spacing: 0.6px; margin-top: 4px; }
.searchBlock { position: sticky; top: 64px; z-index: 30; background: rgba(26,46,48,0.92); backdrop-filter: blur(6px); border: 1px solid var(--orange-border); border-radius: var(--radius); padding: clamp(8px,1.2vw,14px); display: flex; flex-direction: column; gap: 8px; margin-bottom: clamp(10px,1.6vw,16px); }
.searchWrap { position: relative; display: flex; align-items: center; }
.searchIcon { position: absolute; left: 10px; color: var(--orange); font-size: 14px; }
.searchInput { width: 100%; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.15); border-radius: var(--radius-sm); color: #fff; font-family: 'DM Sans', sans-serif; font-size: 13px; padding: 9px 32px 9px 32px; }
.searchInput:focus { outline: none; border-color: var(--orange); }
.clearBtn { position: absolute; right: 8px; background: none; border: none; color: rgba(255,255,255,0.6); cursor: pointer; display: flex; }
.clearBtn:hover { color: #fff; }
.filterRow { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.filterBtn { font-family: 'DM Sans', sans-serif; font-size: 9px; font-weight: 800; letter-spacing: 1px; padding: 6px 10px; border-radius: var(--radius-sm); border: 1px solid rgba(255,255,255,0.15); background: transparent; color: rgba(255,255,255,0.65); cursor: pointer; transition: all .2s; }
.filterBtn:hover { border-color: var(--orange-border); color: #fff; }
.filterBtnActive { background: var(--orange); border-color: var(--orange); color: #1a2e30; }
.recordCount { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 9px; color: rgba(255,255,255,0.5); letter-spacing: 1px; }
.tableWrap { border: 1px solid var(--orange-border); border-radius: var(--radius); overflow-x: auto; background: var(--panel-bg); }
.ledgerTable { width: 100%; border-collapse: collapse; min-width: 760px; }
.ledgerTable th { font-family: 'DM Sans', sans-serif; font-size: 8px; font-weight: 800; letter-spacing: 1.2px; color: var(--orange); text-align: left; padding: 10px 10px; border-bottom: 1px solid var(--orange-border); }
.ledgerTable td { font-family: 'DM Sans', sans-serif; font-size: 12px; color: rgba(255,255,255,0.85); padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); vertical-align: middle; }
.row { cursor: pointer; transition: background .15s; }
.row:hover { background: rgba(238,140,58,0.06); }
.rowOpen { background: rgba(238,140,58,0.09); }
.clientName { font-weight: 800; color: #fff; letter-spacing: 0.4px; }
.mono { font-family: 'Space Mono', monospace; font-size: 11px; letter-spacing: 0.4px; }
.moneyRed { color: var(--red); font-weight: 700; }
.moneyGreen { color: var(--green); font-weight: 700; }
.badgeCell { display: flex; gap: 4px; flex-wrap: wrap; }
.textBadge { font-family: 'DM Sans', sans-serif; font-size: 8px; font-weight: 800; letter-spacing: 0.8px; padding: 3px 6px; border-radius: 4px; }
.badgeRecv { background: rgba(239,68,68,0.16); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
.badgeTitled { background: rgba(16,185,129,0.14); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.35); }
.badgeBacklog { background: rgba(245,158,11,0.14); color: #fcd34d; border: 1px solid rgba(245,158,11,0.35); }
.badgeIdle { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.15); }
.toneDot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-left: 6px; vertical-align: middle; }
.tonePos { background: var(--green); box-shadow: 0 0 6px rgba(16,185,129,0.7); }
.toneNeg { background: var(--red); box-shadow: 0 0 6px rgba(239,68,68,0.7); }
.chev { color: var(--orange); transition: transform .2s; font-size: 14px; }
.chevOpen { transform: rotate(180deg); }
.detailRow td { background: rgba(0,0,0,0.18); padding: 12px; }
.detailBox { display: flex; flex-direction: column; gap: 10px; }
.detailHead { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-family: 'DM Sans', sans-serif; font-size: 11px; color: rgba(255,255,255,0.6); }
.detailHead svg { color: var(--orange); margin-right: 6px; vertical-align: -2px; }
.jumpBtn { font-family: 'DM Sans', sans-serif; font-size: 9px; font-weight: 800; letter-spacing: 1px; padding: 7px 12px; border-radius: var(--radius-sm); border: 1px solid var(--orange-border); background: transparent; color: var(--orange); cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all .2s; }
.jumpBtn:hover { background: var(--orange); color: #1a2e30; border-color: var(--orange); }
.plotList { display: flex; flex-direction: column; gap: 6px; }
.plotRow { display: flex; align-items: center; gap: 12px; width: 100%; text-align: left; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: 9px 12px; cursor: pointer; transition: border-color .2s; }
.plotRow:hover { border-color: var(--orange-border); }
.plotName { font-family: 'Space Mono', monospace; font-weight: 700; font-size: 12px; color: #fff; min-width: 90px; }
.plotDistrict { font-size: 10px; color: rgba(255,255,255,0.55); display: inline-flex; align-items: center; gap: 4px; flex: 1; }
.plotGo { margin-left: auto; font-size: 8px; font-weight: 800; letter-spacing: 1px; color: var(--orange); }
.detailEmpty { font-size: 10px; letter-spacing: 1px; color: rgba(255,255,255,0.45); font-weight: 700; }
.emptyState { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 48px 0; color: rgba(255,255,255,0.5); font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 800; letter-spacing: 1.2px; }
.emptyIcon { font-size: 26px; color: rgba(238,140,58,0.5); }
@media (max-width: 700px) {
  .searchBlock { top: 56px; }
  .ledgerTable { min-width: 600px; }
  .ledgerTable th { font-size: 7px; }
  .ledgerTable td { padding: 8px; }
  .filterBtn { padding: 6px 8px; font-size: 8px; }
}
"""

write(PAGE, PAGE_JSX)
write(CSS, PAGE_CSS)

# ---------- route + import in App.jsx ----------
al = read(APP).split("\n")
i = find(al, "import RecoveryPortal from './pages/Recovery/RecoveryPortal';")
if i >= 0 and 'ClientLedgerPage' not in "\n".join(al):
    al.insert(i + 1, "import ClientLedgerPage from './pages/Clients/ClientLedgerPage';")
    print("OK App import")
else:
    print("SKIP App import")
i = find(al, '{ path: "recovery", element:')
if i >= 0 and '{ path: "clients"' not in "\n".join(al):
    indent = al[i][:len(al[i]) - len(al[i].lstrip())]
    al.insert(i + 1, indent + '{ path: "clients", element: <ProtectedRoute><Shell><ClientLedgerPage /></Shell></ProtectedRoute> },')
    print("OK App route")
else:
    print("SKIP App route")
write(APP, "\n".join(al))

# ---------- service function ----------
sl = read(SVC).split("\n")
if 'getClientLedger' not in "\n".join(sl):
    i = find(sl, 'getNotes: (clientId) =>')
    if i >= 0:
        sl.insert(i + 1, "getClientLedger: () => api.get('/recovery/clients/ledger').then(r => r.data),")
        write(SVC, "\n".join(sl))
        print("OK recoveryService getClientLedger")
    else:
        print("MISSING recoveryService getNotes anchor")
else:
    print("SKIP recoveryService getClientLedger already present")

# ---------- sidebar entry directly under Recovery (clone the recovery nav line) ----------
sidebar = None
for cand in [FE / "components" / "layout" / "Sidebar.jsx", FE / "components" / "Sidebar.jsx"]:
    if cand.exists():
        sidebar = cand
        break
if sidebar is None:
    print("MISSING Sidebar.jsx (tell David the path)")
else:
    sb = read(sidebar).split("\n")
    if "'/clients'" in "\n".join(sb) or '"/clients"' in "\n".join(sb):
        print("SKIP sidebar clients entry already present")
    else:
        i = find(sb, '/recovery')
        if i < 0:
            print("MISSING sidebar recovery anchor")
        else:
            anchor = sb[i]
            newl = anchor
            for a, b in [('/recovery', '/clients'), ('FiPhoneCall', 'FiUsers'), ('FiPhone', 'FiUsers'), ('Recovery', 'Clients'), ('RECOVERY', 'CLIENTS'), ('recovery', 'clients')]:
                newl = newl.replace(a, b)
            sb.insert(i + 1, newl)
            if 'FiUsers' not in "\n".join(sb):
                j = find(sb, "react-icons/fi")
                if j >= 0:
                    sb[j] = sb[j].replace('FiPhoneCall', 'FiPhoneCall, FiUsers', 1)
                    print("OK sidebar FiUsers import")
            write(sidebar, "\n".join(sb))
            print("OK sidebar clients entry under recovery")

# ---------- backend aggregate endpoint ----------
cs = read(CTRL)
if '/clients/ledger' not in cs:
    cl = cs.split("\n")
    idx = len(cl) - 1
    while idx >= 0 and cl[idx].strip() != '}':
        idx -= 1
    if idx < 0:
        print("MISSING controller class close")
    else:
        block = """@GetMapping("/clients/ledger")
@PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_SECRETARY','ROLE_ADMIN','ROLE_DIRECTOR')")
@org.springframework.transaction.annotation.Transactional(readOnly = true)
public java.util.List<java.util.Map<String, Object>> clientLedger() {
java.util.Map<java.util.UUID, java.util.List<com.gesolutions.erp.modules.land.model.LandProject>> pm = new java.util.HashMap<>();
for (com.gesolutions.erp.modules.land.model.LandProject p : projectRepo.findAll()) {
if (p.getProprietors() == null) continue;
for (com.gesolutions.erp.modules.client.model.Client o : p.getProprietors()) {
if (o == null || o.getId() == null) continue;
pm.computeIfAbsent(o.getId(), k -> new java.util.ArrayList<>()).add(p);
}
}
java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
for (com.gesolutions.erp.modules.client.model.Client c : clientRepo.findAll()) {
java.util.List<com.gesolutions.erp.modules.land.model.LandProject> ps = pm.getOrDefault(c.getId(), java.util.List.of());
java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
m.put("id", c.getId());
m.put("name", c.getFullName());
m.put("nin", c.getNationalId());
m.put("phone", c.getPhoneNumber());
m.put("email", c.getEmail());
m.put("reliability", c.getReliabilityScore());
m.put("lastContact", c.getLastContactedAt() == null ? null : c.getLastContactedAt().toString());
java.math.BigDecimal owed = java.math.BigDecimal.ZERO;
java.math.BigDecimal paid = java.math.BigDecimal.ZERO;
java.math.BigDecimal storage = java.math.BigDecimal.ZERO;
java.util.List<java.util.Map<String, Object>> plots = new java.util.ArrayList<>();
for (com.gesolutions.erp.modules.land.model.LandProject p : ps) {
java.math.BigDecimal o = p.isReceivable() ? p.receivableTotalOwed() : p.activeTotalOwed();
owed = owed.add(o);
paid = paid.add(p.getAmountPaid() == null ? java.math.BigDecimal.ZERO : p.getAmountPaid());
storage = storage.add(p.getStorageFeesAccumulated() == null ? java.math.BigDecimal.ZERO : p.getStorageFeesAccumulated());
java.util.Map<String, Object> row = new java.util.LinkedHashMap<>();
row.put("projectId", p.getId());
row.put("plot", p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null ? p.getLandTitle().getPlotNumber() : p.getProjectIndex());
row.put("district", p.getDistrict());
row.put("receivable", p.isReceivable());
row.put("titled", p.getLandTitle() != null);
row.put("legacy", p.isLegacy());
row.put("owed", o);
plots.add(row);
}
m.put("plots", plots);
m.put("plotCount", ps.size());
m.put("owed", owed);
m.put("paid", paid);
m.put("storage", storage);
java.util.List<com.gesolutions.erp.modules.client.model.RecoveryNote> ns = noteRepo.findByClientOrderByCreatedAtDesc(c);
m.put("lastTag", ns.isEmpty() ? null : ns.get(0).getTag());
m.put("lastTone", ns.isEmpty() ? null : ns.get(0).getTone());
out.add(m);
}
out.sort((a, b) -> String.valueOf(a.get("name")).compareToIgnoreCase(String.valueOf(b.get("name"))));
return out;
}""".split("\n")
        cl[idx:idx] = block
        write(CTRL, "\n".join(cl))
        print("OK backend /recovery/clients/ledger endpoint")
else:
    print("SKIP backend ledger endpoint already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix120: Client Ledger page (Ledger formatting for clients) + sidebar entry under Recovery + /recovery/clients/ledger aggregate endpoint"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")