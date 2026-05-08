import os

def patch(path, old, new, label=""):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING: {label or path}")
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label or path}")
    return True

def write_file(path, content, label=""):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  WRITTEN: {label or path}")

# ======================================================================
# FIX 1: SIDEBAR - Remove scrolling, compact NYENZ, show all links
# ======================================================================
print("=== FIX 1: Sidebar - remove scroll, compact, show all links ===")

SIDEBAR_CSS = "erp-frontend/src/components/layout/Sidebar.module.css"

patch(SIDEBAR_CSS,
    """.sidebar {
    height: 100vh;
    overflow-y: hidden;
    --sidebar-collapsed-width: 60px;
    --sidebar-width:           210px;

    width: var(--sidebar-width);
    /* Subtract header height so sidebar never overflows below viewport.
       Falls back to clamp value if the token isn't set on the root.    */
    height: calc(100vh - var(--header-height, clamp(52px, 7vw, 64px)));
    background: linear-gradient(180deg, #1a2e30 0%, #162a2c 50%, #1a2e30 100%);
    border-right: 2px solid rgba(238, 140, 58, 0.3);
    position: relative;
    display: flex;
    flex-direction: column;
    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
    z-index: 100;
}""",
    """.sidebar {
    --sidebar-collapsed-width: 52px;
    --sidebar-width:           200px;

    width: var(--sidebar-width);
    height: calc(100vh - var(--header-height, clamp(52px, 7vw, 64px)));
    background: linear-gradient(180deg, #1a2e30 0%, #162a2c 50%, #1a2e30 100%);
    border-right: 2px solid rgba(238, 140, 58, 0.3);
    position: relative;
    display: flex;
    flex-direction: column;
    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
    z-index: 100;
    overflow: hidden;
}""",
    "Sidebar - no scroll, narrower collapsed")

patch(SIDEBAR_CSS,
    """.collapsed { width: var(--sidebar-collapsed-width); }""",
    """.collapsed { width: var(--sidebar-collapsed-width); overflow: hidden; }""",
    "Sidebar collapsed overflow")

# Fix nav scroll to not scroll, just clip
patch(SIDEBAR_CSS,
    """.sidebarNav {
    padding: clamp(12px, 1.8vw, 22px) 0;
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: none;
}
.sidebarNav::-webkit-scrollbar { display: none; }""",
    """.sidebarNav {
    padding: clamp(6px, 1vw, 10px) 0;
    flex: 1;
    overflow-y: hidden;
    overflow-x: hidden;
}""",
    "Sidebar nav - no scroll")

# Compact nav items
patch(SIDEBAR_CSS,
    """.navItem {
    display: flex;
    align-items: center;
    gap: clamp(10px, 1.3vw, 16px);
    padding: clamp(11px, 1.4vw, 15px) clamp(10px, 1.2vw, 16px);
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    transition: background 0.25s, color 0.25s, border-color 0.25s;
    border-left: 3px solid transparent;
    white-space: nowrap;
    outline: none; /* handled by focus-visible below */
}""",
    """.navItem {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(8px, 1vw, 11px) clamp(8px, 1vw, 12px);
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    transition: background 0.25s, color 0.25s, border-color 0.25s;
    border-left: 3px solid transparent;
    white-space: nowrap;
    outline: none;
}""",
    "Sidebar nav items - more compact")

# Compact collapsed nav items
patch(SIDEBAR_CSS,
    """.collapsed .navItem {
    padding: clamp(13px, 1.6vw, 17px) 0;
    justify-content: center;
    border-left-width: 0;
    border-right: 3px solid transparent;
}""",
    """.collapsed .navItem {
    padding: clamp(9px, 1.1vw, 12px) 0;
    justify-content: center;
    border-left-width: 0;
    border-right: 3px solid transparent;
}""",
    "Sidebar collapsed nav items compact")

# Make footer much smaller
patch(SIDEBAR_CSS,
    """.sidebarFooter {
    padding: clamp(16px, 2.2vw, 26px) 0;
    background: rgba(0, 0, 0, 0.3);
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: clamp(70px, 9vw, 100px);
}""",
    """.sidebarFooter {
    padding: clamp(8px, 1vw, 12px) 0;
    background: rgba(0, 0, 0, 0.3);
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: clamp(40px, 5vw, 56px);
    flex-shrink: 0;
}""",
    "Sidebar footer compact")

# Smaller NYENZ branding
patch(SIDEBAR_CSS,
    """.branding {
    font-family: 'Space Mono', monospace;
    color: #EE8C3A;
    font-size: clamp(9px, 1vw, 13px);
    font-weight: 900;
    letter-spacing: 4px;
    text-transform: uppercase;
    transition: transform 0.4s ease, font-size 0.4s ease;
    white-space: nowrap;
}

/* Rotate into vertical serial-number style when collapsed */
.collapsed .branding {
    transform: rotate(-90deg);
    font-size: clamp(7px, 0.8vw, 10px);
    letter-spacing: 8px;
}

.version {
    font-size: 7px !important; opacity: 0.5;
    font-family: 'Space Mono', monospace;
    color: rgba(255, 255, 255, 0.15);
    font-size: clamp(6px, 0.65vw, 8px);
    font-weight: 700;
    margin-top: clamp(4px, 0.6vw, 8px);
    letter-spacing: 1px;
}
.collapsed .version {
    font-size: 7px !important; opacity: 0.5; display: none; }""",
    """.branding {
    font-family: 'Space Mono', monospace;
    color: #EE8C3A;
    font-size: clamp(7px, 0.75vw, 9px);
    font-weight: 900;
    letter-spacing: 3px;
    text-transform: uppercase;
    transition: transform 0.4s ease, font-size 0.4s ease;
    white-space: nowrap;
}
.collapsed .branding {
    transform: rotate(-90deg);
    font-size: clamp(6px, 0.65vw, 7px);
    letter-spacing: 6px;
}
.version { display: none; }""",
    "Sidebar branding smaller")

# Fix mobile sidebar - also no scroll
patch(SIDEBAR_CSS,
    """    .sidebar {
    height: 100vh;
    overflow-y: hidden;
        position: fixed;
        left: 0;
        /* Sit BELOW the header — top: 0 would slide under it and clip nav items */
        top: var(--header-height, clamp(52px, 7vw, 64px));
        height: calc(100vh - var(--header-height, clamp(52px, 7vw, 64px)));
        width: 210px;
        box-shadow: 15px 0 40px rgba(0, 0, 0, 0.7);
        overflow-y: auto;
    }""",
    """    .sidebar {
        position: fixed;
        left: 0;
        top: var(--header-height, clamp(52px, 7vw, 64px));
        height: calc(100vh - var(--header-height, clamp(52px, 7vw, 64px)));
        width: 200px;
        box-shadow: 15px 0 40px rgba(0, 0, 0, 0.7);
        overflow: hidden;
    }""",
    "Sidebar mobile - no scroll")

# Smaller icon
patch(SIDEBAR_CSS,
    """.navIcon {
    font-size: clamp(16px, 1.8vw, 21px);
    min-width: clamp(20px, 2.2vw, 26px);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}""",
    """.navIcon {
    font-size: clamp(14px, 1.5vw, 17px);
    min-width: clamp(18px, 1.8vw, 22px);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}""",
    "Sidebar nav icon smaller")

# Smaller nav text
patch(SIDEBAR_CSS,
    """.navText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 1vw, 12px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1px;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}""",
    """.navText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}""",
    "Sidebar nav text smaller")

# Section title smaller
patch(SIDEBAR_CSS,
    """.navSectionTitle {
    font-family: 'Space Mono', monospace;
    color: rgba(255, 255, 255, 0.2);
    font-size: clamp(6px, 0.65vw, 8px);
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0 clamp(10px, 1.2vw, 16px);
    margin-bottom: clamp(8px, 1vw, 14px);
    white-space: nowrap;
}""",
    """.navSectionTitle {
    font-family: 'Space Mono', monospace;
    color: rgba(255, 255, 255, 0.2);
    font-size: 6px;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0 clamp(8px, 1vw, 12px);
    margin-bottom: clamp(4px, 0.6vw, 8px);
    white-space: nowrap;
}""",
    "Sidebar section title smaller")

patch(SIDEBAR_CSS,
    """.navSection { margin-bottom: clamp(12px, 1.8vw, 22px); }""",
    """.navSection { margin-bottom: clamp(4px, 0.6vw, 8px); }""",
    "Sidebar section margin smaller")

# ======================================================================
# FIX 2: AUDIT PAGE - Major responsive overhaul
# ======================================================================
print("=== FIX 2: Audit page CSS - full responsive fix ===")

AUDIT_CSS = "erp-frontend/src/pages/Audit/AuditPage.module.css"

# Full replacement of the audit CSS for filter + mobile sections
audit_css_content = open(AUDIT_CSS, "r", encoding="utf-8", errors="replace").read()

# Fix filterGrid - single horizontal row, no wrapping, proper overflow
old_filter_grid = """.filterGrid {
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
.filterGrid::-webkit-scrollbar { display: none; }"""

new_filter_grid = """.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: visible;
    scrollbar-width: none;
    width: 100%;
    padding-bottom: 4px;
    position: relative;
    z-index: 10;
}
.filterGrid::-webkit-scrollbar { display: none; }"""

patch(AUDIT_CSS, old_filter_grid, new_filter_grid, "Audit filterGrid overflow-y visible")

# Fix hwSelectWrap - needs z-index for dropdown visibility
old_hw_select_wrap = """/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 1 1 clamp(120px, 15vw, 200px);
    max-width: clamp(140px, 20vw, 220px);
    min-width: 0;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }

/* Hide HardwareSelect label - we use placeholder-style filter buttons inline */
.hwSelectWrap label {
    display: none !important;
}"""

new_hw_select_wrap = """/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 1 1 clamp(110px, 14vw, 190px);
    max-width: clamp(130px, 18vw, 210px);
    min-width: 0;
    position: relative;
    z-index: 50;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }

/* Hide HardwareSelect label */
.hwSelectWrap label {
    display: none !important;
}"""

patch(AUDIT_CSS, old_hw_select_wrap, new_hw_select_wrap, "Audit hwSelectWrap z-index")

# Fix reset button size - match filter buttons properly
old_reset_btn = """.resetBtn {
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
.resetBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }"""

new_reset_btn = """.resetBtn {
    flex: 0 0 auto;
    height: clamp(34px, 4vw, 40px);
    padding: 0 clamp(10px, 1.3vw, 16px);
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
    display: inline-flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: clamp(4px, 0.6vw, 6px);
    text-transform: uppercase;
    white-space: nowrap;
    flex-shrink: 0;
}
.resetBtn:hover { border-color: #EE8C3A; color: #EE8C3A; background: rgba(238,140,58,0.12); }
.resetBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }"""

patch(AUDIT_CSS, old_reset_btn, new_reset_btn, "Audit resetBtn proper sizing")

# Fix VISIBLE RECORDS badge - smaller on mobile
old_diag_item = """.diagItem {
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
.diagItem strong { font-family: 'Space Mono', monospace; }"""

new_diag_item = """.diagItem {
    background: var(--navy);
    color: #fff;
    padding: clamp(3px,0.4vw,6px) clamp(6px,0.9vw,12px);
    border-radius: var(--radius-sm);
    border: 1px solid var(--orange-border);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(7px, 0.75vw, 9px);
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: clamp(4px,0.5vw,7px);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.diagItem svg { color: var(--orange); font-size: 10px; }
.diagItem strong { font-family: 'Space Mono', monospace; }"""

patch(AUDIT_CSS, old_diag_item, new_diag_item, "Audit diagItem smaller")

# Fix HardwareSelect override to ensure dropdowns appear above other content
old_hw_select_override = """/* Override HardwareSelect box to be compact like filter buttons */
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
}"""

new_hw_select_override = """/* Override HardwareSelect box to be compact like filter buttons */
.hwSelectWrap .selectBox,
.hwSelectWrap [class*="selectBox"] {
    height: clamp(34px, 4vw, 40px) !important;
    padding: 0 clamp(8px, 1.1vw, 14px) !important;
    font-size: clamp(9px, 0.9vw, 11px) !important;
    letter-spacing: 1.5px !important;
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    border-radius: var(--radius-sm) !important;
    overflow: visible !important;
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
.hwSelectWrap [class*="dropdown"] {
    z-index: 9999 !important;
    position: absolute !important;
}"""

patch(AUDIT_CSS, old_hw_select_override, new_hw_select_override, "Audit HardwareSelect dropdown z-index fix")

# Fix mobile for audit - better layout
old_audit_mobile = """@media (max-width: 768px) {
    .header      { flex-direction: column; align-items: flex-start; }
    .controlHub  { gap: var(--gap-md); }
    .filterGrid  { flex-direction: column; width: 100%; align-items: stretch; }
    .hwSelectWrap { max-width: 100%; min-width: 0; flex: 1 1 100%; }
    .resetBtn    { width: 100%; justify-content: center; }
    .logMain     { grid-template-columns: 1fr 1fr; gap: var(--gap-md); align-items: start; }
    .timeMark    { grid-column: 1; }
    .actionMark  { grid-column: 2; justify-self: end; text-align: right; }
    .targetMark  { grid-column: 1 / span 2; margin-top: var(--gap-md); }
    .iconChassis { display: none; }
    .actionMeta  { align-items: flex-end; }
}"""

new_audit_mobile = """@media (max-width: 768px) {
    .header      { flex-direction: column; align-items: flex-start; }
    .controlHub  { gap: var(--gap-md); }
    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        width: 100%;
        gap: 6px;
        padding-bottom: 4px;
    }
    .hwSelectWrap { flex: 0 0 auto; max-width: 140px; min-width: 110px; }
    .resetBtn    { flex: 0 0 auto; padding: 0 12px; }
    .logMain     { grid-template-columns: 1fr 1fr; gap: var(--gap-md); align-items: start; }
    .timeMark    { grid-column: 1; }
    .actionMark  { grid-column: 2; justify-self: end; text-align: right; }
    .targetMark  { grid-column: 1 / span 2; margin-top: var(--gap-md); }
    .iconChassis { display: none; }
    .actionMeta  { align-items: flex-end; }
}"""

patch(AUDIT_CSS, old_audit_mobile, new_audit_mobile, "Audit mobile - keep filter row horizontal")

# Fix 480px breakpoint too
old_audit_480 = """@media (max-width: 480px) {
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
    .resetBtn    { flex: 1 1 100%; justify-content: center; }"""

new_audit_480 = """@media (max-width: 480px) {
    .container {
        --gap-xl:  10px;
        --gap-lg:  7px;
        --gap-md:  4px;
        --fs-h1:   15px;
        --fs-time: 10px;
        --fs-action: 8px;
        --fs-target: 9px;
        --fs-btn:  8px;
    }
    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 5px;
    }
    .hwSelectWrap { flex: 0 0 auto; max-width: 120px; min-width: 100px; }
    .resetBtn    { flex: 0 0 auto; padding: 0 10px; font-size: 8px; height: 32px; }"""

patch(AUDIT_CSS, old_audit_480, new_audit_480, "Audit 480px - keep filter row horizontal")

# Fix the timelineFrame to have overflow visible so dropdowns escape
old_timeline = """.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: hidden; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }"""
new_timeline = """.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: visible; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }
.timelineFrameInner { overflow: hidden; border-radius: var(--radius); }"""
patch(AUDIT_CSS, old_timeline, new_timeline, "Audit timelineFrame overflow visible")

# Fix controlHub to have overflow visible
old_control_hub = """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; }"""
new_control_hub = """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; position: relative; z-index: 20; overflow: visible; }"""
patch(AUDIT_CSS, old_control_hub, new_control_hub, "Audit controlHub z-index")

# ======================================================================
# FIX 3: HardwareSelect - dropdown must appear above everything
# ======================================================================
print("=== FIX 3: HardwareSelect - dropdown z-index fix ===")

HW_SELECT_CSS = "erp-frontend/src/components/common/HardwareSelect.module.css"

patch(HW_SELECT_CSS,
    """.dropdown {
    position: absolute;
    top: calc(100% + 5px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: 8px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5); /* HEAVIER SHADOW FOR DEPTH */
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
}""",
    """.dropdown {
    position: absolute;
    top: calc(100% + 5px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: 8px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5);
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
    z-index: 9999;
}""",
    "HardwareSelect dropdown z-index 9999")

# Also fix the openWrapper
patch(HW_SELECT_CSS,
    """/* FIXED: This pulls the field to the front when clicked */
.openWrapper {
    z-index: 9999 !important;
}""",
    """/* FIXED: This pulls the field to the front when clicked */
.openWrapper {
    z-index: 9999 !important;
    overflow: visible !important;
}""",
    "HardwareSelect openWrapper overflow visible")

# ======================================================================
# FIX 4: LEDGER PAGE - Mobile list improvements
# ======================================================================
print("=== FIX 4: Ledger page - mobile list improvements ===")

LEDGER_CSS = "erp-frontend/src/pages/Ledger/LedgerPage.module.css"

# Better mobile table
old_ledger_responsive = """@media (max-width: 768px) {
    .searchBlock { max-width: 100%; }
    .ownerName   { max-width: clamp(80px, 30vw, 140px); }
}
@media (max-width: 480px) {
    .jointBadge  { display: none; } /* Too cramped on small phones */
    .pctLabel    { display: none; }
}"""

new_ledger_responsive = """@media (max-width: 768px) {
    .searchBlock { max-width: 100%; }
    .ownerName   { max-width: clamp(80px, 28vw, 140px); }
    .tableScroll { margin: -20px; margin-bottom: 0; }
    .ledgerTable { min-width: clamp(560px, 90vw, 900px); }
    .ledgerTable th { padding: 9px 10px; font-size: 7px; }
    .ledgerTable td { padding: 8px 10px; }
    .pagination { padding: 8px 10px; }
}
@media (max-width: 480px) {
    .jointBadge  { display: none; }
    .pctLabel    { display: none; }
    .tableScroll { margin: -15px; margin-bottom: 0; }
    .ledgerTable { min-width: 480px; font-size: 10px; }
    .plotCell strong { font-size: 10px; }
    .ownerName { max-width: 90px; font-size: 10px; }
    .ownerPhone { font-size: 9px; }
    .debtAmount, .debtCritical { font-size: 10px; }
    .boxTag { font-size: 8px; padding: 2px 5px; }
}"""

patch(LEDGER_CSS, old_ledger_responsive, new_ledger_responsive, "Ledger mobile improvements")

# Fix tableScroll margin for HardwarePanel
old_table_scroll = """.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel's 30px padding to use full width */
    margin: -30px;
    margin-bottom: 0;
}"""
new_table_scroll = """.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel's 30px padding to use full width */
    margin: -30px;
    margin-bottom: 0;
    -webkit-overflow-scrolling: touch;
}"""
patch(LEDGER_CSS, old_table_scroll, new_table_scroll, "Ledger tableScroll touch scrolling")

# ======================================================================
# FIX 5: PAYMENTS PAGE - Apply ledger-style design
# ======================================================================
print("=== FIX 5: Payments page - ledger-style design ===")

PAYMENTS_CSS_FULL = """.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --red:           #ef4444;
    --green:         #10b981;
    --cyan:          #06b6d4;

    --gap-xl:    clamp(14px, 2vw, 22px);
    --gap-lg:    clamp(10px, 1.5vw, 18px);
    --gap-md:    clamp(7px,  1.1vw, 13px);
    --radius:    10px;
    --radius-sm: 6px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(8px,  0.85vw, 10px);
    --fs-label:  clamp(7px,  0.75vw, 9px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-input:  clamp(11px, 1.1vw, 13px);
    --fs-th:     clamp(7px,  0.78vw, 9px);
    --fs-td:     clamp(10px, 1.05vw, 12px);
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);

    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}

@keyframes warmBoot {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── PAGE HEADER ── */
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
}
.headerLeft { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; margin: 0; letter-spacing: 1.5px; text-transform: uppercase; line-height: 1; }
.subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

.refreshBtn {
    background: rgba(26,46,48,0.08);
    border: 1px solid rgba(26,46,48,0.15);
    color: #1a2e30;
    border-radius: 8px;
    padding: 8px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    transition: all 0.2s;
    flex-shrink: 0;
    height: var(--btn-height, clamp(36px, 4.5vw, 44px));
}
.refreshBtn:hover { background: #EE8C3A; color: #fff; border-color: #EE8C3A; }

/* ── SUMMARY CARDS ── */
.summaryRow {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 20px);
}
.sumCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    border-radius: var(--radius);
    padding: clamp(12px, 1.5vw, 18px);
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.sumCard label { font-family: 'DM Sans', sans-serif; font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 1px; }
.sumCard strong { font-family: 'Space Mono', monospace; font-size: var(--fs-value); color: #fff; font-weight: 700; word-break: break-all; }
.sumCard span { font-size: var(--fs-label); color: rgba(255,255,255,0.35); }

/* ── CONTROLS ── */
.controls {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: clamp(14px, 2vw, 20px);
}

.searchWrap {
    position: relative;
    display: flex;
    align-items: center;
    background: #fff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    height: clamp(36px, 4.5vw, 44px);
    max-width: clamp(300px, 50vw, 560px);
    transition: border-color 0.2s;
}
.searchWrap:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.searchIcon { position: absolute; left: 12px; color: #EE8C3A; font-size: clamp(14px, 1.5vw, 17px); pointer-events: none; }
.searchInput {
    width: 100%; border: none; outline: none; background: transparent;
    color: #1a2e30; padding: 0 36px 0 38px;
    font-family: 'DM Sans', sans-serif; font-weight: 800;
    font-size: var(--fs-input);
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.clearBtn {
    position: absolute; right: 8px; background: transparent; border: none;
    cursor: pointer; color: rgba(26,46,48,0.4); display: flex;
    align-items: center; padding: 4px; border-radius: 4px;
}
.clearBtn:hover { color: #1a2e30; }

/* ── FILTER ROW - matches ledger style ── */
.filterRow {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: clamp(6px, 1vw, 10px);
    padding-bottom: 4px;
    scrollbar-width: none;
}
.filterRow::-webkit-scrollbar { display: none; }

.filterBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(10px, 1.3vw, 16px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    flex-shrink: 0;
}
.filterBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.filterActive {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    box-shadow: 0 0 12px rgba(238, 140, 58, 0.35);
}

/* ── TABLE ── */
.tableWrap {
    overflow-x: auto;
    border-radius: var(--radius);
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    box-shadow: 0 8px 28px rgba(0,0,0,0.15);
    -webkit-overflow-scrolling: touch;
}
.table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    min-width: clamp(600px, 85vw, 1000px);
}
.table thead tr { border-bottom: 2px solid var(--orange); }
.table th {
    background: #162a2c;
    padding: clamp(10px, 1.3vw, 15px) clamp(10px, 1.3vw, 16px);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-th);
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    text-align: left;
    white-space: nowrap;
}
.row {
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: background 0.15s, border-left-color 0.15s;
    border-left: 3px solid transparent;
}
.row:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.table td {
    padding: clamp(9px, 1.2vw, 13px) clamp(10px, 1.3vw, 16px);
    color: rgba(255,255,255,0.9);
    vertical-align: middle;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-td);
}

.dateCell { display: flex; flex-direction: column; gap: 2px; white-space: nowrap; font-weight: 700; }
.time { font-family: 'Space Mono', monospace; font-size: var(--fs-label); opacity: 0.45; }
.plotNum { font-family: 'Space Mono', monospace; color: #EE8C3A; font-size: var(--fs-value); font-weight: 700; letter-spacing: 0.5px; }
.ownerCell { font-weight: 700; color: #fff; max-width: clamp(100px, 14vw, 180px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.typeBadge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: clamp(2px, 0.3vw, 4px) clamp(6px, 0.8vw, 9px);
    border-radius: 4px;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-transform: uppercase;
    white-space: nowrap;
    letter-spacing: 0.5px;
}
.amount { font-family: 'Space Mono', monospace; font-size: var(--fs-value); font-weight: 700; }
.balance { font-family: 'Space Mono', monospace; font-size: var(--fs-meta); color: rgba(255,255,255,0.5); }
.recorder { display: inline-flex; align-items: center; gap: 5px; font-size: var(--fs-meta); color: rgba(255,255,255,0.6); }
.notesCell { font-style: italic; color: rgba(255,255,255,0.45); max-width: clamp(100px, 14vw, 180px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--fs-meta); }
.goBtn {
    background: rgba(238,140,58,0.1); border: 1px solid rgba(238,140,58,0.35);
    color: #EE8C3A; border-radius: 6px; padding: 6px; cursor: pointer;
    display: flex; align-items: center; transition: all 0.2s;
}
.goBtn:hover { background: #EE8C3A; color: #1a2e30; }

.loading, .empty {
    text-align: center;
    padding: clamp(40px, 7vw, 70px) 20px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-meta);
    color: rgba(255,255,255,0.3);
    text-transform: uppercase;
    letter-spacing: 2px;
}

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
    .summaryRow { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
    .summaryRow { grid-template-columns: 1fr; gap: 8px; }
    .searchWrap { max-width: 100%; }
    .filterRow { gap: 6px; }
    .table { min-width: 560px; }
}
@media (max-width: 480px) {
    .summaryRow { grid-template-columns: 1fr 1fr; }
    .sumCard strong { font-size: 13px; }
    .table { min-width: 500px; }
    .table th { padding: 8px; font-size: 7px; letter-spacing: 1px; }
    .table td { padding: 8px; }
    .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }
}
"""

write_file("erp-frontend/src/pages/Payments/PaymentsPage.module.css", PAYMENTS_CSS_FULL, "Payments CSS full rewrite - ledger style")

# ======================================================================
# FIX 6: SETTINGS PAGE - Responsive inputs
# ======================================================================
print("=== FIX 6: Settings page - responsive inputs ===")

SETTINGS_CSS = "erp-frontend/src/pages/settings/SettingsPage.module.css"

# Fix workstationGrid to be responsive
patch(SETTINGS_CSS,
    """.workstationGrid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--gap-xl); align-items: start; }""",
    """.workstationGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(clamp(280px, 45vw, 500px), 1fr)); gap: var(--gap-xl); align-items: start; }""",
    "Settings workstationGrid responsive")

# Fix HardwareInput within settings to use global vars
# The inputs in settings use HardwareInput component which already uses global vars
# But the form inputs inside modals need fixing
patch(SETTINGS_CSS,
    """.modalBody   { padding-top: clamp(7px,0.9vw,11px); display: flex; flex-direction: column; gap: var(--gap-md); }""",
    """.modalBody   { padding-top: clamp(7px,0.9vw,11px); display: flex; flex-direction: column; gap: var(--gap-md); width: 100%; }""",
    "Settings modalBody full width")

# Fix eyeBtn to work with variable height inputs
patch(SETTINGS_CSS,
    """.eyeBtn {
    position: absolute;
    right: clamp(8px,1vw,12px);
    /* HardwareInput: label (~22px) + input (~42px) = ~64px total.
       Eye should sit in the INPUT portion, vertically centered.
       top ≈ label_height + (input_height / 2) - (icon / 2)
       ≈ 22px + 21px - 9px = 34px → use top: clamp(30px,4.5vw,38px)        */
    top: clamp(28px, 4vw, 36px);""",
    """.eyeBtn {
    position: absolute;
    right: clamp(8px,1vw,12px);
    top: calc(var(--label-font, 10px) + 12px + var(--input-height, 44px) / 2 - 9px);""",
    "Settings eyeBtn responsive top position")

# Fix 900px breakpoint for settings
patch(SETTINGS_CSS,
    """@media (max-width: 900px) {
    .workstationGrid { grid-template-columns: 1fr; }
    .dualRow         { grid-template-columns: 1fr; }
    .header          { flex-direction: column; align-items: flex-start; }
}""",
    """@media (max-width: 900px) {
    .workstationGrid { grid-template-columns: 1fr; }
    .dualRow         { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 640px) {
    .dualRow { grid-template-columns: 1fr; }
}""",
    "Settings 900px responsive - keep dual row on medium screens")

# Fix staffStream max-height
patch(SETTINGS_CSS,
    """.staffStream {
    display: flex; flex-direction: column; gap: var(--gap-md);
    max-height: clamp(260px,36vw,400px); overflow-y: auto;""",
    """.staffStream {
    display: flex; flex-direction: column; gap: var(--gap-md);
    max-height: clamp(300px, 40vh, 480px); overflow-y: auto;""",
    "Settings staffStream better max-height")

# ======================================================================
# FIX 7: GLOBAL - Ensure all native select elements scale too
# ======================================================================
print("=== FIX 7: Global index.css - comprehensive responsive sizing ===")

INDEX_CSS = "erp-frontend/src/index.css"

old_global_inputs = """/* Apply to all native inputs */
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
}"""

new_global_inputs = """/* Apply to all native inputs */
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
}

/* Scrollable container helper */
.scroll-x-touch {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
}"""

patch(INDEX_CSS, old_global_inputs, new_global_inputs, "Global - add touch scrolling helper")

# ======================================================================
# FIX 8: LLM Guide update
# ======================================================================
print("=== FIX 8: LLM Guide Addendum update ===")

guide_lines = [
    "# GE SOLUTIONS ERP -- CONTEXT ADDENDUM",
    "# Last updated: May 2026 - Comprehensive Mobile + Responsive Fix",
    "",
    "## KEY CHANGES THIS SESSION",
    "",
    "### SIDEBAR FIXES",
    "- Sidebar is now NOT scrollable -- all nav items always visible",
    "- Reduced NYENZ branding section (smaller font, less padding)",
    "- Reduced nav item padding for compactness",
    "- Collapsed width reduced from 60px to 52px",
    "",
    "### AUDIT PAGE FIXES",
    "- Filter row (ALL STAFF, ALL ACTIONS, RESET FILTERS) stays on ONE horizontal row on all screen sizes",
    "- Filter row is overflow-x: auto with nowrap -- never wraps to new lines",
    "- HardwareSelect dropdowns now appear above other content (z-index: 9999)",
    "- VISIBLE RECORDS badge made smaller on mobile",
    "- RESET FILTERS button same height and style as other filter buttons",
    "- controlHub has z-index: 20 and overflow: visible",
    "",
    "### LEDGER PAGE FIXES",
    "- Table has -webkit-overflow-scrolling: touch for mobile",
    "- Better min-width at different breakpoints",
    "- Compact header/cell sizes on mobile",
    "",
    "### PAYMENTS PAGE FIXES",
    "- Full CSS rewrite to match Ledger page style",
    "- Uses same filter button style (dark inactive, orange hover/active)",
    "- Single horizontal filter row, overflow-x scroll",
    "- Ledger-style table with dark panel background",
    "- Fully responsive at 480px, 640px, 900px breakpoints",
    "",
    "### SETTINGS PAGE FIXES",
    "- workstationGrid uses auto-fit for responsiveness",
    "- dualRow stays 2-col on medium screens, goes 1-col on small",
    "- eyeBtn position uses CSS calc() with global vars",
    "",
    "### GLOBAL FIXES",
    "- HardwareSelect dropdown z-index: 9999 -- always appears above everything",
    "- HardwareSelect openWrapper has overflow: visible",
    "",
    "## FILTER BUTTON RULE (ALL PAGES)",
    "- Inactive: background rgba(26,46,48,0.75), border rgba(255,255,255,0.18), color rgba(255,255,255,0.85)",
    "- Hover: background rgba(238,140,58,0.12), color #EE8C3A, border #EE8C3A",
    "- Active: background #EE8C3A, color #1a2e30, border #EE8C3A",
    "- Font: DM Sans 900, uppercase, letter-spacing 1.5px, font-size 9-11px",
    "- Layout: single horizontal row, flex-wrap: nowrap, overflow-x: auto",
    "",
    "## SIDEBAR NON-SCROLL RULE",
    "- Sidebar MUST NOT scroll -- use compact nav item sizes to fit all 8 items",
    "- If adding more nav items, reduce padding further",
    "",
    "See original LLM_CONTEXT_GUIDE.md for full project context.",
]

guide_content = "\n".join(guide_lines)
with open("LLM_CONTEXT_GUIDE_ADDENDUM.md", "w", encoding="utf-8") as f:
    f.write(guide_content)
print("  OK: LLM_CONTEXT_GUIDE_ADDENDUM.md updated")

print("")
print("=== ALL DONE ===")
print("Run: git add -A && git commit -m 'Mobile responsiveness: sidebar no-scroll, audit filter row fix, dropdowns z-index, ledger mobile, payments ledger-style, settings responsive' && git push")