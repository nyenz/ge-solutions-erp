import os, sys

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except FileNotFoundError:
        return None

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

base = 'erp-frontend/src/pages/Recovery'
css_path = os.path.join(base, 'RecoveryPortal.module.css')

new_css = r"""/* PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238,140,58,0.15);
    --orange-border: rgba(238,140,58,0.32);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg,#1c3335 0%,#213E40 100%);
    --red:           #ef4444;
    --emerald:       #10b981;
    --cyan:          #06b6d4;

    --gap-xl:    clamp(16px, 2.2vw, 28px);
    --gap-lg:    clamp(10px, 1.4vw, 18px);
    --gap-md:    clamp(7px,  1vw,   13px);
    --gap-sm:    clamp(4px,  0.6vw,  8px);
    --pad-card:  clamp(16px, 2vw,   26px);
    --radius:    14px;
    --radius-sm: 8px;
    --radius-xs: 5px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-label:  clamp(8px,  0.82vw, 10px);
    --fs-meta:   clamp(9px,  0.9vw,  11px);
    --fs-value:  clamp(11px, 1.1vw,  13px);
    --fs-phone:  clamp(12px, 1.2vw,  14px);
    --fs-owner:  clamp(13px, 1.4vw,  16px);
    --fs-demand: clamp(15px, 1.8vw,  20px);
    --fs-badge:  clamp(7px,  0.75vw,  9px);
    --fs-btn:    clamp(9px,  0.9vw,  11px);
    --fs-note:   clamp(10px, 1vw,   12px);
    --fs-plot:   clamp(16px, 2vw,   22px);

    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    padding: clamp(14px,2.5vh,32px) clamp(12px,2vw,28px) clamp(60px,8vw,100px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

/* ── TOAST ── */
.toastContainer {
    position: fixed; bottom: 24px; right: 24px; z-index: 99999;
    display: flex; flex-direction: column-reverse;
    gap: 8px; max-width: 400px; pointer-events: none;
}
.toast {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 12px 16px; border-radius: 10px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    pointer-events: all;
    animation: toastIn 0.3s cubic-bezier(0.18,0.89,0.32,1.28) both;
}
@keyframes toastIn { from{opacity:0;transform:translateX(40px)} to{opacity:1;transform:translateX(0)} }
.toast_success { background: rgba(16,185,129,0.95); border-left: 4px solid #059669; color:#fff; }
.toast_error   { background: rgba(239,68,68,0.95);  border-left: 4px solid #b91c1c; color:#fff; }
.toast_warn    { background: rgba(245,158,11,0.95); border-left: 4px solid #b45309; color:#fff; }
.toast_info    { background: rgba(6,182,212,0.95);  border-left: 4px solid #0369a1; color:#fff; }
.toastIcon  { font-size: 15px; flex-shrink: 0; margin-top: 1px; }
.toastMsg   { font-family:'Space Mono',monospace; font-size:10px; font-weight:700; line-height:1.4; flex:1; min-width:0; word-break:break-word; }
.toastClose { background:transparent; border:none; color:inherit; opacity:0.6; cursor:pointer; padding:2px; font-size:13px; flex-shrink:0; transition:opacity 0.15s; }
.toastClose:hover { opacity:1; }

/* ── BOOT ── */
.bootScreen  { height:60vh; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px; }
.bootSpinner { width:40px; height:40px; border:3px solid rgba(238,140,58,0.15); border-top-color:#EE8C3A; border-radius:50%; animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.bootLabel   { font-family:'Cinzel',serif; font-size:12px; font-weight:700; letter-spacing:4px; color:#EE8C3A; text-transform:uppercase; }

/* ── HEADER ── */
.pageHeader {
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: clamp(10px,1.4vw,16px);
    margin-bottom: clamp(14px,2vw,24px);
    border-left: clamp(3px,0.4vw,5px) solid #EE8C3A;
    padding: clamp(10px,1.4vw,16px) clamp(16px,2.2vw,28px);
    background: rgba(255,255,255,0.62);
    border-radius: 0 var(--radius) var(--radius) 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.07);
    flex-shrink: 0;
}
.headerLeft  { display:flex; flex-direction:column; gap:3px; min-width:0; flex:1; }
.headerRight { display:flex; align-items:center; gap: clamp(8px,1.2vw,14px); flex-shrink:0; flex-wrap:wrap; }
.pageTitle   { font-family:'Cinzel',serif; color:#1a2e30; font-size:var(--fs-h1); font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin:0; line-height:1.1; }
.pageSubtitle{ font-family:'DM Sans',sans-serif; color:#64748b; font-size:clamp(8px,0.85vw,10px); font-weight:900; text-transform:uppercase; letter-spacing:1px; margin:0; }

/* ── MODE SWITCH ── */
.modeSwitch {
    display:flex; background:var(--navy); padding:4px;
    border-radius:var(--radius-sm); border:1px solid var(--orange-border);
    gap:3px; flex-wrap:nowrap; flex-shrink:0;
}
.modeActive {
    background:var(--orange); color:var(--navy); border:none;
    padding: clamp(6px,0.9vw,9px) clamp(12px,1.5vw,18px);
    border-radius: 6px;
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size:clamp(9px,0.95vw,11px); letter-spacing:1px;
    text-transform:uppercase; cursor:pointer;
    display:flex; align-items:center; gap:7px; white-space:nowrap;
    transition: background 0.2s;
}
.modeActive:hover { background:#d4732a; }
.modeInactive {
    background:transparent; color:rgba(255,255,255,0.65); border:none;
    padding: clamp(6px,0.9vw,9px) clamp(12px,1.5vw,18px);
    border-radius: 6px;
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size:clamp(9px,0.95vw,11px); letter-spacing:1px;
    text-transform:uppercase; cursor:pointer;
    display:flex; align-items:center; gap:7px; white-space:nowrap;
    transition:background 0.2s, color 0.2s;
}
.modeInactive:hover { background:rgba(255,255,255,0.1); color:#fff; }

/* ── FINANCIAL HUD ── */
.finHUD {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--gap-md);
    margin-bottom: var(--gap-lg);
    flex-shrink: 0;
}
.finHUDCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    border-radius: var(--radius);
    padding: clamp(14px,1.8vw,22px);
    display: flex; flex-direction: column; gap: 5px;
    position: relative;
    overflow: hidden;
}
.finHUDCard::before {
    content: '';
    position: absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, transparent, rgba(238,140,58,0.6), transparent);
}
.finHUDCard label {
    font-family:'DM Sans',sans-serif; font-size:var(--fs-badge);
    font-weight:900; color:rgba(255,255,255,0.45);
    text-transform:uppercase; letter-spacing:1.2px;
}
.finHUDCard strong {
    font-family:'Space Mono',monospace;
    font-size:clamp(14px,1.7vw,20px);
    font-weight:700; word-break:break-all; line-height:1.1;
}
.finHUDCard span {
    font-size:var(--fs-badge);
    color:rgba(255,255,255,0.3);
    font-family:'DM Sans',sans-serif; font-weight:800;
}

/* ── FILTER BAR ── */
.filterBar {
    display: flex; flex-direction: column; gap: var(--gap-md);
    margin-bottom: clamp(10px,1.3vw,16px);
    flex-shrink: 0;
    position: sticky; top: 0; z-index: 200;
    background: transparent;
    padding: clamp(8px,1vw,12px) 0;
    margin-left: clamp(-12px,-2vw,-28px);
    margin-right: clamp(-12px,-2vw,-28px);
    padding-left: clamp(12px,2vw,28px);
    padding-right: clamp(12px,2vw,28px);
}
.searchInner {
    position: relative; display: flex; align-items: center;
    background: #fff; border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    width: 100%; max-width: clamp(300px,42vw,520px);
    height: clamp(36px,4vw,44px);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.searchInner:focus-within {
    border-color: var(--orange);
    box-shadow: 0 0 0 3px rgba(238,140,58,0.15);
}
.searchIcon {
    position:absolute; left:12px; top:50%; transform:translateY(-50%);
    color:var(--orange); font-size:16px; pointer-events:none; flex-shrink:0;
}
.searchInput {
    width:100%; border:none; outline:none; background:transparent;
    color:var(--navy); padding-right:34px !important; padding-left:42px !important;
    font-family:'DM Sans',sans-serif; font-weight:800;
    font-size:clamp(11px,1.1vw,13px); height:100%;
    transition: padding 0.2s ease;
}
.searchInputActive { padding-left:14px !important; }
.searchInput::placeholder { font-weight:500; color:rgba(26,46,48,0.35); }
.searchClear {
    position:absolute; right:8px; top:50%; transform:translateY(-50%);
    background:transparent; border:none; cursor:pointer;
    color:rgba(26,46,48,0.4); display:flex; align-items:center;
    padding:3px; border-radius:4px; transition:color 0.15s, background 0.15s;
}
.searchClear:hover { color:var(--navy); background:rgba(26,46,48,0.08); }

.filterPills {
    display:flex; flex-wrap:nowrap; overflow-x:auto;
    gap: clamp(6px,0.8vw,10px);
    scrollbar-width:none; padding-bottom:2px;
}
.filterPills::-webkit-scrollbar { display:none; }
.filterPill {
    background: rgba(26,46,48,0.75);
    border: 1.5px solid rgba(255,255,255,0.18);
    color: rgba(255,255,255,0.85);
    padding: clamp(7px,0.9vw,9px) clamp(14px,1.6vw,20px);
    border-radius: var(--radius-sm);
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size:clamp(9px,0.9vw,11px); letter-spacing:1.5px;
    text-transform:uppercase; cursor:pointer;
    transition: all 0.2s ease;
    display:inline-flex; align-items:center; gap:5px;
    white-space:nowrap; flex-shrink:0;
}
.filterPill:hover { background:rgba(238,140,58,0.12); color:#EE8C3A; border-color:#EE8C3A; }
.filterPillActive {
    background:#EE8C3A !important; color:#1a2e30 !important;
    border-color:#EE8C3A !important;
    box-shadow:0 0 14px rgba(238,140,58,0.4);
}

/* ── LEGEND ── */
.legend {
    display: flex; flex-wrap: wrap; gap: clamp(10px,1.5vw,20px);
    margin-bottom: clamp(10px,1.3vw,16px);
    padding: clamp(6px,0.8vw,10px) 0;
    flex-shrink: 0;
}
.legendItem {
    display: flex; align-items: center; gap: 7px;
    font-family:'DM Sans',sans-serif;
    font-size: clamp(9px,0.9vw,11px); font-weight:800;
    color:rgba(26,46,48,0.7); white-space:nowrap;
}

/* ── SECTION GROUPS ── */
.missionGrid { display: flex; flex-direction: column; gap: var(--gap-xl); }

.sectionGroup {
    display: flex; flex-direction: column;
    gap: var(--gap-md);
}
.sectionHeader {
    display: inline-flex; align-items: center; gap: 9px;
    align-self: flex-start;
    font-family:'DM Sans',sans-serif;
    font-size: clamp(9px,0.95vw,11px); font-weight:900;
    color: #fff; text-transform:uppercase; letter-spacing:2px;
    padding: clamp(6px,0.8vw,10px) clamp(14px,1.7vw,22px);
    border-radius: 6px;
    background: rgba(26,46,48,0.8);
    border: 1px solid rgba(238,140,58,0.3);
    margin-bottom: clamp(4px,0.6vw,8px);
}
.sectionHeaderBacklog {
    color: #fca5a5;
    background: rgba(100,20,20,0.55);
    border-color: rgba(239,68,68,0.4);
}

/* ── MISSION CARD ── */
.missionCard {
    background: var(--panel-bg);
    border: 1.5px solid rgba(238,140,58,0.22);
    border-radius: var(--radius);
    box-shadow: 0 4px 20px rgba(0,0,0,0.18), 0 1px 4px rgba(0,0,0,0.12);
    transition: border-color 0.25s, box-shadow 0.25s, transform 0.2s;
    overflow: hidden;
    width: 100%;
    position: relative;
}
.missionCard::after {
    content: '';
    position: absolute; top:0; left:0; right:0; height:1px;
    background: linear-gradient(90deg, transparent, rgba(238,140,58,0.4), transparent);
    opacity: 0;
    transition: opacity 0.25s;
}
.missionCard:hover {
    border-color: rgba(238,140,58,0.55);
    box-shadow: 0 8px 32px rgba(0,0,0,0.28), 0 2px 8px rgba(0,0,0,0.16);
    transform: translateY(-1px);
}
.missionCard:hover::after { opacity:1; }
.cardLocked  { opacity:0.72; border-style:dashed; }
.cardLocked:hover { transform:none; }
.cardBacklog {
    border-color: rgba(239,68,68,0.32);
    box-shadow: 0 4px 20px rgba(239,68,68,0.08), 0 1px 4px rgba(0,0,0,0.12);
}
.cardBacklog:hover { border-color:rgba(239,68,68,0.6); }

/* ── STATUS BADGE ── */
.statusBadge {
    float: right;
    display: inline-flex; align-items: center; gap: 5px;
    padding: clamp(5px,0.7vw,7px) clamp(10px,1.3vw,14px);
    font-family:'DM Sans',sans-serif;
    font-size: var(--fs-badge); font-weight:900; letter-spacing:1px;
    text-transform:uppercase;
    border-radius: 0 0 0 var(--radius-sm);
    border-left: 1px solid rgba(255,255,255,0.08);
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.statusRed    { color:#fca5a5; background:rgba(239,68,68,0.12); }
.statusBlue   { color:#93c5fd; background:rgba(59,130,246,0.1); }
.statusGrey   { color:rgba(255,255,255,0.38); background:rgba(255,255,255,0.04); }
.statusDefault{ color:rgba(255,255,255,0.45); background:transparent; }

/* ── CARD HEADER ── */
.cardHeader {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: start;
    gap: var(--gap-md);
    padding: var(--pad-card);
    cursor: pointer; user-select: none; clear:both;
}
.cardHeader:focus-visible {
    outline: 2px solid var(--orange); outline-offset:-2px;
    border-radius: var(--radius);
}

.cardMain {
    display: flex; flex-direction: column;
    gap: clamp(5px,0.7vw,9px);
    min-width: 0;
}

/* Top row: dot + plotID + backlog pill */
.cardTopRow {
    display: flex; align-items: center;
    gap: clamp(8px,1vw,12px);
    flex-wrap: wrap;
}
.plotId {
    font-family:'Space Mono',monospace;
    color: var(--orange);
    font-size: var(--fs-plot);
    font-weight: 900; letter-spacing:0.5px;
    line-height: 1;
}
.backlogPill {
    font-family:'DM Sans',sans-serif; font-size: var(--fs-badge);
    font-weight:900; text-transform:uppercase; letter-spacing:1px;
    background:rgba(239,68,68,0.2);
    border:1px solid rgba(239,68,68,0.5);
    border-radius:4px; padding: 2px 9px; color:#fca5a5; flex-shrink:0;
}

/* Owner + phone */
.ownerLine {
    font-family:'Cinzel',serif; color:#fff;
    font-size: var(--fs-owner); font-weight:700;
    letter-spacing: 0.3px; line-height:1.2;
    white-space: nowrap; overflow:hidden; text-overflow:ellipsis;
}
.phoneLine {
    font-family:'Space Mono',monospace;
    color: rgba(255,255,255,0.5);
    font-size: var(--fs-phone); font-weight:700;
    letter-spacing: 0.3px;
}

/* Balance line */
.balanceLine {
    display: flex; align-items: baseline; gap: 10px;
    margin-top: 2px;
}
.balanceLabel {
    font-family:'DM Sans',sans-serif;
    font-size: var(--fs-badge); font-weight:900;
    color: rgba(255,255,255,0.45);
    text-transform:uppercase; letter-spacing:1px; white-space:nowrap;
}
.balanceVal {
    font-family:'Space Mono',monospace;
    font-size: var(--fs-demand); font-weight:900; color:#fff;
}
.balanceRed { color:#fca5a5; }

/* ── SIDE ACTIONS ── */
.cardSideActions {
    display: flex; flex-direction: column;
    align-items: flex-end; justify-content: space-between;
    gap: var(--gap-sm); flex-shrink: 0;
    padding-top: 2px;
    min-height: clamp(60px,8vw,90px);
}
.logCallBtnSmall {
    background: var(--orange); color: var(--navy); border: none;
    border-radius: var(--radius-sm);
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size: var(--fs-btn); text-transform:uppercase; letter-spacing:1.2px;
    padding: clamp(9px,1.1vw,12px) clamp(14px,1.7vw,20px);
    cursor:pointer; display:flex; align-items:center; gap:6px;
    transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
    white-space:nowrap;
    box-shadow: 0 4px 14px rgba(238,140,58,0.3);
}
.logCallBtnSmall:hover:not(:disabled) {
    background:#f09a48;
    box-shadow: 0 6px 20px rgba(238,140,58,0.45);
    transform:translateY(-1px);
}
.logCallBtnSmall:disabled {
    background: rgba(255,255,255,0.08);
    border: 1.5px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.28);
    cursor:not-allowed; font-size:clamp(8px,0.82vw,9px);
    box-shadow: none; transform:none;
}
.expandIcon {
    color: rgba(255,255,255,0.32); font-size:22px;
    transition: color 0.2s, transform 0.3s;
}
.missionCard:hover .expandIcon { color:var(--orange); }

/* ── CARD BODY (expanded) ── */
.cardBody {
    padding: 0 var(--pad-card) var(--pad-card);
}
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(238,140,58,0.25), transparent);
    margin: clamp(4px,0.6vw,8px) 0 clamp(12px,1.5vw,18px);
}

/* Timing row */
.timingRow {
    display: flex; align-items: center; flex-wrap: wrap;
    gap: clamp(6px,0.9vw,12px);
    font-size: var(--fs-note); color:#e2e8f0; font-weight:700;
    background: rgba(0,0,0,0.28);
    padding: clamp(9px,1.1vw,13px) clamp(12px,1.5vw,18px);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: var(--gap-md);
}
.timingRow strong { color:#fff; }
.timingSep { width:1px; height:13px; background:rgba(255,255,255,0.18); flex-shrink:0; }

/* Plots sub list */
.plotsSubList { display:flex; flex-direction:column; gap:var(--gap-md); }

.plotSubCard {
    background: rgba(0,0,0,0.22);
    border-radius: var(--radius-sm);
    padding: clamp(12px,1.5vw,18px);
    border-left: 3px solid var(--orange);
    transition: border-color 0.2s, background 0.2s;
}
.plotSubCard:hover { background:rgba(0,0,0,0.3); }

/* Financial detail inside each plot sub-card */
.finDetail {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: var(--radius-xs);
    padding: clamp(10px,1.2vw,14px);
    margin: clamp(8px,1vw,12px) 0;
    display: flex; flex-direction: column; gap: 7px;
}
.finDetailRow {
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 12px; font-family:'DM Sans',sans-serif;
    font-size: clamp(10px,1vw,12px); font-weight:700;
    color: rgba(255,255,255,0.6);
}
.finDetailRow strong {
    font-family:'Space Mono',monospace; color:#fff;
    font-size: clamp(11px,1.1vw,13px);
}
.finDetailTotal {
    border-top: 1px solid rgba(255,255,255,0.1);
    padding-top: 7px; margin-top:3px; font-weight:900;
}
.finDetailTotal span {
    color:rgba(255,255,255,0.85); text-transform:uppercase; letter-spacing:0.5px;
}

/* Last interaction note */
.lastNote {
    display: flex; align-items: flex-start; gap: 7px;
    font-size: var(--fs-meta); color:rgba(255,255,255,0.4);
    font-style:italic; font-weight:600; line-height:1.45;
    background: rgba(255,255,255,0.025);
    padding: clamp(6px,0.8vw,9px) clamp(9px,1.1vw,13px);
    border-radius: var(--radius-xs);
    border-left: 2px solid rgba(255,255,255,0.1);
}

/* Expanded action buttons */
.expandedActions {
    display: flex; gap: var(--gap-sm); flex-wrap: wrap;
    margin-top: var(--gap-md);
}
.folderBtn {
    background: rgba(255,255,255,0.08);
    border: 1.5px solid rgba(255,255,255,0.2);
    color: #fff; font-family:'DM Sans',sans-serif; font-weight:900;
    border-radius: var(--radius-sm); font-size:var(--fs-btn);
    padding: clamp(7px,0.9vw,10px) clamp(12px,1.5vw,18px);
    cursor:pointer; display:inline-flex; align-items:center;
    justify-content:center; gap:5px; transition:all 0.2s; white-space:nowrap;
}
.folderBtn:hover { border-color:var(--orange); color:var(--orange); background:rgba(238,140,58,0.1); }
.payBtn {
    background: rgba(34,197,94,0.12);
    border: 1.5px solid rgba(34,197,94,0.4);
    color: #4ade80; font-family:'DM Sans',sans-serif; font-weight:900;
    border-radius: var(--radius-sm); font-size:var(--fs-btn);
    padding: clamp(7px,0.9vw,10px) clamp(12px,1.5vw,18px);
    cursor:pointer; display:inline-flex; align-items:center;
    justify-content:center; gap:5px; transition:all 0.2s; white-space:nowrap;
}
.payBtn:hover { background:#22c55e; color:#1a2e30; border-color:#22c55e; }

/* ── CALL MODAL ── */
.historyStream {
    max-height:180px; overflow-y:auto;
    background:#f8fafc; border-radius:10px;
    padding:12px; margin-bottom:14px;
    border:1px solid #e2e8f0;
    scrollbar-width:thin;
}
.historyTitle  {
    font-family:'DM Sans',sans-serif; font-size:9px; font-weight:900;
    color:#475569; margin-bottom:9px;
    border-bottom:1px solid #e2e8f0; padding-bottom:6px;
    text-transform:uppercase; letter-spacing:1.2px;
}
.historyItem   { border-bottom:1px solid #f1f5f9; padding-bottom:8px; margin-bottom:8px; }
.historyItem:last-child { border-bottom:none; margin-bottom:0; }
.historyMeta   {
    display:flex; justify-content:space-between; align-items:center;
    font-family:'DM Sans',sans-serif; font-size:10px; font-weight:800;
    color:#c2410c; margin-bottom:3px;
}
.historyItem p { font-family:'DM Sans',sans-serif; font-size:12px; color:#1a2e30; line-height:1.5; font-weight:600; margin:0; }
.emptyHistory  { font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700; color:#94a3b8; text-align:center; padding:18px 0; }

/* ── EMPTY STATE ── */
.emptyGate {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 18px; padding: clamp(48px,9vw,90px) 24px; text-align:center;
    background: rgba(26,46,48,0.3);
    border: 1.5px dashed rgba(238,140,58,0.2);
    border-radius: var(--radius);
}
.emptyIcon  { font-size: clamp(44px,7vw,64px); color:#10b981; opacity:0.35; }
.emptyTitle { font-family:'Cinzel',serif; font-size: clamp(14px,1.8vw,20px); font-weight:700; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:2px; margin:0; }

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
    .finHUD { grid-template-columns: repeat(3, 1fr); }
    .pageHeader { flex-direction: column; align-items: flex-start; }
    .headerRight { width:100%; }
    .modeSwitch { width:100%; }
    .modeActive, .modeInactive { flex:1; justify-content:center; }
}
@media (max-width: 640px) {
    .finHUD { grid-template-columns: 1fr 1fr; }
    .finHUD .finHUDCard:last-child { grid-column: 1 / -1; }
    .cardHeader { grid-template-columns: 1fr; gap: var(--gap-md); }
    .cardSideActions { flex-direction: row; align-items: center; width:100%; justify-content: space-between; min-height: auto; }
    .logCallBtnSmall { flex:1; justify-content:center; }
    .statusBadge { float:none; align-self:flex-start; border-radius: var(--radius-xs); }
}
@media (max-width: 480px) {
    .container { padding: 12px 12px 60px; }
    .finHUD { grid-template-columns: 1fr; }
    .finHUD .finHUDCard:last-child { grid-column: 1; }
    .finDetailRow { font-size:10px; }
    .plotId { font-size:15px; }
    .ownerLine { font-size:13px; }
    .balanceVal { font-size:15px; }
    .timingRow { padding: 8px 11px; font-size:10px; }
}
"""

write_file(css_path, new_css)
print(f"OK: {css_path}")
print("All patches applied.") 