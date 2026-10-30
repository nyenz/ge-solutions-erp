// PATH: erp-frontend/src/pages/settings/RecoveryEmailPanel.jsx
// fix279: OWNER ONLY. The email that receives the 6-digit code when the owner forgets the key
// (login page > Forgot your key? > EMAIL ME A CODE). Needs the current key to change it.
import React, { useEffect, useState } from 'react';
import { FiMail } from 'react-icons/fi';
import settingsService from '../../services/settingsService';
import HardwareInput from '../../components/common/HardwareInput';
import styles from './SettingsPage.module.css';

const PLACEHOLDER = /@gesolutions\.com$/i;

export default function RecoveryEmailPanel({ toast }) {
    const [current, setCurrent] = useState(null);
    const [email, setEmail] = useState('');
    const [key, setKey] = useState('');
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        let alive = true;
        settingsService.getMyProfile().then(p => { if (alive) setCurrent(p?.email || ''); }).catch(() => { if (alive) setCurrent(''); });
        return () => { alive = false; };
    }, []);

    const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim()) && !PLACEHOLDER.test(email.trim());
    const save = async (e) => {
        if (e) e.preventDefault();
        if (!emailOk || !key || saving) return;
        setSaving(true);
        try {
            await settingsService.setRecoveryEmail(key, email.trim());
            setCurrent(email.trim()); setEmail(''); setKey('');
            toast('Saved. Recovery codes will go to that email.', 'success');
        } catch (err) { toast(err.message, 'error'); }
        finally { setSaving(false); }
    };

    const state = current === null ? 'Loading...' : (!current || PLACEHOLDER.test(current)) ? 'NOT SET (recovery by email does not work yet)' : current;
    return (
        <form onSubmit={save} autoComplete="off">
            <div className={styles.prefGroupBox}>
                <div className={styles.prefGroupLabel}>Recovery email (owner)</div>
                <p className={styles.statusLegend}>Now: {state}</p>
                <div className={styles.dualRow}>
                    <HardwareInput id="recovery-email" name="recovery-email" label="NEW RECOVERY EMAIL" type="email" autoComplete="off" value={email} onChange={e => setEmail(e.target.value)} />
                    <HardwareInput id="recovery-email-key" name="current-password" label="CURRENT KEY" type="password" autoComplete="current-password" value={key} onChange={e => setKey(e.target.value)} />
                </div>
                <div className={styles.submitRow}>
                    <button type="submit" className={styles.commitBtn} disabled={!emailOk || !key || saving}><FiMail aria-hidden="true" /> {saving ? 'SAVING...' : 'SAVE EMAIL'}</button>
                </div>
            </div>
        </form>
    );
}
