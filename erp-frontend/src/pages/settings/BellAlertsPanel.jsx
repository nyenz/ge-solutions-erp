// PATH: erp-frontend/src/pages/settings/BellAlertsPanel.jsx
// fix288 (David): every person with a bell chooses which groups of alerts ring it. Saved on the server for the account
// (the same on every device). A CRITICAL alert always shows, and at least one group stays on.
import React, { useEffect, useState } from 'react';
import { FiBell } from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import { CATALOG } from '../../components/common/notificationCatalog';   // fix289: the name of each single alert
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
    const [types, setTypes] = useState({});          // fix289: { GROUP: [CODE, ...] } -- the single alerts
    const [open, setOpen] = useState('');            // fix289: the group whose single alerts are shown
    const [busy, setBusy] = useState('');   // the thing being saved
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        let alive = true;
        recoveryService.getAlertPrefs()
            .then(p => { if (alive) { setGroups(p.groups || []); setMuted(p.muted || []); setTypes(p.types || {}); } })
            .catch(() => { if (alive) setFailed(true); });
        return () => { alive = false; };
    }, []);

    // fix289: save a new list of switched-off groups / single alerts (T:CODE)
    const save = async (next, what) => {
        if (busy) return;
        setBusy(what);
        try {
            const p = await recoveryService.saveAlertPrefs(next);
            setMuted(p.muted || []);
            toast(what + '. The bell follows within a minute.', 'success');
        } catch (err) { toast(errorText(err), 'error'); }
        finally { setBusy(''); }
    };
    const turn = (g, on) => {
        const next = on ? muted.filter(x => x !== g && !(types[g] || []).includes(x.slice(2))) : [...muted.filter(x => !(types[g] || []).map(c => 'T:' + c).includes(x)), g];
        save(next, (GROUP_INFO[g] ? GROUP_INFO[g][0] : g) + ' alerts ' + (on ? 'ON' : 'OFF'));
    };
    const turnOne = (code, on) => {
        const key = 'T:' + code;
        save(on ? muted.filter(x => x !== key) : [...muted, key], ((CATALOG[code] && CATALOG[code].label) || code) + (on ? ' ON' : ' OFF'));
    };
    const allOn = () => save([], 'Every alert ON');

    if (failed) return null;
    // drawn inside the Appearance > NOTIFICATIONS card, under Notification refresh
    return (
        <>
            <div className={styles.prefRow}>
                <div className={styles.prefLabel}>
                    <strong><FiBell aria-hidden="true" /> Bell alerts</strong>
                    <span>Choose what rings your bell. Saved for your account on every device. Critical alerts (a project deleted, books that do not match the payments, a flagged problem, a failed nightly job) always show.</span>
                </div>
            </div>
            {groups === null && <div className={styles.prefRow}><div className={styles.prefLabel}><span>Loading...</span></div></div>}
            {groups && groups.length > 0 && (<div className={styles.prefRow}>
                <div className={styles.prefLabel}><strong>All alerts</strong><span>{muted.length ? muted.length + ' switched off.' : 'Every alert is on.'}</span></div>
                <div className={styles.prefOptions}>
                    <button type="button" className={muted.length ? styles.prefBtn : styles.prefBtnActive} aria-pressed={!muted.length} disabled={!!busy || !muted.length} onClick={allOn}>ALL ON</button>
                </div>
            </div>)}
            {(groups || []).map(g => {
                const on = !muted.includes(g);
                const [label, hint] = GROUP_INFO[g] || [g, ''];
                return (
                    <div key={g} className={styles.prefRow}>
                        <div className={styles.prefLabel}><strong>{label}</strong><span>{hint}</span></div>
                        <div className={styles.prefOptions} role="group" aria-label={label + ' alerts'}>
                            <button type="button" className={on ? styles.prefBtnActive : styles.prefBtn} aria-pressed={on} disabled={!!busy} onClick={() => !on && turn(g, true)}>ON</button>
                            <button type="button" className={!on ? styles.prefBtnActive : styles.prefBtn} aria-pressed={!on} disabled={!!busy} onClick={() => on && turn(g, false)}>OFF</button>
                            {on && (types[g] || []).length > 1 && <button type="button" className={open === g ? styles.prefBtnActive : styles.prefBtn} aria-expanded={open === g}
                                onClick={() => setOpen(open === g ? '' : g)}>CHOOSE ({(types[g] || []).length})</button>}
                        </div>
                        {/* fix289: each single alert of this group, switched on or off one by one */}
                        {on && open === g && (<div className={styles.alertList}>
                            {(types[g] || []).map(code => {
                                const oneOn = !muted.includes('T:' + code);
                                return (<div key={code} className={styles.alertItem}>
                                    <span>{(CATALOG[code] && CATALOG[code].label) || code}</span>
                                    <button type="button" className={oneOn ? styles.prefBtnActive : styles.prefBtn} aria-pressed={oneOn} disabled={!!busy}
                                        aria-label={((CATALOG[code] && CATALOG[code].label) || code) + (oneOn ? ': on, press to switch off' : ': off, press to switch on')}
                                        onClick={() => turnOne(code, !oneOn)}>{oneOn ? 'ON' : 'OFF'}</button>
                                </div>);
                            })}
                        </div>)}
                    </div>
                );
            })}
        </>
    );
}
