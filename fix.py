# fix.py -- fix126: Client Ledger redo (row click -> dedicated portfolio) + new ClientPortfolioPage + dossier endpoint
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules"
CLP = FE / "pages" / "Clients" / "ClientLedgerPage.jsx"
CLCSS = FE / "pages" / "Clients" / "ClientLedgerPage.module.css"
CPP = FE / "pages" / "Clients" / "ClientPortfolioPage.jsx"
CPPCSS = FE / "pages" / "Clients" / "ClientPortfolioPage.module.css"
APP = FE / "App.jsx"
SVC = FE / "services" / "recoveryService.js"
CTRL = BE / "client" / "controller" / "RecoveryNoteController.java"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding="utf-8", newline="") as f: f.write(s)
    print("WROTE", p.name)
def find(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]: return i
    return -1

# ================= 1. CLIENT LEDGER REDO =================
LEDGER_JSX = """// PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUsers, FiSearch, FiX } from 'react-icons/fi';
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
  { color: '#10b981', label: 'Paid up' },
  { color: '#f59e0b', label: 'Folder stage' },
  { color: '#94a3b8', label: 'No plots' },
];
const Pins = () => (<React.Fragment>
  <span className={`${styles.pins} ${styles.pinsTop}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
  <span className={`${styles.pins} ${styles.pinsBottom}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
  <span className={styles.cornerBl} aria-hidden="true" />
  <span className={styles.cornerBr} aria-hidden="true" />
</React.Fragment>);

const ClientLedgerPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = String(user?.role || '').toUpperCase();
  const isDirector = !!user?.isRoot || role === 'ROLE_ADMIN' || role === 'ROLE_DIRECTOR';
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [loadCode, setLoadCode] = useState('');
  const [term, setTerm] = useState('');
  const [filter, setFilter] = useState('ALL');

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await recoveryService.getClientLedger() || []); setLoadError(false); setLoadCode(''); }
    catch (err) { setLoadError(true); setLoadCode(err && err.response ? 'HTTP ' + err.response.status : 'NETWORK'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    const t = term.toLowerCase().replace(/\\s+/g, '');
    return rows.filter(c => {
      if (t) {
        const hay = [c.name, c.nin, c.phone, c.email, ...(c.plots || []).map(p => String(p.plot))].join(' ').toLowerCase().replace(/\\s+/g, '');
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
          <p className={styles.subtitle}>Every client — click a row for the full portfolio dossier</p>
        </div>
      </header>
      <div className={styles.controlHub}>
        <div className={styles.searchBlock}>
          <div className={styles.searchWrap}>
            <FiSearch className={styles.searchIcon} aria-hidden="true" />
            <input type="search" className={styles.searchInput} value={term} onChange={e => setTerm(e.target.value)}
              placeholder="Search name, NIN, phone or plot..." aria-label="Search clients" autoComplete="off" />
            {term && (<button type="button" className={styles.clearBtn} onClick={() => setTerm('')} aria-label="Clear search"><FiX aria-hidden="true" /></button>)}
          </div>
        </div>
        <div className={styles.filterRow}>
          {FILTERS.map(f => (<button key={f.key} type="button" className={`${styles.filterBtn} ${filter === f.key ? styles.filterBtnActive : ''}`} onClick={() => setFilter(f.key)}>{f.label}</button>))}
        </div>
        <div className={styles.legendRow} aria-label="Client status legend">
          {LEGEND.map(l => (<span key={l.label} className={styles.legendItem}><i className={styles.legendDot} style={{ background: l.color }} /> {l.label}</span>))}
        </div>
      </div>
      <div className={styles.tablePanel}>
        <Pins />
        <div className={styles.tableScroll}>
          <table className={styles.ledgerTable}>
            <thead>
              <tr>
                <th>#</th><th>Client</th><th>NIN</th><th>Contact</th><th>Plots</th><th>Status</th>
                {isDirector && <th>Owed (UGX)</th>}
                {isDirector && <th>Paid (UGX)</th>}
                <th>Last contact</th><th>Reliability</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (<tr><td colSpan={cols} className={styles.noRecords}>SYNCING CLIENT REGISTER...</td></tr>)
                : loadError ? (<tr><td colSpan={cols} className={styles.noRecords}>COULD NOT LOAD CLIENTS {loadCode ? '(' + loadCode + ') ' : ''}— REFRESH TO RETRY</td></tr>)
                : filtered.length === 0 ? (<tr><td colSpan={cols} className={styles.noRecords}><FiUsers className={styles.noRecordsIcon} aria-hidden="true" />NO CLIENTS MATCH THIS VIEW</td></tr>)
                : filtered.map((c, i) => {
                  const recCount = (c.plots || []).filter(p => p.receivable).length;
                  const titledCount = (c.plots || []).filter(p => p.titled && !p.receivable).length;
                  const folderCount = (c.plots || []).filter(p => !p.titled).length;
                  return (
                    <tr key={c.id} className={styles.row} onClick={() => navigate('/client/' + c.id)} tabIndex={0}
                      title="Click to open client portfolio"
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/client/' + c.id); } }}>
                      <td><span className={styles.mono}>{i + 1}</span></td>
                      <td><span className={styles.clientName}>{c.name}</span><span className={styles.subLine}>{c.email || 'no email'}</span></td>
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
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
        <footer className={styles.tableFoot}>
          <span className={styles.footCount}>SHOWING {filtered.length} OF {rows.length} CLIENTS</span>
          <span className={styles.footCount}>CLICK A CLIENT FOR THE FULL PORTFOLIO</span>
        </footer>
      </div>
      <BackToTopButton />
    </div>
  );
};
export default ClientLedgerPage;
"""

LEDGER_CSS = """/* PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.module.css */
/* fix126: redo - verbatim Project Ledger metrics, row click opens portfolio */
.container {
  --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981; --amber: #f59e0b;
  --panel-bg: linear-gradient(160deg,#1c3335 0%,#213E40 100%);
  --radius: 10px; --radius-sm: 6px;
  --fs-h1: clamp(18px,2.5vw,26px); --fs-sub: clamp(8px,0.85vw,10px);
  display: flex; flex-direction: column; gap: clamp(10px,1.5vw,18px);
  padding: clamp(16px,3vw,32px) clamp(14px,3vw,40px) 60px;
  min-height: 100vh; background: transparent; box-sizing: border-box;
}
.pageHeader {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
  gap: clamp(10px,1.4vw,16px); margin-bottom: clamp(14px,2vw,24px);
  border-left: clamp(3px,0.4vw,5px) solid var(--orange);
  padding: clamp(10px,1.4vw,16px) clamp(16px,2.2vw,28px);
  background: rgba(255,255,255,0.62); border-radius: 0 12px 12px 0;
  backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; text-align: left; }
.title { font-family: 'Cinzel', serif; font-size: var(--fs-h1); color: #1a2e30; letter-spacing: 2px; margin: 0; }
.subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }
.controlHub { display: flex; flex-direction: column; gap: clamp(6px,0.9vw,10px); }
.searchBlock { position: sticky; top: 64px; z-index: 30; padding: clamp(8px,1vw,12px) 0; }
.searchWrap {
  position: relative; display: flex; align-items: center;
  background: #fff; border: 1.5px solid #c8d6d7; border-radius: var(--radius-sm);
  height: clamp(36px,4.5vw,44px); max-width: clamp(300px,50vw,560px);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.searchWrap:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.searchIcon { position: absolute; left: 10px; color: var(--orange); font-size: 14px; flex-shrink: 0; }
.searchInput {
  background: transparent; border: none; outline: none; width: 100%; height: 100%;
  box-sizing: border-box; color: #1a2e30;
  padding: 0 clamp(10px,1.2vw,14px) 0 clamp(36px,4.5vw,44px);
  font-family: 'DM Sans', sans-serif; font-weight: 800; font-size: clamp(11px,1.1vw,13px);
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.clearBtn { position: absolute; right: 8px; background: none; border: none; color: rgba(26,46,48,0.35); cursor: pointer; display: flex; }
.clearBtn:hover { color: #1a2e30; }
.filterRow { display: flex; flex-wrap: wrap; gap: clamp(6px,0.9vw,10px); align-items: center; }
.filterBtn {
  background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85);
  padding: clamp(7px,0.9vw,9px) clamp(12px,1.5vw,18px); border-radius: 6px;
  font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px,0.95vw,11px);
  letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
}
.filterBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.filterBtnActive { background: #EE8C3A !important; color: #1a2e30 !important; border-color: #EE8C3A !important; box-shadow: 0 0 14px rgba(238,140,58,0.4); }
.filterBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.legendRow { display: flex; flex-wrap: nowrap; gap: 14px; padding: 4px 0 2px clamp(6px,1vw,12px); overflow-x: auto; scrollbar-width: none; }
.legendRow::-webkit-scrollbar { display: none; }
.legendItem { display: inline-flex; align-items: center; gap: 6px; font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: rgba(26,46,48,0.65); white-space: nowrap; flex-shrink: 0; }
.legendDot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; box-shadow: none; }
.tablePanel { position: relative; background: var(--panel-bg); border: 1.5px solid var(--orange-border); border-radius: var(--radius); }
.pins { position: absolute; display: flex; gap: 7px; pointer-events: none; }
.pinsTop { top: -3px; left: 50%; transform: translateX(-50%); }
.pinsBottom { bottom: -3px; left: 50%; transform: translateX(-50%); }
.pin { width: 3px; height: 5px; background: var(--orange); }
.cornerBl, .cornerBr { position: absolute; width: clamp(10px,1.4vw,14px); height: clamp(10px,1.4vw,14px); border-bottom: 1.5px solid rgba(255,255,255,0.35); pointer-events: none; }
.cornerBl { bottom: 8px; left: 8px; border-left: 1.5px solid rgba(255,255,255,0.35); border-radius: 0 0 0 6px; }
.cornerBl::after { content: ''; position: absolute; width: 5px; height: 5px; background: white; border-radius: 50%; bottom: -3px; left: -3px; box-shadow: 0 0 6px rgba(255,255,255,0.4); }
.cornerBr { bottom: 8px; right: 8px; border-right: 1.5px solid rgba(255,255,255,0.35); border-radius: 0 0 6px 0; }
.cornerBr::after { content: ''; position: absolute; width: 5px; height: 5px; background: white; border-radius: 50%; bottom: -3px; right: -3px; box-shadow: 0 0 6px rgba(255,255,255,0.4); }
.tableScroll { overflow-x: auto; border-radius: var(--radius); scrollbar-width: none; transform: translateZ(0); }
.tableScroll::-webkit-scrollbar { display: none; width: 0; height: 0; }
.ledgerTable { width: 100%; border-collapse: separate; border-spacing: 0; font-size: clamp(11px,1.2vw,13px); min-width: 760px; }
.ledgerTable thead th {
  background: #162a2c; text-align: left;
  padding: clamp(9px,1.2vw,13px) clamp(10px,1.5vw,16px);
  font-family: 'DM Sans', sans-serif; font-size: clamp(8px,0.9vw,10px); font-weight: 900;
  letter-spacing: 2px; color: var(--orange); text-transform: uppercase;
  border-bottom: 3px solid var(--orange); white-space: nowrap;
}
.ledgerTable tbody td {
  padding: clamp(8px,1.1vw,12px) clamp(10px,1.5vw,16px);
  border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle;
  color: rgba(255,255,255,0.85); font-family: 'DM Sans', sans-serif;
}
.row { cursor: pointer; border-left: 3px solid transparent; transition: background 0.18s, border-left-color 0.18s; }
.row:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.row:focus-visible { background: rgba(238,140,58,0.07); outline: 2px solid var(--orange); outline-offset: -2px; }
.clientName { display: block; font-weight: 900; color: #ffffff; font-size: clamp(12px,1.4vw,15px); letter-spacing: 0.4px; }
.subLine { display: block; font-family: 'Space Mono', monospace; font-size: clamp(9px,1vw,11px); color: rgba(255,255,255,0.4); margin-top: 2px; }
.mono { font-family: 'Space Mono', monospace; font-size: clamp(10px,1.1vw,12px); color: rgba(255,255,255,0.6); }
.moneyRed { color: #fca5a5; font-weight: 900; }
.moneyGreen { color: #22c55e; font-weight: 900; }
.badgeCell { display: flex; gap: 4px; flex-wrap: wrap; }
.textBadge { font-family: 'DM Sans', sans-serif; font-size: clamp(7px,0.85vw,9px); font-weight: 800; letter-spacing: 0.8px; padding: 3px 6px; border-radius: 4px; white-space: nowrap; }
.badgeRecv { background: rgba(239,68,68,0.16); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
.badgeTitled { background: rgba(16,185,129,0.14); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.35); }
.badgeBacklog { background: rgba(245,158,11,0.14); color: #fcd34d; border: 1px solid rgba(245,158,11,0.35); }
.badgeIdle { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.15); }
.toneDot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-left: 6px; vertical-align: middle; }
.tonePos { background: var(--green); box-shadow: 0 0 6px rgba(16,185,129,0.7); }
.toneNeg { background: var(--red); box-shadow: 0 0 6px rgba(239,68,68,0.7); }
.noRecords {
  text-align: center; padding: clamp(40px,6vw,70px) 20px;
  color: rgba(255,255,255,0.22); font-family: 'Space Mono', monospace;
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
}
.noRecordsIcon { display: block; margin: 0 auto 10px; font-size: clamp(30px,5vw,48px); opacity: 0.15; }
.tableFoot { display: flex; justify-content: space-between; align-items: center; padding: 10px clamp(10px,1.5vw,16px) 12px; border-top: 1px solid rgba(255,255,255,0.06); }
.footCount { font-family: 'Space Mono', monospace; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px; color: rgba(255,255,255,0.4); text-transform: uppercase; }
@media (max-width: 700px) {
  .searchBlock { top: 56px; }
  .ledgerTable { min-width: 600px; }
  .ledgerTable thead th { font-size: 7px; letter-spacing: 1px; }
  .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }
}
"""

write(CLP, LEDGER_JSX)
write(CLCSS, LEDGER_CSS)

# ================= 2. CLIENT PORTFOLIO PAGE =================
PORT_JSX = """// PATH: erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiShield, FiClock, FiActivity, FiCreditCard, FiUsers } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './ClientPortfolioPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const dayDiff = (iso) => { if (!iso) return null; const d = new Date(iso); if (isNaN(d.getTime())) return null; return Math.floor((Date.now() - d.getTime()) / 86400000); };
const Pins = () => (<React.Fragment>
  <span className={`${styles.pins} ${styles.pinsTop}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
  <span className={`${styles.pins} ${styles.pinsBottom}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
  <span className={styles.cornerBl} aria-hidden="true" />
  <span className={styles.cornerBr} aria-hidden="true" />
</React.Fragment>);

const ClientPortfolioPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = String(user?.role || '').toUpperCase();
  const isDirector = !!user?.isRoot || role === 'ROLE_ADMIN' || role === 'ROLE_DIRECTOR';
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadCode, setLoadCode] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try { setD(await recoveryService.getClientDossier(id)); setLoadCode(''); }
    catch (err) { setD(null); setLoadCode(err && err.response ? 'HTTP ' + err.response.status : 'NETWORK'); }
    finally { setLoading(false); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  const backBtn = (<button type="button" className={styles.backBtn} onClick={() => navigate('/clients')}><FiArrowLeft aria-hidden="true" /> BACK TO CLIENT LEDGER</button>);

  if (loading) return (<div className={styles.container}><div className={styles.noRecordsBig}>SYNCING CLIENT DOSSIER...</div></div>);
  if (!d) return (<div className={styles.container}>
    <header className={styles.pageHeader}><div className={styles.headerLeft}>
      <h1 className={styles.title}>Client Dossier</h1>
      <p className={styles.subtitle}>Full portfolio, money and call history</p>
    </div>{backBtn}</header>
    <div className={styles.noRecordsBig}>COULD NOT LOAD DOSSIER {loadCode ? '(' + loadCode + ') ' : ''}— REFRESH TO RETRY</div>
  </div>);

  const rel = d.reliability != null ? Number(d.reliability) : null;
  const relClass = rel == null ? styles.badgeIdle : rel >= 80 ? styles.badgeTitled : rel >= 50 ? styles.badgeBacklog : styles.badgeRecv;
  const days = dayDiff(d.lastContact);

  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>{d.name}</h1>
          <p className={styles.subtitle}>Client dossier — every plot, shilling and call in one place</p>
        </div>
        {backBtn}
      </header>

      <section className={styles.panel}>
        <Pins />
        <h2 className={styles.panelTitle}><FiUsers aria-hidden="true" /> IDENTITY</h2>
        <div className={styles.specGrid}>
          <div className={styles.specItem}><span className={styles.specLabel}><FiShield aria-hidden="true" /> NIN</span><span className={styles.specMono}>{d.nin || '---'}</span></div>
          <div className={styles.specItem}><span className={styles.specLabel}><FiPhoneCall aria-hidden="true" /> PHONE</span><span className={styles.specMono}>{d.phone || '---'}</span></div>
          <div className={styles.specItem}><span className={styles.specLabel}><FiMail aria-hidden="true" /> EMAIL</span><span className={styles.specValue}>{d.email || '---'}</span></div>
          <div className={styles.specItem}><span className={styles.specLabel}><FiMapPin aria-hidden="true" /> ADDRESS</span><span className={styles.specValue}>{d.address || '---'}</span></div>
          <div className={styles.specItem}><span className={styles.specLabel}><FiClock aria-hidden="true" /> LAST CONTACT</span><span className={styles.specValue}>{d.lastContact ? String(d.lastContact).slice(0, 10) + (days != null ? ' (' + days + 'D AGO)' : '') : 'NEVER'}</span></div>
          <div className={styles.specItem}><span className={styles.specLabel}><FiActivity aria-hidden="true" /> RELIABILITY</span><span className={`${styles.textBadge} ${relClass}`}>{rel != null ? rel.toFixed(0) : '---'}</span></div>
        </div>
      </section>

      {isDirector && (
        <div className={styles.moneyStrip}>
          <div className={`${styles.statCard} ${styles.statRed}`}><label>TOTAL OWED</label><strong>UGX {fmt(d.totals ? d.totals.owed : 0)}</strong></div>
          <div className={`${styles.statCard} ${styles.statGreen}`}><label>TOTAL PAID</label><strong>UGX {fmt(d.totals ? d.totals.paid : 0)}</strong></div>
          <div className={`${styles.statCard} ${styles.statAmber}`}><label>STORAGE FEES</label><strong>UGX {fmt(d.totals ? d.totals.storage : 0)}</strong></div>
          <div className={styles.statCard}><label>PLOTS</label><strong>{(d.plots || []).length}</strong></div>
        </div>
      )}

      <section className={styles.panel}>
        <Pins />
        <h2 className={styles.panelTitle}><FiMapPin aria-hidden="true" /> PLOT PORTFOLIO</h2>
        <div className={styles.tableScroll}>
          <table className={styles.ledgerTable}>
            <thead><tr><th>Plot</th><th>District</th><th>Status</th>{isDirector && <th>Owed (UGX)</th>}{isDirector && <th>Paid (UGX)</th>}<th /></tr></thead>
            <tbody>
              {(d.plots || []).length === 0 ? (<tr><td colSpan={isDirector ? 6 : 4} className={styles.noRecords}>NO PLOTS REGISTERED</td></tr>) :
                (d.plots || []).map((p, i) => (
                  <tr key={i} className={styles.row} onClick={() => navigate('/folder/' + p.projectId)} tabIndex={0}
                    title="Click to open folder"
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/folder/' + p.projectId); } }}>
                    <td><span className={styles.plotName}>{p.plot || 'UNTITLED'}</span></td>
                    <td>{p.district || '---'}</td>
                    <td><span className={`${styles.textBadge} ${p.receivable ? styles.badgeRecv : p.titled ? styles.badgeTitled : styles.badgeBacklog}`}>{p.receivable ? 'RECEIVABLE' : p.titled ? 'TITLED' : 'FOLDER'}</span></td>
                    {isDirector && <td><span className={`${styles.mono} ${Number(p.owed) > 0 ? styles.moneyRed : styles.moneyGreen}`}>{fmt(p.owed)}</span></td>}
                    {isDirector && <td><span className={styles.mono}>{fmt(p.paid)}</span></td>}
                    <td><span className={styles.plotGo}>OPEN FOLDER</span></td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      {isDirector && (
        <section className={styles.panel}>
          <Pins />
          <h2 className={styles.panelTitle}><FiCreditCard aria-hidden="true" /> PAYMENT HEALTH PER PLOT</h2>
          <div className={styles.tableScroll}>
            <table className={styles.ledgerTable}>
              <thead><tr><th>Plot</th><th>Paid (UGX)</th><th>Storage (UGX)</th><th>Last payment</th><th>Health</th></tr></thead>
              <tbody>
                {(d.plots || []).length === 0 ? (<tr><td colSpan={5} className={styles.noRecords}>NO PAYMENT RECORDS</td></tr>) :
                  (d.plots || []).map((p, i) => {
                    const dd = dayDiff(p.lastPayment);
                    const health = dd == null ? { c: styles.dotGrey, t: 'No payment yet' } : dd <= 30 ? { c: styles.dotGreen, t: 'Paid within 30 days' } : dd <= 90 ? { c: styles.dotAmber, t: 'Paid 1-3 months ago' } : { c: styles.dotRed, t: 'No recent payment' };
                    return (<tr key={i} className={styles.rowStatic}>
                      <td><span className={styles.plotName}>{p.plot || 'UNTITLED'}</span></td>
                      <td><span className={styles.mono}>{fmt(p.paid)}</span></td>
                      <td><span className={styles.mono}>{fmt(p.storage)}</span></td>
                      <td><span className={styles.mono}>{p.lastPayment ? String(p.lastPayment).slice(0, 10) : 'NEVER'}</span></td>
                      <td><span className={styles.healthCell}><i className={`${styles.legendDot} ${health.c}`} /> {health.t}</span></td>
                    </tr>);
                  })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className={styles.panel}>
        <Pins />
        <h2 className={styles.panelTitle}><FiPhoneCall aria-hidden="true" /> CALL LOG</h2>
        {(d.notes || []).length === 0 ? (<div className={styles.noRecords}>NO CALLS LOGGED FOR THIS CLIENT</div>) : (
          <div className={styles.noteList}>
            {(d.notes || []).map((n, i) => (
              <article key={i} className={styles.noteRow}>
                <span className={`${styles.textBadge} ${n.tone === 'POSITIVE' ? styles.badgeTitled : n.tone === 'NEGATIVE' ? styles.badgeRecv : styles.badgeBacklog}`}>{n.tag}</span>
                <span className={styles.noteDate}>{n.createdAt ? String(n.createdAt).slice(0, 10) : '---'}</span>
                <span className={styles.noteAuthor}>{n.author || 'SYSTEM'}</span>
                {n.text && <p className={styles.noteText}>{n.text}</p>}
              </article>
            ))}
          </div>
        )}
      </section>
      <BackToTopButton />
    </div>
  );
};
export default ClientPortfolioPage;
"""

PORT_CSS = """/* PATH: erp-frontend/src/pages/Clients/ClientPortfolioPage.module.css */
/* fix126: client dossier - same Ledger family tokens */
.container {
  --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981; --amber: #f59e0b;
  --panel-bg: linear-gradient(160deg,#1c3335 0%,#213E40 100%);
  --radius: 10px; --radius-sm: 6px;
  --fs-h1: clamp(18px,2.5vw,26px); --fs-sub: clamp(8px,0.85vw,10px);
  display: flex; flex-direction: column; gap: clamp(10px,1.5vw,18px);
  padding: clamp(16px,3vw,32px) clamp(14px,3vw,40px) 60px;
  min-height: 100vh; background: transparent; box-sizing: border-box;
}
.pageHeader {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
  gap: clamp(10px,1.4vw,16px); margin-bottom: clamp(14px,2vw,24px);
  border-left: clamp(3px,0.4vw,5px) solid var(--orange);
  padding: clamp(10px,1.4vw,16px) clamp(16px,2.2vw,28px);
  background: rgba(255,255,255,0.62); border-radius: 0 12px 12px 0;
  backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; text-align: left; }
.title { font-family: 'Cinzel', serif; font-size: var(--fs-h1); color: #1a2e30; letter-spacing: 2px; margin: 0; }
.subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }
.backBtn {
  font-family: 'DM Sans', sans-serif; font-size: clamp(8px,0.9vw,10px); font-weight: 900; letter-spacing: 1.2px;
  padding: clamp(8px,1vw,11px) clamp(12px,1.5vw,18px); border-radius: 6px;
  border: 1.5px solid var(--orange-border); background: transparent; color: #EE8C3A;
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s; text-transform: uppercase;
}
.backBtn:hover { background: #EE8C3A; color: #1a2e30; border-color: #EE8C3A; }
.panel { position: relative; background: var(--panel-bg); border: 1.5px solid var(--orange-border); border-radius: var(--radius); padding: clamp(12px,1.8vw,20px); }
.panelTitle {
  font-family: 'DM Sans', sans-serif; font-size: clamp(9px,1vw,11px); font-weight: 900; letter-spacing: 2px;
  color: var(--orange); text-transform: uppercase; margin: 0 0 clamp(10px,1.4vw,16px);
  display: flex; align-items: center; gap: 8px;
}
.panelTitle svg { font-size: clamp(12px,1.4vw,15px); }
.pins { position: absolute; display: flex; gap: 7px; pointer-events: none; }
.pinsTop { top: -3px; left: 50%; transform: translateX(-50%); }
.pinsBottom { bottom: -3px; left: 50%; transform: translateX(-50%); }
.pin { width: 3px; height: 5px; background: var(--orange); }
.cornerBl, .cornerBr { position: absolute; width: clamp(10px,1.4vw,14px); height: clamp(10px,1.4vw,14px); border-bottom: 1.5px solid rgba(255,255,255,0.35); pointer-events: none; }
.cornerBl { bottom: 8px; left: 8px; border-left: 1.5px solid rgba(255,255,255,0.35); border-radius: 0 0 0 6px; }
.cornerBl::after { content: ''; position: absolute; width: 5px; height: 5px; background: white; border-radius: 50%; bottom: -3px; left: -3px; box-shadow: 0 0 6px rgba(255,255,255,0.4); }
.cornerBr { bottom: 8px; right: 8px; border-right: 1.5px solid rgba(255,255,255,0.35); border-radius: 0 0 6px 0; }
.cornerBr::after { content: ''; position: absolute; width: 5px; height: 5px; background: white; border-radius: 50%; bottom: -3px; right: -3px; box-shadow: 0 0 6px rgba(255,255,255,0.4); }
.specGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(clamp(160px,22vw,240px), 1fr)); gap: clamp(8px,1.2vw,14px); }
.specItem { display: flex; flex-direction: column; gap: 4px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: clamp(8px,1.1vw,12px); }
.specLabel { display: inline-flex; align-items: center; gap: 6px; font-family: 'DM Sans', sans-serif; font-size: clamp(7px,0.85vw,9px); font-weight: 900; letter-spacing: 1.5px; color: rgba(255,255,255,0.45); text-transform: uppercase; }
.specLabel svg { color: var(--orange); }
.specValue { font-family: 'DM Sans', sans-serif; font-size: clamp(11px,1.2vw,13px); font-weight: 700; color: rgba(255,255,255,0.85); word-break: break-word; }
.specMono { font-family: 'Space Mono', monospace; font-size: clamp(10px,1.1vw,12px); color: rgba(255,255,255,0.75); word-break: break-word; }
.moneyStrip { display: grid; grid-template-columns: repeat(auto-fit, minmax(clamp(140px,18vw,200px), 1fr)); gap: clamp(8px,1.2vw,14px); }
.statCard { background: var(--panel-bg); border: 1.5px solid var(--orange-border); border-radius: var(--radius); padding: clamp(10px,1.4vw,16px); display: flex; flex-direction: column; gap: 6px; }
.statCard label { font-family: 'DM Sans', sans-serif; font-size: clamp(7px,0.85vw,9px); font-weight: 900; letter-spacing: 1.5px; color: rgba(255,255,255,0.45); text-transform: uppercase; }
.statCard strong { font-family: 'Space Mono', monospace; font-size: clamp(13px,1.8vw,19px); color: #ffffff; }
.statRed strong { color: #fca5a5; }
.statGreen strong { color: #22c55e; }
.statAmber strong { color: #fcd34d; }
.tableScroll { overflow-x: auto; scrollbar-width: none; transform: translateZ(0); }
.tableScroll::-webkit-scrollbar { display: none; width: 0; height: 0; }
.ledgerTable { width: 100%; border-collapse: separate; border-spacing: 0; font-size: clamp(11px,1.2vw,13px); min-width: 560px; }
.ledgerTable thead th {
  background: #162a2c; text-align: left;
  padding: clamp(9px,1.2vw,13px) clamp(10px,1.5vw,16px);
  font-family: 'DM Sans', sans-serif; font-size: clamp(8px,0.9vw,10px); font-weight: 900;
  letter-spacing: 2px; color: var(--orange); text-transform: uppercase;
  border-bottom: 3px solid var(--orange); white-space: nowrap;
}
.ledgerTable tbody td {
  padding: clamp(8px,1.1vw,12px) clamp(10px,1.5vw,16px);
  border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle;
  color: rgba(255,255,255,0.85); font-family: 'DM Sans', sans-serif;
}
.row { cursor: pointer; border-left: 3px solid transparent; transition: background 0.18s, border-left-color 0.18s; }
.row:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.row:focus-visible { background: rgba(238,140,58,0.07); outline: 2px solid var(--orange); outline-offset: -2px; }
.rowStatic { border-left: 3px solid transparent; }
.plotName { font-family: 'Space Mono', monospace; font-weight: 900; font-size: clamp(11px,1.2vw,13px); color: #fff; }
.plotGo { font-size: clamp(7px,0.85vw,9px); font-weight: 900; letter-spacing: 1px; color: var(--orange); text-transform: uppercase; }
.mono { font-family: 'Space Mono', monospace; font-size: clamp(10px,1.1vw,12px); color: rgba(255,255,255,0.6); }
.moneyRed { color: #fca5a5; font-weight: 900; }
.moneyGreen { color: #22c55e; font-weight: 900; }
.textBadge { font-family: 'DM Sans', sans-serif; font-size: clamp(7px,0.85vw,9px); font-weight: 800; letter-spacing: 0.8px; padding: 3px 6px; border-radius: 4px; white-space: nowrap; }
.badgeRecv { background: rgba(239,68,68,0.16); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
.badgeTitled { background: rgba(16,185,129,0.14); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.35); }
.badgeBacklog { background: rgba(245,158,11,0.14); color: #fcd34d; border: 1px solid rgba(245,158,11,0.35); }
.badgeIdle { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.15); }
.healthCell { display: inline-flex; align-items: center; gap: 6px; font-size: clamp(9px,1vw,11px); font-weight: 700; color: rgba(255,255,255,0.6); white-space: nowrap; }
.legendDot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; box-shadow: none; }
.dotGreen { background: #10b981; }
.dotAmber { background: #f59e0b; }
.dotRed { background: #ef4444; }
.dotGrey { background: #94a3b8; }
.noteList { display: flex; flex-direction: column; gap: 8px; }
.noteRow { display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: clamp(8px,1.1vw,12px); }
.noteDate { font-family: 'Space Mono', monospace; font-size: clamp(9px,1vw,11px); color: rgba(255,255,255,0.5); }
.noteAuthor { font-family: 'DM Sans', sans-serif; font-size: clamp(9px,1vw,11px); font-weight: 700; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.8px; }
.noteText { width: 100%; margin: 2px 0 0; font-family: 'DM Sans', sans-serif; font-size: clamp(11px,1.2vw,13px); color: rgba(255,255,255,0.8); }
.noRecords {
  text-align: center; padding: clamp(30px,5vw,50px) 20px;
  color: rgba(255,255,255,0.22); font-family: 'Space Mono', monospace;
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
}
.noRecordsBig {
  margin: clamp(40px,8vw,90px) auto; max-width: clamp(320px,60vw,560px);
  text-align: center; padding: clamp(30px,5vw,50px) 20px;
  background: var(--panel-bg); border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  color: rgba(255,255,255,0.35); font-family: 'Space Mono', monospace;
  font-size: clamp(9px,1vw,11px); font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
}
@media (max-width: 700px) {
  .ledgerTable { min-width: 480px; }
  .ledgerTable thead th { font-size: 7px; letter-spacing: 1px; }
}
"""

write(CPP, PORT_JSX)
write(CPPCSS, PORT_CSS)

# ================= 3. route + import =================
al = read(APP).split("\n")
if 'ClientPortfolioPage' not in "\n".join(al):
    i = find(al, "import ClientLedgerPage from './pages/Clients/ClientLedgerPage';")
    if i >= 0:
        al.insert(i + 1, "import ClientPortfolioPage from './pages/Clients/ClientPortfolioPage';")
        print("OK App import ClientPortfolioPage")
    else:
        print("MISSING App ClientLedgerPage import anchor")
    j = find(al, '{ path: "clients", element:')
    if j >= 0:
        indent = al[j][:len(al[j]) - len(al[j].lstrip())]
        al.insert(j + 1, indent + '{ path: "client/:id", element: <ProtectedRoute><Shell><ClientPortfolioPage /></Shell></ProtectedRoute> },')
        print("OK App route client/:id")
    else:
        print("MISSING App clients route anchor")
    write(APP, "\n".join(al))
else:
    print("SKIP App portfolio wiring already present")

# ================= 4. service functions (with fallback anchors) =================
s = read(SVC)
added = False
if 'getClientLedger' not in s:
    sl = s.split("\n")
    i = find(sl, 'getNotes:')
    if i < 0: i = find(sl, 'const recoveryService = {')
    if i >= 0:
        sl.insert(i + 1, "getClientLedger: () => api.get('/recovery/clients/ledger').then(r => r.data),")
        s = "\n".join(sl); added = True
        print("OK recoveryService getClientLedger inserted")
    else:
        print("MISSING recoveryService anchor for getClientLedger")
else:
    print("SKIP getClientLedger already present")
if 'getClientDossier' not in s:
    sl = s.split("\n")
    i = find(sl, 'getClientLedger:')
    if i < 0: i = find(sl, 'getNotes:')
    if i < 0: i = find(sl, 'const recoveryService = {')
    if i >= 0:
        sl.insert(i + 1, "getClientDossier: (clientId) => api.get('/recovery/clients/' + clientId + '/dossier').then(r => r.data),")
        s = "\n".join(sl); added = True
        print("OK recoveryService getClientDossier inserted")
    else:
        print("MISSING recoveryService anchor for getClientDossier")
else:
    print("SKIP getClientDossier already present")
if added:
    write(SVC, s)

# ================= 5. backend dossier endpoint =================
cs = read(CTRL)
if '/clients/{id}/dossier' not in cs:
    cl = cs.split("\n")
    idx = len(cl) - 1
    while idx >= 0 and cl[idx].strip() != '}':
        idx -= 1
    if idx < 0:
        print("MISSING controller class close")
    else:
        block = """@GetMapping("/clients/{id}/dossier")
@PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_SECRETARY','ROLE_ADMIN','ROLE_DIRECTOR')")
@org.springframework.transaction.annotation.Transactional(readOnly = true)
public java.util.Map<String, Object> clientDossier(@PathVariable UUID id) {
java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
com.gesolutions.erp.modules.client.model.Client c = clientRepo.findById(id).orElseThrow(() -> new RuntimeException("Client not found"));
out.put("id", c.getId());
out.put("name", c.getFullName());
out.put("nin", c.getNationalId());
out.put("phone", c.getPhoneNumber());
out.put("email", c.getEmail());
out.put("address", c.getHomeAddress());
out.put("reliability", c.getReliabilityScore());
out.put("lastContact", c.getLastContactedAt() == null ? null : c.getLastContactedAt().toString());
out.put("monthlyContacts", c.getMonthlyContactCount());
java.util.List<java.util.Map<String, Object>> plots = new java.util.ArrayList<>();
java.math.BigDecimal owed = java.math.BigDecimal.ZERO;
java.math.BigDecimal paid = java.math.BigDecimal.ZERO;
java.math.BigDecimal storage = java.math.BigDecimal.ZERO;
for (com.gesolutions.erp.modules.land.model.LandProject p : projectRepo.findAll()) {
if (p.getProprietors() == null) continue;
boolean mine = false;
for (com.gesolutions.erp.modules.client.model.Client o : p.getProprietors()) { if (o != null && id.equals(o.getId())) { mine = true; break; } }
if (!mine) continue;
java.math.BigDecimal o1 = p.isReceivable() ? p.receivableTotalOwed() : p.activeTotalOwed();
java.math.BigDecimal p1 = p.getAmountPaid() == null ? java.math.BigDecimal.ZERO : p.getAmountPaid();
java.math.BigDecimal s1 = p.getStorageFeesAccumulated() == null ? java.math.BigDecimal.ZERO : p.getStorageFeesAccumulated();
owed = owed.add(o1); paid = paid.add(p1); storage = storage.add(s1);
java.util.Map<String, Object> pm = new java.util.LinkedHashMap<>();
pm.put("projectId", p.getId());
pm.put("plot", p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null ? p.getLandTitle().getPlotNumber() : p.getProjectIndex());
pm.put("district", p.getDistrict());
pm.put("receivable", p.isReceivable());
pm.put("titled", p.getLandTitle() != null);
pm.put("legacy", p.isLegacy());
pm.put("owed", o1); pm.put("paid", p1); pm.put("storage", s1);
pm.put("lastPayment", p.getLastPaymentDate() == null ? null : p.getLastPaymentDate().toString());
plots.add(pm);
}
out.put("plots", plots);
java.util.Map<String, Object> totals = new java.util.LinkedHashMap<>();
totals.put("owed", owed); totals.put("paid", paid); totals.put("storage", storage);
out.put("totals", totals);
java.util.List<java.util.Map<String, Object>> notes = new java.util.ArrayList<>();
for (com.gesolutions.erp.modules.client.model.RecoveryNote n : noteRepo.findByClientOrderByCreatedAtDesc(c)) {
java.util.Map<String, Object> nm2 = new java.util.LinkedHashMap<>();
nm2.put("id", n.getId()); nm2.put("tag", n.getTag()); nm2.put("tone", n.getTone()); nm2.put("text", n.getText());
nm2.put("author", n.getAuthor() == null ? null : n.getAuthor().getUsername());
nm2.put("createdAt", n.getCreatedAt() == null ? null : n.getCreatedAt().toString());
notes.add(nm2);
}
out.put("notes", notes);
return out;
}""".split("\n")
        cl[idx:idx] = block
        write(CTRL, "\n".join(cl))
        print("OK backend /clients/{id}/dossier endpoint")
else:
    print("SKIP backend dossier endpoint already present")
if '/clients/ledger' not in cs:
    print("WARNING backend /clients/ledger endpoint missing - tell David now")
else:
    print("OK backend /clients/ledger endpoint present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix126: Client Ledger redo (row click opens dossier) + ClientPortfolioPage + /clients/{id}/dossier endpoint"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")