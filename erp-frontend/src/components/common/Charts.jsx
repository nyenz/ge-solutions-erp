// PATH: erp-frontend/src/components/common/Charts.jsx
/**
 * GOLDEN SEED -- CHARTS
 *
 * Hand-rolled SVG. No charting library, on purpose: Recharts and friends are
 * 90-150kB gzipped for four chart types, they ship their own colour opinions
 * that would have to be fought back to the Golden Seed palette, and this app
 * is loaded over Ugandan mobile data. Five small components cost nothing and
 * read the theme tokens directly, so they follow Cream/Slate/Midnight for
 * free.
 *
 * Every chart takes the same shape so the studio can swap between them
 * without reshaping its data:
 *
 *   rows      [{ id, label, value, parts?: [{ label, value }] }]
 *   format    (n) => string     how to write a value
 *
 * Colour: one accent ramp, walked in order. Never colour alone as the carrier
 * of meaning -- every series is labelled in the legend and on hover.
 */
import React, { useId, useMemo, useState } from 'react';
import styles from './Charts.module.css';

const RAMP = [
    'var(--accent)', '#4FA3A5', '#C2643F', '#7E9B54', '#9B6FA8',
    '#4E7CA8', '#D4A63C', '#B05A78', '#5B8C7B', '#8A7250',
];
const colourAt = (i) => RAMP[i % RAMP.length];

const niceCeiling = (max) => {
    if (!Number.isFinite(max) || max <= 0) return 1;
    const mag = Math.pow(10, Math.floor(Math.log10(max)));
    const step = [1, 2, 2.5, 5, 10].find(s => max <= s * mag) || 10;
    return step * mag;
};

const ticksFor = (ceil, count = 4) =>
    Array.from({ length: count + 1 }, (_, i) => (ceil / count) * i);

/* Long district names have to be readable without becoming the whole chart. */
const trim = (s, n) => {
    const str = String(s ?? '---');
    return str.length > n ? str.slice(0, n - 1) + '…' : str;
};

/* ── shared chrome ─────────────────────────────────────────────────── */
const Legend = ({ items }) => (
    <div className={styles.legend}>
        {items.map((it, i) => (
            <span key={it.label + i} className={styles.legendItem}>
                <span className={styles.legendSwatch} style={{ background: it.colour }} />
                {it.label}
            </span>
        ))}
    </div>
);

const Empty = ({ label = 'NOTHING TO CHART' }) => (
    <div className={styles.empty}>{label}</div>
);

/* ═══════════════════════════════════════════════════════════════════
   HORIZONTAL BARS -- the default.
   Ranked categories with long names (districts, staff, categories) read
   far better sideways: the label gets a full line of horizontal room
   instead of being rotated 45 degrees under a tick.
   ═══════════════════════════════════════════════════════════════════ */
export const BarRows = ({ rows, format = String }) => {
    const max = useMemo(
        () => Math.max(0, ...rows.map(r => Math.abs(Number(r.value) || 0))),
        [rows],
    );
    if (!rows.length) return <Empty />;

    return (
        <div className={styles.barRows}>
            {rows.map((r, i) => (
                <div key={r.id ?? i} className={styles.barRow}>
                    <span className={styles.barLabel} title={String(r.label)}>{r.label}</span>
                    <span className={styles.barTrack}>
                        <span
                            className={styles.barFill}
                            style={{
                                width: max ? `${Math.max(1.5, (Math.abs(Number(r.value) || 0) / max) * 100)}%` : '1.5%',
                                background: colourAt(i),
                            }}
                        />
                    </span>
                    <span className={styles.barValue}>{format(r.value)}</span>
                </div>
            ))}
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════
   VERTICAL COLUMNS -- for anything with a natural left-to-right order,
   which in practice means months. A time series drawn as ranked bars
   hides the shape you were looking for.
   ═══════════════════════════════════════════════════════════════════ */
export const ColumnChart = ({ rows, format = String, height = 230 }) => {
    const [hover, setHover] = useState(null);
    const W = 760, PAD_L = 62, PAD_R = 12, PAD_T = 14, PAD_B = 42;
    const max = Math.max(0, ...rows.map(r => Math.abs(Number(r.value) || 0)));
    const ceil = niceCeiling(max);
    const plotW = W - PAD_L - PAD_R;
    const plotH = height - PAD_T - PAD_B;

    if (!rows.length) return <Empty />;

    const slot = plotW / rows.length;
    const barW = Math.min(46, Math.max(5, slot * 0.62));

    return (
        <div className={styles.svgWrap}>
            <svg viewBox={`0 0 ${W} ${height}`} className={styles.svg} role="img"
                aria-label={`Column chart of ${rows.length} values`}>
                {ticksFor(ceil).map((t, i) => {
                    const y = PAD_T + plotH - (t / ceil) * plotH;
                    return (
                        <g key={i}>
                            <line x1={PAD_L} x2={W - PAD_R} y1={y} y2={y} className={styles.grid} />
                            <text x={PAD_L - 8} y={y + 3.5} className={styles.axisText} textAnchor="end">
                                {format(t)}
                            </text>
                        </g>
                    );
                })}

                {rows.map((r, i) => {
                    const v = Math.abs(Number(r.value) || 0);
                    const h = ceil ? (v / ceil) * plotH : 0;
                    const x = PAD_L + slot * i + (slot - barW) / 2;
                    return (
                        <g key={r.id ?? i}
                            onMouseEnter={() => setHover(i)}
                            onMouseLeave={() => setHover(null)}>
                            <rect x={PAD_L + slot * i} y={PAD_T} width={slot} height={plotH} fill="transparent" />
                            <rect
                                x={x} y={PAD_T + plotH - h} width={barW} height={Math.max(h, 1)}
                                rx={3}
                                fill={colourAt(i)}
                                opacity={hover === null || hover === i ? 1 : 0.42}
                            />
                            <text x={x + barW / 2} y={height - PAD_B + 15}
                                className={styles.axisText} textAnchor="middle">
                                {trim(r.label, rows.length > 12 ? 5 : 10)}
                            </text>
                            {hover === i && (
                                <text x={x + barW / 2} y={PAD_T + plotH - h - 6}
                                    className={styles.valueText} textAnchor="middle">
                                    {format(r.value)}
                                </text>
                            )}
                        </g>
                    );
                })}
                <line x1={PAD_L} x2={W - PAD_R} y1={PAD_T + plotH} y2={PAD_T + plotH} className={styles.axis} />
            </svg>
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════
   LINE -- trend over an ordered dimension.
   ═══════════════════════════════════════════════════════════════════ */
export const LineChart = ({ rows, format = String, height = 230 }) => {
    const [hover, setHover] = useState(null);
    const gradId = useId().replace(/[:]/g, '');
    const W = 760, PAD_L = 62, PAD_R = 14, PAD_T = 14, PAD_B = 42;
    const max = Math.max(0, ...rows.map(r => Math.abs(Number(r.value) || 0)));
    const ceil = niceCeiling(max);
    const plotW = W - PAD_L - PAD_R;
    const plotH = height - PAD_T - PAD_B;

    if (rows.length < 2) return <Empty label="A LINE NEEDS AT LEAST TWO GROUPS" />;

    const xAt = i => PAD_L + (plotW / (rows.length - 1)) * i;
    const yAt = v => PAD_T + plotH - (ceil ? (Math.abs(Number(v) || 0) / ceil) * plotH : 0);

    const path = rows.map((r, i) => `${i ? 'L' : 'M'}${xAt(i)},${yAt(r.value)}`).join(' ');
    const area = `${path} L${xAt(rows.length - 1)},${PAD_T + plotH} L${PAD_L},${PAD_T + plotH} Z`;
    const every = Math.ceil(rows.length / 10);

    return (
        <div className={styles.svgWrap}>
            <svg viewBox={`0 0 ${W} ${height}`} className={styles.svg} role="img"
                aria-label={`Line chart across ${rows.length} groups`}>
                <defs>
                    <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="var(--accent)" stopOpacity="0.32" />
                        <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
                    </linearGradient>
                </defs>

                {ticksFor(ceil).map((t, i) => {
                    const y = PAD_T + plotH - (t / ceil) * plotH;
                    return (
                        <g key={i}>
                            <line x1={PAD_L} x2={W - PAD_R} y1={y} y2={y} className={styles.grid} />
                            <text x={PAD_L - 8} y={y + 3.5} className={styles.axisText} textAnchor="end">
                                {format(t)}
                            </text>
                        </g>
                    );
                })}

                <path d={area} fill={`url(#${gradId})`} />
                <path d={path} className={styles.line} />

                {rows.map((r, i) => (
                    <g key={r.id ?? i}
                        onMouseEnter={() => setHover(i)}
                        onMouseLeave={() => setHover(null)}>
                        <circle cx={xAt(i)} cy={yAt(r.value)} r={hover === i ? 5.5 : 3.2} className={styles.dot} />
                        <circle cx={xAt(i)} cy={yAt(r.value)} r={14} fill="transparent" />
                        {i % every === 0 && (
                            <text x={xAt(i)} y={height - PAD_B + 15} className={styles.axisText} textAnchor="middle">
                                {trim(r.label, 8)}
                            </text>
                        )}
                        {hover === i && (
                            <text x={xAt(i)} y={yAt(r.value) - 11} className={styles.valueText} textAnchor="middle">
                                {format(r.value)}
                            </text>
                        )}
                    </g>
                ))}
                <line x1={PAD_L} x2={W - PAD_R} y1={PAD_T + plotH} y2={PAD_T + plotH} className={styles.axis} />
            </svg>
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════
   DONUT -- share of a whole. Only honest for a handful of positive
   parts, so it tops out at 8 and folds the rest into OTHER.
   ═══════════════════════════════════════════════════════════════════ */
export const DonutChart = ({ rows, format = String, size = 210 }) => {
    const [hover, setHover] = useState(null);

    const slices = useMemo(() => {
        const pos = rows
            .map(r => ({ ...r, value: Math.abs(Number(r.value) || 0) }))
            .filter(r => r.value > 0);
        if (pos.length <= 8) return pos;
        const head = pos.slice(0, 7);
        const tail = pos.slice(7).reduce((s, r) => s + r.value, 0);
        return [...head, { id: '__other', label: 'OTHER', value: tail }];
    }, [rows]);

    const total = slices.reduce((s, r) => s + r.value, 0);
    if (!total) return <Empty label="NOTHING POSITIVE TO SHARE OUT" />;

    const R = size / 2, RING = size * 0.19, r = R - RING / 2;
    let angle = -Math.PI / 2;

    const arcs = slices.map((s, i) => {
        const sweep = (s.value / total) * Math.PI * 2;
        const x1 = R + r * Math.cos(angle);
        const y1 = R + r * Math.sin(angle);
        angle += sweep;
        const x2 = R + r * Math.cos(angle);
        const y2 = R + r * Math.sin(angle);
        return {
            ...s,
            colour: colourAt(i),
            pct: (s.value / total) * 100,
            d: `M${x1},${y1} A${r},${r} 0 ${sweep > Math.PI ? 1 : 0} 1 ${x2},${y2}`,
        };
    });

    const focus = hover === null ? null : arcs[hover];

    return (
        <div className={styles.donutWrap}>
            <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} role="img"
                aria-label={`Share of total across ${slices.length} groups`}>
                {arcs.map((a, i) => (
                    <path key={a.id ?? i} d={a.d} fill="none"
                        stroke={a.colour} strokeWidth={RING}
                        opacity={hover === null || hover === i ? 1 : 0.35}
                        onMouseEnter={() => setHover(i)}
                        onMouseLeave={() => setHover(null)} />
                ))}
                <text x={R} y={R - 4} textAnchor="middle" className={styles.donutValue}>
                    {focus ? format(focus.value) : format(total)}
                </text>
                <text x={R} y={R + 13} textAnchor="middle" className={styles.donutLabel}>
                    {focus ? `${trim(focus.label, 14)} ${focus.pct.toFixed(1)}%` : 'TOTAL'}
                </text>
            </svg>
            <Legend items={arcs.map(a => ({ label: `${trim(a.label, 18)} (${a.pct.toFixed(1)}%)`, colour: a.colour }))} />
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════
   STACKED -- the split-by view. Each group is one bar, divided by the
   second dimension, which is the only chart here that can answer
   "payments per month, split by who recorded them" in one picture.
   ═══════════════════════════════════════════════════════════════════ */
export const StackedRows = ({ rows, format = String }) => {
    const keys = useMemo(() => {
        const seen = [];
        rows.forEach(r => (r.parts || []).forEach(p => {
            if (!seen.includes(p.label)) seen.push(p.label);
        }));
        return seen;
    }, [rows]);

    const max = useMemo(
        () => Math.max(0, ...rows.map(r => (r.parts || []).reduce((s, p) => s + Math.abs(Number(p.value) || 0), 0))),
        [rows],
    );

    if (!rows.length || !keys.length) return <Empty />;

    return (
        <div className={styles.barRows}>
            {rows.map((r, i) => {
                const parts = r.parts || [];
                const sum = parts.reduce((s, p) => s + Math.abs(Number(p.value) || 0), 0);
                return (
                    <div key={r.id ?? i} className={styles.barRow}>
                        <span className={styles.barLabel} title={String(r.label)}>{r.label}</span>
                        <span className={styles.barTrack}>
                            <span className={styles.stack} style={{ width: max ? `${Math.max(1.5, (sum / max) * 100)}%` : '1.5%' }}>
                                {parts.map((p, j) => (
                                    <span
                                        key={p.label + j}
                                        className={styles.stackPart}
                                        title={`${p.label}: ${format(p.value)}`}
                                        style={{
                                            width: sum ? `${(Math.abs(Number(p.value) || 0) / sum) * 100}%` : '0%',
                                            background: colourAt(keys.indexOf(p.label)),
                                        }}
                                    />
                                ))}
                            </span>
                        </span>
                        <span className={styles.barValue}>{format(sum)}</span>
                    </div>
                );
            })}
            <Legend items={keys.map((k, i) => ({ label: trim(k, 20), colour: colourAt(i) }))} />
        </div>
    );
};

export const CHART_TYPES = [
    { key: 'bars',   label: 'BARS'    },
    { key: 'column', label: 'COLUMNS' },
    { key: 'line',   label: 'LINE'    },
    { key: 'donut',  label: 'SHARE'   },
    { key: 'stack',  label: 'STACKED' },
];

export const Chart = ({ type, rows, format }) => {
    if (type === 'column') return <ColumnChart  rows={rows} format={format} />;
    if (type === 'line')   return <LineChart    rows={rows} format={format} />;
    if (type === 'donut')  return <DonutChart   rows={rows} format={format} />;
    if (type === 'stack')  return <StackedRows  rows={rows} format={format} />;
    return <BarRows rows={rows} format={format} />;
};

export default Chart;
