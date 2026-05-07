# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE
# For any AI assistant continuing work on this project
# Last updated: May 2026 -- Priority 1 ongoing: header+filter+subtitle uniformity

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
RULE: The LLM_CONTEXT_GUIDE.md must be updated inside fix.py on every session -- use the list-of-lines approach.
RULE: Always open files with errors='replace' when reading: open(path, 'r', encoding='utf-8', errors='replace')

### CRITICAL -- Why patches fail:
- If fix.py says 'patch target not found', the CSS already has the change OR the text doesn't match exactly.
- Always read the actual file content from the conversation context before writing str.replace patches.
- The documents shared in the conversation ARE the current file contents -- use them as source of truth.
- Copy the exact block including all whitespace, comments, and surrounding lines.
- Special characters in source files (em dashes, arrows, etc.) cause UnicodeDecodeError -- use errors='replace' when reading.

### Two files David always gets:
1. fix.py -- writes all changed source code files
2. LLM_CONTEXT_GUIDE.md -- updated guide for the next AI session (written BY fix.py)

### Fix.py efficiency rules:
- Use file.read() + str.replace() for partial changes -- keeps fix.py small
- Only use full file rewrite when many sections change or file is new
- Always use encoding='utf-8' in open() calls
- Always use errors='replace' when READING files (prevents crash on special chars)
- Always use os.makedirs(os.path.dirname(path), exist_ok=True) before writing new files
- Skip os.makedirs for root-level files (empty path causes error)
- When writing the LLM guide itself, use a list of lines joined with newlines -- never embed it in a triple-quoted string
- Print OK/MISSING for every patch so David can see what happened
- NEVER use special unicode characters in fix.py strings -- ASCII only

### How David gets the files:
- You call present_files(['/mnt/user-data/outputs/fix.py', '/mnt/user-data/outputs/LLM_CONTEXT_GUIDE.md'])
- David downloads both from the chat interface
- For fix.py: open in VS Code, Ctrl+A, Delete, paste new content, Ctrl+S, run `py fix.py`
- For LLM_CONTEXT_GUIDE.md: replace the file in the project root
- Then: git add -A && git commit -m 'message' && git push
- Watch Render Events tab for green tick (5-10 min free tier)
- Test at golden-seed.onrender.com
- If red: click 'deploy logs' -> read error -> fix -> repeat

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
  fix.py
  docker-compose.yml
  render.yaml

---

## 7. UI DESIGN STANDARDS (CRITICAL -- apply consistently)

### Page Header Style (ALL pages MUST match Dashboard)
- Use className={styles.pageHeader} for the <header> element
- Inside pageHeader: always use <div className={styles.headerLeft}> wrapping title + subtitle
- If there are action buttons/controls, put them in <div className={styles.headerRight}>
- White/cream glass panel: background: rgba(255,255,255,0.62)
- Left orange border: border-left: clamp(3px,0.4vw,5px) solid var(--orange)
- Border radius: 0 12px 12px 0 (flat left, rounded right)
- Backdrop blur: backdrop-filter: blur(15px)
- Box shadow: 0 4px 15px rgba(0,0,0,0.07)
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
- Layout: single horizontal row, flex-wrap:nowrap, overflow-x:auto, scrollbar-width:none
- NO icons inside filter buttons -- text only
- On mobile: same single row, side-scrollable (never wraps to multiple lines)

### Text on Light Background Rule
- The controlHub area (search, filters, badge legend) sits on the warm cream/beige background
- Any text in this area must use dark colors: rgba(26,46,48,0.xx) or #64748b
- Never use rgba(255,255,255,x) for text that appears outside a dark panel
- Badge legend items: color: rgba(26,46,48,0.65), font-size 9-11px
- Search hint: color: rgba(26,46,48,0.45)

### FolderPage Header
- Uses .terminalHeader -- its own design, do NOT change to pageHeader
- It has unique backlog/edit badges that need their own layout

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

### Priority 1 -- Styling & Uniformity -- IN PROGRESS
- RecoveryPortal: 2-column grid, mobile responsive -- DONE
- PaymentsPage: filter buttons unified to dark-bg inactive style -- DONE
- IntakePage: cleaned up financials -- DONE
- LedgerPage: tagBacklog + rowBacklog CSS; filter fixed; plot ID two lines -- DONE
- AuditPage: RESET FILTERS aligned; fully responsive -- DONE
- All page headers: unified glass panel using .pageHeader class -- DONE
  - Root cause found: !important block at bottom of every CSS was position:absolute-ing buttons
  - Fix: Removed all !important blocks, switched to clean .pageHeader class
  - Recovery portal header restructured: left=title+subtitle, right=stats+tabs
  - RecoveryPortal.jsx fully rewritten (clean UTF-8, no special chars) to fix encoding crash
- Filter bar unification: all pages now use identical filter button styles -- DONE
  - Single horizontal row, side-scrollable on mobile
  - No icons in filter buttons -- text only
  - Standard: dark inactive, orange hover, orange-filled active
- Subtitle positioning: all pages now use headerLeft wrapper for title+subtitle -- DONE
  - subtitle style: DM Sans 900, #64748b, uppercase, small
- LedgerPage badge legend + search hint: dark text for light background -- DONE

---

## 11. WHAT STILL NEEDS TO BE DONE (in priority order)

### Priority 1 -- Remaining uniformity checks
- Check screenshot of each page after this deploy
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

1. Create fix.py AND updated LLM_CONTEXT_GUIDE.md -> present_files both -> David downloads both
2. David replaces local fix.py -> py fix.py -> check output for OK/MISSING
3. David replaces local LLM_CONTEXT_GUIDE.md
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