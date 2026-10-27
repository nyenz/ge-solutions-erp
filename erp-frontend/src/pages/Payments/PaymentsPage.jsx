// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
// fix181 (Section 16, 12.4): the payment lines, built on WHAT the money was for (TITLE or STORAGE FEES) and WHAT kind of
// line it is (opening deposit, payment in receivables, reversal) -- not on the old payment-type words.
//  - the server filters, sorts and pages (/recovery/payments/list); the cards are the true totals for the same filters
//    (/recovery/payments/totals), never just the rows on screen;
//  - the client who PAID (current name and phone), the project index and type, the receipt, reversed pairs;
//  - one date format (05 Oct 2026); "Date not recorded" for undated opening deposits; the entry time on a second line;
//  - search, tab, sort, dates and filters live in the address, so Back returns to the same list;
//  - a failed load says so (with RETRY) instead of looking like "no payments".
import RetryButton from '../../components/common/RetryButton';
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { scrollBehavior } from '../../utils/motion';   // fix226: follows Settings > Animation
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FiSearch, FiX, FiUser, FiRefreshCw, FiLayers, FiArrowUp, FiArrowDown, FiFileText, FiCheckSquare, FiChevronLeft, FiChevronRight, FiChevronDown, FiCheck, FiAlertTriangle } from 'react-icons/fi';
import HardwareModal from '../../components/common/HardwareModal';
import { PaymentHealthDot, PaymentHealthLegend } from '../../components/common/PaymentHealth';
import api from '../../api/axios';
import BackToTopButton from '../../components/common/BackToTopButton';
import HardwareDatePicker from '../../components/common/HardwareDatePicker';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import styles from './PaymentsPage.module.css';
import { LoadingState } from '../../components/common/LoadingState';
import TabDock, { accentOf } from '../../components/common/TabDock';
import { useSwapMotion } from '../../hooks/useTabMotion';
import useTableScrollHandoff from '../../hooks/useTableScrollHandoff';
import { errorText } from '../../utils/errorText';
import { useAuth } from '../../hooks/useAuth';
import { roleFlags } from '../../utils/roles';
import { PAY_METHODS, methodLabel } from '../../utils/paymentMethods';   // fix214

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
const PAGE = 50;
// fix214 (David): the method buttons -- every method, then "Not recorded" for payments saved before methods were asked for
const METHOD_FILTERS = PAY_METHODS.map(m => ({ key: m.value, label: m.label })).concat([{ key: 'NONE', label: 'Not recorded' }]);


const dayCount = (s) => { const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})/); if (!m) return null; return Math.max(0, Math.round((Date.now() - new Date(+m[1], +m[2] - 1, +m[3]).getTime()) / 864e5)); };

// One small custom drop-down (never the browser's own). Closes on a click outside or Escape.
const useClose = (open, setOpen) => {
    const ref = useRef(null);
    useEffect(() => {
        if (!open) return undefined;
        const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
        const k = (e) => { if (e.key === 'Escape') setOpen(false); };
        document.addEventListener('mousedown', h); document.addEventListener('keydown', k);
        return () => { document.removeEventListener('mousedown', h); document.removeEventListener('keydown', k); };
    }, [open, setOpen]);
    return ref;
};
const FilterMenu = ({ label, value, options, onPick, allLabel = 'All', compact = false, className = '' }) => {
    const [open, setOpen] = useState(false);
    const ref = useClose(open, setOpen);
    const cur = options.find(o => o.key === value);
    return (
        <div className={`${styles.fMenu} ${className}`} ref={ref}>
            <button type="button" className={`${styles.fBtn} ${value ? styles.fBtnOn : ''} ${compact ? styles.fBtnCompact : ''}`} aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen(o => !o)}>
                <span className={styles.fLab}>{label}</span>
                <span className={styles.fVal}>{cur ? cur.label : allLabel}</span>
                <FiChevronDown className={`${styles.fCaret} ${open ? styles.fCaretUp : ''}`} aria-hidden="true" />
            </button>
            {open && (
                <div className={styles.fPop} role="listbox" aria-label={label}>
                    <button type="button" role="option" aria-selected={!value} className={`${styles.fItem} ${!value ? styles.fItemOn : ''}`} onClick={() => { onPick(''); setOpen(false); }}>
                        <span>{allLabel}</span>{!value && <FiCheck aria-hidden="true" />}
                    </button>
                    {options.map(o => (
                        <button key={o.key} type="button" role="option" aria-selected={value === o.key} className={`${styles.fItem} ${value === o.key ? styles.fItemOn : ''}`} onClick={() => { onPick(o.key); setOpen(false); }}>
                            <span>{o.label}</span>
                            {o.note && <em>{o.note}</em>}
                            {value === o.key && <FiCheck aria-hidden="true" />}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};
// the "MORE" drop-down: the two tick boxes (Missing receipt, Include deleted projects) behind one button
const ToggleMenu = ({ label, items }) => {
    const [open, setOpen] = useState(false);
    const ref = useClose(open, setOpen);
    const n = items.filter(i => i.on).length;
    return (
        <div className={styles.fMenu} ref={ref}>
            <button type="button" className={`${styles.fBtn} ${n ? styles.fBtnOn : ''}`} aria-haspopup="true" aria-expanded={open} onClick={() => setOpen(o => !o)}>
                <span className={styles.fLab}>{label}</span>
                <span className={styles.fVal}>{n ? n + ' on' : 'None'}</span>
                <FiChevronDown className={`${styles.fCaret} ${open ? styles.fCaretUp : ''}`} aria-hidden="true" />
            </button>
            {open && (
                <div className={styles.fPop} role="group" aria-label={label}>
                    {items.map(i => (
                        <label key={i.key} className={`${styles.fItem} ${styles.fTick} ${i.on ? styles.fItemOn : ''}`}>
                            <input type="checkbox" checked={i.on} onChange={e => i.onToggle(e.target.checked)} />
                            <span className={styles.fBox} aria-hidden="true">{i.on && <FiCheck />}</span>
                            <span>{i.label}</span>
                        </label>
                    ))}
                </div>
            )}
        </div>
    );
};

const PaymentsPage = () => {
    const navigate = useNavigate();
    const tableHandoffRef = useTableScrollHandoff();
    const [params, setParams] = useSearchParams();
    const q = params.get('q') || '';
    const tab = params.get('tab') || 'ALL';
    const swapRef = useSwapMotion(tab);   // fix192: the list fades in gently when the tab changes
    const sort = params.get('sort') || 'date';
    const dir = params.get('dir') || 'desc';
    const from = params.get('from') || '';
    const to = params.get('to') || '';
    const includeDeleted = params.get('deleted') === '1';
    const missingReceipt = params.get('noreceipt') === '1';
    const method = params.get('method') || '';   // fix214
    const recordedBy = params.get('by') || '';
        const [receiptFor, setReceiptFor] = useState(null);
    const page = Math.max(0, Number(params.get('page') || 0));
    const highlight = params.get('row') || '';

    // fix206 (David): the Manager sees the payment LINES of the last 90 days (to check and fix entries), never the totals
    // or the whole history -- "not the full picture". The server enforces the same (PaymentController.list).
    const { user } = useAuth();
    const fullView = roleFlags(user).canSeeCompanyMoney;
    const [searchText, setSearchText] = useState(q);
    const [data, setData] = useState(null);       // { rows, total }
    const [totals, setTotals] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [books, setBooks] = useState(null);
    const openBooks = params.get('books') === '1';   // fix181 (17.10): the BOOKS_MISMATCH alert opens the check

    const set = useCallback((patch, keepPage) => {
        const next = new URLSearchParams(params);
        Object.entries(patch).forEach(([k, v]) => { if (v === '' || v === null || v === undefined || v === false) next.delete(k); else next.set(k, v === true ? '1' : String(v)); });
        if (!keepPage) next.delete('page');
        setParams(next, { replace: true });
    }, [params, setParams]);

    const load = useCallback(() => {
        setBusy(true); setError('');
        const p = { tab, sort, dir, q: q || undefined, from: from || undefined, to: to || undefined, includeDeleted, missingReceipt, method: method || undefined, recordedBy: recordedBy || undefined, page, size: PAGE };
        return Promise.all([
            api.get('/recovery/payments/list', { params: p }).then(r => setData(r.data)),
            fullView ? api.get('/recovery/payments/totals', { params: { tab, q: q || undefined, from: from || undefined, to: to || undefined, missingReceipt, method: method || undefined, recordedBy: recordedBy || undefined } }).then(r => setTotals(r.data)) : Promise.resolve(),
        ]).catch(e => setError(errorText(e))).finally(() => setBusy(false));
    }, [tab, sort, dir, q, from, to, includeDeleted, missingReceipt, method, recordedBy, page, fullView]);

    useEffect(() => {
        let alive = true;
        const p = { tab, sort, dir, q: q || undefined, from: from || undefined, to: to || undefined, includeDeleted, missingReceipt, method: method || undefined, recordedBy: recordedBy || undefined, page, size: PAGE };
        Promise.all([
            api.get('/recovery/payments/list', { params: p }),
            fullView ? api.get('/recovery/payments/totals', { params: { tab, q: q || undefined, from: from || undefined, to: to || undefined, missingReceipt, method: method || undefined, recordedBy: recordedBy || undefined } }) : Promise.resolve({ data: null }),
        ]).then(([l, t]) => { if (alive) { setData(l.data); setTotals(t.data); setError(''); } })
          .catch(e => { if (alive) setError(errorText(e)); });
        return () => { alive = false; };
    }, [tab, sort, dir, q, from, to, includeDeleted, missingReceipt, method, recordedBy, page, fullView]);

    // search waits a moment after typing
    useEffect(() => {
        const t = setTimeout(() => { if (searchText !== q) set({ q: searchText }); }, 400);
        return () => clearTimeout(t);
    }, [searchText, q, set]);

    const handleSort = (key) => set({ sort: key, dir: sort === key && dir === 'desc' ? 'asc' : 'desc' });
    const sortIcon = (field) => {
        if (sort !== field) return <span className={styles.sortArrowInactive}> &#8597;</span>;
        return dir === 'asc'
            ? <FiArrowUp style={{ display: 'inline', marginLeft: 3, fontSize: 10, color: 'currentColor' }} />
            : <FiArrowDown style={{ display: 'inline', marginLeft: 3, fontSize: 10, color: 'currentColor' }} />;
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

    useEffect(() => {
        if (!openBooks) return undefined;
        let alive = true;
        api.get('/recovery/payments/books-check').then(r => { if (alive) setBooks(r.data); }).catch(() => {});
        return () => { alive = false; };
    }, [openBooks]);

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
                    {fullView && <HeaderButton icon={FiCheckSquare} label="BOOKS CHECK" tip="Check that every project's payment lines add up to its amount paid" onClick={runBooksCheck} />}
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={busy} tip="Load the payments again" onClick={load} />
                </HeaderActions>
            </header>

            {books && (
                <div className={books.ok ? styles.booksOk : styles.booksBad} role="status">
                    {books.error ? books.error : books.ok ? 'Books check: every project adds up.' : `Books check: ${books.differences.length} project(s) do not add up (nothing was changed):`}
                    {!books.ok && (books.differences || []).map(d => (
                        <div key={d.projectId}>#{d.projectIndex} {d.client}: lines UGX {fmt(d.sumOfLines)}, amount paid UGX {fmt(d.amountPaid)} (difference UGX {fmt(d.difference)})</div>
                    ))}
                    <button type="button" className={styles.booksClose} onClick={() => setBooks(null)} aria-label="Close the books check"><FiX size={14} /></button>
                </div>
            )}

            {!fullView && (
                <p className={styles.subtitle}>You see the payment lines of the last 90 days, to check and correct entries. Totals and the full history are for the Director.</p>
            )}
            {fullView && (<>
            <div className={styles.summaryRow}>
                <div className={`${styles.sumCard} ${styles.sumGreen}`}>
                    <label>TITLE COLLECTED</label>
                    <strong>UGX {fmt(totals && totals.titleNet)}</strong>
                    <span>net of reversals</span>
                </div>
                <div className={`${styles.sumCard} ${styles.sumYellow}`}>
                    <label>STORAGE FEES COLLECTED</label>
                    <strong>UGX {fmt(totals && totals.storageNet)}</strong>
                    <span>net of reversals</span>
                </div>
                <div className={`${styles.sumCard} ${styles.sumRed}`}>
                    <label>REVERSED</label>
                    <strong>UGX {fmt(totals && totals.reversed)}</strong>
                    <span>taken back</span>
                </div>
                <div className={`${styles.sumCard} ${styles.sumWhite}`}>
                    <label>NET TOTAL</label>
                    <strong>UGX {fmt(totals && totals.net)}</strong>
                    <span>{totals ? fmt(totals.rowCount) + ' lines' : ''}</span>
                </div>
            </div>
            </>)}
            {fullView && totals && totals.undatedCount > 0 && (
                <p className={styles.subtitle}>UGX {fmt(totals.undatedSum)} recorded without a date ({totals.undatedCount} opening deposit(s)); they are in the totals but in no month.</p>
            )}

            <div className={styles.controlHub}>
                <div className={styles.controlRow}>
                    <div className={styles.searchBlock}>
                        <div className={styles.searchWrap}>
                            <input type="search" className={styles.searchInput}
                                placeholder="Search project, client, phone, amount..." title="Searches the project, plot, client, phone, amount, reference, who recorded it and the notes"
                                aria-label="Search payment records" autoComplete="off"
                                value={searchText} onChange={e => setSearchText(e.target.value)} />
                            <FiSearch className={styles.searchIcon} aria-hidden="true" />
                            {searchText && (<button type="button" className={styles.clearBtn} onClick={() => setSearchText('')} aria-label="Clear search"><FiX size={14} /></button>)}
                        </div>
                    </div>
                    <TabDock className={styles.dockSlot} items={TABS} value={tab} onChange={v => set({ tab: v === 'ALL' ? '' : v })} label="Filter payments" />
                </div>
                {/* filters as labelled drop-downs */}
                {(() => {
                    const methodOpts = METHOD_FILTERS.filter(m => m.key !== 'NONE' || !totals || (totals.byMethod || []).some(b => b.method === 'NONE')).map(m => {
                        const sum = totals && (totals.byMethod || []).find(b => b.method === m.key);
                        return { key: m.key, label: m.label, note: fullView && sum ? 'UGX ' + fmt(sum.net) : undefined };
                    });
                    const byOpts = ((data && data.recorders) || []).map(r => ({ key: r, label: r }));
                    const dates = (<>
                        <label className={styles.dateField}><span>FROM</span><HardwareDatePicker value={from} max={to || undefined} ariaLabel="From date" onChange={v => set({ from: v })} /></label>
                        <label className={styles.dateField}><span>TO</span><HardwareDatePicker value={to} min={from || undefined} ariaLabel="To date" onChange={v => set({ to: v })} /></label>
                    </>);
                    const toggles = [
                        { key: 'nr', label: 'Missing receipt', on: missingReceipt, onToggle: v => set({ noreceipt: v }) },
                        ...(fullView ? [{ key: 'del', label: 'Include deleted projects', on: includeDeleted, onToggle: v => set({ deleted: v }) }] : []),
                    ];
                    const active = [
                        method && { k: 'method', label: 'Paid with: ' + methodLabel(method), clear: () => set({ method: '' }) },
                        recordedBy && { k: 'by', label: 'Recorded by: ' + recordedBy, clear: () => set({ by: '' }) },
                        missingReceipt && { k: 'nr', label: 'Missing receipt', clear: () => set({ noreceipt: false }) },
                        includeDeleted && { k: 'del', label: 'Deleted projects included', clear: () => set({ deleted: false }) },
                    ].filter(Boolean);
                    const clearAll = () => set({ method: '', by: '', noreceipt: false, deleted: false, from: '', to: '' });
                    return (
                        <div className={styles.filterRow} data-layout="A">
                            {dates}
                            <span className={styles.filterSep} aria-hidden="true" />
                            <FilterMenu label="PAID WITH" value={method} options={methodOpts} onPick={v => set({ method: v })} allLabel="All methods" />
                            <FilterMenu label="RECORDED BY" value={recordedBy} options={byOpts} onPick={v => set({ by: v })} allLabel="Everyone" />
                            <ToggleMenu label="MORE" items={toggles} />
                            {(active.length > 0 || from || to) && <button type="button" className={styles.clearAll} onClick={clearAll}>CLEAR ALL</button>}
                        </div>
                    );
                })()}
                <div className={styles.legendRow}>
                    <span className={styles.legendItem}>Deleted projects are never in the totals. A line can be in two tabs (for example an opening deposit that paid the title).</span>
                    <span className={styles.legendItem}><PaymentHealthLegend /></span>
                </div>
            </div>

            {error && (
                <div className={styles.errorBar} role="alert"><FiAlertTriangle className={styles.errorIcon} aria-hidden="true" /><span className={styles.errorText}>{error}</span><RetryButton className={styles.errorRetry} onClick={load} /></div>
            )}

            {!data && !error ? (
                <LoadingState label="LOADING PAYMENTS..." />
            ) : (
                /* fix183: the SAME table card as the Project Ledger and the Client Ledger (edge-to-edge table, bottom corner
                   brackets and pins, PREV / RANGE / NEXT footer). It used to sit inside a padded panel with its own pager. */
                <div className={styles.tablePanel} data-tab-accent={accentOf(TABS, tab)} ref={swapRef}>
                    <div className={styles.decorBl} aria-hidden="true" />
                    <div className={styles.decorBr} aria-hidden="true" />
                        <div className={styles.tableScroll} ref={tableHandoffRef}>
                            <table className={styles.ledgerTable}>
                                <thead>
                                    <tr>
                                        <th className={styles.thSortable} onClick={() => handleSort('date')} aria-sort={sort === 'date' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>DATE PAID {sortIcon('date')}</th>
                                        <th className={`${styles.thSortable} gsStickyCol`} onClick={() => handleSort('project')} aria-sort={sort === 'project' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>PROJECT {sortIcon('project')}</th>
                                        <th className={styles.thSortable} onClick={() => handleSort('client')} aria-sort={sort === 'client' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>CLIENT WHO PAID {sortIcon('client')}</th>
                                        <th>FOR</th>
                                        <th>METHOD</th>
                                        <th className={styles.thSortable} onClick={() => handleSort('amount')} aria-sort={sort === 'amount' ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}>AMOUNT {sortIcon('amount')}</th>
                                        <th>RECEIPT</th>
                                        <th>RECORDED BY</th>
                                        <th>NOTES</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.length === 0 ? (
                                        <tr><td colSpan="9" className={styles.noRecords}><div className={styles.noRecordsInner}><FiLayers className={styles.noRecordsIcon} />
                                            <span>{q ? `No payment matches "${q}"` : 'No payment lines for these filters'}</span></div></td></tr>
                                    ) : rows.map((pay) => {
                                        const day = fmtDay(pay.paidOn);
                                        return (
                                            <tr key={pay.id} id={'pay-' + pay.id} onClick={() => openRow(pay)} tabIndex={0} role="row"
                                                className={`${styles.dataRow} ${String(pay.id) === highlight ? styles.rowHighlight : ''}`} data-kind={pay.kind === 'REVERSAL' ? 'rev' : pay.kind === 'OPENING_DEPOSIT' ? 'open' : pay.allocation === 'STORAGE' ? 'stor' : 'title'}
                                                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openRow(pay); } }}
                                                title="Open the project folder">
                                                <td>
                                                    <div className={styles.dateCell}>
                                                        <span className={styles.dateLine}>{pay.kind !== 'REVERSAL' && day && <PaymentHealthDot days={dayCount(pay.paidOn)} style={{ marginTop: 0 }} />}{day || <span className={styles.time}>Date not recorded</span>}</span>
                                                        {day && pay.timeKnown && <span className={styles.time}>{fmtTime(pay.paidOn)}</span>}
                                                        <span className={styles.time}>entered {fmtDay(pay.enteredAt)} {fmtTime(pay.enteredAt)}</span>
                                                    </div>
                                                </td>
                                                <td className="gsStickyCol">
                                                    <strong className={styles.plotNum}>#{pay.projectIndex || '---'}</strong>
                                                    <div className={styles.time}>{pay.projectTypeLabel || ''}{pay.plotNumber ? ' - plot ' + pay.plotNumber : ''}</div>
                                                    {pay.deleted && <div className={`${styles.time} ${styles.bad}`}>Deleted project</div>}
                                                </td>
                                                <td className={styles.ownerCell}>{pay.clientName}{pay.payerPhone && <div className={styles.time}>{pay.payerPhone}</div>}</td>
                                                <td>
                                                    <span className={`${styles.forCell} ${styles['for' + (pay.kind === 'REVERSAL' ? 'Rev' : pay.kind === 'OPENING_DEPOSIT' ? 'Open' : pay.allocation === 'STORAGE' ? 'Stor' : 'Title')]}`}>{pay.allocation === 'STORAGE' ? 'Storage fees' : 'Title work'}</span>
                                                    {KIND_LABEL[pay.kind] && <div className={styles.time}>{KIND_LABEL[pay.kind]}</div>}
                                                    {pay.reversed && <div className={`${styles.time} ${styles.bad}`}>Reversed</div>}
                                                    {pay.kind === 'REVERSAL' && pay.reversalOf && (
                                                        <button type="button" className={styles.linkBtn} onClick={e => { e.stopPropagation(); const el = document.getElementById('pay-' + pay.reversalOf); if (el) el.scrollIntoView({ behavior: scrollBehavior(), block: 'center' }); }}>
                                                            reverses payment of {fmtDay(pay.reversalOfDate) || 'an earlier day'}</button>
                                                    )}
                                                </td>
                                                <td>
                                                    <span className={`${pay.paymentMethod ? styles.methodCell : styles.methodCellNone} ${styles['m' + (pay.paymentMethod || 'NONE')]}`}>{methodLabel(pay.paymentMethod)}</span>
                                                    {pay.paymentReference && <div className={styles.time}>{pay.paymentReference}</div>}
                                                </td>
                                                <td>
                                                    <strong className={`${styles.amount} ${Number(pay.amountPaid) < 0 ? styles.bad : ''}`} data-strike={pay.reversed ? '' : undefined}>
                                                        UGX {fmt(pay.amountPaid)}</strong>
                                                    {pay.balanceAfter != null && <div className={styles.time}>owed after: UGX {fmt(pay.balanceAfter)}</div>}
                                                    {pay.paidPct != null && pay.kind !== 'REVERSAL' && (
                                                        <div className={styles.payProg}>
                                                            <div className={styles.payBar} role="progressbar" aria-valuenow={pay.paidPct} aria-valuemin={0} aria-valuemax={100} aria-label="How much of the project is paid after this line"><div className={`${styles.payFill} ${pay.paidPct >= 100 ? styles.payFillDone : ''}`} style={{ width: pay.paidPct + '%' }} /></div>
                                                            <span className={styles.payPct}>{pay.paidPct}% paid</span>
                                                        </div>)}
                                                </td>
                                                <td>
                                                    {pay.kind === 'REVERSAL' ? null : pay.hasReceipt
                                                        ? <button type="button" className={styles.receiptBtn} title="Open the receipt in the project folder" aria-label="Open the receipt"
                                                            onClick={e => { e.stopPropagation(); setReceiptFor(pay); }}><FiFileText aria-hidden="true" /></button>
                                                        : <span className={`${styles.time} ${styles.bad}`}>No receipt</span>}
                                                </td>
                                                <td><span className={styles.recorder}><FiUser size={10} /> {pay.recordedBy}</span></td>
                                                <td className={styles.notesCell}>{pay.notes || '---'}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    <div className={styles.pinsBottom} aria-hidden="true">{[...Array(4)].map((_, i) => <div key={i} className={styles.pin} />)}</div>
                    <footer className={styles.pagination} aria-label="Pagination" aria-live="polite">
                        <button type="button" className={styles.pageBtn} disabled={page === 0} aria-label="Previous page" onClick={() => set({ page: page - 1 }, true)}>
                            <FiChevronLeft aria-hidden="true" /> PREV
                        </button>
                        <span className={styles.pageIndicator} aria-current="page">
                            RANGE {page + 1}
                            {total > 0 && <span className={styles.recordCount}> — {first} TO {last} OF {fmt(total)} LINES</span>}
                        </span>
                        <button type="button" className={styles.pageBtn} disabled={last >= total} aria-label="Next page" onClick={() => set({ page: page + 1 }, true)}>
                            NEXT <FiChevronRight aria-hidden="true" />
                        </button>
                    </footer>
                </div>
            )}
            <HardwareModal isOpen={!!receiptFor} onClose={() => setReceiptFor(null)} title="RECEIPT">
                {receiptFor && (
                    <>
                        <div className={styles.rcpPaper}>
                            <div className={styles.rcpHead}><strong>GE SOLUTIONS</strong><span>OFFICIAL RECEIPT</span></div>
                            <div className={styles.rcpRow}><span>Project</span><b>#{receiptFor.projectIndex}</b></div>
                            <div className={styles.rcpRow}><span>Received from</span><b>{receiptFor.clientName}</b></div>
                            <div className={styles.rcpRow}><span>Date</span><b>{fmtDay(receiptFor.paidOn)}</b></div>
                            <div className={styles.rcpRow}><span>Method</span><b>{methodLabel(receiptFor.paymentMethod)}</b></div>
                            <div className={`${styles.rcpRow} ${styles.rcpTotal}`}><span>Amount</span><b>UGX {fmt(receiptFor.amountPaid)}</b></div>
                        </div>
                        <div className={styles.rcpBtns}>
                            <button type="button" className={styles.rcpOpen} onClick={() => { const r = receiptFor; setReceiptFor(null); openRow(r); }}>OPEN PROJECT FOLDER</button>
                        </div>
                    </>
                )}
            </HardwareModal>
        </div>
    );
};

export default PaymentsPage;
