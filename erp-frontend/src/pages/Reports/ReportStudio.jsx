// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
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
