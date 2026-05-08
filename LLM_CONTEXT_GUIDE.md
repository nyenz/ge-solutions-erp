# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE
# For any AI assistant continuing work on this project
# Last updated: May 2026 -- 4 new UI rules added to Section 7

---

## 1. WHO IS DAVID (the developer)

- Name: David, goes by nyenz on GitHub
- Location: Kampala, Uganda
- Skill level: BEGINNER. Can follow exact step-by-step instructions precisely.
- What he CAN do:
  - Copy and run terminal commands exactly as given
  - Download files and replace them in VS Code
  - Run `py fix.py` to apply file changes
  - Run `git add/commit/push` commands
  - Read screenshots and describe what he sees
  - Share screenshots to confirm progress
- What he CANNOT do:
  - Debug code independently
  - Read Java/React errors without guidance
  - Write code himself
  - Understand partial code snippets -- needs full files always
- Tools he uses: VS Code, Git Bash terminal (inside VS Code), GitHub, Chrome browser
- Python is installed: use `py` command (not `python`)
- Project folder: `C:/Users/nyenz/Desktop/app/ge solns`

---

## 2. HOW TO COMMUNICATE WITH DAVID

- Use SIMPLE English. No jargon without explanation.
- Use OUTLINE/BULLET format for explanations -- not long paragraphs.
- Keep responses SHORT unless doing code.
- When explaining a concept, use analogies or plain words.
- When errors happen, read the log yourself and tell him exactly what is wrong in one sentence.
- Never ask 'which would you prefer A or B' -- just do everything needed unless there is a real decision required.
- Confirm one step at a time. Do not skip ahead.
- When David shares a screenshot, read it carefully before responding.

---

## 3. HOW TO OUTPUT CODE CHANGES -- THE fix.py SYSTEM

RULE: Never ask David to manually copy-paste code into files. Always use fix.py.
RULE: The LLM guide (LLM_CONTEXT_GUIDE.md) is a SEPARATE file from fix.py. Always output them separately.
RULE: Use str.replace (patch) in fix.py when only a section of a file changes. Only rewrite full files when changes are large or spread throughout.
RULE: Never put triple-quoted strings inside triple-quoted strings in fix.py -- use a list of lines joined with newlines instead (this avoids SyntaxError).
RULE: Never use special unicode characters (em dashes, smart quotes, etc.) in fix.py strings -- use plain ASCII only (-- instead of --, - instead of em dash). This prevents UnicodeDecodeError when reading files that Windows saved with a different encoding.
RULE: Before writing a patch, always verify the exact text to replace by reading the document context. Do not guess.
RULE: Always open files with errors='replace' when reading: open(path, 'r', encoding='utf-8', errors='replace')

### CRITICAL -- Why patches fail:
- If fix.py says 'patch target not found', the CSS already has the change OR the text doesn't match exactly.
- Always read the actual file content from the conversation context before writing str.replace patches.
- The documents shared in the conversation ARE the current file contents -- use them as source of truth.
- Copy the exact block including all whitespace, comments, and surrounding lines.
- Special characters in source files (em dashes, arrows, etc.) cause UnicodeDecodeError -- use errors='replace' when reading.

### Two files David always gets:
1. fix.py -- writes all changed source code files
2. LLM_CONTEXT_ADDENDUM.md -- updated addendum for incremental changes (NOT the master guide)

### Fix.py efficiency rules:
- Use file.read() + str.replace() for partial changes -- keeps fix.py small
- Only use full file rewrite when many sections change or file is new
- Always use encoding='utf-8' in open() calls
- Always use errors='replace' when READING files (prevents crash on special chars)
- Always use os.makedirs(os.path.dirname(path), exist_ok=True) before writing new files
- Skip os.makedirs for root-level files (empty path causes error)
- Print OK/MISSING for every patch so David can see what happened
- NEVER use special unicode characters in fix.py strings -- ASCII only

### How David gets the files:
- You call present_files() with the output files
- David downloads both from the chat interface
- For fix.py: open in VS Code, Ctrl+A, Delete, paste new content, Ctrl+S, run `py fix.py`
- For .md files: replace the file in the project root directly
- Then: git add -A && git commit -m 'message' && git push
- Watch Render Events tab for green tick (5-10 min free tier)
- Test at golden-seed.onrender.com
- If red: click 'deploy logs' -> read error -> fix -> repeat

### ADDENDUM RULE (CRITICAL):
- The master guide (LLM_CONTEXT_GUIDE.md) is NEVER edited for incremental changes each session.
- All new rules, discoveries, and session notes go into LLM_CONTEXT_ADDENDUM.md only.
- The ONLY parts of the master guide that ever get updated are Section 10 and Section 11.
- Section 10 and 11 are only updated after explicit David approval at end of session.

---

## 4. THE PROJECT -- WHAT IT IS

### Name
Golden Seed ERP (code name: NYENZ)

### Purpose
Internal staff accountability tool for GE Solutions -- a Ugandan land surveying and title processing company. Staff-only. Not client-facing.

### Core functions
- Store land title records digitally with scanned documents
- Remind staff which clients to call (2x per month, 14-day interval rule)
- Staff log what happened on each call
- Management sees full audit trail of all actions
- Backlog system: clients who stop paying get UGX 50,000/month storage penalty
- Payment recording with full history per plot

---

## 5. TECH STACK

| Layer | Technology |
|-------|-----------|
| Backend | Java Spring Boot 3.2.5 |
| Database ORM | Hibernate / JPA |
| Database | PostgreSQL (Neon cloud, free tier) |
| Auth | JWT tokens |
| Build | Maven |
| Utilities | Lombok, Spring Security |
| Frontend | React 19, Vite |
| Styling | CSS Modules |
| Routing | React Router |
| HTTP | Axios |
| File Storage | Cloudinary (cloud name: dfd115bnz) |
| Deployment | Render free tier |
| Repo | GitHub (PRIVATE): github.com/nyenz/ge-solutions-erp |

### URLs
- Backend: https://ge-solutions-api.onrender.com
- Frontend: https://golden-seed.onrender.com

### Database
- Host: ep-wispy-cell-an2afrm4.c-6.us-east-1.aws.neon.tech
- Name: neondb
- User: neondb_owner

---

## 6. PROJECT FOLDER STRUCTURE

ge solns/
  erp-backend/
    src/main/java/com/gesolutions/erp/
  erp-frontend/
    src/
      api/axios.js
      context/AuthProvider.jsx
      hooks/useAuth.js
      components/
      pages/
        Audit/AuditPage.jsx + AuditPage.module.css
        Dashboard/
        DigitalFolder/FolderPage.jsx
        Intake/IntakePage.jsx + IntakePage.module.css
        Ledger/LedgerPage.jsx + LedgerPage.module.css
        Payments/PaymentsPage.jsx + PaymentsPage.module.css
        Recovery/RecoveryPortal.jsx + RecoveryPortal.module.css
        Reports/ReportHub.jsx
        login/LoginPage.jsx
        settings/SettingsPage.jsx
      services/
  LLM_CONTEXT_GUIDE.md
  LLM_CONTEXT_ADDENDUM.md
  fix.py
  docker-compose.yml
  render.yaml

---

## 7. UI DESIGN STANDARDS (CRITICAL -- apply consistently)

### UI UNIFORMITY RULE (DEFAULT DESIGN APPROACH)
Every element of the same type must look and behave identically across all pages and sections regardless of where it appears. Only deviate when explicitly instructed. This covers all element types including: buttons (primary, secondary, filter, action), headings (page titles, section titles, table headers), inputs (text fields, search boxes, number inputs), dropdowns/selects, tables (headers, rows, cells), lists, badges/tags/pills, modals/popups, pagination controls, empty states, icons, tooltips/hints, error messages, success/warning/info messages, loading states/spinners, corner decorations, dividers/separators, scrollbars, and any decorative or structural UI element. For every element the following must be identical everywhere: font (family, size, weight, letter-spacing, text-transform), color (text, background, border), padding, margin, spacing/gap, border (width, style, color, radius), shadow, hover/active/selected/focus/error states, and responsive behavior. When a new element is introduced its style must be derived from the closest existing matching element -- never invent a new style when one already exists.

### RESPONSIVENESS RULE (DEFAULT DESIGN APPROACH)
Every element, property, and value must respond to screen size changes by default. This applies to everything without exception: buttons, headings, text, inputs, dropdowns, tables, lists, badges/tags/pills, modals, icons, images, pagination, empty states, decorative elements, corner decorations, dividers, scrollbars, and all sizing properties (margin, padding, gap, border-width, border-radius, shadow size, font-size, letter-spacing, line-height, container widths, panel heights). All sizing must use clamp() for fonts and spacing, percentage or vw/vh for widths and heights. Hardcoded px is only acceptable for values that must never scale (e.g. a 1px border line). On small screens everything compresses but remains fully readable and usable -- nothing overflows, overlaps, or disappears. On normal/large screens everything returns to its designed size.

### "SAME DESIGN" PHRASE RULE
When the instruction says "same design", the element must be identical in every measurable way: size, padding, margin, spacing/gap, font (family, size, weight, letter-spacing, text-transform), color (text, background, border), border (width, style, color, radius), shadow, responsiveness, hover/active/selected/focus/error states, animation/transition, and alignment/positioning behavior.

### NO BROWSER DEFAULT STYLING RULE (DEFAULT DESIGN APPROACH)
Every element must be explicitly styled -- no browser defaults are ever acceptable anywhere in the app. This includes without exception: buttons, inputs, dropdowns/selects, checkboxes, radio buttons, file inputs, range sliders, scrollbars, arrows (dropdown, scroll, navigation), dots (pagination, bullets, list markers), links, tables, focus outlines, placeholder text, selection highlight, fieldsets/legends, number input spinners, date/time pickers, search cancel buttons, tooltips, and any other element the browser would otherwise style on its own. Every new element introduced must conform to the existing app theme -- matching established colors, fonts, spacing, borders, and interaction states. A new element must never look foreign next to existing ones. When in doubt derive the style from the closest matching existing element in the app.

### Page Header Style (ALL pages MUST match Dashboard)
- Use className={styles.pageHeader} for the <header> element
- Inside pageHeader: always use <div className={styles.headerLeft}> wrapping title + subtitle
- If there are action buttons/controls, put them in <div className={styles.headerRight}>
- White/cream glass panel: background: rgba(255,255,255,0.62)
- Left orange border: border-left: clamp(3px,0.4vw,5px) solid var(--orange)
- Border radius: 0 12px 12px 0 (flat left, rounded right)
- Backdrop blur: backdrop-filter: blur(15px)
- Box shadow: 0 4px 15px rgba(0,0,0,0.07)
- PADDING (must match Dashboard): clamp(10px,1.4vw,16px) top/bottom, clamp(16px,2.2vw,28px) left/right
- MARGIN-BOTTOM (must match Dashboard): clamp(14px,2vw,24px)
- Title (.title): Cinzel serif, color: #1a2e30 (hardcoded navy, NOT var(--navy) which is white on dark panels), uppercase, letter-spacing 1.5px
- Subtitle (.subtitle): DM Sans 900, color: #64748b, uppercase, letter-spacing 1px, font-size clamp(8px,0.85vw,10px)
- .headerLeft: flex column, gap clamp(3px,0.4vw,5px), flex:1, min-width:0
- .headerRight: flex row, align-items:center, gap, flex-shrink:0, flex-wrap:wrap
- NEVER use position:absolute on buttons inside the header -- use flex gap

### Filter Button Style (CONFIRMED STANDARD -- ALL pages must match)
- Inactive: background: rgba(26,46,48,0.75), border: 1.5px solid rgba(255,255,255,0.18), color: rgba(255,255,255,0.85)
- Hover: background: rgba(238,140,58,0.12), color: #EE8C3A, border-color: var(--orange)
- Active/Selected: background: #EE8C3A, color: #1a2e30, border-color: #EE8C3A
- Font: DM Sans 900, uppercase, letter-spacing 1.5px, font-size 11px
- Layout: single horizontal row, flex-direction:ROW, align-items:center, flex-wrap:nowrap, overflow-x:auto
- NO icons inside filter buttons -- text only
- On mobile: same single row, side-scrollable (never wraps to multiple lines)

### Ledger Page Plot Column Style (CONFIRMED)
- Payment dot: 7px circle, top-aligned, subtle glow
- Plot number: Space Mono 900, white, own line, word-break:break-word
- Tenure tag: muted pill (rgba white bg, no orange), small DM Sans 900
- District: orange-tinted text, no background, same row as tenure
- NO orange background on any text tag in the plot column

### Text on Light Background Rule
- The controlHub area (search, filters, badge legend) sits on the warm cream/beige background
- Any text in this area must use dark colors: rgba(26,46,48,0.xx) or #64748b
- Never use rgba(255,255,255,x) for text that appears outside a dark panel
- Badge legend items: color: rgba(26,46,48,0.65), font-size 9-11px
- Search hint: moved to input placeholder (no separate hint text below search)

### Search Input Rules
- Search hints go INSIDE the input placeholder, not as separate text below
- Browser native ::-webkit-search-cancel-button is permanently disabled
- The custom .searchClear icon is forced to --orange
- Text-indent is dynamically applied to avoid search text overlapping the left icon

### Dropdown Rules
- Must be perfectly rectangular with border-radius: var(--radius-sm) (6px-8px). NO PILLS.
- Must use flex: 1 1 120px to stretch and compress seamlessly on mobile
- Must have ::-webkit-scrollbar { display: none; }

### Table Design Standard (CONFIRMED -- Ledger is the master reference)
- Table wraps in a dark background container: background: rgba(0,0,0,0.15)
- Header row background: #162a2c (very dark teal)
- Header text: DM Sans 900, color: var(--orange), uppercase, letter-spacing 2px
- Header border-bottom: 3px solid var(--orange)
- Row hover: background rgba(255,255,255,0.04), border-left-color: var(--orange)
- Row border-left: 3px solid transparent (becomes orange on hover/focus)
- Cell padding: clamp(9px,1.3vw,14px) clamp(12px,1.8vw,20px)
- Cell border-bottom: 1px solid rgba(255,255,255,0.05)
- NO glow effects on rows -- clean flat design only
- Pagination: sits inside the panel, border-top separator, space-between layout
- Table wrappers (.tableScroll) must NOT use negative margins on mobile
- They must respect the standard border-radius to prevent bleeding off screen edges

### Empty State Rules
- Searching in tables MUST return dynamic text: NO RECORDS MATCH 'term'
- Use Ledger logic as the absolute source of truth

### FolderPage Header
- Uses .terminalHeader -- its own design, do NOT change to pageHeader
- It has unique backlog/edit badges that need their own layout

### Modal Popup Standard (CONFIRMED -- HardwareModal.module.css)
- All popups use HardwareModal component
- Use modalStyles.modalInput, modalStyles.modalTextarea for form inputs
- Use modalStyles.modalLabel for field labels
- Use modalStyles.modalField for field wrappers
- Use modalStyles.modalInfoBox / modalStyles.modalInfoBoxDanger for info blocks
- Use modalStyles.modalBtnPrimary / modalStyles.modalBtnSecondary for buttons
- Use modalStyles.modalFooter for the button row
- Import: import modalStyles from '../../components/common/HardwareModal.module.css'

---

## 8. HOW THE APP WORKS -- LINEAR FLOW

Step 1: INTAKE -> Step 2: LEDGER -> Step 3: FOLDER PAGE
Step 4: RECOVERY HUB -> Step 5: PAYMENTS -> Step 6: AUDIT

---

## 9. KEY BUSINESS RULES

- 2-14 Rule: Max 2 calls/client/month. Min 14 days between calls.
- Recovery grouping: By unique phone number.
- Backlog trigger: 365 days no payment (auto) OR admin manually.
- Storage fee: UGX 50,000 every 30 days from backlog START DATE.
- Payment types: STANDARD, INITIAL_DEPOSIT, BACKLOG_PARTIAL.
- Phone uniqueness: Two owners cannot share the same phone number.
- Admin/Root only: Payments, backlog management, Reports, Audit.
- Cloudinary: All files stored on Cloudinary.

---

## 10. WHAT HAS BEEN COMPLETED (chronological)
# AI RULE: At end of session -- ask David which items he is happy with before
# adding anything here. Base updates on: addendum log + David approval + code.
# Once an item is here it is NEVER moved back to Section 11.

### Priority 1 -- Styling & Uniformity -- LARGELY COMPLETE
- RecoveryPortal: 2-column grid, mobile responsive -- DONE
- PaymentsPage: filter buttons unified to dark-bg inactive style -- DONE
- IntakePage: cleaned up financials -- DONE
- LedgerPage: tagBacklog + rowBacklog CSS; filter fixed; plot ID two lines -- DONE
- AuditPage: RESET FILTERS aligned; fully responsive -- DONE
- All page headers: unified glass panel using .pageHeader class -- DONE
- Filter bar unification: all pages now use identical filter button styles -- DONE
  - Single horizontal row, side-scrollable on mobile
  - No icons in filter buttons -- text only
  - flex-direction: ROW with align-items:center
  - Standard: dark inactive, orange hover, orange-filled active
- Subtitle positioning: all pages now use headerLeft wrapper for title+subtitle -- DONE
- Header padding/margin matched to Dashboard on ALL pages -- DONE
- LedgerPage badge legend + search hint: dark text for light background -- DONE
- LedgerPage search hint moved to placeholder (no redundant text below) -- DONE
- LedgerPage plot column: no orange bg on tags, clean two-line layout, smaller dots -- DONE
- LedgerPage table: breaks out of HardwarePanel padding to use full width -- DONE
- Modal popups: all now use uniform HardwareModal form classes -- DONE
- PaymentsPage: full table rewrite to match Ledger dark table design -- DONE
- AuditPage: HardwareSelect dropdown z-index fixed -- DONE

---

## 11. WHAT STILL NEEDS TO BE DONE (in priority order)
# AI RULE: At end of session -- remove anything David confirmed is done.
# Add anything new that came up. Only unfinished work lives here.
# Base updates on: addendum log + David approval + code.

### Priority 1 -- Remaining uniformity checks
- Check screenshot of each page after deploy
- Table header alignment, row spacing uniformity across pages
- Pagination controls uniformity

### Priority 2 -- Reports overhaul
1. Add backlog report (all backlog plots with storage fees breakdown)
2. Add completed titles report (released plots)
3. Add payment history report (all payments, date range filter)
4. Add storage fees report (total fees per plot)
5. Add monthly collection report (how much collected each month)

### Priority 3 -- Mobile audit + small fixes
1. Full mobile responsiveness check on all pages
2. Completed clients count on dashboard
3. Print layout cleanup
4. Phone uniqueness frontend validation
5. Release button should warn if no documents uploaded

### Language simplification (can do alongside any priority)
- 'Master Hardware Override' -> 'Edit'
- 'Nuclear Purge' -> 'Delete'
- 'Intel' -> 'Notes'
- 'Vault' -> 'Documents'
- 'Recovery Sync' -> 'Call Logged'
- 'Asset Intake' -> 'New Plot'
- 'Forensic Stream' -> 'Recent Activity'

### Future (not started)
- Multi-company: clone repo per client company
- Notification model (exists in code but never used)
- Rate limiting on login endpoint

---

## 12. KNOWN ISSUES (not blocking)

- WebConfig.java has old local file serving reference -- harmless (Cloudinary is used)
- Notification model exists but never used
- No rate limiting on login
- Release button does not check for uploaded documents first
- payment_schedules table still exists in DB -- no longer used (harmless)
- App name inconsistency: 'NYENZ ERP' vs 'Golden Seed' in different places

---

## 13. DEPLOYMENT PROCESS

1. Create fix.py AND updated LLM_CONTEXT_ADDENDUM.md -> present_files both -> David downloads both
2. David replaces local fix.py -> py fix.py -> check output for OK/MISSING
3. David replaces local LLM_CONTEXT_ADDENDUM.md
4. git add -A && git commit -m 'message' && git push
5. Render -> Events tab -> wait for green tick (5-10 min free tier)
6. Test at golden-seed.onrender.com
7. If red: click 'deploy logs' -> read error -> fix -> repeat

---

## 14. COMMON ERRORS AND FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| Can not set boolean field isBacklog to null | DB rows have NULL, Java primitive boolean | Use Boolean (capital B) not boolean |
| UnicodeDecodeError in fix.py | File has special chars (em dashes etc), Windows encoding | Use errors='replace' when reading files |
| UnicodeEncodeError in fix.py | Windows default encoding on write | Always use encoding='utf-8' in open() |
| nothing added to commit | Files already match what's in git | Force add specific files |
| 500 on /dashboard/summary | Backend crash -- check Render Logs tab | Read Caused by: line at bottom of log |
| CSS class not found | Class used in JSX but not defined in .module.css | Add the missing class to the CSS file |
| SyntaxError in fix.py with triple quotes | LLM guide embedded inside triple-quoted string | Use list of lines joined with newlines instead |
| fix.py shows 'patch target not found' | Text to replace doesn't match file exactly | Read actual file from conversation context before writing patch |
| Header buttons overlapping title | !important position:absolute in CSS override block | Remove !important block, use .pageHeader flex layout |
| Text invisible on light bg | Color was rgba(255,255,255,x) -- white on cream | Use rgba(26,46,48,x) -- dark on light |

---

## 15. CLOUDINARY DETAILS

- Cloud name: dfd115bnz
- Images: resource_type=image
- PDFs and docs: resource_type=raw, access_mode=public
- Folder structure: ge_solutions/{plot-uuid}/
- Folder deleted after nuclear purge