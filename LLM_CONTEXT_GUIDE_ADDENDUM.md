# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# Last updated: May 2026 - Comprehensive Mobile + Responsive Fix

## KEY CHANGES THIS SESSION

### SIDEBAR FIXES
- Sidebar is now NOT scrollable -- all nav items always visible
- Reduced NYENZ branding section (smaller font, less padding)
- Reduced nav item padding for compactness
- Collapsed width reduced from 60px to 52px

### AUDIT PAGE FIXES
- Filter row (ALL STAFF, ALL ACTIONS, RESET FILTERS) stays on ONE horizontal row on all screen sizes
- Filter row is overflow-x: auto with nowrap -- never wraps to new lines
- HardwareSelect dropdowns now appear above other content (z-index: 9999)
- VISIBLE RECORDS badge made smaller on mobile
- RESET FILTERS button same height and style as other filter buttons
- controlHub has z-index: 20 and overflow: visible

### LEDGER PAGE FIXES
- Table has -webkit-overflow-scrolling: touch for mobile
- Better min-width at different breakpoints
- Compact header/cell sizes on mobile

### PAYMENTS PAGE FIXES
- Full CSS rewrite to match Ledger page style
- Uses same filter button style (dark inactive, orange hover/active)
- Single horizontal filter row, overflow-x scroll
- Ledger-style table with dark panel background
- Fully responsive at 480px, 640px, 900px breakpoints

### SETTINGS PAGE FIXES
- workstationGrid uses auto-fit for responsiveness
- dualRow stays 2-col on medium screens, goes 1-col on small
- eyeBtn position uses CSS calc() with global vars

### GLOBAL FIXES
- HardwareSelect dropdown z-index: 9999 -- always appears above everything
- HardwareSelect openWrapper has overflow: visible

## FILTER BUTTON RULE (ALL PAGES)
- Inactive: background rgba(26,46,48,0.75), border rgba(255,255,255,0.18), color rgba(255,255,255,0.85)
- Hover: background rgba(238,140,58,0.12), color #EE8C3A, border #EE8C3A
- Active: background #EE8C3A, color #1a2e30, border #EE8C3A
- Font: DM Sans 900, uppercase, letter-spacing 1.5px, font-size 9-11px
- Layout: single horizontal row, flex-wrap: nowrap, overflow-x: auto

## SIDEBAR NON-SCROLL RULE
- Sidebar MUST NOT scroll -- use compact nav item sizes to fit all 8 items
- If adding more nav items, reduce padding further

See original LLM_CONTEXT_GUIDE.md for full project context.