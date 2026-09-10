# fix.py -- fix124: Ledger legend indent + Client Ledger rebuilt as exact Ledger visual clone
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
LEDGER_CSS = FE / "pages" / "Ledger" / "LedgerPage.module.css"
CLP = FE / "pages" / "Clients" / "ClientLedgerPage.jsx"
CLCSS = FE / "pages" / "Clients" / "ClientLedgerPage.module.css"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding="utf-8", newline="") as f: f.write(s)
    print("WROTE", p.name)

# ---------- 1. Project Ledger: legend row moves inside like Recovery ----------
s = read(LEDGER_CSS)
if 'fix124' not in s:
    s = s.rstrip("\n") + """
/* fix124: dot-definition legend sits a little inside, matching Recovery dotLegend indent */
.legendRow { padding: 4px 0 2px clamp(6px, 1vw, 12px); }
"""
    write(LEDGER_CSS, s)
    print("OK ledger legend indent")
else:
    print("SKIP ledger legend indent already present")

# ---------- 2. Client Ledger page rebuilt (Ledger visual clone) ----------
PAGE_JSX = """// PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUsers, FiSearch, FiX, FiPhoneCall, FiChevronDown, FiMail, FiMapPin } from 'react-icons/fi';
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
const LEGEND = [
  { color: '#ef4444', label: 'In receivables' },
  { color: '#22c55e', label: 'Paid up' },
  { color: '#f59e0b', label: 'Folder stage' },
  { color: '#94a3b8', label: 'No plots' },
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

  const cols = isDirector ? 10 : 8;

  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Client Ledger</h1>
          <p className={styles.subtitle}>Every client — identity, plots and live balance in one register</p>
        </div>
      </header>
      <div className={styles.controlHub}>
        <div className={styles.searchBlock}>
          <div className={styles.searchInner}>
            <FiSearch className={styles.searchIcon} aria-hidden="true" />
            <input type="search" className={styles.searchInput} value={term} onChange={e => setTerm(e.target.value)}
              placeholder="Search name, NIN, phone or plot..." aria-label="Search clients" autoComplete="off" />
            {term && (<button type="button" className={styles.clearBtn} onClick={() => setTerm('')} aria-label="Clear search"><FiX aria-hidden="true" /></button>)}
          </div>
        </div>
        <div className={styles.filterRow}>
          {FILTERS.map(f => (<button key={f.key} type="button" className={`${styles.filterBtn} ${filter === f.key ? styles.filterBtnActive : ''}`} onClick={() => setFilter(f.key)}>{f.label}</button>))}
          <span className={styles.recordCount}>{filtered.length} CLIENT{filtered.length === 1 ? '' : 'S'}</span>
        </div>
        <div className={styles.legendRow} aria-label="Client status legend">
          {LEGEND.map(l => (<span key={l.label} className={styles.legendItem}><span className={styles.legendDot} style={{ background: l.color, boxShadow: `0 0 4px ${l.color}` }} /> {l.label}</span>))}
        </div>
      </div>
      <div className={styles.tablePanel}>
        <div className={styles.tableScroll}>
          <table className={styles.ledgerTable}>
            <thead>
              <tr>
                <th>Client</th><th>NIN</th><th>Contact</th><th>Plots</th><th>Status</th>
                {isDirector && <th>Owed (UGX)</th>}
                {isDirector && <th>Paid (UGX)</th>}
                <th>Last contact</th><th>Reliability</th><th aria-label="Expand" />
              </tr>
            </thead>
            <tbody>
              {loading ? (<tr><td colSpan={cols} className={styles.emptyCell}>SYNCING CLIENT REGISTER...</td></tr>)
                : loadError ? (<tr><td colSpan={cols} className={styles.emptyCell}>COULD NOT LOAD CLIENTS — REFRESH TO RETRY</td></tr>)
                : filtered.length === 0 ? (<tr><td colSpan={cols} className={styles.emptyCell}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><div>NO CLIENTS MATCH THIS VIEW</div></td></tr>)
                : filtered.map(c => {
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
                      <td>{c.lastContact ? String(c.lastContact).slice(0, 10) : 'NEVER'}{(c.lastTone === 'POSITIVE' || c.lastTone === 'NEGATIVE') ? <span className={`${styles.toneDot} ${c.lastTone === 'NEGATIVE' ? styles.toneNeg : styles.tonePos}`} title={c.lastTag} /> : null}</td>
                      <td><span className={styles.mono}>{c.reliability != null ? Number(c.reliability).toFixed(0) : '---'}</span></td>
                      <td><FiChevronDown className={`${styles.chev} ${open ? styles.chevOpen : ''}`} aria-hidden="true" /></td>
                    </tr>
                    {open && (
                      <tr className={styles.detailRow}>
                        <td colSpan={cols}>
                          <div className={styles.detailBox}>
                            <div className={styles.detailHead}>
                              <span><FiMail aria-hidden="true" /> {c.email || 'no email'}</span>
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
      </div>
      <BackToTopButton />
    </div>
  );
};
export default ClientLedgerPage;
"""

PAGE_CSS = """/* PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.module.css */
/* fix124: exact visual clone of LedgerPage (post fix124 legend indent included) */
.container {
  --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981; --amber: #f59e0b;
  --panel-bg: linear-gradient(160deg,#1c3335 0%,#213E40 100%);
  --radius: 10px; --radius-sm: 6px;
  --fs-h1: clamp(18px,2.5vw,24px); --fs-sub: clamp(9px,0.9vw,11px);
  display: flex; flex-direction: column; gap: clamp(10px,1.5vw,18px);
  padding: clamp(16px,3vw,32px) clamp(14px,3vw,40px) 60px;
  min-height: 100vh; background: transparent; box-sizing: border-box;
}
/* glass page header - verbatim Ledger */
.pageHeader {
  display: flex; justify-content: flex-start; align-items: center; flex-wrap: wrap;
  gap: clamp(8px,1.2vw,14px); margin: 0;
  border-left: clamp(3px,0.4vw,5px) solid var(--orange);
  padding: clamp(10px,1.4vw,16px) clamp(16px,2.2vw,28px);
  background: rgba(255,255,255,0.62); border-radius: 0 12px 12px 0;
  backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; text-align: left; }
.title { font-family: 'Cinzel', serif; font-size: var(--fs-h1); color: #1a2e30; letter-spacing: 1px; margin: 0; }
.subtitle { font-family: 'DM Sans', sans-serif; font-size: var(--fs-sub); font-weight: 700; color: rgba(26,46,48,0.6); letter-spacing: 0.6px; margin: 0; text-transform: uppercase; }
.controlHub { display: flex; flex-direction: column; gap: 8px; }
/* sticky white search - Ledger pattern */
.searchBlock { position: sticky; top: 64px; z-index: 30; }
.searchInner { position: relative; max-width: clamp(240px,32vw,420px); }
.searchIcon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--orange); font-size: 13px; }
.searchInput {
  width: 100%; box-sizing: border-box;
  background: #ffffff; border: 1px solid rgba(26,46,48,0.15); border-radius: 8px;
  padding: 10px 34px 10px 32px;
  font-family: 'DM Sans', sans-serif; font-size: 12px; color: #1a2e30;
}
.searchInput:focus { outline: 2px solid var(--orange); outline-offset: 1px; border-color: var(--orange); }
.searchInput::placeholder { color: rgba(26,46,48,0.4); }
.clearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgba(26,46,48,0.4); cursor: pointer; display: flex; }
.clearBtn:hover { color: #1a2e30; }
/* filter chips - Ledger slate fill, orange active glow */
.filterRow { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filterBtn {
  background: rgba(26,46,48,0.55); color: #ffffff; border: 1px solid transparent;
  border-radius: 6px; padding: 8px 14px;
  font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px,0.95vw,11px);
  letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; white-space: nowrap;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}
.filterBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.filterBtnActive { background: #EE8C3A !important; color: #1a2e30 !important; border-color: #EE8C3A !important; font-weight: 900 !important; box-shadow: 0 0 14px rgba(238,140,58,0.35); }
.filterBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.recordCount { margin-left: auto; color: var(--orange); font-family: 'Space Mono', monospace; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
/* legend row - Ledger rhythm INCLUDING the fix124 inside indent */
.legendRow { display: flex; flex-wrap: nowrap; gap: 14px; padding: 4px 0 2px clamp(6px,1vw,12px); overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none; }
.legendRow::-webkit-scrollbar { display: none; }
.legendItem { display: flex; align-items: center; gap: 6px; font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; color: rgba(26,46,48,0.6); white-space: nowrap; flex-shrink: 0; }
.legendDot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
/* dark table panel - Ledger treatment */
.tablePanel { position: relative; background: var(--panel-bg); border: 1px solid var(--orange-border); border-radius: var(--radius); }
.tableScroll { overflow-x: auto; border-radius: var(--radius); scrollbar-width: none; -ms-overflow-style: none; transform: translateZ(0); }
.tableScroll::-webkit-scrollbar { display: none; width: 0; height: 0; }
.ledgerTable { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 760px; }
.ledgerTable thead th {
  position: sticky; top: 0; z-index: 5;
  background: #162a2c; color: var(--orange); text-align: left;
  padding: clamp(9px,1.3vw,14px) clamp(12px,1.8vw,20px);
  font-family: 'DM Sans', sans-serif; font-size: clamp(8px,0.9vw,10px); font-weight: 900;
  letter-spacing: 1.2px; text-transform: uppercase;
  border-bottom: 3px solid var(--orange);
}
.ledgerTable tbody td {
  padding: clamp(9px,1.3vw,14px) clamp(12px,1.8vw,20px);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.85); font-family: 'DM Sans', sans-serif; font-size: 12px; vertical-align: middle;
}
.row { cursor: pointer; border-left: 3px solid transparent; transition: background 0.15s, border-left-color 0.1s; }
.row:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.row:focus-visible { background: rgba(238,140,58,0.07); outline: 2px solid var(--orange); outline-offset: -2px; }
.rowOpen { background: rgba(238,140,58,0.09); border-left-color: var(--orange); }
.clientName { font-weight: 800; color: #ffffff; letter-spacing: 0.4px; }
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
.chev { color: var(--orange); transition: transform 0.2s; font-size: 14px; }
.chevOpen { transform: rotate(180deg); }
.emptyCell { text-align: center; padding: clamp(20px,4vw,40px) 16px; color: rgba(255,255,255,0.5); font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 800; letter-spacing: 1.2px; }
.emptyIcon { font-size: 26px; color: rgba(238,140,58,0.5); display: block; margin: 0 auto 10px; }
/* expanded detail */
.detailRow td { background: rgba(0,0,0,0.18); padding: 12px clamp(12px,1.8vw,20px); }
.detailBox { display: flex; flex-direction: column; gap: 10px; }
.detailHead { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-family: 'DM Sans', sans-serif; font-size: 11px; color: rgba(255,255,255,0.6); }
.detailHead svg { color: var(--orange); margin-right: 6px; vertical-align: -2px; }
.jumpBtn {
  font-family: 'DM Sans', sans-serif; font-size: 9px; font-weight: 800; letter-spacing: 1px;
  padding: 7px 12px; border-radius: var(--radius-sm);
  border: 1px solid var(--orange-border); background: transparent; color: var(--orange);
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s;
}
.jumpBtn:hover { background: var(--orange); color: #1a2e30; border-color: var(--orange); }
.plotList { display: flex; flex-direction: column; gap: 6px; }
.plotRow {
  display: flex; align-items: center; gap: 12px; width: 100%; text-align: left;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-sm); padding: 9px 12px; cursor: pointer; transition: border-color 0.2s;
}
.plotRow:hover { border-color: var(--orange-border); }
.plotName { font-family: 'Space Mono', monospace; font-weight: 700; font-size: 12px; color: #fff; min-width: 90px; }
.plotDistrict { font-size: 10px; color: rgba(255,255,255,0.55); display: inline-flex; align-items: center; gap: 4px; flex: 1; }
.plotGo { margin-left: auto; font-size: 8px; font-weight: 800; letter-spacing: 1px; color: var(--orange); }
.detailEmpty { font-size: 10px; letter-spacing: 1px; color: rgba(255,255,255,0.45); font-weight: 700; }
@media (max-width: 700px) {
  .searchBlock { top: 56px; }
  .ledgerTable { min-width: 600px; }
  .ledgerTable thead th { font-size: 7px; letter-spacing: 1px; }
  .ledgerTable tbody td { padding: 8px; }
  .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }
}
"""

write(CLP, PAGE_JSX)
write(CLCSS, PAGE_CSS)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix124: Ledger legend indent inside + Client Ledger rebuilt as exact Ledger visual clone"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")