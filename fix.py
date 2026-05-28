import os

# RecoveryPortal.module.css - replace the card-related CSS sections
css_path = r'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'

with open(css_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace mission card styles
old_card = """.missionCard {
    background: var(--panel-bg);
    border: 1px solid rgba(238,140,58,0.18);
    border-radius: var(--radius);
    box-shadow: 0 2px 10px rgba(0,0,0,0.14);
    transition: border-color 0.22s, box-shadow 0.22s;
    overflow: hidden;
    width: 100%;
}
.missionCard:hover {
    border-color: rgba(238,140,58,0.42);
    box-shadow: 0 4px 20px rgba(0,0,0,0.22);
}
.cardLocked  { opacity:0.68; border-style:dashed; }
.cardLocked:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.14); }
.cardBacklog { border-color: rgba(239,68,68,0.25); }
.cardBacklog:hover { border-color: rgba(239,68,68,0.5); }

/* ── CARD HEADER — compact single row ── */
.cardHeader {
    display: flex;
    flex-direction: column;
    gap: clamp(6px,0.8vw,9px);
    padding: clamp(14px, 1.8vw, 22px) clamp(16px, 2.2vw, 28px);
    cursor: pointer;
    user-select: none;
}
.cardHeader:focus-visible { outline:2px solid var(--orange); outline-offset:-2px; border-radius:var(--radius); }

/* ── STATUS BADGE — inline, small ── */
.statusBadge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 7px;
    font-family:'DM Sans',sans-serif;
    font-size:var(--fs-2xs); font-weight:900; letter-spacing:0.8px;
    text-transform:uppercase;
    border-radius: 20px;
    flex-shrink: 0;
    white-space: nowrap;
}
.statusRed    { color:#fca5a5; background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); }
.statusBlue   { color:#93c5fd; background:rgba(59,130,246,0.1);  border:1px solid rgba(59,130,246,0.2); }
.statusGrey   { color:rgba(255,255,255,0.35); background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); }
.statusDefault{ color:rgba(255,255,255,0.4); background:transparent; border:1px solid rgba(255,255,255,0.1); }

/* ── CARD MAIN — horizontal, single-line layout ── */
.cardMain {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(8px,1vw,12px);
    width: 100%;
    flex-wrap: nowrap;
}

/* payment dot slot */
.cardTopRow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(8px,1vw,12px);
    width: 100%;
}
.cardTopRowLeft {
    display: flex;
    align-items: center;
    gap: clamp(6px,0.8vw,9px);
    min-width: 0;
    flex: 1;
}

.plotId {
    font-family:'Space Mono',monospace;
    color: var(--orange);
    font-size: var(--fs-value);
    font-weight: 900; letter-spacing:0.3px;
    line-height: 1;
    flex-shrink: 0;
}

.backlogPill {
    font-family:'DM Sans',sans-serif; font-size:var(--fs-2xs);
    font-weight:900; text-transform:uppercase; letter-spacing:0.8px;
    background:rgba(239,68,68,0.18);
    border:1px solid rgba(239,68,68,0.4);
    border-radius:3px; padding: 1px 6px; color:#fca5a5; flex-shrink:0;
}

/* owner + phone stacked, centre column */
.ownerLine {
    font-family:'DM Sans',sans-serif; color:rgba(255,255,255,0.9);
    font-size: var(--fs-td); font-weight:800;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    flex: 1; min-width: 0;
}

.phoneLine {
    font-family:'Space Mono',monospace;
    color: rgba(255,255,255,0.85);
    font-size: var(--fs-meta); font-weight:700;
    white-space:nowrap; flex-shrink:0;
}

/* debt amount — right side */
.balanceLine {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
}
.balanceLabel {
    font-family:'DM Sans',sans-serif;
    font-size: clamp(9px,0.9vw,10px); font-weight:900;
    color: rgba(255,255,255,0.5);
    text-transform:uppercase; letter-spacing:0.8px;
}
.balanceVal {
    font-family:'Space Mono',monospace;
    font-size: var(--fs-value); font-weight:900; color:#fff;
}
.balanceRed { color:#fca5a5 !important; }

/* ── SIDE ACTIONS — compact vertical stack ── */
.cardSideActions {
    display: flex;
    align-items: center;
    gap: clamp(6px,0.8vw,9px);
    flex-shrink: 0;
    margin-left: auto;
}

.logCallBtnSmall {
    background: var(--orange); color: var(--navy); border: none;
    border-radius: var(--radius-sm);
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size: var(--fs-btn); text-transform:uppercase; letter-spacing:1px;
    padding: clamp(7px,0.9vw,10px) clamp(12px,1.4vw,16px);
    cursor:pointer; display:inline-flex; align-items:center; gap:5px;
    transition: background 0.18s, transform 0.12s;
    white-space:nowrap;
}
.logCallBtnSmall:hover:not(:disabled) { background:#f09a48; transform:translateY(-1px); }
.logCallBtnSmall:disabled {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.22);
    cursor:not-allowed; font-size:var(--fs-2xs);
    transform:none;
}

.expandIcon {
    color: rgba(255,255,255,0.28); font-size:16px;
    transition: color 0.18s;
    flex-shrink: 0;
}
.missionCard:hover .expandIcon { color:var(--orange); }"""

new_card = """.missionCard {
    background: var(--panel-bg);
    border: 1.5px solid rgba(238,140,58,0.22);
    border-radius: var(--radius);
    box-shadow: 0 6px 24px rgba(0,0,0,0.18);
    transition: border-color 0.22s, box-shadow 0.22s, transform 0.18s;
    overflow: hidden;
    width: 100%;
}
.missionCard:hover {
    border-color: rgba(238,140,58,0.52);
    box-shadow: 0 10px 36px rgba(0,0,0,0.28);
    transform: translateY(-1px);
}
.cardLocked  { opacity:0.62; border-style:dashed; }
.cardLocked:hover { transform: none; box-shadow: 0 6px 24px rgba(0,0,0,0.18); }
.cardBacklog { border-color: rgba(239,68,68,0.32); }
.cardBacklog:hover { border-color: rgba(239,68,68,0.62); }

/* ── CARD HEADER — spacious two-line layout ── */
.cardHeader {
    display: flex;
    flex-direction: column;
    gap: clamp(10px,1.4vw,16px);
    padding: clamp(18px, 2.2vw, 28px) clamp(20px, 2.8vw, 32px);
    cursor: pointer;
    user-select: none;
}
.cardHeader:focus-visible { outline:2px solid var(--orange); outline-offset:-2px; border-radius:var(--radius); }

/* ── STATUS BADGE — inline, small ── */
.statusBadge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 9px;
    font-family:'DM Sans',sans-serif;
    font-size:clamp(8px,0.82vw,10px); font-weight:900; letter-spacing:0.8px;
    text-transform:uppercase;
    border-radius: 20px;
    flex-shrink: 0;
    white-space: nowrap;
}
.statusRed    { color:#fca5a5; background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); }
.statusBlue   { color:#93c5fd; background:rgba(59,130,246,0.1);  border:1px solid rgba(59,130,246,0.2); }
.statusGrey   { color:rgba(255,255,255,0.35); background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); }
.statusDefault{ color:rgba(255,255,255,0.4); background:transparent; border:1px solid rgba(255,255,255,0.1); }

/* ── CARD TOP ROW — Line 1: Plot ID + Debt ── */
.cardMain {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(10px,1.4vw,18px);
    width: 100%;
    flex-wrap: nowrap;
}

.cardTopRow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(10px,1.4vw,18px);
    width: 100%;
}
.cardTopRowLeft {
    display: flex;
    align-items: center;
    gap: clamp(8px,1.1vw,13px);
    min-width: 0;
    flex: 1;
}

/* ── PLOT ID — prominent, bold, Space Mono ── */
.plotId {
    font-family:'Space Mono',monospace;
    color: var(--orange);
    font-size: clamp(15px,1.7vw,20px);
    font-weight: 900;
    letter-spacing: 0.5px;
    line-height: 1;
    flex-shrink: 0;
    text-shadow: 0 0 16px rgba(238,140,58,0.25);
}

.backlogPill {
    font-family:'DM Sans',sans-serif; font-size:clamp(8px,0.82vw,9px);
    font-weight:900; text-transform:uppercase; letter-spacing:0.8px;
    background:rgba(239,68,68,0.18);
    border:1px solid rgba(239,68,68,0.4);
    border-radius:4px; padding: 2px 8px; color:#fca5a5; flex-shrink:0;
}

/* ── LINE 2: OWNER + PHONE — strong and readable ── */
.ownerLine {
    font-family:'DM Sans',sans-serif;
    color: rgba(255,255,255,0.95);
    font-size: clamp(13px,1.4vw,16px);
    font-weight: 900;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    flex: 1; min-width: 0;
    letter-spacing: 0.2px;
}

.phoneLine {
    font-family:'Space Mono',monospace;
    color: rgba(255,255,255,0.75);
    font-size: clamp(11px,1.15vw,14px);
    font-weight: 700;
    white-space:nowrap; flex-shrink:0;
    background: rgba(255,255,255,0.05);
    padding: clamp(3px,0.4vw,5px) clamp(8px,1vw,12px);
    border-radius: 5px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* ── DEBT AMOUNT — bold, right-aligned ── */
.balanceLine {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    flex-shrink: 0;
}
.balanceLabel {
    font-family:'DM Sans',sans-serif;
    font-size: clamp(8px,0.82vw,10px); font-weight:900;
    color: rgba(255,255,255,0.4);
    text-transform:uppercase; letter-spacing:1px;
}
.balanceVal {
    font-family:'Space Mono',monospace;
    font-size: clamp(14px,1.6vw,19px);
    font-weight: 900;
    color: #fff;
    line-height: 1;
}
.balanceRed { color:#fca5a5 !important; text-shadow: 0 0 10px rgba(239,68,68,0.3); }

/* ── SIDE ACTIONS ── */
.cardSideActions {
    display: flex;
    align-items: center;
    gap: clamp(8px,1vw,12px);
    flex-shrink: 0;
    margin-left: clamp(8px,1vw,14px);
}

.logCallBtnSmall {
    background: var(--orange);
    color: var(--navy);
    border: none;
    border-radius: var(--radius-sm);
    font-family:'DM Sans',sans-serif;
    font-weight: 900;
    font-size: clamp(10px,1vw,12px);
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: clamp(10px,1.2vw,14px) clamp(16px,1.8vw,22px);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 0.18s, transform 0.12s, box-shadow 0.18s;
    white-space: nowrap;
    box-shadow: 0 3px 10px rgba(238,140,58,0.28);
}
.logCallBtnSmall:hover:not(:disabled) {
    background: #f09a48;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(238,140,58,0.42);
}
.logCallBtnSmall:disabled {
    background: rgba(255,255,255,0.07);
    border: 1.5px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.25);
    cursor: not-allowed;
    font-size: clamp(9px,0.9vw,11px);
    transform: none;
    box-shadow: none;
}

.expandIcon {
    color: rgba(255,255,255,0.25);
    font-size: clamp(16px,1.8vw,20px);
    transition: color 0.18s;
    flex-shrink: 0;
}
.missionCard:hover .expandIcon { color:var(--orange); }"""

if old_card in content:
    content = content.replace(old_card, new_card)
    print("OK: card styles replaced")
else:
    print("MISSING: card styles block not found - checking for partial match")
    # Try replacing just the missionCard block
    if '.missionCard {' in content and '.expandIcon {' in content:
        print("INFO: found individual classes, will do targeted replacements")

# Also update font size variables to be larger
old_vars = """    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(8px,  0.85vw, 10px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-input:  clamp(11px, 1.1vw, 13px);
    --fs-th:     clamp(8px,  0.85vw, 10px);
    --fs-td:     clamp(10px, 1.05vw, 12px);
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);"""

new_vars = """    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(8px,  0.85vw, 10px);
    --fs-value:  clamp(13px, 1.4vw, 16px);
    --fs-tag:    clamp(8px,  0.82vw, 10px);
    --fs-input:  clamp(12px, 1.2vw, 14px);
    --fs-th:     clamp(9px,  0.9vw, 11px);
    --fs-td:     clamp(12px, 1.2vw, 14px);
    --fs-meta:   clamp(10px, 1vw,   12px);
    --fs-btn:    clamp(10px, 1vw,   12px);"""

if old_vars in content:
    content = content.replace(old_vars, new_vars)
    print("OK: font size variables updated")
else:
    print("MISSING: font size variables block")

# Update section header to have more breathing room
old_section = """.sectionHeader {
    display: inline-flex; align-items: center; gap: 7px;
    align-self: flex-start;
    font-family:'DM Sans',sans-serif;
    font-size:var(--fs-2xs); font-weight:900;
    color: rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:1.8px;
    padding: clamp(4px,0.5vw,6px) clamp(10px,1.3vw,16px);
    border-radius: 4px;
    background: rgba(26,46,48,0.7);
    border: 1px solid rgba(238,140,58,0.2);
    margin-bottom: clamp(3px,0.4vw,5px);
}"""

new_section = """.sectionHeader {
    display: inline-flex; align-items: center; gap: 8px;
    align-self: flex-start;
    font-family:'DM Sans',sans-serif;
    font-size:clamp(9px,0.9vw,11px); font-weight:900;
    color: rgba(255,255,255,0.8); text-transform:uppercase; letter-spacing:2px;
    padding: clamp(7px,0.9vw,10px) clamp(14px,1.7vw,20px);
    border-radius: 6px;
    background: rgba(26,46,48,0.8);
    border: 1.5px solid rgba(238,140,58,0.28);
    margin-bottom: clamp(6px,0.8vw,10px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}"""

if old_section in content:
    content = content.replace(old_section, new_section)
    print("OK: section header updated")
else:
    print("MISSING: section header block")

# Update card body padding
old_body = """.cardBody {
    border-top: 1px solid rgba(255,255,255,0.06);
    padding: clamp(8px,1vw,12px) clamp(10px,1.3vw,16px) clamp(10px,1.3vw,14px);
}"""

new_body = """.cardBody {
    border-top: 1px solid rgba(255,255,255,0.08);
    padding: clamp(14px,1.8vw,20px) clamp(20px,2.8vw,32px) clamp(16px,2vw,24px);
    background: rgba(0,0,0,0.12);
}"""

if old_body in content:
    content = content.replace(old_body, new_body)
    print("OK: card body padding updated")
else:
    print("MISSING: card body block")

# Update timing row to be more substantial
old_timing = """.timingRow {
    display: flex; align-items: center; flex-wrap: wrap;
    gap: clamp(5px,0.7vw,9px);
    font-size:var(--fs-xs); color:rgba(255,255,255,0.55); font-weight:700;
    background: rgba(0,0,0,0.2);
    padding: clamp(5px,0.6vw,7px) clamp(9px,1.1vw,12px);
    border-radius: var(--radius-xs);
    margin-bottom: clamp(6px,0.8vw,9px);
}"""

new_timing = """.timingRow {
    display: flex; align-items: center; flex-wrap: wrap;
    gap: clamp(8px,1vw,14px);
    font-family:'DM Sans',sans-serif;
    font-size:clamp(10px,1vw,12px); color:rgba(255,255,255,0.6); font-weight:800;
    background: rgba(0,0,0,0.25);
    padding: clamp(8px,1vw,11px) clamp(12px,1.5vw,18px);
    border-radius: var(--radius-sm);
    margin-bottom: clamp(10px,1.3vw,14px);
    border: 1px solid rgba(255,255,255,0.06);
}"""

if old_timing in content:
    content = content.replace(old_timing, new_timing)
    print("OK: timing row updated")
else:
    print("MISSING: timing row block")

# Update fin HUD cards to be more substantial
old_hud = """.finHUDCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    border-radius: var(--radius);
    padding: clamp(10px,1.4vw,16px);
    display: flex; flex-direction: column; gap: 3px;
}
.finHUDCard label {
    font-family:'DM Sans',sans-serif; font-size:var(--fs-2xs);
    font-weight:900; color:rgba(255,255,255,0.4);
    text-transform:uppercase; letter-spacing:1px;
}
.finHUDCard strong {
    font-family:'Space Mono',monospace;
    font-size:clamp(12px,1.5vw,17px);
    font-weight:700; word-break:break-all; line-height:1.1;
}
.finHUDCard span {
    font-size:var(--fs-2xs); color:rgba(255,255,255,0.25);
    font-family:'DM Sans',sans-serif; font-weight:800;
}"""

new_hud = """.finHUDCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    border-radius: var(--radius);
    padding: clamp(16px,2vw,22px) clamp(18px,2.2vw,26px);
    display: flex; flex-direction: column; gap: clamp(4px,0.5vw,6px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.14);
}
.finHUDCard label {
    font-family:'DM Sans',sans-serif; font-size:clamp(8px,0.82vw,10px);
    font-weight:900; color:rgba(255,255,255,0.45);
    text-transform:uppercase; letter-spacing:1.2px;
}
.finHUDCard strong {
    font-family:'Space Mono',monospace;
    font-size:clamp(14px,1.7vw,20px);
    font-weight:700; word-break:break-all; line-height:1.1;
}
.finHUDCard span {
    font-size:clamp(9px,0.9vw,11px); color:rgba(255,255,255,0.3);
    font-family:'DM Sans',sans-serif; font-weight:800;
}"""

if old_hud in content:
    content = content.replace(old_hud, new_hud)
    print("OK: fin HUD cards updated")
else:
    print("MISSING: fin HUD cards block")

# Update mission grid gap
old_grid = """.missionGrid { display: flex; flex-direction: column; gap: var(--gap-lg); }

.sectionGroup { display: flex; flex-direction: column; gap: clamp(3px,0.4vw,5px); }"""

new_grid = """.missionGrid { display: flex; flex-direction: column; gap: clamp(10px,1.5vw,16px); }

.sectionGroup { display: flex; flex-direction: column; gap: clamp(6px,0.8vw,9px); }"""

if old_grid in content:
    content = content.replace(old_grid, new_grid)
    print("OK: mission grid gap updated")
else:
    print("MISSING: mission grid gap block")

# Update responsive overrides for mobile
old_mobile = """@media (max-width: 480px) {
    .container { padding: 10px 10px 50px; }
    .finHUD { grid-template-columns: 1fr; }
    .finHUD .finHUDCard:last-child { grid-column:1; }
    .balanceLabel { display: none; }
    .cardHeader { gap: 8px; padding: 10px 12px; }
    .cardTopRow { flex-wrap: wrap; gap: 6px; }
    .cardTopRowLeft { flex-wrap: wrap; }
    .cardMain { flex-wrap: wrap; gap: 6px; }
    .ownerLine { font-size: 13px; }
    .phoneLine { font-size: 11px; width: 100%; }
    .cardSideActions { width: 100%; justify-content: flex-end; margin-left: 0; }
    .logCallBtnSmall { font-size: 10px; padding: 7px 12px; }
    .balanceVal { font-size: 12px; }
}"""

new_mobile = """@media (max-width: 480px) {
    .container { padding: 10px 10px 60px; }
    .finHUD { grid-template-columns: 1fr; }
    .finHUD .finHUDCard:last-child { grid-column:1; }
    .cardHeader { gap: 10px; padding: 16px 14px; }
    .cardTopRow { flex-wrap: wrap; gap: 8px; }
    .cardTopRowLeft { flex-wrap: wrap; }
    .cardMain { flex-wrap: wrap; gap: 8px; }
    .ownerLine { font-size: 14px; }
    .phoneLine { font-size: 12px; width: 100%; }
    .cardSideActions { width: 100%; justify-content: flex-end; margin-left: 0; margin-top: 4px; }
    .logCallBtnSmall { font-size: 11px; padding: 10px 14px; width: 100%; justify-content: center; }
    .balanceVal { font-size: 14px; }
    .plotId { font-size: 14px; }
}"""

if old_mobile in content:
    content = content.replace(old_mobile, new_mobile)
    print("OK: mobile overrides updated")
else:
    print("MISSING: mobile overrides block")

with open(css_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("\nDONE: RecoveryPortal.module.css patched successfully")