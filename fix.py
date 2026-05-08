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

# ======================================================================
# FIX 1: Audit page - ALL STAFF, ALL ACTIONS, RESET FILTERS on one line
#         same style/size as Ledger filter buttons
# ======================================================================
print("=== FIX 1: Audit filterGrid - all controls on one horizontal line ===")

AUDIT_CSS = "erp-frontend/src/pages/Audit/AuditPage.module.css"

# Replace controlHub layout to be column only for search, row for filters
patch(AUDIT_CSS,
    """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); }""",
    """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; }""",
    "Audit controlHub full width")

# Replace filterGrid to be a single horizontal flex row (matching ledger filterRail)
patch(AUDIT_CSS,
    """.filterGrid {
    display: flex;
    align-items: flex-end;
    gap: var(--gap-md);
    flex-wrap: wrap;
    width: 100%;
}""",
    """.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 1vw, 12px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    width: 100%;
    padding-bottom: 2px;
}
.filterGrid::-webkit-scrollbar { display: none; }""",
    "Audit filterGrid horizontal single row")

# Make hwSelectWrap shrink to compact size matching filter buttons
patch(AUDIT_CSS,
    """/* Responsive select wraps */
.hwSelectWrap {
    flex: 1 1 clamp(130px, 18vw, 220px);
    max-width: clamp(150px, 24vw, 260px);
    min-width: clamp(120px, 15vw, 150px);
}""",
    """/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 1 1 clamp(120px, 15vw, 200px);
    max-width: clamp(140px, 20vw, 220px);
    min-width: 0;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }""",
    "Audit hwSelectWrap compact")

# Override HardwareSelect label to be tiny like ledger filter labels
patch(AUDIT_CSS,
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
    """/* Hide HardwareSelect label - we use placeholder-style filter buttons inline */
.hwSelectWrap label {
    display: none !important;
}""",
    "Audit hide HardwareSelect labels")

# Make HardwareSelect trigger look like a filter button
patch(AUDIT_CSS,
    """/* Reset button — same height as HardwareSelect trigger (52px) */
@media (max-width: 600px) {
    .filters { flex-direction: column; width: 100%; gap: 10px; }
    .filters > div, .resetBtn { width: 100% !important; }
}
.resetBtn {
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
    """/* Reset button - same style as ledger filter buttons */
.resetBtn {
    flex: 0 0 auto;
    height: clamp(34px, 4vw, 40px);
    padding: 0 clamp(12px, 1.5vw, 18px);
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
    flex-shrink: 0;
}
.resetBtn:hover { border-color: #EE8C3A; color: #EE8C3A; background: rgba(238,140,58,0.12); }
.resetBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }""",
    "Audit resetBtn compact filter-button style")

# Override HardwareSelect box height to match filter buttons
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
    }
    .filterGrid  { flex-direction: column; align-items: stretch; }
    .hwSelectWrap { min-width: 0; max-width: 100%; flex: 1 1 100%; }
    .resetBtn    { width: 100%; justify-content: center; height: clamp(38px, 10vw, 44px); }""",
    """/* Override HardwareSelect box to be compact like filter buttons */
.hwSelectWrap .selectBox,
.hwSelectWrap [class*="selectBox"] {
    height: clamp(34px, 4vw, 40px) !important;
    padding: 0 clamp(10px, 1.3vw, 16px) !important;
    font-size: clamp(9px, 0.9vw, 11px) !important;
    letter-spacing: 1.5px !important;
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    border-radius: var(--radius-sm) !important;
}
.hwSelectWrap [class*="selectBox"]:hover {
    background: rgba(238, 140, 58, 0.12) !important;
    color: #EE8C3A !important;
    border-color: #EE8C3A !important;
}
.hwSelectWrap [class*="currentValue"] {
    color: rgba(255, 255, 255, 0.85) !important;
    font-size: clamp(9px, 0.9vw, 11px) !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    font-weight: 900 !important;
}
.hwSelectWrap [class*="icon"] {
    color: rgba(255, 255, 255, 0.5) !important;
}

@media (max-width: 480px) {
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
    .filterGrid  { flex-wrap: wrap; }
    .hwSelectWrap { flex: 1 1 calc(50% - 6px); min-width: 0; }
    .resetBtn    { flex: 1 1 100%; justify-content: center; }""",
    "Audit mobile responsive + HardwareSelect override")

# ======================================================================
# FIX 2: VISIBLE RECORDS badge - move below title on mobile, smaller
# ======================================================================
print("=== FIX 2: Audit - VISIBLE RECORDS badge repositioned ===")

# Fix pageHeader to stack properly and diagHUD below on mobile
patch(AUDIT_CSS,
    """.headerLeft { display: flex; flex-direction: column; gap: clamp(3px,0.4vw,5px); min-width: 0; flex: 1; }
.title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0; line-height: 1; }
.subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }
.diagHUD { display: flex; gap: var(--gap-md); }
.diagItem { background: var(--navy); color: #fff; padding: clamp(7px,1vw,11px) clamp(12px,1.6vw,18px); border-radius: var(--radius-sm); border: 1px solid var(--orange-border); font-family: 'DM Sans', sans-serif; font-size: var(--fs-meta); font-weight: 900; display: flex; align-items: center; gap: clamp(8px,1vw,12px); text-transform: uppercase; letter-spacing: 0.5px; }
.diagItem svg { color: var(--orange); }
.diagItem strong { font-family: 'Space Mono', monospace; }""",
    """.headerLeft { display: flex; flex-direction: column; gap: clamp(3px,0.4vw,5px); min-width: 0; flex: 1; }
.title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0; line-height: 1; }
.subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }
.diagHUD { display: flex; gap: var(--gap-md); flex-shrink: 0; align-self: flex-end; }
.diagItem {
    background: var(--navy);
    color: #fff;
    padding: clamp(4px,0.6vw,7px) clamp(8px,1.1vw,14px);
    border-radius: var(--radius-sm);
    border: 1px solid var(--orange-border);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.8vw, 10px);
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: clamp(5px,0.7vw,8px);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.diagItem svg { color: var(--orange); font-size: 12px; }
.diagItem strong { font-family: 'Space Mono', monospace; }""",
    "Audit diagHUD smaller, bottom-aligned")

# Fix pageHeader to allow wrapping so diagHUD drops to bottom on mobile
patch(AUDIT_CSS,
    """/* -- PAGE HEADER unified glass panel matching Dashboard -- */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 24px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}""",
    """/* -- PAGE HEADER unified glass panel matching Dashboard -- */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: clamp(6px, 1vw, 12px);
    margin-bottom: clamp(14px, 2vw, 24px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}""",
    "Audit pageHeader align-items flex-end so badge sits bottom-right")

# ======================================================================
# FIX 3: GLOBAL responsive input boxes and buttons via index.css
# ======================================================================
print("=== FIX 3: Global CSS - uniform responsive input/button sizing ===")

INDEX_CSS = "erp-frontend/src/index.css"

patch(INDEX_CSS,
    """/* Force all inputs and selects to fill their hardware containers */
input, select, textarea, .HardwareSelect_selectBox__xxxx {
    width: 100% !important;
    box-sizing: border-box;
}""",
    """/* ===== GLOBAL RESPONSIVE INPUT + BUTTON SIZING =====
   One place to control ALL input/button sizes across the entire app.
   Change these variables to rescale everything uniformly.
   Mobile: smaller; Tablet: medium; Desktop: full size.
   ===================================================== */
:root {
    /* Input height - scales with viewport */
    --input-height: clamp(38px, 5.5vw, 48px);
    /* Input font size */
    --input-font:   clamp(12px, 1.3vw, 14px);
    /* Input padding horizontal */
    --input-px:     clamp(10px, 1.4vw, 15px);
    /* Button height */
    --btn-height:   clamp(38px, 5.5vw, 48px);
    /* Button font */
    --btn-font:     clamp(10px, 1.1vw, 13px);
    /* Button padding horizontal */
    --btn-px:       clamp(14px, 2vw, 32px);
    /* Border radius */
    --input-radius: clamp(6px, 0.8vw, 8px);
    /* Label font */
    --label-font:   clamp(9px, 0.9vw, 11px);
    /* Header height */
    --header-height: clamp(52px, 7vw, 64px);
}

/* Apply to all native inputs */
input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
textarea {
    height: var(--input-height);
    font-size: var(--input-font) !important;
    padding-left: var(--input-px) !important;
    padding-right: var(--input-px) !important;
    border-radius: var(--input-radius) !important;
    box-sizing: border-box;
    width: 100% !important;
}

textarea {
    height: auto !important;
    min-height: clamp(80px, 12vw, 120px);
    padding-top: var(--input-px) !important;
    padding-bottom: var(--input-px) !important;
}

/* Labels */
label {
    font-size: var(--label-font);
}""",
    "Global responsive input/button CSS variables")

# ======================================================================
# FIX 4: HardwareInput - use global vars
# ======================================================================
print("=== FIX 4: HardwareInput - use global input height var ===")

HW_INPUT_CSS = "erp-frontend/src/components/common/HardwareInput.module.css"

patch(HW_INPUT_CSS,
    """.input {
    width: 100%; padding: 12px 15px; border: none; outline: none; 
    background: transparent; color: var(--navy); font-size: 15px; font-weight: 600;
}""",
    """.input {
    width: 100%;
    padding: 0 var(--input-px, 15px);
    height: var(--input-height, 44px);
    border: none;
    outline: none;
    background: transparent;
    color: var(--navy);
    font-size: var(--input-font, 14px);
    font-weight: 600;
    box-sizing: border-box;
}""",
    "HardwareInput use global vars")

patch(HW_INPUT_CSS,
    """.inputContainer {
    position: relative; background: #ffffff; border-radius: 8px;
    border: 2px solid rgba(238, 140, 58, 0.3); transition: border-color 0.3s ease, box-shadow 0.3s ease;
    display: flex; align-items: center;
}""",
    """.inputContainer {
    position: relative;
    background: #ffffff;
    border-radius: var(--input-radius, 8px);
    border: 2px solid rgba(238, 140, 58, 0.3);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
    display: flex;
    align-items: center;
    height: var(--input-height, 44px);
    overflow: hidden;
}""",
    "HardwareInput container height var")

# ======================================================================
# FIX 5: HardwareSelect - use global vars
# ======================================================================
print("=== FIX 5: HardwareSelect - use global vars ===")

HW_SELECT_CSS = "erp-frontend/src/components/common/HardwareSelect.module.css"

patch(HW_SELECT_CSS,
    """.selectBox {
    background: #ffffff;
    border-radius: 8px;
    border: 2px solid rgba(238, 140, 58, 0.3);
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: 0.3s ease;
    height: 52px;
}""",
    """.selectBox {
    background: #ffffff;
    border-radius: var(--input-radius, 8px);
    border: 2px solid rgba(238, 140, 58, 0.3);
    padding: 0 clamp(10px, 1.4vw, 18px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: 0.3s ease;
    height: var(--input-height, 44px);
}""",
    "HardwareSelect use global height var")

patch(HW_SELECT_CSS,
    """.currentValue { color: var(--navy); font-weight: 700; font-size: 15px; }""",
    """.currentValue { color: var(--navy); font-weight: 700; font-size: var(--input-font, 14px); }""",
    "HardwareSelect currentValue font var")

# ======================================================================
# FIX 6: HardwareButton - use global vars
# ======================================================================
print("=== FIX 6: HardwareButton - use global vars ===")

HW_BTN_CSS = "erp-frontend/src/components/common/HardwareButton.module.css"

patch(HW_BTN_CSS,
    """.btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 16px 32px;
    border-radius: 8px;
    border: none;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
}""",
    """.btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: clamp(8px, 1vw, 12px);
    padding: 0 var(--btn-px, 32px);
    height: var(--btn-height, 48px);
    border-radius: var(--input-radius, 8px);
    border: none;
    font-weight: 800;
    font-size: var(--btn-font, 13px);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
    white-space: nowrap;
}""",
    "HardwareButton use global vars")

# ======================================================================
# FIX 7: Login page - make inputs/button responsive
# ======================================================================
print("=== FIX 7: Login page inputs responsive ===")

LOGIN_CSS = "erp-frontend/src/pages/login/LoginPage.module.css"

patch(LOGIN_CSS,
    """.input {
    width: 100%; height: clamp(40px, 5.5vh, 48px); background: rgba(255, 255, 255, 0.1);
    border: 1.5px solid rgba(255, 255, 255, 0.2); border-radius: 8px; color: white;
    padding: 0 15px; font-size: clamp(14px, 1.7vh, 15px); outline: none; transition: 0.3s;
}""",
    """.input {
    width: 100%;
    height: var(--input-height, 44px);
    background: rgba(255, 255, 255, 0.1);
    border: 1.5px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--input-radius, 8px);
    color: white;
    padding: 0 var(--input-px, 15px);
    font-size: var(--input-font, 14px);
    outline: none;
    transition: 0.3s;
}""",
    "Login input global vars")

# ======================================================================
# FIX 8: Intake page inputs - use global vars
# ======================================================================
print("=== FIX 8: Intake page - hwInput uses global vars ===")

INTAKE_CSS = "erp-frontend/src/pages/Intake/IntakePage.module.css"

patch(INTAKE_CSS,
    """    --input-h:   clamp(40px, 5.5vw, 48px);""",
    """    --input-h:   var(--input-height, clamp(38px, 5.5vw, 48px));""",
    "Intake input-h uses global var")

patch(INTAKE_CSS,
    """.hwInput {
    width: 100% !important; height: var(--input-h);
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    padding: 0 clamp(10px, 1.2vw, 14px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-input);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--navy);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    appearance: none; -webkit-appearance: none;
    box-sizing: border-box; min-width: 0; display: block;
}""",
    """.hwInput {
    width: 100% !important;
    height: var(--input-height, clamp(38px, 5.5vw, 48px));
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--input-radius, var(--radius-sm));
    padding: 0 var(--input-px, clamp(10px, 1.2vw, 14px));
    font-family: 'DM Sans', sans-serif;
    font-size: var(--input-font, var(--fs-input));
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--navy);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    appearance: none; -webkit-appearance: none;
    box-sizing: border-box; min-width: 0; display: block;
}""",
    "Intake hwInput global vars")

patch(INTAKE_CSS,
    """.primaryCommitBtn {
    height: var(--input-h); padding: 0 clamp(20px, 2.5vw, 32px);""",
    """.primaryCommitBtn {
    height: var(--btn-height, var(--input-h)); padding: 0 var(--btn-px, clamp(20px, 2.5vw, 32px));""",
    "Intake primaryCommitBtn global btn vars")

# ======================================================================
# FIX 9: Folder page inputs - use global vars
# ======================================================================
print("=== FIX 9: FolderPage inputs - global vars ===")

FOLDER_CSS = "erp-frontend/src/pages/DigitalFolder/FolderPage.module.css"

patch(FOLDER_CSS,
    """    --input-h:         clamp(34px, 4.5vw, 40px);""",
    """    --input-h:         var(--input-height, clamp(34px, 4.5vw, 40px));""",
    "FolderPage input-h global var")

patch(FOLDER_CSS,
    """.hwInput {
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    color: var(--navy);
    padding: 0 clamp(10px, 1.4vw, 14px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-input);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    height: var(--input-h);
    outline: none;
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
    -webkit-appearance: none;
    appearance: none;
}""",
    """.hwInput {
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--input-radius, var(--radius-sm));
    color: var(--navy);
    padding: 0 var(--input-px, clamp(10px, 1.4vw, 14px));
    font-family: 'DM Sans', sans-serif;
    font-size: var(--input-font, var(--fs-input));
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    height: var(--input-height, var(--input-h));
    outline: none;
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
    -webkit-appearance: none;
    appearance: none;
}""",
    "FolderPage hwInput global vars")

patch(FOLDER_CSS,
    """.selectTrigger {
    width: 100%; height: var(--input-h);
    background: #ffffff; border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    padding: 0 clamp(10px, 1.4vw, 14px);""",
    """.selectTrigger {
    width: 100%; height: var(--input-height, var(--input-h));
    background: #ffffff; border: 1.5px solid #c8d6d7;
    border-radius: var(--input-radius, var(--radius-sm));
    padding: 0 var(--input-px, clamp(10px, 1.4vw, 14px));""",
    "FolderPage selectTrigger global vars")

# ======================================================================
# FIX 10: Settings page - inputs responsive
# ======================================================================
print("=== FIX 10: Settings page - inputs/buttons responsive ===")

SETTINGS_CSS = "erp-frontend/src/pages/settings/SettingsPage.module.css"

patch(SETTINGS_CSS,
    """.commitBtn {
    background: var(--orange); color: var(--navy); border: none;
    padding: clamp(9px,1.1vw,12px) clamp(16px,2vw,24px);
    border-radius: var(--radius-sm);""",
    """.commitBtn {
    background: var(--orange); color: var(--navy); border: none;
    padding: 0 var(--btn-px, clamp(16px,2vw,24px));
    height: var(--btn-height, clamp(38px, 5vw, 44px));
    border-radius: var(--input-radius, var(--radius-sm));""",
    "Settings commitBtn global vars")

# ======================================================================
# FIX 11: Update LLM guide addendum
# ======================================================================
print("=== FIX 11: Update LLM guide ===")

GUIDE_LINES = [
    "# GE SOLUTIONS ERP -- CONTEXT ADDENDUM",
    "# Last updated: May 2026",
    "",
    "## KEY CHANGES THIS SESSION",
    "- Audit page: ALL STAFF / ALL ACTIONS / RESET FILTERS now on single horizontal row",
    "  matching Ledger filter button style (dark inactive, orange hover/active)",
    "- Audit HardwareSelect labels hidden; selects styled like filter buttons",
    "- Audit VISIBLE RECORDS badge: smaller, bottom-right aligned, does not block title",
    "- GLOBAL RESPONSIVE SIZING: Added CSS variables in index.css:",
    "    --input-height: clamp(38px, 5.5vw, 48px)",
    "    --input-font:   clamp(12px, 1.3vw, 14px)",
    "    --input-px:     clamp(10px, 1.4vw, 15px)",
    "    --btn-height:   clamp(38px, 5.5vw, 48px)",
    "    --btn-font:     clamp(10px, 1.1vw, 13px)",
    "    --btn-px:       clamp(14px, 2vw, 32px)",
    "    --input-radius: clamp(6px, 0.8vw, 8px)",
    "    --label-font:   clamp(9px, 0.9vw, 11px)",
    "- All pages (Intake, FolderPage, Settings, Login, HardwareInput, HardwareSelect,",
    "  HardwareButton) now use these global vars for uniform size scaling",
    "- To change app-wide input/button sizes: edit :root vars in index.css ONLY",
    "",
    "## AUDIT FILTER LAYOUT RULE",
    "- filterGrid is flex-direction:row, flex-wrap:nowrap, overflow-x:auto",
    "- HardwareSelect labels are hidden via .hwSelectWrap label { display: none }",
    "- HardwareSelect boxes styled to match filterBtn via CSS attribute override",
    "- resetBtn same height and style as filter buttons",
    "",
    "See original LLM_CONTEXT_GUIDE.md for full project context.",
]

guide_content = "\n".join(GUIDE_LINES)
with open("LLM_CONTEXT_GUIDE_ADDENDUM.md", "w", encoding="utf-8") as f:
    f.write(guide_content)
print("  OK: LLM_CONTEXT_GUIDE_ADDENDUM.md written")

print("")
print("=== ALL DONE ===")
print("Run: git add -A && git commit -m 'Audit filter row uniform, VISIBLE RECORDS repositioned, global responsive input/button sizing' && git push")