// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
// fix181 (Section 16, 12.4): the payment lines, built on WHAT the money was for (TITLE or STORAGE FEES) and WHAT kind of
// line it is (opening deposit, payment in receivables, reversal) -- not on the old payment-type words.
//  - the server filters, sorts and pages (/recovery/payments/list); the cards are the true totals for the same filters
//    (/recovery/payments/totals), never just the rows on screen;
//  - the client who PAID (current name and phone), the project index and type, the receipt, reversed pairs;
//  - one date format (05 Oct 2026); "Date not recorded" for undated opening deposits; the entry time on a second line;
//  - search, tab, sort, dates and filters live in the address, so Back returns to the same list;
//  - a failed load says so (with RETRY) instead of looking like "no payments".
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FiSearch, FiX, FiUser, FiRefreshCw, FiLayers, FiArrowUp, FiArrowDown, FiFileText, FiCheckSquare } from 'react-icons/fi';
import api from '../../api/axios';
import HardwarePanel from '../../components/ui/HardwarePanel';
import BackToTopButton from '../../components/common/BackToTopButton';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import styles from './PaymentsPage.module.css';
import { LoadingState } from '../../components/common/LoadingState';
import TabDock, { accentOf } from '../../components/common/TabDock';
import useTableScrollHandoff from '../../hooks/useTableScrollHandoff';
import { errorText } from '../../utils/errorText';

const fmt = (n) => Number(n || 0).toLocaleString();
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
// one fixed format, read from the server's own text (no time-zone guessing): "05 Oct 2026"
const fmtDay = (s) => { if (!s) return null; const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? m[3] + ' ' + MONTHS[Number(m[2]) - 1] + ' ' + m[1] : null; };
const fmtTime = (s) => { const m = String(s || '').match(/T(\d{2}):(\d{2})/); return m ? m[1] + ':' + m[2] : ''; };

const TABS = [
    { key: 'ALL', label: 'ALL' },
    { key: 'TITLE', label: 'TITLE', accent: 'green' },
    { key: 'STORAGE', label: 'STORAGE FEES', accent: 'yellow' },
    { key: 'OPENING', label: 'OPENING DEPOSITS', accent: 'cyan' },
    { key: 'REVERSALS', label: 'REVERSALS', accent: 'red' },
];
const KIND_LABEL = { OPENING_DEPOSIT: 'OPENING DEPOSIT', IN_RECEIVABLES: 'PAYMENT IN RECEIVABLES', REVERSAL: 'REVERSAL', PAYMENT: '' };
const PURPOSE_COLOR = { TITLE: '#22c55e', STORAGE: '#eab308' };
const PAGE = 50;

const PaymentsPage = () => {
    const navigate = useNavigate();
    const tableHandoffRef = useTableScrollHandoff();
    const [params, setParams] = useSearchParams();
    const q = params.get('q') || '';
    const tab = params.get('tab') || 'ALL';
    const sort = params.get('sort') || 'date';
    const dir = params.get('dir') || 'desc';
    const from = params.get('from') || '';
    const to = params.get('to') || '';
    const includeDeleted = params.get('deleted') === '1';
    const missingReceipt = params.get('noreceipt') === '1';
    const page = Math.max(0, Number(params.get('page') || 0));
    const highlight = params.get('row') || '';

    const [searchText, setSearchText] = useState(q);
    const [data, setData] = useState(null);       // { rows, total }
    const [totals, setTotals] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [books, setBooks] = useState(null);

    const set = useCallback((patch, keepPage) => {
        const next = new URLSearchParams(params);
        Object.entries(patch).forEach(([k, v]) => { if (v === '' || v === null || v === undefined || v === false) next.delete(k); else next.set(k, v === true ? '1' : String(v)); });
        if (!keepPage) next.delete('page');
        setParams(next, { replace: true });
    }, [params, setParams]);

    const load = useCallback(() => {
        setBusy(true); setError('');
        const p = { tab, sort, dir, q: q || undefined, from: from || undefined, to: to || undefined, includeDeleted, missingReceipt, page, size: PAGE };
        return Promise.all([
            api.get('/recovery/payments/list', { params: p }).then(r => setData(r.data)),
            api.get('/recovery/payments/totals', { params: { tab, q: q || undefined, from: from || undefined, to: to || undefined, missingReceipt } }).then(r => setTotals(r.data)),
        ]).catch(e => setError(errorText(e))).finally(() => setBusy(false));
    }, [tab, sort, dir, q, from, to, includeDeleted, missingReceipt, page]);

    useEffect(() => {
        let alive = true;
        const p = { tab, sort, dir, q: q || undefined, from: from || undefined, to: to || undefined, includeDeleted, missingReceipt, page, size: PAGE };
        Promise.all([
            api.get('/recovery/payments/list', { params: p }),
            api.get('/recovery/payments/totals', { params: { tab, q: q || undefined, from: from || undefined, to: to || undefined, missingReceipt } }),
        ]).then(([l, t]) => { if (alive) { setData(l.data); setTotals(t.data); setError(''); } })
          .catch(e => { if (alive) setError(errorText(e)); });
        return () => { alive = false; };
    }, [tab, sort, dir, q, from, to, includeDeleted, missingReceipt, page]);

    // search waits a moment after typing
    useEffect(() => {
        const t = setTimeout(() => { if (searchText !== q) set({ q: searchText }); }, 400);
        return () => clearTimeout(t);
    }, [searchText, q, set]);

    const handleSort = (key) => set({ sort: key, dir: sort === key && dir === 'desc' ? 'asc' : 'desc' });
    const sortIcon = (field) => {
        if (sort !== field) return <span className={styles.sortArrowInactive}> &#8597;</span>;
        return dir === 'asc'
            ? <FiArrowUp style={{ display: 'inline', marginLeft: 3, fontSize: 10, color: '#fff' }} />
            : <FiArrowDown style={{ display: 'inline', marginLeft: 3, fontSize: 10, color: '#fff' }} />;
    };

    const openRow = (pay) => {
        if (!pay.projectId) return;
        set({ row: pay.id }, true);
        navigate(`/folder/${pay.projectId}#payment-${pay.id}`);
    };

    const runBooksCheck = async () => {
        try { setBooks((await api.get('/recovery/payments/books-check')).data); }
        catch (e) { setBooks({ ok: false, error: errorText(e), differences: [] }); }
    };

    const rows = (data && data.rows) || [];
    const total = (data && data.total) || 0;
    const first = total === 0 ? 0 : page * PAGE + 1;
    const last = Math.min(total, (page + 1) * PAGE);

    return (
        <div className={styles.container}>
            <BackToTopButton />
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Payment Records</h1>
                    <p className={styles.subtitle}>Every payment line: title work and storage fees, opening deposits and reversals</p>
                </div>
                <HeaderActions>
                    <HeaderButton icon={FiCheckSquare} label="BOOKS CHECK" tip="Check that every project's payment lines add up to its amount paid" onClick={runBooksCheck} />
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={busy} tip="Load the payments again" onClick={load} />
                </HeaderActions>
            </header>

            {books && (
                <div className={books.ok ? styles.booksOk : styles.booksBad} role="status">
                    {books.error ? books.error : books.ok ? 'Books check: every project adds up.' : `Books check: ${books.differences.length} project(s) do not add up (nothing was changed):`}
                    {!books.ok && (books.differences || []).map(d => (
                        <div key={d.projectId}>#{d.projectIndex} {d.client}: lines UGX {fmt(d.sumOfLines)}, amount paid UGX {fmt(d.amountPaid)} (difference UGX {fmt(d.difference)})</div>
                    ))}
                    <button type="button" className={styles.clearBtn} onClick={() => setBooks(null)} aria-label="Close"><FiX size={14} /></button>
                </div>
            )}

            <div className={styles.summaryRow}>
                <div className={`${styles.sumCard} ${styles.sumGreen}`}>
                    <label style={{ color: '#22c55e' }}>TITLE COLLECTED</label>
                    <strong style={{ color: '#22c55e' }}>UGX {fmt(totals && totals.titleNet)}</strong>
                    <span>net of reversals</span>
                </div>
                <div className={`${styles.sumCard} ${styles.sumWhite}`}>
                    <label style={{ color: '#eab308' }}>STORAGE FEES COLLECTED</label>
                    <strong style={{ color: '#eab308' }}>UGX {fmt(totals && totals.storageNet)}</strong>
                    <span>net of reversals</span>
                </div>
                <div className={`${styles.sumCard} ${styles.sumRed}`}>
                    <label style={{ color: '#ef4444' }}>REVERSED</label>
                    <strong style={{ color: '#ef4444' }}>UGX {fmt(totals && totals.reversed)}</strong>
                    <span>taken back</span>
                </div>
                <div className={`${styles.sumCard} ${styles.sumWhite}`}>
                    <label>NET TOTAL</label>
                    <strong>UGX {fmt(totals && totals.net)}</strong>
                    <span>{totals ? fmt(totals.rowCount) + ' lines' : ''}</span>
                </div>
            </div>
            {totals && totals.undatedCount > 0 && (
                <p className={styles.subtitle}>UGX {fmt(totals.undatedSum)} recorded without a date ({totals.undatedCount} opening deposit(s)); they are in the totals but in no month.</p>
            )}

            <div className={styles.controlHub}>
                <div className={styles.controlRow}>
                    <div className={styles.searchBlock}>
                        <div className={styles.searchWrap}>
                            <input type="search" className={styles.searchInput}
                                placeholder="Search project, plot, client, phone, amount, recorded by, notes..."
                                aria-label="Search payment records" autoComplete="off"
                                value={searchText} onChange={e => setSearchText(e.target.value)} />
                            <FiSearch className={styles.searchIcon} aria-hidden="true" />
                            {searchText && (<button type="button" className={styles.clearBtn} onClick={() => setSearchText('')} aria-label="Clear search"><FiX size={14} /></button>)}
                        </div>
                    </div>
                    <TabDock className={styles.dockSlot} items={TABS} value={tab} onChange={v => set({ tab: v === 'ALL' ? '' : v })} label="Filter payments" />
                </div>
                <div className={styles.legendRow}>
                    <label className={styles.legendItem}>From <input type="date" value={from} onChange={e => set({ from: e.target.value })} /></label>
                    <label className={styles.legendItem}>To <input type="date" value={to} onChange={e => set({ to: e.target.value })} /></label>
                    <label className={styles.legendItem}><input type="checkbox" checked={missingReceipt} onChange={e => set({ noreceipt: e.target.checked })} /> Missing receipt</label>
                    <label className={styles.legendItem}><input type="checkbox" checked={includeDeleted} onChange={e => set({ deleted: e.target.checked })} /> Include deleted projects (never in totals)</label>
                    <span className={styles.legendItem}>A line can be in two tabs (for example an opening deposit that paid the title).</span>
                </div>
            </div>

            {error && (
                <div className={styles.booksBad} role="alert">{error} <button type="button" className={styles.retryBtn} onClick={load}>RETRY</button></div>
            )}

            {!data && !error ? (
                <LoadingState label="LOADING PAYMENTS..." />
            ) : (
                <div className={styles.accentWrap} data-tab-accent={accentOf(TABS, tab)}>
                    <HardwarePanel variant="dark" hideTop>
                        <div className={styles.tableScroll} ref={tableHandoffRef}>
                            <table className={styles.ledgerTable}>
                                <thead>
                                    <tr>
                                        <th className={styles.thSortable} onClick={() => handleSort('date')} aria-sort={sort === 'date' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>DATE PAID {sortIcon('date')}</th>
                                        <th className={styles.thSortable} onClick={() => handleSort('project')} aria-sort={sort === 'project' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>PROJECT {sortIcon('project')}</th>
                                        <th className={styles.thSortable} onClick={() => handleSort('client')} aria-sort={sort === 'client' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>CLIENT WHO PAID {sortIcon('client')}</th>
                                        <th>FOR</th>
                                        <th className={styles.thSortable} onClick={() => handleSort('amount')} aria-sort={sort === 'amount' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>AMOUNT {sortIcon('amount')}</th>
                                        <th>RECEIPT</th>
                                        <th>RECORDED BY</th>
                                        <th>NOTES</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.length === 0 ? (
                                        <tr><td colSpan="8" className={styles.noRecords}><div className={styles.noRecordsInner}><FiLayers className={styles.noRecordsIcon} />
                                            <span>{q ? `No payment matches "${q}"` : 'No payment lines for these filters'}</span></div></td></tr>
                                    ) : rows.map((pay) => {
                                        const day = fmtDay(pay.paidOn);
                                        const color = PURPOSE_COLOR[pay.allocation] || '#22c55e';
                                        return (
                                            <tr key={pay.id} id={'pay-' + pay.id} onClick={() => openRow(pay)} tabIndex={0} role="row"
                                                className={`${styles.dataRow} ${String(pay.id) === highlight ? styles.rowHighlight : ''}`}
                                                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openRow(pay); } }}
                                                title="Open the project folder">
                                                <td>
                                                    <div className={styles.dateCell}>
                                                        <span>{day || <span className={styles.time}>Date not recorded</span>}</span>
                                                        {day && pay.timeKnown && <span className={styles.time}>{fmtTime(pay.paidOn)}</span>}
                                                        <span className={styles.time}>entered {fmtDay(pay.enteredAt)} {fmtTime(pay.enteredAt)}</span>
                                                    </div>
                                                </td>
                                                <td>
                                                    <strong className={styles.plotNum}>#{pay.projectIndex || '---'}</strong>
                                                    <div className={styles.time}>{pay.projectTypeLabel || ''}{pay.plotNumber ? ' - plot ' + pay.plotNumber : ''}</div>
                                                    {pay.deleted && <span className={styles.typeBadge} style={{ color: '#ef4444' }}>DELETED</span>}
                                                </td>
                                                <td className={styles.ownerCell}>{pay.clientName}{pay.payerPhone && <div className={styles.time}>{pay.payerPhone}</div>}</td>
                                                <td>
                                                    <span className={styles.typeBadge} style={{ color }}>
                                                        <i className={styles.legendDot} style={{ background: color }} aria-hidden="true" />
                                                        {pay.allocation === 'STORAGE' ? 'STORAGE FEES' : 'TITLE'}
                                                    </span>
                                                    {KIND_LABEL[pay.kind] && <div className={styles.time}>{KIND_LABEL[pay.kind]}</div>}
                                                    {pay.reversed && <div className={styles.time} style={{ color: '#ef4444' }}>REVERSED</div>}
                                                    {pay.kind === 'REVERSAL' && pay.reversalOf && (
                                                        <button type="button" className={styles.linkBtn} onClick={e => { e.stopPropagation(); const el = document.getElementById('pay-' + pay.reversalOf); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }}>
                                                            reverses payment of {fmtDay(pay.reversalOfDate) || 'an earlier day'}</button>
                                                    )}
                                                </td>
                                                <td>
                                                    <strong className={styles.amount} style={{ color: Number(pay.amountPaid) < 0 ? '#ef4444' : color, textDecoration: pay.reversed ? 'line-through' : 'none' }}>
                                                        UGX {fmt(pay.amountPaid)}</strong>
                                                    {pay.balanceAfter != null && <div className={styles.time}>owed after: UGX {fmt(pay.balanceAfter)}</div>}
                                                </td>
                                                <td>
                                                    {pay.kind === 'REVERSAL' ? null : pay.hasReceipt
                                                        ? <button type="button" className={styles.linkBtn} title="Open the receipt in the project folder"
                                                            onClick={e => { e.stopPropagation(); openRow(pay); }}><FiFileText aria-hidden="true" /> receipt</button>
                                                        : <span className={styles.typeBadge} style={{ color: '#ef4444' }}>NO RECEIPT</span>}
                                                </td>
                                                <td><span className={styles.recorder}><FiUser size={10} /> {pay.recordedBy}</span></td>
                                                <td className={styles.notesCell}>{pay.notes || '---'}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </HardwarePanel>
                    <div className={styles.legendRow} aria-live="polite">
                        <span className={styles.legendItem}>{first} to {last} of {fmt(total)}</span>
                        <button type="button" className={styles.retryBtn} disabled={page === 0} onClick={() => set({ page: page - 1 }, true)}>PREVIOUS</button>
                        <button type="button" className={styles.retryBtn} disabled={last >= total} onClick={() => set({ page: page + 1 }, true)}>NEXT</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PaymentsPage;
