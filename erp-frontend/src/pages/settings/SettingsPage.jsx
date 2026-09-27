import React, { useState, useEffect, useCallback } from 'react';
import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff, FiSliders, FiMonitor, FiChevronDown } from 'react-icons/fi';
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
  /* Every hwPanel now genuinely collapses -- these five default open so
     nothing changes for anyone who never touches a header, but a long
     staff roster or deleted-plots list can be tucked away instead of
     permanently occupying the full column. */
  const [appOpen, setAppOpen] = useState(true);
  const [secOpen, setSecOpen] = useState(true);
  const [govOpen, setGovOpen] = useState(true);
  const [dangerOpen, setDangerOpen] = useState(true);
  const [delOpen, setDelOpen] = useState(true);
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
        <div className={styles.hwPanel} data-kind="appearance">
          <div
            className={appOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}
            role="button" tabIndex={0}
            onClick={() => setAppOpen(o => !o)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setAppOpen(o => !o); } }}
            aria-expanded={appOpen} aria-label="Collapse or expand appearance panel"
          >
            <div className={styles.drawerTitle}><FiSliders className={styles.drawerIcon} aria-hidden="true" /> APPEARANCE</div>
            <FiChevronDown className={appOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden="true" />
          </div>
          {appOpen && <div className={styles.panelBody}><div className={styles.panelInner}>
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
          </div></div>}
        </div>
        <div className={styles.hwPanel} data-kind="security">
          <div
            className={secOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}
            role="button" tabIndex={0}
            onClick={() => setSecOpen(o => !o)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSecOpen(o => !o); } }}
            aria-expanded={secOpen} aria-label="Collapse or expand personal security panel"
          >
            <div className={styles.drawerTitle}><FiKey className={styles.drawerIcon} aria-hidden="true" /> PERSONAL SECURITY</div>
            <FiChevronDown className={secOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden="true" />
          </div>
          {secOpen && <div className={styles.panelBody}><div className={styles.panelInner}>
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
          </div></div>}
        </div>
        {isRoot && (
          <div className={styles.hwPanel} data-kind="governance">
            <div
              className={govOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}
              role="button" tabIndex={0}
              onClick={() => setGovOpen(o => !o)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setGovOpen(o => !o); } }}
              aria-expanded={govOpen} aria-label="Collapse or expand staff governance panel"
            >
              <div className={styles.drawerTitle}><FiShield className={styles.drawerIcon} aria-hidden="true" /> STAFF GOVERNANCE</div>
              <FiChevronDown className={govOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden="true" />
            </div>
            {govOpen && <div className={styles.panelBody}><div className={styles.panelInner}>
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
            </div></div>}
          </div>
        )}
        {isRoot && (
          <div className={`${styles.hwPanel} ${styles.dangerPanel}`}>
            <div
              className={dangerOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}
              role="button" tabIndex={0}
              onClick={() => setDangerOpen(o => !o)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDangerOpen(o => !o); } }}
              aria-expanded={dangerOpen} aria-label="Collapse or expand danger zone panel"
            >
              <div className={styles.drawerTitle}><FiAlertTriangle className={styles.drawerIcon} aria-hidden="true" /> DANGER ZONE</div>
              <FiChevronDown className={dangerOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden="true" />
            </div>
            {dangerOpen && <div className={styles.panelBody}><div className={styles.panelInner}>
              <div className={styles.wipeField}>
                <HardwareInput label={'TYPE "WIPE-EVERYTHING" TO ARM'} value={wipeText} onChange={e => setWipeText(e.target.value)} />
              </div>
              <button type="button" className={styles.wipeBtn} disabled={wipeText !== 'WIPE-EVERYTHING' || wiping} onClick={wipe}>
                <FiTrash2 aria-hidden="true" /> {wiping ? 'WIPING...' : 'WIPE ALL BUSINESS DATA'}
              </button>
            </div></div>}
          </div>
        )}
        {isRoot && (
          <div className={styles.hwPanel} data-kind="deleted">
            <div
              className={delOpen ? `${styles.drawerHeader} ${styles.drawerHeaderOpen}` : styles.drawerHeader}
              role="button" tabIndex={0}
              onClick={() => setDelOpen(o => !o)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDelOpen(o => !o); } }}
              aria-expanded={delOpen} aria-label="Collapse or expand recently deleted plots panel"
            >
              <div className={styles.drawerTitle}><FiRotateCcw className={styles.drawerIcon} aria-hidden="true" /> RECENTLY DELETED PLOTS</div>
              <FiChevronDown className={delOpen ? `${styles.chevron} ${styles.rotated}` : styles.chevron} aria-hidden="true" />
            </div>
            {delOpen && <div className={styles.panelBody}><div className={styles.panelInner}>
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
            </div></div>}
          </div>
        )}
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
