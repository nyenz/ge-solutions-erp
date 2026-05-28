import os

# PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css
# We patch the card header and related styles only.

path = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 1. Replace card header layout
old = """.cardHeader {
    display: flex;
    align-items: center;
    gap: clamp(8px,1.1vw,14px);
    padding: clamp(8px,1vw,11px) clamp(10px,1.3vw,16px);
    cursor: pointer;
    user-select: none;
    min-height: 0;
}
.cardHeader:focus-visible { outline:2px solid var(--orange); outline-offset:-2px; border-radius:var(--radius); }"""

new = """.cardHeader {
    display: flex;
    flex-direction: column;
    gap: clamp(6px,0.8vw,9px);
    padding: clamp(10px,1.2vw,14px) clamp(12px,1.5vw,18px);
    cursor: pointer;
    user-select: none;
}
.cardHeader:focus-visible { outline:2px solid var(--orange); outline-offset:-2px; border-radius:var(--radius); }"""

if old in content:
    content = content.replace(old, new)
    print("OK: cardHeader layout patched")
else:
    print("MISSING: cardHeader layout")

# 2. Replace cardTopRow — now the first line: plot id + backlog pill left, owed right
old = """.cardTopRow {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}"""

new = """.cardTopRow {
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
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: cardTopRow patched")
else:
    print("MISSING: cardTopRow")

# 3. Replace cardMain — now the second line: name left, phone centre, actions right
old = """.cardMain {
    display: flex;
    align-items: center;
    gap: clamp(8px,1.1vw,14px);
    flex: 1;
    min-width: 0;
    overflow: hidden;
}"""

new = """.cardMain {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(8px,1vw,12px);
    width: 100%;
    flex-wrap: nowrap;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: cardMain patched")
else:
    print("MISSING: cardMain")

# 4. Increase plotId font size
old = """.plotId {
    font-family:'Space Mono',monospace;
    color: var(--orange);
    font-size:var(--fs-mono);
    font-weight: 900; letter-spacing:0.3px;
    line-height: 1;
    flex-shrink: 0;
}"""

new = """.plotId {
    font-family:'Space Mono',monospace;
    color: var(--orange);
    font-size: clamp(12px,1.3vw,15px);
    font-weight: 900; letter-spacing:0.3px;
    line-height: 1;
    flex-shrink: 0;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: plotId font size")
else:
    print("MISSING: plotId font size")

# 5. Increase ownerLine font size and remove overflow clipping
old = """.ownerLine {
    font-family:'DM Sans',sans-serif; color:rgba(255,255,255,0.9);
    font-size:var(--fs-sm); font-weight:800;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    flex: 1; min-width: 0;
}"""

new = """.ownerLine {
    font-family:'DM Sans',sans-serif; color:rgba(255,255,255,0.9);
    font-size: clamp(12px,1.3vw,14px); font-weight:800;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    flex: 1; min-width: 0;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: ownerLine font size")
else:
    print("MISSING: ownerLine font size")

# 6. Increase phoneLine font size and visibility
old = """.phoneLine {
    font-family:'Space Mono',monospace;
    color: rgba(255,255,255,0.38);
    font-size:var(--fs-2xs); font-weight:700;
    white-space:nowrap; flex-shrink:0;
}"""

new = """.phoneLine {
    font-family:'Space Mono',monospace;
    color: rgba(255,255,255,0.75);
    font-size: clamp(11px,1.1vw,13px); font-weight:700;
    white-space:nowrap; flex-shrink:0;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: phoneLine font size")
else:
    print("MISSING: phoneLine font size")

# 7. balanceLine — remove margin-left:auto since it's now in a flex row with justify-content
old = """.balanceLine {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
    margin-left: auto;
}"""

new = """.balanceLine {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: balanceLine margin removed")
else:
    print("MISSING: balanceLine margin")

# 8. Increase balanceLabel and balanceVal font sizes
old = """.balanceLabel {
    font-family:'DM Sans',sans-serif;
    font-size:var(--fs-2xs); font-weight:900;
    color: rgba(255,255,255,0.35);
    text-transform:uppercase; letter-spacing:0.8px;
}
.balanceVal {
    font-family:'Space Mono',monospace;
    font-size:var(--fs-mono); font-weight:900; color:#fff;
}"""

new = """.balanceLabel {
    font-family:'DM Sans',sans-serif;
    font-size: clamp(9px,0.9vw,10px); font-weight:900;
    color: rgba(255,255,255,0.5);
    text-transform:uppercase; letter-spacing:0.8px;
}
.balanceVal {
    font-family:'Space Mono',monospace;
    font-size: clamp(12px,1.3vw,14px); font-weight:900; color:#fff;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: balance font sizes")
else:
    print("MISSING: balance font sizes")

# 9. cardSideActions — keep it tighter, remove flex-shrink:0 conflict
old = """.cardSideActions {
    display: flex;
    align-items: center;
    gap: clamp(5px,0.6vw,8px);
    flex-shrink: 0;
}"""

new = """.cardSideActions {
    display: flex;
    align-items: center;
    gap: clamp(6px,0.8vw,9px);
    flex-shrink: 0;
    margin-left: auto;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: cardSideActions")
else:
    print("MISSING: cardSideActions")

# 10. Increase logCallBtnSmall font size
old = """.logCallBtnSmall {
    background: var(--orange); color: var(--navy); border: none;
    border-radius: var(--radius-sm);
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size:var(--fs-xs); text-transform:uppercase; letter-spacing:1px;
    padding: clamp(6px,0.75vw,8px) clamp(9px,1.1vw,13px);
    cursor:pointer; display:inline-flex; align-items:center; gap:4px;
    transition: background 0.18s, transform 0.12s;
    white-space:nowrap;
}"""

new = """.logCallBtnSmall {
    background: var(--orange); color: var(--navy); border: none;
    border-radius: var(--radius-sm);
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size: clamp(10px,1vw,12px); text-transform:uppercase; letter-spacing:1px;
    padding: clamp(7px,0.9vw,10px) clamp(12px,1.4vw,16px);
    cursor:pointer; display:inline-flex; align-items:center; gap:5px;
    transition: background 0.18s, transform 0.12s;
    white-space:nowrap;
}"""

if old in content:
    content = content.replace(old, new)
    print("OK: logCallBtnSmall font size")
else:
    print("MISSING: logCallBtnSmall font size")

# 11. Mobile: stack everything vertically at small screens
# Find the existing mobile media query for 480px and add card-specific rules
old = """@media (max-width: 480px) {
    .container { padding: 10px 10px 50px; }
    .finHUD { grid-template-columns: 1fr; }
    .finHUD .finHUDCard:last-child { grid-column:1; }
    .balanceLabel { display: none; }
}"""

new = """@media (max-width: 480px) {
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

if old in content:
    content = content.replace(old, new)
    print("OK: mobile stacking")
else:
    print("MISSING: mobile stacking")

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

# Now patch RecoveryPortal.jsx to update the renderCard function
# to use the new two-line layout and remove status badges

jsx_path = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'

with open(jsx_path, 'r', encoding='utf-8', errors='replace') as f:
    jsx = f.read()

old_header = """                {/* COMPACT SINGLE-ROW HEADER */}
                <div className={styles.cardHeader} onClick={toggle} role="button" tabIndex={0}
                    aria-expanded={isExpanded}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } }}>

                    <div className={styles.cardTopRow}>
                        <PaymentBadge badge={mission.plots?.[0]?.paymentHealthBadge} />
                        <span className={styles.plotId}>{plotNumbers}</span>
                        {mission.hasBacklogPlots && <span className={styles.backlogPill}>BACKLOG</span>}
                        <span className={`${styles.statusBadge} ${getStatusStyle(mission.missionStatus)}`}>
                            {mission.isLocked && <FiLock size={8} />}
                            {mission.missionStatus}
                        </span>
                    </div>

                    <div className={styles.cardMain}>
                        <span className={styles.ownerLine}>{mission.ownerName}</span>
                        <span className={styles.phoneLine}>{mission.phoneNumber}</span>
                    </div>

                    <div className={styles.balanceLine}>
                        <span className={styles.balanceLabel}>OWED</span>
                        <span className={`${styles.balanceVal} ${mission.hasBacklogPlots ? styles.balanceRed : ''}`}>
                            UGX {fmt(mission.totalDemand)}
                        </span>
                    </div>

                    <div className={styles.cardSideActions}>
                        <button className={styles.logCallBtnSmall}
                            disabled={mission.isLocked}
                            onClick={e => {
                                e.stopPropagation();
                                if (mission.plots?.[0]) {
                                    setCallModal({ open: true, mission: mission.plots[0] });
                                    setLogContent('');
                                }
                            }}
                            aria-label="Log call">
                            <FiPhoneCall size={11} />
                            {mission.isLocked ? 'LOCKED' : 'LOG CALL'}
                        </button>
                        <div className={styles.expandIcon} aria-hidden="true">
                            {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                        </div>
                    </div>
                </div>"""

new_header = """                {/* TWO-LINE CARD HEADER */}
                <div className={styles.cardHeader} onClick={toggle} role="button" tabIndex={0}
                    aria-expanded={isExpanded}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } }}>

                    {/* Line 1: Plot ID + Backlog Pill (left) | Total Owed (right) */}
                    <div className={styles.cardTopRow}>
                        <div className={styles.cardTopRowLeft}>
                            <PaymentBadge badge={mission.plots?.[0]?.paymentHealthBadge} />
                            <span className={styles.plotId}>{plotNumbers}</span>
                            {mission.hasBacklogPlots && <span className={styles.backlogPill}>BACKLOG</span>}
                        </div>
                        <div className={styles.balanceLine}>
                            <span className={styles.balanceLabel}>OWED</span>
                            <span className={`${styles.balanceVal} ${mission.hasBacklogPlots ? styles.balanceRed : ''}`}>
                                UGX {fmt(mission.totalDemand)}
                            </span>
                        </div>
                    </div>

                    {/* Line 2: Owner Name (left) | Phone (centre) | Actions (right) */}
                    <div className={styles.cardMain}>
                        <span className={styles.ownerLine}>{mission.ownerName}</span>
                        <span className={styles.phoneLine}>{mission.phoneNumber}</span>
                        <div className={styles.cardSideActions}>
                            <button className={styles.logCallBtnSmall}
                                disabled={mission.isLocked}
                                onClick={e => {
                                    e.stopPropagation();
                                    if (mission.plots?.[0]) {
                                        setCallModal({ open: true, mission: mission.plots[0] });
                                        setLogContent('');
                                    }
                                }}
                                aria-label="Log call">
                                <FiPhoneCall size={12} />
                                {mission.isLocked ? 'LOCKED' : 'LOG CALL'}
                            </button>
                            <div className={styles.expandIcon} aria-hidden="true">
                                {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                            </div>
                        </div>
                    </div>
                </div>"""

if old_header in jsx:
    jsx = jsx.replace(old_header, new_header)
    print("OK: JSX card header patched")
else:
    print("MISSING: JSX card header")

with open(jsx_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(jsx)

print("\nDone. Run: git add -A && git commit -m 'fix: recovery card two-line layout, larger fonts, mobile stack' && git push")