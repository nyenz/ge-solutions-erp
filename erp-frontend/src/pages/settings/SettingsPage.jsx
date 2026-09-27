// PATH: erp-frontend/src/pages/settings/SettingsPage.jsx
// GOLDEN SEED -- SETTINGS PAGE (fix121: Report Studio parity rewrite).
// The five stacked, independently-collapsing hwPanels are gone. Settings now
// reads exactly like the Reports workstation: a chip dock of tabs up top
// (the same tile spec as Report Studio's dataset row -- label + monospace
// count, solid-orange when active) feeding ONE gradient card below, whose
// head bar recolors per section (orange/cyan/violet/red/slate) the way
// Report Studio's own panels stay orange throughout. Same CornerDecor
// brackets, same click-anywhere collapsible head, same button language.
import React, { useState, useEffect, useCallback } from 'react';
import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff, FiSliders, FiMonitor, FiChevronDown, FiArchive } from 'react-icons/fi';
import { createPortal } from 'react-dom';
import { useAuth } from '../../hooks/useAuth';
import { usePreferences } from '../../context/usePreferences';
import settingsService from '../../services/settingsService';
import landService from '../../services/landService';
import HardwareInput from '../../components/common/HardwareInput';
import HardwareSelect from '../../components/common/HardwareSelect';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import CornerDecor from '../../components/ui/CornerDecor';
import styles from './SettingsPage.module.css';
import { LoadingState } from '../../components/common/LoadingState';
const TOAST_ICONS = { success: <FiCheckSquare aria-hidden="true" />, error: <FiAlertCircle aria-hidden="true" />, warn: <FiAlertTriangle aria-hidden="true" />, info: <FiInfo aria-hidden="true" /> };
const RANKS = ['ROLE_ADMIN', 'ROLE_DIRECTOR', 'ROLE_MANAGER', 'ROLE_SECRETARY'];

/* Every option here is wired to real CSS in index.css -- see the note at the
   top of context/PreferencesProvider.jsx for what each one moves. */
const PREF_GROUPS = [
  { key: 'theme', label: 'Page theme', hint: 'Background and chrome. Panels stay navy in both.',
    options: [{ value: 'light', label: 'CREAM' }, { value: 'dark', label: 'SLATE' }] },
  { key: 'uiScale', label: 'Interface size', hint: 'Scales the whole app, not just text.',
    options: [{ value: '90', label: '90%' }, { value: '100', label: '100%' }, { value: '110', label: '110%' }, { value: '125', label: '125%' }] },
  { key: 'statSize', label: 'Summary box size', hint: 'The figures at the top of Payments, Expenses and the dossier.',
    options: [{ value: 'small', label: 'SMALL' }, { value: 'standard', label: 'STANDARD' }, { value: 'large', label: 'LARGE' }] },
  { key: 'tips', label: 'Hover explainers', hint: 'How long before they appear, or turn them off.',
    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'slow', label: 'SLOW' }, { value: 'off', label: 'OFF' }] },
  { key: 'motion', label: 'Animation', hint: 'Turn off movement and fades across the app.',
    options: [{ value: 'full', label: 'ON' }, { value: 'reduced', label: 'REDUCED' }] },
  { key: 'contrast', label: 'Table contrast', hint: 'Stronger row lines for low-quality monitors.',
    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'high', label: 'HIGH' }] },
  { key: 'notifPoll', label: 'Notification refresh', hint: 'How often the bell checks for new signals in the background.',
    options: [{ value: '300', label: '5 MIN' }, { value: '900', label: '15 MIN' }, { value: '0', label: 'MANUAL' }] },
];

const SettingsPage = () => {
  const { user } = useAuth();
  const { prefs, setPref, resetPrefs } = usePreferences();
  const isRoot = !!user?.isRoot;
  /* One tab is on screen at a time now (Report Studio dataset-tile spec),
     so the old per-panel appOpen/secOpen/govOpen/dangerOpen/delOpen quintet
     collapses into a single tab key plus one collapse toggle for whichever
     card is currently showing. */
  const [tab, setTab] = useState('appearance');
  const [panelOpen, setPanelOpen] = useState(true);
  const [toasts, setToasts] = useState([]);
  const toast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(p => [...p, { id, message, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 5000);
  }, []);
  const [oldPw, setOldPw] = useState(''); const [newPw, setNewPw] = useState('');
  const [showOld, setShowOld] = useState(false); const [showNew, setShowNew] = useState(false);
  const [savingPw, setSavingPw] = useState(false);
  const [ops, setOps] = useState([]); const [opsLoading, setOpsLoading] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [newOp, setNewOp] = useState({ username: '', email: '', role: 'ROLE_MANAGER' });
  const [reveal, setReveal] = useState(null);
  const [rankMenu, setRankMenu] = useState(null);
  const [wipeText, setWipeText] = useState('');
  const [wiping, setWiping] = useState(false);
  const [deleted, setDeleted] = useState([]); const [delLoading, setDelLoading] = useState(false);
  const loadOps = useCallback(async () => {
    if (!isRoot) return;
    setOpsLoading(true);
    try { setOps(await settingsService.getAllOperators()); } catch (e) { toast(e.message, 'error'); }
    finally { setOpsLoading(false); }
  }, [isRoot, toast]);
  const loadDeleted = useCallback(async () => {
    if (!isRoot) return;
    setDelLoading(true);
    try { setDeleted(await landService.getDeletedProjects()); } catch { setDeleted([]); }
    finally { setDelLoading(false); }
  }, [isRoot]);
  useEffect(() => { loadOps(); loadDeleted(); }, [loadOps, loadDeleted]);
  const changePw = async () => {
    setSavingPw(true);
    try { await settingsService.changePersonalPassword(oldPw, newPw); toast('Security key updated.', 'success'); setOldPw(''); setNewPw(''); }
    catch (e) { toast(e.message, 'error'); }
    finally { setSavingPw(false); }
  };
  const createOp = async () => {
    try {
      const res = await settingsService.registerManager(newOp);
      setAddOpen(false); setReveal({ username: res.username, key: res.temporaryPassword });
      setNewOp({ username: '', email: '', role: 'ROLE_MANAGER' });
      loadOps();
    } catch (e) { toast(e.message, 'error'); }
  };
  const wipe = async () => {
    setWiping(true);
    try { const r = await settingsService.wipeAllData(); toast(r.message || 'System wiped.', 'warn'); }
    catch (e) { toast(e.message, 'error'); }
    finally { setWiping(false); setWipeText(''); }
  };
  const rankClass = (r) => r === 'ROLE_ADMIN' ? styles.rankAdmin : r === 'ROLE_MANAGER' ? styles.rankManager : r === 'ROLE_SECRETARY' ? styles.rankSecretary : styles.rankAdmin;

  /* fix121: the dock -- same shape as Report Studio's dataset tile row
     (label + Space Mono count, solid orange when selected). Governance,
     Danger and the Archive only exist for root, exactly as their hwPanels
     used to be root-gated. */
  const TABS = [
    { key: 'appearance', label: 'APPEARANCE', icon: FiSliders, accent: 'orange', count: PREF_GROUPS.length },
    { key: 'security', label: 'SECURITY', icon: FiKey, accent: 'cyan', count: null },
    ...(isRoot ? [{ key: 'governance', label: 'STAFF', icon: FiShield, accent: 'violet', count: ops.length }] : []),
    ...(isRoot ? [{ key: 'danger', label: 'DANGER ZONE', icon: FiAlertTriangle, accent: 'red', count: null }] : []),
    ...(isRoot ? [{ key: 'deleted', label: 'ARCHIVE', icon: FiArchive, accent: 'slate', count: deleted.length }] : []),
  ];
  const activeTab = TABS.find(t => t.key === tab) || TABS[0];
  const selectTab = (key) => { setTab(key); setPanelOpen(true); };

  return (
    <div className={styles.container}>
      {typeof document !== 'undefined' && createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
          {toasts.map(t => (<div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
            <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
            <span className={styles.toastMsg}>{t.message}</span>
            <button className={styles.toastClose} onClick={() => setToasts(p => p.filter(x => x.id !== t.id))} aria-label="Dismiss"><FiX aria-hidden="true" /></button>
          </div>))}
        </div>, document.body)}
      <header className={styles.pageHeader}>
        <div className={styles.pageHeaderLeft}>
          <h1 className={styles.title}>Settings</h1>
          <p className={styles.subtitle}>Appearance, security, governance and the danger zone</p>
        </div>
        {user?.mustChangePassword && (<div className={`${styles.handbrakeBadge} ${styles.blink}`}><FiLock aria-hidden="true" /> CHANGE YOUR PASSWORD TO UNLOCK THE SYSTEM</div>)}
      </header>

      <div className={styles.workstationGrid}>
        {/* ── TAB DOCK -- Report Studio dataset-tile spec ── */}
        <div className={styles.dockRow}>
          <div className={styles.tabDock}>
            <div className={styles.tabRow}>
              {TABS.map(t => (
                <button
                  key={t.key} type="button"
                  className={tab === t.key ? styles.tabOn : styles.tab}
                  data-accent={t.accent}
                  onClick={() => selectTab(t.key)}
                  aria-pressed={tab === t.key}
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
        <div className={styles.workstationCard} data-accent={activeTab.accent}>
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

            {tab === 'appearance' && (
              <>
                <div className={styles.securityAlert}><FiMonitor aria-hidden="true" /><span>These are saved on this device, not on your account -- the office shares logins across a desktop and two phones, and "this screen is too small to read" is a fact about the screen.</span></div>
                {PREF_GROUPS.map(group => (
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
                <div className={styles.submitRow}>
                  <button type="button" className={styles.commitBtn} onClick={resetPrefs}><FiRotateCcw aria-hidden="true" /> RESET APPEARANCE</button>
                </div>
              </>
            )}

            {tab === 'security' && (
              <>
                <div className={styles.securityAlert}><FiShield aria-hidden="true" /><span>Minimum 8 characters, one uppercase letter and one number. Changing your key unlocks full access.</span></div>
                <div className={styles.dualRow}>
                  <div className={styles.eyeInpWrap}>
                    <HardwareInput label="CURRENT KEY" type={showOld ? 'text' : 'password'} value={oldPw} onChange={e => setOldPw(e.target.value)} />
                    <button type="button" className={styles.eyeBtn} onClick={() => setShowOld(s => !s)} aria-label="Toggle current key visibility">{showOld ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}</button>
                  </div>
                  <div className={styles.eyeInpWrap}>
                    <HardwareInput label="NEW KEY" type={showNew ? 'text' : 'password'} value={newPw} onChange={e => setNewPw(e.target.value)} />
                    <button type="button" className={styles.eyeBtn} onClick={() => setShowNew(s => !s)} aria-label="Toggle new key visibility">{showNew ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}</button>
                  </div>
                </div>
                <div className={styles.submitRow}>
                  <button type="button" className={styles.commitBtn} onClick={changePw} disabled={savingPw || !oldPw || !newPw}><FiKey aria-hidden="true" /> COMMIT NEW KEY</button>
                </div>
              </>
            )}

            {tab === 'governance' && isRoot && (
              <>
                <div className={styles.ledgerActions}>
                  <button type="button" className={styles.addOpBtn} onClick={() => setAddOpen(true)}><FiUserPlus aria-hidden="true" /> PROVISION OPERATOR</button>
                </div>
                <div className={styles.statusLegend}>
                  <span className={styles.legendDot} style={{ background: '#10b981' }} /><span className={styles.legendText}>ACTIVE</span>
                  <span className={styles.legendSep} />
                  <span className={styles.legendDot} style={{ background: '#ef4444' }} /><span className={styles.legendText}>SUSPENDED</span>
                </div>
                <div className={styles.staffStream}>
                  {opsLoading && <LoadingState label="SYNCING REGISTRY..." tone="bare" />}
                  {!opsLoading && ops.map(op => (
                    <div key={op.username} className={`${styles.opCard} ${!op.active ? styles.cardDimmed : ''}`}>
                      <div className={styles.opHeader}>
                        <div className={styles.opAvatar}>{(op.username || '?').charAt(0).toUpperCase()}<span className={`${styles.statusDot} ${op.active ? styles.dotGreen : styles.dotRed}`} /></div>
                        <div className={styles.opInfo}>
                          <strong>{op.username}{op.root ? ' (ROOT)' : ''}</strong>
                          <span className={rankClass(op.role)}>{(op.role || '').replace('ROLE_', '')}</span>
                        </div>
                        <div className={styles.opActions}>
                          <div className={styles.rankMenuWrapper}>
                            <button type="button" className={styles.rankBtn} disabled={op.root} onClick={() => setRankMenu(rankMenu === op.username ? null : op.username)} aria-label="Change rank"><FiShield aria-hidden="true" /></button>
                            {rankMenu === op.username && (
                              <div className={styles.rankMenu}>
                                {RANKS.map(rk => (
                                  <div key={rk} className={`${styles.rankMenuItem} ${op.role === rk ? styles.rankMenuItemActive : ''}`}
                                    onClick={async () => { setRankMenu(null); try { await settingsService.updateOperatorRole(op.username, rk); toast('Rank updated.', 'success'); loadOps(); } catch (e) { toast(e.message, 'error'); } }}>
                                    {rk.replace('ROLE_', '')}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          <button type="button" className={`${styles.killSwitchBtn} ${op.active ? styles.killSwitchActive : styles.killSwitchInactive}`} disabled={op.root}
                            onClick={async () => { try { await settingsService.toggleOperator(op.username, !op.active); toast(op.active ? 'Operator suspended.' : 'Operator activated.', 'warn'); loadOps(); } catch (e) { toast(e.message, 'error'); } }}
                            aria-label={op.active ? 'Suspend operator' : 'Activate operator'}>
                            <FiPower aria-hidden="true" />
                          </button>
                          <button type="button" className={styles.resetTrigger} disabled={op.root}
                            onClick={async () => { try { const key = await settingsService.resetOperatorKey(op.username); setReveal({ username: op.username, key }); } catch (e) { toast(e.message, 'error'); } }}
                            aria-label="Reset security key">
                            <FiRotateCcw aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                      <div className={styles.opDetails}><p><FiInfo aria-hidden="true" /> {op.email || 'no email on file'}</p></div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {tab === 'danger' && isRoot && (
              <>
                <div className={styles.dangerAlert}><FiAlertTriangle aria-hidden="true" /><span>This deletes every project, client, payment and expense on the whole system. There is no undo. Operator accounts and your own login are not touched.</span></div>
                <div className={styles.wipeField}>
                  <HardwareInput label={'TYPE "WIPE-EVERYTHING" TO ARM'} value={wipeText} onChange={e => setWipeText(e.target.value)} />
                </div>
                <button type="button" className={styles.wipeBtn} disabled={wipeText !== 'WIPE-EVERYTHING' || wiping} onClick={wipe}>
                  <FiTrash2 aria-hidden="true" /> {wiping ? 'WIPING...' : 'WIPE ALL BUSINESS DATA'}
                </button>
              </>
            )}

            {tab === 'deleted' && isRoot && (
              <>
                {delLoading && <LoadingState label="SYNCING DELETED PLOTS..." tone="bare" />}
                {!delLoading && deleted.length === 0 && <p className={styles.hint}>NO DELETED PLOTS.</p>}
                {!delLoading && deleted.map(p => (
                  <div key={p.id} className={styles.opCard} style={{ marginBottom: 8 }}>
                    <div className={styles.opHeader}>
                      <div className={styles.opInfo}>
                        <strong>#{p.projectIndex || '---'} {p.landTitle ? p.landTitle.plotNumber : ''}</strong>
                        <span className={styles.rankManager}>{p.district || '---'}</span>
                      </div>
                      <button type="button" className={styles.commitBtn} onClick={async () => { try { await landService.restoreProject(p.id); toast('Plot restored.', 'success'); loadDeleted(); } catch { toast('Restore failed.', 'error'); } }}>
                        <FiRotateCcw aria-hidden="true" /> RESTORE
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}

          </div></div>}
        </div>
      </div>

      <HardwareModal isOpen={addOpen} onClose={() => setAddOpen(false)} title="PROVISION OPERATOR">
        <div className={styles.modalBody}>
          <HardwareInput label="USERNAME" value={newOp.username} onChange={e => setNewOp({ ...newOp, username: e.target.value })} required />
          <HardwareInput label="EMAIL" type="email" value={newOp.email} onChange={e => setNewOp({ ...newOp, email: e.target.value })} required />
          <div className={styles.selectWrap}>
            <HardwareSelect label="RANK" options={RANKS} value={newOp.role} onChange={v => setNewOp({ ...newOp, role: v })} />
          </div>
        </div>
        <div className={styles.modalCenter}>
          <HardwareButton onClick={createOp} icon={FiUserPlus} disabled={!newOp.username || !newOp.email}>CREATE</HardwareButton>
        </div>
      </HardwareModal>
      <HardwareModal isOpen={!!reveal} onClose={() => setReveal(null)} title="TEMPORARY SECURITY KEY">
        <div className={styles.revealBox}>
          <FiAlertTriangle className={styles.warningIcon} aria-hidden="true" />
          <p className={styles.revealHint}>HAND THIS KEY TO {reveal ? reveal.username.toUpperCase() : ''}. THEY MUST CHANGE IT AT FIRST LOGIN.</p>
          <div className={styles.serial}>{reveal ? reveal.key : ''}</div>
          <p className={styles.revealDisclaimer}>THIS KEY IS SHOWN ONCE ONLY.</p>
        </div>
      </HardwareModal>
      <BackToTopButton />
    </div>
  );
};
export default SettingsPage;
