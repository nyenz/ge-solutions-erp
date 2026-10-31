// PATH: erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx
// CLIENT DOSSIER v2 -- design + information rethink.
// Visual language now matches the Intake / Client Ledger / Recovery family
// (navy-orange panels, pins + corner decor, Cinzel titles) instead of the
// stale "card" theme this page's CSS module used to carry -- see fix.py for
// the full reasoning. Information is reorganised around ONE question per
// section: who is this person, what do they owe as a household, which of
// their projects (solo or joint) make up that number, how healthy is each
// payment, and what has staff said to them.
import { roleFlags } from '../../utils/roles';
import { scrollBehavior } from '../../utils/motion';   // fix226: follows Settings > Animation
import { PaymentHealthDot } from '../../components/common/PaymentHealth';
import { paymentLabel } from '../../utils/paymentHealth';
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiArrowLeft, FiPhoneCall, FiMail, FiMapPin, FiClock, FiCreditCard,
  FiUsers, FiUser, FiEdit3, FiSave, FiX, FiFolder, FiPercent, FiAlertTriangle,
  FiArrowUp, FiArrowDown, FiPrinter,
} from 'react-icons/fi';
import ClientFilePrint from '../../components/print/ClientFilePrint';   // fix212
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import clientService from '../../services/clientService';
import BackToTopButton from '../../components/common/BackToTopButton';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import CornerDecor from '../../components/ui/CornerDecor';
import { PROJECT_STATUS } from '../../utils/projectStatus';
import styles from './ClientPortfolioPage.module.css';
import RetryButton from '../../components/common/RetryButton';
import useTableScrollHandoff from '../../hooks/useTableScrollHandoff';
import { LoadingState } from '../../components/common/LoadingState';
import { errorText } from '../../utils/errorText';   // fix205
import { methodLine } from '../../utils/paymentMethods';   // fix214
import NotesTimeline from '../../components/notes/NotesTimeline';   // fix215
import { invoiceText, contractText } from '../../utils/projectNumbers';   // fix284 (B4)
import { fmtDay, fmtMoney } from '../../utils/format';   // fix284 (B3)

const fmt = fmtMoney;
const dayDiff = (iso) => { if (!iso) return null; const d = new Date(iso); if (isNaN(d.getTime())) return null; return Math.floor((Date.now() - d.getTime()) / 86400000); };
const isJoint = (p) => String(p.ownershipType || 'SOLO').toUpperCase() === 'JOINT';
// fix181 (5.5, 11.8): paid / billed, both from the server; 100% only when the title was really handed over
const pctPaid = (p) => { const owed = Number(p.owed || 0); const paid = Number(p.paid || 0); const total = Number(p.billed || 0) || (owed + paid); return total > 0 ? Math.min((paid / total) * 100, 100) : (p.released ? 100 : 0); };
const pctTone = (pct) => (pct >= 75 ? styles.tagGood : pct >= 25 ? styles.tagWarn : styles.tagBad);

// Shared by both tables below -- sorts a list of plot rows by any column
// key (numeric or text), ascending or descending.
const sortPlots = (rows, key, direction) => {
  if (!key) return rows;
  const dir = direction === 'asc' ? 1 : -1;
  return [...rows].sort((a, b) => {
    let aVal, bVal;
    if (key === 'index') { aVal = a.index || ''; bVal = b.index || ''; }
    else if (key === 'district') { aVal = a.district || ''; bVal = b.district || ''; }
    else if (key === 'owed') { aVal = Number(a.owed || 0); bVal = Number(b.owed || 0); }
    else if (key === 'paid') { aVal = Number(a.paid || 0); bVal = Number(b.paid || 0); }
    else if (key === 'pct') { aVal = pctPaid(a); bVal = pctPaid(b); }
    else if (key === 'storage') { aVal = Number(a.storage || 0); bVal = Number(b.storage || 0); }
    else if (key === 'lastPayment') { aVal = a.lastPayment || ''; bVal = b.lastPayment || ''; }
    else { aVal = a[key]; bVal = b[key]; }
    // fix181 (5.10): natural, case-blind order; empty values last in both directions
    const empty = (v) => v === null || v === undefined || v === '';
    if (empty(aVal) && empty(bVal)) return 0;
    if (empty(aVal)) return 1;
    if (empty(bVal)) return -1;
    const cmp = (typeof aVal === 'number' && typeof bVal === 'number') ? aVal - bVal
      : String(aVal).localeCompare(String(bVal), undefined, { numeric: true, sensitivity: 'base' });
    return cmp * dir;
  });
};

// -- IDENTIFIER CELL -- the project index is permanent from the day the
// record is created (single-identity model, guide 8.2/8.3) and is now the
// ONLY identifier this page shows per row -- the plot-number column is
// gone, so a folder with no title yet still reads cleanly instead of
// showing an empty "no title yet" placeholder next to it.
const IndexCell = ({ p, numbers }) => (
  <span className={styles.indexStack}>
    <span className={styles.mono}>{p.index || '---'}</span>
    {numbers && p.invoiceNumber && <span className={styles.numSub} title="Invoice number">{invoiceText(p.invoiceNumber)}</span>}
    {numbers && p.contractNumber && <span className={styles.numSub} title="Contract number">{contractText(p.contractNumber)}</span>}
  </span>
);

const emptyForm = { name: '', phone: '', email: '', address: '' };

const ClientPortfolioPage = () => {
  const projectTableRef = useTableScrollHandoff();
  const healthTableRef = useTableScrollHandoff();
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isDirector = roleFlags(user).isOwnerLevel;
  // Same bar Digital Folder uses for record edits: director or manager.
  const canEdit = roleFlags(user).isManager;
  // fix193 (review Q3 = B): the Secretary makes the recovery calls, so the Secretary may correct the PHONE only
  const phoneOnly = roleFlags(user).isSecretary;

  const [d, setD] = useState(null);
  const [noteTotal, setNoteTotal] = useState(null);   // fix225: the real number of notes, after every change
  const [loading, setLoading] = useState(true);
  const [, setLoadCode] = useState('');

  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveError, setSaveError] = useState('');

  // Project Portfolio table's sort state, and Payment Health's own
  // (separate) one -- same click-header-to-sort idiom the Client Ledger
  // already uses.
  const [sortConfig, setSortConfig] = useState({ key: '', direction: 'asc' });
  const handleSort = (key) => setSortConfig((prev) => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
  const renderSortIcon = (key) => sortConfig.key !== key ? null
    : (sortConfig.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

  const [healthSort, setHealthSort] = useState({ key: '', direction: 'asc' });
  const handleHealthSort = (key) => setHealthSort((prev) => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
  const renderHealthSortIcon = (key) => healthSort.key !== key ? null
    : (healthSort.direction === 'asc' ? <FiArrowUp className={styles.sortActive} aria-hidden="true" /> : <FiArrowDown className={styles.sortActive} aria-hidden="true" />);

  const load = useCallback(async () => {
    setLoading(true);
    try { setD(await recoveryService.getClientDossier(id)); setLoadCode(''); }
    catch { setD(null); setLoadCode(''); }   // fix205: no status numbers on screen
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
    // fix181 (5.5, 6.7): the money totals come from the server (billed, paid, storage split, kept fees)
    const st = d && d.totals ? d.totals : null;
    if (st) Object.assign(t, { owed: Number(st.owed || 0), paid: Number(st.paid || 0), billed: Number(st.billed || 0),
      storage: Number(st.storage || 0), storagePaid: Number(st.storagePaid || 0), storageUnpaid: Number(st.storageUnpaid || 0), keptFees: Number(st.keptFees || 0) });
    return t;
  }, [plots, d]);

  // A client can hold one project, several of their own, or a share in
  // someone else's -- grouping SOLO first then JOINT keeps that visible at
  // a glance instead of burying joint ownership in a flat list.
  const groups = useMemo(() => ([
    { key: 'SOLO', label: 'SOLO PROJECTS', rows: sortPlots(plots.filter((p) => !isJoint(p)), sortConfig.key, sortConfig.direction) },
    { key: 'JOINT', label: 'JOINT PROJECTS', rows: sortPlots(plots.filter(isJoint), sortConfig.key, sortConfig.direction) },
  ].filter((g) => g.rows.length > 0)), [plots, sortConfig]);

  const healthRows = useMemo(() => sortPlots(plots, healthSort.key, healthSort.direction), [plots, healthSort]);

  const startEdit = () => {
    setForm({ name: d.name || '', phone: d.phone || '', email: d.email || '', address: d.address || '' });
    setFieldErrors({}); setSaveError(''); setIsEditing(true);
  };
  const cancelEdit = () => { setIsEditing(false); setFieldErrors({}); setSaveError(''); };
  const saveEdit = async () => {
    const errs = {};
    if (!phoneOnly && !form.name.trim()) errs.name = 'Required';
    if (!form.phone.trim()) errs.phone = 'Required';
    if (Object.keys(errs).length) { setFieldErrors(errs); return; }
    setFieldErrors({}); setSaveError(''); setSaving(true);
    try {
      await clientService.updateClient(id, phoneOnly ? { phoneNumber: form.phone.trim() } : {
        fullName: form.name.trim(), phoneNumber: form.phone.trim(),
        email: form.email.trim(), homeAddress: form.address.trim(),
      });
      setIsEditing(false);
      await load();
    } catch (err) { setSaveError(err && err.response ? errorText(err) : 'Not saved. Try again.'); }   // fix205
    finally { setSaving(false); }
  };

  const scrollToSection = (elId) => { const el = document.getElementById(elId); if (el) el.scrollIntoView({ behavior: scrollBehavior(), block: 'start' }); };

  const backBtn = (<button type="button" className={styles.backBtn} onClick={() => navigate('/clients')}><FiArrowLeft aria-hidden="true" /> BACK</button>);

  if (loading) return (<div data-page="client" className={styles.container}><LoadingState label="SYNCING CLIENT DOSSIER..." size="page" /></div>);
  if (!d) return (<div data-page="client" className={styles.container}>
    <header className={styles.pageHeader}><div className={styles.headerLeft}>
      <h1 className={styles.title}>Client Dossier</h1>
      <p className={styles.subtitle}>Full portfolio, money and call history</p>
    </div>{backBtn}</header>
    <div className={styles.errorState}>
      <FiAlertTriangle aria-hidden="true" className={styles.errorIcon} /> <span className={styles.errorText}>Could not load this client: no reply from the server (the internet is down, or the server is waking up). Nothing was saved. Try again in a few seconds.</span>
      <RetryButton className={styles.retryBtn} onClick={() => load()} />
    </div>
  </div>);

  const days = d.daysSinceContact ?? dayDiff(d.lastContact);   // fix181 (11.9): counted on the server
  const cols = isDirector ? 8 : 5;

  return (
    <div data-page="client" className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>{d.name}</h1>
          <p className={styles.subtitle}>Client dossier - every project, shilling and call in one place</p>
        </div>
        <div className={styles.headerActions}>
          {(canEdit || phoneOnly) && !isEditing && (<button type="button" className={styles.editBtn} onClick={startEdit}><FiEdit3 aria-hidden="true" /> {phoneOnly ? 'EDIT PHONE' : 'EDIT DETAILS'}</button>)}
          {(canEdit || phoneOnly) && isEditing && (<div className={styles.editGroup}>
            <button type="button" className={styles.cancelBtn} onClick={cancelEdit} disabled={saving}><FiX aria-hidden="true" /> CANCEL</button>
            <button type="button" className={styles.saveBtn} onClick={saveEdit} disabled={saving}><FiSave aria-hidden="true" /> {saving ? 'SAVING...' : 'SAVE'}</button>
          </div>)}
          {!isEditing && (<button type="button" className={styles.printBtn} onClick={() => window.print()} aria-label="Print this client's file" title="Print this client's file"><FiPrinter aria-hidden="true" /></button>)}   {/* fix227: icon only, like the Folder page */}
          {backBtn}
        </div>
      </header>
      {/* fix212: what PRINT puts on paper -- a Client File in the same layout as the Project File */}
      <ClientFilePrint className={styles.printDocWrap} client={d} plots={plots} totals={totals} showMoney={isDirector} printedBy={user?.username} />

      <CollapsibleSection icon={<FiUsers aria-hidden="true" />} title="IDENTITY">
        <CornerDecor hideTop />
        {saveError && <div className={styles.errorBanner}>{saveError}</div>}
        <div className={styles.specGrid} data-editing={isEditing ? 'IDENTITY DETAILS' : undefined}>
          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiUser aria-hidden="true" /> FULL NAME</span>
            {isEditing && !phoneOnly
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
            {isEditing && !phoneOnly
              ? (<input type="email" aria-label="Email" className={styles.editInput} value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />)
              : (<span className={styles.specValue}>{d.email || '---'}</span>)}
          </div>
          <div className={styles.specItem}>
            <span className={styles.specLabel}><FiMapPin aria-hidden="true" /> ADDRESS</span>
            {isEditing && !phoneOnly
              ? (<input className={styles.editInput} value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />)
              : (<span className={styles.specValue}>{d.address || '---'}</span>)}
          </div>
          <div className={styles.specItem}><span className={styles.specLabel}><FiClock aria-hidden="true" /> LAST CONTACT</span><span className={styles.specValue}>{d.lastContact ? fmtDay(d.lastContact) + (days != null ? ' (' + days + 'D AGO)' : '') : 'NEVER'}</span></div>
        </div>
      </CollapsibleSection>

      {isDirector && (
        <div className={styles.moneyStrip}>
          <div className={`${styles.statCard} ${styles.statRed} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>TOTAL OWED</label><strong>UGX {fmt(totals.owed)}</strong>
            <span className={styles.statNote}>{totals.count} {totals.count === 1 ? 'project' : 'projects'}</span>
          </div>
          <div className={`${styles.statCard} ${styles.statGreen} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>TOTAL PAID</label><strong>UGX {fmt(totals.paid)}</strong>
            <span className={styles.statNote}>{Number(totals.billed || 0) > 0 ? Math.round((Number(totals.paid) / Number(totals.billed)) * 100) : 0}% of billed</span>
          </div>
          <div className={`${styles.statCard} ${styles.statAmber} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('health-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('health-panel'); } }}>
            <label>STORAGE FEES</label><strong>UGX {fmt(totals.storage)}</strong>
            <span className={styles.statNote}>accrued or kept: UGX {fmt(totals.storagePaid)} paid, UGX {fmt(totals.storageUnpaid)} unpaid{Number(totals.keptFees || 0) > 0 ? ' (UGX ' + fmt(totals.keptFees) + ' kept after set aside)' : ''}</span>
          </div>
          <div className={`${styles.statCard} ${styles.statCyan} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>PROJECTS</label><strong>{totals.count}</strong>
            <span className={styles.statNote}>in this portfolio</span>
          </div>
          <div className={`${styles.statCard} ${styles.statWhite} ${styles.statClickable}`} role="button" tabIndex={0}
            onClick={() => scrollToSection('portfolio-panel')}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scrollToSection('portfolio-panel'); } }}>
            <label>OWNERSHIP</label><strong className={styles.statTextValue}>{totals.solo} SOLO / {totals.joint} JOINT</strong>
            <span className={styles.statNote}>tenure split</span>
          </div>
        </div>
      )}

      <div id="portfolio-panel">
      <CollapsibleSection icon={<FiFolder aria-hidden="true" />} title="PROJECT PORTFOLIO"
        right={<span className={styles.panelCornerBadge}>{totals.count} {totals.count === 1 ? 'PROJECT' : 'PROJECTS'}</span>}>
        <CornerDecor hideTop />
        <div className={styles.tableScroll} ref={projectTableRef}>
          <table className={styles.ledgerTable}>
            <thead><tr>
              <th onClick={() => handleSort('index')} className={`${styles.sortable} gsStickyCol`} aria-sort={sortConfig.key === 'index' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Index {renderSortIcon('index')}</th>
              <th onClick={() => handleSort('district')} className={styles.sortable} aria-sort={sortConfig.key === 'district' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>District {renderSortIcon('district')}</th>
              <th>Ownership</th><th>Status</th>
              {isDirector && <th onClick={() => handleSort('owed')} className={styles.sortable} aria-sort={sortConfig.key === 'owed' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Owed (UGX) {renderSortIcon('owed')}</th>}
              {isDirector && <th onClick={() => handleSort('paid')} className={styles.sortable} aria-sort={sortConfig.key === 'paid' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Paid (UGX) {renderSortIcon('paid')}</th>}
              {isDirector && <th onClick={() => handleSort('pct')} className={styles.sortable} aria-sort={sortConfig.key === 'pct' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}><FiPercent aria-hidden="true" /> Paid % {renderSortIcon('pct')}</th>}
              <th />
            </tr></thead>
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
                          <td className="gsStickyCol"><IndexCell p={p} numbers /></td>
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
                          <td>
                            {/* fix181 (11.8, 6.3, 6.5, 6.8, 6.2): the honest status words, type, Recovery state, the first-month note and subdivision links */}
                            {/* fix184: the ONE status word first (utils/projectStatus.js); whether title details are saved is a separate quiet line */}
                            <span className={`${styles.tag} ${p.released ? styles.tagGood : p.receivable ? styles.tagBad : styles.tagNeutral}`}
                              title={(p.released ? PROJECT_STATUS.HANDED_OVER : p.receivable ? PROJECT_STATUS.RECEIVABLES : PROJECT_STATUS.ACTIVE).tip}>
                              {(p.released ? PROJECT_STATUS.HANDED_OVER : p.receivable ? PROJECT_STATUS.RECEIVABLES : PROJECT_STATUS.ACTIVE).label}</span>
                            {p.problem && <span className={`${styles.tag} ${styles.tagBad}`}>PROBLEM</span>}
                            {p.critical && <span className={`${styles.tag} ${styles.tagBad}`}>CRITICAL</span>}
                            {p.recoveryState && (<button type="button" className={styles.coChip} title="Open this client in Recovery"
                              onClick={(e) => { e.stopPropagation(); navigate('/recovery?client=' + id); }}>{p.recoveryState}</button>)}
                            <span className={styles.coLine}>{p.projectTypeLabel || ''}{p.hasTitleDetails ? ' - has title details' : ' - no title details yet'}</span>
                            {p.recoveryStartsOn && <span className={styles.coLine}>new project - recovery starts {fmtDay(p.recoveryStartsOn)}</span>}
                            {p.parentProjectId && (<button type="button" className={styles.coChip} onClick={(e) => { e.stopPropagation(); navigate('/folder/' + p.parentProjectId); }}>
                              From #{p.parentProjectIndex || '?'} plot {p.parentSubdivisionNo}</button>)}
                            {(p.transfers || []).length > 0 && (<span className={styles.coLine}>{p.transfers.length} of {p.subdivisionCount || '?'} plot(s) transferred:
                              {p.transfers.map(t => (<button key={t.projectId} type="button" className={styles.coChip}
                                onClick={(e) => { e.stopPropagation(); navigate('/folder/' + t.projectId); }}>#{t.index} (plot {t.plotNo}{t.released ? ', released' : ''})</button>))}</span>)}
                          </td>
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
      </CollapsibleSection>
      </div>

      {isDirector && (
        <div id="health-panel">
        <CollapsibleSection icon={<FiCreditCard aria-hidden="true" />} title="PAYMENT HEALTH PER PROJECT">
          <CornerDecor hideTop />
          <div className={styles.tableScroll} ref={healthTableRef}>
            <table className={styles.ledgerTable}>
              <thead><tr>
                <th onClick={() => handleHealthSort('index')} className={`${styles.sortable} gsStickyCol`} aria-sort={healthSort.key === 'index' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Index {renderHealthSortIcon('index')}</th>
                <th onClick={() => handleHealthSort('paid')} className={styles.sortable} aria-sort={healthSort.key === 'paid' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Paid (UGX) {renderHealthSortIcon('paid')}</th>
                <th onClick={() => handleHealthSort('storage')} className={styles.sortable} aria-sort={healthSort.key === 'storage' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Storage (UGX) {renderHealthSortIcon('storage')}</th>
                <th onClick={() => handleHealthSort('lastPayment')} className={styles.sortable} aria-sort={healthSort.key === 'lastPayment' ? (healthSort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>Last payment {renderHealthSortIcon('lastPayment')}</th>
                <th>Health</th>
              </tr></thead>
              <tbody>
                {healthRows.length === 0 ? (<tr><td colSpan={5} className={styles.noRecords}>NO PAYMENT RECORDS</td></tr>) :
                  healthRows.map((p, i) => {
                    // fix181 (5.2, 6.6): the shared gradient and the server's day count
                    const isNew = !!p.recoveryStartsOn && p.daysSincePayment == null;
                    return (<tr key={p.projectId || i} className={styles.rowStatic}>
                      <td className="gsStickyCol"><IndexCell p={p} /></td>
                      <td><span className={styles.mono}>{fmt(p.paid)}</span></td>
                      <td><span className={styles.mono}>{fmt(p.storage)}</span></td>
                      <td><span className={styles.mono}>{p.lastPayment ? fmtDay(p.lastPayment) : 'NEVER'}</span></td>
                      <td><span className={styles.healthCell}><PaymentHealthDot days={p.daysSincePayment} isNew={isNew} startsOn={p.recoveryStartsOn} /> {paymentLabel(p.daysSincePayment, isNew, p.recoveryStartsOn)}</span></td>
                    </tr>);
                  })}
              </tbody>
            </table>
          </div>
        </CollapsibleSection>
        </div>
      )}

      {isDirector && plots.some(p => (p.payments || []).length > 0) && (
        <CollapsibleSection icon={<FiCreditCard aria-hidden="true" />} title="PAYMENTS (WHO PAID)">
          <CornerDecor hideTop />
          {/* fix181 (4.7, 6.1, 11.7): every payment line, the client who paid (current name), reversals marked */}
          <div className={styles.noteList}>
            {plots.filter(p => (p.payments || []).length > 0).map(p => (
              <article key={p.projectId} className={styles.noteRow}>
                <span className={styles.mono}>#{p.index}</span>
                {isJoint(p) && <span className={styles.noteAuthor}>paid by this client: UGX {fmt(p.paidByThisClient)}</span>}
                {/* fix266 (David): one tidy row per payment -- date, amount, who paid, how; reversals marked, not shouted */}
                <div className={styles.payTable} role="table" aria-label={'Payments of project #' + p.index}>
                  <div className={styles.payHead} role="row">
                    <span role="columnheader">DATE</span><span role="columnheader">AMOUNT (UGX)</span><span role="columnheader">PAID BY</span><span role="columnheader">HOW</span><span role="columnheader" />
                  </div>
                  {p.payments.map(pay => (
                    <div key={pay.id} role="row" className={`${styles.payLine} ${pay.reversed ? styles.payLineGone : ''} ${pay.reversal ? styles.payLineRev : ''}`}>
                      <span role="cell" className={styles.payDate}>{pay.paidOn ? fmtDay(pay.paidOn) : 'No date'}</span>
                      <span role="cell" className={styles.payAmt}>{fmt(pay.amount)}</span>
                      <span role="cell" className={styles.payWho}>{pay.payerName}</span>
                      <span role="cell" className={styles.payHow}>{methodLine(pay.paymentMethod, pay.paymentReference)}</span>
                      <span role="cell" className={styles.payTags}>
                        {pay.allocation === 'STORAGE' && <em className={styles.payTag}>STORAGE FEES</em>}
                        {pay.reversal && <em className={`${styles.payTag} ${styles.payTagRev}`}>REVERSAL</em>}
                        {pay.reversed && <em className={styles.payTag}>REVERSED</em>}
                      </span>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* fix215 (David): one Notes timeline for this client -- notes, decisions, money, events and calls of all their projects */}
      <CollapsibleSection icon={<FiPhoneCall aria-hidden="true" />} title="NOTES AND HISTORY" right={noteTotal != null ? <span className={styles.coChip} title="Lines in the notes">{noteTotal}</span> : null}>
        <CornerDecor hideTop />
        {/* fix181 (6.4): straight to this client's card in Recovery */}
        <button type="button" className={styles.coChip} onClick={() => navigate('/recovery?client=' + id)} title="Open this client's card on the Recovery page">OPEN IN RECOVERY</button>
        <NotesTimeline scope="client" id={id} refreshKey={d} onCount={setNoteTotal} />
      </CollapsibleSection>
      <BackToTopButton />
    </div>
  );
};
export default ClientPortfolioPage;
