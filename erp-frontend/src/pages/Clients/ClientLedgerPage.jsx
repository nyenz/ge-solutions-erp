// PATH: erp-frontend/src/pages/Clients/ClientLedgerPage.jsx
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
    const t = term.toLowerCase().replace(/\s+/g, '');
    return rows.filter(c => {
      if (t) {
        const hay = [c.name, c.nin, c.phone, ...(c.plots || []).map(p => String(p.plot))].join(' ').toLowerCase().replace(/\s+/g, '');
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
