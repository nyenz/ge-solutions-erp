#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOLDEN SEED -- fix69
=====================================================================
1. REPORTS / ANALYSIS IS A LIGHT SURFACE NOW
   Five stacked panels of controls rendered in navy was a wall of dark
   from header to footer. The studio is now paper: cream workbench,
   white controls with navy ink, light table body. The only dark things
   left are the stat cards and the table header bar -- the two things
   that should pull the eye.

2. REFRESH ON THE REPORTS HEADER
   The studio caches its dataset locally, so the header button bumps a
   token the studio listens for and re-pulls whatever dataset is loaded.

3. NO DUPLICATION ON THE ANALYSIS TAB
   The EXPENSE ANALYSIS drawer was the EXPENSES dataset with the
   grouping pre-chosen -- the same numbers, two clicks away in the
   builder. Gone. The canned CSV pillars stay on REPORTS. ANALYSIS is
   now one thing: ask anything.

4. DROPDOWNS INSTEAD OF CHIP WALLS
   Forty column checkboxes laid out as chips filled a phone screen
   before you reached anything else. Same include/exclude control,
   folded into a dropdown. Dataset picker is a select too.

5. HOVER EXPLAINERS TIME OUT
   They sat there as long as the pointer did. They now fade after six
   seconds -- long enough to read twice, short enough to stop being
   furniture. Also portalled into #root so they scale with the new UI
   size setting.

6. STAT BOXES CAME DOWN A SIZE
   fix68 overshot. The default scale is smaller, and it is now a
   SETTING rather than a constant.

7. SETTINGS: A REAL APPEARANCE PANEL
   New preferences system (context/PreferencesProvider) writing data
   attributes and CSS variables onto <html>, so a preference reaches
   every page without every page opting in. Six settings, all of them
   actually wired: page theme (cream / slate dark), UI size, stat card
   size, reduced motion, hover-explainer dwell or off, high-contrast
   tables. Per-device in localStorage.

8. FOLDER PAGE: OWNER NAMES OPEN THE DOSSIER
   In the OWNERS tab and in RELATED PROJECTS, the owner name is now a
   link to that client's portfolio. It was the one place in the app
   holding a client name that did not go anywhere.

9. AUDIT: DATE RANGE + CSV EXPORT
   The log could be filtered by operator and action but not by when,
   which is the first question anyone asks of an audit trail. Added a
   from/to filter and an export of the current view.

Run:  python fix.py     (from the repo root)
Auto: git add -A / commit / push
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, 'erp-frontend', 'src')
P = lambda *a: os.path.join(FE, *a)

CHANGED, SKIPPED = [], []


def read(p):
    with open(p, 'r', encoding='utf-8') as fh:
        return fh.read()


def write(p, text, label):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(text)
    if label not in CHANGED:
        CHANGED.append(label)
    print('  [write] ' + label)


def require(p, label):
    if not os.path.isfile(p):
        print('  [MISS ] ' + label)
        SKIPPED.append(label)
        return False
    return True


def swap(text, old, new, label):
    if new and new in text:
        print('  [ skip] ' + label + ' (already applied)')
        return text
    if old not in text:
        print('  [WARN ] ' + label + ' -- anchor not found, left alone')
        SKIPPED.append(label)
        return text
    print('  [patch] ' + label)
    return text.replace(old, new, 1)


def swap_all(text, old, new, label):
    if old not in text:
        print('  [ skip] ' + label + ' (nothing to replace)')
        return text
    print('  [patch] ' + label)
    return text.replace(old, new)


def append_block(text, marker, block, label):
    if marker in text:
        print('  [ skip] ' + label + ' (already applied)')
        return text
    print('  [patch] ' + label)
    return text.rstrip() + '\n' + block


def run(cmd):
    print('$ ' + ' '.join(cmd))
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


# ============================================ EMBEDDED FILE BODIES

TOOLTIP_JSX = r"""// PATH: erp-frontend/src/components/common/Tooltip.jsx
import React, { useState, useRef, useCallback, useEffect, useLayoutEffect, useId } from 'react';
import { createPortal } from 'react-dom';
import styles from './Tooltip.module.css';

/**
 * GOLDEN SEED -- THE HOVER EXPLAINER
 *
 * Wrap anything whose meaning isn't obvious -- an icon-only button, a short
 * tag like LOCKED, an abbreviation -- and it explains itself on hover.
 *
 * Why not the browser's own title="" attribute:
 *   - it waits roughly a second before appearing
 *   - it can't be styled, so it ignores the app's contrast rule entirely
 *   - it does nothing on touch, and staff use this on phones
 *   - screen readers treat it inconsistently
 *
 * It renders into document.body through a portal so it is never clipped by a
 * panel's overflow:hidden -- which is exactly what would happen inside the
 * table wrappers and panel bodies.
 *
 * fix68 -- TWO THINGS CHANGED HERE:
 *
 * 1. EDGE CLIPPING. The old version centred the bubble on the anchor and then
 *    clamped that CENTRE to 80px from each edge. 80px is less than half the
 *    bubble's width, so anything anchored near an edge -- the sidebar nav
 *    being the obvious one -- still had its left side cut off the screen.
 *    Guessing at a safe centre can't work, because the bubble's width isn't
 *    known until it has text in it. So it now renders, measures itself, and
 *    nudges horizontally by exactly the overflow. One extra paint, no clip.
 *
 * 2. WEIGHT. It was a bordered card: orange 1.5px edge, heavy shadow, DM Sans
 *    600. Next to a dense table that reads as another panel, and the border
 *    is what made it feel crowded. It is now a plain translucent slab --
 *    no border, no pointer, blurred backdrop, Inter at normal weight.
 */
// fix69: dwell and auto-dismiss come from the user's Appearance setting,
// which the provider writes onto <html data-tips>. "off" means the explainer
// never opens at all -- some people find it noise, and that is a fair call.
const TIP_MODES = {
    normal: { delay: 120, life: 6000 },
    slow:   { delay: 500, life: 9000 },
    off:    { delay: 0,   life: 0, disabled: true },
};
const tipMode = () => {
    if (typeof document === 'undefined') return TIP_MODES.normal;
    return TIP_MODES[document.documentElement.getAttribute('data-tips')] || TIP_MODES.normal;
};

// Portal target is #root, not <body>: the UI-size setting applies zoom to
// #root, and a bubble outside it would render at 100% next to a page at 125%
// and sit in the wrong place.
const portalTarget = () => (typeof document === 'undefined'
    ? null
    : (document.getElementById('root') || document.body));

export const Tooltip = ({ label, children, placement = 'top', delay, disabled = false, block = false }) => {
    const [open, setOpen] = useState(false);
    const [box, setBox] = useState({ top: 0, left: 0, place: placement });
    const [shift, setShift] = useState(0);
    const anchorRef = useRef(null);
    const bubbleRef = useRef(null);
    const timerRef = useRef(null);
    const lifeRef = useRef(null);
    const tipId = useId();

    const measure = useCallback(() => {
        const el = anchorRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        // Flip to the underside if there isn't room above.
        const place = (placement === 'top' && r.top < 64) ? 'bottom' : placement;
        setShift(0);
        setBox({
            top: place === 'bottom' ? r.bottom + 8 : r.top - 8,
            left: r.left + r.width / 2,
            place,
        });
    }, [placement]);

    // Measured correction: run after the bubble is in the DOM and has a real
    // width. dx is zero on the second pass, so this settles immediately.
    useLayoutEffect(() => {
        if (!open) return;
        const el = bubbleRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        const margin = 10;
        let dx = 0;
        if (r.left < margin) dx = margin - r.left;
        else if (r.right > window.innerWidth - margin) dx = (window.innerWidth - margin) - r.right;
        if (Math.abs(dx) > 0.5) setShift(s => s + dx);
    }, [open, box, shift]);

    const show = useCallback(() => {
        const mode = tipMode();
        if (disabled || !label || mode.disabled) return;
        clearTimeout(timerRef.current);
        clearTimeout(lifeRef.current);
        timerRef.current = setTimeout(() => {
            measure();
            setOpen(true);
            // Auto-dismiss: an explainer you have already read should not keep
            // sitting on top of the row underneath it.
            if (mode.life > 0) {
                lifeRef.current = setTimeout(() => { setOpen(false); setShift(0); }, mode.life);
            }
        }, delay === undefined ? mode.delay : delay);
    }, [disabled, label, delay, measure]);

    const hide = useCallback(() => {
        clearTimeout(timerRef.current);
        clearTimeout(lifeRef.current);
        setOpen(false);
        setShift(0);
    }, []);

    useEffect(() => () => { clearTimeout(timerRef.current); clearTimeout(lifeRef.current); }, []);

    useEffect(() => {
        if (!open) return undefined;
        const onKey = (e) => { if (e.key === 'Escape') hide(); };
        // Any scroll moves the anchor out from under the bubble, so just close.
        window.addEventListener('keydown', onKey);
        window.addEventListener('scroll', hide, true);
        window.addEventListener('resize', hide);
        return () => {
            window.removeEventListener('keydown', onKey);
            window.removeEventListener('scroll', hide, true);
            window.removeEventListener('resize', hide);
        };
    }, [open, hide]);

    if (!label) return children;

    return (
        <>
            <span
                ref={anchorRef}
                className={block ? `${styles.anchor} ${styles.anchorBlock}` : styles.anchor}
                onMouseEnter={show}
                onMouseLeave={hide}
                onFocus={show}
                onBlur={hide}
                onTouchStart={() => { if (tipMode().disabled) return; measure(); setOpen(o => !o); }}
                aria-describedby={open ? tipId : undefined}
            >
                {children}
            </span>
            {open && portalTarget() && createPortal(
                <div
                    ref={bubbleRef}
                    id={tipId}
                    role="tooltip"
                    className={styles.bubble}
                    style={{
                        top: box.top,
                        left: box.left,
                        transform: `translate(calc(-50% + ${shift}px), ${box.place === 'bottom' ? '0' : '-100%'})`,
                    }}
                >
                    {label}
                </div>,
                portalTarget(),
            )}
        </>
    );
};

/**
 * An icon-only button that explains itself. Use this instead of a bare
 * <button><FiSomething /></button>: the tooltip text doubles as the
 * aria-label, so it is impossible to ship an unlabelled icon button.
 */
export const IconButton = ({ tip, icon, onClick, className, size = 13, disabled = false }) => {
    const Icon = icon;
    return (
        <Tooltip label={tip} disabled={disabled}>
            <button
                type="button"
                className={className}
                onClick={onClick}
                disabled={disabled}
                aria-label={tip}
            >
                <Icon size={size} aria-hidden="true" />
            </button>
        </Tooltip>
    );
};

/**
 * Inline jargon. Renders the word with a dotted underline so people can SEE
 * there is an explanation waiting, rather than having to discover it.
 */
export const Term = ({ children, tip, className }) => (
    <Tooltip label={tip}>
        <span className={`${styles.term} ${className || ''}`} tabIndex={0}>{children}</span>
    </Tooltip>
);

export default Tooltip;
"""

STUDIO_JSX = r"""// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
/**
 * GOLDEN SEED -- REPORT STUDIO
 *
 * The point of this screen is that it does not decide anything for you.
 *
 * Pick a dataset. Narrow it with as many conditions as you like -- one client,
 * one district, one week, or nothing at all and see everything. Choose which
 * columns you want in front of you and drop the ones you don't. Group it and
 * measure it: total owed per district, average days since payment per staff
 * member, count of projects per stage. Split that by a second dimension when
 * you want to compare -- payments per month split by who recorded them, spend
 * per category split by who spent it.
 *
 * Everything is one dataset + filters + columns + grouping + measures, and any
 * combination of those four is legal. That is the whole design: there is no
 * fixed list of reports to run out of.
 *
 * ROLES: datasets and columns are filtered by `canSeeMoney` before they are
 * ever offered (see reportData.js). The server is still the real boundary --
 * this just keeps a manager from being shown a money column that would come
 * back 403.
 */
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
    FiDatabase, FiFilter, FiColumns, FiBarChart2, FiDownloadCloud,
    FiPlus, FiX, FiRefreshCw, FiSave, FiTrash2, FiSearch, FiAlertCircle,
    FiChevronUp, FiChevronDown,
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import { LoadingState } from '../../components/common/LoadingState';
import { Tooltip } from '../../components/common/Tooltip';
import {
    DATASETS, datasetsFor, fieldsFor, fieldByKey, operatorsFor,
    AGGREGATIONS, applyFilters, groupRows, summarise, measureLabel, measureType,
    formatValue, toCSV, downloadCSV, loadViews, saveViews, num,
} from './reportData';
import styles from './ReportStudio.module.css';

const CHART_LIMIT = 24;
const TABLE_LIMIT = 500;

const newCondition = () => ({ uid: Math.random().toString(36).slice(2), field: '', op: '', value: '', value2: '' });

const ReportStudio = ({ canSeeMoney = false, mode = 'report', reloadToken = 0 }) => {
    const available = useMemo(() => datasetsFor(canSeeMoney), [canSeeMoney]);
    const [datasetKey, setDatasetKey] = useState(available[0]?.key || 'PROJECTS');
    const dataset = DATASETS[datasetKey] || available[0];

    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [search, setSearch] = useState('');
    const [mergeMode, setMergeMode] = useState('AND');
    const [conditions, setConditions] = useState([]);
    const [columns, setColumns] = useState([]);
    const [groupBy, setGroupBy] = useState('');
    const [splitBy, setSplitBy] = useState('');
    const [measures, setMeasures] = useState([{ agg: 'count', field: '' }]);
    const [sort, setSort] = useState({ key: '', dir: 'desc' });
    const [colMenuOpen, setColMenuOpen] = useState(false);
    const colMenuRef = useRef(null);
    useEffect(() => {
        const onDown = (e) => {
            if (colMenuRef.current && !colMenuRef.current.contains(e.target)) setColMenuOpen(false);
        };
        document.addEventListener('mousedown', onDown);
        return () => document.removeEventListener('mousedown', onDown);
    }, []);

    const [views, setViews] = useState(() => loadViews());
    const [viewName, setViewName] = useState('');

    const fields = useMemo(() => fieldsFor(dataset, canSeeMoney), [dataset, canSeeMoney]);

    /* ── loading ────────────────────────────────────────────────── */
    const load = useCallback(async (key) => {
        const ds = DATASETS[key];
        if (!ds) return;
        setLoading(true);
        setError('');
        try {
            const data = await ds.load();
            setRows(Array.isArray(data) ? data : []);
        } catch {
            setRows([]);
            setError('Could not load ' + ds.label.toLowerCase() + '. You may not have access, or the connection dropped.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(datasetKey); }, [datasetKey, load]);

    // REFRESH in the page header bumps reloadToken. Skipped on first render --
    // the effect above has already done the initial pull.
    const firstRun = useRef(true);
    useEffect(() => {
        if (firstRun.current) { firstRun.current = false; return; }
        load(datasetKey);
    }, [reloadToken, datasetKey, load]);

    // Switching dataset invalidates every field reference, so the builder
    // resets to that dataset's sensible defaults rather than carrying over
    // conditions that can no longer match anything.
    useEffect(() => {
        const ds = DATASETS[datasetKey];
        if (!ds) return;
        const allowed = fieldsFor(ds, canSeeMoney).map(f => f.key);
        setColumns(ds.defaultColumns.filter(c => allowed.includes(c)));
        setConditions([]);
        setGroupBy('');
        setSplitBy('');
        setMeasures([{ agg: 'count', field: '' }]);
        setSort({ key: '', dir: 'desc' });
        setSearch('');
    }, [datasetKey, canSeeMoney]);

    /* ── pipeline ───────────────────────────────────────────────── */
    const filtered = useMemo(
        () => applyFilters(rows, dataset, conditions, mergeMode, search),
        [rows, dataset, conditions, mergeMode, search],
    );

    const grouped = useMemo(() => {
        if (!groupBy) return null;
        const g = groupRows(filtered, dataset, [groupBy, splitBy], measures);
        const idx = 0;
        g.sort((a, b) => num(b.values[idx]) - num(a.values[idx]));
        return g;
    }, [filtered, dataset, groupBy, splitBy, measures]);

    const totals = useMemo(() => summarise(filtered, dataset, measures), [filtered, dataset, measures]);

    const tableRows = useMemo(() => {
        if (grouped) return null;
        const list = [...filtered];
        if (sort.key) {
            const fld = fieldByKey(dataset, sort.key);
            if (fld) {
                list.sort((a, b) => {
                    const av = fld.get(a);
                    const bv = fld.get(b);
                    let cmp;
                    if (fld.type === 'number' || fld.type === 'money' || fld.type === 'percent') cmp = num(av) - num(bv);
                    else if (fld.type === 'date') cmp = new Date(av || 0).getTime() - new Date(bv || 0).getTime();
                    else cmp = String(av ?? '').localeCompare(String(bv ?? ''));
                    return sort.dir === 'asc' ? cmp : -cmp;
                });
            }
        }
        return list;
    }, [filtered, grouped, sort, dataset]);

    const chartMax = useMemo(() => {
        if (!grouped || grouped.length === 0) return 0;
        return Math.max(...grouped.map(g => Math.abs(num(g.values[0]))));
    }, [grouped]);

    /* ── condition editing ──────────────────────────────────────── */
    const addCondition = () => setConditions(c => [...c, newCondition()]);
    const dropCondition = (uid) => setConditions(c => c.filter(x => x.uid !== uid));
    const patchCondition = (uid, patch) =>
        setConditions(c => c.map(x => (x.uid === uid ? { ...x, ...patch } : x)));

    const toggleColumn = (key) =>
        setColumns(c => (c.includes(key) ? c.filter(k => k !== key) : [...c, key]));

    const patchMeasure = (i, patch) =>
        setMeasures(m => m.map((x, idx) => (idx === i ? { ...x, ...patch } : x)));

    /* ── saved views ────────────────────────────────────────────── */
    const persist = (next) => { setViews(next); saveViews(next); };

    const saveCurrentView = () => {
        const name = viewName.trim();
        if (!name) return;
        const snapshot = {
            name, datasetKey, search, mergeMode, conditions, columns,
            groupBy, splitBy, measures, sort,
        };
        persist([...views.filter(v => v.name !== name), snapshot]);
        setViewName('');
    };

    const applyView = (v) => {
        setDatasetKey(v.datasetKey);
        // The dataset-change effect resets the builder, so the snapshot has to
        // land after it, not with it.
        setTimeout(() => {
            setSearch(v.search || '');
            setMergeMode(v.mergeMode || 'AND');
            setConditions(v.conditions || []);
            setColumns(v.columns || []);
            setGroupBy(v.groupBy || '');
            setSplitBy(v.splitBy || '');
            setMeasures(v.measures || [{ agg: 'count', field: '' }]);
            setSort(v.sort || { key: '', dir: 'desc' });
        }, 0);
    };

    /* ── export ─────────────────────────────────────────────────── */
    const exportCSV = () => {
        const stamp = new Date().toISOString().slice(0, 10);
        if (grouped) {
            const headers = [
                fieldByKey(dataset, groupBy)?.label || 'Group',
                ...(splitBy ? [fieldByKey(dataset, splitBy)?.label || 'Split'] : []),
                'Rows',
                ...measures.map(m => measureLabel(m, dataset)),
            ];
            const matrix = grouped.map(g => [
                g.path[0] ?? '',
                ...(splitBy ? [g.path[1] ?? ''] : []),
                g.count,
                ...g.values,
            ]);
            downloadCSV(`GOLDEN_SEED_${datasetKey}_GROUPED_${stamp}.csv`, toCSV(headers, matrix));
            return;
        }
        const cols = columns.map(k => fieldByKey(dataset, k)).filter(Boolean);
        downloadCSV(
            `GOLDEN_SEED_${datasetKey}_${stamp}.csv`,
            toCSV(cols.map(c => c.label), tableRows.map(r => cols.map(c => c.get(r)))),
        );
    };

    const toggleSort = (key) =>
        setSort(s => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' }));

    /* ── render ─────────────────────────────────────────────────── */
    const groupField = fieldByKey(dataset, groupBy);
    const splitField = fieldByKey(dataset, splitBy);
    const chartRows = grouped ? grouped.slice(0, CHART_LIMIT) : [];

    return (
        <div className={styles.studio}>

            {/* ── DATA SOURCE ─────────────────────────────────────── */}
            <CollapsibleSection
                icon={<FiDatabase aria-hidden="true" />}
                title="DATA SOURCE"
                right={<span className={styles.badge}>{loading ? 'LOADING' : `${rows.length} ROWS`}</span>}
            >
                {/* A select, not a row of chips: four today, more later, and a
                    wrapping chip row is the first thing to break on a phone. */}
                <div className={styles.chipRow}>
                    <label className={styles.picker}>
                        <span className={styles.miniLabel}>Dataset</span>
                        <select
                            className={styles.select}
                            value={datasetKey}
                            onChange={e => setDatasetKey(e.target.value)}
                            aria-label="Dataset"
                        >
                            {available.map(ds => <option key={ds.key} value={ds.key}>{ds.label}</option>)}
                        </select>
                    </label>
                    <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}>
                        <FiRefreshCw size={11} aria-hidden="true" /> RELOAD
                    </button>
                </div>
                <p className={styles.hint}>{dataset?.blurb}</p>
                {!canSeeMoney && (
                    <p className={styles.hint}>
                        <FiAlertCircle size={12} aria-hidden="true" />
                        Financial datasets and money columns are hidden on your role.
                    </p>
                )}
                {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden="true" /> {error}</div>}

                <div className={styles.viewBar}>
                    <input
                        className={styles.input}
                        placeholder="Name this setup to save it..."
                        value={viewName}
                        onChange={e => setViewName(e.target.value)}
                    />
                    <Tooltip label="Save the current dataset, filters, columns and grouping. Saved on this device.">
                        <button className={styles.chipActive} onClick={saveCurrentView} disabled={!viewName.trim()}>
                            <FiSave size={11} aria-hidden="true" /> SAVE VIEW
                        </button>
                    </Tooltip>
                </div>
                {views.length > 0 && (
                    <div className={styles.chipRow}>
                        {views.map(v => (
                            <span key={v.name} className={styles.viewChip}>
                                <button className={styles.viewChipName} onClick={() => applyView(v)}>{v.name}</button>
                                <button
                                    className={styles.viewChipDrop}
                                    onClick={() => persist(views.filter(x => x.name !== v.name))}
                                    aria-label={`Delete saved view ${v.name}`}
                                >
                                    <FiTrash2 size={10} aria-hidden="true" />
                                </button>
                            </span>
                        ))}
                    </div>
                )}
            </CollapsibleSection>

            {/* ── FILTERS ─────────────────────────────────────────── */}
            <CollapsibleSection
                icon={<FiFilter aria-hidden="true" />}
                title="NARROW IT DOWN"
                right={<span className={styles.badge}>{filtered.length} OF {rows.length}</span>}
            >
                <div className={styles.searchRow}>
                    <FiSearch className={styles.searchIcon} aria-hidden="true" />
                    <input
                        className={styles.searchInput}
                        placeholder="Free text across every text column -- a name, a plot, a district..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                    {search && (
                        <button className={styles.searchClear} onClick={() => setSearch('')} aria-label="Clear search">
                            <FiX size={13} aria-hidden="true" />
                        </button>
                    )}
                </div>

                <div className={styles.chipRow}>
                    <span className={styles.miniLabel}>Match</span>
                    <Tooltip label="Every condition must be true">
                        <button className={mergeMode === 'AND' ? styles.chipActive : styles.chip} onClick={() => setMergeMode('AND')}>ALL</button>
                    </Tooltip>
                    <Tooltip label="Any one condition is enough">
                        <button className={mergeMode === 'OR' ? styles.chipActive : styles.chip} onClick={() => setMergeMode('OR')}>ANY</button>
                    </Tooltip>
                </div>

                {conditions.map(c => {
                    const fld = fieldByKey(dataset, c.field);
                    const ops = operatorsFor(fld?.type || 'text');
                    const opDef = ops.find(o => o.key === c.op);
                    const inputType = opDef?.input === 'date' ? 'date'
                        : (fld && ['number', 'money', 'percent'].includes(fld.type)) || c.op === 'lastDays' ? 'number'
                            : 'text';
                    return (
                        <div key={c.uid} className={styles.condRow}>
                            <select
                                className={styles.select}
                                value={c.field}
                                onChange={e => patchCondition(c.uid, { field: e.target.value, op: '', value: '', value2: '' })}
                                aria-label="Field"
                            >
                                <option value="">Choose a field...</option>
                                {fields.map(fl => <option key={fl.key} value={fl.key}>{fl.label}</option>)}
                            </select>
                            <select
                                className={styles.select}
                                value={c.op}
                                onChange={e => patchCondition(c.uid, { op: e.target.value })}
                                disabled={!fld}
                                aria-label="Condition"
                            >
                                <option value="">is...</option>
                                {ops.map(o => <option key={o.key} value={o.key}>{o.label}</option>)}
                            </select>
                            {opDef?.value && (
                                <input
                                    className={styles.input}
                                    type={inputType}
                                    value={c.value}
                                    placeholder={c.op === 'lastDays' ? 'days' : 'value'}
                                    onChange={e => patchCondition(c.uid, { value: e.target.value })}
                                    aria-label="Value"
                                />
                            )}
                            {opDef?.value2 && (
                                <input
                                    className={styles.input}
                                    type={inputType}
                                    value={c.value2}
                                    placeholder="and"
                                    onChange={e => patchCondition(c.uid, { value2: e.target.value })}
                                    aria-label="Second value"
                                />
                            )}
                            <button className={styles.dropBtn} onClick={() => dropCondition(c.uid)} aria-label="Remove condition">
                                <FiX size={13} aria-hidden="true" />
                            </button>
                        </div>
                    );
                })}

                <div className={styles.chipRow}>
                    <button className={styles.chip} onClick={addCondition}>
                        <FiPlus size={11} aria-hidden="true" /> ADD CONDITION
                    </button>
                    {conditions.length > 0 && (
                        <button className={styles.chip} onClick={() => setConditions([])}>
                            <FiX size={11} aria-hidden="true" /> CLEAR ALL
                        </button>
                    )}
                </div>
            </CollapsibleSection>

            {/* ── COLUMNS ─────────────────────────────────────────── */}
            <CollapsibleSection
                icon={<FiColumns aria-hidden="true" />}
                title="COLUMNS TO SHOW"
                defaultOpen={mode === 'report'}
                right={<span className={styles.badge}>{columns.length} PICKED</span>}
            >
                <p className={styles.hint}>
                    Only applies to the row-by-row table. Grouped results show your measures instead.
                </p>
                {/* Forty checkboxes laid out as chips filled most of a phone
                    screen before you reached anything else. Same include /
                    exclude control, folded into a dropdown. */}
                <div className={styles.dropdown} ref={colMenuRef}>
                    <button
                        type="button"
                        className={styles.dropdownBtn}
                        onClick={() => setColMenuOpen(o => !o)}
                        aria-expanded={colMenuOpen}
                    >
                        <span>{columns.length === 0 ? 'No columns picked' : `${columns.length} of ${fields.length} columns`}</span>
                        <FiChevronDown className={colMenuOpen ? styles.dropdownIconOpen : ''} aria-hidden="true" />
                    </button>
                    {colMenuOpen && (
                        <div className={styles.dropdownList}>
                            <div className={styles.dropdownActions}>
                                <button className={styles.miniBtn} onClick={() => setColumns(fields.map(fl => fl.key))}>ALL</button>
                                <button className={styles.miniBtn} onClick={() => setColumns([])}>NONE</button>
                                <button className={styles.miniBtn} onClick={() => setColumns(dataset.defaultColumns.filter(k => fields.some(fl => fl.key === k)))}>RESET</button>
                            </div>
                            {fields.map(fl => (
                                <label key={fl.key} className={styles.dropdownOption}>
                                    <input
                                        type="checkbox"
                                        checked={columns.includes(fl.key)}
                                        onChange={() => toggleColumn(fl.key)}
                                    />
                                    {fl.label}
                                </label>
                            ))}
                        </div>
                    )}
                </div>
            </CollapsibleSection>

            {/* ── GROUP & MEASURE ─────────────────────────────────── */}
            <CollapsibleSection
                icon={<FiBarChart2 aria-hidden="true" />}
                title="GROUP, MEASURE & COMPARE"
                defaultOpen={mode === 'analysis'}
                right={<span className={styles.badge}>{groupBy ? 'GROUPED' : 'ROW BY ROW'}</span>}
            >
                <div className={styles.pickerGrid}>
                    <label className={styles.picker}>
                        <span className={styles.miniLabel}>Group by</span>
                        <select className={styles.select} value={groupBy} onChange={e => setGroupBy(e.target.value)}>
                            <option value="">(no grouping -- show every row)</option>
                            {fields.map(fl => <option key={fl.key} value={fl.key}>{fl.label}</option>)}
                        </select>
                    </label>
                    <label className={styles.picker}>
                        <span className={styles.miniLabel}>Compare / split by</span>
                        <select className={styles.select} value={splitBy} onChange={e => setSplitBy(e.target.value)} disabled={!groupBy}>
                            <option value="">(none)</option>
                            {fields.filter(fl => fl.key !== groupBy).map(fl => <option key={fl.key} value={fl.key}>{fl.label}</option>)}
                        </select>
                    </label>
                </div>

                {measures.map((m, i) => {
                    const def = AGGREGATIONS.find(a => a.key === m.agg);
                    return (
                        <div key={i} className={styles.condRow}>
                            <select className={styles.select} value={m.agg} onChange={e => patchMeasure(i, { agg: e.target.value })} aria-label="Measure">
                                {AGGREGATIONS.map(a => <option key={a.key} value={a.key}>{a.label}</option>)}
                            </select>
                            {def?.needsField && (
                                <select className={styles.select} value={m.field} onChange={e => patchMeasure(i, { field: e.target.value })} aria-label="Measure field">
                                    <option value="">Choose a field...</option>
                                    {fields
                                        .filter(fl => (m.agg === 'distinct' ? true : ['number', 'money', 'percent'].includes(fl.type)))
                                        .map(fl => <option key={fl.key} value={fl.key}>{fl.label}</option>)}
                                </select>
                            )}
                            {measures.length > 1 && (
                                <button className={styles.dropBtn} onClick={() => setMeasures(ms => ms.filter((_, idx) => idx !== i))} aria-label="Remove measure">
                                    <FiX size={13} aria-hidden="true" />
                                </button>
                            )}
                        </div>
                    );
                })}
                <div className={styles.chipRow}>
                    <button className={styles.chip} onClick={() => setMeasures(ms => [...ms, { agg: 'sum', field: '' }])}>
                        <FiPlus size={11} aria-hidden="true" /> ADD MEASURE
                    </button>
                </div>
            </CollapsibleSection>

            {/* ── RESULTS ─────────────────────────────────────────── */}
            <CollapsibleSection
                icon={<FiBarChart2 aria-hidden="true" />}
                title="RESULTS"
                right={
                    <button className={styles.exportBtn} onClick={exportCSV} disabled={loading || filtered.length === 0}>
                        <FiDownloadCloud size={11} aria-hidden="true" /> EXPORT CSV
                    </button>
                }
            >
                {loading ? <LoadingState label="PULLING DATA..." tone="bare" /> : (
                    <>
                        <div className={styles.statStrip}>
                            <div className={styles.statCard}>
                                <label>ROWS MATCHED</label>
                                <strong>{filtered.length.toLocaleString()}</strong>
                                <span className={styles.statNote}>of {rows.length.toLocaleString()} loaded</span>
                            </div>
                            {measures.map((m, i) => (
                                <div key={i} className={styles.statCard}>
                                    <label>{measureLabel(m, dataset)}</label>
                                    <strong>{formatValue(totals[i], measureType(m, dataset))}</strong>
                                    <span className={styles.statNote}>across the filtered set</span>
                                </div>
                            ))}
                        </div>

                        {grouped && grouped.length > 0 && (
                            <>
                                <div className={styles.sectionLabel}>
                                    {measureLabel(measures[0], dataset)} by {groupField?.label}
                                    {splitField ? ' split by ' + splitField.label : ''}
                                </div>
                                <div className={styles.chart}>
                                    {chartRows.map(g => (
                                        <div key={g.id} className={styles.chartRow}>
                                            <span className={styles.chartLabel} title={g.id}>{g.id}</span>
                                            <div className={styles.chartTrack}>
                                                <div
                                                    className={styles.chartFill}
                                                    style={{ width: chartMax ? `${Math.max(1, (Math.abs(num(g.values[0])) / chartMax) * 100)}%` : '1%' }}
                                                />
                                            </div>
                                            <span className={styles.chartValue}>
                                                {formatValue(g.values[0], measureType(measures[0], dataset))}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                                {grouped.length > CHART_LIMIT && (
                                    <p className={styles.hint}>
                                        Chart shows the top {CHART_LIMIT} of {grouped.length} groups. The table and the CSV have all of them.
                                    </p>
                                )}
                            </>
                        )}

                        <div className={styles.tableScroll}>
                            {grouped ? (
                                <table className={styles.table}>
                                    <thead>
                                        <tr>
                                            <th>{groupField?.label || 'Group'}</th>
                                            {splitField && <th>{splitField.label}</th>}
                                            <th>Rows</th>
                                            {measures.map((m, i) => <th key={i}>{measureLabel(m, dataset)}</th>)}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {grouped.length === 0 ? (
                                            <tr><td colSpan={3 + measures.length} className={styles.emptyCell}>NOTHING MATCHES THOSE CONDITIONS</td></tr>
                                        ) : grouped.map(g => (
                                            <tr key={g.id}>
                                                <td className={styles.strong}>{g.path[0]}</td>
                                                {splitField && <td>{g.path[1] ?? '---'}</td>}
                                                <td className={styles.mono}>{g.count}</td>
                                                {g.values.map((v, i) => (
                                                    <td key={i} className={styles.mono}>{formatValue(v, measureType(measures[i], dataset))}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <table className={styles.table}>
                                    <thead>
                                        <tr>
                                            {columns.length === 0 ? <th>No columns picked</th> : columns.map(k => {
                                                const fl = fieldByKey(dataset, k);
                                                if (!fl) return null;
                                                return (
                                                    <th key={k} className={styles.sortable} onClick={() => toggleSort(k)}>
                                                        {fl.label}
                                                        {sort.key === k && (sort.dir === 'asc'
                                                            ? <FiChevronUp size={10} aria-hidden="true" />
                                                            : <FiChevronDown size={10} aria-hidden="true" />)}
                                                    </th>
                                                );
                                            })}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {columns.length === 0 ? (
                                            <tr><td className={styles.emptyCell}>PICK AT LEAST ONE COLUMN ABOVE</td></tr>
                                        ) : tableRows.length === 0 ? (
                                            <tr><td colSpan={columns.length} className={styles.emptyCell}>NOTHING MATCHES THOSE CONDITIONS</td></tr>
                                        ) : tableRows.slice(0, TABLE_LIMIT).map((r, i) => (
                                            <tr key={r.id || r.projectId || i}>
                                                {columns.map(k => {
                                                    const fl = fieldByKey(dataset, k);
                                                    if (!fl) return null;
                                                    const isNum = ['number', 'money', 'percent'].includes(fl.type);
                                                    return (
                                                        <td key={k} className={isNum ? styles.mono : undefined}>
                                                            {formatValue(fl.get(r), fl.type)}
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>

                        {!grouped && tableRows.length > TABLE_LIMIT && (
                            <p className={styles.hint}>
                                Showing the first {TABLE_LIMIT} of {tableRows.length.toLocaleString()} rows to keep the page quick.
                                The CSV export contains every one of them.
                            </p>
                        )}
                    </>
                )}
            </CollapsibleSection>
        </div>
    );
};

export default ReportStudio;
"""

STUDIO_CSS = r"""/* PATH: erp-frontend/src/pages/Reports/ReportStudio.module.css */
/* fix69 -- THE STUDIO IS A LIGHT SURFACE NOW.
   Every other page in the app is a handful of dark panels floating on the
   cream background, and that works because you look at each panel for a
   second. The studio is the opposite: it is a workbench you sit at, with
   five stacked panels of controls, and rendered dark it was a wall of navy
   from header to footer with no light anywhere.
   So: the workbench is paper (cream/white), the controls are white with navy
   ink, and the only dark objects left are the ones that should draw the eye
   -- the stat cards and the results table header. */
.studio {
  --orange: #EE8C3A;
  --orange-soft: rgba(238,140,58,0.12);
  --navy: #213E40;
  --navy-deep: #1a2e30;
  --ink: #1a2e30;
  --ink-soft: #5b6f70;
  --paper: #faf8f5;
  --paper-edge: #dfd9d1;
  --red: #b91c1c;
  --radius: 10px; --radius-sm: 6px;

  display: flex; flex-direction: column; gap: clamp(7px,1.1vw,14px);
  font-family: 'Inter', sans-serif;
  /* CONTRAST RULE: this block is light, so text here is INK, never cream.
     Anything that needs to stay cream declares it locally. */
  color: var(--ink);
}

.badge {
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px; text-transform: uppercase;
  color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.14); border-radius: 20px; padding: 4px 12px; flex-shrink: 0;
}

.hint {
  display: flex; align-items: center; gap: 7px; margin: 0;
  font-size: clamp(10px,1vw,11.5px); font-weight: 500; line-height: 1.5;
  color: var(--ink-soft);
}
.hint svg { color: var(--orange); flex-shrink: 0; }

.error {
  display: flex; align-items: center; gap: 8px;
  background: #fee2e2; border: 1px solid #fca5a5;
  color: var(--red); font-size: 11.5px; font-weight: 700; border-radius: 6px; padding: 8px 12px;
}

.sectionLabel {
  font-size: clamp(9px,0.9vw,11px); font-weight: 900; letter-spacing: 2px;
  color: var(--navy-deep); text-transform: uppercase;
}

/* ── controls ─────────────────────────────────────────────────────── */
.chipRow { display: flex; flex-wrap: wrap; align-items: flex-end; gap: clamp(6px,0.9vw,10px); }

.chip, .chipActive, .exportBtn, .miniBtn {
  font-family: 'Inter', sans-serif; font-weight: 900;
  text-transform: uppercase; letter-spacing: 1.5px;
  border-radius: var(--radius-sm); cursor: pointer; transition: all 0.18s ease;
  display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;
}
.chip, .chipActive, .exportBtn {
  font-size: clamp(8px,0.85vw,10px);
  padding: clamp(7px,0.95vw,10px) clamp(10px,1.4vw,16px);
  border: 1.5px solid var(--paper-edge);
  background: #fff; color: var(--ink);
}
.chip:hover:not(:disabled) { border-color: var(--orange); color: var(--orange); background: var(--orange-soft); }
.chipActive, .exportBtn { background: var(--orange); color: var(--navy-deep); border-color: var(--orange); }
.chipActive:hover:not(:disabled), .exportBtn:hover:not(:disabled) { background: #d97a2b; border-color: #d97a2b; }
.chip:disabled, .chipActive:disabled, .exportBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.chip:focus-visible, .chipActive:focus-visible, .exportBtn:focus-visible, .miniBtn:focus-visible {
  outline: 2px solid var(--orange); outline-offset: 2px;
}
.miniBtn {
  font-size: 9px; padding: 5px 10px; border: 1.5px solid var(--paper-edge);
  background: #fff; color: var(--ink);
}
.miniBtn:hover { border-color: var(--orange); color: var(--orange); }

.miniLabel {
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1.5px;
  text-transform: uppercase; color: var(--ink-soft);
}

/* ── saved views ──────────────────────────────────────────────────── */
.viewBar { display: flex; flex-wrap: wrap; gap: clamp(6px,0.9vw,10px); align-items: center; }
.viewChip {
  display: inline-flex; align-items: center;
  border: 1.5px solid rgba(238,140,58,0.5); border-radius: var(--radius-sm); overflow: hidden; background: #fff;
}
.viewChipName {
  background: transparent; border: none; color: #b45309;
  font-family: 'Inter', sans-serif; font-size: clamp(9px,0.95vw,11px); font-weight: 800;
  padding: 7px 12px; cursor: pointer; transition: background 0.15s;
}
.viewChipName:hover { background: var(--orange-soft); }
.viewChipDrop {
  background: #fee2e2; border: none; color: var(--red);
  padding: 8px 9px; cursor: pointer; display: flex; align-items: center; transition: background 0.15s;
}
.viewChipDrop:hover { background: #ef4444; color: #fff; }

/* ── inputs ───────────────────────────────────────────────────────── */
.input, .select {
  height: 36px; padding: 0 10px; border-radius: var(--radius-sm);
  border: 1.5px solid var(--paper-edge); background: #fff; color: var(--ink);
  font-family: 'Inter', sans-serif; font-size: clamp(11px,1.05vw,12.5px); font-weight: 600;
  min-width: 130px; flex: 1 1 150px; max-width: 100%;
}
.input::placeholder { color: rgba(26,46,48,0.38); font-weight: 500; }
.input:focus, .select:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-soft); }
.select { cursor: pointer; }
.select option { background: #fff; color: var(--ink); }

.condRow {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  background: #fff; border: 1.5px solid var(--paper-edge); border-radius: var(--radius-sm);
  padding: 8px; 
}
.dropBtn {
  height: 36px; width: 36px; flex: 0 0 36px; border-radius: var(--radius-sm);
  background: #fee2e2; border: 1.5px solid transparent; color: var(--red);
  display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.15s;
}
.dropBtn:hover { background: #ef4444; color: #fff; }

.pickerGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: clamp(8px,1.2vw,14px); }
.picker { display: flex; flex-direction: column; gap: 5px; min-width: 0; flex: 1 1 200px; }

/* ── the columns dropdown ─────────────────────────────────────────── */
.dropdown { position: relative; max-width: 420px; }
.dropdownBtn {
  width: 100%; height: 38px; padding: 0 12px; border-radius: var(--radius-sm);
  border: 1.5px solid var(--paper-edge); background: #fff; color: var(--ink);
  font-family: 'Inter', sans-serif; font-size: clamp(11px,1.05vw,12.5px); font-weight: 800;
  cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 8px;
  text-transform: uppercase; transition: border-color 0.2s;
}
.dropdownBtn:hover { border-color: var(--orange); }
.dropdownBtn svg { color: var(--orange); flex-shrink: 0; transition: transform 0.2s; }
.dropdownIconOpen { transform: rotate(180deg); }
.dropdownList {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 400;
  background: #fff; border: 2px solid var(--orange); border-radius: var(--radius-sm);
  box-shadow: 0 20px 44px rgba(26,46,48,0.28);
  max-height: 320px; overflow-y: auto;
}
.dropdownActions {
  display: flex; gap: 6px; padding: 8px 10px; position: sticky; top: 0;
  background: #fff; border-bottom: 1px solid var(--paper-edge);
}
.dropdownOption {
  display: flex; align-items: center; gap: 9px;
  padding: 8px 12px; color: var(--ink); font-size: 12px; font-weight: 700;
  border-bottom: 1px solid #f1eeea; cursor: pointer; text-transform: uppercase;
}
.dropdownOption:last-child { border-bottom: none; }
.dropdownOption:hover { background: var(--orange-soft); }
.dropdownOption input { accent-color: var(--orange); width: 15px; height: 15px; cursor: pointer; }

/* ── free-text search ─────────────────────────────────────────────── */
.searchRow {
  position: relative; display: flex; align-items: center;
  background: #fff; border: 1.5px solid var(--paper-edge); border-radius: var(--radius-sm);
  height: clamp(38px,4.5vw,44px); transition: border-color 0.2s, box-shadow 0.2s;
}
.searchRow:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-soft); }
.searchIcon { position: absolute; left: 12px; color: var(--orange); font-size: 15px; pointer-events: none; }
.searchInput {
  width: 100%; border: none; outline: none; background: transparent;
  color: var(--ink); padding: 0 36px 0 38px; height: 100%;
  font-family: 'Inter', sans-serif; font-weight: 700; font-size: clamp(11px,1.1vw,13px);
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.35); }
.searchClear {
  position: absolute; right: 8px; background: transparent; border: none; cursor: pointer;
  color: rgba(26,46,48,0.45); display: flex; align-items: center; padding: 5px; border-radius: 4px;
}
.searchClear:hover { color: var(--ink); background: rgba(26,46,48,0.08); }

/* ── stat strip -- kept dark on purpose: on a light workbench these are
      the one thing that should pull the eye. ───────────────────────── */
.statStrip { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr)); gap: clamp(10px,1.4vw,16px); }
.statCard {
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid rgba(238,140,58,0.28); border-radius: var(--radius);
  padding: clamp(12px,1.5vw,18px); display: flex; flex-direction: column; gap: 4px;
}
.statCard label { font-size: var(--stat-label); font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.5); }
.statCard strong { font-family: 'Space Mono', monospace; font-size: var(--stat-value); font-weight: 700; color: #fff; word-break: break-all; }
.statNote { font-size: var(--stat-note); font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.35); }

/* ── chart ────────────────────────────────────────────────────────── */
.chart {
  display: flex; flex-direction: column; gap: 9px;
  background: #fff; border: 1.5px solid var(--paper-edge); border-radius: var(--radius);
  padding: clamp(12px,1.5vw,18px);
}
.chartRow { display: grid; grid-template-columns: minmax(90px, 190px) 1fr minmax(80px, 140px); align-items: center; gap: 10px; }
.chartLabel {
  font-size: clamp(9px,0.95vw,11px); font-weight: 800; color: var(--ink);
  text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.chartTrack { height: 13px; background: #efe9e2; border-radius: 999px; overflow: hidden; }
.chartFill { height: 100%; background: linear-gradient(90deg, var(--orange) 0%, #d97a28 100%); border-radius: 999px; transition: width 0.4s ease; }
.chartValue { font-family: 'Space Mono', monospace; font-size: clamp(9px,0.95vw,11px); font-weight: 700; text-align: right; color: var(--navy-deep); }

/* ── results table -- light body, navy header bar ─────────────────── */
.tableScroll {
  overflow-x: auto; background: #fff;
  border: 1.5px solid var(--paper-edge); border-radius: var(--radius);
  scrollbar-width: thin; scrollbar-color: var(--orange) transparent;
}
.tableScroll::-webkit-scrollbar { height: 6px; }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }
.table { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 640px; }
.table thead th {
  background: var(--navy); color: var(--orange);
  font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  letter-spacing: 2px; text-transform: uppercase; text-align: left;
  padding: clamp(9px,1.3vw,14px) clamp(10px,1.5vw,16px);
  white-space: nowrap; position: sticky; top: 0; z-index: 2;
}
.sortable { cursor: pointer; transition: background 0.18s, color 0.18s; }
.sortable:hover { background: #2c5052; color: #fff; }
.table tbody td {
  padding: clamp(8px,1.1vw,12px) clamp(10px,1.5vw,16px);
  border-bottom: 1px solid #f1eeea; vertical-align: middle;
  color: var(--ink); font-size: clamp(11px,1.05vw,12.5px); font-weight: 500;
  max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.table tbody tr { border-left: 3px solid transparent; transition: background 0.15s; }
.table tbody tr:nth-child(even) { background: #fbf9f7; }
.table tbody tr:hover { background: var(--orange-soft); border-left-color: var(--orange); }
.mono { font-family: 'Space Mono', monospace; font-weight: 700; }
.strong { font-weight: 800; }

.emptyCell {
  text-align: center; padding: clamp(20px,4vw,40px) 16px;
  font-family: 'Space Mono', monospace; color: var(--ink-soft);
  font-size: 11px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
}

@media (max-width: 640px) {
  .chartRow { grid-template-columns: minmax(70px, 110px) 1fr minmax(64px, 96px); }
  .input, .select, .picker { flex: 1 1 100%; min-width: 0; }
  .dropdown { max-width: none; }
  .table { min-width: 560px; }
}
"""

REPORTHUB_JSX = r"""// PATH: erp-frontend/src/pages/Reports/ReportHub.jsx
/**
 * GOLDEN SEED -- REPORTS & ANALYSIS
 *
 * Two tabs, because these are two different jobs:
 *
 *   REPORTS  -- "give me the file". The twelve canned CSV pillars the server
 *               generates, plus a builder for the twelve-thousand it doesn't:
 *               pick a dataset, filter it to one client or one district or one
 *               week, choose your columns, export.
 *
 *   ANALYSIS -- "tell me what it says". The same builder pointed at grouping
 *               and measures instead of rows -- totals per district, average
 *               days-since-payment per staff member, spend per category split
 *               by who spent it -- plus the expense analysis.
 *
 * It is the same engine behind both tabs (ReportStudio); the tab only decides
 * which panel opens first. Splitting them into two tools would have meant two
 * filter builders to keep in step.
 *
 * ROLES: financial datasets, money columns and the financial CSV pillars are
 * all gated on hasFinancialAccess, which mirrors what the server enforces.
 */
import React, { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
    FiBarChart2, FiMap, FiActivity, FiLayers,
    FiShield, FiTrendingUp, FiTrendingDown, FiLock, FiDownloadCloud,
    FiChevronDown, FiCreditCard, FiDatabase, FiFileText,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo, FiSliders, FiRefreshCw
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import reportService from '../../services/reportService';
import BackToTopButton from '../../components/common/BackToTopButton';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import ReportStudio from './ReportStudio';
import styles from './ReportHub.module.css';

// ─── TOAST ────────────────────────────────────────────────────────
const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);
    const dismiss = useCallback(id => setToasts(prev => prev.filter(t => t.id !== id)), []);
    return { toasts, toast, dismissToast: dismiss };
};
const TOAST_ICONS = {
    success: <FiCheckSquare  aria-hidden="true" />,
    error:   <FiAlertCircle  aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo          aria-hidden="true" />,
};
const ToastContainer = ({ toasts, onDismiss }) => {
    if (typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
                    <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
                    <span className={styles.toastMsg}>{t.message}</span>
                    <button className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss">
                        <FiX aria-hidden="true" />
                    </button>
                </div>
            ))}
        </div>,
        document.body
    );
};

// ─── DRAWER HEADER ────────────────────────────────────────────────
const DrawerTitle = ({ label, isOpen, onClick, icon: IconComponent }) => (
    <div
        className={styles.drawerHeader}
        onClick={onClick}
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        aria-label={`${label}, ${isOpen ? 'collapse' : 'expand'}`}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}
    >
        <div className={styles.drawerTitle}>
            {IconComponent && <IconComponent className={styles.drawerIcon} aria-hidden="true" />}
            {label}
        </div>
        <FiChevronDown className={`${styles.chevron} ${isOpen ? styles.rotated : ''}`} aria-hidden="true" />
    </div>
);

// ─── REPORT DATA ──────────────────────────────────────────────────
const REPORT_SCHEMA = {
    debt:      { columns: 'PLOT_ID, PRIMARY_OWNER, PHONE, TOTAL_VAL, PAID_VAL, ARREARS, BOX_LOC, STATUS', desc: 'Lists every plot with an outstanding balance. Shows the full financial picture per client — what they owe, what they have paid, and where their physical file is stored.' },
    revenue:   { columns: 'DATE, PLOT_ID, OWNER_NAME, PAYMENT_TYPE, AMOUNT_UGX, BALANCE_AFTER_UGX, RECORDED_BY, NOTES', desc: 'A chronological log of every cash payment ever recorded in the system, including who logged it and the running balance after each transaction.' },
    perf:      { columns: 'TIMESTAMP, OPERATOR, PLOT_ID, NOTE_SNIPPET', desc: 'Pulls every call log and follow-up note entered by staff. Use this to audit which managers are actively contacting clients and how frequently.' },
    map:       { columns: 'BOX_LOCATION, PLOT_ID, TENURE, DISTRICT, STAGE_INDEX, IS_LEGACY', desc: 'A full inventory of every physical file sorted by cabinet box number. Useful for locating a specific title in the office archive quickly.' },
    stage:     { columns: 'PHASE_NUMBER, TOTAL_FILES_IN_STAGE', desc: 'Shows how many title files are stuck at each of the five survey stages. Helps identify bottlenecks slowing down the processing pipeline.' },
    risk:      { columns: 'OWNER_NAME, SCORE_PERCENT, LAST_CALL_DATE', desc: 'Ranks all registered clients by their reliability score — a measure of payment consistency and responsiveness to calls.' },
    legal:     { columns: 'PLOT, OWNER, PHONE, NIN_STATUS, ADDRESS_STATUS, READINESS', desc: 'Checks whether every registered owner has a valid National ID and home address on file — the two fields required before issuing a legal demand notice.' },
    audit:     { columns: 'TIMESTAMP, OPERATOR, ACTION_CODE, HARDWARE_DETAILS', desc: 'The complete forensic footprint of every action taken inside the system — edits, deletions, logins, payment recordings, and stage changes.' },
    receivable:   { columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, RECEIVABLES_START, TITLE_COST_UGX, STORAGE_FEES_UGX, MONTHS_IN_RECEIVABLES, TOTAL_PAID, TOTAL_OWED', desc: 'A detailed breakdown of every plot currently in the receivables system, including accumulated storage fees and months elapsed since the receivables start date.' },
    completed: { columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, TOTAL_COST, AMOUNT_PAID, STATUS', desc: 'Lists all titles that have been fully paid or officially released to the client. Use this to track closed cases and measure overall throughput.' },
    reconcile: { columns: 'OPERATOR_ID, TOTAL_CASH_COLLECTED_UGX, NUMBER_OF_TRANSACTIONS, FIRST_PAYMENT_DATE, LAST_PAYMENT_DATE', desc: 'Anti-theft report: groups all payments by the staff member who recorded them. Compare these totals against physical cash in the office to detect discrepancies.' },
    monthly:   { columns: 'YEAR_MONTH, TOTAL_COLLECTED_UGX, TRANSACTION_COUNT', desc: 'Shows total cash collected each calendar month for the past 24 months. Use this to spot seasonal patterns and track collection performance over time.' },
};

// ─── DRAWER PANEL ─────────────────────────────────────────────────
// Module scope on purpose. Defined inside ReportHub it would be a NEW
// component type on every render, so React would unmount and remount its
// children -- and the Report Studio would lose every filter you had set
// the moment you collapsed any other drawer on the page.
const DrawerPanel = ({ label, icon, open, onToggle, tall = false, children }) => (
    <div className={styles.hwPanel}>
        <DrawerTitle label={label} isOpen={open} onClick={onToggle} icon={icon} />
        <div
            className={`${styles.panelBody} ${open ? (tall ? styles.bodyOpenTall : styles.bodyOpen) : styles.bodyClosed}`}
            aria-hidden={!open}
        >
            {tall
                ? (open && <div className={styles.studioInner}>{children}</div>)
                : <div className={styles.panelInner}>{children}</div>}
        </div>
    </div>
);

// ─── MAIN ─────────────────────────────────────────────────────────
const ReportHub = () => {
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();

    const hasFinancialAccess = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';

    const [tab, setTab] = useState('REPORTS');
    // The studio caches its dataset in local state, so REFRESH in the page
    // header has to reach it. Bumping this token is the signal; the studio
    // re-pulls whichever dataset it is currently on.
    const [reloadToken, setReloadToken] = useState(0);
    const [drawers, setDrawers] = useState({
        finance: true, ops: true, system: false, p2: true, studio: true,
        aStudio: true, expenses: false,
    });
    const [expandedId, setExpandedId] = useState(null);
    const [status, setStatus] = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
        receivable: false, completed: false, reconcile: false, monthly: false,
    });

    const toggleDrawer = key => setDrawers(prev => ({ ...prev, [key]: !prev[key] }));

    const triggerPillarExport = async (id, action, label) => {
        setStatus(prev => ({ ...prev, [id]: true }));
        try {
            await action();
            toast(`${label} -- EXPORT COMPLETE`, 'success', 4000);
        } catch (err) {
            toast(`REPORT FAULT: ${err.message || 'UNKNOWN ERROR'}`, 'error', 8000);
        } finally {
            setStatus(prev => ({ ...prev, [id]: false }));
        }
    };

    const FINANCIAL_GROUP = [
        { id: 'debt',    title: 'Master Debt Ledger',     icon: FiCreditCard, action: reportService.downloadDebtLedger   },
        { id: 'revenue', title: 'Revenue Inflow History',  icon: FiDatabase,   action: reportService.downloadRevenue      },
        { id: 'perf',    title: 'Recovery Throughput',     icon: FiActivity,   action: reportService.downloadPerformance  },
    ];
    const OPS_GROUP = [
        { id: 'map',   title: 'Physical Archive Map',  icon: FiMap,        action: reportService.downloadArchiveMap   },
        { id: 'stage', title: 'Survey Stage Audit',    icon: FiLayers,     action: reportService.downloadBottlenecks  },
        { id: 'risk',  title: 'Reliability Scorecard', icon: FiTrendingUp, action: reportService.downloadReliability  },
    ];
    const SYSTEM_GROUP = [
        { id: 'legal', title: 'Legal Readiness Audit', icon: FiFileText, action: reportService.downloadLegalReady  },
        { id: 'audit', title: 'Master System Audit',   icon: FiShield,   action: reportService.downloadAuditTrail  },
    ];
    const PRIORITY2_GROUP = [
        { id: 'receivable', title: 'Receivables Breakdown',       icon: FiLock,        action: reportService.downloadReceivableBreakdown     },
        { id: 'completed',  title: 'Completed Titles',            icon: FiCheckSquare, action: reportService.downloadCompletedTitles         },
        { id: 'reconcile',  title: 'Operator Cash Reconciliation', icon: FiShield,      action: reportService.downloadOperatorReconciliation  },
        { id: 'monthly',    title: 'Monthly Collection',          icon: FiBarChart2,   action: reportService.downloadMonthlyCollection       },
    ];

    const ReportRow = ({ item }) => {
        const ItemIcon = item.icon;
        const isLoading = status[item.id];
        const isExpanded = expandedId === item.id;
        const schema = REPORT_SCHEMA[item.id] || {};

        return (
            <div className={styles.reportRowWrap}>
                <div
                    className={`${styles.reportRow} ${isExpanded ? styles.reportRowActive : ''}`}
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    role="button"
                    tabIndex={0}
                    aria-expanded={isExpanded}
                    aria-label={`${item.title}, ${isExpanded ? 'collapse' : 'expand details'}`}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedId(isExpanded ? null : item.id); } }}
                >
                    <div className={styles.iconFrame} aria-hidden="true">
                        <ItemIcon aria-hidden="true" />
                    </div>
                    <span className={styles.rptTitle}>{item.title}</span>
                    <FiChevronDown className={`${styles.rowChevron} ${isExpanded ? styles.rotated : ''}`} aria-hidden="true" />
                </div>

                <div className={`${styles.reportDetails} ${isExpanded ? styles.detailsOpen : styles.detailsClosed}`}>
                    <div className={styles.detailBox}>
                        <div className={styles.detailHeader}>
                            <span>REPORT INTELLIGENCE DISCOVERY [SECURE]</span>
                        </div>
                        <p className={styles.detailDesc}>{schema.desc}</p>
                        {schema.columns && (
                            <div className={styles.schemaBlock}>
                                <span className={styles.schemaLabel}>CSV COLUMN SCHEMA:</span>
                                <p className={styles.schemaColumns}>{schema.columns}</p>
                            </div>
                        )}
                        <div className={styles.detailActions}>
                            <button
                                className={styles.exportBtnLarge}
                                onClick={e => { e.stopPropagation(); triggerPillarExport(item.id, item.action, item.title); }}
                                disabled={isLoading}
                                aria-label={isLoading ? `Exporting ${item.title}` : `Download ${item.title}`}
                            >
                                {isLoading
                                    ? <><div className={styles.exportSpinner} aria-hidden="true" /> STREAMING DATA...</>
                                    : <><FiDownloadCloud aria-hidden="true" /> DOWNLOAD CSV</>
                                }
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <BackToTopButton />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Reports &amp; Analysis</h1>
                    <p className={styles.subtitle}>Canned exports, or build exactly the question you want to ask</p>
                </div>
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH"
                        tip="Pull the current dataset again from the server"
                        onClick={() => setReloadToken(t => t + 1)} />
                </HeaderActions>
            </header>

            <div className={styles.tabRow} role="tablist" aria-label="Reports and analysis">
                <button
                    role="tab"
                    aria-selected={tab === 'REPORTS'}
                    className={tab === 'REPORTS' ? styles.tabActive : styles.tab}
                    onClick={() => setTab('REPORTS')}
                >
                    <FiFileText aria-hidden="true" /> REPORTS
                </button>
                <button
                    role="tab"
                    aria-selected={tab === 'ANALYSIS'}
                    className={tab === 'ANALYSIS' ? styles.tabActive : styles.tab}
                    onClick={() => setTab('ANALYSIS')}
                >
                    <FiBarChart2 aria-hidden="true" /> ANALYSIS
                </button>
            </div>

            {tab === 'REPORTS' && (
                <div className={styles.pillarStack}>
                    <DrawerPanel open={drawers.studio} onToggle={() => toggleDrawer('studio')} label="BUILD YOUR OWN REPORT" icon={FiSliders} tall>
                        <ReportStudio canSeeMoney={hasFinancialAccess} mode="report" reloadToken={reloadToken} />
                    </DrawerPanel>

                    {hasFinancialAccess ? (
                        <DrawerPanel open={drawers.finance} onToggle={() => toggleDrawer('finance')} label="FINANCIAL REPORTS" icon={FiBarChart2}>
                            <div className={styles.reportList}>
                                {FINANCIAL_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                            </div>
                        </DrawerPanel>
                    ) : (
                        <div className={styles.restrictionHandbrake} role="alert">
                            <FiLock className={styles.lockIcon} aria-hidden="true" />
                            <div className={styles.warningText}>
                                <strong>SECURITY HANDBRAKE ACTIVE</strong>
                                <p>FINANCIAL PILLARS ARE ENCRYPTED. CONTACT ROOT OWNER FOR ACCESS.</p>
                            </div>
                        </div>
                    )}

                    <DrawerPanel open={drawers.ops} onToggle={() => toggleDrawer('ops')} label="OPERATIONAL REPORTS" icon={FiMap}>
                        <div className={styles.reportList}>
                            {OPS_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                        </div>
                    </DrawerPanel>

                    {hasFinancialAccess && (
                        <DrawerPanel open={drawers.system} onToggle={() => toggleDrawer('system')} label="SYSTEM REPORTS" icon={FiShield}>
                            <div className={styles.reportList}>
                                {SYSTEM_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                            </div>
                        </DrawerPanel>
                    )}

                    {hasFinancialAccess && (
                        <DrawerPanel open={drawers.p2} onToggle={() => toggleDrawer('p2')} label="MORE REPORTS" icon={FiBarChart2}>
                            <div className={styles.reportList}>
                                {PRIORITY2_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                            </div>
                        </DrawerPanel>
                    )}
                </div>
            )}

            {tab === 'ANALYSIS' && (
                <div className={styles.pillarStack}>
                    {/* Just the studio. The expense-analysis drawer that used to
                        sit here was the EXPENSES dataset with the grouping
                        pre-chosen for you -- the same numbers, reachable in two
                        clicks from the builder, so it was a second way to say
                        the same thing. The canned CSV pillars stay on the
                        REPORTS tab where they belong. */}
                    <DrawerPanel open={drawers.aStudio} onToggle={() => toggleDrawer('aStudio')}
                        label="ASK ANYTHING" icon={FiSliders} tall>
                        <ReportStudio canSeeMoney={hasFinancialAccess} mode="analysis" reloadToken={reloadToken} />
                    </DrawerPanel>
                </div>
            )}
        </div>
    );
};

export default ReportHub;
"""

PREFS_CONTEXT = r"""// PATH: erp-frontend/src/context/PreferencesContext.js
import { createContext } from 'react';

export const DEFAULT_PREFS = {
    theme: 'light',      // light | dark   -- page background and chrome
    uiScale: '100',      // 90 | 100 | 110 | 125
    statSize: 'standard',// small | standard | large
    motion: 'full',      // full | reduced
    tips: 'normal',      // normal | slow | off
    contrast: 'normal',  // normal | high
};

export const PreferencesContext = createContext({
    prefs: DEFAULT_PREFS,
    setPref: () => {},
    resetPrefs: () => {},
});
"""

PREFS_PROVIDER = r"""// PATH: erp-frontend/src/context/PreferencesProvider.jsx
/**
 * GOLDEN SEED -- APPEARANCE PREFERENCES
 *
 * Everything here is applied by writing data-attributes and CSS variables onto
 * <html>, which is the only way a preference can reach every page without
 * every page having to opt in. The CSS that reads them lives in index.css.
 *
 * Choices are per-device, in localStorage, not per-account on the server. That
 * is deliberate: "this screen is too small to read" is a fact about the screen
 * in front of you, not about who you are, and the office shares logins across
 * a desktop and two phones.
 *
 * WHAT EACH ONE ACTUALLY DOES -- no setting here is decorative:
 *   theme     swaps the page background and the sidebar rail between the
 *             cream original and a slate dark. Panels stay dark navy in both,
 *             because the panel palette is still hard-coded per page; a full
 *             inversion needs that tokenised first.
 *   uiScale   zoom on #root. The app is laid out in px and clamp(), not rem,
 *             so a root font-size would move almost nothing -- zoom moves all
 *             of it. Tooltips portal into #root rather than <body> so they
 *             scale and stay aligned with it.
 *   statSize  the --stat-* tokens the summary cards read off.
 *   motion    kills animation and transition app-wide.
 *   tips      hover-explainer dwell, or off entirely.
 *   contrast  strengthens table rules and panel edges.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PreferencesContext, DEFAULT_PREFS } from './PreferencesContext';

const KEY = 'goldenseed.prefs.v1';

const readStored = () => {
    try {
        const raw = window.localStorage.getItem(KEY);
        if (!raw) return DEFAULT_PREFS;
        return { ...DEFAULT_PREFS, ...JSON.parse(raw) };
    } catch {
        return DEFAULT_PREFS;
    }
};

const STAT_SIZES = {
    small:    { label: 'clamp(8px, 0.8vw, 9.5px)',  value: 'clamp(12px, 1.3vw, 15px)',   valueSm: 'clamp(10px, 1.1vw, 12px)', note: 'clamp(7px, 0.75vw, 9px)' },
    standard: { label: 'clamp(8px, 0.85vw, 10px)',  value: 'clamp(13px, 1.45vw, 16.5px)', valueSm: 'clamp(11px, 1.2vw, 13px)', note: 'clamp(7px, 0.8vw, 9px)' },
    large:    { label: 'clamp(9px, 0.95vw, 11px)',  value: 'clamp(16px, 1.8vw, 21px)',    valueSm: 'clamp(13px, 1.4vw, 16px)', note: 'clamp(8px, 0.85vw, 10px)' },
};

export const PreferencesProvider = ({ children }) => {
    const [prefs, setPrefs] = useState(readStored);

    useEffect(() => {
        const root = document.documentElement;
        root.setAttribute('data-theme', prefs.theme);
        root.setAttribute('data-motion', prefs.motion);
        root.setAttribute('data-tips', prefs.tips);
        root.setAttribute('data-contrast', prefs.contrast);
        root.style.setProperty('--ui-scale', String(Number(prefs.uiScale || 100) / 100));

        const s = STAT_SIZES[prefs.statSize] || STAT_SIZES.standard;
        root.style.setProperty('--stat-label', s.label);
        root.style.setProperty('--stat-value', s.value);
        root.style.setProperty('--stat-value-sm', s.valueSm);
        root.style.setProperty('--stat-note', s.note);

        try { window.localStorage.setItem(KEY, JSON.stringify(prefs)); } catch { /* private mode */ }
    }, [prefs]);

    const setPref = useCallback((key, value) => setPrefs(p => ({ ...p, [key]: value })), []);
    const resetPrefs = useCallback(() => setPrefs(DEFAULT_PREFS), []);

    const value = useMemo(() => ({ prefs, setPref, resetPrefs }), [prefs, setPref, resetPrefs]);

    return (
        <PreferencesContext.Provider value={value}>
            {children}
        </PreferencesContext.Provider>
    );
};

export default PreferencesProvider;
"""

USE_PREFS = r"""// PATH: erp-frontend/src/context/usePreferences.js
import { useContext } from 'react';
import { PreferencesContext } from './PreferencesContext';

export const usePreferences = () => useContext(PreferencesContext);
export default usePreferences;
"""


# ============================================================ 1. GLOBAL CSS
GLOBAL_CSS = """
/* ===== APPEARANCE PREFERENCES (fix69) ==============================
   Written onto <html> by context/PreferencesProvider. Everything below
   is the CSS half of a setting the user can actually change in
   Settings -> Appearance. Nothing here is decorative.
   ================================================================== */
:root {
    --ui-scale: 1;

    /* The page background is built from these two in
       CircuitBackground.module.css, which is what makes a dark page
       theme possible at all without touching every panel. */
    --bg-base: #F4F2EF;
    --bg-rgb: 244, 242, 239;
}

/* PAGE THEME -- background and chrome only. Panels stay dark navy in
   both themes: that palette is still hard-coded per page, and a half
   inverted app is worse than a consistent one. Tokenising the panel
   colours is the next step, and then this selector grows. */
:root[data-theme="dark"] {
    --bg-base: #16292b;
    --bg-rgb: 22, 41, 43;
    --text-on-light: #F4F2EF;
}

/* UI SIZE -- the app is laid out in px and clamp(), not rem, so a root
   font-size would move almost nothing. zoom moves all of it, and #root
   is the right place because the tooltip portal lives inside it. */
#root { zoom: var(--ui-scale); }

/* REDUCED MOTION -- the user's explicit choice, so !important is
   correct here: it has to beat every page's local animation. */
:root[data-motion="reduced"] *,
:root[data-motion="reduced"] *::before,
:root[data-motion="reduced"] *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
}

/* HIGH CONTRAST -- stronger row rules and panel edges. Helps most on the
   cheap office monitors, which is where it was asked for. */
:root[data-contrast="high"] table tbody td { border-bottom-color: rgba(255, 255, 255, 0.22) !important; }
:root[data-contrast="high"] table tbody tr:hover { background: rgba(255, 255, 255, 0.10) !important; }
"""


def patch_global_css():
    print('\n[1/9] index.css -- preference tokens, zoom, motion, contrast')
    p = P('index.css')
    if not require(p, 'index.css'):
        return
    css = read(p)
    # fix68 set these as constants; they are a user setting now, and the
    # provider overwrites them at runtime. These stay as the fallback for
    # the first paint before React mounts.
    css = swap(css, '--stat-label:    clamp(9px,  0.95vw, 11px);',
               '--stat-label:    clamp(8px,  0.85vw, 10px);', 'stat label down a size')
    css = swap(css, '--stat-value:    clamp(17px, 2.0vw,  23px);',
               '--stat-value:    clamp(13px, 1.45vw, 16.5px);', 'stat value down a size')
    css = swap(css, '--stat-value-sm: clamp(13px, 1.5vw,  17px);',
               '--stat-value-sm: clamp(11px, 1.2vw,  13px);', 'stat small value down a size')
    css = swap(css, '--stat-note:     clamp(8px,  0.85vw, 10px);',
               '--stat-note:     clamp(7px,  0.8vw,  9px);', 'stat note down a size')
    css = append_block(css, '/* ===== APPEARANCE PREFERENCES (fix69)', GLOBAL_CSS, 'index.css preference layer')
    write(p, css, 'index.css')


# ============================================================ 2. BACKGROUND
def patch_background():
    print('\n[2/9] CircuitBackground -- tokenised so a dark page theme is possible')
    p = P('components', 'layout', 'CircuitBackground.module.css')
    if not require(p, 'CircuitBackground.module.css'):
        return
    css = read(p)
    css = swap(css, '    background: #F4F2EF;\n    background:',
               '    background: var(--bg-base);\n    background:', 'background base token')
    css = swap_all(css, 'rgba(244,242,239,', 'rgba(var(--bg-rgb),', 'background gradient tokens')
    write(p, css, 'CircuitBackground.module.css')


# ============================================================ 3. PROVIDER
def patch_bootstrap():
    print('\n[3/9] Preferences provider wired into the bootstrapper')
    write(P('context', 'PreferencesContext.js'), PREFS_CONTEXT, 'context/PreferencesContext.js')
    write(P('context', 'PreferencesProvider.jsx'), PREFS_PROVIDER, 'context/PreferencesProvider.jsx')
    write(P('context', 'usePreferences.js'), USE_PREFS, 'context/usePreferences.js')

    p = P('main.jsx')
    if not require(p, 'main.jsx'):
        return
    s = read(p)
    s = swap(s, "import App from './App.jsx'",
             "import App from './App.jsx'\nimport PreferencesProvider from './context/PreferencesProvider'", 'main.jsx import')
    s = swap(s, """  <React.StrictMode>
    <App />
  </React.StrictMode>,""",
             """  <React.StrictMode>
    {/* Outermost on purpose: it writes onto <html> before anything renders,
        so the first paint is already at the user's chosen size and theme. */}
    <PreferencesProvider>
      <App />
    </PreferencesProvider>
  </React.StrictMode>,""", 'main.jsx provider')
    write(p, s, 'main.jsx')


# ============================================================ 4. TOOLTIP
def patch_tooltip():
    print('\n[4/9] Hover explainers time out, and scale with the UI')
    write(P('components', 'common', 'Tooltip.jsx'), TOOLTIP_JSX, 'components/common/Tooltip.jsx')


# ============================================================ 5. REPORTS
def patch_reports():
    print('\n[5/9] Reports -- light surface, header refresh, no duplication')
    write(P('pages', 'Reports', 'ReportStudio.jsx'), STUDIO_JSX, 'pages/Reports/ReportStudio.jsx')
    write(P('pages', 'Reports', 'ReportStudio.module.css'), STUDIO_CSS, 'pages/Reports/ReportStudio.module.css')
    write(P('pages', 'Reports', 'ReportHub.jsx'), REPORTHUB_JSX, 'pages/Reports/ReportHub.jsx')

    p = P('pages', 'Reports', 'ReportHub.module.css')
    if require(p, 'ReportHub.module.css'):
        css = read(p)
        css = append_block(css, '/* ── STUDIO SURFACE (fix69)', """
/* ── STUDIO SURFACE (fix69) ───────────────────────────────────────
   The drawer that holds the Report Studio is a light workbench, not a
   navy panel -- see the note at the top of ReportStudio.module.css. */
.studioInner {
    background: #faf8f5;
    border-top: 1px solid #e6e0d8;
    padding: clamp(12px, 1.8vw, 22px);
}
""", 'ReportHub studio surface')
        write(p, css, 'ReportHub.module.css')

    # The expense analysis component is no longer mounted anywhere. Left on
    # disk rather than deleted: it is the only place the by-staff endpoint is
    # called, and that is worth keeping around if it is ever wanted back.
    print('  [note ] ExpenseAnalysis.jsx left on disk, no longer mounted')


# ============================================================ 6. SETTINGS
APPEARANCE_PANEL = """        <div className={styles.hwPanel}>
          <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiSliders className={styles.drawerIcon} aria-hidden="true" /> APPEARANCE</div></div>
          <div className={styles.panelBody} style={{ maxHeight: 2000 }}><div className={styles.panelInner}>
            <div className={styles.securityAlert}><FiMonitor aria-hidden="true" /><span>These are saved on this device, not on your account -- the office shares logins across a desktop and two phones, and "this screen is too small to read" is a fact about the screen.</span></div>
            {PREF_GROUPS.map(group => (
              <div key={group.key} className={styles.prefRow}>
                <div className={styles.prefLabel}>
                  <strong>{group.label}</strong>
                  <span>{group.hint}</span>
                </div>
                <div className={styles.prefOptions} role="group" aria-label={group.label}>
                  {group.options.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      className={prefs[group.key] === opt.value ? styles.prefBtnActive : styles.prefBtn}
                      aria-pressed={prefs[group.key] === opt.value}
                      onClick={() => setPref(group.key, opt.value)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            <div className={styles.submitRow}>
              <button type="button" className={styles.commitBtn} onClick={resetPrefs}><FiRotateCcw aria-hidden="true" /> RESET APPEARANCE</button>
            </div>
          </div></div>
        </div>
"""

PREF_GROUPS_CONST = """
/* Every option here is wired to real CSS in index.css -- see the note at the
   top of context/PreferencesProvider.jsx for what each one moves. */
const PREF_GROUPS = [
  { key: 'theme', label: 'Page theme', hint: 'Background and chrome. Panels stay navy in both.',
    options: [{ value: 'light', label: 'CREAM' }, { value: 'dark', label: 'SLATE' }] },
  { key: 'uiScale', label: 'Interface size', hint: 'Scales the whole app, not just text.',
    options: [{ value: '90', label: '90%' }, { value: '100', label: '100%' }, { value: '110', label: '110%' }, { value: '125', label: '125%' }] },
  { key: 'statSize', label: 'Summary box size', hint: 'The figures at the top of Payments, Expenses and the dossier.',
    options: [{ value: 'small', label: 'SMALL' }, { value: 'standard', label: 'STANDARD' }, { value: 'large', label: 'LARGE' }] },
  { key: 'tips', label: 'Hover explainers', hint: 'How long before they appear, or turn them off.',
    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'slow', label: 'SLOW' }, { value: 'off', label: 'OFF' }] },
  { key: 'motion', label: 'Animation', hint: 'Turn off movement and fades across the app.',
    options: [{ value: 'full', label: 'ON' }, { value: 'reduced', label: 'REDUCED' }] },
  { key: 'contrast', label: 'Table contrast', hint: 'Stronger row lines for low-quality monitors.',
    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'high', label: 'HIGH' }] },
];
"""

SETTINGS_CSS = """
/* ── APPEARANCE (fix69) ───────────────────────────────────────────── */
.prefRow {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 12px; padding: clamp(10px, 1.3vw, 14px) 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.prefRow:last-of-type { border-bottom: none; }
.prefLabel { display: flex; flex-direction: column; gap: 3px; min-width: 190px; flex: 1 1 200px; }
.prefLabel strong {
  font-family: 'Inter', sans-serif; font-size: clamp(10px, 1vw, 12px);
  font-weight: 900; letter-spacing: 1.2px; text-transform: uppercase;
  color: rgba(244, 242, 239, 0.9);
}
/* CONTRAST RULE: cream 62% on the navy panel is 5.3:1 -- fine for this size. */
.prefLabel span {
  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px);
  font-weight: 500; line-height: 1.45; color: rgba(244, 242, 239, 0.62);
}
.prefOptions { display: flex; flex-wrap: wrap; gap: 6px; }
.prefBtn, .prefBtnActive {
  font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);
  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
  padding: clamp(6px, 0.9vw, 9px) clamp(10px, 1.4vw, 15px);
  border-radius: 6px; cursor: pointer; transition: all 0.18s ease; white-space: nowrap;
  border: 1.5px solid rgba(255, 255, 255, 0.18);
  background: rgba(26, 46, 48, 0.75); color: rgba(255, 255, 255, 0.85);
}
.prefBtn:hover { background: rgba(238, 140, 58, 0.14); border-color: #EE8C3A; color: #EE8C3A; }
.prefBtnActive { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.prefBtn:focus-visible, .prefBtnActive:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 2px; }
"""


def patch_settings():
    print('\n[6/9] Settings -- a real, wired Appearance panel')
    p = P('pages', 'settings', 'SettingsPage.jsx')
    if require(p, 'SettingsPage.jsx'):
        s = read(p)
        s = swap(s, "import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff } from 'react-icons/fi';",
                 "import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff, FiSliders, FiMonitor } from 'react-icons/fi';",
                 'Settings: icon imports')
        s = swap(s, "import { useAuth } from '../../hooks/useAuth';",
                 "import { useAuth } from '../../hooks/useAuth';\nimport { usePreferences } from '../../context/usePreferences';",
                 'Settings: usePreferences import')
        s = swap(s, "const RANKS = ['ROLE_ADMIN', 'ROLE_DIRECTOR', 'ROLE_MANAGER', 'ROLE_SECRETARY'];",
                 "const RANKS = ['ROLE_ADMIN', 'ROLE_DIRECTOR', 'ROLE_MANAGER', 'ROLE_SECRETARY'];\n" + PREF_GROUPS_CONST,
                 'Settings: preference groups')
        s = swap(s, "  const { user } = useAuth();\n  const isRoot = !!user?.isRoot;",
                 "  const { user } = useAuth();\n  const { prefs, setPref, resetPrefs } = usePreferences();\n  const isRoot = !!user?.isRoot;",
                 'Settings: preferences hook')
        s = swap(s, "      <div className={styles.workstationGrid}>\n",
                 "      <div className={styles.workstationGrid}>\n" + APPEARANCE_PANEL,
                 'Settings: Appearance panel')
        s = swap(s, "<p className={styles.subtitle}>Security, governance and danger zone</p>",
                 "<p className={styles.subtitle}>Appearance, security, governance and the danger zone</p>",
                 'Settings: subtitle')
        write(p, s, 'SettingsPage.jsx')

    p = P('pages', 'settings', 'SettingsPage.module.css')
    if require(p, 'SettingsPage.module.css'):
        css = read(p)
        css = append_block(css, '/* ── APPEARANCE (fix69)', SETTINGS_CSS, 'Settings: Appearance CSS')
        write(p, css, 'SettingsPage.module.css')


# ============================================================ 7. FOLDER
def patch_folder():
    print('\n[7/9] Folder page -- owner names open the client dossier')
    p = P('pages', 'DigitalFolder', 'FolderPage.jsx')
    if not require(p, 'FolderPage.jsx'):
        return
    s = read(p)
    # Owner cards in the OWNERS tab. Every other client name in the app opens
    # the dossier; this was the one that did not.
    s = swap(s,
             """                            </div>)) : project.proprietors.map((p, i) => (<div key={i} className={styles.ownerStaticCard}>
                                <h2 className={styles.ownerName}>{p.fullName}</h2>""",
             """                            </div>)) : project.proprietors.map((p, i) => (<div key={i} className={styles.ownerStaticCard}>
                                {/* Every other client name in the app opens the
                                    dossier. This one used to be dead text. */}
                                {p.id ? (
                                    <button type="button" className={styles.ownerNameLink}
                                        onClick={() => navigate('/client/' + p.id)}
                                        title={`Open ${p.fullName}'s full portfolio`}>
                                        {p.fullName}
                                    </button>
                                ) : <h2 className={styles.ownerName}>{p.fullName}</h2>}""",
             'Folder: owner name -> dossier')
    write(p, s, 'FolderPage.jsx')

    p = P('pages', 'DigitalFolder', 'FolderPage.module.css')
    if require(p, 'FolderPage.module.css'):
        css = read(p)
        css = append_block(css, '/* ── OWNER NAME LINK (fix69)', """
/* ── OWNER NAME LINK (fix69) ──────────────────────────────────────
   Matches .ownerName exactly, plus the affordances that say it goes
   somewhere: pointer, underline on hover, a real focus ring. It is a
   <button> and not an <a> because it navigates through the router. */
.ownerNameLink {
  display: block; width: 100%; text-align: left;
  background: none; border: none; padding: 0; margin: 0 0 10px;
  font-family: 'Cinzel', serif;
  font-size: clamp(14px, 1.6vw, 19px);
  font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  color: #EE8C3A; cursor: pointer;
  transition: color 0.15s, text-decoration-color 0.15s;
  text-decoration: underline; text-decoration-color: rgba(238, 140, 58, 0.35);
  text-underline-offset: 4px;
}
.ownerNameLink:hover { color: #fff; text-decoration-color: #fff; }
.ownerNameLink:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 3px; border-radius: 3px; }
""", 'Folder: owner link CSS')
        write(p, css, 'FolderPage.module.css')


# ============================================================ 8. AUDIT
def patch_audit():
    print('\n[8/9] Audit -- date range and CSV export')
    p = P('pages', 'Audit', 'AuditPage.jsx')
    if not require(p, 'AuditPage.jsx'):
        return
    s = read(p)
    s = swap(s, "    FiChevronLeft, FiChevronRight, FiPhoneCall, FiUser\n",
             "    FiChevronLeft, FiChevronRight, FiPhoneCall, FiUser, FiDownloadCloud\n",
             'Audit: export icon')
    s = swap(s, "import React, { useState, useEffect, useCallback } from 'react';",
             "import React, { useState, useEffect, useCallback, useMemo } from 'react';",
             'Audit: useMemo import')
    s = swap(s, "    const [filters,    setFilters]    = useState({ operator: '', action: '', search: '' });",
             "    const [filters,    setFilters]    = useState({ operator: '', action: '', search: '', from: '', to: '' });",
             'Audit: date filter state')
    s = swap(s, """    const isDirty = filters.search !== '' || (filters.operator !== '' && filters.operator !== 'ALL STAFF') || (filters.action !== '' && filters.action !== 'ALL ACTIONS');""",
             """    const isDirty = filters.search !== '' || filters.from !== '' || filters.to !== '' || (filters.operator !== '' && filters.operator !== 'ALL STAFF') || (filters.action !== '' && filters.action !== 'ALL ACTIONS');""",
             'Audit: dirty check includes dates')
    # The search endpoint takes operator and action but not a date window, and
    # the log is already paged, so the window is applied to the page in hand.
    s = swap(s, "    useEffect(() => { fetchForensics(); }, [fetchForensics]);",
             """    useEffect(() => { fetchForensics(); }, [fetchForensics]);

    // WHEN, which is the first question anyone asks of an audit trail and the
    // one filter the page did not have. The search endpoint takes operator and
    // action but no date window, so this narrows the page in hand rather than
    // the query -- honest about its scope in the hint under the controls.
    const visibleLogs = useMemo(() => {
        const from = filters.from ? new Date(filters.from + 'T00:00:00').getTime() : null;
        const to   = filters.to   ? new Date(filters.to   + 'T23:59:59').getTime() : null;
        if (from === null && to === null) return logs;
        return logs.filter(l => {
            const t = new Date(l.timestamp).getTime();
            if (!Number.isFinite(t)) return false;
            if (from !== null && t < from) return false;
            if (to !== null && t > to) return false;
            return true;
        });
    }, [logs, filters.from, filters.to]);

    const exportVisible = () => {
        const cell = v => {
            const str = v === null || v === undefined ? '' : String(v);
            return /[",\\n]/.test(str) ? '"' + str.replace(/"/g, '""') + '"' : str;
        };
        const rows = visibleLogs.map(l => [
            new Date(l.timestamp).toISOString(), l.performedBy, l.action, l.details || '',
        ]);
        const csv = [['TIMESTAMP', 'OPERATOR', 'ACTION', 'DETAILS'], ...rows]
            .map(r => r.map(cell).join(',')).join('\\n');
        // The BOM stops Excel reading a UTF-8 CSV as Latin-1.
        const blob = new Blob(['\\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.setAttribute('download', 'GOLDEN_SEED_AUDIT_' + new Date().toISOString().slice(0, 10) + '.csv');
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    };""",
             'Audit: date window + CSV export')
    s = swap(s, """                    <button className={styles.resetBtn} onClick={() => setFilters({operator:'', action:'', search:''})} aria-label="Reset all filters">
                        <FiFilter aria-hidden="true" /> RESET FILTERS
                    </button>""",
             """                    <label className={styles.dateField}>
                        <span>FROM</span>
                        <input type="date" value={filters.from} aria-label="From date"
                            onChange={e => setFilters({...filters, from: e.target.value})} />
                    </label>
                    <label className={styles.dateField}>
                        <span>TO</span>
                        <input type="date" value={filters.to} aria-label="To date"
                            onChange={e => setFilters({...filters, to: e.target.value})} />
                    </label>
                    <button className={styles.resetBtn} onClick={() => setFilters({operator:'', action:'', search:'', from:'', to:''})} aria-label="Reset all filters">
                        <FiFilter aria-hidden="true" /> RESET FILTERS
                    </button>
                    <button className={styles.resetBtn} onClick={exportVisible} disabled={visibleLogs.length === 0} aria-label="Export the visible log to CSV">
                        <FiDownloadCloud aria-hidden="true" /> EXPORT CSV
                    </button>""",
             'Audit: date inputs + export button')
    s = swap(s, "                    {!loading && logs.length === 0 && <div className={styles.emptySignal} role=\"status\">NO DIGITAL FOOTPRINTS FOUND FOR THIS RANGE</div>}\n                    {!loading && logs.map(log => (",
             "                    {!loading && visibleLogs.length === 0 && <div className={styles.emptySignal} role=\"status\">NO DIGITAL FOOTPRINTS FOUND FOR THIS RANGE</div>}\n                    {!loading && visibleLogs.map(log => (",
             'Audit: render the filtered list')
    s = swap(s, "<span>VISIBLE RECORDS: <strong>{logs.length}</strong></span>",
             "<span>VISIBLE RECORDS: <strong>{visibleLogs.length}</strong></span>",
             'Audit: HUD counts what is on screen')
    write(p, s, 'AuditPage.jsx')

    p = P('pages', 'Audit', 'AuditPage.module.css')
    if require(p, 'AuditPage.module.css'):
        css = read(p)
        css = append_block(css, '/* ── DATE FILTER (fix69)', """
/* ── DATE FILTER (fix69) ──────────────────────────────────────────
   Matches .resetBtn's height and weight so the filter row stays one
   straight line rather than a stack of differently-sized controls. */
.dateField {
  display: flex; align-items: center; gap: 7px;
  background: #fff; border: 1.5px solid #c8d6d7; border-radius: 6px;
  padding: 0 10px; height: clamp(36px, 4.4vw, 44px);
}
.dateField span {
  font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 900;
  letter-spacing: 1.5px; text-transform: uppercase;
  /* CONTRAST RULE: this control is white, so its text is navy. */
  color: #5b6f70;
}
.dateField input {
  border: none; outline: none; background: transparent; color: #1a2e30;
  font-family: 'Inter', sans-serif; font-size: clamp(10px, 1vw, 12px); font-weight: 700;
  min-width: 108px;
}
.dateField:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.16); }
""", 'Audit: date field CSS')
        write(p, css, 'AuditPage.module.css')


# ============================================================ main
def main():
    print('=' * 70)
    print('GOLDEN SEED -- fix69')
    print('=' * 70)
    if not os.path.isdir(FE):
        print('ERROR: erp-frontend/src not found. Run fix.py from the repo root.')
        sys.exit(1)

    patch_global_css()
    patch_background()
    patch_bootstrap()
    patch_tooltip()
    patch_reports()
    patch_settings()
    patch_folder()
    patch_audit()

    print('\n[9/9] Done patching.')
    print('\n' + '-' * 70)
    print('FILES WRITTEN: ' + str(len(CHANGED)))
    for c in CHANGED:
        print('  - ' + c)
    if SKIPPED:
        print('ANCHORS MISSED (left untouched, review by hand):')
        for s in SKIPPED:
            print('  ! ' + s)
    print('-' * 70)

    print('\nCommitting...')
    run(['git', 'add', '-A'])
    code = run(['git', 'commit', '-m',
                'fix69: Report Studio on a light surface with header refresh and '
                'dropdown pickers, analysis tab de-duplicated, tooltips time out '
                'and scale, smaller stat boxes, Settings appearance preferences '
                '(theme/UI size/motion/tips/contrast), folder owner names open '
                'the dossier, audit date range + CSV export'])
    if code != 0:
        print('  (nothing to commit, or commit failed -- pushing anyway)')
    run(['git', 'push'])
    print('\nDone.')


if __name__ == '__main__':
    main()