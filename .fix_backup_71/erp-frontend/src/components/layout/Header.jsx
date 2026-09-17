import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiBell, FiLogOut, FiCheck } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import styles from './Header.module.css';
const SEV_COLOR = { POSITIVE: '#10b981', WARN: '#f59e0b', CRITICAL: '#ef4444', INFO: '#06b6d4' };
const Header = ({ onToggle }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [staleCount, setStaleCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifs, setNotifs] = useState([]);
  const [unread, setUnread] = useState(0);
  const dropRef = useRef(null);
  const isRoot = user?.isRoot;
  const roleMap = { ROLE_ADMIN: 'ADMIN', ROLE_DIRECTOR: 'DIRECTOR', ROLE_MANAGER: 'MANAGER', ROLE_SECRETARY: 'SECRETARY' };
  const displayRole = isRoot ? 'ROOT OWNER' : (roleMap[user?.role] || 'STAFF');
  const initials = user?.username?.charAt(0).toUpperCase() || 'A';
  const sync = useCallback(async () => {
    try { setStaleCount((await recoveryService.getTaskCount()) ?? 0); } catch {}
    try { setUnread((await recoveryService.getUnreadCount()) ?? 0); } catch {}
  }, []);
  useEffect(() => {
    sync();
    const iv = setInterval(sync, 300000);
    return () => clearInterval(iv);
  }, [sync]);
  useEffect(() => {
    const h = (e) => { if (dropRef.current && !dropRef.current.contains(e.target)) setNotifOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);
  const openDrop = async () => {
    const next = !notifOpen;
    setNotifOpen(next);
    if (next) { try { setNotifs(await recoveryService.getNotifications()); } catch { setNotifs([]); } }
  };
  const go = (n) => {
    setNotifOpen(false);
    if (n.entityType === 'PROJECT' && n.entityId) navigate('/folder/' + n.entityId);
    else navigate('/recovery');
    recoveryService.markRead(n.id).then(sync).catch(() => {});
  };
  const badge = unread + (staleCount > 0 ? staleCount : 0);
  return (
    <header className={styles.header}>
      <div className={styles.headerLeft}>
        <button type="button" className={styles.sidebarToggle} onClick={onToggle} aria-label="Toggle sidebar navigation">
          <FiMenu aria-hidden="true" />
        </button>
        <div className={styles.logoSection} aria-label="Golden Seed ERP">
          <div className={styles.logoSmallPulse} aria-hidden="true">
            <div className={styles.pulseInner}>🌱</div>
            <div className={styles.pulseRing} />
          </div>
          <span className={styles.brandName}>GOLDEN SEED</span>
        </div>
      </div>
      <div className={styles.headerRight}>
        <div className={styles.notifWrap} ref={dropRef}>
          <button
            type="button"
            className={`${styles.notificationGroup} ${badge > 0 ? styles.activeSensor : ''}`}
            onClick={openDrop}
            aria-label={badge > 0 ? badge + ' signals pending' : 'Open notifications'}
          >
            <FiBell className={styles.bellIcon} aria-hidden="true" />
            {badge > 0 && <span className={styles.badge} aria-hidden="true">{badge > 99 ? '99+' : badge}</span>}
          </button>
          {notifOpen && (
            <div className={styles.notifDrop}>
              <div className={styles.notifHead}>
                <span>SIGNALS</span>
                <button type="button" className={styles.notifReadAll} onClick={() => recoveryService.markAllRead().then(sync).catch(() => {})}>
                  <FiCheck aria-hidden="true" /> READ ALL
                </button>
              </div>
              {notifs.length === 0 && <div className={styles.notifEmpty}>NO SIGNALS</div>}
              {notifs.slice(0, 12).map(n => (
                <button type="button" key={n.id} className={`${styles.notifRow} ${n.read ? styles.notifRead : ''}`} onClick={() => go(n)}>
                  <span className={styles.notifDot} style={{ background: SEV_COLOR[n.severity] || '#06b6d4' }} />
                  <span className={styles.notifMsg}>{n.message}</span>
                </button>
              ))}
              {staleCount > 0 && (
                <button type="button" className={styles.notifRow} onClick={() => { setNotifOpen(false); navigate('/recovery'); }}>
                  <span className={styles.notifDot} style={{ background: '#EE8C3A' }} />
                  <span className={styles.notifMsg}>{staleCount} recovery mission{staleCount > 1 ? 's' : ''} due now</span>
                </button>
              )}
            </div>
          )}
        </div>
        <div className={styles.userCard} aria-label={`Logged in as ${user?.username}, ${displayRole}`}>
          <div className={styles.avatar} aria-hidden="true">{initials}</div>
          <div className={styles.userMeta}>
            <span className={styles.userName}>{user?.username}</span>
            <span className={styles.roleTag}>{displayRole}</span>
          </div>
        </div>
        <button type="button" className={styles.logoutTrigger} onClick={logout} aria-label="Sign out of session">
          <FiLogOut aria-hidden="true" />
        </button>
      </div>
    </header>
  );
};
export default Header;
