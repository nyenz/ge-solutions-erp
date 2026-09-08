import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom';
import { FiSearch, FiX, FiPhone, FiMapPin, FiClock, FiChevronDown, FiChevronUp, FiUser, FiFolderPlus } from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import { useAuth } from '../../hooks/useAuth';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';
const TABS = [
  { key: 'ALL', label: 'ALL DUE' },
  { key: 'CONTACTED', label: 'CONTACTED' },
  { key: 'MISSED', label: 'MISSED' },
  { key: 'SITE', label: 'SITE VISIT' },
  { key: 'LOCKED', label: 'LOCKED' },
];
function fmtD(s) { if (!s) return 'NEVER'; const d = new Date(s); const p = (x) => String(x).padStart(2, '0'); return p(d.getDate()) + '/' + p(d.getMonth() + 1) + '/' + d.getFullYear(); }
export default function RecoveryPortal() {
  const [tab, setTab] = useState('ALL');
  const [counts, setCounts] = useState(null);
  const [stats, setStats] = useState(null);
  const [rows, setRows] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [openId, setOpenId] = useState(null);
  const [sel, setSel] = useState(null);
  const [notes, setNotes] = useState([]);
  const [picked, setPicked] = useState(null);
  const [text, setText] = useState('');
  const [coWarn, setCoWarn] = useState(null);
  const [busy, setBusy] = useState(false);
  const [toasts, setToasts] = useState([]);
  const loadedOnce = useRef(false);
  const { user } = useAuth();
  const canManage = user?.isRoot || ['ROLE_ADMIN', 'ROLE_DIRECTOR', 'ROLE_MANAGER'].includes(user?.role);
  const toast = useCallback((msg, type) => { const id = Date.now() + Math.random(); setToasts((p) => [...p, { id, msg, type: type || 'info' }]); setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000); }, []);
  const load = useCallback(() => {
    setLoading(!loadedOnce.current);
    Promise.all([recoveryService.getQueues(), recoveryService.getQueue(tab), recoveryService.getTags(), recoveryService.getStats()])
      .then((r) => {
        setCounts(r[0].data || r[0]); setTags(r[2].data || r[2]); setStats(r[3].data || r[3]);
        const list = r[1].data || r[1];
        setRows(list);
        setOpenId(list.length ? list[0].id : null);
        loadedOnce.current = true;
        setLoading(false);
      }).catch(() => { setLoading(false); toast('Could not load recovery queue.', 'error'); });
  }, [tab, toast]);
  useEffect(() => { load(); }, [load]);
  const open = (c) => { setSel(c); setPicked(null); setText(''); recoveryService.getNotes(c.id).then((r) => setNotes(r.data || [])); };
  const save = () => {
    if (!picked || !sel) return;
    setBusy(true);
    recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text: text })
      .then((r) => { setSel(null); toast('Logged.', 'success'); if (r && r.data && r.data.coOwnerWarning) setCoWarn(r.data.coOwnerWarning); load(); })
      .catch((e) => { setBusy(false); toast((e.response && e.response.data && e.response.data.error) || 'Save failed', 'error'); });
  };
  const term = search.toLowerCase().replace(/\s+/g, '');
  const rowsF = rows.filter((c) => !term || [c.name, c.nin, c.phone, c.lastTag, c.district, c.village, ...(c.indexes || [])].join(' ').toLowerCase().replace(/\s+/g, '').indexOf(term) >= 0);
  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Recovery Cockpit</h1>
          <p className={styles.subtitle}>Call logs only - numbers only</p>
        </div>
      </header>
      <div className={styles.countsHUD}>
        <div className={styles.countCard}><label>TODAY'S CALLS</label><strong>{stats ? stats.callsToday : '-'}</strong></div>
        <div className={styles.countCard}><label>MONTH'S CALLS</label><strong>{stats ? stats.callsMonth : '-'}</strong></div>
        <div className={styles.countCard}><label>LONGEST WAIT</label><strong>{stats ? stats.longestWait : '-'}</strong></div>
        <div className={styles.countCard}><label>MONTH'S MISS</label><strong>{stats ? stats.missMonth : '-'}</strong></div>
      </div>
      <div className={styles.stickyRail}>
      <div className={styles.stickyTabs} role="tablist" aria-label="Recovery queues">
        <div className={styles.tabSearch}>
          <FiSearch className={styles.searchIcon} aria-hidden="true" />
          <input type="search" className={styles.searchInput} placeholder="Search name, NIN, phone, index..." value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search recovery queue" autoComplete="off" />
          {search && (<button type="button" className={styles.searchClearBtn} onClick={() => setSearch('')} aria-label="Clear search"><FiX aria-hidden="true" /></button>)}
        </div>
        <div className={styles.tabRow}>
          {TABS.map((t) => (
            <button key={t.key} role="tab" aria-selected={tab === t.key} className={`${styles.qTab} ${tab === t.key ? styles.qTabActive : ''}`} onClick={() => setTab(t.key)}>
              {t.label} ({counts ? counts[t.key] : '-'})
            </button>
          ))}
        </div>
      </div>
      <div className={styles.dotLegend} aria-label="Payment dot legend">
        <span><i className={styles.payDotGreen} /> Recent payment</span>
        <span><i className={styles.payDotYellow} /> Payment 2-4 weeks ago</span>
        <span><i className={styles.payDotRed} /> No recent payment</span>
      </div>
      </div>
      {loading && rows.length === 0 ? (
        <div className={styles.emptyState} role="status"><div className={styles.loadingSpinner} aria-hidden="true" /><span>SYNCING RECOVERY QUEUE...</span></div>
      ) : (
        <div className={`${styles.list} ${loading ? styles.refreshing : ''}`}>
          {rowsF.map((c) => {
            const isOpen = openId === c.id;
            return (
              <article key={c.id} className={`${styles.rowCard} ${isOpen ? styles.rowOpen : ''}`}>
                <button type="button" className={styles.rowHead} onClick={() => setOpenId(isOpen ? null : c.id)} aria-expanded={isOpen}>
                  <span className={styles.callPos}>{c.position ? tab + ' #' + c.position + '/' + c.queueTotal : tab}</span>
                  <span className={styles.cname}>{c.name || c.nin || 'UNKNOWN CLIENT'}</span>
                  <span className={c.payBadge === 'GREEN' ? styles.payDotGreen : c.payBadge === 'YELLOW' ? styles.payDotYellow : styles.payDotRed} title={c.payBadge === 'GREEN' ? 'Recent payment' : c.payBadge === 'YELLOW' ? 'Payment 2-4 weeks ago' : 'No recent payment'} />
                  {c.lastTag && (<span className={c.lastTone === 'POSITIVE' ? styles.chipPos : c.lastTone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{c.lastTag}</span>)}
                  {c.dayMiss > 0 && <span className={styles.dayChip}>day {c.dayMiss}/30</span>}
                  <span className={styles.reason}>{c.reason}</span>
                  {isOpen ? <FiChevronUp aria-hidden="true" /> : <FiChevronDown aria-hidden="true" />}
                </button>
                {isOpen && (
                  <div className={styles.rowBody}>
                    <span className={styles.nin}>{c.nin}</span>
                    <span className={styles.mono}>{c.phone}</span>
                    <span className={styles.projLine}>
                      {(c.projectIds || []).map((pid, i) => (<a key={pid} className={styles.projLink} href={'/folder/' + pid} onClick={(e) => e.stopPropagation()}>#{c.indexes[i] || pid}</a>))}
                    </span>
                    {c.coNames && c.coNames.length > 0 && (<span className={styles.coLine}><FiUser aria-hidden="true" /> Joint with: {c.coNames.join(', ')}</span>)}
                    {c.district && (<span className={styles.loc}><FiMapPin aria-hidden="true" /> {c.district}{c.village ? ' - ' + c.village : ''}</span>)}
                    <span className={styles.attemptLine}><FiClock aria-hidden="true" /> Good calls this 30 days: {c.calls30}/2 - Misses: {c.miss30}</span>
                    {c.unlock && (<span className={styles.lockBanner}><FiClock aria-hidden="true" /> Resting until {fmtD(c.unlock)} - read only.</span>)}
                    <span className={styles.rowActions}>
                      <button type="button" className={styles.cardBtn} onClick={() => open(c)} disabled={c.state === 'LOCKED'}><FiPhone aria-hidden="true" /> OPEN CALL LOG</button>
                      {(c.projectIds || []).length > 0 && (<a className={styles.cardBtnLink} href={'/folder/' + c.projectIds[0]}><FiFolderPlus aria-hidden="true" /> OPEN FOLDER</a>)}
                    </span>
                  </div>
                )}
              </article>
            );
          })}
          {rowsF.length === 0 && (<div className={styles.emptyState}><span>{term ? 'NO RECORDS MATCH "' + term.toUpperCase() + '"' : 'QUEUE CLEAR'}</span></div>)}
        </div>
      )}
      <HardwareModal isOpen={!!sel} onClose={() => setSel(null)} title={sel ? 'CALL LOG - ' + sel.name : 'CALL LOG'}>
        {sel && (<>
          <div className={styles.metaRow}><span className={styles.nin}>{sel.nin}</span><span className={styles.mono}>{sel.phone}</span></div>
          {sel.unlock && (<div className={styles.lockBanner}><FiClock aria-hidden="true" /> Resting until {fmtD(sel.unlock)} - read only.</div>)}
          <div className={styles.tagwall}>
            <label className={styles.wallLabel}>CALL (WE SPOKE)</label>
            <div className={styles.wallRow}>
              {tags.filter((t) => t.tone === 'POSITIVE').map((t) => (
                <button type="button" key={t.tag} className={styles.tagPos + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')} disabled={!!sel.unlock} onClick={() => setPicked(t)}>{t.tag}</button>
              ))}
            </div>
            <label className={styles.wallLabel}>MISSED (NO CONTACT)</label>
            <div className={styles.wallRow}>
              {tags.filter((t) => t.tone === 'NEGATIVE').map((t) => (
                <button type="button" key={t.tag} className={styles.tagNeg + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')} disabled={!!sel.unlock} onClick={() => setPicked(t)}>{t.tag}</button>
              ))}
            </div>
          </div>
          <div className={modalStyles.modalField}>
            <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
            <input type="text" className={modalStyles.modalInput} value={text} onChange={(e) => setText(e.target.value)} aria-label="Optional note" />
          </div>
          <div className={styles.histSection}>
            <label className={styles.wallLabel}>HISTORY</label>
            {notes.map((n) => (
              <div key={n.id} className={styles.histRow}>
                <span className={n.tone === 'POSITIVE' ? styles.chipPos : n.tone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{n.tag}</span>
                <span className={styles.histMeta}>{n.author || 'SYSTEM'} - {fmtD(n.createdAt)}</span>
                {n.text && <span className={styles.histText}>{n.text}</span>}
                {canManage && n.source === 'RECOVERY' && n.tag !== 'payment received' && (
                  <button type="button" className={styles.histDelete} aria-label="Delete note"
                    onClick={() => recoveryService.deleteNote(n.id).then(() => { toast('Note deleted.', 'warn'); recoveryService.getNotes(sel.id).then((r) => setNotes(r.data || [])); load(); })}>
                    <FiX aria-hidden="true" />
                  </button>
                )}
              </div>
            ))}
            {notes.length === 0 && (<div className={styles.trayEmpty}>NO CALLS LOGGED YET.</div>)}
          </div>
          <div className={modalStyles.modalFooter}>
            <HardwareButton type="button" onClick={save} loading={busy} icon={FiPhone} disabled={!picked || !!sel.unlock}>LOG OUTCOME</HardwareButton>
          </div>
        </>)}
      </HardwareModal>
      {coWarn && (
        <div className={styles.coWarnBanner} role="status">
          <span>{coWarn}</span>
          <button type="button" className={styles.coWarnDismiss} onClick={() => setCoWarn(null)} aria-label="Dismiss notice">&times;</button>
        </div>
      )}
      <BackToTopButton />
      {typeof document !== 'undefined' && ReactDOM.createPortal(
        <div className={styles.toastStack} role="region" aria-label="Notifications" aria-live="polite">
          {toasts.map((t) => (<div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`}>{t.msg}</div>))}
        </div>,
        document.body
      )}
    </div>
  );
}
