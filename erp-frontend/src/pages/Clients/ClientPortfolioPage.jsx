// PATH: erp-frontend/src/pages/Clients/ClientPortfolioPage.jsx
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
