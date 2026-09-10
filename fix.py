# fix.py -- fix125: Client Ledger pixel-matched to Project Ledger (verbatim tokens, pins, corners, hover reactions) + load diagnostics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules"
CLP = FE / "pages" / "Clients" / "ClientLedgerPage.jsx"
CLCSS = FE / "pages" / "Clients" / "ClientLedgerPage.module.css"
SVC = FE / "services" / "recoveryService.js"
CTRL = BE / "client" / "controller" / "RecoveryNoteController.java"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding="utf-8", newline="") as f: f.write(s)
    print("WROTE", p.name)

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
  { color: '#10b981', label: 'Paid up' },
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
  const [loadCode, setLoadCode] = useState('');
  const [term, setTerm] = useState('');
  const [filter, setFilter] = useState('ALL');
  const [openId, setOpenId] = useState(null);

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
          <p className={styles.subtitle}>Every client — identity, plots and live balance in one register</p>
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
        <span className={`${styles.pins} ${styles.pinsTop}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
        <span className={`${styles.pins} ${styles.pinsBottom}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
        <span className={styles.cornerBl} aria-hidden="true" />
        <span className={styles.cornerBr} aria-hidden="true" />
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
              {loading ? (<tr><td colSpan={cols} className={styles.noRecords}>SYNCING CLIENT REGISTER...</td></tr>)
                : loadError ? (<tr><td colSpan={cols} className={styles.noRecords}>COULD NOT LOAD CLIENTS {loadCode ? '(' + loadCode + ') ' : ''}— REFRESH TO RETRY</td></tr>)
                : filtered.length === 0 ? (<tr><td colSpan={cols} className={styles.noRecords}><FiUsers className={styles.noRecordsIcon} aria-hidden="true" />NO CLIENTS MATCH THIS VIEW</td></tr>)
                : filtered.map(c => {
                  const open = openId === c.id;
                  const recCount = (c.plots || []).filter(p => p.receivable).length;
                  const titledCount = (c.plots || []).filter(p => p.titled && !p.receivable).length;
                  const folderCount = (c.plots || []).filter(p => !p.titled).length;
                  return (<React.Fragment key={c.id}>
                    <tr className={`${styles.row} ${open ? styles.rowOpen : ''}`} onClick={() => setOpenId(open ? null : c.id)} tabIndex={0}
                      onKeyDown={e => { if (e.key === 'Enter') setOpenId(open ? null : c.id); }}>
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
        <footer className={styles.tableFoot}>
          <span className={styles.footCount}>SHOWING {filtered.length} OF {rows.length} CLIENTS</span>
          <span className={styles.footCount}>CLIENT REGISTER</span>
        </footer>
      </div>
      <BackToTopButton />
    </div>
  );
};
export default ClientLedgerPage;
"""

PAGE_CSS = """/* PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.module.css */
/* fix125: verbatim Project Ledger tokens - fonts, padding, spacing, hover reactions, card furniture */
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
/* glass page header - verbatim unified panel */
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
/* white search pill - verbatim Ledger searchWrap */
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
/* filter chips - verbatim Ledger/Recovery filterBtn */
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
/* legend row - fix124 indent, flat 8px dots, Ledger type */
.legendRow { display: flex; flex-wrap: nowrap; gap: 14px; padding: 4px 0 2px clamp(6px,1vw,12px); overflow-x: auto; scrollbar-width: none; }
.legendRow::-webkit-scrollbar { display: none; }
.legendItem { display: inline-flex; align-items: center; gap: 6px; font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: rgba(26,46,48,0.65); white-space: nowrap; flex-shrink: 0; }
.legendDot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; box-shadow: none; }
/* dark table card with Ledger furniture: pins + bottom corner brackets */
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
/* table - verbatim Ledger .table metrics */
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
.rowOpen { background: rgba(238,140,58,0.09); border-left-color: var(--orange); }
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
.chev { color: var(--orange); transition: transform 0.3s ease; font-size: clamp(15px,1.8vw,20px); flex-shrink: 0; }
.chevOpen { transform: rotate(180deg); }
/* empty / error - verbatim Ledger noRecords treatment */
.noRecords {
  text-align: center; padding: clamp(40px,6vw,70px) 20px;
  color: rgba(255,255,255,0.22); font-family: 'Space Mono', monospace;
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
}
.noRecordsIcon { display: block; margin: 0 auto 10px; font-size: clamp(30px,5vw,48px); opacity: 0.15; }
/* footer bar - Ledger pagination rhythm */
.tableFoot { display: flex; justify-content: space-between; align-items: center; padding: 10px clamp(10px,1.5vw,16px) 12px; border-top: 1px solid rgba(255,255,255,0.06); }
.footCount { font-family: 'Space Mono', monospace; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px; color: rgba(255,255,255,0.4); text-transform: uppercase; }
/* expanded detail */
.detailRow td { background: rgba(0,0,0,0.18); padding: clamp(10px,1.4vw,16px) clamp(10px,1.5vw,16px); }
.detailBox { display: flex; flex-direction: column; gap: 10px; }
.detailHead { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-family: 'DM Sans', sans-serif; font-size: clamp(10px,1.1vw,12px); color: rgba(255,255,255,0.6); }
.detailHead svg { color: var(--orange); margin-right: 6px; vertical-align: -2px; }
.jumpBtn {
  font-family: 'DM Sans', sans-serif; font-size: clamp(8px,0.9vw,10px); font-weight: 900; letter-spacing: 1px;
  padding: clamp(7px,0.9vw,10px) clamp(12px,1.4vw,16px); border-radius: var(--radius-sm);
  border: 1.5px solid var(--orange-border); background: transparent; color: var(--orange);
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s; text-transform: uppercase;
}
.jumpBtn:hover { background: var(--orange); color: #1a2e30; border-color: var(--orange); }
.plotList { display: flex; flex-direction: column; gap: 6px; }
.plotRow {
  display: flex; align-items: center; gap: 12px; width: 100%; text-align: left;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-sm); padding: clamp(8px,1.1vw,12px) clamp(10px,1.4vw,14px);
  cursor: pointer; transition: border-color 0.2s, background 0.2s;
}
.plotRow:hover { border-color: var(--orange-border); background: rgba(238,140,58,0.06); }
.plotName { font-family: 'Space Mono', monospace; font-weight: 900; font-size: clamp(11px,1.2vw,13px); color: #fff; min-width: 90px; }
.plotDistrict { font-size: clamp(9px,1vw,11px); color: rgba(255,255,255,0.55); display: inline-flex; align-items: center; gap: 4px; flex: 1; }
.plotGo { margin-left: auto; font-size: clamp(7px,0.85vw,9px); font-weight: 900; letter-spacing: 1px; color: var(--orange); text-transform: uppercase; }
.detailEmpty { font-size: clamp(9px,1vw,11px); letter-spacing: 1px; color: rgba(255,255,255,0.45); font-weight: 700; text-transform: uppercase; }
@media (max-width: 700px) {
  .searchBlock { top: 56px; }
  .ledgerTable { min-width: 600px; }
  .ledgerTable thead th { font-size: 7px; letter-spacing: 1px; }
  .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }
}
"""

write(CLP, PAGE_JSX)
write(CLCSS, PAGE_CSS)

# ---------- guards: service function + backend endpoint must exist ----------
s = read(SVC)
if 'getClientLedger' not in s:
    sl = s.split("\n")
    i = -1
    for n, ln in enumerate(sl):
        if 'const recoveryService = {' in ln:
            i = n
            break
    if i >= 0:
        sl.insert(i + 1, "getClientLedger: () => api.get('/recovery/clients/ledger').then(r => r.data),")
        write(SVC, "\n".join(sl))
        print("OK recoveryService getClientLedger inserted")
    else:
        i2 = -1
        for n, ln in enumerate(sl):
            if 'getNotes:' in ln:
                i2 = n
                break
        if i2 >= 0:
            sl.insert(i2 + 1, "getClientLedger: () => api.get('/recovery/clients/ledger').then(r => r.data),")
            write(SVC, "\n".join(sl))
            print("OK recoveryService getClientLedger inserted after getNotes")
        else:
            print("MISSING recoveryService anchor")
else:
    print("SKIP recoveryService getClientLedger already present")

cs = read(CTRL)
if '/clients/ledger' not in cs:
    print("MISSING backend /clients/ledger endpoint - tell David immediately")
else:
    print("OK backend /clients/ledger endpoint present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix125: Client Ledger pixel-matched to Project Ledger (verbatim tokens, pins, corner brackets, hover reactions, footer) + load HTTP diagnostics"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")