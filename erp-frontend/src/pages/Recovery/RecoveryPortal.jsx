import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import {
  FiSearch, FiX, FiPhone, FiMapPin, FiClock, FiAlertTriangle,
  FiArchive, FiFilePlus, FiFolderPlus, FiChevronDown, FiChevronUp, FiUser
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

// EXACT Intake entry labels - one source of truth across pages
const ENTRY_META = [
  { label: 'New Folder',   icon: FiFolderPlus, cls: 'badgeFolder' },
  { label: 'New Title',    icon: FiFilePlus,  cls: 'badgeTitle' },
  { label: 'Legacy Title', icon: FiArchive,   cls: 'badgeLegacy' },
];
const FILTERS = [
  { key: 'all',  label: 'ALL DUE' },
  { key: 'p1',   label: 'PRIORITY 1' },
  { key: 'p2',   label: 'PRIORITY 2' },
  { key: 'p3',   label: 'PRIORITY 3' },
  { key: 'site', label: 'SITE VISITS' },
];

function fmtDT(s) {
  if (!s) return 'NEVER';
  const d = new Date(s);
  const p = (x) => String(x).padStart(2, '0');
  return p(d.getDate()) + '/' + p(d.getMonth() + 1) + '/' + d.getFullYear() + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
}

function Badge({ type }) {
  const meta = ENTRY_META.find((e) => e.label === type);
  if (!meta) return <span className={styles.badgeLegacy}>-</span>;
  const Icon = meta.icon;
  return <span className={styles[meta.cls]}><Icon size={11} aria-hidden="true" /> {meta.label}</span>;
}

function Dots({ n }) {
  return (
    <span className={styles.dots} title={n + ' of 2 calls this month'}>
      {[0, 1].map((i) => (<span key={i} className={i < n ? styles.dotOn : styles.dotOff} />))}
    </span>
  );
}

export default function RecoveryPortal() {
  const [queue, setQueue] = useState([]);
  const [lockedList, setLockedList] = useState([]);
  const [tags, setTags] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [showLocked, setShowLocked] = useState(false);
  const [sel, setSel] = useState(null);
  const [notes, setNotes] = useState([]);
  const [picked, setPicked] = useState(null);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [toasts, setToasts] = useState([]);
  const collapsedOnce = React.useRef(false);

  const toast = useCallback((msg, type) => {
    const id = Date.now() + Math.random();
    setToasts((p) => [...p, { id, msg, type: type || 'info' }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000);
  }, []);

  // low-tier consistency: auto-collapse sidebar on first interaction (like Intake)
  useEffect(() => {
    const handler = () => {
      if (collapsedOnce.current) return;
      collapsedOnce.current = true;
      const aside = document.querySelector('aside');
      const toggle = document.querySelector('[class*="sidebarToggle"]');
      if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
    };
    window.addEventListener('click', handler, { once: true });
    return () => window.removeEventListener('click', handler);
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      recoveryService.getQueue(), recoveryService.getLocked(),
      recoveryService.getTags(), recoveryService.getStats(),
    ]).then((r) => {
      setQueue(r[0].data || []);
      setLockedList(r[1].data || []);
      setTags(r[2].data || []);
      setStats(r[3].data || null);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
      toast('Could not load the recovery queue. Refresh to retry.', 'error');
    });
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  const open = (c) => {
    setSel(c); setPicked(null); setText('');
    recoveryService.getNotes(c.id).then((r) => setNotes(r.data || []));
  };

  const save = () => {
    if (!picked || !sel) return;
    setBusy(true);
    recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text: text })
      .then(() => { setSel(null); toast('Outcome logged.', 'success'); load(); })
      .catch((e) => {
        setBusy(false);
        toast((e.response && e.response.data && e.response.data.error) || 'Save failed', 'error');
      });
  };

  const term = search.toLowerCase().replace(/\s+/g, '');
  const matches = (c) => {
    if (!term) return true;
    const hay = [c.name, c.nin, c.phone, c.lastTag, c.entryType, c.district, c.village,
      ...(c.indexes || [])].join(' ').toLowerCase().replace(/\s+/g, '');
    return hay.indexOf(term) >= 0;
  };
  const rows = queue.filter((c) => {
    if (!matches(c)) return false;
    if (filter === 'all') return true;
    if (filter === 'site') return c.lastTag === 'needs site visit';
    return c.priority === Number(filter.replace('p', ''));
  });
  const count = (k) => (stats ? stats[k] : '-');

  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Recovery Cockpit</h1>
          <p className={styles.subtitle}>Call logs and follow-up queue - numbers only</p>
        </div>
      </header>

      <div className={styles.countsHUD}>
        <div className={styles.countCard}><label>DUE NOW</label><strong>{count('dueNow')}</strong></div>
        <div className={styles.countCard}><label>CALLS TODAY</label><strong>{count('callsToday')}</strong></div>
        <div className={styles.countCard}><label>THIS MONTH</label><strong>{count('callsThisMonth')}</strong></div>
        <div className={styles.countCard}><label>LOCKED</label><strong>{count('locked')}</strong></div>
        <div className={styles.countCard}><label>SITE VISITS</label><strong>{count('siteVisits')}</strong></div>
      </div>

      <div className={styles.controls}>
        <div className={styles.searchBlock}>
          <div className={styles.searchInner}>
            <FiSearch className={styles.searchIcon} aria-hidden="true" />
            <input type="search" className={styles.searchInput}
              placeholder="Search name, NIN, phone, index, tag, district..."
              value={search} onChange={(e) => setSearch(e.target.value)}
              aria-label="Search recovery queue" autoComplete="off" />
            {search && (
              <button type="button" className={styles.searchClearBtn} onClick={() => setSearch('')} aria-label="Clear search">
                <FiX aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
        <div className={styles.filterRail} role="group" aria-label="Filter queue">
          {FILTERS.map((f) => (
            <button key={f.key}
              className={`${styles.filterBtn} ${filter === f.key ? styles.activeFilter : ''}`}
              onClick={() => setFilter(f.key)} aria-pressed={filter === f.key}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className={styles.emptyState} role="status">
          <div className={styles.loadingSpinner} aria-hidden="true" />
          <span>SYNCING RECOVERY QUEUE...</span>
        </div>
      ) : (
        <div className={styles.grid}>
          {rows.map((c) => (
            <article key={c.id} className={styles.card} onClick={() => open(c)}>
              <header className={styles.cardHead}>
                <span className={styles['p' + c.priority]}>P{c.priority}</span>
                <Badge type={c.entryType} />
                <Dots n={c.attemptsThisMonth || 0} />
              </header>
              <h2 className={styles.cname}>{c.name}</h2>
              <div className={styles.nin}>{c.nin}</div>
              <div className={styles.mono}>{c.phone}</div>
              {(c.indexes || []).length > 0 && (<div className={styles.mono}>#{c.indexes.join(' #')}</div>)}
              {c.district && (<div className={styles.loc}>{c.district}{c.village ? ' - ' + c.village : ''}</div>)}
              <div className={styles.cardFoot}>
                {c.lastTag
                  ? <span className={c.lastTone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{c.lastTag}</span>
                  : <span className={styles.chipNone}>NO CONTACT YET</span>}
                <span className={styles.mono}>{fmtDT(c.lastContactedAt)}</span>
              </div>
              <button type="button" className={styles.openBtn} onClick={(e) => { e.stopPropagation(); open(c); }}>
                <FiPhone aria-hidden="true" /> OPEN CALL LOG
              </button>
            </article>
          ))}
          {rows.length === 0 && (
            <div className={styles.emptyState}>
              <span>{term ? 'NO RECORDS MATCH "' + term.toUpperCase() + '"' : 'QUEUE CLEAR - EVERYONE COOLED DOWN OR CONTACTED'}</span>
            </div>
          )}
        </div>
      )}

      <section className={styles.lockedTray}>
        <button type="button" className={styles.trayToggle} onClick={() => setShowLocked((s) => !s)} aria-expanded={showLocked}>
          <FiAlertTriangle aria-hidden="true" />
          LOCKED CLIENTS ({lockedList.length}) - READ ONLY
          {showLocked ? <FiChevronUp aria-hidden="true" /> : <FiChevronDown aria-hidden="true" />}
        </button>
        {showLocked && (
          <div className={styles.trayList}>
            {lockedList.filter(matches).map((c) => (
              <div key={c.id} className={styles.trayRow} onClick={() => open(c)}>
                <Badge type={c.entryType} />
                <span className={styles.cname}>{c.name}</span>
                <span className={styles.nin}>{c.nin}</span>
                <span className={styles.mono}>CALLABLE {fmtDT(c.nextUnlock)}</span>
              </div>
            ))}
            {lockedList.length === 0 && (<div className={styles.trayEmpty}>NO LOCKED CLIENTS.</div>)}
          </div>
        )}
      </section>

      <HardwareModal isOpen={!!sel} onClose={() => setSel(null)}
        title={sel ? 'CALL LOG - ' + sel.name : 'CALL LOG'}>
        {sel && (<>
          <div className={styles.metaRow}>
            <Badge type={sel.entryType} />
            <span className={styles.nin}>{sel.nin}</span>
            <span className={styles.mono}>{sel.phone}</span>
          </div>
          <div className={styles.attemptLine}>
            <FiUser aria-hidden="true" /> CALLS THIS MONTH: <Dots n={sel.attemptsThisMonth || 0} />
          </div>
          {sel.locked && (
            <div className={styles.lockBanner}>
              <FiAlertTriangle aria-hidden="true" />
              COOL-DOWN ACTIVE - READ ONLY. CALLABLE {fmtDT(sel.nextUnlock)}.
            </div>
          )}
          <div className={styles.tagwall}>
            <label className={styles.wallLabel}>POSITIVE</label>
            <div className={styles.wallRow}>
              {tags.filter((t) => t.tone === 'POSITIVE').map((t) => (
                <button type="button" key={t.tag}
                  className={styles.tagPos + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                  disabled={sel.locked && t.countsAsAttempt}
                  onClick={() => setPicked(t)}>
                  {t.tag}
                </button>
              ))}
            </div>
            <label className={styles.wallLabel}>NEGATIVE</label>
            <div className={styles.wallRow}>
              {tags.filter((t) => t.tone === 'NEGATIVE').map((t) => (
                <button type="button" key={t.tag}
                  className={styles.tagNeg + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                  disabled={sel.locked && t.countsAsAttempt}
                  onClick={() => setPicked(t)}>
                  {t.tag.indexOf('site visit') >= 0 ? <FiMapPin aria-hidden="true" /> :
                    (t.countsAsAttempt ? <FiPhone aria-hidden="true" /> : <FiClock aria-hidden="true" />)}
                  {t.tag}
                </button>
              ))}
            </div>
          </div>
          <div className={modalStyles.modalField}>
            <label className={modalStyles.modalLabel}>OPTIONAL DETAIL (RARE)</label>
            <input type="text" className={modalStyles.modalInput} value={text}
              onChange={(e) => setText(e.target.value)} aria-label="Optional note detail" />
          </div>
          <div className={styles.histSection}>
            <label className={styles.wallLabel}>CALL LOG</label>
            {notes.map((n) => (
              <div key={n.id} className={styles.histRow}>
                <span className={n.tone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{n.tag}</span>
                <span className={styles.histMeta}>{n.author || 'SYSTEM'} - {fmtDT(n.createdAt)}</span>
                {n.text && <span className={styles.histText}>{n.text}</span>}
              </div>
            ))}
            {notes.length === 0 && (<div className={styles.trayEmpty}>NO CALLS LOGGED YET.</div>)}
          </div>
          <div className={modalStyles.modalFooter}>
            <HardwareButton type="button" onClick={save} loading={busy} icon={FiPhone}
              disabled={!picked || sel.locked}>
              LOG OUTCOME
            </HardwareButton>
          </div>
        </>)}
      </HardwareModal>

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
