# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE
# For any AI assistant continuing work on this project
# Last updated: May 2026 -- Priority 1 uniformity fixes applied

## KEY CHANGES THIS SESSION
- All page headers now uniform: Cinzel 700, clamp(18px,2.5vw,24px), same padding/margin
- Recovery portal ACTION QUEUE/FULL SCHEDULE never cut off on mobile (nowrap scroll)
- Ledger filter buttons now match Payments style: dark inactive, orange active
- Ledger .tenureTag (MAILO etc) is now plain text only - no border or background box
- Audit page filter controls fully responsive, resetBtn matches filterBtn hover style
- Audit HardwareSelect labels use dark text (rgba(26,46,48,0.65)) on light controlHub bg
- Audit mobile: filterGrid stacks vertically, all controls full width

## STYLE STANDARDS (updated)
### Filter Button Standard (ALL pages):
- Inactive: background rgba(26,46,48,0.75), border rgba(255,255,255,0.18), color rgba(255,255,255,0.85)
- Hover: background rgba(238,140,58,0.12), color #EE8C3A, border #EE8C3A
- Active/selected: background #EE8C3A, color #1a2e30, border #EE8C3A, box-shadow orange glow

### Page Header (ALL pages):
- Title: Cinzel serif, color #1a2e30 (navy), clamp(18px,2.5vw,24px), font-weight 700
- Subtitle: DM Sans 900, color #64748b, clamp(8px,0.85vw,10px), uppercase, letter-spacing 1px

### Tenure/Type Tags in Ledger plot column:
- NO background, NO border, NO padding - plain colored text only
- .tenureTag: color rgba(255,255,255,0.45), transparent bg, no border

See original LLM_CONTEXT_GUIDE.md for full project context.