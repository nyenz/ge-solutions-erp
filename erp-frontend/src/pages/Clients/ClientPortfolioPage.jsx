// PATH: erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx
// CLIENT DOSSIER v2 -- design + information rethink.
// Visual language now matches the Intake / Client Ledger / Recovery family
// (navy-orange panels, pins + corner decor, Cinzel titles) instead of the
// stale "card" theme this page's CSS module used to carry -- see fix.py for
// the full reasoning. Information is reorganised around ONE question per
// section: who is this person, what do they owe as a household, which of
// their projects (solo or joint) make up that number, how healthy is each
// payment, and what has staff said to them.
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiClock, FiCreditCard,
  FiUsers, FiUser, FiEdit3, FiSave, FiX, FiFolder, FiPercent,
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import clientService from '../../services/clientService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './ClientPortfolioPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const dayDiff = (iso) => { if (!iso) return null; const d = new Date(iso); if (isNaN(d.getTime())) return null; return Math.floor((Date.now() - d.getTime()) / 86400000); };
const isJoint = (p) => String(p.ownershipType || 'SOLO').toUpperCase() === 'JOINT';
// Same "paid / (paid+owed)" recovery-rate formula the Client Ledger uses,
// so a client's per-project number and their ledger-row number always agree.
const pctPaid = (p) => { const owed = Number(p.owed || 0); const paid = Number(p.paid || 0); const total = owed + paid; return total > 0 ? Math.min((paid / total) * 100, 100) : (p.titled ? 100 : 0); };
const pctTone = (pct) => (pct >= 75 ? styles.tagGood : pct >= 25 ? styles.tagWarn : styles.tagBad);

const Pins = () => (<React.Fragment>
  <div className={styles.pinsTop} aria-hidden="true">{[...Array(4)].map((_, i) => <div key={i} className={styles.pin} />)}</div>
  <div className={styles.pinsBottom} aria-hidden="true">{[...Array(4)].map((_, i) => <div key={i} className={styles.pin} />)}</div>
  <span className={styles.decorBl} aria-hidden="true" />
  <span className={styles.decorBr} aria-hidden="true" />
</React.Fragment>);

// -- IDENTIFIER CELL -- the project index is permanent from the day the
// record is created (single-identity model, guide 8.2/8.3) and is now the
// ONLY identifier this page shows per row -- the plot-number column is
// gone, so a folder with no title yet still reads cleanly instead of
// showing an empty "no title yet" placeholder next to it.
const IndexCell = ({ p }) => (<span className={styles.mono}>{p.index || '---'}</span>);

const emptyForm = { name: '', phone: '', email: '', address: '' };

const ClientPortfolioPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = String(user?.role || '').toUpperCase();
  const isDirector = !!user?.isRoot || role === 'ROLE_ADMIN' || role === 'ROLE_DIRECTOR';
  // Same bar Digital Folder uses for record edits: director or manager.
  const canEdit = isDirector || role === 'ROLE_MANAGER';

  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadCode, setLoadCode] = useState('');

  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveError, setSaveError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try { setD(await recoveryService.getClientDossier(id)); setLoadCode(''); }
    catch (err) { setD(null); setLoadCode(err && err.response ? 'HTTP ' + err.response.status : 'NETWORK'); }
    finally { setLoading(false); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  const plots = useMemo(() => (d && Array.isArray(d.plots) ? d.plots : []), [d]);

  // Every project this client holds appears exactly once in the dossier
  // list, joint or not, so the roll-up is a plain sum over that list --
  // keyed by projectId purely as a guard against a duplicate row.
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

  // A client can hold one project, several of their own, or a share in
  // someone else's -- grouping SOLO first then JOINT keeps that visible at
  // a glance instead of burying joint ownership in a flat list.
  const groups = useMemo(() => ([
    { key: 'SOLO', label: 'SOLO PROJECTS', rows: plots.filter((p) => !isJoint(p)) },
    { key: 'JOINT', label: 'JOINT PROJECTS', rows: plots.filter(isJoint) },
  ].filter((g) => g.rows.length > 0)), [plots]);

  const startEdit = () => {
    setForm({ name: d.name || '', phone: d.phone || '', email: d.email || '', address: d.address || '' });
    setFieldErrors({}); setSaveError(''); setIsEditing(true);
  };
  const cancelEdit = () => { setIsEditing(false); setFieldErrors({}); setSaveError(''); };
  const saveEdit = async () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Required';
    if (!form.phone.trim()) errs.phone = 'Required';
    if (Object.keys(errs).length) { setFieldErrors(errs); return; }
    setFieldErrors({}); setSaveError(''); setSaving(true);
    try {
      await clientService.updateClient(id, {
        fullName: form.name.trim(), phoneNumber: form.phone.trim(),
        email: form.email.trim(), homeAddress: form.address.trim(),
      });
      setIsEditing(false);
      await load();
    } catch (err) { setSaveError(err.response?.data?.message || 'Save failed -- try again.'); }
    finally { setSaving(false); }
  };

  const scrollToSection = (elId) => { const el = document.getElementById(elId); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); };

  const backBtn = (<button type="button" className={styles.backBtn} onClick={() => navigate('/clients')}><FiArrowLeft aria-hidden="true" /> BACK TO CLIENT LEDGER</button>);

  if (loading) return (<div className={styles.container}><div className={styles.noRecordsBig}>SYNCING CLIENT DOSSIER...</div></div>);
  if (!d) return (<div className={styles.container}>
    <header className={styles.pageHeader}><div className={styles.headerLeft}>
      <h1 className={styles.title}>Client Dossier</h1>
      <p className={styles.subtitle}>Full portfolio, money and call history</p>
    </div>{backBtn}</header>
    <div className={styles.noRecordsBig}>COULD NOT LOAD DOSSIER {loadCode ? '(' + loadCode + ') ' : ''}- REFRESH TO RETRY</div>
  </div>);

  const days = dayDiff(d.lastContact);
  const cols = isDirector ? 8 : 5;

  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>{d.name}</h1>
          <p className={styles.subtitle}>Client dossier - every project, shilling and call in one place</p>
        </div>
        <div className={styles.headerActions}>
          {canEdit && !isEditing && (<button type="button" className={styles.editBtn} onClick={startEdit}><FiEdit3 aria-hidden="true" /> EDIT PORTFOLIO</button>)}
          {canEdit && isEditing && (<div className={styles.editGroup}>
            <button type="button" className={styles.cancelBtn} onClick={cancelEdit} disabled={saving}><FiX aria-hidden="true" /> CANCEL</button>
            <button type="button" className={styles.saveBtn} onClick={saveEdit} disabled={saving}><FiSave aria-hidden="true" /> {saving ? 'SAVING...' : 'SAVE'}</button>
          </div>)}
          {backBtn}
        </div>
      </header>

      <section className={styles.panel}>
        <Pins />
        <h2 className={styles.panelTitle}><FiUsers aria-hidden="true" /> IDENTITY</h2>
        {saveError && <div className={styles.errorBanner}>{saveError}</div>}
        <div className={styles.specGrid}>
          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiUser aria-hidden="true" /> FULL NAME</span>
            {isEditing
              ? (<input className={`${styles.editInput} ${fieldErrors.name ? styles.inputError : ''}`} value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />)
              : (<span className={styles.specValue}>{d.name || '---'}</span>)}
          </div>
          <div className={styles.specItem}><span className={styles.specLabel}>NIN</span><span className={styles.specMono}>{d.nin || '---'}</span></div>
          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiPhoneCall aria-hidden="true" /> PHONE</span>
            {isEditing
              ? (<input className={`${styles.editInput} ${styles.editInputPhone} ${fieldErrors.phone ? styles.inputError : ''}`} value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />)
              : (<span className={`${styles.specMono} ${styles.specPhone}`}>{d.phone || '---'}</span>)}
          </div>
          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiMail aria-hidden="true" /> EMAIL</span>
            {isEditing
              ? (<input className={styles.editInput} value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />)
              : (<span className={styles.specValue}>{d.email || '---'}</span>)}
          </div>
          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiMapPin aria-hidden="true" /> ADDRESS</span>
            {isEditing
              ? (<input className={styles.editInput} value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />)
              : (<span className={styles.specValue}>{d.address || '---'}</span>)}
          </div>
          <div className={styles.specItem}><span className={styles.specLabel}><FiClock aria-hidden="true" /> LAST CONTACT</span><span className={styles.specValue}>{d.lastContact ? String(d.lastContact).slice(0, 10) + (days != null ? ' (' + days + 'D AGO)' : '') : 'NEVER'}</span></div>
        </div>
      </section>

      {isDirector && (
        <div className={styles.moneyStrip}>
          <div className={`${styles.statCard} ${styles.statRed} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>TOTAL OWED</label><strong>UGX {fmt(totals.owed)}</strong>
          </div>
          <div className={`${styles.statCard} ${styles.statGreen} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>TOTAL PAID</label><strong>UGX {fmt(totals.paid)}</strong>
          </div>
          <div className={`${styles.statCard} ${styles.statAmber} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('health-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('health-panel'); } }}>
            <label>STORAGE FEES</label><strong>UGX {fmt(totals.storage)}</strong>
          </div>
          <div className={`${styles.statCard} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>PROJECTS</label><strong>{totals.count}</strong><span className={styles.statNote}>{totals.solo} SOLO / {totals.joint} JOINT</span>
          </div>
        </div>
      )}

      <section className={styles.panel} id="portfolio-panel">
        <Pins />
        <h2 className={styles.panelTitle}><FiFolder aria-hidden="true" /> PROJECT PORTFOLIO</h2>
        <div className={styles.tableScroll}>
          <table className={styles.ledgerTable}>
            <thead><tr><th>Index</th><th>District</th><th>Ownership</th><th>Status</th>{isDirector && <th>Owed (UGX)</th>}{isDirector && <th>Paid (UGX)</th>}{isDirector && <th><FiPercent aria-hidden="true" /> Paid %</th>}<th /></tr></thead>
            <tbody>
              {plots.length === 0 ? (<tr><td colSpan={cols} className={styles.noRecords}>NO PROJECTS REGISTERED</td></tr>) :
                groups.map((g) => (
                  <React.Fragment key={g.key}>
                    <tr className={styles.groupRow}><td colSpan={cols}>{g.label} ({g.rows.length})</td></tr>
                    {g.rows.map((p, i) => {
                      const pct = pctPaid(p);
                      return (
                        <tr key={p.projectId || g.key + i} className={styles.row} onClick={() => navigate('/folder/' + p.projectId)} tabIndex={0}
                          title="Click to open folder"
                          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/folder/' + p.projectId); } }}>
                          <td><IndexCell p={p} /></td>
                          <td>{p.district || '---'}</td>
                          <td>
                            <span className={`${styles.tag} ${isJoint(p) ? styles.tagJoint : styles.tagNeutral}`}>{isJoint(p) ? 'JOINT' : 'SOLO'}</span>
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
                          <td><span className={`${styles.tag} ${p.receivable ? styles.tagBad : p.titled ? styles.tagGood : styles.tagWarn}`}>{p.receivable ? 'RECEIVABLE' : p.titled ? 'TITLED' : 'FOLDER'}</span></td>
                          {isDirector && <td><span className={`${styles.mono} ${Number(p.owed) > 0 ? styles.moneyRed : styles.moneyGreen}`}>{fmt(p.owed)}</span></td>}
                          {isDirector && <td><span className={styles.mono}>{fmt(p.paid)}</span></td>}
                          {isDirector && (<td>
                            <div className={styles.pctWrap}>
                              <div className={styles.pctBar} role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
                                <div className={`${styles.pctFill} ${pctTone(pct)}`} style={{ width: pct + '%' }} />
                              </div>
                              <span className={styles.pctLabel}>{Math.round(pct)}%</span>
                            </div>
                          </td>)}
                          <td><span className={styles.openLink}>OPEN FOLDER</span></td>
                        </tr>
                      );
                    })}
                  </React.Fragment>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      {isDirector && (
        <section className={styles.panel} id="health-panel">
          <Pins />
          <h2 className={styles.panelTitle}><FiCreditCard aria-hidden="true" /> PAYMENT HEALTH PER PROJECT</h2>
          <div className={styles.tableScroll}>
            <table className={styles.ledgerTable}>
              <thead><tr><th>Index</th><th>Paid (UGX)</th><th>Storage (UGX)</th><th>Last payment</th><th>Health</th></tr></thead>
              <tbody>
                {plots.length === 0 ? (<tr><td colSpan={5} className={styles.noRecords}>NO PAYMENT RECORDS</td></tr>) :
                  plots.map((p, i) => {
                    const dd = dayDiff(p.lastPayment);
                    const health = dd == null ? { c: styles.dotRed, t: 'Nothing received yet' } : dd <= 30 ? { c: styles.dotGreen, t: 'Paid this month' } : dd <= 60 ? { c: styles.dotAmber, t: 'Paid about 2 months ago' } : { c: styles.dotOrange, t: 'Over 2 months since paying' };
                    return (<tr key={p.projectId || i} className={styles.rowStatic}>
                      <td><IndexCell p={p} /></td>
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
                <span className={`${styles.tag} ${n.tone === 'POSITIVE' ? styles.tagGood : n.tone === 'NEGATIVE' ? styles.tagBad : styles.tagWarn}`}>{n.tag}</span>
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
