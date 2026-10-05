// PATH: erp-frontend/src/pages/Pending/MyEntriesPage.jsx
// fix181 (8.7d, 12.3): MY ENTRIES -- the projects an Employee entered: still waiting (with how many days), started by the
// office, or rejected (with the reason, for 30 days, so they know to enter it again). No money anywhere.
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import pendingService from '../../services/pendingService';
import { errorText } from '../../utils/errorText';
import { LoadingState, EmptyState } from '../../components/common/LoadingState';
import styles from './Pending.module.css';

const day = (v) => (v ? String(v).slice(0, 10) : '');

export default function MyEntriesPage() {
    const navigate = useNavigate();
    const [rows, setRows] = useState(null);
    const [error, setError] = useState('');

    const load = useCallback(async () => {
        setError('');
        try { setRows(await pendingService.mine()); }
        catch (e) { setError(errorText(e)); setRows([]); }
    }, []);
    useEffect(() => {
        let alive = true;
        pendingService.mine().then(d => { if (alive) setRows(d); }).catch(e => { if (alive) { setError(errorText(e)); setRows([]); } });
        return () => { alive = false; };
    }, []);

    const open = (r) => { if (r.pending && !r.rejected) navigate('/pending/' + r.id); };

    return (
        <div className={styles.page}>
            <header className={styles.head}>
                <div className={styles.headLeft}>
                    <h1 className={styles.title}>My Entries</h1>
                    <span className={styles.sub}>Projects you entered. The office adds the prices and starts them.</span>
                </div>
            </header>
            {error && <div className={styles.error} role="alert">{error} <button type="button" className={`${styles.btn} ${styles.btnGhost}`} onClick={load}>RETRY</button></div>}
            {rows === null && <LoadingState label="LOADING YOUR ENTRIES..." size="page" />}
            {rows && rows.length === 0 && !error && <EmptyState label="NO ENTRIES YET">Use NEW PROJECT to enter one.</EmptyState>}
            {rows && rows.map(r => {
                const clickable = r.pending && !r.rejected;
                return (
                    <div key={r.id} className={`${styles.card} ${styles.cardBody} ${clickable ? styles.rowLink : ''}`}
                        role={clickable ? 'button' : undefined} tabIndex={clickable ? 0 : undefined}
                        onClick={() => open(r)} onKeyDown={e => { if (e.key === 'Enter') open(r); }}>
                        <div className={styles.row}>
                            <span className={styles.idx}>#{r.projectIndex}</span>
                            {r.rejected
                                ? <span className={`${styles.badge} ${styles.badgeRejected}`}>REJECTED</span>
                                : r.pending
                                    ? <span className={`${styles.badge} ${styles.badgePending}`}>PENDING {r.ageDays != null ? '- ' + r.ageDays + ' day(s)' : ''}</span>
                                    : <span className={`${styles.badge} ${styles.badgeStarted}`}>STARTED {day(r.startedAt)}</span>}
                        </div>
                        <div className={styles.muted}>
                            {(r.projectType || '').replace(/_/g, ' ')} {r.district ? '- ' + r.district : ''} {r.clientNames && r.clientNames.length ? '- ' + r.clientNames.join(', ') : ''}
                        </div>
                        <div className={styles.muted}>Entered {day(r.enteredAt)}</div>
                        {r.rejected && r.rejectedReason && <div className={styles.error}>Reason: {r.rejectedReason}</div>}
                    </div>
                );
            })}
        </div>
    );
}
