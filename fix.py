import os

def patch(path, old, new, label=""):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING: {label or path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label or path}")

print("=== FIX 1: Uniform page header font sizes (all pages match Dashboard) ===")

# --- LEDGER PAGE header title font fix ---
LEDGER_CSS = "erp-frontend/src/pages/Ledger/LedgerPage.module.css"
patch(LEDGER_CSS,
    "--fs-h1:     clamp(18px, 2.8vw, 26px);",
    "--fs-h1:     clamp(18px, 2.5vw, 24px);",
    "Ledger h1 font size uniform")

# --- INTAKE PAGE header title font fix ---
INTAKE_CSS = "erp-frontend/src/pages/Intake/IntakePage.module.css"
patch(INTAKE_CSS,
    "--fs-h1:    clamp(18px, 3vw,    30px);",
    "--fs-h1:    clamp(18px, 2.5vw, 24px);",
    "Intake h1 font size uniform")

# --- RECOVERY PAGE header title font fix ---
RECOVERY_CSS = "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css"
patch(RECOVERY_CSS,
    "--fs-h1:    clamp(16px,2.2vw,22px);",
    "--fs-h1:    clamp(18px,2.5vw,24px);",
    "Recovery h1 font size uniform")

# --- AUDIT PAGE header title font fix ---
AUDIT_CSS = "erp-frontend/src/pages/Audit/AuditPage.module.css"
patch(AUDIT_CSS,
    "--fs-h1:    clamp(17px, 2.5vw, 24px);",
    "--fs-h1:    clamp(18px, 2.5vw, 24px);",
    "Audit h1 font size uniform")

# --- PAYMENTS PAGE header title font fix ---
PAYMENTS_CSS = "erp-frontend/src/pages/Payments/PaymentsPage.module.css"
patch(PAYMENTS_CSS,
    ".title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: clamp(16px, 2.2vw, 22px); font-weight: 700; margin: 0; letter-spacing: 2px; }",
    ".title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: clamp(18px, 2.5vw, 24px); font-weight: 700; margin: 0; letter-spacing: 1.5px; }",
    "Payments h1 font size uniform")

# --- REPORTS PAGE header title font fix ---
REPORTS_CSS = "erp-frontend/src/pages/Reports/ReportHub.module.css"
patch(REPORTS_CSS,
    "--fs-h1:    clamp(18px, 2.5vw, 24px);",
    "--fs-h1:    clamp(18px, 2.5vw, 24px);",
    "Reports h1 already correct")

print("=== FIX 2: Recovery portal - ACTION QUEUE / FULL SCHEDULE never cut off ===")

patch(RECOVERY_CSS,
    ".modeSwitch { display:flex; background:var(--navy); padding:4px; border-radius:var(--radius-sm); border:1px solid var(--orange-border); gap:3px; overflow-x:auto; scrollbar-width:none; flex-wrap:nowrap; }",
    ".modeSwitch { display:flex; background:var(--navy); padding:4px; border-radius:var(--radius-sm); border:1px solid var(--orange-border); gap:3px; overflow-x:auto; scrollbar-width:none; flex-wrap:nowrap; min-width:0; flex-shrink:0; }",
    "Recovery modeSwitch no-shrink")

patch(RECOVERY_CSS,
    ".modeActive   { background:var(--orange); color:var(--navy); border:none; padding:7px 16px; border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:var(--fs-btn); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; }",
    ".modeActive   { background:var(--orange); color:var(--navy); border:none; padding:clamp(6px,0.9vw,8px) clamp(10px,1.3vw,16px); border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:clamp(9px,1vw,11px); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; flex-shrink:0; }",
    "Recovery modeActive no-shrink")

patch(RECOVERY_CSS,
    ".modeInactive { background:transparent; color:rgba(255,255,255,0.75); border:none; padding:7px 16px; border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:var(--fs-btn); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; transition:background 0.2s,color 0.2s; }",
    ".modeInactive { background:transparent; color:rgba(255,255,255,0.75); border:none; padding:clamp(6px,0.9vw,8px) clamp(10px,1.3vw,16px); border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:clamp(9px,1vw,11px); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; transition:background 0.2s,color 0.2s; flex-shrink:0; }",
    "Recovery modeInactive no-shrink")

# Fix headerRight on small screens to allow wrapping properly
patch(RECOVERY_CSS,
    ".headerRight {\n    display: flex;\n    align-items: center;\n    gap: clamp(8px, 1.2vw, 14px);\n    flex-shrink: 0;\n    flex-wrap: wrap;\n}",
    ".headerRight {\n    display: flex;\n    align-items: center;\n    gap: clamp(8px, 1.2vw, 14px);\n    flex-shrink: 0;\n    flex-wrap: nowrap;\n    overflow-x: auto;\n    scrollbar-width: none;\n}",
    "Recovery headerRight no-wrap scroll")

print("=== FIX 3: Ledger - ALL ARCHIVES active filter orange like Payments ALL TYPES ===")

# Replace the existing filterBtn + activeFilter in LedgerPage.module.css
# The current file has .filterBtn and .activeFilter at bottom - replace them
patch(LEDGER_CSS,
    """.filterBtn {
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    padding: 8px 16px;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}

.filterBtn:hover {
    background: rgba(238, 140, 58, 0.12) !important;
    color: #EE8C3A !important;
    border-color: var(--orange) !important;
}

.filterActive {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    box-shadow: 0 0 15px rgba(238, 140, 58, 0.4) !important;
}""",
    """.filterBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px,0.9vw,9px) clamp(12px,1.5vw,18px);
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px,0.95vw,11px);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
    flex-shrink: 0;
}

.filterBtn:hover {
    background: rgba(238, 140, 58, 0.12);
    color: #EE8C3A;
    border-color: #EE8C3A;
}

.filterActive,
.activeFilter {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    font-weight: 900 !important;
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.4) !important;
}""",
    "Ledger filterBtn unified with Payments style")

# Also fix activeFilter class that existed separately
patch(LEDGER_CSS,
    """/* Active/selected: orange bg + dark navy text — same as Payments "ALL TYPES" */
.activeFilter {
    background: #EE8C3A !important;
    border-color: #EE8C3A !important;
    color: #1a2e30 !important;
    font-weight: 900 !important;
    box-shadow: 0 2px 12px rgba(238, 140, 58, 0.4);
}""",
    """/* Active/selected: orange bg + dark navy text — same as Payments "ALL TYPES" */
/* .activeFilter is now merged into .filterActive above */""",
    "Ledger remove duplicate activeFilter")

print("=== FIX 4: Ledger - MAILO tag loses border/background, only text color ===")

patch(LEDGER_CSS,
    """.tenureTag {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    color: rgba(255,255,255,0.55);
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    padding: 1px 7px;
    border-radius: 3px;
    text-transform: uppercase;
    margin-right: 4px;
}""",
    """.tenureTag {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    color: rgba(255,255,255,0.45);
    background: transparent;
    border: none;
    padding: 0;
    text-transform: uppercase;
    margin-right: 4px;
}""",
    "Ledger tenureTag no box - plain text only")

print("=== FIX 5: Audit page - filter controls fully responsive, uniform buttons ===")

# Replace Audit filterGrid / hwSelectWrap / resetBtn to be fully responsive
patch(AUDIT_CSS,
    """.filterGrid {
    display: flex;
    align-items: flex-end;
    gap: var(--gap-md);
    flex-wrap: wrap;
}""",
    """.filterGrid {
    display: flex;
    align-items: flex-end;
    gap: var(--gap-md);
    flex-wrap: wrap;
    width: 100%;
}""",
    "Audit filterGrid full width")

patch(AUDIT_CSS,
    """/* Shrinks on small screens — no fixed min-width */
.hwSelectWrap {
    flex: 1 1 clamp(140px, 18vw, 220px);
    max-width: clamp(160px, 24vw, 260px);
    min-width: clamp(120px, 15vw, 160px);
}""",
    """/* Responsive select wraps */
.hwSelectWrap {
    flex: 1 1 clamp(130px, 18vw, 220px);
    max-width: clamp(150px, 24vw, 260px);
    min-width: clamp(120px, 15vw, 150px);
}""",
    "Audit hwSelectWrap responsive")

# Fix resetBtn to match filterBtn pattern with hover/active effects
patch(AUDIT_CSS,
    """.resetBtn {
    height: 52px; /* Matches dropdown height */
    flex: 0 0 auto;
    height: clamp(44px, 5.5vw, 52px);
    padding: 0 clamp(12px, 1.5vw, 20px);
    background: var(--navy);
    color: #fff;
    border: 1.5px solid rgba(255, 255, 255, 0.15);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: border-color 0.2s, color 0.2s, background 0.2s;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    text-transform: uppercase;
    white-space: nowrap;
    /* Align with bottom of select (which has a label above it) */
    margin-bottom: 0;
}
.resetBtn:hover { border-color: var(--orange); color: var(--orange); background: rgba(238,140,58,0.08); }
.resetBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }""",
    """.resetBtn {
    flex: 0 0 auto;
    height: clamp(44px, 5.5vw, 52px);
    padding: 0 clamp(12px, 1.5vw, 20px);
    background: rgba(26, 46, 48, 0.75);
    color: rgba(255, 255, 255, 0.85);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    text-transform: uppercase;
    white-space: nowrap;
    margin-bottom: 0;
}
.resetBtn:hover { border-color: #EE8C3A; color: #EE8C3A; background: rgba(238,140,58,0.12); }
.resetBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }""",
    "Audit resetBtn matches filterBtn style")

# Fix Audit HardwareSelect label color to be dark (on light controlHub bg)
patch(AUDIT_CSS,
    """/* HardwareSelect renders its own <label> */
.hwSelectWrap label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: var(--fs-label) !important;
    font-weight: 900 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    display: block !important;
    margin-bottom: clamp(3px, 0.4vw, 5px) !important;
}""",
    """/* HardwareSelect renders its own <label> */
.hwSelectWrap label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: var(--fs-label) !important;
    font-weight: 900 !important;
    color: rgba(26,46,48,0.65) !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    display: block !important;
    margin-bottom: clamp(3px, 0.4vw, 5px) !important;
}""",
    "Audit select label dark text on light bg")

# Add mobile responsive fix for audit filterGrid
patch(AUDIT_CSS,
    """@media (max-width: 480px) {
    .container {
        --gap-xl:  10px;
        --gap-lg:  7px;
        --gap-md:  4px;
        --fs-h1:   16px;
        --fs-time: 11px;
        --fs-action: 9px;
        --fs-target: 10px;
        --fs-btn:  8px;
    }""",
    """@media (max-width: 480px) {
    .container {
        --gap-xl:  10px;
        --gap-lg:  7px;
        --gap-md:  4px;
        --fs-h1:   16px;
        --fs-time: 11px;
        --fs-action: 9px;
        --fs-target: 10px;
        --fs-btn:  8px;
    }
    .filterGrid  { flex-direction: column; align-items: stretch; }
    .hwSelectWrap { min-width: 0; max-width: 100%; flex: 1 1 100%; }
    .resetBtn    { width: 100%; justify-content: center; height: clamp(38px, 10vw, 44px); }""",
    "Audit mobile filterGrid stacked")

print("=== FIX 6: Ledger - reduce spacing between table border boxes ===")

# The HardwarePanel has 30px padding. The tableScroll uses negative margin to break out.
# We want to keep the double-box look but reduce gap.
patch(LEDGER_CSS,
    """.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Small breathing room — rows don't touch the container edges */
    padding: clamp(4px, 0.5vw, 6px) clamp(6px, 0.8vw, 10px);
}""",
    """.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel padding for full-width table */
    margin: -30px;
    margin-bottom: 0;
}""",
    "Ledger tableScroll restore negative margin full-width")

print("=== FIX 7: Update LLM context guide ===")

GUIDE_LINES = [
    "# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE",
    "# For any AI assistant continuing work on this project",
    "# Last updated: May 2026 -- Priority 1 uniformity fixes applied",
    "",
    "## KEY CHANGES THIS SESSION",
    "- All page headers now uniform: Cinzel 700, clamp(18px,2.5vw,24px), same padding/margin",
    "- Recovery portal ACTION QUEUE/FULL SCHEDULE never cut off on mobile (nowrap scroll)",
    "- Ledger filter buttons now match Payments style: dark inactive, orange active",
    "- Ledger .tenureTag (MAILO etc) is now plain text only - no border or background box",
    "- Audit page filter controls fully responsive, resetBtn matches filterBtn hover style",
    "- Audit HardwareSelect labels use dark text (rgba(26,46,48,0.65)) on light controlHub bg",
    "- Audit mobile: filterGrid stacks vertically, all controls full width",
    "",
    "## STYLE STANDARDS (updated)",
    "### Filter Button Standard (ALL pages):",
    "- Inactive: background rgba(26,46,48,0.75), border rgba(255,255,255,0.18), color rgba(255,255,255,0.85)",
    "- Hover: background rgba(238,140,58,0.12), color #EE8C3A, border #EE8C3A",
    "- Active/selected: background #EE8C3A, color #1a2e30, border #EE8C3A, box-shadow orange glow",
    "",
    "### Page Header (ALL pages):",
    "- Title: Cinzel serif, color #1a2e30 (navy), clamp(18px,2.5vw,24px), font-weight 700",
    "- Subtitle: DM Sans 900, color #64748b, clamp(8px,0.85vw,10px), uppercase, letter-spacing 1px",
    "",
    "### Tenure/Type Tags in Ledger plot column:",
    "- NO background, NO border, NO padding - plain colored text only",
    "- .tenureTag: color rgba(255,255,255,0.45), transparent bg, no border",
    "",
    "See original LLM_CONTEXT_GUIDE.md for full project context.",
]

guide_content = "\n".join(GUIDE_LINES)
with open("LLM_CONTEXT_GUIDE_ADDENDUM.md", "w", encoding="utf-8") as f:
    f.write(guide_content)
print("  OK: LLM_CONTEXT_GUIDE_ADDENDUM.md written")

print("")
print("=== ALL DONE ===")
print("Next: git add -A && git commit -m 'UI uniformity: header sizes, filter buttons, tenure tag, audit responsive, recovery mobile' && git push")