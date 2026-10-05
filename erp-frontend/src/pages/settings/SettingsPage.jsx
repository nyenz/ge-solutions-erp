// PATH: erp-frontend/src/pages/settings/SettingsPage.jsx
// GOLDEN SEED -- SETTINGS PAGE (fix121: Report Studio parity rewrite).
// The five stacked, independently-collapsing hwPanels are gone. Settings now
// reads exactly like the Reports workstation: a chip dock of tabs up top
// (the same tile spec as Report Studio's dataset row -- label + monospace
// count, solid-orange when active) feeding ONE gradient card below, whose
// head bar recolors per section (orange/cyan/violet/red/slate) the way
// Report Studio's own panels stay orange throughout. Same CornerDecor
// brackets, same click-anywhere collapsible head, same button language.
import { portalRoot } from '../../components/common/portalRoot';
import React, { useState, useEffect, useCallback } from 'react';
import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff, FiSliders, FiMonitor, FiChevronDown, FiArchive, FiCopy } from 'react-icons/fi';
import { createPortal } from 'react-dom';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { usePreferences } from '../../context/usePreferences';
import settingsService from '../../services/settingsService';
import landService from '../../services/landService';
import HardwareInput from '../../components/common/HardwareInput';
import HardwareModal from '../../components/common/HardwareModal';
import BackToTopButton from '../../components/common/BackToTopButton';
import CornerDecor from '../../components/ui/CornerDecor';
import styles from './SettingsPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';
import { LoadingState } from '../../components/common/LoadingState';
import { roleFlags, manageableRanks, rankLabel, rankOf, LANDING_OPTIONS, RANKS as RANK_INFO } from '../../utils/roles';
import { errorText } from '../../utils/errorText';
const TOAST_ICONS = { success: <FiCheckSquare aria-hidden="true" />, error: <FiAlertCircle aria-hidden="true" />, warn: <FiAlertTriangle aria-hidden="true" />, info: <FiInfo aria-hidden="true" /> };

/* Every option here is wired to real CSS in index.css -- see the note at the
   top of context/PreferencesProvider.jsx for what each one moves. */
const PREF_GROUPS = [
  { key: 'theme', group: 'Display', label: 'Page theme', hint: 'CREAM and SLATE change the background and keep navy panels. LIGHT makes the panels light too.',
    options: [{ value: 'light', label: 'CREAM' }, { value: 'dark', label: 'SLATE' }, { value: 'bright', label: 'LIGHT' }] },
  { key: 'uiScale', group: 'Display', label: 'Interface size', hint: 'Scales the whole app, not just text.',
    options: [{ value: '90', label: '90%' }, { value: '100', label: '100%' }, { value: '110', label: '110%' }, { value: '125', label: '125%' }] },
  { key: 'statSize', group: 'Display', label: 'Summary box size', hint: 'The figures at the top of Recovery, Client Portfolio, Payments, Expenses and Audit.',
    options: [{ value: 'small', label: 'SMALL' }, { value: 'standard', label: 'STANDARD' }, { value: 'large', label: 'LARGE' }] },
  { key: 'tips', group: 'Interaction', label: 'Hover explainers', hint: 'How long before they appear, or turn them off.',
    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'slow', label: 'SLOW' }, { value: 'off', label: 'OFF' }] },
  { key: 'motion', group: 'Interaction', label: 'Animation', hint: 'Turn off movement and fades across the app.',
    options: [{ value: 'full', label: 'ON' }, { value: 'reduced', label: 'REDUCED' }] },
  { key: 'contrast', group: 'Interaction', label: 'Table contrast', hint: 'Stronger row lines in tables (Ledger, Clients, Payments, Expenses, Reports, Folder).',
    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'high', label: 'HIGH' }] },
  // fix181 (14.0a): the start page after sign-in; only pages this rank may open, none for Employee (always New Project)
  { key: 'landing', group: 'Interaction', label: 'Start page', hint: 'Where signing in takes you. Saved for you only.',
    options: LANDING_OPTIONS, staffOnly: true },
  { key: 'notifPoll', group: 'Notifications', label: 'Notification refresh', hint: 'How often the bell and the red "due for a call" number refresh. Paused while this tab is hidden. MANUAL refreshes when you open the bell.',
    options: [{ value: '300', label: '5 MIN' }, { value: '900', label: '15 MIN' }, { value: '0', label: 'MANUAL' }] },
];

/* fix127: group PREF_GROUPS into named sections so Appearance
   renders as three separated cards instead of one long flat
   list -- same data, grouped once instead of re-diffed against
   the previous row every render. */
const prefSections = (flags) => ['Display', 'Interaction', 'Notifications'].map(name => ({
  name,
  items: PREF_GROUPS.filter(g => g.group === name && (!g.staffOnly || flags.isStaff)),
})).filter(sec => sec.items.length > 0);

// fix181 (14.1d): the key rules, shown ticking off as the person types (the server rules stay the source of truth)
const KEY_RULES = [
  { id: 'len', label: 'At least 8 characters', test: (v) => v.length >= 8 },
  { id: 'cap', label: 'One capital letter', test: (v) => /[A-Z]/.test(v) },
  { id: 'num', label: 'One number', test: (v) => /[0-9]/.test(v) },
];
// fix181 (15.4d): the same username rule as the server
const USERNAME_RULE = /^[A-Za-z0-9._-]{3,30}$/;
const fmtDateTime = (d) => (d ? new Date(d).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '');
const daysLeft = (d) => (d ? Math.ceil((new Date(d).getTime() - Date.now()) / 86400000) : null);

const SettingsPage = () => {
  const { user, updateSession } = useAuth();
  const navigate = useNavigate();
  const { prefs, setPref, resetPrefs } = usePreferences();
  // fix181: Staff and Archive for Director and Admin; Danger Zone (wipe) for the Admin only
  const flags = roleFlags(user);
  const isOwner = flags.isOwnerLevel;
  const locked = !!user?.mustChangePassword;
  const RANKS = manageableRanks(user);
  // fix181 (17.10, 21.9): links can open a tab (/settings?tab=staff, ?tab=appearance)
  const [settingsParams] = useSearchParams();
  const TAB_ALIASES = { staff: 'governance', appearance: 'appearance', security: 'security', archive: 'deleted', danger: 'danger' };
  const [tab, setTab] = useState(() => TAB_ALIASES[(settingsParams.get('tab') || '').toLowerCase()] || 'appearance');
  const [panelOpen, setPanelOpen] = useState(true);
  const [toasts, setToasts] = useState([]);
  // fix181 (15.6c): success and info close after 5 seconds; errors and warnings stay until closed (or 20 seconds)
  const toast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(p => [...p, { id, message, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), (type === 'error' || type === 'warn') ? 20000 : 5000);
  }, []);
  const [oldPw, setOldPw] = useState(''); const [newPw, setNewPw] = useState(''); const [newPw2, setNewPw2] = useState('');
  const [showOld, setShowOld] = useState(false); const [showNew, setShowNew] = useState(false);
  const [savingPw, setSavingPw] = useState(false);
  const [ops, setOps] = useState(null); const [opsLoading, setOpsLoading] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const firstRank = RANKS.includes('ROLE_MANAGER') ? 'ROLE_MANAGER' : (RANKS[RANKS.length - 1] || 'ROLE_EMPLOYEE');
  const [newOp, setNewOp] = useState({ username: '', email: '', role: firstRank });
  const [reveal, setReveal] = useState(null);
  const [copied, setCopied] = useState(false);
  const [rankFor, setRankFor] = useState(null);      // { op, role } -- the rank modal (14.5b, 15.4b)
  const [resetFor, setResetFor] = useState(null);    // the person whose key is about to be reset (14.3d)
  const [wipeText, setWipeText] = useState('');
  const [wipeKey, setWipeKey] = useState('');
  const [wiping, setWiping] = useState(false);
  const [wipeResult, setWipeResult] = useState(null);
  const [deleted, setDeleted] = useState(null); const [delLoading, setDelLoading] = useState(false); const [delError, setDelError] = useState('');
  const [delSearch, setDelSearch] = useState('');
  const [restoreAsk, setRestoreAsk] = useState(null);   // { project, message } -- clash confirmation (14.7c)

  const loadOps = useCallback(async () => {
    if (!isOwner) return;
    setOpsLoading(true);
    try { setOps(await settingsService.getAllOperators()); } catch (e) { toast(e.message, 'error'); }
    finally { setOpsLoading(false); }
  }, [isOwner, toast]);
  const loadDeleted = useCallback(async () => {
    if (!isOwner) return;
    setDelLoading(true); setDelError('');
    try { setDeleted(await landService.getDeletedProjects()); }
    catch (e) { setDelError(errorText(e)); }   // fix181 (14.7b): a failed load is an error with Retry, not "nothing deleted"
    finally { setDelLoading(false); }
  }, [isOwner]);
  // fix181 (15.6b): each tab loads its own data the first time it is opened, not on page load
  useEffect(() => {
    if (locked) return;
    if (tab === 'governance' && ops === null && !opsLoading) loadOps();
    if (tab === 'deleted' && deleted === null && !delLoading && !delError) loadDeleted();
  }, [tab, locked, ops, opsLoading, loadOps, deleted, delLoading, delError, loadDeleted]);

  const rulesOk = KEY_RULES.every(r => r.test(newPw));
  const sameAsOld = !!newPw && newPw === oldPw;
  const repeatOk = !!newPw2 && newPw2 === newPw;
  const canChangePw = !!oldPw && rulesOk && repeatOk && !sameAsOld && !savingPw;
  const changePw = async (e) => {
    if (e) e.preventDefault();
    if (!canChangePw) return;
    setSavingPw(true);
    try {
      const res = await settingsService.changePersonalPassword(oldPw, newPw);
      updateSession(res);   // fix181: this device keeps working with the new token; other devices are signed out
      setOldPw(''); setNewPw(''); setNewPw2('');
      if (locked) { navigate('/', { replace: true }); return; }   // 14.1a: unlocked -> the person's start page
      toast('Your key was changed. Other devices were signed out.', 'success');
    }
    catch (err) { toast(err.message, 'error'); }
    finally { setSavingPw(false); }
  };
  const newUserOk = USERNAME_RULE.test(newOp.username.trim());
  const newEmailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(newOp.email.trim());
  const createOp = async () => {
    try {
      const res = await settingsService.registerManager(newOp);
      setAddOpen(false); setCopied(false); setReveal({ username: res.username, key: res.temporaryPassword });
      setNewOp({ username: '', email: '', role: firstRank });
      loadOps();
    } catch (e) { toast(e.message, 'error'); }
  };
  const changeRank = async () => {
    const { op, role } = rankFor;
    setRankFor(null);
    if (!role || role === op.role) return;   // 14.5b: the same rank is not a change
    try { await settingsService.updateOperatorRole(op.username, role); toast(`${op.username} is now ${rankLabel(role)}. They must sign in again.`, 'success'); }
    catch (e) { toast(e.message, 'error'); }
    finally { loadOps(); }   // 14.5f: the list is reloaded after a failure too
  };
  const toggleOp = async (op) => {
    try { await settingsService.toggleOperator(op.username, !op.active); toast(op.active ? `${op.username} is suspended.` : `${op.username} is active again.`, 'warn'); }
    catch (e) { toast(e.message, 'error'); }
    finally { loadOps(); }
  };
  const resetKey = async () => {
    const op = resetFor;
    setResetFor(null);
    try { const key = await settingsService.resetOperatorKey(op.username); setCopied(false); setReveal({ username: op.username, key }); }
    catch (e) { toast(e.message, 'error'); }
    finally { loadOps(); }
  };
  const copyKey = async () => {
    try { await navigator.clipboard.writeText(reveal?.key || ''); setCopied(true); }
    catch { toast('Copy did not work here. Select the key and copy it by hand.', 'warn'); }
  };
  const wipe = async () => {
    setWiping(true);
    try {
      const r = await settingsService.wipeAllData(wipeKey);
      setWipeResult(r);              // 14.4e: a result box with what was deleted
      setOps(null); setDeleted(null); // the local lists are stale now
    }
    catch (e) { toast(e.message, 'error'); }
    finally { setWiping(false); setWipeText(''); setWipeKey(''); }
  };
  const restore = async (p, force = false) => {
    try {
      await landService.restoreProject(p.id, force);
      setRestoreAsk(null);
      toast(`Project #${p.projectIndex} was restored${p.pending ? ' (still Pending)' : ''}.`, 'success');
      loadDeleted();
    } catch (e) {
      const msg = errorText(e);
      const raw = String(e?.response?.data?.message || '');
      if (!force && raw.startsWith('RESTORE_CLASH')) setRestoreAsk({ project: p, message: msg });
      else { setRestoreAsk(null); toast(msg, 'error'); }
    }
  };
  const rankClass = (r) => r === 'ROLE_ADMIN' ? styles.rankAdmin : r === 'ROLE_DIRECTOR' ? styles.rankDirector : r === 'ROLE_MANAGER' ? styles.rankManager : r === 'ROLE_SECRETARY' ? styles.rankSecretary : styles.rankEmployee;
  // a person can be managed here only when they rank below the one signed in (the server checks this too)
  const canManageOp = (op) => !op.root && rankOf(op.role) < flags.rank && op.username !== user?.username;

  const delRows = (deleted || []).filter(p => {
    const q = delSearch.trim().toLowerCase();
    if (!q) return true;
    return [p.projectIndex, p.plotLabel, p.district, p.projectType, p.reason, p.deletedBy, ...(p.clientNames || [])]
      .some(v => v && String(v).toLowerCase().includes(q));
  });

  /* The dock: one tab on screen at a time. fix181 (15.6a): while the temporary key must be changed, ONLY Security.
     Counts show "..." until that tab has loaded (15.6b). */
  const TABS = locked
    ? [{ key: 'security', label: 'SECURITY', icon: FiKey, accent: 'cyan', count: null }]
    : [
      { key: 'appearance', label: 'APPEARANCE', icon: FiSliders, accent: 'orange', count: prefSections(flags).reduce((n, sec) => n + sec.items.length, 0) },
      { key: 'security', label: 'SECURITY', icon: FiKey, accent: 'cyan', count: null },
      ...(isOwner ? [{ key: 'governance', label: 'STAFF', icon: FiShield, accent: 'green', count: ops === null ? '...' : ops.length }] : []),
      ...(flags.canWipe ? [{ key: 'danger', label: 'DANGER ZONE', icon: FiAlertTriangle, accent: 'red', count: null }] : []),
      ...(isOwner ? [{ key: 'deleted', label: 'ARCHIVE', icon: FiArchive, accent: 'yellow', count: deleted === null ? '...' : deleted.length }] : []),
    ];
  const activeTab = TABS.find(t => t.key === tab) || TABS[0];
  const selectTab = (key) => { setTab(key); setPanelOpen(true); };
  // fix181 (14.6d): the subtitle names only what this person can see
  const subtitle = locked ? 'Choose your own key to unlock the system'
    : ['Appearance', 'security', ...(isOwner ? ['staff'] : []), ...(flags.canWipe ? ['the danger zone'] : []), ...(isOwner ? ['the archive'] : [])]
      .join(', ').replace(/, ([^,]*)$/, ' and $1');

  return (
    <div className={styles.container}>
      {typeof document !== 'undefined' && createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
          {toasts.map(t => (<div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
            <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
            <span className={styles.toastMsg}>{t.message}</span>
            <button className={styles.toastClose} onClick={() => setToasts(p => p.filter(x => x.id !== t.id))} aria-label="Dismiss"><FiX aria-hidden="true" /></button>
          </div>))}
        </div>, portalRoot())}
      <header className={styles.pageHeader}>
        <div className={styles.pageHeaderLeft}>
          <h1 className={styles.title}>Settings</h1>
          <p className={styles.subtitle}>{subtitle}</p>
        </div>
        {locked && (<div className={`${styles.handbrakeBadge} ${styles.blink}`}><FiLock aria-hidden="true" /> CHANGE YOUR KEY TO UNLOCK THE SYSTEM</div>)}
      </header>

      <div className={styles.workstationGrid}>
        {/* ── TAB DOCK ── fix181 (15.6e): real tabs for screen readers */}
        <div className={styles.dockRow}>
          <div className={styles.tabDock}>
            <div className={styles.tabRow} role="tablist" aria-label="Settings sections">
              {TABS.map(t => (
                <button
                  key={t.key} type="button" role="tab" id={`settings-tab-${t.key}`}
                  className={activeTab.key === t.key ? styles.tabOn : styles.tab}
                  data-accent={t.accent}
                  onClick={() => selectTab(t.key)}
                  aria-selected={activeTab.key === t.key} aria-controls="settings-panel"
                >
                  <t.icon aria-hidden="true" />
                  <span>{t.label}</span>
                  {t.count !== null && <span className={styles.tabCount}>{t.count}</span>}
                </button>
              ))}
            </div>
          </div>
          <span className={styles.dockBadge}>{TABS.length} SECTION{TABS.length === 1 ? '' : 'S'}</span>
        </div>

        {/* ── ACTIVE CARD -- one gradient panel, recolored per section ── */}
        <div className={styles.workstationCard} data-accent={activeTab.accent} role="tabpanel" id="settings-panel" aria-labelledby={`settings-tab-${activeTab.key}`}>
          <CornerDecor hideTop />
          <div
            className={panelOpen ? `${styles.panelHeadRow} ${styles.panelHeadRowOpen}` : styles.panelHeadRow}
            role="button" tabIndex={0}
            onClick={() => setPanelOpen(o => !o)}
            onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setPanelOpen(o => !o); } }}
            aria-expanded={panelOpen} aria-label={`Collapse or expand ${activeTab.label.toLowerCase()}`}
          >
            <div className={styles.panelHeadTitle}><activeTab.icon className={styles.panelHeadIcon} aria-hidden="true" /> {activeTab.label}</div>
            <span className={styles.headToggle}><FiChevronDown className={panelOpen ? styles.pickIconOpen : ''} aria-hidden="true" /></span>
          </div>

          {panelOpen && <div className={styles.panelBody}><div className={styles.panelInner}>

            {activeTab.key === 'appearance' && (
              <>
                <div className={styles.securityAlert}><FiMonitor aria-hidden="true" /><span>These are saved on this device for you only. Someone else signing in here keeps their own choices.</span></div>
                {/* fix127: three lighter cream cards (Report Catalogue's own
                    #f2ede4 tone) instead of one long dark list -- each
                    section groups its own rows so Appearance reads as
                    organised clusters, not seven settings in a row. */}
                <div className={styles.prefSectionsGrid}>
                  {prefSections(flags).map(section => (
                    <div key={section.name} className={styles.prefGroupBox}>
                      <div className={styles.prefGroupLabel}>{section.name}</div>
                      {section.items.map(group => (
                        <div key={group.key} className={styles.prefRow}>
                          <div className={styles.prefLabel}>
                            <strong>{group.label}</strong>
                            <span>{group.hint}</span>
                          </div>
                          <div className={styles.prefOptions} role="group" aria-label={group.label}>
                            {group.options.map(opt => (
                              <button
                                key={opt.value}
                                type="button"
                                className={prefs[group.key] === opt.value ? styles.prefBtnActive : styles.prefBtn}
                                aria-pressed={prefs[group.key] === opt.value}
                                onClick={() => setPref(group.key, opt.value)}
                              >
                                {opt.label}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
                <div className={styles.submitRow}>
                  <button type="button" className={styles.commitBtn} onClick={resetPrefs}><FiRotateCcw aria-hidden="true" /> RESET APPEARANCE</button>
                </div>
              </>
            )}

            {activeTab.key === 'security' && (
              <form onSubmit={changePw} autoComplete="on">
                {/* fix181 (15.6d): a hidden username so the browser's password manager knows whose key this is */}
                <input type="text" name="username" autoComplete="username" value={user?.username || ''} readOnly hidden />
                <div className={styles.securityAlert}><FiShield aria-hidden="true" /><span>{locked ? 'You signed in with a temporary key. Choose your own key to unlock the system.' : 'Changing your key signs you out on your other devices.'}</span></div>
                <div className={styles.dualRow}>
                  <div className={styles.eyeInpWrap}>
                    <HardwareInput id="current-key" name="current-password" autoComplete="current-password" label="CURRENT KEY" type={showOld ? 'text' : 'password'} value={oldPw} onChange={e => setOldPw(e.target.value)} />
                    <button type="button" className={styles.eyeBtn} onClick={() => setShowOld(s => !s)} aria-label={showOld ? 'Hide the current key' : 'Show the current key'}>{showOld ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}</button>
                  </div>
                  <div className={styles.eyeInpWrap}>
                    <HardwareInput id="new-key" name="new-password" autoComplete="new-password" label="NEW KEY" type={showNew ? 'text' : 'password'} value={newPw} onChange={e => setNewPw(e.target.value)} />
                    <button type="button" className={styles.eyeBtn} onClick={() => setShowNew(s => !s)} aria-label={showNew ? 'Hide the new key' : 'Show the new key'}>{showNew ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}</button>
                  </div>
                </div>
                <div className={styles.dualRow}>
                  <div className={styles.eyeInpWrap}>
                    <HardwareInput id="new-key-repeat" name="new-password-repeat" autoComplete="new-password" label="REPEAT NEW KEY" type={showNew ? 'text' : 'password'} value={newPw2} onChange={e => setNewPw2(e.target.value)} />
                  </div>
                  <ul className={styles.keyRules} aria-label="Key rules">
                    {KEY_RULES.map(r => (
                      <li key={r.id} className={r.test(newPw) ? styles.ruleOk : styles.ruleTodo}>{r.test(newPw) ? '✓' : '•'} {r.label}</li>
                    ))}
                    <li className={newPw2 ? (repeatOk ? styles.ruleOk : styles.ruleBad) : styles.ruleTodo}>{repeatOk ? '✓' : '•'} Both new boxes match</li>
                    {sameAsOld && <li className={styles.ruleBad}>The new key must be different from the current one</li>}
                  </ul>
                </div>
                <div className={styles.submitRow}>
                  <button type="submit" className={styles.commitBtn} disabled={!canChangePw}><FiKey aria-hidden="true" /> {savingPw ? 'SAVING...' : 'SAVE NEW KEY'}</button>
                </div>
              </form>
            )}

            {activeTab.key === 'governance' && isOwner && (
              <>
                <div className={styles.ledgerActions}>
                  <button type="button" className={styles.addOpBtn} onClick={() => setAddOpen(true)} disabled={RANKS.length === 0}><FiUserPlus aria-hidden="true" /> ADD STAFF</button>
                </div>
                <div className={styles.statusLegend}>
                  <span className={styles.legendDot} style={{ background: '#10b981' }} /><span className={styles.legendText}>ACTIVE</span>
                  <span className={styles.legendSep} />
                  <span className={styles.legendDot} style={{ background: '#ef4444' }} /><span className={styles.legendText}>SUSPENDED</span>
                </div>
                <div className={styles.staffStream}>
                  {opsLoading && <LoadingState label="Loading staff..." tone="bare" />}
                  {!opsLoading && (ops || []).map(op => {
                    const left = op.mustChangePassword ? daysLeft(op.tempKeyExpiresAt) : null;
                    return (
                    <div key={op.username} className={`${styles.opCard} ${!op.active ? styles.cardDimmed : ''}`}>
                      <div className={styles.opHeader}>
                        <div className={styles.opAvatar}>{(op.username || '?').charAt(0).toUpperCase()}<span className={`${styles.statusDot} ${op.active ? styles.dotGreen : styles.dotRed}`} /></div>
                        <div className={styles.opInfo}>
                          <strong>{op.username}{op.root ? ' (ADMIN)' : ''}{op.demo ? ' · DEMO' : ''}</strong>
                          <span className={rankClass(op.role)}>{rankLabel(op.role).toUpperCase()}</span>
                        </div>
                        <div className={styles.opActions}>
                          <button type="button" className={styles.rankBtn} disabled={!canManageOp(op)} onClick={() => setRankFor({ op, role: op.role })} aria-label={`Change the rank of ${op.username}`}><FiShield aria-hidden="true" /></button>
                          <button type="button" className={`${styles.killSwitchBtn} ${op.active ? styles.killSwitchActive : styles.killSwitchInactive}`} disabled={!canManageOp(op)}
                            onClick={() => toggleOp(op)}
                            aria-label={op.active ? `Suspend ${op.username}` : `Activate ${op.username}`}>
                            <FiPower aria-hidden="true" />
                          </button>
                          <button type="button" className={styles.resetTrigger} disabled={!canManageOp(op)}
                            onClick={() => setResetFor(op)}
                            aria-label={`Reset the key of ${op.username}`}>
                            <FiRotateCcw aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                      <div className={styles.opDetails}>
                        <p><FiInfo aria-hidden="true" /> {op.email || 'no email on file'}</p>
                        {/* fix181 (15.4e): a temporary key is valid for 7 days */}
                        {left !== null && <p className={left <= 0 ? styles.ruleBad : styles.ruleTodo}>{left <= 0 ? 'Temporary key expired. Reset it to give a new one.' : `Temporary key not changed yet: expires in ${left} day${left === 1 ? '' : 's'}.`}</p>}
                      </div>
                    </div>
                    );
                  })}
                </div>
              </>
            )}

            {activeTab.key === 'danger' && flags.canWipe && (
              <>
                {/* fix181 (14.4a, owner choice B): the text says exactly what is deleted and what is kept */}
                <div className={styles.dangerAlert}><FiAlertTriangle aria-hidden="true" /><span>This deletes every project, client, payment, expense, document and uploaded file, every note and notification, the custom status lists and the expense presets. There is no undo. Kept: all staff accounts, the audit trail, document types and the appearance choices.</span></div>
                {wipeResult && (
                  <div className={styles.wipeResult} role="status">
                    <strong>Wipe complete.</strong>
                    <span> Deleted: {Object.entries(wipeResult.deleted || {}).map(([k, v]) => `${v} ${k}`).join(', ') || 'nothing'}.</span>
                    <span> Files deleted: {wipeResult.filesDeleted ?? 0}.</span>
                    {Number(wipeResult.filesFailed) > 0 && <span className={styles.ruleBad}> {wipeResult.filesFailed} files could NOT be deleted. Check the Cloudinary dashboard.</span>}
                    <span> Staff accounts and the audit trail were kept.</span>
                  </div>
                )}
                <div className={styles.wipeField}>
                  <HardwareInput id="wipe-phrase" label={'TYPE "WIPE-EVERYTHING" TO ARM'} value={wipeText} onChange={e => setWipeText(e.target.value)} autoCapitalize="characters" spellCheck={false} />
                </div>
                <div className={styles.wipeField}>
                  {/* fix181 (14.4f): the Admin's own key, checked on the server */}
                  <HardwareInput id="wipe-key" name="current-password" autoComplete="current-password" label="YOUR KEY" type="password" value={wipeKey} onChange={e => setWipeKey(e.target.value)} />
                </div>
                <button type="button" className={styles.wipeBtn} disabled={wipeText !== 'WIPE-EVERYTHING' || !wipeKey || wiping} onClick={wipe}>
                  <FiTrash2 aria-hidden="true" /> {wiping ? 'WIPING...' : 'WIPE ALL BUSINESS DATA'}
                </button>
              </>
            )}

            {activeTab.key === 'deleted' && isOwner && (
              <>
                <div className={styles.wipeField}>
                  <HardwareInput id="archive-search" label="SEARCH THE ARCHIVE" value={delSearch} onChange={e => setDelSearch(e.target.value)} placeholder="Project, plot, client, reason..." />
                </div>
                {delLoading && <LoadingState label="Loading deleted projects..." tone="bare" />}
                {!delLoading && delError && (
                  <div className={styles.dangerAlert} role="alert"><FiAlertTriangle aria-hidden="true" /><span>{delError}</span>
                    <button type="button" className={styles.commitBtn} onClick={loadDeleted}><FiRotateCcw aria-hidden="true" /> RETRY</button>
                  </div>
                )}
                {!delLoading && !delError && deleted && delRows.length === 0 && <p className={styles.hint}>{deleted.length === 0 ? 'No deleted projects.' : 'Nothing matches the search.'}</p>}
                {!delLoading && !delError && delRows.map(p => (
                  <div key={p.id} className={styles.opCard} style={{ marginBottom: 8 }}>
                    <div className={styles.opHeader}>
                      <div className={styles.opInfo}>
                        <strong>#{p.projectIndex || '---'} · {p.plotLabel}{p.pending ? ' · PENDING' : ''}</strong>
                        <span className={styles.rankManager}>{[p.projectType, p.district].filter(Boolean).join(' · ') || '---'}</span>
                      </div>
                      <button type="button" className={styles.commitBtn} onClick={() => restore(p)}>
                        <FiRotateCcw aria-hidden="true" /> RESTORE
                      </button>
                    </div>
                    <div className={styles.opDetails}>
                      {p.clientNames && p.clientNames.length > 0 && <p>Clients: {p.clientNames.join(', ')}</p>}
                      <p>Deleted {fmtDateTime(p.deletedAt)}{p.deletedBy ? ` by ${p.deletedBy}` : ''}.</p>
                      {p.reason && <p>Reason: {p.reason}</p>}
                    </div>
                  </div>
                ))}
              </>
            )}

          </div></div>}
        </div>
      </div>

      <HardwareModal isOpen={addOpen} onClose={() => setAddOpen(false)} title="ADD STAFF">
        <div className={styles.modalBody}>
          <HardwareInput id="new-username" label="USERNAME" value={newOp.username} onChange={e => setNewOp({ ...newOp, username: e.target.value })} required autoCapitalize="none" spellCheck={false} />
          <p className={newOp.username && !newUserOk ? styles.ruleBad : styles.ruleTodo}>3 to 30 letters, digits, dot, underscore or hyphen. No spaces.</p>
          <HardwareInput id="new-email" label="EMAIL" type="email" value={newOp.email} onChange={e => setNewOp({ ...newOp, email: e.target.value })} required autoCapitalize="none" spellCheck={false} />
          {/* fix181 (14.5d): friendly rank names with a one-line description; the code is what is sent */}
          <fieldset className={styles.rankChoices}>
            <legend>RANK</legend>
            {RANKS.map(rk => (
              <label key={rk} className={styles.rankChoice}>
                <input type="radio" name="new-rank" value={rk} checked={newOp.role === rk} onChange={() => setNewOp({ ...newOp, role: rk })} />
                <span><strong>{rankLabel(rk)}</strong> <em>{RANK_INFO[rk]?.hint}</em></span>
              </label>
            ))}
          </fieldset>
        </div>
        <div className={styles.modalCenter}>
          <button type="button" className={modalStyles.modalBtnPrimary} onClick={createOp} disabled={!newUserOk || !newEmailOk}>
            <FiUserPlus aria-hidden="true" /> CREATE
          </button>
        </div>
      </HardwareModal>

      {/* fix181 (14.5b, 15.4b): the rank change is a small modal with radio buttons and one confirmation */}
      <HardwareModal isOpen={!!rankFor} onClose={() => setRankFor(null)} title="CHANGE RANK">
        {rankFor && (
          <>
            <div className={styles.modalBody}>
              <fieldset className={styles.rankChoices}>
                <legend>New rank for {rankFor.op.username}</legend>
                {RANKS.map(rk => (
                  <label key={rk} className={styles.rankChoice}>
                    <input type="radio" name="change-rank" value={rk} checked={rankFor.role === rk} onChange={() => setRankFor({ ...rankFor, role: rk })} />
                    <span><strong>{rankLabel(rk)}</strong>{rk === rankFor.op.role ? ' (now)' : ''} <em>{RANK_INFO[rk]?.hint}</em></span>
                  </label>
                ))}
              </fieldset>
              {rankFor.role !== rankFor.op.role && (
                <p className={styles.revealHint}>Change {rankFor.op.username} from {rankLabel(rankFor.op.role).toUpperCase()} to {rankLabel(rankFor.role).toUpperCase()}? They will have to sign in again.</p>
              )}
            </div>
            <div className={styles.modalCenter}>
              <button type="button" className={modalStyles.modalBtnPrimary} onClick={changeRank} disabled={rankFor.role === rankFor.op.role}>CHANGE</button>
              <button type="button" className={styles.commitBtn} onClick={() => setRankFor(null)}>CANCEL</button>
            </div>
          </>
        )}
      </HardwareModal>

      {/* fix181 (14.3d): resetting a key asks first and names the person */}
      <HardwareModal isOpen={!!resetFor} onClose={() => setResetFor(null)} title="RESET KEY">
        {resetFor && (
          <>
            <div className={styles.modalBody}>
              <p className={styles.revealHint}>Give {resetFor.username} a new temporary key? Their current key stops working and they are signed out everywhere.</p>
            </div>
            <div className={styles.modalCenter}>
              <button type="button" className={modalStyles.modalBtnPrimary} onClick={resetKey}><FiRotateCcw aria-hidden="true" /> RESET KEY</button>
              <button type="button" className={styles.commitBtn} onClick={() => setResetFor(null)}>CANCEL</button>
            </div>
          </>
        )}
      </HardwareModal>

      {/* fix181 (14.7c): a restore that clashes with a live project asks first */}
      <HardwareModal isOpen={!!restoreAsk} onClose={() => setRestoreAsk(null)} title="RESTORE PROJECT?">
        {restoreAsk && (
          <>
            <div className={styles.modalBody}><p className={styles.revealHint}>{restoreAsk.message}</p></div>
            <div className={styles.modalCenter}>
              <button type="button" className={modalStyles.modalBtnPrimary} onClick={() => restore(restoreAsk.project, true)}>RESTORE ANYWAY</button>
              <button type="button" className={styles.commitBtn} onClick={() => setRestoreAsk(null)}>CANCEL</button>
            </div>
          </>
        )}
      </HardwareModal>

      <HardwareModal isOpen={!!reveal} onClose={() => setReveal(null)} title="TEMPORARY KEY">
        <div className={styles.revealBox}>
          <FiAlertTriangle className={styles.warningIcon} aria-hidden="true" />
          <p className={styles.revealHint}>Give this key to {reveal ? reveal.username : ''}. They must change it when they first sign in. It is valid for 7 days.</p>
          <div className={styles.serial}>{reveal ? reveal.key : ''}</div>
          {/* fix181 (14.3c): copy instead of photographing the screen */}
          <button type="button" className={styles.commitBtn} onClick={copyKey}><FiCopy aria-hidden="true" /> {copied ? 'COPIED' : 'COPY KEY'}</button>
          <p className={styles.revealDisclaimer}>This key is shown once only.</p>
        </div>
      </HardwareModal>
      <BackToTopButton />
    </div>
  );
};
export default SettingsPage;
