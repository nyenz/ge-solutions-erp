// PATH: erp-frontend/src/pages/Dashboard/Dashboard.jsx
// fix181 (Section 20, 12.5): the home page per rank. The server decides which blocks each rank gets
// (GET /dashboard/home, HomeDashboardService.dashboardBlocks) and sends only those; this page draws whatever arrives and
// never checks the rank itself. Every tile is a link to the page and filter that shows the same number. LAST SYNC is the
// server's time; REFRESH keeps the numbers on screen; the page refreshes when you come back after 5 minutes; an error
// says what went wrong (network, not allowed, signed out) with RETRY.
// fix182: redesigned on the Settings page language -- navy workstation cards whose Cinzel head bar, line and hover take
// ONE accent per section, with cream "group boxes" inside (the light/dark tone play), icon frames, a recovery ring, a
// 6-month trend, money-in vs money-out bars and a stacked status bar per project type. The last answer is kept for the
// session, so coming back to the Dashboard shows the numbers at once and refreshes them behind the scenes.
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
    FiRefreshCw, FiDollarSign, FiTrendingUp, FiAlertTriangle, FiArchive, FiPhoneCall, FiPlusSquare, FiClock,
    FiCheckCircle, FiActivity, FiLayers, FiShield, FiInbox, FiCalendar, FiArrowRight, FiChevronDown, FiBookOpen,
    FiUsers, FiLock, FiPackage,
} from 'react-icons/fi';
import api from '../../api/axios';
import styles from './Dashboard.module.css';
import { LoadingState } from '../../components/common/LoadingState';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import { friendlyAction } from '../Audit/auditCatalog';
import { errorText } from '../../utils/errorText';
import { useAuth } from '../../hooks/useAuth';
import { cached, remember } from '../../utils/pageCache';

const fmt = (n) => Number(n || 0).toLocaleString();
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const day = (s) => { const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})T?(\d{2})?:?(\d{2})?/); return m ? m[3] + ' ' + MONTHS[Number(m[2]) - 1] + ' ' + m[1] + (m[4] ? ' ' + m[4] + ':' + m[5] : '') : ''; };
const time = (s) => { const m = String(s || '').match(/T(\d{2}):(\d{2})/); return m ? m[1] + ':' + m[2] : ''; };
const typeLabel = (t) => String(t || '').replace(/_/g, ' ');
/** UGX 271,730,000 -> 271.7M (the full figure stays in the tooltip) */
const short = (n) => {
    const v = Number(n || 0), a = Math.abs(v);
    if (a >= 1e9) return (v / 1e9).toFixed(a >= 1e10 ? 0 : 1) + 'B';
    if (a >= 1e6) return (v / 1e6).toFixed(a >= 1e8 ? 0 : 1) + 'M';
    if (a >= 1e3) return (v / 1e3).toFixed(0) + 'K';
    return String(v);
};
const greeting = () => { const h = new Date().getHours(); return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'; };


/** A Settings workstation card: Cinzel head bar in the section's accent, orange line under it, body below. */
function Card({ title, icon: Icon, accent = 'orange', wide = false, right, children, label }) {
    return (
        <section className={`${styles.card} ${wide ? styles.cardWide : ''}`} data-accent={accent} aria-label={label || title}>
            <header className={styles.cardHead}>
                <span className={styles.cardTitle}>{Icon && <span className={styles.headIcon}><Icon aria-hidden="true" /></span>}{title}</span>
                {right}
            </header>
            <div className={styles.cardBody}>{children}</div>
        </section>
    );
}

/** A cream KPI tile: icon frame, big figure, label, and where the click goes. */
function Tile({ to, n, label, icon: Icon, tone = 'orange', money = false, hint }) {
    const value = n == null ? '-' : money ? short(n) : fmt(n);
    return (
        <Link className={styles.tile} data-tone={tone} to={to} title={(money && n != null ? 'UGX ' + fmt(n) + ' - ' : '') + (hint || 'Open the list')}>
            <span className={styles.tileTop}>
                {Icon && <span className={styles.tileIcon}><Icon aria-hidden="true" /></span>}
                <FiArrowRight className={styles.tileGo} aria-hidden="true" />
            </span>
            <span className={styles.tileNum}>{money && n != null && <small>UGX </small>}{value}</span>
            <span className={styles.tileLabel}>{label}</span>
        </Link>
    );
}

/** The recovery ring: how much of all the title money has come in. */
function Ring({ pct }) {
    const p = Math.max(0, Math.min(100, Number(pct) || 0));
    const r = 52, c = 2 * Math.PI * r;
    return (
        <div className={styles.ring} role="img" aria-label={'Capital recovered: ' + p + ' percent'}>
            <svg viewBox="0 0 128 128" aria-hidden="true">
                <circle className={styles.ringTrack} cx="64" cy="64" r={r} />
                <circle className={styles.ringFill} cx="64" cy="64" r={r} strokeDasharray={c} strokeDashoffset={c * (1 - p / 100)} />
            </svg>
            <div className={styles.ringText}><strong>{p.toFixed(p % 1 ? 1 : 0)}%</strong><span>recovered</span></div>
        </div>
    );
}

function Trend({ trend }) {
    const rows = trend || [];
    const max = Math.max(1, ...rows.map(t => Number(t.amount || 0)));
    const last = rows.length - 1;
    return (
        <div className={styles.trend} aria-label="Money received per month, last 6 months">
            {rows.map((t, i) => {
                const h = Math.max(3, (Number(t.amount) / max) * 100);
                return (
                    <div key={t.month} className={styles.trendCol} title={t.month + ': UGX ' + fmt(t.amount)}>
                        <span className={styles.trendVal}>{Number(t.amount) ? short(t.amount) : '0'}</span>
                        <div className={styles.trendTrack}><div className={`${styles.trendBar} ${i === last ? styles.trendBarNow : ''}`} style={{ height: h + '%' }} /></div>
                        <span className={styles.trendLabel}>{MONTHS[Number(String(t.month).slice(5, 7)) - 1]}</span>
                    </div>
                );
            })}
        </div>
    );
}

/** One project type: a stacked bar of where its open projects stand, opening to the full list. */
function Pipeline({ byType }) {
    const [open, setOpen] = useState(null);
    const types = Object.entries(byType || {})
        .map(([t, m]) => [t, m, Object.entries(m).filter(([k]) => k !== 'HANDED OVER').reduce((s, [, v]) => s + v, 0), m['HANDED OVER'] || 0])
        .sort((a, b) => b[2] - a[2]);
    if (types.length === 0) return <div className={styles.empty}>No projects yet.</div>;
    const PALETTE = ['#EE8C3A', '#06b6d4', '#10b981', '#eab308', '#8b5cf6', '#f97316', '#14b8a6', '#64748b', '#ec4899', '#84cc16', '#0ea5e9'];
    return (
        <div className={styles.pipe}>
            {types.map(([t, m, openCount, handed]) => {
                const parts = Object.entries(m).filter(([k]) => k !== 'HANDED OVER');
                const isOpen = open === t;
                return (
                    <div key={t} className={`${styles.pipeRow} ${isOpen ? styles.pipeRowOpen : ''}`}>
                        <button type="button" className={styles.pipeHead} aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : t)}>
                            <span className={styles.pipeName}>{typeLabel(t)}</span>
                            <span className={styles.pipeBar} aria-hidden="true">
                                {parts.map(([k, v], i) => (
                                    <span key={k} style={{ flexGrow: v, background: k === 'RECEIVABLES' ? '#ef4444' : k === 'PENDING' ? '#94a3b8' : PALETTE[i % PALETTE.length] }} />
                                ))}
                            </span>
                            <span className={styles.pipeCount}><strong>{openCount}</strong> open{handed ? ' · ' + handed + ' handed over' : ''}</span>
                            <FiChevronDown className={styles.pipeChevron} aria-hidden="true" />
                        </button>
                        {isOpen && (
                            <ul className={styles.pipeList}>
                                {parts.map(([k, v], i) => (
                                    <li key={k}>
                                        <span className={styles.pipeDot} style={{ background: k === 'RECEIVABLES' ? '#ef4444' : k === 'PENDING' ? '#94a3b8' : PALETTE[i % PALETTE.length] }} />
                                        <span className={styles.pipeStatus}>{k}</span>
                                        <span className={styles.pipeNum}>{v}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                );
            })}
        </div>
    );
}

function Period({ p }) {
    const inn = Number(p.revenue || 0), out = Number(p.expenses || 0), max = Math.max(1, inn, out);
    const net = Number(p.net || 0);
    return (
        <div className={styles.group}>
            <div className={styles.groupLabel}>{p.label}</div>
            <div className={styles.flow}>
                <div className={styles.flowRow}><span>Money in</span><span className={styles.flowTrack}><span className={styles.flowIn} style={{ width: (inn / max) * 100 + '%' }} /></span><strong title={'UGX ' + fmt(inn)}>{short(inn)}</strong></div>
                <div className={styles.flowRow}><span>Expenses</span><span className={styles.flowTrack}><span className={styles.flowOut} style={{ width: (out / max) * 100 + '%' }} /></span><strong title={'UGX ' + fmt(out)}>{short(out)}</strong></div>
            </div>
            <div className={styles.groupFoot}>
                <span>Net <strong className={net >= 0 ? styles.good : styles.bad}>UGX {fmt(net)}</strong></span>
                <span>{fmt(p.transactions)} payment{Number(p.transactions) === 1 ? '' : 's'}</span>
            </div>
        </div>
    );
}

const Dashboard = () => {
    const { user } = useAuth();
    const [data, setData] = useState(() => cached('home'));   // a return visit draws at once, then refreshes
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const loadedAt = useRef(0);

    const load = useCallback(() => {
        setBusy(true);
        return api.get('/dashboard/home')
            .then(r => { setData(remember('home', r.data)); setError(''); loadedAt.current = Date.now(); })
            .catch(e => setError(errorText(e)))
            .finally(() => setBusy(false));
    }, []);

    useEffect(() => {
        let alive = true;
        api.get('/dashboard/home').then(r => { if (alive) { setData(remember('home', r.data)); loadedAt.current = Date.now(); } })
            .catch(e => { if (alive) setError(errorText(e)); });
        const onVis = () => { if (!document.hidden && Date.now() - loadedAt.current > 5 * 60 * 1000) load(); };
        document.addEventListener('visibilitychange', onVis);
        return () => { alive = false; document.removeEventListener('visibilitychange', onVis); };
    }, [load]);

    if (!data && !error) return (<div className={styles.container}><LoadingState label="LOADING DASHBOARD..." size="page" /></div>);

    const b = new Set((data && data.blocks) || []);
    const wq = (data && data.workQueue) || {};
    const money = data && data.money;
    const health = data && data.systemHealth;
    const today = new Date();

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.titleBlock}>
                    <h1 className={styles.pageTitle}>Dashboard</h1>
                    <p className={styles.pageSubtitle}>{data ? String(data.rankLabel || '').toUpperCase() : ''} · All actions are logged.</p>
                </div>
                <HeaderActions>
                    <span className={styles.syncBadge}><FiClock aria-hidden="true" /> LAST SYNC {data ? day(data.serverTime) : '-'}</span>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={busy} tip="Load the numbers again" onClick={load} />
                </HeaderActions>
            </header>

            <div className={styles.welcome}>
                <div>
                    <span className={styles.welcomeHi}>{greeting()}{user && user.username ? ', ' + user.username : ''}.</span>
                    <span className={styles.welcomeSub}><FiCalendar aria-hidden="true" /> {today.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</span>
                </div>
                <div className={styles.quick}>
                    <Link to="/land/new" className={styles.quickBtn}><FiPlusSquare aria-hidden="true" /> New project</Link>
                    <Link to="/land/projects" className={styles.quickBtn}><FiLayers aria-hidden="true" /> Ledger</Link>
                    {b.has('dueCalls') && <Link to="/recovery" className={styles.quickBtn}><FiPhoneCall aria-hidden="true" /> Recovery</Link>}
                    {b.has('money') && <Link to="/payments" className={styles.quickBtn}><FiDollarSign aria-hidden="true" /> Payments</Link>}
                </div>
            </div>

            {error && (<div className={styles.error} role="alert"><FiAlertTriangle aria-hidden="true" /> {error} <button type="button" className={styles.retry} onClick={load}>RETRY</button></div>)}

            {data && (
                <div className={styles.grid}>
                    {b.has('money') && money && (
                        <Card title="Money" icon={FiDollarSign} wide accent="orange">
                            <div className={styles.moneyTop}>
                                <div className={`${styles.group} ${styles.recover}`}>
                                    <Ring pct={money.collectionPercent} />
                                    <div className={styles.recoverText}>
                                        <span className={styles.groupLabel}>Capital recovered</span>
                                        <strong className={styles.bigMoney}>UGX {fmt(money.titleCollected)}</strong>
                                        <span className={styles.muted}>of UGX {fmt(money.totalValue)} in title work</span>
                                    </div>
                                </div>
                                <div className={styles.tiles}>
                                    <Tile to="/payments?tab=TITLE" n={money.titleCollected} money label="Title money collected" icon={FiCheckCircle} tone="green" />
                                    <Tile to="/land/projects?tab=CRITICAL" n={money.titleArrears} money label="Title money still owed" icon={FiAlertTriangle} tone="red" />
                                    <Tile to="/payments" n={money.collectedThisMonth} money label="Collected this month" icon={FiTrendingUp} tone="orange" />
                                    <Tile to="/land/projects?tab=RECEIVABLES" n={money.storageFeesUnpaid} money label="Storage fees unpaid" icon={FiArchive} tone="yellow" />
                                </div>
                            </div>
                            <div className={styles.moneyBottom}>
                                <div className={styles.group}>
                                    <div className={styles.groupLabel}>Money received, last 6 months</div>
                                    <Trend trend={money.trend} />
                                </div>
                                <div className={styles.group}>
                                    <div className={styles.groupLabel}>Storage fees</div>
                                    <div className={styles.kv}><span>Accrued (in receivables)</span><strong>UGX {fmt(money.storageFeesAccrued)}</strong></div>
                                    <div className={styles.kv}><span>Collected</span><strong className={styles.good}>UGX {fmt(money.storageFeesCollected)}</strong></div>
                                    <div className={styles.kv}><span>Unpaid</span><strong className={styles.bad}>UGX {fmt(money.storageFeesUnpaid)}</strong></div>
                                    {Number(money.keptFees) > 0 && <div className={styles.kv}><span>Kept after set aside</span><strong>UGX {fmt(money.keptFees)}</strong></div>}
                                    {Number(money.undatedCount) > 0 && <div className={styles.note}>UGX {fmt(money.undatedSum)} recorded without a date ({money.undatedCount} opening deposit{money.undatedCount === 1 ? '' : 's'}) is in no month.</div>}
                                </div>
                            </div>
                        </Card>
                    )}

                    {b.has('periods') && data.periods && (
                        <Card title="Money in and out" icon={FiTrendingUp} accent="cyan">
                            <div className={styles.stack}>{Object.entries(data.periods).map(([k, p]) => <Period key={k} p={p} />)}</div>
                        </Card>
                    )}

                    {(b.has('dueCalls') || b.has('newProjects') || b.has('problems') || b.has('receivables')) && (
                        <Card title="Today" icon={FiCalendar} accent="green">
                            <div className={styles.tiles}>
                                {b.has('dueCalls') && <Tile to="/recovery" n={data.dueCalls} label="Clients due for a call" icon={FiPhoneCall} tone="cyan" />}
                                {b.has('newProjects') && <Tile to="/land/projects" n={data.newProjects} label="New projects (7 days)" icon={FiPlusSquare} tone="green" />}
                                {b.has('problems') && !b.has('workQueue') && <Tile to="/land/projects?tab=PROBLEM" n={data.problems} label="Problem flags" icon={FiAlertTriangle} tone="red" />}
                                {b.has('receivables') && !b.has('workQueue') && <Tile to="/land/projects?tab=RECEIVABLES" n={data.receivables} label="In receivables" icon={FiArchive} tone="yellow" />}
                            </div>
                        </Card>
                    )}

                    {b.has('workQueue') && (
                        <Card title="Work queue" icon={FiInbox} accent="orange">
                            <div className={styles.tiles}>
                                <Tile to="/land/projects?tab=PENDING" n={wq.pending && wq.pending.count} icon={FiClock} tone="slate"
                                    label={'Pending - set prices' + (wq.pending && wq.pending.oldestDays != null && wq.pending.count ? ' (oldest ' + wq.pending.oldestDays + ' d)' : '')} />
                                <Tile to="/land/projects?tab=PROBLEM" n={wq.problems} label="Problem flags" icon={FiAlertTriangle} tone="red" />
                                <Tile to="/land/projects?tab=RECEIVABLES" n={wq.receivables} label="In receivables" icon={FiArchive} tone="yellow" />
                                <Tile to="/land/projects?tab=PAID" n={wq.releaseReady} label="Ready for hand-over" icon={FiPackage} tone="green" />
                            </div>
                        </Card>
                    )}

                    {b.has('waitingForYou') && data.waitingForYou && (
                        <Card title="Waiting for you" icon={FiBookOpen} accent="violet">
                            <div className={styles.checklist}>
                                {[
                                    ['/land/projects?tab=PAID', data.waitingForYou.releaseReady, 'titles ready to hand over', FiPackage],
                                    ['/land/projects?tab=PROBLEM', data.waitingForYou.problems, 'problem flags to clear', FiAlertTriangle],
                                    ['/land/projects?tab=RECEIVABLES', data.waitingForYou.flaggedReceivableThisWeek, 'went into receivables this week', FiArchive],
                                    ['/payments?books=1', data.waitingForYou.booksMismatch, 'books check differences', FiShield],
                                ].map(([to, n, text, icon]) => (
                                    <Link key={to + text} to={to} className={`${styles.checkItem} ${Number(n) > 0 ? styles.checkItemHot : ''}`}>
                                        {React.createElement(icon, { 'aria-hidden': true, className: styles.checkIcon })}
                                        <strong>{n == null || n < 0 ? '-' : fmt(n)}</strong><span>{text}</span>
                                        <FiArrowRight aria-hidden="true" className={styles.checkGo} />
                                    </Link>
                                ))}
                            </div>
                        </Card>
                    )}

                    {b.has('releaseReady') && data.releaseReady && (
                        <Card title={'Ready for hand-over (' + fmt(data.releaseReady.count) + ')'} icon={FiPackage} accent="green">
                            {(data.releaseReady.first || []).length === 0 ? <div className={styles.empty}>Nothing is ready.</div>
                                : (<div className={styles.chips}>{data.releaseReady.first.map(p => (
                                    <Link key={p.id} to={'/folder/' + p.id} className={styles.chip} title={[p.type, p.client].filter(Boolean).join(' - ')}>
                                        <strong>#{p.index}</strong>{p.client && <span>{p.client}</span>}
                                    </Link>))}</div>)}
                        </Card>
                    )}

                    {b.has('systemHealth') && health && (
                        <Card title="System health" icon={FiShield} accent="slate">
                            <div className={styles.group}>
                                {[
                                    ['Failed sign-ins (24 h)', fmt(health.failedLogins24h), Number(health.failedLogins24h) > 5 ? 'warn' : 'ok', '/audit'],
                                    ['Night job failures (7 days)', fmt(health.jobFailures7d), Number(health.jobFailures7d) > 0 ? 'bad' : 'ok', null],
                                    ['Books check', health.booksMismatch === 0 ? 'adds up' : health.booksMismatch < 0 ? 'not checked' : health.booksMismatch + ' differ', health.booksMismatch === 0 ? 'ok' : 'bad', '/payments?books=1'],
                                    ['Staff accounts', fmt(health.accounts), 'ok', null],
                                    ['Audit lines today', fmt(health.auditLinesToday), 'ok', '/audit'],
                                ].map(([k, v, st, to]) => (
                                    <div key={k} className={styles.kv}>
                                        <span><i className={styles.light} data-state={st} aria-hidden="true" />{k}</span>
                                        {to ? <Link to={to} className={styles.kvLink}>{v}</Link> : <strong>{v}</strong>}
                                    </div>
                                ))}
                                {health.oneAdminWarning && <div className={`${styles.note} ${styles.bad}`}><FiLock aria-hidden="true" /> {health.oneAdminWarning}</div>}
                            </div>
                        </Card>
                    )}

                    {b.has('pipeline') && (
                        <Card title="Projects by type and stage" icon={FiLayers} wide accent="cyan"
                            right={<span className={styles.headNote}>Click a type to see every stage</span>}>
                            <Pipeline byType={data.pipeline} />
                        </Card>
                    )}

                    {b.has('recentActivity') && (
                        <Card title="Recent activity" icon={FiActivity} wide accent="orange" right={<Link to="/audit" className={styles.headLink}>Full audit log <FiArrowRight aria-hidden="true" /></Link>}>
                            {(data.recentActivity || []).length === 0 ? <div className={styles.empty}>Nothing yet.</div> : (
                                <ol className={styles.timeline}>
                                    {(data.recentActivity || []).map(a => (
                                        <li key={a.id}>
                                            <Link to={'/audit?id=' + a.id} className={styles.event}>
                                                <span className={styles.eventTime}>{time(a.timestamp)}<small>{day(a.timestamp).slice(0, 6)}</small></span>
                                                <span className={styles.eventBody}>
                                                    <strong>{friendlyAction(a.action)}</strong>
                                                    <span className={styles.eventWho}><FiUsers aria-hidden="true" /> {a.performedBy}</span>
                                                    {a.details && <span className={styles.eventText}>{a.details}</span>}
                                                </span>
                                            </Link>
                                        </li>
                                    ))}
                                </ol>
                            )}
                        </Card>
                    )}
                </div>
            )}
        </div>
    );
};

export default Dashboard;
