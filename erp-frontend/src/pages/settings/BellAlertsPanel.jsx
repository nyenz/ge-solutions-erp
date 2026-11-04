// PATH: erp-frontend/src/pages/settings/BellAlertsPanel.jsx
// fix288 (David): every person with a bell chooses which groups of alerts ring it. Saved on the server for the account
// (the same on every device). A CRITICAL alert always shows, and at least one group stays on.
import React, { useEffect, useState } from 'react';
import { FiBell } from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import { errorText } from '../../utils/errorText';
import styles from './SettingsPage.module.css';

const GROUP_INFO = {
    MONEY: ['Money', 'Payments on receivables, reversals, cost changes, fees reduced, storage fees, expenses.'],
    PIPELINE: ['Projects', 'New and Pending entries, projects started, titles handed over, problems, deleted or restored, moved to receivables.'],
    RECOVERY: ['Recovery', 'Clients resting or callable again after calls, site visits needed.'],
    NOTES: ['Notes', 'Follow-up days that are due, and notes pinned to the top.'],
    STAFF: ['Staff', 'Staff accounts made, ranks changed, accounts suspended or switched on, keys reset.'],
    SYSTEM: ['System', 'Data wiped, logins blocked after wrong tries, a nightly job that failed.'],
};

export default function BellAlertsPanel({ toast }) {
    const [groups, setGroups] = useState(null);
    const [muted, setMuted] = useState([]);
    const [busy, setBusy] = useState('');
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        let alive = true;
        recoveryService.getAlertPrefs()
            .then(p => { if (alive) { setGroups(p.groups || []); setMuted(p.muted || []); } })
            .catch(() => { if (alive) setFailed(true); });
        return () => { alive = false; };
    }, []);

    const turn = async (g, on) => {
        if (busy) return;
        const next = on ? muted.filter(x => x !== g) : [...muted, g];
        if (groups && next.length >= groups.length) { toast('Keep at least one group of bell alerts on.', 'error'); return; }
        setBusy(g);
        try {
            const p = await recoveryService.saveAlertPrefs(next);
            setMuted(p.muted || []);
            toast((GROUP_INFO[g] ? GROUP_INFO[g][0] : g) + ' alerts ' + (on ? 'ON' : 'OFF') + '. The bell follows within a minute.', 'success');
        } catch (err) { toast(errorText(err), 'error'); }
        finally { setBusy(''); }
    };

    if (failed) return null;
    return (
        <div className={styles.prefGroupBox}>
            <div className={styles.prefGroupLabel}><FiBell aria-hidden="true" /> Bell alerts</div>
            <div className={styles.prefRow}>
                <div className={styles.prefLabel}>
                    <span>Choose what rings your bell. Saved for your account on every device. Critical alerts (a project deleted, books that do not match the payments, a flagged problem, a failed nightly job) always show.</span>
                </div>
            </div>
            {groups === null && <div className={styles.prefRow}><div className={styles.prefLabel}><span>Loading...</span></div></div>}
            {(groups || []).map(g => {
                const on = !muted.includes(g);
                const [label, hint] = GROUP_INFO[g] || [g, ''];
                return (
                    <div key={g} className={styles.prefRow}>
                        <div className={styles.prefLabel}><strong>{label}</strong><span>{hint}</span></div>
                        <div className={styles.prefOptions} role="group" aria-label={label + ' alerts'}>
                            <button type="button" className={on ? styles.prefBtnActive : styles.prefBtn} aria-pressed={on} disabled={!!busy} onClick={() => !on && turn(g, true)}>ON</button>
                            <button type="button" className={!on ? styles.prefBtnActive : styles.prefBtn} aria-pressed={!on} disabled={!!busy} onClick={() => on && turn(g, false)}>OFF</button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
