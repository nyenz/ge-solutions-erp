import React, { useState, useEffect, useCallback } from 'react';
import { FiPhone, FiSearch, FiX, FiMapPin, FiClock, FiAlertTriangle } from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import { useAuth } from '../../hooks/useAuth';
import styles from './RecoveryPortal.module.css';

// entry-type labels kept identical to Intake (discovered at fix time)
const ENTRY_TYPES = ["NEW", "LEGACY", "BACKLOG"];

const ENTRY_TONE = {};
ENTRY_TYPES.forEach(function (t, i) { ENTRY_TONE[String(t).toUpperCase()] = i; });

function fmtWhen(s) {
  if (!s) return 'never';
  var d = new Date(s);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function RecoveryPortal() {
  const { user } = useAuth();
  const [queue, setQueue] = useState([]);
  const [tags, setTags] = useState([]);
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState('');
  const [sel, setSel] = useState(null);      // selected client row
  const [notes, setNotes] = useState([]);
  const [picked, setPicked] = useState(null); // picked tag def
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = useCallback(function () {
    Promise.all([
      recoveryService.getQueue(), recoveryService.getTags(), recoveryService.getStats()
    ]).then(function (r) {
      setQueue(r[0].data || []);
      setTags(r[1].data || []);
      setStats(r[2].data || null);
    }).catch(function (e) { setMsg('load failed: ' + (e.message || e)); });
  }, []);
  useEffect(function () { load(); }, [load]);

  const open = function (c) {
    setSel(c); setPicked(null); setText(''); setMsg(null);
    recoveryService.getNotes(c.id).then(function (r) { setNotes(r.data || []); });
  };

  const save = function () {
    if (!picked || !sel) return;
    setBusy(true); setMsg(null);
    recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text: text })
      .then(function () { setSel(null); load(); })
      .catch(function (e) {
        setBusy(false);
        setMsg((e.response && e.response.data && e.response.data.error) || 'save failed');
      });
  };

  const term = search.toLowerCase().replace(/\s+/g, '');
  const rows = queue.filter(function (c) {
    if (!term) return true;
    var hay = [c.name, c.nin, c.phone, c.lastTag, c.entryType].join(' ').toLowerCase().replace(/\s+/g, '');
    return hay.indexOf(term) >= 0;
  });

  return (
    <div className={styles.cockpit}>
      <header className={styles.topbar}>
        <h1 className={styles.title}>RECOVERY COCKPIT</h1>
        <div className={styles.counts}>
          <div className={styles.count}><span>{stats ? stats.dueNow : '-'}</span><label>DUE NOW</label></div>
          <div className={styles.count}><span>{stats ? stats.callsToday : '-'}</span><label>CALLS TODAY</label></div>
          <div className={styles.count}><span>{stats ? stats.callsThisMonth : '-'}</span><label>THIS MONTH</label></div>
          <div className={styles.count}><span>{stats ? stats.locked : '-'}</span><label>LOCKED</label></div>
          <div className={styles.count}><span>{stats ? stats.siteVisits : '-'}</span><label>SITE VISITS</label></div>
        </div>
      </header>

      <div className={styles.searchRow}>
        <FiSearch />
        <input
          placeholder="search name / NIN / phone / tag (e.g. needs site visit)"
          value={search}
          onChange={function (e) { setSearch(e.target.value); }}
        />
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr><th>#</th><th>CLIENT</th><th>PHONE</th><th>TYPE</th><th>LAST OUTCOME</th><th>LAST CONTACT</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map(function (c, i) {
              return (
                <tr key={c.id} className={styles.row} onClick={function () { open(c); }}>
                  <td className={styles.num}>{i + 1}</td>
                  <td>
                    <span className={styles.cname}>{c.name}</span>
                    <span className={styles.nin}>{c.nin}</span>
                  </td>
                  <td className={styles.mono}>{c.phone}</td>
                  <td>
                    {c.entryType
                      ? <span className={styles['badge' + (ENTRY_TONE[String(c.entryType).toUpperCase()] || 0)]}>{c.entryType}</span>
                      : <span className={styles.badge0}>-</span>}
                  </td>
                  <td>
                    {c.lastTag
                      ? <span className={c.lastTone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{c.lastTag}</span>
                      : <span className={styles.chipNone}>no contact</span>}
                  </td>
                  <td className={styles.mono}>{fmtWhen(c.lastContactedAt)}</td>
                  <td><button className={styles.openBtn}><FiPhone /> open</button></td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr><td colSpan="7" className={styles.empty}>queue clear - everyone cooled down or contacted</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {sel && (
        <div className={styles.overlay} onClick={function () { setSel(null); }}>
          <div className={styles.drawer} onClick={function (e) { e.stopPropagation(); }}>
            <header className={styles.drawerHead}>
              <div>
                <h2>{sel.name}</h2>
                <span className={styles.nin}>{sel.nin}</span>
                <span className={styles.mono}>{sel.phone}</span>
              </div>
              <button className={styles.closeBtn} onClick={function () { setSel(null); }}><FiX /></button>
            </header>

            {sel.locked && (
              <div className={styles.lockBanner}>
                <FiAlertTriangle /> cool-down active - read only (14-day / 2-call rule)
              </div>
            )}

            <div className={styles.tagwall}>
              <label className={styles.wallLabel}>POSITIVE</label>
              <div className={styles.wallRow}>
                {tags.filter(function (t) { return t.tone === 'POSITIVE'; }).map(function (t) {
                  return (
                    <button key={t.tag}
                      className={(styles.tagPos) + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                      disabled={sel.locked && t.countsAsAttempt}
                      onClick={function () { setPicked(t); }}>
                      {t.tag}
                    </button>
                  );
                })}
              </div>
              <label className={styles.wallLabel}>NEGATIVE</label>
              <div className={styles.wallRow}>
                {tags.filter(function (t) { return t.tone === 'NEGATIVE'; }).map(function (t) {
                  return (
                    <button key={t.tag}
                      className={(styles.tagNeg) + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                      disabled={sel.locked && t.countsAsAttempt}
                      onClick={function () { setPicked(t); }}>
                      {t.tag.indexOf('site visit') >= 0 ? <FiMapPin /> : (t.countsAsAttempt ? <FiPhone /> : <FiClock />)} {t.tag}
                    </button>
                  );
                })}
              </div>
            </div>

            <input className={styles.noteInput}
              placeholder="optional detail (rare)"
              value={text}
              onChange={function (e) { setText(e.target.value); }} />

            {msg && <div className={styles.err}>{msg}</div>}

            <div className={styles.drawerActions}>
              <button className={styles.saveBtn} disabled={!picked || busy} onClick={save}>
                {busy ? 'saving...' : 'log outcome'}
              </button>
            </div>

            <div className={styles.history}>
              {notes.map(function (n) {
                return (
                  <div key={n.id} className={styles.histRow}>
                    <span className={n.tone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{n.tag}</span>
                    <span className={styles.histMeta}>{n.author || 'system'} - {fmtWhen(n.createdAt)}</span>
                    {n.text && <span className={styles.histText}>{n.text}</span>}
                  </div>
                );
              })}
              {notes.length === 0 && <div className={styles.empty}>no notes yet</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
