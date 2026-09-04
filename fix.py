# fix.py -- fix60: Recovery page reference-style rebuild + backend queue/audit fixes
# Reference pages: Intake + Ledger. Numbers-only HUD. HardwareModal call log.
import os, sys, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("WROTE", os.path.basename(p))

def backup(p):
    if os.path.exists(p):
        shutil.copy2(p, ROOT / ".fix_backup" / (os.path.basename(p) + ".bak60"))
        print("BACKUP", os.path.basename(p))

def patch(p, old, new, label):
    s = read(p)
    if old in s:
        write(p, s.replace(old, new, 1))
        print("OK   ", label)
    else:
        print("MISSING", label)

CTRL = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
SVC  = FE / "services" / "recoveryService.js"
JSX  = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
CSS  = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"

# ================= BACKEND PATCHES =================
# 1) Badge: titled non-legacy projects must read "New Title" (LandProject has no getTitleAtIntake)
patch(CTRL,
"            Boolean ta = readBool(p, \"getTitleAtIntake\", \"isTitleAtIntake\");\n            if (Boolean.TRUE.equals(ta)) return \"New Title\";",
"            Object title = call(p, \"getLandTitle\");\n            if (title != null) return \"New Title\";",
"backend: entryType via landTitle")

# 2) Queue eligibility: use REAL owed math (activeTotalOwed / receivableTotalOwed)
patch(CTRL,
"            Number bal = readNum(p, \"getBalance\", \"getAmountOwed\", \"getOutstandingBalance\");\n            if (bal != null) { if (bal.doubleValue() > 0) return true; else continue; }",
"            Number act = readNum(p, \"activeTotalOwed\");\n            Number rec = readNum(p, \"receivableTotalOwed\");\n            double owed = Math.max(act == null ? 0 : act.doubleValue(), rec == null ? 0 : rec.doubleValue());\n            if (owed > 0) return true;",
"backend: qualifies uses real owed math")

# 3) Audit: AuditService method is logAction(String,String) - include the name
patch(CTRL,
"            if (!(name.equals(\"log\") || name.equals(\"record\") || name.equals(\"write\"))) continue;",
"            if (!(name.equals(\"log\") || name.equals(\"record\") || name.equals(\"write\") || name.equals(\"logAction\"))) continue;",
"backend: audit logAction wired")

# 4) Header bell: expose getTaskCount mapped to stats.dueNow
patch(SVC,
"  getStats:  () => api.get('/recovery/stats'),",
"  getStats:  () => api.get('/recovery/stats'),\n  getTaskCount: () => api.get('/recovery/stats').then(r => r.data.dueNow),",
"service: getTaskCount for header bell")

# ================= FRONTEND REWRITE =================
backup(JSX); backup(CSS)

JSX_CONTENT = r"""import React, { useState, useEffect, useCallback } from 'react';
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
"""
# ReactDOM import needed for createPortal
JSX_CONTENT = JSX_CONTENT.replace(
    "import React, { useState, useEffect, useCallback } from 'react';",
    "import React, { useState, useEffect, useCallback } from 'react';\nimport ReactDOM from 'react-dom';")

write(JSX, JSX_CONTENT)

CSS_CONTENT = r"""/* PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css */
/* fix60: reference-style rebuild - tokens verbatim from Ledger/Intake */
.container {
  --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981; --amber: #f59e0b;
  --panel-bg: linear-gradient(160deg,#1c3335 0%,#213E40 100%);
  --radius: 10px; --radius-sm: 6px;
  --fs-h1: clamp(18px,2.5vw,24px); --fs-sub: clamp(9px,0.9vw,11px);
  --fs-label: clamp(8px,0.85vw,10px); --fs-value: clamp(13px,1.4vw,17px);
  --fs-td: clamp(11px,1.15vw,13px); --fs-meta: clamp(9px,0.95vw,11px); --fs-btn: clamp(9px,0.9vw,11px);
  max-width: 1400px; width: 100%; margin: 0 auto;
  padding: clamp(12px,2vh,22px) clamp(12px,2vw,24px) 16px;
  font-family: 'Inter',sans-serif; color: #fff;
  display: flex; flex-direction: column; gap: clamp(10px,1.5vw,18px);
  box-sizing: border-box;
  animation: warmBoot 0.6s cubic-bezier(0.2,1,0.3,1) both;
}
@keyframes warmBoot { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* glass page header - verbatim from Ledger/Intake */
.pageHeader {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
  gap: clamp(8px,1.2vw,14px);
  border-left: clamp(3px,0.4vw,5px) solid var(--orange);
  padding: clamp(8px,1.2vw,14px) clamp(14px,1.8vw,22px);
  background: rgba(255,255,255,0.62); border-radius: 0 12px 12px 0;
  backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
.title { font-family: 'Cinzel',serif; color: var(--navy-deep); font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin: 0; line-height: 1.1; }
.subtitle { color: #64748b; font-size: var(--fs-sub); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

/* numbers-only HUD - Payments sumCard language */
.countsHUD { display: grid; grid-template-columns: repeat(auto-fit,minmax(120px,1fr)); gap: clamp(8px,1.2vw,14px); }
.countCard {
  background: var(--panel-bg); border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(10px,1.4vw,16px); display: flex; flex-direction: column; gap: 4px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.2); transition: border-color 0.2s, transform 0.2s;
}
.countCard:hover { border-color: var(--orange); transform: translateY(-2px); }
.countCard label { font-family: 'Inter',sans-serif; font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 2px; }
.countCard strong { font-family: 'Space Mono',monospace; font-size: var(--fs-value); font-weight: 700; color: #fff; }

/* controls: white Ledger search + standard filter buttons */
.controls { display: flex; flex-direction: column; gap: 8px; }
.searchBlock { width: min(100%, clamp(220px,38vw,420px)); }
.searchInner { position: relative; display: flex; align-items: center; background: #fff; border: 1.5px solid #c8d6d7; border-radius: 6px; height: clamp(36px,4.5vw,44px); transition: border-color .2s, box-shadow .2s; }
.searchInner:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238,140,58,0.18); }
.searchIcon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--orange); pointer-events: none; }
.searchInput { width: 100%; border: none; outline: none; background: transparent; color: #1a2e30; padding: 0 34px 0 38px; font-weight: 600; font-size: 12px; height: 100%; font-family: 'Inter',sans-serif; }
.searchInput::placeholder { color: rgba(26,46,48,0.35); font-weight: 500; }
.searchInput::-webkit-search-cancel-button { -webkit-appearance: none; appearance: none; }
.searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--orange); cursor: pointer; display: flex; padding: 4px; border-radius: 4px; }
.searchClearBtn:hover { background: rgba(238,140,58,0.15); }
.filterRail { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; }
.filterRail::-webkit-scrollbar { display: none; }
.filterBtn { background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 8px 16px; border-radius: 6px; font-weight: 900; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; white-space: nowrap; transition: all .2s; font-family: 'Inter',sans-serif; }
.filterBtn:hover { background: rgba(238,140,58,0.12); color: var(--orange); border-color: var(--orange); }
.activeFilter { background: var(--orange) !important; color: #1a2e30 !important; border-color: var(--orange) !important; }
.filterBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* cards */
.grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(300px,1fr)); gap: clamp(10px,1.4vw,16px); }
.card {
  background: var(--panel-bg); border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(12px,1.6vw,18px); display: flex; flex-direction: column; gap: 8px; cursor: pointer;
  box-shadow: 0 8px 28px rgba(0,0,0,0.16); transition: border-color .2s, transform .2s, box-shadow .2s;
}
.card:hover { border-color: rgba(238,140,58,0.45); transform: translateY(-2px); box-shadow: 0 12px 36px rgba(0,0,0,0.28); }
.cardHead { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.p1,.p2,.p3 { font-family: 'Space Mono',monospace; font-size: 10px; font-weight: 900; letter-spacing: 1px; border-radius: 999px; padding: 3px 9px; border: 1px solid; }
.p1 { color: #fca5a5; background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.4); }
.p2 { color: #fcd34d; background: rgba(245,158,11,0.12); border-color: rgba(245,158,11,0.4); }
.p3 { color: #34d399; background: rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.4); }
.badgeFolder,.badgeTitle,.badgeLegacy { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 700; letter-spacing: 1px; border-radius: 999px; padding: 3px 9px; border: 1px solid; }
.badgeFolder { color: var(--orange); background: rgba(238,140,58,0.10); border-color: rgba(238,140,58,0.35); }
.badgeTitle  { color: var(--green); background: rgba(16,185,129,0.10); border-color: rgba(16,185,129,0.35); }
.badgeLegacy { color: #64748b; background: rgba(100,116,139,0.12); border-color: rgba(100,116,139,0.35); }
.dots { display: inline-flex; gap: 4px; margin-left: auto; }
.dotOn,.dotOff { width: 8px; height: 8px; border-radius: 50%; }
.dotOn { background: var(--orange); box-shadow: 0 0 4px var(--orange); }
.dotOff { border: 1px solid rgba(255,255,255,0.3); }
.cname { font-size: var(--fs-td); font-weight: 800; margin: 0; text-transform: uppercase; letter-spacing: 0.3px; }
.nin { font-family: 'Space Mono',monospace; font-size: 11px; color: var(--orange); }
.mono { font-family: 'Space Mono',monospace; font-size: 11px; color: rgba(255,255,255,0.6); }
.loc { font-size: var(--fs-meta); color: rgba(255,255,255,0.5); }
.cardFoot { display: flex; align-items: center; gap: 8px; justify-content: space-between; flex-wrap: wrap; }
.chipPos,.chipNeg,.chipNone { font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 999px; white-space: nowrap; border: 1px solid; }
.chipPos { background: rgba(16,185,129,0.10); color: #34d399; border-color: rgba(16,185,129,0.35); }
.chipNeg { background: rgba(239,68,68,0.12); color: #fca5a5; border-color: rgba(239,68,68,0.4); }
.chipNone { color: rgba(255,255,255,0.4); border: 1px dashed rgba(255,255,255,0.25); }
.openBtn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  height: clamp(32px,3.8vw,38px); padding: 0 clamp(12px,1.5vw,17px);
  background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.8);
  border-radius: var(--radius-sm); font-family: 'Inter',sans-serif; font-weight: 900; font-size: var(--fs-btn);
  text-transform: uppercase; letter-spacing: 1px; cursor: pointer; transition: all 0.2s; margin-top: 4px;
}
.openBtn:hover { background: rgba(238,140,58,0.12); color: var(--orange); border-color: var(--orange); }
.openBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* empty / loading - Ledger language */
.emptyState {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;
  padding: clamp(40px,6vw,70px) 20px; background: var(--panel-bg); border: 1.5px solid var(--orange-border);
  border-radius: var(--radius); font-family: 'Space Mono',monospace; font-size: var(--fs-meta);
  font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.25);
  grid-column: 1 / -1;
}
.loadingSpinner { width: 32px; height: 32px; border: 3px solid rgba(238,140,58,0.15); border-top-color: var(--orange); border-radius: 50%; animation: spin 0.9s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* locked tray */
.lockedTray { background: var(--panel-bg); border: 1.5px solid var(--orange-border); border-radius: var(--radius); overflow: hidden; }
.trayToggle {
  width: 100%; display: flex; align-items: center; gap: 8px; background: transparent; border: none;
  color: #fcd34d; padding: 12px 16px; font-family: 'Inter',sans-serif; font-weight: 900; font-size: var(--fs-btn);
  letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer;
}
.trayToggle:hover { background: rgba(245,158,11,0.08); }
.trayToggle:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }
.trayList { border-top: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; }
.trayRow { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 10px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); cursor: pointer; }
.trayRow:hover { background: rgba(255,255,255,0.04); }
.trayEmpty { padding: 12px 16px; color: rgba(255,255,255,0.3); font-size: var(--fs-meta); font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }

/* modal innards */
.metaRow { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.attemptLine { display: flex; align-items: center; gap: 8px; font-size: var(--fs-meta); font-weight: 800; color: rgba(255,255,255,0.5); margin-bottom: 8px; }
.attemptLine svg { color: var(--orange); }
.lockBanner {
  display: flex; align-items: center; gap: 8px; background: rgba(245,158,11,0.12);
  border: 1px solid rgba(245,158,11,0.4); border-radius: 6px; padding: 10px 12px;
  font-size: var(--fs-meta); font-weight: 800; color: #fcd34d; margin-bottom: 10px;
}
.tagwall { margin-bottom: 10px; }
.wallLabel { display: block; font-size: var(--fs-label); font-weight: 900; letter-spacing: 2px; color: rgba(255,255,255,0.5); text-transform: uppercase; margin: 8px 0 6px; }
.wallRow { display: flex; gap: 8px; flex-wrap: wrap; }
.tagPos,.tagNeg { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 8px 14px; font-size: 12px; font-weight: 700; cursor: pointer; border: 1px solid; transition: all 0.2s; }
.tagPos { background: rgba(16,185,129,0.10); color: #34d399; border-color: rgba(16,185,129,0.35); }
.tagNeg { background: rgba(239,68,68,0.12); color: #fca5a5; border-color: rgba(239,68,68,0.4); }
.tagPos:hover:not(:disabled) { background: rgba(16,185,129,0.2); }
.tagNeg:hover:not(:disabled) { background: rgba(239,68,68,0.2); }
.tagPos:disabled,.tagNeg:disabled { opacity: 0.35; cursor: not-allowed; }
.tagOn { outline: 2px solid var(--orange); outline-offset: 2px; }
.histSection { margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px; display: flex; flex-direction: column; gap: 8px; }
.histRow { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: var(--fs-meta); }
.histMeta { color: rgba(255,255,255,0.45); font-weight: 700; }
.histText { color: rgba(255,255,255,0.8); }

/* toasts - verbatim Intake values */
.toastStack { position: fixed; bottom: clamp(16px,2.5vh,28px); right: clamp(16px,2vw,28px); z-index: 99999; display: flex; flex-direction: column; gap: 8px; max-width: min(420px,90vw); pointer-events: none; }
.toast { background: #1a2e30; color: #fff; border: 1px solid rgba(238,140,58,0.28); padding: 12px 20px; border-radius: 6px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); font-family: 'Inter',sans-serif; font-size: 12px; font-weight: 700; animation: slideIn 0.3s ease-out; pointer-events: all; }
.toast_error { background: #ef4444; border-color: #ef4444; }
.toast_success { background: #10b981; border-color: #10b981; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

@media (max-width: 600px) {
  .countsHUD { grid-template-columns: 1fr 1fr; }
  .grid { grid-template-columns: 1fr; }
  .searchBlock { width: 100%; }
}
"""
write(CSS, CSS_CONTENT)

# ================= GIT =================
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix60: recovery reference-style rebuild + queue/audit/bell fixes"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE fix60")