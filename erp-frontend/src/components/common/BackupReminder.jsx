// PATH: erp-frontend/src/components/common/BackupReminder.jsx
// fix268 (David): the monthly reminder. Root only, on the Dashboard: when no backup was saved in the last 30 days, one
// small bar says so and opens Settings > BACKUP. Nothing shows when the backup is recent.
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiHardDrive } from 'react-icons/fi';
import settingsService from '../../services/settingsService';
import { daysSince, BACKUP_DUE_DAYS } from '../../utils/backup';
import styles from './BackupReminder.module.css';

export default function BackupReminder({ user }) {
    const [last, setLast] = useState(undefined);
    const isRoot = !!user?.isRoot;
    useEffect(() => {
        if (!isRoot) return undefined;
        let alive = true;
        settingsService.backupStatus().then(r => { if (alive) setLast(r?.lastBackupAt || null); }).catch(() => {});
        return () => { alive = false; };
    }, [isRoot]);
    if (!isRoot || last === undefined) return null;
    const ago = daysSince(last);
    if (last !== null && ago < BACKUP_DUE_DAYS) return null;
    return (
        <div className={styles.bar} role="status">
            <FiHardDrive aria-hidden="true" className={styles.icon} />
            <span className={styles.text}>{last === null ? 'No backup has been saved to your computer yet.' : `Last backup was ${ago} days ago.`} Save one to your hard drive.</span>
            <Link to="/settings?tab=backup" className={styles.btn}>BACK UP NOW</Link>
        </div>
    );
}
