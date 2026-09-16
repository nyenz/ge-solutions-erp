#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOLDEN SEED -- fix67
=====================================================================
DESIGN COHERENCE PASS: Payments -> Portfolio -> Expenses, plus the
Analysis relocation.

1. PORTFOLIO MONEY STRIP
   The five stat boxes on the Client Dossier now use the Payment
   Records .sumCard spec verbatim: navy gradient (160deg #1c3335 ->
   #213E40), 1.5px orange hairline border, 10px radius, mono value,
   and a third "note" line under the figure -- the exact cards the
   brief circled in blue. Colour variants follow Payments' own idiom
   (border + label + value all take the accent colour) instead of the
   old pastel-text-on-white-border treatment.

2. EXPENSES PAGE OVERHAUL
   Rebuilt against the updated Portfolio page as the single reference:
     - same container tokens, padding, gap rhythm and Inter type stack
     - same frosted-glass page header and same header button spec
     - HardwarePanel -> CollapsibleSection + CornerDecor (the exact
       components Portfolio uses), with the same corner badge
     - same .ledgerTable treatment (header bar, 3px orange rule,
       orange left-border on row hover, group/tag/mono idioms)
     - a money strip of the new stat cards at the top
     - preset tiles are no longer 84px slabs: they are ordinary
       buttons, sized to the Portfolio header button spec

3. ANALYSIS MOVED TO REPORTS
   The whole Director analysis block (period toggles, by-category,
   by-staff, spending-over-time, and the full expense search) is
   lifted out of Expenses into its own component and mounted as an
   "EXPENSE ANALYSIS" drawer on the Report Hub. No behaviour lost --
   same service calls, same filters, same 100-row truncation flag.

Run:  python fix.py
Auto: git add -A / commit / push
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, 'erp-frontend', 'src')

PORTFOLIO_CSS = os.path.join(FE, 'pages', 'Clients', 'ClientPortfolioPage.module.css')
PORTFOLIO_JSX = os.path.join(FE, 'pages', 'Clients', 'ClientPortfolioPage.jsx')
EXPENSES_JSX = os.path.join(FE, 'pages', 'Financials', 'ExpensesPage.jsx')
EXPENSES_CSS = os.path.join(FE, 'pages', 'Financials', 'ExpensesPage.module.css')
ANALYSIS_JSX = os.path.join(FE, 'pages', 'Reports', 'ExpenseAnalysis.jsx')
ANALYSIS_CSS = os.path.join(FE, 'pages', 'Reports', 'ExpenseAnalysis.module.css')
REPORTHUB_JSX = os.path.join(FE, 'pages', 'Reports', 'ReportHub.jsx')
REPORTHUB_CSS = os.path.join(FE, 'pages', 'Reports', 'ReportHub.module.css')

CHANGED = []
SKIPPED = []


# ---------------------------------------------------------------- helpers
def read(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def write(path, text, label):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)
    CHANGED.append(label)
    print('  [write] ' + label)


def require(path, label):
    if not os.path.isfile(path):
        print('  [MISS ] ' + label + ' -- not found at ' + path)
        SKIPPED.append(label)
        return False
    return True


def swap(text, old, new, label):
    """Exact-substring replace. Idempotent: a no-op if `new` is already in."""
    if new in text:
        print('  [ skip] ' + label + ' (already applied)')
        return text
    if old not in text:
        print('  [WARN ] ' + label + ' -- anchor not found, left alone')
        SKIPPED.append(label)
        return text
    print('  [patch] ' + label)
    return text.replace(old, new, 1)


def between(text, start_anchor, end_anchor, new_block, label):
    """Replace everything from start_anchor up to (not including) end_anchor."""
    if new_block.strip() and new_block.strip() in text:
        print('  [ skip] ' + label + ' (already applied)')
        return text
    i = text.find(start_anchor)
    j = text.find(end_anchor)
    if i == -1 or j == -1 or j < i:
        print('  [WARN ] ' + label + ' -- anchors not found, left alone')
        SKIPPED.append(label)
        return text
    print('  [patch] ' + label)
    return text[:i] + new_block + text[j:]


def run(cmd):
    print('$ ' + ' '.join(cmd))
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


# ================================================================== 1. PORTFOLIO
MONEY_STRIP_CSS = """/* -- MONEY STRIP -- these are the Payment Records summary cards, lifted
   verbatim: same navy gradient, same 1.5px orange hairline, same 10px
   radius, same Space Mono figure, same muted third line. The old build
   used the lighter #3a5a5c panel gradient and a white 10% border, which
   made the dossier read as a different product to /payments. Colour
   variants follow the Payments idiom too -- the accent colour lands on
   the border, the label AND the figure, rather than a pastel value on a
   near-invisible border. */
.moneyStrip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: clamp(10px, 1.4vw, 16px);
}
.statCard {
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid var(--orange-border);
  border-radius: var(--radius);
  padding: clamp(12px, 1.5vw, 18px);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.statClickable { cursor: pointer; transition: border-color 0.2s ease, box-shadow 0.2s ease; }
.statClickable:hover { border-color: var(--orange); box-shadow: 0 0 0 1px rgba(238,140,58,0.18); }
.statClickable:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.statCard label {
  font-family: 'Inter', sans-serif;
  font-size: clamp(7px, 0.75vw, 9px);
  font-weight: 900; letter-spacing: 1px; text-transform: uppercase;
  color: rgba(255,255,255,0.5);
}
.statCard strong {
  font-family: 'Space Mono', monospace;
  font-size: clamp(11px, 1.1vw, 13px);
  font-weight: 700; color: #fff; word-break: break-all;
}
.statTextValue { font-size: clamp(11px, 1.1vw, 13px); }
.statRed   { border-color: rgba(239,68,68,0.55); }
.statRed   label, .statRed   strong { color: #ef4444; }
.statGreen { border-color: rgba(34,197,94,0.55); }
.statGreen label, .statGreen strong { color: #22c55e; }
.statAmber { border-color: rgba(238,140,58,0.55); }
.statAmber label, .statAmber strong { color: var(--orange); }
.statNote {
  font-family: 'Inter', sans-serif;
  font-size: clamp(7px, 0.75vw, 9px);
  font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  color: rgba(255,255,255,0.35);
}

"""


def patch_portfolio():
    print('\n[1/4] Client Dossier money strip -> Payment Records card spec')
    if require(PORTFOLIO_CSS, 'ClientPortfolioPage.module.css'):
        css = read(PORTFOLIO_CSS)
        css = between(css, '/* -- MONEY STRIP -- */', '/* -- TABLE -- */',
                      MONEY_STRIP_CSS, 'portfolio .statCard -> .sumCard spec')
        write(PORTFOLIO_CSS, css, 'ClientPortfolioPage.module.css')

    if not require(PORTFOLIO_JSX, 'ClientPortfolioPage.jsx'):
        return
    jsx = read(PORTFOLIO_JSX)

    # The Payments cards carry a third muted line ("33 records"). The dossier
    # cards had only two, so they were visibly shorter than their siblings on
    # /payments. Each one now states what its figure is counted over.
    jsx = swap(
        jsx,
        '<label>TOTAL OWED</label><strong>UGX {fmt(totals.owed)}</strong>',
        '<label>TOTAL OWED</label><strong>UGX {fmt(totals.owed)}</strong>\n'
        '            <span className={styles.statNote}>'
        '{totals.count} {totals.count === 1 ? \'project\' : \'projects\'}</span>',
        'TOTAL OWED note line')

    jsx = swap(
        jsx,
        '<label>TOTAL PAID</label><strong>UGX {fmt(totals.paid)}</strong>',
        '<label>TOTAL PAID</label><strong>UGX {fmt(totals.paid)}</strong>\n'
        '            <span className={styles.statNote}>'
        '{(Number(totals.owed) + Number(totals.paid)) > 0'
        ' ? Math.round((Number(totals.paid) / (Number(totals.owed) + Number(totals.paid))) * 100)'
        ' : 0}% of billed</span>',
        'TOTAL PAID note line')

    jsx = swap(
        jsx,
        '<label>STORAGE FEES</label><strong>UGX {fmt(totals.storage)}</strong>',
        '<label>STORAGE FEES</label><strong>UGX {fmt(totals.storage)}</strong>\n'
        '            <span className={styles.statNote}>receivables accrued</span>',
        'STORAGE FEES note line')

    jsx = swap(
        jsx,
        '<label>PROJECTS</label><strong>{totals.count}</strong>',
        '<label>PROJECTS</label><strong>{totals.count}</strong>\n'
        '            <span className={styles.statNote}>in this portfolio</span>',
        'PROJECTS note line')

    jsx = swap(
        jsx,
        '<label>OWNERSHIP</label><strong className={styles.statTextValue}>'
        '{totals.solo} SOLO / {totals.joint} JOINT</strong>',
        '<label>OWNERSHIP</label><strong className={styles.statTextValue}>'
        '{totals.solo} SOLO / {totals.joint} JOINT</strong>\n'
        '            <span className={styles.statNote}>tenure split</span>',
        'OWNERSHIP note line')

    write(PORTFOLIO_JSX, jsx, 'ClientPortfolioPage.jsx')


# ================================================================== 2. EXPENSES CSS
EXPENSES_CSS_BODY = r"""/* PATH: erp-frontend/src/pages/Financials/ExpensesPage.module.css */
/* EXPENSES v3 -- rebuilt on the Client Dossier (ClientPortfolioPage) as the
   reference, which is itself now pixel-matched to Payment Records. Every
   token below is the dossier's: same container padding and gap rhythm, same
   Inter stack, same frosted header, same button spec, same stat card, same
   ledger table. The page no longer carries its own DM Sans / HardwarePanel /
   84px-tile dialect. The Director analysis styles that used to live here
   (period toggles, bars, time series, search filters, category dropdown)
   moved out with the analysis itself -- see Reports/ExpenseAnalysis.module.css. */
.container {
  --orange: #EE8C3A; --orange-dim: rgba(238,140,58,0.18); --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --green: #10b981; --amber: #f59e0b;
  --radius: 10px; --radius-sm: 6px;
  max-width: 1400px; width: 100%; margin: 0 auto;
  padding: clamp(12px,2vh,22px) clamp(12px,2vw,24px) 28px;
  font-family: 'Inter', sans-serif; color: #fff;
  display: flex; flex-direction: column; gap: clamp(7px,1.1vw,14px);
  box-sizing: border-box;
}

/* -- HEADER -- verbatim frosted-glass treatment from the dossier -- */
.pageHeader {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
  gap: clamp(8px,1.2vw,14px); border-left: clamp(3px,0.4vw,5px) solid var(--orange);
  padding: clamp(8px,1.2vw,14px) clamp(14px,1.8vw,22px);
  background: rgba(255,255,255,0.62); border-radius: 0 12px 12px 0;
  backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
.title { font-family: 'Cinzel', serif; color: var(--navy-deep); font-size: clamp(18px,2.5vw,24px); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; line-height: 1.1; margin: 0; }
.subtitle { color: #64748b; font-size: clamp(9px,0.9vw,11px); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin: 0; }
.headerActions { display: flex; align-items: center; gap: clamp(6px,0.9vw,10px); flex-wrap: wrap; }

/* -- BUTTON SPEC -- identical to the dossier's .backBtn / .editBtn family.
   Every button on this page is one of these three, so nothing here is
   bigger or louder than its equivalent on the dossier. -- */
.ghostBtn, .primaryBtn, .presetBtn, .presetBtnOther, .presetBtnNew {
  font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  text-transform: uppercase; letter-spacing: 1.5px;
  padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.18); background: rgba(26,46,48,0.75); color: rgba(255,255,255,0.85);
  cursor: pointer; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;
}
.ghostBtn:hover, .presetBtn:hover, .presetBtnOther:hover {
  background: rgba(238,140,58,0.12); color: var(--orange); border-color: var(--orange);
}
.primaryBtn, .presetBtnNew { background: var(--orange); color: #1a2e30; border-color: var(--orange); }
.primaryBtn:hover, .presetBtnNew:hover { background: #d97a2b; border-color: #d97a2b; }
.ghostBtn:disabled, .primaryBtn:disabled { opacity: 0.5; cursor: wait; }
.ghostBtn:focus-visible, .primaryBtn:focus-visible,
.presetBtn:focus-visible, .presetBtnOther:focus-visible, .presetBtnNew:focus-visible {
  outline: 2px solid var(--orange); outline-offset: 2px;
}
/* OTHER is the "not one of the tiles" escape hatch, so it stays dashed --
   the one deliberate difference, and it is a border style, not a size. */
.presetBtnOther { border-style: dashed; }

/* -- PANEL CORNER BADGE -- the dossier's, unchanged -- */
.panelCornerBadge {
  font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px;
  color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 20px; padding: 4px 12px; text-transform: uppercase; flex-shrink: 0;
}

/* -- MONEY STRIP -- the Payment Records / dossier stat card, same spec -- */
.moneyStrip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: clamp(10px, 1.4vw, 16px);
}
.statCard {
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid var(--orange-border);
  border-radius: var(--radius);
  padding: clamp(12px, 1.5vw, 18px);
  display: flex; flex-direction: column; gap: 4px;
}
.statCard label {
  font-family: 'Inter', sans-serif; font-size: clamp(7px,0.75vw,9px);
  font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.5);
}
.statCard strong {
  font-family: 'Space Mono', monospace; font-size: clamp(11px,1.1vw,13px);
  font-weight: 700; color: #fff; word-break: break-all;
}
.statNote {
  font-family: 'Inter', sans-serif; font-size: clamp(7px,0.75vw,9px);
  font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.35);
}
.statAmber { border-color: rgba(238,140,58,0.55); }
.statAmber label, .statAmber strong { color: var(--orange); }
.statGreen { border-color: rgba(34,197,94,0.55); }
.statGreen label, .statGreen strong { color: #22c55e; }

/* -- PRESET ROW -- was a grid of 84px slabs, which made "log an expense"
   the visually heaviest thing in the app. They are buttons now, flowing in
   a wrapped row at the dossier's button size. -- */
.presetRow { display: flex; flex-wrap: wrap; align-items: center; gap: clamp(6px,0.9vw,10px); }

/* Plain-English note at the top of a panel, for a rule that would otherwise
   only be discoverable by hovering something. */
.panelHint {
  display: flex; align-items: center; gap: 7px; margin: 0;
  font-family: 'Inter', sans-serif; font-size: clamp(10px,1vw,11px); font-weight: 600; line-height: 1.4;
  color: rgba(244,242,239,0.62);
}
.panelHint svg { color: var(--orange); flex-shrink: 0; }

/* Visually hidden, still read out by screen readers -- for the actions
   column header, which has no visible text. */
.srOnly {
  position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}

/* -- TABLE -- the dossier's .ledgerTable, character for character -- */
.tableScroll { overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none; }
.tableScroll::-webkit-scrollbar { display: none; }
.ledgerTable { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 680px; }
.ledgerTable thead th {
  background: #162a2c; color: var(--orange); font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  letter-spacing: 2px; text-transform: uppercase; text-align: left; padding: clamp(9px,1.3vw,14px) clamp(10px,1.5vw,16px);
  border-bottom: 3px solid var(--orange); white-space: nowrap;
}
.ledgerTable thead th:first-child { border-radius: 6px 0 0 0; }
.ledgerTable thead th:last-child { border-radius: 0 6px 0 0; }
.ledgerTable tbody td { padding: clamp(9px,1.2vw,13px) clamp(10px,1.5vw,16px); border-bottom: 1px solid rgba(255,255,255,0.06); vertical-align: middle; color: #fff; font-size: clamp(10px,1.05vw,12px); }
.ledgerTable tbody tr.row { transition: background 0.15s; border-left: 3px solid transparent; }
.ledgerTable tbody tr.row:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.mono { font-family: 'Space Mono', monospace; }
.dateCell { white-space: nowrap; color: rgba(255,255,255,0.6); font-family: 'Space Mono', monospace; font-size: clamp(9px,0.95vw,11px); }
.moneyCell { font-family: 'Space Mono', monospace; font-weight: 700; white-space: nowrap; color: #fca5a5; }
.metaCell { color: rgba(255,255,255,0.7); white-space: nowrap; }
.notesCell { color: rgba(255,255,255,0.55); font-style: italic; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notesCell span { display: inline-block; max-width: 100%; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: bottom; }
.noNote { color: rgba(244,242,239,0.45); font-style: normal; }

/* .emptyCell sits INSIDE a dark panel already -- a card here would be a card
   in a card, so only the text colour is set (cream, never white-on-cream). */
.emptyCell {
  text-align: center; padding: clamp(20px,4vw,40px) 16px;
  font-family: 'Space Mono', monospace; color: rgba(244,242,239,0.68);
  font-size: 11px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
}

/* -- one-word tags -- the dossier's .tag idiom: coloured text, no chip
   background, so they never compete with the money figures -- */
.categoryTag { font-size: 10px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: var(--orange); }
.editedBadge { margin-left: 8px; font-size: 9px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: var(--amber); cursor: help; }
.spentByTag {
  display: block; margin-top: 3px;
  color: rgba(244,242,239,0.66); font-size: 9px; font-weight: 800;
  letter-spacing: 1px; text-transform: uppercase; white-space: normal; cursor: help;
}
.lockedTag {
  display: inline-flex; align-items: center; gap: 4px;
  color: rgba(244,242,239,0.62); font-size: 9px; font-weight: 800;
  letter-spacing: 1px; text-transform: uppercase; white-space: nowrap;
}

.rowActions { display: flex; align-items: center; gap: 6px; }
.editIconBtn, .deleteIconBtn {
  width: 26px; height: 26px; border-radius: 5px; border: 1.5px solid transparent;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background 0.15s, border-color 0.15s, color 0.15s;
}
/* PALETTE: this was blue (#3b82f6). Blue appears nowhere else in the app --
   the palette is orange / navy / red / green / amber / violet / cyan. */
.editIconBtn { background: rgba(238,140,58,0.15); color: var(--orange); }
.editIconBtn:hover { background: rgba(238,140,58,0.3); border-color: var(--orange); }
.deleteIconBtn { background: rgba(239,68,68,0.15); color: var(--red); }
.deleteIconBtn:hover { background: rgba(239,68,68,0.3); border-color: var(--red); }
.editIconBtn:disabled, .deleteIconBtn:disabled { opacity: 0.4; cursor: not-allowed; }
.editIconBtn:focus-visible, .deleteIconBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
/* A row mid-delete dims so the click clearly registered. */
.rowBusy { opacity: 0.45; pointer-events: none; }

/* -- AMOUNT INPUT (triggers native numeric keypad on mobile) -- */
.amountInput {
  width: 100%; height: 56px; font-size: 28px; font-weight: 900; text-align: center;
  border-radius: var(--radius-sm); border: 1.5px solid rgba(255,255,255,0.15);
  background: rgba(0,0,0,0.25); color: #fff; font-family: 'Space Mono', monospace;
  box-sizing: border-box;
}
.amountInput:focus { outline: none; border-color: var(--orange); }

/* -- RESPONSIVE -- same breakpoints the dossier uses -- */
@media (max-width: 700px) {
  .ledgerTable { min-width: 600px; }
  .ledgerTable thead th { font-size: 7px; letter-spacing: 1px; }
  .pageHeader { flex-direction: column; align-items: flex-start; gap: 12px; border-radius: 0; }
  .headerActions { width: 100%; }
  .ghostBtn { flex: 1; justify-content: center; }
}
@media (max-width: 480px) {
  .ledgerTable tbody td { padding: 8px; }
  .presetRow { gap: 6px; }
}
"""


# ================================================================== 3. EXPENSES JSX
EXPENSES_JSX_BODY = r"""// PATH: erp-frontend/src/pages/Financials/ExpensesPage.jsx
// EXPENSES v3 -- see ExpensesPage.module.css for the design note. Structurally
// this page is now the Client Dossier: frosted header, stat strip, then
// CollapsibleSection panels carrying CornerDecor and a corner badge. The
// Director analysis block that used to hang off the ANALYSIS toggle here now
// lives on the Report Hub (Reports/ExpenseAnalysis.jsx) -- this page is purely
// "log cash going out, and fix it within 24h".
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    FiTrendingDown, FiPlus, FiRefreshCw, FiEdit2, FiTrash2,
    FiClock, FiLock, FiInfo
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import expenseService from '../../services/expenseService';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import { LoadingRow } from '../../components/common/LoadingState';
import { Tooltip, IconButton, Term } from '../../components/common/Tooltip';
import { GLOSSARY } from '../../components/common/glossary';
import { useToasts, useConfirm } from '../../components/common/useFeedback';
import { ToastStack, ConfirmDialog } from '../../components/common/Feedback';
import styles from './ExpensesPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const EDIT_WINDOW_HOURS = 24;

const isStillEditable = (createdAt) => {
    if (!createdAt) return false;
    const ageMs = Date.now() - new Date(createdAt).getTime();
    return ageMs < EDIT_WINDOW_HOURS * 60 * 60 * 1000;
};

const hoursLeft = (createdAt) => {
    const ageMs = Date.now() - new Date(createdAt).getTime();
    const remaining = EDIT_WINDOW_HOURS * 60 * 60 * 1000 - ageMs;
    return Math.max(0, Math.ceil(remaining / (60 * 60 * 1000)));
};

const ExpensesPage = () => {
    const { user } = useAuth();
    const isDirector = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';

    const { toasts, toast, dismissToast } = useToasts();
    const { confirmState, confirm, handleAnswer } = useConfirm();

    const [presets, setPresets] = useState([]);
    const [recent, setRecent] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);

    // F3: the 24h edit window used to be judged only at render time, so a row
    // kept its edit button until someone reloaded the page. This tick makes
    // the row flip to LOCKED on its own, within a minute of the window closing.
    const [, setClockTick] = useState(0);
    useEffect(() => {
        const id = setInterval(() => setClockTick(t => t + 1), 60 * 1000);
        return () => clearInterval(id);
    }, []);

    const loadAll = useCallback(async () => {
        setLoading(true);
        try {
            const [presetData, recentData, categoryData] = await Promise.all([
                expenseService.getPresets(),
                expenseService.getRecent(EDIT_WINDOW_HOURS),
                expenseService.getCategories(),
            ]);
            setPresets(presetData || []);
            setRecent(recentData || []);
            setCategories(categoryData || []);
        } catch {
            toast('Could not load expenses. Check your connection.', 'error');
        } finally {
            setLoading(false);
        }
    }, [toast]);

    useEffect(() => { loadAll(); }, [loadAll]);

    // Every category ever used -- preset tiles plus anything typed under OTHER.
    // Feeds the shared datalist behind both "type it yourself" fields.
    const knownCategories = useMemo(() => {
        const names = new Set();
        presets.forEach(p => p.name && names.add(p.name));
        categories.forEach(c => c && names.add(c));
        return [...names].sort((a, b) => a.localeCompare(b));
    }, [presets, categories]);

    // The stat strip reads straight off the 24h window already in memory --
    // no extra call, and it agrees with the table underneath it by construction.
    const dayTotal = useMemo(
        () => recent.reduce((sum, e) => sum + Number(e.amount || 0), 0),
        [recent],
    );
    const editableCount = useMemo(
        () => recent.filter(e => isStillEditable(e.createdAt)).length,
        [recent],
    );

    // -- LOG MODAL (tap a preset, or OTHER) --------------------------
    const [logModal, setLogModal] = useState({ open: false, presetName: '', isOther: false });
    const [logCategory, setLogCategory] = useState('');
    const [logAmount, setLogAmount] = useState('');
    const [logNote, setLogNote] = useState('');
    const [logSpentBy, setLogSpentBy] = useState('');
    const [logging, setLogging] = useState(false);

    const openLogModal = (presetName) => {
        setLogModal({ open: true, presetName, isOther: false });
        setLogCategory(presetName);
        setLogAmount('');
        setLogNote('');
        setLogSpentBy('');
    };
    const openOtherModal = () => {
        setLogModal({ open: true, presetName: '', isOther: true });
        setLogCategory('');
        setLogAmount('');
        setLogNote('');
        setLogSpentBy('');
    };
    const closeLogModal = () => setLogModal({ open: false, presetName: '', isOther: false });

    const submitLog = async () => {
        if (logModal.isOther && !logCategory.trim()) { toast('What is this expense for?', 'error'); return; }
        if (!logAmount || Number(logAmount) <= 0) { toast('Enter an amount.', 'error'); return; }
        setLogging(true);
        try {
            await expenseService.create({
                category: (logModal.isOther ? logCategory : logModal.presetName).trim(),
                amount: Number(logAmount),
                note: logNote,
                spentBy: logSpentBy,
            });
            closeLogModal();
            await loadAll();
            toast('Expense logged.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not log this expense.', 'error');
        } finally {
            setLogging(false);
        }
    };

    // -- NEW PRESET MODAL ------------------------------------------
    const [presetModal, setPresetModal] = useState(false);
    const [newPresetName, setNewPresetName] = useState('');
    const [savingPreset, setSavingPreset] = useState(false);

    const submitPreset = async () => {
        if (!newPresetName.trim()) { toast('Enter a name for this preset.', 'error'); return; }
        setSavingPreset(true);
        try {
            await expenseService.createPreset(newPresetName.trim());
            setPresetModal(false);
            setNewPresetName('');
            await loadAll();
            toast('Preset added.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not create this preset.', 'error');
        } finally {
            setSavingPreset(false);
        }
    };

    // -- EDIT MODAL (within 24h only) --------------------------------
    const [editModal, setEditModal] = useState({ open: false, expense: null });
    const [editCategory, setEditCategory] = useState('');
    const [editAmount, setEditAmount] = useState('');
    const [editNote, setEditNote] = useState('');
    const [editSpentBy, setEditSpentBy] = useState('');
    const [saving, setSaving] = useState(false);

    const openEdit = (expense) => {
        setEditModal({ open: true, expense });
        setEditCategory(expense.category);
        setEditAmount(String(expense.amount));
        setEditNote(expense.note || '');
        setEditSpentBy(expense.spentBy || '');
    };

    const submitEdit = async () => {
        if (!editAmount || Number(editAmount) <= 0) { toast('Enter an amount.', 'error'); return; }
        setSaving(true);
        try {
            await expenseService.update(editModal.expense.id, {
                category: editCategory.trim(),
                amount: Number(editAmount),
                note: editNote,
                spentBy: editSpentBy,
            });
            setEditModal({ open: false, expense: null });
            await loadAll();
            toast('Expense updated.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not save this edit.', 'error');
        } finally {
            setSaving(false);
        }
    };

    // F2: deletingId guards against a double-click firing two deletes.
    const [deletingId, setDeletingId] = useState(null);

    const handleDelete = async (expense) => {
        if (deletingId) return;
        const ok = await confirm(
            'DELETE EXPENSE',
            `Delete the ${expense.category} entry of UGX ${fmt(expense.amount)}? This cannot be undone.`,
            'danger',
        );
        if (!ok) return;
        setDeletingId(expense.id);
        try {
            await expenseService.remove(expense.id);
            await loadAll();
            toast('Entry deleted.', 'warn');
        } catch {
            toast('Could not delete this entry.', 'error');
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Expenses</h1>
                    <p className={styles.subtitle}>Log any cash that leaves the office</p>
                </div>
                <div className={styles.headerActions}>
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
                </div>
            </header>

            {/* Shared autocomplete source for every "type it yourself" category field */}
            <datalist id="expense-categories">
                {knownCategories.map(c => <option key={c} value={c} />)}
            </datalist>

            {/* STAT STRIP -- same card spec as the dossier and Payment Records */}
            <div className={styles.moneyStrip}>
                <div className={`${styles.statCard} ${styles.statAmber}`}>
                    <label>SPENT (LAST 24H)</label>
                    <strong>UGX {fmt(dayTotal)}</strong>
                    <span className={styles.statNote}>{recent.length} {recent.length === 1 ? 'entry' : 'entries'}</span>
                </div>
                <div className={`${styles.statCard} ${styles.statGreen}`}>
                    <label>STILL EDITABLE</label>
                    <strong>{editableCount}</strong>
                    <span className={styles.statNote}>of {recent.length} in window</span>
                </div>
                <div className={styles.statCard}>
                    <label>PRESETS</label>
                    <strong>{presets.length}</strong>
                    <span className={styles.statNote}>one-tap categories</span>
                </div>
                <div className={styles.statCard}>
                    <label>CATEGORIES USED</label>
                    <strong>{knownCategories.length}</strong>
                    <span className={styles.statNote}>all time</span>
                </div>
            </div>

            {/* LOG AN EXPENSE -- ONE TAP */}
            <CollapsibleSection
                icon={<FiTrendingDown aria-hidden="true" />}
                title="LOG AN EXPENSE"
                right={<span className={styles.panelCornerBadge}>{presets.length} {presets.length === 1 ? 'PRESET' : 'PRESETS'}</span>}
            >
                <p className={styles.panelHint}>
                    <FiInfo size={12} aria-hidden="true" />
                    Tap a category to log it. Anything without a tile goes under OTHER.
                </p>
                <div className={styles.presetRow}>
                    {presets.map(p => (
                        <Tooltip key={p.id} label={`Log a ${p.name} expense`}>
                            <button className={styles.presetBtn} onClick={() => openLogModal(p.name)}>
                                {p.name.toUpperCase()}
                            </button>
                        </Tooltip>
                    ))}
                    <Tooltip label="Anything with no tile -- you type what it was for">
                        <button className={styles.presetBtnOther} onClick={openOtherModal}>
                            OTHER
                        </button>
                    </Tooltip>
                    <Tooltip label="Add a new tile for a cost you log often">
                        <button className={styles.presetBtnNew} onClick={() => setPresetModal(true)}>
                            <FiPlus size={12} aria-hidden="true" /> NEW PRESET
                        </button>
                    </Tooltip>
                </div>
            </CollapsibleSection>

            {/* RECENT ENTRIES -- EDITABLE WITHIN 24H */}
            <CollapsibleSection
                icon={<FiClock aria-hidden="true" />}
                title="RECENT ENTRIES (LAST 24H)"
                right={<span className={styles.panelCornerBadge}>{recent.length} {recent.length === 1 ? 'ENTRY' : 'ENTRIES'}</span>}
            >
                <p className={styles.panelHint}>
                    <FiInfo size={12} aria-hidden="true" />
                    You can edit your own entries for {EDIT_WINDOW_HOURS} hours. After that they lock.
                </p>
                <div className={styles.tableScroll}>
                    <table className={styles.ledgerTable}>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Category</th>
                                <th>Amount (UGX)</th>
                                <th>Logged By</th>
                                <th>Note</th>
                                <th><span className={styles.srOnly}>Actions</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <LoadingRow colSpan={6} label="LOADING EXPENSES..." />
                            ) : recent.length === 0 ? (
                                <tr><td colSpan="6" className={styles.emptyCell}>NO EXPENSES LOGGED IN THE LAST 24 HOURS</td></tr>
                            ) : recent.map(e => {
                                const editable = isStillEditable(e.createdAt);
                                return (
                                    <tr key={e.id} className={`${styles.row} ${deletingId === e.id ? styles.rowBusy : ''}`}>
                                        <td className={styles.dateCell}>
                                            {new Date(e.createdAt).toLocaleString()}
                                        </td>
                                        <td>
                                            <Tooltip label={GLOSSARY.CATEGORY}>
                                                <span className={styles.categoryTag}>{e.category}</span>
                                            </Tooltip>
                                            {e.editedAt && (
                                                <Tooltip label={GLOSSARY.EDITED}>
                                                    <span className={styles.editedBadge}>EDITED</span>
                                                </Tooltip>
                                            )}
                                        </td>
                                        <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                        <td className={styles.metaCell}>
                                            {e.recordedBy}
                                            {e.spentBy && e.spentBy !== e.recordedBy && (
                                                <Tooltip label={GLOSSARY.SPENT_BY}>
                                                    <span className={styles.spentByTag}>SPENT: {e.spentBy}</span>
                                                </Tooltip>
                                            )}
                                        </td>
                                        <td className={styles.notesCell}>
                                            {e.note
                                                ? <Tooltip label={e.note}><span>{e.note}</span></Tooltip>
                                                : <span className={styles.noNote}>---</span>}
                                        </td>
                                        <td>
                                            <div className={styles.rowActions}>
                                                {editable ? (
                                                    <IconButton
                                                        tip={`Edit this entry -- ${hoursLeft(e.createdAt)}h left before it locks`}
                                                        icon={FiEdit2}
                                                        className={styles.editIconBtn}
                                                        onClick={() => openEdit(e)}
                                                    />
                                                ) : (
                                                    <Term tip={GLOSSARY.LOCKED} className={styles.lockedTag}>
                                                        <FiLock size={10} aria-hidden="true" /> LOCKED
                                                    </Term>
                                                )}
                                                {isDirector && (
                                                    <IconButton
                                                        tip="Delete this entry permanently (Directors only)"
                                                        icon={FiTrash2}
                                                        className={styles.deleteIconBtn}
                                                        onClick={() => handleDelete(e)}
                                                        disabled={deletingId === e.id}
                                                    />
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </CollapsibleSection>

            {/* LOG EXPENSE MODAL */}
            <HardwareModal isOpen={logModal.open} onClose={closeLogModal}
                title={logModal.isOther ? 'LOG EXPENSE -- OTHER' : `LOG EXPENSE -- ${logModal.presetName.toUpperCase()}`}>
                {logModal.isOther && (
                    <div className={modalStyles.modalField}>
                        <label className={modalStyles.modalLabel}>WHAT IS THIS EXPENSE FOR?</label>
                        <input
                            type="text"
                            list="expense-categories"
                            className={modalStyles.modalInput}
                            placeholder="e.g. Courier fee"
                            value={logCategory}
                            onChange={e => setLogCategory(e.target.value)}
                        />
                    </div>
                )}
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT (UGX)</label>
                    <input
                        type="number"
                        inputMode="decimal"
                        className={styles.amountInput}
                        placeholder="0"
                        autoFocus
                        value={logAmount}
                        onChange={e => setLogAmount(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Any extra detail..."
                        value={logNote}
                        onChange={e => setLogNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>WHO ACTUALLY SPENT THIS (IF NOT YOU)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Defaults to you"
                        value={logSpentBy}
                        onChange={e => setLogSpentBy(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={closeLogModal}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitLog} loading={logging} icon={FiPlus}>
                        SAVE EXPENSE
                    </HardwareButton>
                </div>
            </HardwareModal>

            {/* NEW PRESET MODAL */}
            <HardwareModal isOpen={presetModal} onClose={() => setPresetModal(false)} title="NEW PRESET">
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>PRESET NAME</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="e.g. Generator Fuel"
                        autoFocus
                        value={newPresetName}
                        onChange={e => setNewPresetName(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={() => setPresetModal(false)}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitPreset} loading={savingPreset} icon={FiPlus}>
                        ADD PRESET
                    </HardwareButton>
                </div>
            </HardwareModal>

            {/* EDIT MODAL */}
            <HardwareModal isOpen={editModal.open} onClose={() => setEditModal({ open: false, expense: null })}
                title="EDIT EXPENSE">
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>CATEGORY</label>
                    <input
                        type="text"
                        list="expense-categories"
                        className={modalStyles.modalInput}
                        value={editCategory}
                        onChange={e => setEditCategory(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT (UGX)</label>
                    <input
                        type="number"
                        inputMode="decimal"
                        className={styles.amountInput}
                        value={editAmount}
                        onChange={e => setEditAmount(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        value={editNote}
                        onChange={e => setEditNote(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>WHO ACTUALLY SPENT THIS (IF NOT THE LOGGER)</label>
                    <input
                        type="text"
                        className={modalStyles.modalInput}
                        placeholder="Defaults to whoever logged it"
                        value={editSpentBy}
                        onChange={e => setEditSpentBy(e.target.value)}
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setEditModal({ open: false, expense: null })}>
                        CANCEL
                    </button>
                    <HardwareButton onClick={submitEdit} loading={saving} icon={FiEdit2}>
                        SAVE CHANGES
                    </HardwareButton>
                </div>
            </HardwareModal>

            <BackToTopButton />
            <ToastStack toasts={toasts} onDismiss={dismissToast} />
            <ConfirmDialog state={confirmState} onAnswer={handleAnswer} />
        </div>
    );
};

export default ExpensesPage;
"""


# ================================================================== 4. ANALYSIS (moved to Reports)
ANALYSIS_CSS_BODY = r"""/* PATH: erp-frontend/src/pages/Reports/ExpenseAnalysis.module.css */
/* The Director expense analysis, moved off the Expenses page and onto the
   Report Hub. Styling follows the same reference chain as everything else in
   this pass -- Payment Records -> Client Dossier -> here: Inter stack, the
   dossier's button/tag/table idioms, and the Payments .sumCard for the total.
   Nothing here is page chrome; it renders inside a Report Hub drawer. */
.wrap {
  --orange: #EE8C3A; --orange-border: rgba(238,140,58,0.28);
  --navy: #213E40; --navy-deep: #1a2e30; --red: #ef4444; --amber: #f59e0b;
  --radius: 10px; --radius-sm: 6px;
  display: flex; flex-direction: column; gap: clamp(10px,1.4vw,16px);
  padding: clamp(12px,1.6vw,18px);
  font-family: 'Inter', sans-serif; color: #fff;
}

/* -- toggles -- the app's confirmed standard filter-button spec -- */
.toggleRow { display: flex; gap: clamp(6px,0.9vw,10px); flex-wrap: wrap; }
.toggleBtn, .toggleBtnActive {
  font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  text-transform: uppercase; letter-spacing: 1.5px;
  padding: clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px); border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.18); background: rgba(26,46,48,0.75); color: rgba(255,255,255,0.85);
  cursor: pointer; transition: all 0.2s ease;
}
.toggleBtn:hover { background: rgba(238,140,58,0.12); color: var(--orange); border-color: var(--orange); }
.toggleBtnActive {
  background: var(--orange); color: #1a2e30; border-color: var(--orange);
  box-shadow: 0 0 12px rgba(238,140,58,0.35);
}
.toggleBtn:focus-visible, .toggleBtnActive:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* -- headline total -- the Payments summary card -- */
.totalCard {
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid var(--orange-border); border-radius: var(--radius);
  padding: clamp(12px,1.5vw,18px); display: flex; flex-direction: column; gap: 4px;
}
.totalCard label { font-size: clamp(7px,0.75vw,9px); font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.5); }
.totalCard strong { font-family: 'Space Mono', monospace; font-size: clamp(14px,1.6vw,18px); font-weight: 700; color: var(--orange); word-break: break-all; }

.sectionLabel {
  font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 2px;
  color: var(--orange); text-transform: uppercase; margin: clamp(4px,0.8vw,8px) 0 0;
}

/* -- category / staff bars -- */
.bars { display: flex; flex-direction: column; gap: 10px; }
.barRow { display: grid; grid-template-columns: 110px 1fr 110px; align-items: center; gap: 10px; }
.barLabel { font-size: clamp(9px,0.95vw,11px); font-weight: 800; color: rgba(255,255,255,0.8); text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.barLabel span { display: inline-block; max-width: 100%; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: bottom; }
.barTrack { height: 12px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden; }
.barFill { height: 100%; background: linear-gradient(90deg, var(--orange) 0%, #d97a28 100%); border-radius: 999px; transition: width 0.4s ease; }
.barValue { font-family: 'Space Mono', monospace; font-size: clamp(9px,0.95vw,11px); font-weight: 700; text-align: right; color: rgba(255,255,255,0.7); }

/* -- spending over time -- */
.tsChart { display: flex; gap: 6px; overflow-x: auto; padding: 4px 4px 0; align-items: flex-end; min-height: 140px; scrollbar-width: none; }
.tsChart::-webkit-scrollbar { display: none; }
.tsBarWrap { display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0; width: 32px; cursor: help; }
.tsBarTrack { height: 110px; width: 100%; display: flex; align-items: flex-end; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; }
.tsBarFill { width: 100%; background: linear-gradient(180deg, var(--orange) 0%, #d97a28 100%); border-radius: 3px 3px 0 0; min-height: 2px; }
/* CONTRAST RULE: white 45% at 8px was 3.1:1 -- far under the floor for
   text this small. */
.tsBarLabel { font-family: 'Space Mono', monospace; font-size: 8px; color: rgba(244,242,239,0.7); white-space: nowrap; }

/* -- search -- */
.divider { border-top: 1px solid rgba(255,255,255,0.1); padding-top: clamp(10px,1.4vw,14px); }
.filterRow { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filterInput {
  height: 34px; padding: 0 10px; border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.15); background: rgba(0,0,0,0.2); color: #fff;
  font-family: 'Inter', sans-serif; font-size: clamp(10px,1.05vw,12px); font-weight: 600; min-width: 120px;
}
.filterInput:focus { outline: none; border-color: var(--orange); }

.categoryDropdown { position: relative; flex: 1 1 160px; min-width: 120px; }
.categoryDropdownBtn {
  width: 100%; height: 34px; padding: 0 10px; border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.15); background: rgba(0,0,0,0.2); color: #fff;
  font-family: 'Inter', sans-serif; font-size: clamp(10px,1.05vw,12px); font-weight: 700;
  cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 8px;
  text-align: left; text-transform: uppercase; transition: border-color 0.2s;
}
.categoryDropdownBtn span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.categoryDropdownBtn:hover { border-color: var(--orange); }
.categoryDropdownBtn svg { color: var(--orange); flex-shrink: 0; transition: transform 0.2s; }
.categoryDropdownIconOpen { transform: rotate(180deg); }
.categoryDropdownList {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  background: #ffffff; border: 2px solid var(--orange); border-radius: var(--radius-sm);
  box-shadow: 0 20px 50px rgba(0,0,0,0.5), 0 8px 20px rgba(0,0,0,0.25);
  overflow: hidden; max-height: 220px; overflow-y: auto; z-index: 300; scrollbar-width: none;
}
.categoryDropdownList::-webkit-scrollbar { display: none; }
.categoryDropdownOption {
  padding: 9px 12px; color: var(--navy); font-size: 12px; font-weight: 700; background: #ffffff;
  border-bottom: 1px solid #f1f5f9; cursor: pointer; text-transform: uppercase;
  transition: background 0.15s, color 0.15s;
}
.categoryDropdownOption:last-child { border-bottom: none; }
.categoryDropdownOption:hover { background: var(--orange); color: #fff; }
.categoryDropdownOptionActive { background: #f1f5f9; border-left: 4px solid var(--orange); }

.searchSummary {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  padding: 9px 12px; background: rgba(0,0,0,0.2); border-radius: var(--radius-sm);
  font-family: 'Space Mono', monospace; font-size: 10px; font-weight: 900;
  letter-spacing: 1px; text-transform: uppercase; color: rgba(244,242,239,0.72);
}
.truncatedFlag { color: var(--amber); cursor: help; }

/* -- results table -- the dossier's ledger table -- */
.tableScroll { overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none; }
.tableScroll::-webkit-scrollbar { display: none; }
.ledgerTable { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 680px; }
.ledgerTable thead th {
  background: #162a2c; color: var(--orange); font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  letter-spacing: 2px; text-transform: uppercase; text-align: left;
  padding: clamp(9px,1.3vw,14px) clamp(10px,1.5vw,16px);
  border-bottom: 3px solid var(--orange); white-space: nowrap;
}
.ledgerTable thead th:first-child { border-radius: 6px 0 0 0; }
.ledgerTable thead th:last-child { border-radius: 0 6px 0 0; }
.ledgerTable tbody td { padding: clamp(9px,1.2vw,13px) clamp(10px,1.5vw,16px); border-bottom: 1px solid rgba(255,255,255,0.06); vertical-align: middle; color: #fff; font-size: clamp(10px,1.05vw,12px); }
.ledgerTable tbody tr { border-left: 3px solid transparent; transition: background 0.15s; }
.ledgerTable tbody tr:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.dateCell { white-space: nowrap; font-family: 'Space Mono', monospace; color: rgba(255,255,255,0.6); font-size: clamp(9px,0.95vw,11px); }
.moneyCell { font-family: 'Space Mono', monospace; font-weight: 700; white-space: nowrap; color: #fca5a5; }
.metaCell { color: rgba(255,255,255,0.7); white-space: nowrap; }
.notesCell { color: rgba(255,255,255,0.55); font-style: italic; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notesCell span { display: inline-block; max-width: 100%; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: bottom; }
.noNote { color: rgba(244,242,239,0.45); font-style: normal; }
.categoryTag { font-size: 10px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; color: var(--orange); }

/* CONTRAST RULE: this sits inside a dark drawer, so cream, not white 30%. */
.emptyCell {
  text-align: center; padding: clamp(18px,3vw,32px) 16px;
  font-family: 'Space Mono', monospace; color: rgba(244,242,239,0.68);
  font-size: 11px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;
}

@media (max-width: 768px) {
  .barRow { grid-template-columns: 80px 1fr 80px; }
  .ledgerTable { min-width: 600px; }
}
@media (max-width: 480px) {
  .categoryDropdown { flex: 1 1 100%; }
  .ledgerTable thead th { font-size: 7px; letter-spacing: 1px; }
}
"""

ANALYSIS_JSX_BODY = r"""// PATH: erp-frontend/src/pages/Reports/ExpenseAnalysis.jsx
// The Director expense analysis, moved here from the Expenses page.
//
// Expenses is a data-entry screen -- "log the cash that just left the office"
// -- and hanging a four-section analytics dashboard plus a full-table search
// off a toggle in its header made it two products in one. Reports is where
// every other "read the numbers back to me" surface already lives, so this
// mounts as a drawer there instead.
//
// Nothing was dropped in the move: same expenseService calls, same period and
// bucket toggles, same by-category / by-staff bars, same time series, same
// filter set, and the same 100-row truncation flag.
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiChevronDown } from 'react-icons/fi';
import expenseService from '../../services/expenseService';
import { LoadingState } from '../../components/common/LoadingState';
import { Tooltip, Term } from '../../components/common/Tooltip';
import { GLOSSARY } from '../../components/common/glossary';
import { useToasts } from '../../components/common/useFeedback';
import { ToastStack } from '../../components/common/Feedback';
import styles from './ExpenseAnalysis.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const SEARCH_LIMIT = 100;
const EMPTY_FILTERS = { from: '', to: '', category: '', recordedBy: '', spentBy: '', minAmount: '', maxAmount: '' };

const ExpenseAnalysis = ({ active = true }) => {
    const { toasts, toast, dismissToast } = useToasts();

    const [period, setPeriod] = useState('MONTH');
    const [bucket, setBucket] = useState('DAY');

    const [summary, setSummary] = useState({ total: 0, byCategory: {} });
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [byStaff, setByStaff] = useState({});
    const [staffLoading, setStaffLoading] = useState(false);
    const [series, setSeries] = useState([]);
    const [seriesLoading, setSeriesLoading] = useState(false);

    const [categories, setCategories] = useState([]);
    const [filters, setFilters] = useState(EMPTY_FILTERS);
    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);

    const [categoryDropdownOpen, setCategoryDropdownOpen] = useState(false);
    const categoryDropdownRef = useRef(null);
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (categoryDropdownRef.current && !categoryDropdownRef.current.contains(e.target)) {
                setCategoryDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const loadSummary = useCallback(async (p) => {
        setSummaryLoading(true);
        try {
            const data = await expenseService.getSummary(p);
            setSummary(data || { total: 0, byCategory: {} });
        } catch {
            toast('Could not load the analysis summary.', 'error');
        } finally {
            setSummaryLoading(false);
        }
    }, [toast]);

    const loadByStaff = useCallback(async (p) => {
        setStaffLoading(true);
        try {
            const data = await expenseService.getByStaff(p);
            setByStaff(data || {});
        } catch {
            toast('Could not load the staff breakdown.', 'error');
        } finally {
            setStaffLoading(false);
        }
    }, [toast]);

    const loadSeries = useCallback(async (p, b) => {
        setSeriesLoading(true);
        try {
            const data = await expenseService.getTimeSeries(p, undefined, undefined, b);
            setSeries(data || []);
        } catch {
            toast('Could not load the spending trend.', 'error');
        } finally {
            setSeriesLoading(false);
        }
    }, [toast]);

    // Only fetch while the drawer is actually open -- a closed drawer on the
    // Report Hub should not be firing three calls on every period change.
    useEffect(() => {
        if (!active) return;
        loadSummary(period);
        loadByStaff(period);
        loadSeries(period, bucket);
    }, [active, period, bucket, loadSummary, loadByStaff, loadSeries]);

    useEffect(() => {
        if (!active) return;
        let cancelled = false;
        expenseService.getCategories()
            .then(data => { if (!cancelled) setCategories(data || []); })
            .catch(() => { /* the dropdown just falls back to ALL CATEGORIES */ });
        return () => { cancelled = true; };
    }, [active]);

    const filterableCategories = useMemo(
        () => [...new Set((categories || []).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
        [categories],
    );

    const runSearch = async () => {
        // F5: a min above a max used to just return an empty list, which reads
        // as "no such expenses" rather than "your filter is impossible".
        const min = filters.minAmount === '' ? null : Number(filters.minAmount);
        const max = filters.maxAmount === '' ? null : Number(filters.maxAmount);
        if (min !== null && max !== null && min > max) {
            toast('Min UGX is higher than Max UGX -- nothing can match that.', 'error');
            return;
        }
        if (filters.from && filters.to && filters.from > filters.to) {
            toast('The From date is after the To date.', 'error');
            return;
        }
        setSearching(true);
        try {
            const cleanFilters = Object.fromEntries(
                Object.entries(filters).filter(([, v]) => v !== '' && v !== null)
            );
            const data = await expenseService.search(cleanFilters, 0, SEARCH_LIMIT);
            setSearchResults(data.content || []);
        } catch {
            toast('Search failed.', 'error');
        } finally {
            setSearching(false);
        }
    };

    const clearSearch = () => {
        setFilters(EMPTY_FILTERS);
        setSearchResults(null);
    };

    const searchTotal = useMemo(
        () => (searchResults || []).reduce((sum, e) => sum + Number(e.amount || 0), 0),
        [searchResults],
    );
    const maxCategoryAmount = useMemo(() => {
        const vals = Object.values(summary.byCategory || {});
        return vals.length ? Math.max(...vals.map(Number)) : 0;
    }, [summary]);
    const maxStaffAmount = useMemo(() => {
        const vals = Object.values(byStaff || {});
        return vals.length ? Math.max(...vals.map(Number)) : 0;
    }, [byStaff]);
    const maxSeriesAmount = useMemo(
        () => (series.length ? Math.max(...series.map(pt => Number(pt.total))) : 0),
        [series],
    );

    const Bars = ({ data, loading, loadingLabel, emptyLabel, max }) => {
        if (loading) return <LoadingState label={loadingLabel} tone="bare" />;
        const entries = Object.entries(data || {});
        if (entries.length === 0) return <div className={styles.emptyCell}>{emptyLabel}</div>;
        return (
            <div className={styles.bars}>
                {entries.map(([key, amt]) => (
                    <div key={key} className={styles.barRow}>
                        <span className={styles.barLabel}>
                            <Tooltip label={`${key}: UGX ${fmt(amt)}`}><span>{key}</span></Tooltip>
                        </span>
                        <div className={styles.barTrack}>
                            <div
                                className={styles.barFill}
                                style={{ width: max ? `${(Number(amt) / max) * 100}%` : '0%' }}
                            />
                        </div>
                        <span className={styles.barValue}>UGX {fmt(amt)}</span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className={styles.wrap}>
            <div className={styles.toggleRow}>
                {[
                    ['TODAY', 'Since midnight today'],
                    ['WEEK', 'The last 7 days'],
                    ['MONTH', 'The last 30 days'],
                    ['YEAR', 'The last 365 days'],
                ].map(([p, tip]) => (
                    <Tooltip key={p} label={tip}>
                        <button
                            className={period === p ? styles.toggleBtnActive : styles.toggleBtn}
                            onClick={() => setPeriod(p)}
                            aria-pressed={period === p}
                        >
                            {p}
                        </button>
                    </Tooltip>
                ))}
            </div>

            <div className={styles.totalCard}>
                <label>TOTAL SPENT ({period})</label>
                {summaryLoading
                    ? <LoadingState label="SYNCING TOTAL..." tone="bare" />
                    : <strong>UGX {fmt(summary.total)}</strong>}
            </div>

            <div className={styles.sectionLabel}>
                <Term tip="Every expense in this period, added up per category, biggest first.">BY CATEGORY</Term>
            </div>
            <Bars
                data={summary.byCategory}
                loading={summaryLoading}
                loadingLabel="SYNCING CATEGORIES..."
                emptyLabel="NO EXPENSES IN THIS PERIOD"
                max={maxCategoryAmount}
            />

            <div className={styles.sectionLabel}>
                <Term tip={GLOSSARY.SPENT_BY}>BY STAFF (WHO SPENT IT)</Term>
            </div>
            <Bars
                data={byStaff}
                loading={staffLoading}
                loadingLabel="SYNCING STAFF BREAKDOWN..."
                emptyLabel="NO EXPENSES IN THIS PERIOD"
                max={maxStaffAmount}
            />

            <div className={styles.sectionLabel}>SPENDING OVER TIME</div>
            <div className={styles.toggleRow}>
                {[
                    ['DAY', 'One bar per day'],
                    ['WEEK', 'One bar per week'],
                    ['MONTH', 'One bar per month'],
                ].map(([b, tip]) => (
                    <Tooltip key={b} label={tip}>
                        <button
                            className={bucket === b ? styles.toggleBtnActive : styles.toggleBtn}
                            onClick={() => setBucket(b)}
                            aria-pressed={bucket === b}
                        >
                            {b}
                        </button>
                    </Tooltip>
                ))}
            </div>
            {seriesLoading ? (
                <LoadingState label="LOADING TREND..." tone="bare" />
            ) : series.length === 0 ? (
                <div className={styles.emptyCell}>NO ACTIVITY IN THIS WINDOW</div>
            ) : (
                <div className={styles.tsChart}>
                    {series.map(point => (
                        <Tooltip key={point.bucket} label={`${point.bucket}: UGX ${fmt(point.total)}`}>
                            <div className={styles.tsBarWrap}>
                                <div className={styles.tsBarTrack}>
                                    <div
                                        className={styles.tsBarFill}
                                        style={{ height: maxSeriesAmount ? `${Math.max(2, (Number(point.total) / maxSeriesAmount) * 100)}%` : '2%' }}
                                    />
                                </div>
                                <span className={styles.tsBarLabel}>{point.bucket.slice(-5)}</span>
                            </div>
                        </Tooltip>
                    ))}
                </div>
            )}

            <div className={styles.divider}>
                <div className={styles.sectionLabel}>SEARCH ALL EXPENSES</div>
            </div>
            <div className={styles.filterRow}>
                <Tooltip label="Only show expenses logged on or after this date">
                    <input type="date" className={styles.filterInput} value={filters.from}
                        aria-label="From date"
                        onChange={e => setFilters({ ...filters, from: e.target.value })} />
                </Tooltip>
                <Tooltip label="Only show expenses logged on or before this date">
                    <input type="date" className={styles.filterInput} value={filters.to}
                        aria-label="To date"
                        onChange={e => setFilters({ ...filters, to: e.target.value })} />
                </Tooltip>
                <div className={styles.categoryDropdown} ref={categoryDropdownRef}>
                    <Tooltip label="Every category ever used -- preset tiles and anything typed in under OTHER">
                        <button
                            type="button"
                            className={styles.categoryDropdownBtn}
                            onClick={() => setCategoryDropdownOpen(o => !o)}
                            aria-expanded={categoryDropdownOpen}
                        >
                            <span>{filters.category || 'ALL CATEGORIES'}</span>
                            <FiChevronDown className={categoryDropdownOpen ? styles.categoryDropdownIconOpen : ''} aria-hidden="true" />
                        </button>
                    </Tooltip>
                    {categoryDropdownOpen && (
                        <div className={styles.categoryDropdownList} role="listbox">
                            <div
                                role="option"
                                aria-selected={!filters.category}
                                className={`${styles.categoryDropdownOption} ${!filters.category ? styles.categoryDropdownOptionActive : ''}`}
                                onClick={() => { setFilters({ ...filters, category: '' }); setCategoryDropdownOpen(false); }}
                            >
                                ALL CATEGORIES
                            </div>
                            {filterableCategories.map(name => (
                                <div
                                    key={name}
                                    role="option"
                                    aria-selected={filters.category === name}
                                    className={`${styles.categoryDropdownOption} ${filters.category === name ? styles.categoryDropdownOptionActive : ''}`}
                                    onClick={() => { setFilters({ ...filters, category: name }); setCategoryDropdownOpen(false); }}
                                >
                                    {name}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                <Tooltip label="The staff member who typed the entry into the system">
                    <input type="text" className={styles.filterInput} placeholder="Logged by..."
                        aria-label="Logged by"
                        value={filters.recordedBy} onChange={e => setFilters({ ...filters, recordedBy: e.target.value })} />
                </Tooltip>
                <Tooltip label={GLOSSARY.SPENT_BY}>
                    <input type="text" className={styles.filterInput} placeholder="Spent by..."
                        aria-label="Spent by"
                        value={filters.spentBy} onChange={e => setFilters({ ...filters, spentBy: e.target.value })} />
                </Tooltip>
                <Tooltip label="Hide anything cheaper than this">
                    <input type="number" className={styles.filterInput} placeholder="Min UGX"
                        aria-label="Minimum amount"
                        value={filters.minAmount} onChange={e => setFilters({ ...filters, minAmount: e.target.value })} />
                </Tooltip>
                <Tooltip label="Hide anything more expensive than this">
                    <input type="number" className={styles.filterInput} placeholder="Max UGX"
                        aria-label="Maximum amount"
                        value={filters.maxAmount} onChange={e => setFilters({ ...filters, maxAmount: e.target.value })} />
                </Tooltip>
                <Tooltip label={`Search every expense ever logged (returns up to ${SEARCH_LIMIT} entries)`}>
                    <button className={styles.toggleBtnActive} onClick={runSearch} disabled={searching}>
                        <FiSearch size={12} aria-hidden="true" /> {searching ? 'SEARCHING...' : 'SEARCH'}
                    </button>
                </Tooltip>
                {searchResults && (
                    <Tooltip label="Reset every filter and hide these results">
                        <button className={styles.toggleBtn} onClick={clearSearch}>
                            <FiX size={12} aria-hidden="true" /> CLEAR
                        </button>
                    </Tooltip>
                )}
            </div>

            {searchResults && (
                <>
                    {/* F4: the old version silently stopped at 100 rows, so a
                        truncated list could be read as the whole truth. */}
                    <div className={styles.searchSummary}>
                        <span>
                            {searchResults.length} {searchResults.length === 1 ? 'ENTRY' : 'ENTRIES'}
                            {' -- '}UGX {fmt(searchTotal)} TOTAL
                        </span>
                        {searchResults.length >= SEARCH_LIMIT && (
                            <Term tip={`Only the first ${SEARCH_LIMIT} matches are shown. Narrow the dates or the amount range to see the rest.`}>
                                <span className={styles.truncatedFlag}>SHOWING FIRST {SEARCH_LIMIT} ONLY</span>
                            </Term>
                        )}
                    </div>
                    <div className={styles.tableScroll}>
                        <table className={styles.ledgerTable}>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Category</th>
                                    <th>Amount (UGX)</th>
                                    <th>Logged By</th>
                                    <th>Spent By</th>
                                    <th>Note</th>
                                </tr>
                            </thead>
                            <tbody>
                                {searchResults.length === 0 ? (
                                    <tr><td colSpan="6" className={styles.emptyCell}>NO RESULTS</td></tr>
                                ) : searchResults.map(e => (
                                    <tr key={e.id}>
                                        <td className={styles.dateCell}>{new Date(e.createdAt).toLocaleDateString()}</td>
                                        <td><span className={styles.categoryTag}>{e.category}</span></td>
                                        <td className={styles.moneyCell}>UGX {fmt(e.amount)}</td>
                                        <td className={styles.metaCell}>{e.recordedBy}</td>
                                        <td className={styles.metaCell}>{e.spentBy || e.recordedBy}</td>
                                        <td className={styles.notesCell}>
                                            {e.note
                                                ? <Tooltip label={e.note}><span>{e.note}</span></Tooltip>
                                                : <span className={styles.noNote}>---</span>}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            <ToastStack toasts={toasts} onDismiss={dismissToast} />
        </div>
    );
};

export default ExpenseAnalysis;
"""


# ================================================================== patchers
def patch_expenses():
    print('\n[2/4] Expenses page -> rebuilt on the Client Dossier reference')
    write(EXPENSES_CSS, EXPENSES_CSS_BODY, 'ExpensesPage.module.css')
    write(EXPENSES_JSX, EXPENSES_JSX_BODY, 'ExpensesPage.jsx')


def patch_analysis():
    print('\n[3/4] Analysis -> Reports/ExpenseAnalysis')
    write(ANALYSIS_CSS, ANALYSIS_CSS_BODY, 'Reports/ExpenseAnalysis.module.css')
    write(ANALYSIS_JSX, ANALYSIS_JSX_BODY, 'Reports/ExpenseAnalysis.jsx')


REPORT_PANEL = """                {hasFinancialAccess && (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="EXPENSE ANALYSIS" isOpen={drawers.expenses} onClick={() => toggleDrawer('expenses')} icon={FiTrendingDown} />
                        <div
                            className={`${styles.panelBody} ${drawers.expenses ? styles.bodyOpenTall : styles.bodyClosed}`}
                            aria-hidden={!drawers.expenses}
                        >
                            {/* Mounted only while open: the analysis fires three
                                service calls on mount and on every period change,
                                and a collapsed drawer should cost nothing. */}
                            {drawers.expenses && <ExpenseAnalysis active={drawers.expenses} />}
                        </div>
                    </div>
                )}

"""

REPORT_TAIL_ANCHOR = """            </div>
        </div>
    );
};

export default ReportHub;"""


def patch_reporthub():
    print('\n[4/4] Report Hub -> mount the EXPENSE ANALYSIS drawer')
    if require(REPORTHUB_JSX, 'ReportHub.jsx'):
        jsx = read(REPORTHUB_JSX)

        jsx = swap(jsx,
                   "    FiShield, FiTrendingUp, FiLock, FiDownloadCloud,",
                   "    FiShield, FiTrendingUp, FiTrendingDown, FiLock, FiDownloadCloud,",
                   'ReportHub: FiTrendingDown import')

        jsx = swap(jsx,
                   "import styles from './ReportHub.module.css';",
                   "import ExpenseAnalysis from './ExpenseAnalysis';\n"
                   "import styles from './ReportHub.module.css';",
                   'ReportHub: ExpenseAnalysis import')

        jsx = swap(jsx,
                   "useState({ finance: true, ops: true, system: false, p2: true })",
                   "useState({ finance: true, ops: true, system: false, p2: true, expenses: false })",
                   'ReportHub: expenses drawer state')

        jsx = swap(jsx,
                   REPORT_TAIL_ANCHOR,
                   REPORT_PANEL + REPORT_TAIL_ANCHOR,
                   'ReportHub: EXPENSE ANALYSIS panel')

        write(REPORTHUB_JSX, jsx, 'ReportHub.jsx')

    if require(REPORTHUB_CSS, 'ReportHub.module.css'):
        css = read(REPORTHUB_CSS)
        if '.bodyOpenTall' in css:
            print('  [ skip] ReportHub .bodyOpenTall (already applied)')
        else:
            css = css.rstrip() + """

/* ── EXPENSE ANALYSIS DRAWER ──────────────────────────────────────
   .bodyOpen caps at 6000px and clips overflow, which is right for a
   list of report rows but wrong here: the analysis is taller than the
   cap on a busy month, and its category dropdown has to escape the
   panel to be usable. This variant lifts both constraints. */
.bodyOpenTall { max-height: none; opacity: 1; overflow: visible; }
"""
            print('  [patch] ReportHub .bodyOpenTall')
        write(REPORTHUB_CSS, css, 'ReportHub.module.css')


# ================================================================== main
def main():
    print(__doc__.split('Run:')[0].strip()[:0] or '', end='')
    print('=' * 68)
    print('GOLDEN SEED -- fix67: design coherence (Payments -> Portfolio -> Expenses)')
    print('=' * 68)

    if not os.path.isdir(FE):
        print('ERROR: erp-frontend/src not found next to this script.')
        print('       Run fix.py from the repository root.')
        sys.exit(1)

    patch_portfolio()
    patch_expenses()
    patch_analysis()
    patch_reporthub()

    print('\n' + '-' * 68)
    print('FILES WRITTEN: ' + str(len(CHANGED)))
    for c in CHANGED:
        print('  - ' + c)
    if SKIPPED:
        print('ANCHORS MISSED (left untouched, review by hand):')
        for s in SKIPPED:
            print('  ! ' + s)
    print('-' * 68)

    print('\nCommitting...')
    run(['git', 'add', '-A'])
    code = run(['git', 'commit', '-m',
                'fix67: design coherence pass -- Portfolio stat cards adopt the '
                'Payment Records card spec, Expenses page rebuilt against the '
                'updated Portfolio (panels, tables, spacing, type, button-sized '
                'presets), Director analysis moved to the Report Hub'])
    if code != 0:
        print('  (nothing to commit, or commit failed -- pushing anyway)')
    run(['git', 'push'])
    print('\nDone.')


if __name__ == '__main__':
    main()