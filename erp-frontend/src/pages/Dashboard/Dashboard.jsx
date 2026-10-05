// PATH: erp-frontend/src/pages/Dashboard/Dashboard.jsx
// fix181 (Section 20, 12.5): the home page per rank. The server decides which blocks each rank gets
// (GET /dashboard/home, HomeDashboardService.dashboardBlocks) and sends only those; this page draws whatever arrives and
// never checks the rank itself. Every tile is a link to the page and filter that shows the same number. LAST SYNC is the
// server's time; REFRESH keeps the numbers on screen; the page refreshes when you come back after 5 minutes; an error
// says what went wrong (network, not allowed, signed out) with RETRY.
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { FiRefreshCw } from 'react-icons/fi';
import api from '../../api/axios';
import styles from './Dashboard.module.css';
import h from './Home.module.css';
import { LoadingState } from '../../components/common/LoadingState';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import { friendlyAction } from '../Audit/auditCatalog';
import { errorText } from '../../utils/errorText';

const fmt = (n) => Number(n || 0).toLocaleString();
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const day = (s) => { const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})T?(\d{2})?:?(\d{2})?/); return m ? m[3] + ' ' + MONTHS[Number(m[2]) - 1] + ' ' + m[1] + (m[4] ? ' ' + m[4] + ':' + m[5] : '') : ''; };
const typeLabel = (t) => String(t || '').replace(/_/g, ' ');

function Tile({ to, n, label }) {
    return (<Link className={h.tile} to={to}><span className={h.tileNum}>{n == null ? '-' : fmt(n)}</span><span className={h.tileLabel}>{label}</span></Link>);
}

function Pipeline({ byType }) {
    const [open, setOpen] = useState(null);
    const types = Object.entries(byType || {})
        .map(([t, m]) => [t, m, Object.entries(m).filter(([k]) => k !== 'HANDED OVER').reduce((s, [, v]) => s + v, 0)])
        .sort((a, b) => b[2] - a[2]);
    if (types.length === 0) return <div className={h.note}>No projects yet.</div>;
    return types.map(([t, m, openCount]) => (
        <div key={t}>
            <button type="button" className={h.typeHead} aria-expanded={open === t} onClick={() => setOpen(open === t ? null : t)}>
                <span>{typeLabel(t)}</span><span>{openCount} open</span>
            </button>
            {open === t && Object.entries(m).map(([status, count]) => (
                <div key={status} className={h.row}><span>{status}</span><span className={h.mono}>{count}</span></div>
            ))}
        </div>
    ));
}

const Dashboard = () => {
    const [data, setData] = useState(null);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const loadedAt = useRef(0);

    const load = useCallback(() => {
        setBusy(true);
        return api.get('/dashboard/home')
            .then(r => { setData(r.data); setError(''); loadedAt.current = Date.now(); })
            .catch(e => setError(errorText(e)))
            .finally(() => setBusy(false));
    }, []);

    useEffect(() => {
        let alive = true;
        api.get('/dashboard/home').then(r => { if (alive) { setData(r.data); loadedAt.current = Date.now(); } })
            .catch(e => { if (alive) setError(errorText(e)); });
        const onVis = () => { if (!document.hidden && Date.now() - loadedAt.current > 5 * 60 * 1000) load(); };
        document.addEventListener('visibilitychange', onVis);
        return () => { alive = false; document.removeEventListener('visibilitychange', onVis); };
    }, [load]);

    if (!data && !error) return (<div className={styles.container}><LoadingState label="LOADING DASHBOARD..." size="page" /></div>);

    const b = new Set((data && data.blocks) || []);
    const wq = (data && data.workQueue) || {};
    const money = data && data.money;
    const maxTrend = money ? Math.max(1, ...money.trend.map(t => Number(t.amount || 0))) : 1;

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.titleBlock}>
                    <h1 className={styles.pageTitle}>Dashboard</h1>
                    <p className={styles.pageSubtitle}>{data ? String(data.rankLabel || '').toUpperCase() : ''} · All actions are logged.</p>
                </div>
                <HeaderActions>
                    <span className={styles.syncBadge}>LAST SYNC: {data ? day(data.serverTime) : '-'}</span>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={busy} tip="Load the numbers again" onClick={load} />
                </HeaderActions>
            </header>

            {error && (<div className={h.error} role="alert">{error} <button type="button" className={h.typeHead} style={{ display: 'inline', width: 'auto' }} onClick={load}>RETRY</button></div>)}

            {data && (
                <div className={h.grid}>
                    {b.has('systemHealth') && data.systemHealth && (
                        <section className={h.card} aria-label="System health">
                            <h2 className={h.cardTitle}>System health</h2>
                            <div className={h.row}><span>Failed sign-ins (24 h)</span><Link to="/audit" className={h.mono}>{fmt(data.systemHealth.failedLogins24h)}</Link></div>
                            <div className={h.row}><span>Night job failures (7 days)</span><span className={h.mono}>{fmt(data.systemHealth.jobFailures7d)}</span></div>
                            <div className={h.row}><span>Books check</span><Link to="/payments?books=1" className={h.mono}>{data.systemHealth.booksMismatch === 0 ? 'adds up' : data.systemHealth.booksMismatch + ' differ'}</Link></div>
                            <div className={h.row}><span>Accounts</span><span className={h.mono}>{fmt(data.systemHealth.accounts)}</span></div>
                            {data.systemHealth.oneAdminWarning && <div className={`${h.note} ${h.warn}`}>{data.systemHealth.oneAdminWarning}</div>}
                        </section>
                    )}

                    {b.has('money') && money && (
                        <section className={`${h.card} ${h.cardWide}`} aria-label="Money">
                            <h2 className={h.cardTitle}>Money</h2>
                            <div className={h.tiles}>
                                <Tile to="/payments?tab=TITLE" n={money.titleCollected} label="Title money collected (UGX)" />
                                <Tile to="/land/projects?tab=CRITICAL" n={money.titleArrears} label="Title money still owed (UGX)" />
                                <Tile to="/payments" n={money.collectedThisMonth} label="Collected this month (UGX)" />
                                <Tile to="/land/projects?tab=RECEIVABLES" n={money.storageFeesUnpaid} label="Storage fees unpaid (UGX)" />
                            </div>
                            <div className={h.note}>Capital recovered: {money.collectionPercent}% of UGX {fmt(money.totalValue)}</div>
                            <div className={h.bar} role="progressbar" aria-valuenow={money.collectionPercent} aria-valuemin={0} aria-valuemax={100}>
                                <div className={h.barFill} style={{ width: Math.min(100, Number(money.collectionPercent) || 0) + '%' }} />
                            </div>
                            <div className={h.row}><span>Storage fees accrued (receivables)</span><span className={h.mono}>UGX {fmt(money.storageFeesAccrued)}</span></div>
                            <div className={h.row}><span>Storage fees collected</span><span className={h.mono}>UGX {fmt(money.storageFeesCollected)}</span></div>
                            {Number(money.keptFees) > 0 && <div className={h.row}><span>Fees kept after set aside</span><span className={h.mono}>UGX {fmt(money.keptFees)}</span></div>}
                            {Number(money.undatedCount) > 0 && <div className={h.note}>UGX {fmt(money.undatedSum)} recorded without a date ({money.undatedCount} opening deposit(s)) is in no month.</div>}
                            <div className={h.trend} aria-label="Money received per month, last 6 months">
                                {money.trend.map(t => (
                                    <div key={t.month} className={h.trendCol} title={t.month + ': UGX ' + fmt(t.amount)}>
                                        <div className={h.trendBar} style={{ height: Math.max(2, (Number(t.amount) / maxTrend) * 70) + 'px' }} />
                                        <span className={h.trendLabel}>{MONTHS[Number(t.month.slice(5, 7)) - 1]}</span>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {b.has('periods') && data.periods && Object.entries(data.periods).map(([k, p]) => (
                        <section key={k} className={h.card} aria-label={p.label}>
                            <h2 className={h.cardTitle}>{p.label}</h2>
                            <div className={h.row}><span>Money in</span><span className={h.mono}>UGX {fmt(p.revenue)}</span></div>
                            <div className={h.row}><span>Company expenses</span><span className={h.mono}>UGX {fmt(p.expenses)}</span></div>
                            <div className={h.row}><span>Net</span><span className={h.mono}>UGX {fmt(p.net)}</span></div>
                            <div className={h.row}><span>Payments</span><span className={h.mono}>{fmt(p.transactions)}</span></div>
                        </section>
                    ))}

                    {b.has('waitingForYou') && data.waitingForYou && (
                        <section className={h.card} aria-label="Waiting for you">
                            <h2 className={h.cardTitle}>Waiting for you</h2>
                            <div className={h.tiles}>
                                <Tile to="/land/projects?tab=PAID" n={data.waitingForYou.releaseReady} label="Ready for hand-over" />
                                <Tile to="/land/projects?tab=PROBLEM" n={data.waitingForYou.problems} label="Problem flags" />
                                <Tile to="/land/projects?tab=RECEIVABLES" n={data.waitingForYou.flaggedReceivableThisWeek} label="Receivable this week" />
                                <Tile to="/payments?books=1" n={data.waitingForYou.booksMismatch} label="Books check differences" />
                            </div>
                        </section>
                    )}

                    {b.has('workQueue') && (
                        <section className={h.card} aria-label="Work queue">
                            <h2 className={h.cardTitle}>Work queue</h2>
                            <div className={h.tiles}>
                                <Tile to="/land/projects?tab=PENDING" n={wq.pending && wq.pending.count} label={'Pending (set prices)' + (wq.pending && wq.pending.oldestDays != null ? ' - oldest ' + wq.pending.oldestDays + ' d' : '')} />
                                <Tile to="/land/projects?tab=PROBLEM" n={wq.problems} label="Problem flags" />
                                <Tile to="/land/projects?tab=RECEIVABLES" n={wq.receivables} label="In receivables" />
                                <Tile to="/land/projects?tab=PAID" n={wq.releaseReady} label="Ready for hand-over" />
                            </div>
                        </section>
                    )}

                    {(b.has('dueCalls') || b.has('newProjects') || b.has('problems') || b.has('receivables')) && (
                        <section className={h.card} aria-label="Today">
                            <h2 className={h.cardTitle}>Today</h2>
                            <div className={h.tiles}>
                                {b.has('dueCalls') && <Tile to="/recovery" n={data.dueCalls} label="Clients due for a call" />}
                                {b.has('newProjects') && <Tile to="/land/projects" n={data.newProjects} label="New projects (7 days)" />}
                                {b.has('problems') && !b.has('workQueue') && <Tile to="/land/projects?tab=PROBLEM" n={data.problems} label="Problem flags" />}
                                {b.has('receivables') && !b.has('workQueue') && <Tile to="/land/projects?tab=RECEIVABLES" n={data.receivables} label="In receivables" />}
                            </div>
                        </section>
                    )}

                    {b.has('releaseReady') && data.releaseReady && (
                        <section className={h.card} aria-label="Ready for hand-over">
                            <h2 className={h.cardTitle}>Ready for hand-over ({fmt(data.releaseReady.count)})</h2>
                            {(data.releaseReady.first || []).length === 0 ? <div className={h.note}>Nothing is ready.</div>
                                : data.releaseReady.first.map(p => (<div key={p.id} className={h.row}><Link to={'/folder/' + p.id}>#{p.index}</Link></div>))}
                        </section>
                    )}

                    {b.has('pipeline') && (
                        <section className={`${h.card} ${h.cardWide}`} aria-label="Projects by type and status">
                            <h2 className={h.cardTitle}>Projects by type and status</h2>
                            <Pipeline byType={data.pipeline} />
                        </section>
                    )}

                    {b.has('recentActivity') && (
                        <section className={`${h.card} ${h.cardWide}`} aria-label="Recent activity">
                            <h2 className={h.cardTitle}>Recent activity</h2>
                            <ul className={h.activity}>
                                {(data.recentActivity || []).map(a => (
                                    <li key={a.id}><Link to={'/audit?id=' + a.id}>
                                        <strong>{friendlyAction(a.action)}</strong> <span className={h.note}>{day(a.timestamp)} - {a.performedBy}</span>
                                        <div className={h.note}>{a.details}</div>
                                    </Link></li>
                                ))}
                            </ul>
                        </section>
                    )}
                </div>
            )}
        </div>
    );
};

export default Dashboard;
