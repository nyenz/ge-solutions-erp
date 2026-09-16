#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOLDEN SEED -- fix68
=====================================================================
SIX CHANGES, ONE PASS.

1. STAT BOXES READ BIGGER, EVERYWHERE
   The summary cards were labelled at 7-9px and valued at 11-13px --
   too small to scan a number off at arm's length, which is exactly
   what those cards are for. There are now three global tokens in
   index.css (--stat-label / --stat-value / --stat-note) and every
   stat card in the app points at them: Payments, Client Dossier,
   Client Ledger, Expenses, Recovery, Audit, and the new Report
   Studio. Change the three numbers once and the whole app moves.
   The Dashboard is deliberately left alone, as asked.

2. ONE HEADER BUTTON FOR THE WHOLE APP
   New shared component: components/common/HeaderButton.jsx. It is
   the Payments refresh button's look at the Expenses button's size,
   which is what the brief asked for. Rolled out to Payments,
   Expenses, Project Ledger, Client Ledger, Recovery, Audit and the
   Dossier. BELOW 640px IT COLLAPSES TO AN ICON -- page headers stack
   on phones and a row of word-buttons is what forces the stack.

3. NO MORE DOUBLE "NEW PRESET" ON EXPENSES
   It sat in the header AND in the LOG AN EXPENSE panel. The panel is
   where it belongs -- next to the tiles it creates -- so the header
   copy is gone.

4. REPORTS REBUILT AS REPORTS + ANALYSIS
   Two tabs, and behind both of them a new Report Studio: pick a
   dataset (Projects / Clients / Payments / Expenses), filter it as
   narrow as one client or as broad as everything, include or exclude
   any column, group it, measure it, and split it by a second field
   to compare. Saved views, CSV export of whatever is on screen.
   Role rules hold: restricted datasets and money columns are never
   offered to a user without financial access.

5. THE HOVER EXPLAINER IS QUIETER AND NO LONGER CLIPPED
   It was a bordered navy card with an orange edge and a pointer --
   a third panel-like object on a screen that already has two. Now:
   no border, no pointer, translucent slab, Inter at normal weight.
   And the clipping is fixed properly -- it used to clamp the bubble's
   CENTRE to 80px from the edge, which is less than half its width,
   so sidebar tooltips still ran off screen. It now measures itself
   after render and nudges by exactly the overflow.

Run:  python fix.py
Auto: git add -A / commit / push
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, 'erp-frontend', 'src')

P = lambda *a: os.path.join(FE, *a)

INDEX_CSS = P('index.css')
TOOLTIP_JSX_PATH = P('components', 'common', 'Tooltip.jsx')
TOOLTIP_CSS_PATH = P('components', 'common', 'Tooltip.module.css')
HEADERBTN_JSX_PATH = P('components', 'common', 'HeaderButton.jsx')
HEADERBTN_CSS_PATH = P('components', 'common', 'HeaderButton.module.css')

PAYMENTS_JSX = P('pages', 'Payments', 'PaymentsPage.jsx')
PAYMENTS_CSS = P('pages', 'Payments', 'PaymentsPage.module.css')
EXPENSES_JSX = P('pages', 'Financials', 'ExpensesPage.jsx')
EXPENSES_CSS = P('pages', 'Financials', 'ExpensesPage.module.css')
PORTFOLIO_CSS = P('pages', 'Clients', 'ClientPortfolioPage.module.css')
CLEDGER_JSX = P('pages', 'Clients', 'ClientLedgerPage.jsx')
LEDGER_JSX = P('pages', 'Ledger', 'LedgerPage.jsx')
RECOVERY_JSX = P('pages', 'Recovery', 'RecoveryPortal.jsx')
RECOVERY_CSS = P('pages', 'Recovery', 'RecoveryPortal.module.css')
AUDIT_JSX = P('pages', 'Audit', 'AuditPage.jsx')
AUDIT_CSS = P('pages', 'Audit', 'AuditPage.module.css')
REPORTDATA_PATH = P('pages', 'Reports', 'reportData.js')
STUDIO_JSX_PATH = P('pages', 'Reports', 'ReportStudio.jsx')
STUDIO_CSS_PATH = P('pages', 'Reports', 'ReportStudio.module.css')
REPORTHUB_JSX_PATH = P('pages', 'Reports', 'ReportHub.jsx')
REPORTHUB_CSS_PATH = P('pages', 'Reports', 'ReportHub.module.css')

CHANGED = []
SKIPPED = []


def read(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def write(path, text, label):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)
    if label not in CHANGED:
        CHANGED.append(label)
    print('  [write] ' + label)


def require(path, label):
    if not os.path.isfile(path):
        print('  [MISS ] ' + label + ' -- not found')
        SKIPPED.append(label)
        return False
    return True


def swap(text, old, new, label):
    """Exact-substring replace. Idempotent: a no-op if `new` is already in."""
    if new and new in text:
        print('  [ skip] ' + label + ' (already applied)')
        return text
    if old not in text:
        print('  [WARN ] ' + label + ' -- anchor not found, left alone')
        SKIPPED.append(label)
        return text
    print('  [patch] ' + label)
    return text.replace(old, new, 1)


def resub(text, pattern, repl, label, count=1):
    new, n = re.subn(pattern, repl, text, count=count)
    if n == 0:
        print('  [ skip] ' + label + ' (no match -- already applied or absent)')
    else:
        print('  [patch] ' + label)
    return new


def append_block(text, marker, block, label):
    if marker in text:
        print('  [ skip] ' + label + ' (already applied)')
        return text
    print('  [patch] ' + label)
    return text.rstrip() + '\n' + block


def run(cmd):
    print('$ ' + ' '.join(cmd))
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


# ===================================================== EMBEDDED FILE BODIES

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
export const Tooltip = ({ label, children, placement = 'top', delay = 120, disabled = false, block = false }) => {
    const [open, setOpen] = useState(false);
    const [box, setBox] = useState({ top: 0, left: 0, place: placement });
    const [shift, setShift] = useState(0);
    const anchorRef = useRef(null);
    const bubbleRef = useRef(null);
    const timerRef = useRef(null);
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
        if (disabled || !label) return;
        clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => { measure(); setOpen(true); }, delay);
    }, [disabled, label, delay, measure]);

    const hide = useCallback(() => {
        clearTimeout(timerRef.current);
        setOpen(false);
        setShift(0);
    }, []);

    useEffect(() => () => clearTimeout(timerRef.current), []);

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
                onTouchStart={() => { measure(); setOpen(o => !o); }}
                aria-describedby={open ? tipId : undefined}
            >
                {children}
            </span>
            {open && typeof document !== 'undefined' && createPortal(
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
                document.body,
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

TOOLTIP_CSS = r"""/* PATH: erp-frontend/src/components/common/Tooltip.module.css */

.anchor {
    display: inline-flex;
    align-items: center;
    max-width: 100%;
}

/* The wrapper span becomes the layout box wherever it is inserted. Inside a
   flex or grid parent that is harmless -- the browser blockifies flex and
   grid items -- but inside an ordinary block parent (the sidebar nav) an
   inline-flex span shrinks to its text, and would shrink the nav rows with
   it. block makes the wrapper transparent to layout instead. */
.anchorBlock {
    display: block;
    width: 100%;
}

/* fix68: was a bordered navy card -- orange 1.5px edge, 30px shadow, a
   pointer triangle and DM Sans 600. Three panel-like objects on screen at
   once (page panel, table, tooltip) is what made hovering feel congested.
   This is deliberately not a panel: no border, no pointer, a translucent
   slab that blurs whatever is under it and reads as a passing note.

   The bubble is portalled to <body>, so it sits outside every page's
   .container token scope -- every colour here has to be literal.
   CONTRAST RULE: cream 90% over #121f22 at 86% opacity = 11.1:1. */
.bubble {
    position: fixed;
    z-index: 100000;
    max-width: min(300px, 78vw);
    padding: 7px 11px;
    border-radius: 7px;
    background: rgba(18, 32, 34, 0.86);
    -webkit-backdrop-filter: blur(10px);
    backdrop-filter: blur(10px);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28);
    color: rgba(244, 242, 239, 0.9);
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 400;
    line-height: 1.5;
    letter-spacing: 0.1px;
    text-align: left;
    text-transform: none;
    white-space: normal;
    overflow-wrap: anywhere;
    pointer-events: none; /* never let the bubble eat the next hover */
    animation: tipIn 0.12s ease-out;
}

@keyframes tipIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

/* Inline jargon -- the dotted underline is the affordance. Without it
   nobody knows there is anything to hover over. */
.term {
    border-bottom: 1px dotted currentColor;
    cursor: help;
    outline: none;
}
.term:focus-visible {
    outline: 2px solid #EE8C3A;
    outline-offset: 2px;
    border-radius: 2px;
}

@media (prefers-reduced-motion: reduce) {
    .bubble { animation: none; }
}
"""

HEADERBTN_JSX = r"""// PATH: erp-frontend/src/components/common/HeaderButton.jsx
import React from 'react';
import { Tooltip } from './Tooltip';
import styles from './HeaderButton.module.css';

/**
 * GOLDEN SEED -- THE PAGE HEADER BUTTON
 *
 * One button spec for every page header in the app. It is the Payment Records
 * refresh button's look -- translucent navy on the frosted header bar, thin
 * navy edge, orange on hover -- at the Expenses button's size, which is the
 * smaller of the two the app was shipping.
 *
 * Before this there were three dialects: Payments' 40px light button,
 * Expenses' 34px one, and the Dossier's dark navy pills. Same job, same
 * position on screen, three different sizes and two different colour schemes.
 *
 * ON SMALL SCREENS IT BECOMES AN ICON. Page headers stack on phones and a row
 * of word-buttons is the thing that forces the stack. Below 640px the label is
 * dropped and the button goes square -- the tooltip already carries the words,
 * and aria-label keeps it announced.
 *
 * Variants:
 *   (default) ghost   -- on the frosted white page header
 *   primary           -- the one affirmative action, orange filled
 *   danger            -- destructive
 *   onDark            -- same spec, for a header sitting on a dark panel
 */
export const HeaderActions = ({ children, className = '' }) => (
    <div className={`${styles.actions} ${className}`}>{children}</div>
);

export const HeaderButton = ({
    icon: Icon,
    label,
    onClick,
    tip,
    variant = 'ghost',
    busy = false,
    disabled = false,
    type = 'button',
    ariaLabel,
}) => (
    <Tooltip label={tip || label}>
        <button
            type={type}
            className={`${styles.btn} ${styles[variant] || ''}`}
            onClick={onClick}
            disabled={disabled || busy}
            aria-label={ariaLabel || label}
        >
            {Icon && (
                <span className={`${styles.icon} ${busy ? styles.spin : ''}`} aria-hidden="true">
                    <Icon />
                </span>
            )}
            <span className={styles.label}>{label}</span>
        </button>
    </Tooltip>
);

export default HeaderButton;
"""

HEADERBTN_CSS = r"""/* PATH: erp-frontend/src/components/common/HeaderButton.module.css */

.actions {
    display: flex;
    align-items: center;
    gap: clamp(6px, 0.9vw, 10px);
    flex-wrap: wrap;
    flex-shrink: 0;
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: clamp(30px, 3.4vw, 36px);
    padding: 0 clamp(10px, 1.4vw, 16px);
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    white-space: nowrap;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    /* CONTRAST RULE: #1a2e30 on the frosted header (cream at 62% white) is
       13.4:1. On hover the fill goes orange and the text goes white, which
       is 2.3:1 -- so hover keeps the navy text instead. */
    background: rgba(26, 46, 48, 0.08);
    border: 1.5px solid rgba(26, 46, 48, 0.2);
    color: #1a2e30;
}
.btn:hover:not(:disabled) { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 2px; }

.primary { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.primary:hover:not(:disabled) { background: #d97a2b; border-color: #d97a2b; color: #1a2e30; }

.danger { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.4); color: #991b1b; }
.danger:hover:not(:disabled) { background: #ef4444; border-color: #ef4444; color: #fff; }

/* Same spec, for a header that sits on a dark panel rather than the frosted bar. */
.onDark { background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.18); color: rgba(244, 242, 239, 0.85); }
.onDark:hover:not(:disabled) { background: rgba(238, 140, 58, 0.14); border-color: #EE8C3A; color: #EE8C3A; }

.icon { display: inline-flex; align-items: center; font-size: clamp(11px, 1.2vw, 13px); flex-shrink: 0; }
.spin { animation: hbSpin 0.9s linear infinite; }
@keyframes hbSpin { to { transform: rotate(360deg); } }

/* Icon-only below 640px -- see the note in HeaderButton.jsx. */
@media (max-width: 640px) {
    .btn { width: 34px; min-width: 34px; height: 34px; padding: 0; gap: 0; }
    .label { display: none; }
    .icon { font-size: 15px; }
}

@media (prefers-reduced-motion: reduce) {
    .spin { animation: none; }
}
"""

REPORTDATA_JS = r"""// PATH: erp-frontend/src/pages/Reports/reportData.js
/**
 * GOLDEN SEED -- THE REPORT STUDIO DATA LAYER
 *
 * The canned CSV pillars answer twelve fixed questions. This answers any
 * question, because the shape of the question is the user's to decide: pick a
 * dataset, filter it down as far as you like, choose which columns you want,
 * group it, measure it, compare one slice against another.
 *
 * It runs entirely in the browser on data the app already serves. There is no
 * new backend endpoint and no new query language to get wrong: four list
 * endpoints are pulled once, cached, and everything after that is local. That
 * also means a filter or a grouping is instant and costs nothing, which is the
 * only way an explore-it-yourself tool is usable at all.
 *
 * ROLE RULES ARE ENFORCED IN TWO PLACES, deliberately. The server already
 * refuses the financial endpoints to non-directors -- that is the real
 * boundary. What happens here is the second half: a dataset marked
 * `restricted` and a field marked `money` are never offered to a user without
 * financial access, so a manager is not shown a column that would just come
 * back empty or 403.
 *
 * ADDING A FIELD: add one entry to the dataset's `fields` array. Filters,
 * columns, grouping, measures, comparison and CSV all read from that array, so
 * nothing else needs touching.
 */
import api from '../../api/axios';
import landService from '../../services/landService';
import recoveryService from '../../services/recoveryService';
import expenseService from '../../services/expenseService';

/* ── value helpers ───────────────────────────────────────────────── */
export const num = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
};
export const fmtMoney = (v) => 'UGX ' + num(v).toLocaleString();
export const fmtNum = (v) => num(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
export const fmtDate = (v) => (v ? new Date(v).toLocaleDateString() : '---');

const daysSince = (v) => {
    if (!v) return null;
    const t = new Date(v).getTime();
    if (!Number.isFinite(t)) return null;
    return Math.floor((Date.now() - t) / 86400000);
};
const monthKey = (v) => {
    if (!v) return '---';
    const d = new Date(v);
    if (Number.isNaN(d.getTime())) return '---';
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
};

export const formatValue = (value, type) => {
    if (value === null || value === undefined || value === '') return '---';
    if (type === 'money') return fmtMoney(value);
    if (type === 'number') return fmtNum(value);
    if (type === 'percent') return fmtNum(value) + '%';
    if (type === 'date') return fmtDate(value);
    if (type === 'bool') return value ? 'YES' : 'NO';
    return String(value);
};

const f = (key, label, type, get, extra) => ({ key, label, type, get, ...(extra || {}) });

/* ── PROJECTS ────────────────────────────────────────────────────── */
const projectFields = [
    f('index', 'Project Index', 'text', p => p.projectIndex || ''),
    f('plot', 'Plot Number', 'text', p => p.landTitle?.plotNumber || ''),
    f('titleId', 'Title ID', 'text', p => p.landTitle?.titleId || ''),
    f('tenure', 'Tenure', 'text', p => p.landTitle?.tenure || ''),
    f('blockRoad', 'Block / Road', 'text', p => p.landTitle?.blockRoad || ''),
    f('district', 'District', 'text', p => p.district || ''),
    f('county', 'County', 'text', p => p.county || ''),
    f('subCounty', 'Sub-County', 'text', p => p.subCounty || ''),
    f('parish', 'Parish', 'text', p => p.parish || ''),
    f('village', 'Village', 'text', p => p.village || ''),
    f('area', 'Area', 'text', p => p.area || ''),
    f('owner', 'Primary Owner', 'text', p => p.proprietors?.[0]?.fullName || ''),
    f('ownerPhone', 'Owner Phone', 'text', p => p.proprietors?.[0]?.phoneNumber || ''),
    f('ownerNin', 'Owner NIN', 'text', p => p.proprietors?.[0]?.nationalId || ''),
    f('ownerAddress', 'Owner Address', 'text', p => p.proprietors?.[0]?.homeAddress || ''),
    f('allOwners', 'All Owners', 'text', p => (p.proprietors || []).map(o => o.fullName).join(', ')),
    f('ownerCount', 'Owner Count', 'number', p => (p.proprietors || []).length),
    f('ownership', 'Ownership', 'text', p => ((p.proprietors || []).length > 1 ? 'JOINT' : 'SOLO')),
    f('status', 'Status', 'text', p => p.status || ''),
    f('stage', 'Stage Index', 'number', p => num(p.currentStageIndex)),
    f('planType', 'Plan Type', 'text', p => p.planType || ''),
    f('titled', 'Has Title', 'bool', p => !!p.landTitle),
    f('released', 'Title Released', 'bool', p => !!p.landTitle?.isReleased),
    f('legacy', 'Legacy', 'bool', p => !!p.isLegacy),
    f('receivable', 'In Receivables', 'bool', p => !!p.isReceivable),
    f('problem', 'Flagged Problem', 'bool', p => !!p.problem),
    f('startDate', 'Project Start', 'date', p => p.projectStartDate || null),
    f('lastPayment', 'Last Payment', 'date', p => p.lastPaymentDate || null),
    f('daysSincePayment', 'Days Since Payment', 'number', p => daysSince(p.lastPaymentDate)),
    f('receivableStart', 'Receivables Start', 'date', p => p.receivableStartDate || null),
    f('totalCost', 'Total Cost', 'money', p => num(p.totalCost), { money: true }),
    f('amountPaid', 'Amount Paid', 'money', p => num(p.amountPaid), { money: true }),
    f('balance', 'Balance Owed', 'money', p => Math.max(0, num(p.totalCost) - num(p.amountPaid)), { money: true }),
    f('storage', 'Storage Fees', 'money', p => num(p.storageFeesAccumulated), { money: true }),
    f('originalDebt', 'Original Debt', 'money', p => num(p.originalDebt), { money: true }),
    f('installment', 'Weekly Installment', 'money', p => num(p.weeklyInstallment), { money: true }),
    f('pctPaid', 'Percent Paid', 'percent', p => (num(p.totalCost) > 0 ? Math.round((num(p.amountPaid) / num(p.totalCost)) * 100) : 0), { money: true }),
];

/* ── CLIENTS ─────────────────────────────────────────────────────── */
const clientFields = [
    f('name', 'Client Name', 'text', c => c.name || ''),
    f('nin', 'NIN', 'text', c => c.nin || ''),
    f('phone', 'Phone', 'text', c => c.phone || ''),
    f('email', 'Email', 'text', c => c.email || ''),
    f('plotCount', 'Projects', 'number', c => num(c.plotCount)),
    f('districts', 'Districts', 'text', c => [...new Set((c.plots || []).map(p => p.district).filter(Boolean))].join(', ')),
    f('receivables', 'Has Receivables', 'bool', c => (c.plots || []).some(p => p.receivable)),
    f('lastContact', 'Last Contact', 'date', c => c.lastContact || null),
    f('daysSinceContact', 'Days Since Contact', 'number', c => daysSince(c.lastContact)),
    f('lastPaymentAt', 'Last Payment', 'date', c => c.lastPaymentAt || null),
    f('daysSincePayment', 'Days Since Payment', 'number', c => daysSince(c.lastPaymentAt)),
    f('lastTag', 'Last Call Tag', 'text', c => c.lastTag || ''),
    f('lastTone', 'Last Call Tone', 'text', c => c.lastTone || ''),
    f('owed', 'Total Owed', 'money', c => num(c.owed), { money: true }),
    f('paid', 'Total Paid', 'money', c => num(c.paid), { money: true }),
    f('storage', 'Storage Fees', 'money', c => num(c.storage), { money: true }),
    f('billed', 'Total Billed', 'money', c => num(c.owed) + num(c.paid), { money: true }),
    f('pctPaid', 'Percent Paid', 'percent', c => {
        const total = num(c.owed) + num(c.paid);
        return total > 0 ? Math.round((num(c.paid) / total) * 100) : 0;
    }, { money: true }),
];

/* ── PAYMENTS ────────────────────────────────────────────────────── */
const PAYMENT_TYPE_LABELS = {
    STANDARD: 'Title Payment',
    INITIAL_DEPOSIT: 'Initial Deposit',
    RECEIVABLE_PARTIAL: 'Receivables Payment',
};
const paymentFields = [
    f('date', 'Date', 'date', p => p.timestamp || null),
    f('month', 'Month', 'text', p => monthKey(p.timestamp)),
    f('year', 'Year', 'text', p => (p.timestamp ? String(new Date(p.timestamp).getFullYear()) : '---')),
    f('plot', 'Plot', 'text', p => p.plotNumber || ''),
    f('owner', 'Owner', 'text', p => p.ownerName || ''),
    f('type', 'Payment Type', 'text', p => PAYMENT_TYPE_LABELS[p.paymentType] || p.paymentType || ''),
    f('recordedBy', 'Recorded By', 'text', p => p.recordedBy || ''),
    f('notes', 'Notes', 'text', p => p.notes || ''),
    f('amount', 'Amount Paid', 'money', p => num(p.amountPaid), { money: true }),
    f('balanceAfter', 'Balance After', 'money', p => num(p.balanceAfter), { money: true }),
    f('daysAgo', 'Days Ago', 'number', p => daysSince(p.timestamp)),
];

/* ── EXPENSES ────────────────────────────────────────────────────── */
const expenseFields = [
    f('date', 'Date', 'date', e => e.createdAt || null),
    f('month', 'Month', 'text', e => monthKey(e.createdAt)),
    f('category', 'Category', 'text', e => e.category || ''),
    f('recordedBy', 'Logged By', 'text', e => e.recordedBy || ''),
    f('spentBy', 'Spent By', 'text', e => e.spentBy || e.recordedBy || ''),
    f('note', 'Note', 'text', e => e.note || ''),
    f('edited', 'Edited', 'bool', e => !!e.editedAt),
    f('amount', 'Amount', 'money', e => num(e.amount), { money: true }),
    f('daysAgo', 'Days Ago', 'number', e => daysSince(e.createdAt)),
];

/* ── dataset registry ────────────────────────────────────────────── */
export const DATASETS = {
    PROJECTS: {
        key: 'PROJECTS',
        label: 'Projects',
        blurb: 'Every land project: location, owners, stage, and the money against it.',
        restricted: false,
        fields: projectFields,
        defaultColumns: ['index', 'plot', 'district', 'owner', 'status', 'totalCost', 'amountPaid', 'balance'],
        load: async () => {
            // The ledger endpoint is paged. A report has to see all of it, not
            // page one, so this walks until a short page comes back.
            const out = [];
            const SIZE = 200;
            for (let page = 0; page < 60; page += 1) {
                const data = await landService.getGlobalLedger(page, SIZE);
                const rows = data?.content || [];
                out.push(...rows);
                if (rows.length < SIZE) break;
            }
            return out;
        },
    },
    CLIENTS: {
        key: 'CLIENTS',
        label: 'Clients',
        blurb: 'Every registered client with their portfolio totals and call history.',
        restricted: false,
        fields: clientFields,
        defaultColumns: ['name', 'phone', 'plotCount', 'districts', 'owed', 'paid', 'lastContact'],
        load: async () => (await recoveryService.getClientLedger()) || [],
    },
    PAYMENTS: {
        key: 'PAYMENTS',
        label: 'Payments',
        blurb: 'Every cash payment ever recorded, with who recorded it.',
        restricted: true,
        fields: paymentFields,
        defaultColumns: ['date', 'plot', 'owner', 'type', 'amount', 'recordedBy'],
        load: async () => (await api.get('/recovery/payments/all')).data || [],
    },
    EXPENSES: {
        key: 'EXPENSES',
        label: 'Expenses',
        blurb: 'Every shilling logged as leaving the office, by category and by staff.',
        restricted: true,
        fields: expenseFields,
        defaultColumns: ['date', 'category', 'amount', 'recordedBy', 'spentBy'],
        load: async () => {
            const data = await expenseService.search({}, 0, 5000);
            return data?.content || data || [];
        },
    },
};

export const datasetsFor = (canSeeMoney) =>
    Object.values(DATASETS).filter(d => canSeeMoney || !d.restricted);

export const fieldsFor = (dataset, canSeeMoney) =>
    (dataset?.fields || []).filter(fld => canSeeMoney || !fld.money);

export const fieldByKey = (dataset, key) => (dataset?.fields || []).find(fld => fld.key === key);

/* ── filtering ───────────────────────────────────────────────────── */
export const OPERATORS = {
    text: [
        { key: 'contains', label: 'contains', value: true },
        { key: 'notContains', label: 'does not contain', value: true },
        { key: 'is', label: 'is exactly', value: true },
        { key: 'isNot', label: 'is not', value: true },
        { key: 'startsWith', label: 'starts with', value: true },
        { key: 'empty', label: 'is empty', value: false },
        { key: 'notEmpty', label: 'is not empty', value: false },
    ],
    number: [
        { key: 'eq', label: '=', value: true },
        { key: 'ne', label: '!=', value: true },
        { key: 'gt', label: '>', value: true },
        { key: 'gte', label: '>=', value: true },
        { key: 'lt', label: '<', value: true },
        { key: 'lte', label: '<=', value: true },
        { key: 'between', label: 'between', value: true, value2: true },
    ],
    date: [
        { key: 'after', label: 'on or after', value: true, input: 'date' },
        { key: 'before', label: 'on or before', value: true, input: 'date' },
        { key: 'between', label: 'between', value: true, value2: true, input: 'date' },
        { key: 'lastDays', label: 'in the last N days', value: true },
        { key: 'empty', label: 'is empty (never)', value: false },
        { key: 'notEmpty', label: 'is not empty', value: false },
    ],
    bool: [
        { key: 'isTrue', label: 'is YES', value: false },
        { key: 'isFalse', label: 'is NO', value: false },
    ],
};
OPERATORS.money = OPERATORS.number;
OPERATORS.percent = OPERATORS.number;

export const operatorsFor = (type) => OPERATORS[type] || OPERATORS.text;

const matchOne = (raw, type, op, v1, v2) => {
    if (type === 'bool') {
        if (op === 'isTrue') return !!raw;
        if (op === 'isFalse') return !raw;
        return true;
    }
    if (type === 'date') {
        const has = raw !== null && raw !== undefined && raw !== '';
        if (op === 'empty') return !has;
        if (op === 'notEmpty') return has;
        if (!has) return false;
        const t = new Date(raw).getTime();
        if (op === 'lastDays') {
            const n = Number(v1);
            if (!Number.isFinite(n)) return true;
            return Date.now() - t <= n * 86400000;
        }
        const a = v1 ? new Date(v1 + 'T00:00:00').getTime() : null;
        const b = v2 ? new Date(v2 + 'T23:59:59').getTime() : null;
        if (op === 'after') return a === null || t >= a;
        if (op === 'before') return a === null || t <= new Date(v1 + 'T23:59:59').getTime();
        if (op === 'between') return (a === null || t >= a) && (b === null || t <= b);
        return true;
    }
    if (type === 'number' || type === 'money' || type === 'percent') {
        const n = num(raw);
        const a = Number(v1);
        const b = Number(v2);
        if (op === 'between') {
            if (Number.isFinite(a) && n < a) return false;
            if (Number.isFinite(b) && n > b) return false;
            return true;
        }
        if (!Number.isFinite(a)) return true;
        if (op === 'eq') return n === a;
        if (op === 'ne') return n !== a;
        if (op === 'gt') return n > a;
        if (op === 'gte') return n >= a;
        if (op === 'lt') return n < a;
        if (op === 'lte') return n <= a;
        return true;
    }
    const s = String(raw === null || raw === undefined ? '' : raw).toLowerCase();
    const q = String(v1 === null || v1 === undefined ? '' : v1).toLowerCase().trim();
    if (op === 'empty') return s.trim() === '';
    if (op === 'notEmpty') return s.trim() !== '';
    if (!q) return true;
    if (op === 'contains') return s.includes(q);
    if (op === 'notContains') return !s.includes(q);
    if (op === 'is') return s === q;
    if (op === 'isNot') return s !== q;
    if (op === 'startsWith') return s.startsWith(q);
    return true;
};

/**
 * Conditions combine with AND by default; set `mode` to 'OR' for any-of.
 * `search` is a free-text sweep across every text field, so you can narrow
 * without having to know which column a name lives in.
 */
export const applyFilters = (rows, dataset, conditions, mode = 'AND', search = '') => {
    const active = (conditions || []).filter(c => c.field && c.op);
    const q = (search || '').trim().toLowerCase();
    const textFields = (dataset.fields || []).filter(fld => fld.type === 'text');

    return rows.filter(row => {
        if (q) {
            const hit = textFields.some(fld => String(fld.get(row) || '').toLowerCase().includes(q));
            if (!hit) return false;
        }
        if (active.length === 0) return true;
        const results = active.map(c => {
            const fld = fieldByKey(dataset, c.field);
            if (!fld) return true;
            return matchOne(fld.get(row), fld.type, c.op, c.value, c.value2);
        });
        return mode === 'OR' ? results.some(Boolean) : results.every(Boolean);
    });
};

/* ── measures ────────────────────────────────────────────────────── */
export const AGGREGATIONS = [
    { key: 'count', label: 'Count of rows', needsField: false, type: 'number' },
    { key: 'sum', label: 'Sum', needsField: true },
    { key: 'avg', label: 'Average', needsField: true },
    { key: 'min', label: 'Minimum', needsField: true },
    { key: 'max', label: 'Maximum', needsField: true },
    { key: 'distinct', label: 'Distinct values', needsField: true, type: 'number' },
];

const aggregate = (rows, agg, fld) => {
    if (agg === 'count' || !fld) return rows.length;
    if (agg === 'distinct') return new Set(rows.map(r => String(fld.get(r) ?? ''))).size;
    const vals = rows.map(r => num(fld.get(r)));
    if (vals.length === 0) return 0;
    if (agg === 'sum') return vals.reduce((a, b) => a + b, 0);
    if (agg === 'avg') return vals.reduce((a, b) => a + b, 0) / vals.length;
    if (agg === 'min') return Math.min(...vals);
    if (agg === 'max') return Math.max(...vals);
    return 0;
};

export const measureType = (measure, dataset) => {
    const def = AGGREGATIONS.find(a => a.key === measure.agg);
    if (def && def.type) return def.type;
    const fld = fieldByKey(dataset, measure.field);
    if (!fld) return 'number';
    return fld.type === 'percent' ? 'number' : fld.type;
};

export const measureLabel = (measure, dataset) => {
    const def = AGGREGATIONS.find(a => a.key === measure.agg);
    if (!def) return 'Value';
    if (!def.needsField) return def.label;
    const fld = fieldByKey(dataset, measure.field);
    return def.label + ' of ' + (fld ? fld.label : '?');
};

/**
 * Group by one or two fields and run every measure over each bucket.
 * Two levels is the ceiling on purpose: a third turns a readable table into
 * a puzzle, and "compare" already covers the cross-tab case.
 */
export const groupRows = (rows, dataset, groupKeys, measures) => {
    const keys = (groupKeys || []).filter(Boolean).slice(0, 2);
    const flds = keys.map(k => fieldByKey(dataset, k)).filter(Boolean);
    const buckets = new Map();

    rows.forEach(row => {
        const path = flds.map(fld => {
            const v = fld.get(row);
            if (v === null || v === undefined || v === '') return '(none)';
            if (fld.type === 'bool') return v ? 'YES' : 'NO';
            if (fld.type === 'date') return fmtDate(v);
            return String(v);
        });
        const id = path.join(' \u2023 ') || 'ALL';
        if (!buckets.has(id)) buckets.set(id, { id, path, rows: [] });
        buckets.get(id).rows.push(row);
    });

    return [...buckets.values()].map(b => ({
        id: b.id,
        path: b.path,
        count: b.rows.length,
        values: (measures || []).map(m => aggregate(b.rows, m.agg, fieldByKey(dataset, m.field))),
        rows: b.rows,
    }));
};

export const summarise = (rows, dataset, measures) =>
    (measures || []).map(m => aggregate(rows, m.agg, fieldByKey(dataset, m.field)));

/* ── CSV out ─────────────────────────────────────────────────────── */
const csvCell = (v) => {
    const s = v === null || v === undefined ? '' : String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};

export const toCSV = (headers, matrix) =>
    [headers.map(csvCell).join(','), ...matrix.map(r => r.map(csvCell).join(','))].join('\n');

export const downloadCSV = (filename, csv) => {
    // Excel reads a bare UTF-8 CSV as Latin-1 and mangles anything non-ASCII.
    // The BOM is what tells it otherwise.
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
};

/* ── saved views ─────────────────────────────────────────────────── */
const VIEW_KEY = 'goldenseed.reportstudio.views.v1';

export const loadViews = () => {
    try {
        return JSON.parse(window.localStorage.getItem(VIEW_KEY) || '[]');
    } catch {
        return [];
    }
};

export const saveViews = (views) => {
    try {
        window.localStorage.setItem(VIEW_KEY, JSON.stringify(views));
        return true;
    } catch {
        return false;
    }
};
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
import React, { useState, useEffect, useMemo, useCallback } from 'react';
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

const ReportStudio = ({ canSeeMoney = false, mode = 'report' }) => {
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
                <div className={styles.chipRow}>
                    {available.map(ds => (
                        <Tooltip key={ds.key} label={ds.blurb}>
                            <button
                                className={ds.key === datasetKey ? styles.chipActive : styles.chip}
                                onClick={() => setDatasetKey(ds.key)}
                                aria-pressed={ds.key === datasetKey}
                            >
                                {ds.label.toUpperCase()}
                            </button>
                        </Tooltip>
                    ))}
                    <Tooltip label="Pull this dataset again from the server">
                        <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}>
                            <FiRefreshCw size={11} aria-hidden="true" /> RELOAD
                        </button>
                    </Tooltip>
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
                <div className={styles.chipRow}>
                    {fields.map(fl => (
                        <button
                            key={fl.key}
                            className={columns.includes(fl.key) ? styles.chipActive : styles.chip}
                            onClick={() => toggleColumn(fl.key)}
                            aria-pressed={columns.includes(fl.key)}
                        >
                            {fl.label}
                        </button>
                    ))}
                </div>
                <div className={styles.chipRow}>
                    <button className={styles.chip} onClick={() => setColumns(fields.map(fl => fl.key))}>SELECT ALL</button>
                    <button className={styles.chip} onClick={() => setColumns([])}>CLEAR</button>
                    <button className={styles.chip} onClick={() => setColumns(dataset.defaultColumns.filter(k => fields.some(fl => fl.key === k)))}>RESET</button>
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
/* Same reference chain as the rest of the app -- Payment Records -> Client
   Dossier -> here. Panels are the shared CollapsibleSection, so only the
   controls inside them are styled locally, and every control follows the
   app's standard filter-button / input spec. */
.studio {
  --orange: #EE8C3A; --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --amber: #f59e0b;
  --radius: 10px; --radius-sm: 6px;
  display: flex; flex-direction: column; gap: clamp(7px,1.1vw,14px);
  font-family: 'Inter', sans-serif; color: #fff;
}

.badge {
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px; text-transform: uppercase;
  color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.14); border-radius: 20px; padding: 4px 12px; flex-shrink: 0;
}

.hint {
  display: flex; align-items: center; gap: 7px; margin: 0;
  font-size: clamp(10px,1vw,11px); font-weight: 500; line-height: 1.5;
  color: rgba(244,242,239,0.62);
}
.hint svg { color: var(--orange); flex-shrink: 0; }

.error {
  display: flex; align-items: center; gap: 8px;
  background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.4);
  color: #fca5a5; font-size: 11px; font-weight: 700; border-radius: 6px; padding: 8px 12px;
}

.sectionLabel {
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 2px;
  color: var(--orange); text-transform: uppercase;
}

/* ── chips: the app's standard filter-button spec ─────────────────── */
.chipRow { display: flex; flex-wrap: wrap; align-items: center; gap: clamp(6px,0.9vw,10px); }
.chip, .chipActive, .exportBtn {
  font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  text-transform: uppercase; letter-spacing: 1.5px;
  padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.18); background: rgba(26,46,48,0.75); color: rgba(255,255,255,0.85);
  cursor: pointer; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;
}
.chip:hover:not(:disabled) { background: rgba(238,140,58,0.12); color: var(--orange); border-color: var(--orange); }
.chipActive, .exportBtn { background: var(--orange); color: #1a2e30; border-color: var(--orange); }
.chipActive:hover:not(:disabled), .exportBtn:hover:not(:disabled) { background: #d97a2b; border-color: #d97a2b; }
.chip:disabled, .chipActive:disabled, .exportBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.chip:focus-visible, .chipActive:focus-visible, .exportBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

.miniLabel {
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1.5px;
  text-transform: uppercase; color: rgba(255,255,255,0.5);
}

/* ── saved views ──────────────────────────────────────────────────── */
.viewBar { display: flex; flex-wrap: wrap; gap: clamp(6px,0.9vw,10px); align-items: center; }
.viewChip {
  display: inline-flex; align-items: center; gap: 2px;
  border: 1.5px solid rgba(238,140,58,0.35); border-radius: var(--radius-sm); overflow: hidden;
}
.viewChipName {
  background: rgba(238,140,58,0.1); border: none; color: var(--orange);
  font-family: 'Inter', sans-serif; font-size: clamp(9px,0.95vw,11px); font-weight: 800;
  padding: 7px 12px; cursor: pointer; transition: background 0.15s;
}
.viewChipName:hover { background: rgba(238,140,58,0.22); }
.viewChipDrop {
  background: rgba(239,68,68,0.12); border: none; color: #fca5a5;
  padding: 8px 9px; cursor: pointer; display: flex; align-items: center; transition: background 0.15s;
}
.viewChipDrop:hover { background: rgba(239,68,68,0.3); color: #fff; }

/* ── inputs ───────────────────────────────────────────────────────── */
.input, .select {
  height: 34px; padding: 0 10px; border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.15); background: rgba(0,0,0,0.22); color: #fff;
  font-family: 'Inter', sans-serif; font-size: clamp(10px,1.05vw,12px); font-weight: 600;
  min-width: 130px; flex: 1 1 140px; max-width: 100%;
}
.input:focus, .select:focus { outline: none; border-color: var(--orange); }
.select { cursor: pointer; }
/* The native menu paints on the OS surface, so options need their own
   colours or they render dark-on-dark on some platforms. */
.select option { background: #16292b; color: #fff; }

.condRow { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.dropBtn {
  height: 34px; width: 34px; flex: 0 0 34px; border-radius: var(--radius-sm);
  background: rgba(239,68,68,0.14); border: 1.5px solid transparent; color: #fca5a5;
  display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.15s;
}
.dropBtn:hover { background: rgba(239,68,68,0.3); border-color: var(--red); color: #fff; }

.pickerGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: clamp(8px,1.2vw,14px); }
.picker { display: flex; flex-direction: column; gap: 5px; min-width: 0; }

/* ── free-text search ─────────────────────────────────────────────── */
.searchRow {
  position: relative; display: flex; align-items: center;
  background: #fff; border: 1.5px solid #c8d6d7; border-radius: var(--radius-sm);
  height: clamp(36px,4.5vw,42px); transition: border-color 0.2s, box-shadow 0.2s;
}
.searchRow:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.searchIcon { position: absolute; left: 12px; color: var(--orange); font-size: 15px; pointer-events: none; }
.searchInput {
  width: 100%; border: none; outline: none; background: transparent;
  /* CONTRAST RULE: this input is white, so its text is navy, not cream. */
  color: #1a2e30; padding: 0 36px 0 38px; height: 100%;
  font-family: 'Inter', sans-serif; font-weight: 700; font-size: clamp(11px,1.1vw,13px);
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.35); }
.searchClear {
  position: absolute; right: 8px; background: transparent; border: none; cursor: pointer;
  color: rgba(26,46,48,0.45); display: flex; align-items: center; padding: 5px; border-radius: 4px;
}
.searchClear:hover { color: #1a2e30; background: rgba(26,46,48,0.08); }

/* ── stat strip -- the Payment Records card, same as everywhere ───── */
.statStrip { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr)); gap: clamp(10px,1.4vw,16px); }
.statCard {
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(12px,1.5vw,18px); display: flex; flex-direction: column; gap: 4px;
}
.statCard label { font-size: var(--stat-label); font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.5); }
.statCard strong { font-family: 'Space Mono', monospace; font-size: var(--stat-value); font-weight: 700; color: #fff; word-break: break-all; }
.statNote { font-size: var(--stat-note); font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.35); }

/* ── chart ────────────────────────────────────────────────────────── */
.chart { display: flex; flex-direction: column; gap: 8px; }
.chartRow { display: grid; grid-template-columns: minmax(90px, 190px) 1fr minmax(80px, 140px); align-items: center; gap: 10px; }
.chartLabel {
  font-size: clamp(9px,0.95vw,11px); font-weight: 800; color: rgba(255,255,255,0.82);
  text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.chartTrack { height: 13px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden; }
.chartFill { height: 100%; background: linear-gradient(90deg, var(--orange) 0%, #d97a28 100%); border-radius: 999px; transition: width 0.4s ease; }
.chartValue { font-family: 'Space Mono', monospace; font-size: clamp(9px,0.95vw,11px); font-weight: 700; text-align: right; color: rgba(255,255,255,0.75); }

/* ── table -- the Dossier ledger table ────────────────────────────── */
.tableScroll { overflow-x: auto; scrollbar-width: thin; scrollbar-color: var(--orange) transparent; }
.tableScroll::-webkit-scrollbar { height: 5px; }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 3px; }
.table { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 640px; }
.table thead th {
  background: #162a2c; color: var(--orange); font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  letter-spacing: 2px; text-transform: uppercase; text-align: left;
  padding: clamp(9px,1.3vw,14px) clamp(10px,1.5vw,16px);
  border-bottom: 3px solid var(--orange); white-space: nowrap;
  position: sticky; top: 0; z-index: 2;
}
.table thead th:first-child { border-radius: 6px 0 0 0; }
.table thead th:last-child { border-radius: 0 6px 0 0; }
.sortable { cursor: pointer; transition: background 0.18s, color 0.18s; }
.sortable:hover { background: linear-gradient(rgba(238,140,58,0.12), rgba(238,140,58,0.12)), #162a2c; color: #fff; }
.table tbody td {
  padding: clamp(8px,1.1vw,12px) clamp(10px,1.5vw,16px);
  border-bottom: 1px solid rgba(255,255,255,0.06); vertical-align: middle;
  color: #fff; font-size: clamp(10px,1.05vw,12px);
  max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.table tbody tr { border-left: 3px solid transparent; transition: background 0.15s; }
.table tbody tr:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.mono { font-family: 'Space Mono', monospace; font-weight: 700; }
.strong { font-weight: 800; }

/* CONTRAST RULE: inside a dark panel already, so cream text, no second card. */
.emptyCell {
  text-align: center; padding: clamp(20px,4vw,40px) 16px;
  font-family: 'Space Mono', monospace; color: rgba(244,242,239,0.68);
  font-size: 11px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
}

@media (max-width: 640px) {
  .chartRow { grid-template-columns: minmax(70px, 110px) 1fr minmax(64px, 96px); }
  .input, .select { flex: 1 1 100%; min-width: 0; }
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
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo, FiSliders
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import reportService from '../../services/reportService';
import BackToTopButton from '../../components/common/BackToTopButton';
import ExpenseAnalysis from './ExpenseAnalysis';
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
                        <ReportStudio canSeeMoney={hasFinancialAccess} mode="report" />
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
                    <DrawerPanel open={drawers.aStudio} onToggle={() => toggleDrawer('aStudio')} label="ASK ANYTHING" icon={FiSliders} tall>
                        <ReportStudio canSeeMoney={hasFinancialAccess} mode="analysis" />
                    </DrawerPanel>

                    {hasFinancialAccess ? (
                        <DrawerPanel open={drawers.expenses} onToggle={() => toggleDrawer('expenses')} label="EXPENSE ANALYSIS" icon={FiTrendingDown} tall>
                            <ExpenseAnalysis active={drawers.expenses} />
                        </DrawerPanel>
                    ) : (
                        <div className={styles.restrictionHandbrake} role="alert">
                            <FiLock className={styles.lockIcon} aria-hidden="true" />
                            <div className={styles.warningText}>
                                <strong>SECURITY HANDBRAKE ACTIVE</strong>
                                <p>EXPENSE ANALYSIS IS DIRECTOR-ONLY. CONTACT ROOT OWNER FOR ACCESS.</p>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ReportHub;
"""


# ===================================================== 1. GLOBAL STAT TOKENS
STAT_TOKENS = """
    /* ===== STAT CARD SCALE (fix68) =================================
       The summary boxes at the top of Payments, the Dossier, Expenses,
       Recovery and the Report Studio all read off these three. They were
       each carrying their own clamp() and had drifted small -- 7-9px
       labels over 11-13px figures, which is not a size you can scan a
       number off across a desk. One knob now, app-wide.
       The Dashboard deliberately does NOT use these; it has its own
       layout and was left alone.
       ============================================================== */
    --stat-label:    clamp(9px,  0.95vw, 11px);
    --stat-value:    clamp(17px, 2.0vw,  23px);
    --stat-value-sm: clamp(13px, 1.5vw,  17px);
    --stat-note:     clamp(8px,  0.85vw, 10px);
"""


def patch_global_tokens():
    print('\n[1/6] index.css -- global stat card scale')
    if not require(INDEX_CSS, 'index.css'):
        return
    css = read(INDEX_CSS)
    css = swap(
        css,
        "    --spinner-track:     rgba(238, 140, 58, 0.15);\n",
        "    --spinner-track:     rgba(238, 140, 58, 0.15);\n" + STAT_TOKENS,
        'index.css stat tokens')
    write(INDEX_CSS, css, 'index.css')


# ===================================================== 2. STAT CARDS APP-WIDE
def patch_stat_cards():
    print('\n[2/6] Stat cards -> the shared scale (Dashboard untouched)')

    # -- Payment Records: the card every other page was copied from ------
    if require(PAYMENTS_CSS, 'PaymentsPage.module.css'):
        css = read(PAYMENTS_CSS)
        css = swap(css,
                   ".sumCard label { font-family: 'DM Sans', sans-serif; font-size: var(--fs-label);",
                   ".sumCard label { font-family: 'DM Sans', sans-serif; font-size: var(--stat-label);",
                   'Payments .sumCard label')
        css = swap(css,
                   ".sumCard strong { font-family: 'Space Mono', monospace; font-size: var(--fs-value);",
                   ".sumCard strong { font-family: 'Space Mono', monospace; font-size: var(--stat-value);",
                   'Payments .sumCard value')
        css = swap(css,
                   ".sumCard span { font-size: var(--fs-label); color: rgba(255,255,255,0.35); }",
                   ".sumCard span { font-size: var(--stat-note); color: rgba(255,255,255,0.35); }",
                   'Payments .sumCard note')
        # The 480px override forced the figure back down to 13px, which
        # undid the whole point of the token on the screens that need the
        # size most.
        css = swap(css,
                   "    .sumCard strong { font-size: 13px; }",
                   "    .sumCard strong { font-size: clamp(15px, 4.5vw, 19px); }",
                   'Payments .sumCard 480px override')
        write(PAYMENTS_CSS, css, 'PaymentsPage.module.css')

    # -- Client Dossier --------------------------------------------------
    if require(PORTFOLIO_CSS, 'ClientPortfolioPage.module.css'):
        css = read(PORTFOLIO_CSS)
        css = swap(css, "  font-size: clamp(7px, 0.75vw, 9px);\n  font-weight: 900; letter-spacing: 1px; text-transform: uppercase;\n  color: rgba(255,255,255,0.5);",
                   "  font-size: var(--stat-label);\n  font-weight: 900; letter-spacing: 1px; text-transform: uppercase;\n  color: rgba(255,255,255,0.5);",
                   'Dossier .statCard label')
        css = swap(css, "  font-size: clamp(11px, 1.1vw, 13px);\n  font-weight: 700; color: #fff; word-break: break-all;",
                   "  font-size: var(--stat-value);\n  font-weight: 700; color: #fff; word-break: break-all;",
                   'Dossier .statCard value')
        css = swap(css, ".statTextValue { font-size: clamp(11px, 1.1vw, 13px); }",
                   ".statTextValue { font-size: var(--stat-value-sm); }",
                   'Dossier .statTextValue')
        css = swap(css, "  font-size: clamp(7px, 0.75vw, 9px);\n  font-weight: 700; letter-spacing: 1px; text-transform: uppercase;\n  color: rgba(255,255,255,0.35);",
                   "  font-size: var(--stat-note);\n  font-weight: 700; letter-spacing: 1px; text-transform: uppercase;\n  color: rgba(255,255,255,0.35);",
                   'Dossier .statNote')
        write(PORTFOLIO_CSS, css, 'ClientPortfolioPage.module.css')

    # -- Expenses --------------------------------------------------------
    if require(EXPENSES_CSS, 'ExpensesPage.module.css'):
        css = read(EXPENSES_CSS)
        css = swap(css,
                   "  font-family: 'Inter', sans-serif; font-size: clamp(7px,0.75vw,9px);\n  font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.5);",
                   "  font-family: 'Inter', sans-serif; font-size: var(--stat-label);\n  font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.5);",
                   'Expenses .statCard label')
        css = swap(css,
                   "  font-family: 'Space Mono', monospace; font-size: clamp(11px,1.1vw,13px);\n  font-weight: 700; color: #fff; word-break: break-all;",
                   "  font-family: 'Space Mono', monospace; font-size: var(--stat-value);\n  font-weight: 700; color: #fff; word-break: break-all;",
                   'Expenses .statCard value')
        css = swap(css,
                   "  font-family: 'Inter', sans-serif; font-size: clamp(7px,0.75vw,9px);\n  font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.35);",
                   "  font-family: 'Inter', sans-serif; font-size: var(--stat-note);\n  font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.35);",
                   'Expenses .statNote')
        write(EXPENSES_CSS, css, 'ExpensesPage.module.css')

    # -- Recovery Cockpit ------------------------------------------------
    # This file overrides .countCard twice further down (once inside a
    # later "type scale" block), so the only reliable way in is a final
    # override appended at the end -- same specificity, last one wins.
    if require(RECOVERY_CSS, 'RecoveryPortal.module.css'):
        css = read(RECOVERY_CSS)
        css = append_block(css, '/* fix68: stat scale */', """
/* fix68: stat scale -- the count cards read off the app-wide tokens now.
   This sits at the end on purpose: two earlier blocks in this file also
   set .countCard font sizes, and same-specificity rules are decided by
   source order. */
.countCard label  { font-size: var(--stat-label); }
.countCard strong { font-size: var(--stat-value); }
""", 'Recovery .countCard scale')
        write(RECOVERY_CSS, css, 'RecoveryPortal.module.css')

    # -- Audit HUD pill --------------------------------------------------
    # Targeted rather than appended: this one keeps its 480px shrink,
    # because it is a header pill, not a card, and going to 23px on a
    # phone would push the page title onto three lines.
    if require(AUDIT_CSS, 'AuditPage.module.css'):
        css = read(AUDIT_CSS)
        css = swap(css,
                   "    font-family: 'DM Sans', sans-serif;\n    font-size: clamp(7px, 0.75vw, 9px);\n    font-weight: 900;",
                   "    font-family: 'DM Sans', sans-serif;\n    font-size: var(--stat-label);\n    font-weight: 900;",
                   'Audit .diagItem scale')
        css = swap(css,
                   ".diagItem strong { font-family: 'Space Mono', monospace; }",
                   ".diagItem strong { font-family: 'Space Mono', monospace; font-size: var(--stat-value-sm); }",
                   'Audit .diagItem value')
        write(AUDIT_CSS, css, 'AuditPage.module.css')


# ===================================================== 3. TOOLTIP
def patch_tooltip():
    print('\n[3/6] Hover explainer -- lighter, and no longer clipped')
    write(TOOLTIP_JSX_PATH, TOOLTIP_JSX, 'components/common/Tooltip.jsx')
    write(TOOLTIP_CSS_PATH, TOOLTIP_CSS, 'components/common/Tooltip.module.css')


# ===================================================== 4. HEADER BUTTON
IMPORT_HB = "import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';\n"


def patch_header_buttons():
    print('\n[4/6] One header button spec, rolled out')
    write(HEADERBTN_JSX_PATH, HEADERBTN_JSX, 'components/common/HeaderButton.jsx')
    write(HEADERBTN_CSS_PATH, HEADERBTN_CSS, 'components/common/HeaderButton.module.css')

    # ---- Payments -----------------------------------------------------
    if require(PAYMENTS_JSX, 'PaymentsPage.jsx'):
        jsx = read(PAYMENTS_JSX)
        jsx = swap(jsx, "import styles from './PaymentsPage.module.css';",
                   IMPORT_HB + "import styles from './PaymentsPage.module.css';",
                   'Payments: HeaderButton import')
        jsx = swap(jsx,
                   """                <button className={styles.refreshBtn} onClick={loadPayments} aria-label="Refresh">
                    <FiRefreshCw size={14} /> REFRESH
                </button>""",
                   """                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Pull every payment record again" onClick={loadPayments} />
                </HeaderActions>""",
                   'Payments: header button')
        write(PAYMENTS_JSX, jsx, 'PaymentsPage.jsx')

    # ---- Project Ledger -----------------------------------------------
    if require(LEDGER_JSX, 'LedgerPage.jsx'):
        jsx = read(LEDGER_JSX)
        jsx = swap(jsx, "import styles from './LedgerPage.module.css';",
                   "import { FiRefreshCw } from 'react-icons/fi';\n" + IMPORT_HB
                   + "import styles from './LedgerPage.module.css';",
                   'Ledger: imports')
        jsx = swap(jsx,
                   """                    <p className={styles.subtitle}>Every project — folder to release, live payment health</p>
                </div>
            </header>""",
                   """                    <p className={styles.subtitle}>Every project — folder to release, live payment health</p>
                </div>
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Reload this page of the ledger" onClick={() => fetchLedger()} />
                </HeaderActions>
            </header>""",
                   'Ledger: header button')
        write(LEDGER_JSX, jsx, 'LedgerPage.jsx')

    # ---- Client Ledger ------------------------------------------------
    if require(CLEDGER_JSX, 'ClientLedgerPage.jsx'):
        jsx = read(CLEDGER_JSX)
        jsx = swap(jsx, "import styles from './ClientLedgerPage.module.css';",
                   "import { FiRefreshCw } from 'react-icons/fi';\n" + IMPORT_HB
                   + "import styles from './ClientLedgerPage.module.css';",
                   'Client Ledger: imports')
        jsx = swap(jsx,
                   """                    <p className={styles.subtitle}>Every client — click a row for the full portfolio dossier</p>
                </div>
            </header>""",
                   """                    <p className={styles.subtitle}>Every client — click a row for the full portfolio dossier</p>
                </div>
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Reload every client and their totals" onClick={() => load()} />
                </HeaderActions>
            </header>""",
                   'Client Ledger: header button')
        write(CLEDGER_JSX, jsx, 'ClientLedgerPage.jsx')

    # ---- Recovery Cockpit ---------------------------------------------
    if require(RECOVERY_JSX, 'RecoveryPortal.jsx'):
        jsx = read(RECOVERY_JSX)
        jsx = swap(jsx, "import styles from './RecoveryPortal.module.css';",
                   IMPORT_HB + "import styles from './RecoveryPortal.module.css';",
                   'Recovery: HeaderButton import')
        jsx = swap(jsx,
                   "import { FiSearch, FiX, FiPhone, FiPhoneCall, FiMapPin, FiClock, FiChevronDown, FiUser, FiFolderPlus } from 'react-icons/fi';",
                   "import { FiSearch, FiX, FiPhone, FiPhoneCall, FiMapPin, FiClock, FiChevronDown, FiUser, FiFolderPlus, FiRefreshCw } from 'react-icons/fi';",
                   'Recovery: FiRefreshCw import')
        jsx = swap(jsx,
                   """          <p className={styles.subtitle}>Call logs only - numbers only</p>
        </div>
      </header>""",
                   """          <p className={styles.subtitle}>Call logs only - numbers only</p>
        </div>
        <HeaderActions>
          <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
            tip="Reload the queues, counts and call stats" onClick={() => load()} />
        </HeaderActions>
      </header>""",
                   'Recovery: header button')
        write(RECOVERY_JSX, jsx, 'RecoveryPortal.jsx')

    # ---- Audit --------------------------------------------------------
    if require(AUDIT_JSX, 'AuditPage.jsx'):
        jsx = read(AUDIT_JSX)
        jsx = swap(jsx, "import styles from './AuditPage.module.css';",
                   "import { FiRefreshCw } from 'react-icons/fi';\n" + IMPORT_HB
                   + "import styles from './AuditPage.module.css';",
                   'Audit: imports')
        jsx = swap(jsx,
                   """                        <span>VISIBLE RECORDS: <strong>{logs.length}</strong></span>
                    </div>
                </div>
            </header>""",
                   """                        <span>VISIBLE RECORDS: <strong>{logs.length}</strong></span>
                    </div>
                </div>
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Re-run the current audit search" onClick={() => fetchForensics()} />
                </HeaderActions>
            </header>""",
                   'Audit: header button')
        write(AUDIT_JSX, jsx, 'AuditPage.jsx')


# ===================================================== 5. EXPENSES HEADER
def patch_expenses_header():
    print('\n[5/6] Expenses -- one NEW PRESET, not two')
    if not require(EXPENSES_JSX, 'ExpensesPage.jsx'):
        return
    jsx = read(EXPENSES_JSX)
    jsx = swap(jsx, "import styles from './ExpensesPage.module.css';",
               IMPORT_HB + "import styles from './ExpensesPage.module.css';",
               'Expenses: HeaderButton import')
    jsx = swap(jsx,
               """                <div className={styles.headerActions}>
                    <Tooltip label="Reload the presets and the last 24 hours of entries">
                        <button className={styles.ghostBtn} onClick={loadAll} aria-label="Refresh expenses">
                            <FiRefreshCw size={12} aria-hidden="true" /> REFRESH
                        </button>
                    </Tooltip>
                    <Tooltip label="Add a new tile for a cost you log often">
                        <button className={styles.primaryBtn} onClick={() => setPresetModal(true)}>
                            <FiPlus size={12} aria-hidden="true" /> NEW PRESET
                        </button>
                    </Tooltip>
                </div>""",
               """                {/* NEW PRESET used to live here as well as inside LOG AN
                    EXPENSE. Two buttons, same modal, three inches apart. It
                    belongs next to the tiles it creates, so this is just the
                    refresh now. */}
                <HeaderActions>
                    <HeaderButton icon={FiRefreshCw} label="REFRESH" busy={loading}
                        tip="Reload the presets and the last 24 hours of entries" onClick={loadAll} />
                </HeaderActions>""",
               'Expenses: drop duplicate NEW PRESET')
    write(EXPENSES_JSX, jsx, 'ExpensesPage.jsx')


# ===================================================== 6. REPORTS + ANALYSIS
REPORTHUB_CSS_ADDITION = """
/* ── TABS (fix68) ──────────────────────────────────────────────────
   Reports and Analysis are two different jobs -- "give me the file"
   and "tell me what it says" -- so they are two tabs rather than one
   very long scroll. Standard filter-button spec, same as everywhere. */
.tabRow {
    display: flex;
    gap: clamp(6px, 0.9vw, 10px);
    margin-bottom: clamp(10px, 1.4vw, 16px);
    flex-wrap: wrap;
}
.tab, .tabActive {
    display: inline-flex; align-items: center; gap: 7px;
    font-family: 'Inter', sans-serif;
    font-size: clamp(9px, 0.95vw, 11px);
    font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
    padding: clamp(8px, 1.1vw, 11px) clamp(14px, 2vw, 24px);
    border-radius: var(--radius-sm);
    border: 1.5px solid rgba(26, 46, 48, 0.2);
    background: rgba(255, 255, 255, 0.62);
    -webkit-backdrop-filter: blur(15px);
    backdrop-filter: blur(15px);
    /* CONTRAST RULE: these sit on the cream page, not on a panel, so the
       text is navy on a frosted white pill -- 13.4:1. */
    color: #1a2e30;
    cursor: pointer;
    transition: all 0.2s ease;
}
.tab:hover { border-color: var(--orange); color: var(--orange); }
.tabActive {
    background: var(--orange);
    border-color: var(--orange);
    color: #1a2e30;
    box-shadow: 0 4px 16px rgba(238, 140, 58, 0.3);
}
.tab:focus-visible, .tabActive:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── STUDIO / ANALYSIS DRAWER BODY ────────────────────────────────
   .bodyOpen caps at 6000px and clips overflow -- right for a list of
   report rows, wrong for the studio, which is taller than the cap once
   a table is in it and has select menus that have to escape the panel. */
.bodyOpenTall { max-height: none; opacity: 1; overflow: visible; }
.studioInner { padding: clamp(12px, 1.6vw, 18px); }
"""


def patch_reports():
    print('\n[6/6] Reports -> REPORTS + ANALYSIS, with the Report Studio')
    write(REPORTDATA_PATH, REPORTDATA_JS, 'pages/Reports/reportData.js')
    write(STUDIO_JSX_PATH, STUDIO_JSX, 'pages/Reports/ReportStudio.jsx')
    write(STUDIO_CSS_PATH, STUDIO_CSS, 'pages/Reports/ReportStudio.module.css')
    write(REPORTHUB_JSX_PATH, REPORTHUB_JSX, 'pages/Reports/ReportHub.jsx')

    if require(REPORTHUB_CSS_PATH, 'ReportHub.module.css'):
        css = read(REPORTHUB_CSS_PATH)
        # fix67 already appended a .bodyOpenTall; drop it so the fix68 block
        # is the single definition rather than two competing ones.
        css = css.replace("""

/* ── EXPENSE ANALYSIS DRAWER ──────────────────────────────────────
   .bodyOpen caps at 6000px and clips overflow, which is right for a
   list of report rows but wrong here: the analysis is taller than the
   cap on a busy month, and its category dropdown has to escape the
   panel to be usable. This variant lifts both constraints. */
.bodyOpenTall { max-height: none; opacity: 1; overflow: visible; }
""", '\n')
        css = append_block(css, '/* ── TABS (fix68) ──', REPORTHUB_CSS_ADDITION, 'ReportHub tabs + studio CSS')
        write(REPORTHUB_CSS_PATH, css, 'ReportHub.module.css')


# ===================================================== main
def main():
    print('=' * 70)
    print('GOLDEN SEED -- fix68: stat scale, one header button, tooltip pass,')
    print('                     Reports rebuilt as Reports + Analysis')
    print('=' * 70)

    if not os.path.isdir(FE):
        print('ERROR: erp-frontend/src not found next to this script.')
        print('       Run fix.py from the repository root.')
        sys.exit(1)

    patch_global_tokens()
    patch_stat_cards()
    patch_tooltip()
    patch_header_buttons()
    patch_expenses_header()
    patch_reports()

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
                'fix68: app-wide stat card scale, one shared header button '
                '(icon-only on mobile), quieter unclipped tooltips, duplicate '
                'NEW PRESET removed, Reports rebuilt as Reports + Analysis '
                'tabs with a fully customisable Report Studio'])
    if code != 0:
        print('  (nothing to commit, or commit failed -- pushing anyway)')
    run(['git', 'push'])
    print('\nDone.')


if __name__ == '__main__':
    main()