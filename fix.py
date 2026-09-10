# fix.py -- fix122: split project INDEX from PLOT number + SOLO/JOINT ownership on the client dossier
#
# 1. BACKEND (RecoveryNoteController): the client ledger and the client dossier
#    both collapsed two different identifiers into one "plot" field -- the plot
#    number when a title existed, otherwise the project index as a stand-in.
#    That hides the single-identity model (guide 8.2 / 8.3): the project index
#    is permanent and always present, the plot number only exists once a title
#    is produced. Both endpoints now emit BOTH fields: "index" (always) and
#    "plot" (null until titled).
# 2. BACKEND: dossier plots now carry ownership info the same way
#    RecoveryController.buildOwnerTasks does -- "ownershipType" (SOLO / JOINT)
#    plus a "coOwners" list of {clientId, fullName} for the other proprietors,
#    so the portfolio can say whether a project is individual or joint and link
#    straight to the co-owner's dossier.
# 3. FRONTEND (ClientPortfolioPage): rebuilt around that split. INDEX is the
#    primary identifier column, PLOT is its own column showing the plot number
#    when titled and a muted placeholder when not. Rows are grouped SOLO first
#    then JOINT, each row carries a one-word ownership badge, and joint rows
#    render navigable co-owner chips (same treatment as RecoveryPortal).
#    Director totals are recomputed from the per-project owed/paid/storage,
#    de-duplicated by projectId so a joint project can never be counted twice.
# 4. FRONTEND (ClientLedgerPage): the ledger list rows fall back to the index
#    now that "plot" is null for untitled projects (search + plot stack).
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

CPP = FE / "pages" / "Clients" / "ClientPortfolioPage.jsx"
CPCSS = FE / "pages" / "Clients" / "ClientPortfolioPage.module.css"
CLP = FE / "pages" / "Clients" / "ClientLedgerPage.jsx"
RNC = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"


def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("WROTE", p)


def patch(p, old, new, label):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        s = f.read()
    if old not in s:
        print(("SKIP already applied" if new in s else "MISSING"), label, "->", p)
        return
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s.replace(old, new, 1))
    print("OK", label)


# ---------------------------------------------------------------- BACKEND ----
patch(
    RNC,
    'row.put("plot", p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null ? p.getLandTitle().getPlotNumber() : p.getProjectIndex());',
    'row.put("index", p.getProjectIndex());\n'
    'row.put("plot", p.getLandTitle() == null ? null : p.getLandTitle().getPlotNumber());',
    "clientLedger index/plot split",
)

patch(
    RNC,
    'pm.put("plot", p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null ? p.getLandTitle().getPlotNumber() : p.getProjectIndex());',
    'pm.put("index", p.getProjectIndex());\n'
    'pm.put("plot", p.getLandTitle() == null ? null : p.getLandTitle().getPlotNumber());',
    "clientDossier index/plot split",
)

patch(
    RNC,
    'pm.put("lastPayment", p.getLastPaymentDate() == null ? null : p.getLastPaymentDate().toString());\n'
    'plots.add(pm);',
    'pm.put("lastPayment", p.getLastPaymentDate() == null ? null : p.getLastPaymentDate().toString());\n'
    'java.util.Set<com.gesolutions.erp.modules.client.model.Client> owners = p.getProprietors();\n'
    'pm.put("ownershipType", owners != null && owners.size() > 1 ? "JOINT" : "SOLO");\n'
    'java.util.List<java.util.Map<String, Object>> coOwners = new java.util.ArrayList<>();\n'
    'if (owners != null) {\n'
    'for (com.gesolutions.erp.modules.client.model.Client co : owners) {\n'
    'if (co == null || co.getId() == null || id.equals(co.getId())) continue;\n'
    'java.util.Map<String, Object> cm = new java.util.LinkedHashMap<>();\n'
    'cm.put("clientId", co.getId());\n'
    'cm.put("fullName", co.getFullName());\n'
    'coOwners.add(cm);\n'
    '}\n'
    '}\n'
    'pm.put("coOwners", coOwners);\n'
    'plots.add(pm);',
    "clientDossier ownershipType + coOwners",
)

# ------------------------------------------------------- CLIENT LEDGER LIST --
patch(
    CLP,
    "        ...(c.plots || []).map(p => p.plot),",
    "        ...(c.plots || []).map(p => p.index),\n"
    "        ...(c.plots || []).map(p => p.plot),",
    "ClientLedger search includes index",
)

patch(
    CLP,
    "const plotNums = (c.plots || []).map(p => p.plot).filter(Boolean);",
    "const plotNums = (c.plots || []).map(p => p.plot || p.index).filter(Boolean);",
    "ClientLedger plot stack falls back to index",
)

# ------------------------------------------------------ CLIENT PORTFOLIO -----
PORTFOLIO_JSX = r"""// PATH: erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiShield, FiClock, FiActivity, FiCreditCard, FiUsers, FiUser } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './ClientPortfolioPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const dayDiff = (iso) => { if (!iso) return null; const d = new Date(iso); if (isNaN(d.getTime())) return null; return Math.floor((Date.now() - d.getTime()) / 86400000); };
const isJoint = (p) => String(p.ownershipType || 'SOLO').toUpperCase() === 'JOINT';

const Pins = () => (<React.Fragment>
  <span className={`${styles.pins} ${styles.pinsTop}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
  <span className={`${styles.pins} ${styles.pinsBottom}`} aria-hidden="true"><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /><i className={styles.pin} /></span>
  <span className={styles.cornerBl} aria-hidden="true" />
  <span className={styles.cornerBr} aria-hidden="true" />
</React.Fragment>);

// -- IDENTIFIER CELLS --
// The project index exists from the day the record is created and never
// changes (single-identity model). The plot number only exists once a title
// has actually been produced, so it stays visibly empty until then instead of
// silently borrowing the index.
const IndexCell = ({ p }) => (<span className={styles.plotName}>{p.index || '---'}</span>);
const PlotCell = ({ p }) => (p.plot
  ? <span className={styles.plotName}>{p.plot}</span>
  : <span className={styles.plotEmpty}>-- (no title yet)</span>);

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

  const plots = useMemo(() => (d && Array.isArray(d.plots) ? d.plots : []), [d]);

  // Every project this client holds appears exactly once in the dossier list,
  // joint or not, so the roll-up is a plain sum over that list -- keyed by
  // projectId purely as a guard against a duplicate row ever reaching here.
  const totals = useMemo(() => {
    const seen = new Set();
    const t = { owed: 0, paid: 0, storage: 0, count: 0, solo: 0, joint: 0 };
    plots.forEach((p) => {
      const key = p.projectId || p.index;
      if (key && seen.has(key)) return;
      if (key) seen.add(key);
      t.owed += Number(p.owed || 0);
      t.paid += Number(p.paid || 0);
      t.storage += Number(p.storage || 0);
      t.count += 1;
      if (isJoint(p)) t.joint += 1; else t.solo += 1;
    });
    return t;
  }, [plots]);

  const groups = useMemo(() => ([
    { key: 'SOLO', label: 'SOLO PROJECTS', rows: plots.filter((p) => !isJoint(p)) },
    { key: 'JOINT', label: 'JOINT PROJECTS', rows: plots.filter(isJoint) },
  ].filter((g) => g.rows.length > 0)), [plots]);

  const backBtn = (<button type="button" className={styles.backBtn} onClick={() => navigate('/clients')}><FiArrowLeft aria-hidden="true" /> BACK TO CLIENT LEDGER</button>);

  if (loading) return (<div className={styles.container}><div className={styles.noRecordsBig}>SYNCING CLIENT DOSSIER...</div></div>);
  if (!d) return (<div className={styles.container}>
    <header className={styles.pageHeader}><div className={styles.headerLeft}>
      <h1 className={styles.title}>Client Dossier</h1>
      <p className={styles.subtitle}>Full portfolio, money and call history</p>
    </div>{backBtn}</header>
    <div className={styles.noRecordsBig}>COULD NOT LOAD DOSSIER {loadCode ? '(' + loadCode + ') ' : ''}- REFRESH TO RETRY</div>
  </div>);

  const rel = d.reliability != null ? Number(d.reliability) : null;
  const relClass = rel == null ? styles.badgeIdle : rel >= 80 ? styles.badgeTitled : rel >= 50 ? styles.badgeBacklog : styles.badgeRecv;
  const days = dayDiff(d.lastContact);
  const cols = isDirector ? 8 : 6;

  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>{d.name}</h1>
          <p className={styles.subtitle}>Client dossier - every project, shilling and call in one place</p>
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
          <div className={`${styles.statCard} ${styles.statRed}`}><label>TOTAL OWED</label><strong>UGX {fmt(totals.owed)}</strong></div>
          <div className={`${styles.statCard} ${styles.statGreen}`}><label>TOTAL PAID</label><strong>UGX {fmt(totals.paid)}</strong></div>
          <div className={`${styles.statCard} ${styles.statAmber}`}><label>STORAGE FEES</label><strong>UGX {fmt(totals.storage)}</strong></div>
          <div className={styles.statCard}><label>PROJECTS</label><strong>{totals.count}</strong><span className={styles.statNote}>{totals.solo} SOLO / {totals.joint} JOINT</span></div>
        </div>
      )}

      <section className={styles.panel}>
        <Pins />
        <h2 className={styles.panelTitle}><FiMapPin aria-hidden="true" /> PLOT PORTFOLIO</h2>
        <div className={styles.tableScroll}>
          <table className={styles.ledgerTable}>
            <thead><tr><th>Index</th><th>Plot</th><th>District</th><th>Ownership</th><th>Status</th>{isDirector && <th>Owed (UGX)</th>}{isDirector && <th>Paid (UGX)</th>}<th /></tr></thead>
            <tbody>
              {plots.length === 0 ? (<tr><td colSpan={cols} className={styles.noRecords}>NO PROJECTS REGISTERED</td></tr>) :
                groups.map((g) => (
                  <React.Fragment key={g.key}>
                    <tr className={styles.groupRow}><td colSpan={cols}>{g.label} ({g.rows.length})</td></tr>
                    {g.rows.map((p, i) => (
                      <tr key={p.projectId || g.key + i} className={styles.row} onClick={() => navigate('/folder/' + p.projectId)} tabIndex={0}
                        title="Click to open folder"
                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/folder/' + p.projectId); } }}>
                        <td><IndexCell p={p} /></td>
                        <td><PlotCell p={p} /></td>
                        <td>{p.district || '---'}</td>
                        <td>
                          <span className={`${styles.textBadge} ${isJoint(p) ? styles.badgeJoint : styles.badgeIdle}`}>{isJoint(p) ? 'JOINT' : 'SOLO'}</span>
                          {(p.coOwners || []).length > 0 && (
                            <span className={styles.coLine}>
                              <FiUser aria-hidden="true" /> with:
                              {(p.coOwners || []).map((co) => (
                                <button key={co.clientId} type="button" className={styles.coChip}
                                  onClick={(e) => { e.stopPropagation(); navigate('/client/' + co.clientId); }}>
                                  {co.fullName || 'UNNAMED'}
                                </button>
                              ))}
                            </span>
                          )}
                        </td>
                        <td><span className={`${styles.textBadge} ${p.receivable ? styles.badgeRecv : p.titled ? styles.badgeTitled : styles.badgeBacklog}`}>{p.receivable ? 'RECEIVABLE' : p.titled ? 'TITLED' : 'FOLDER'}</span></td>
                        {isDirector && <td><span className={`${styles.mono} ${Number(p.owed) > 0 ? styles.moneyRed : styles.moneyGreen}`}>{fmt(p.owed)}</span></td>}
                        {isDirector && <td><span className={styles.mono}>{fmt(p.paid)}</span></td>}
                        <td><span className={styles.plotGo}>OPEN FOLDER</span></td>
                      </tr>
                    ))}
                  </React.Fragment>
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
              <thead><tr><th>Index / Plot</th><th>Paid (UGX)</th><th>Storage (UGX)</th><th>Last payment</th><th>Health</th></tr></thead>
              <tbody>
                {plots.length === 0 ? (<tr><td colSpan={5} className={styles.noRecords}>NO PAYMENT RECORDS</td></tr>) :
                  plots.map((p, i) => {
                    const dd = dayDiff(p.lastPayment);
                    const health = dd == null ? { c: styles.dotGrey, t: 'No payment yet' } : dd <= 30 ? { c: styles.dotGreen, t: 'Paid within 30 days' } : dd <= 90 ? { c: styles.dotAmber, t: 'Paid 1-3 months ago' } : { c: styles.dotRed, t: 'No recent payment' };
                    return (<tr key={p.projectId || i} className={styles.rowStatic}>
                      <td>
                        <span className={styles.idStack}>
                          <IndexCell p={p} />
                          <PlotCell p={p} />
                        </span>
                      </td>
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

PORTFOLIO_CSS_ADD = r"""
/* fix122: index / plot split + SOLO-JOINT grouping */
.plotEmpty { font-family: 'DM Sans', sans-serif; font-size: clamp(9px,1vw,11px); font-weight: 700; color: rgba(255,255,255,0.32); white-space: nowrap; }
.idStack { display: flex; flex-direction: column; gap: 2px; }
.groupRow td {
  background: rgba(0,0,0,0.22); border-bottom: 1px solid rgba(238,140,58,0.28);
  font-family: 'DM Sans', sans-serif; font-size: clamp(8px,0.9vw,10px); font-weight: 900;
  letter-spacing: 2px; text-transform: uppercase; color: var(--orange);
  padding: clamp(6px,0.9vw,9px) clamp(10px,1.5vw,16px);
}
.badgeJoint { background: rgba(6,182,212,0.12); color: #67e8f9; border: 1px solid rgba(6,182,212,0.35); }
.coLine { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 5px; font-family: 'DM Sans', sans-serif; font-size: clamp(8px,0.9vw,10px); font-weight: 700; color: rgba(255,255,255,0.45); }
.coLine svg { color: rgba(255,255,255,0.45); font-size: clamp(9px,1vw,11px); flex-shrink: 0; }
.coChip {
  background: none; border: none; padding: 0; cursor: pointer;
  font-family: 'Space Mono', monospace; font-size: clamp(10px,1.1vw,12px); font-weight: 900;
  letter-spacing: 1px; color: #67e8f9; transition: color 0.2s;
}
.coChip:hover { color: #ffffff; }
.coChip:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.statNote { font-family: 'DM Sans', sans-serif; font-size: clamp(7px,0.85vw,9px); font-weight: 900; letter-spacing: 1.2px; color: rgba(255,255,255,0.35); text-transform: uppercase; }
.ledgerTable { min-width: 720px; }
@media (max-width: 700px) { .ledgerTable { min-width: 640px; } }
"""

write(CPP, PORTFOLIO_JSX)

with open(CPCSS, "r", encoding="utf-8", errors="replace") as f:
    _css = f.read()
if "fix122" in _css:
    print("SKIP css already patched")
else:
    write(CPCSS, _css.rstrip("\n") + "\n" + PORTFOLIO_CSS_ADD)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix122: split project index from plot number in client ledger/dossier + SOLO/JOINT ownership on the portfolio page"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")
