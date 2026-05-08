# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# Last updated: May 2026

## KEY CHANGES THIS SESSION
- Audit page: ALL STAFF / ALL ACTIONS / RESET FILTERS now on single horizontal row
  matching Ledger filter button style (dark inactive, orange hover/active)
- Audit HardwareSelect labels hidden; selects styled like filter buttons
- Audit VISIBLE RECORDS badge: smaller, bottom-right aligned, does not block title
- GLOBAL RESPONSIVE SIZING: Added CSS variables in index.css:
    --input-height: clamp(38px, 5.5vw, 48px)
    --input-font:   clamp(12px, 1.3vw, 14px)
    --input-px:     clamp(10px, 1.4vw, 15px)
    --btn-height:   clamp(38px, 5.5vw, 48px)
    --btn-font:     clamp(10px, 1.1vw, 13px)
    --btn-px:       clamp(14px, 2vw, 32px)
    --input-radius: clamp(6px, 0.8vw, 8px)
    --label-font:   clamp(9px, 0.9vw, 11px)
- All pages (Intake, FolderPage, Settings, Login, HardwareInput, HardwareSelect,
  HardwareButton) now use these global vars for uniform size scaling
- To change app-wide input/button sizes: edit :root vars in index.css ONLY

## AUDIT FILTER LAYOUT RULE
- filterGrid is flex-direction:row, flex-wrap:nowrap, overflow-x:auto
- HardwareSelect labels are hidden via .hwSelectWrap label { display: none }
- HardwareSelect boxes styled to match filterBtn via CSS attribute override
- resetBtn same height and style as filter buttons

See original LLM_CONTEXT_GUIDE.md for full project context.