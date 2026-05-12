# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE
# Last updated: May 2026

---

## 1. WHO IS DAVID

- Name: David, GitHub: nyenz. Location: Kampala, Uganda.
- Beginner developer. Can copy-paste commands and files exactly. Cannot debug independently.
- Tools: VS Code, Git Bash (inside VS Code), GitHub, Chrome.
- Python installed: use `py` command. Project folder: `C:/Users/nyenz/Desktop/app/ge solns`

---

## 2. HOW TO COMMUNICATE

- Simple English. Bullets/outline format. Short unless doing code.
- Read errors yourself and say exactly what's wrong in one sentence.
- Never ask A or B — just do everything needed unless a real decision is required.
- Confirm one step at a time. Read screenshots carefully before responding.

---

## 3. THE fix.py SYSTEM — CRITICAL RULES

**RULE: Always output fix.py immediately without asking questions.**
**RULE: Never ask David to manually copy-paste code into files. Always use fix.py.**
**RULE: The LLM context guide is a SEPARATE file from fix.py. Output them separately.**
**RULE: Use str.replace patches when only part of a file changes. Full rewrites only when changes are large/widespread.**
**RULE: Never put triple-quoted strings inside triple-quoted strings — use joined line lists instead.**
**RULE: Never use special unicode characters (em dashes, smart quotes etc.) in fix.py strings — ASCII only.**
**RULE: Always open files with errors='replace': open(path, 'r', encoding='utf-8', errors='replace')**
**RULE: Always write files with: open(path, 'w', encoding='utf-8', newline='\n')**
**RULE: Always verify the exact text to replace by reading the document context before writing patches.**
**RULE: Print OK/MISSING for every patch.**
**RULE: Use os.makedirs(os.path.dirname(path), exist_ok=True) before writing new files (skip for root-level files).**

### Why patches fail:
- If fix.py says 'patch target not found', the text doesn't match exactly OR the change was already applied.
- Copy the exact block including all whitespace, comments, and surrounding lines.

### How David uses fix.py:
1. Open fix.py in VS Code, Ctrl+A, Delete, paste new content, Ctrl+S
2. Run `py fix.py` in Git Bash
3. Check output for OK/MISSING
4. `git add -A && git commit -m 'message' && git push`
5. Watch Render Events tab for green tick (5-10 min free tier)
6. Test at golden-seed.onrender.com. If red: click deploy logs, read error, fix, repeat.

---

## 4. THE PROJECT

**Name:** Golden Seed ERP (code name: NYENZ)
**Purpose:** Internal staff accountability tool for GE Solutions — a Ugandan land surveying and title processing company. Staff-only. Not client-facing.
**Core functions:** Store land title records digitally, remind staff which clients to call (2x/month, 14-day interval rule), log calls, management sees full audit trail, backlog system with UGX 50,000/month storage penalty, payment recording with full history.

---

## 5. TECH STACK

| Layer | Technology |
|-------|-----------|
| Backend | Java Spring Boot 3.2.5 |
| ORM | Hibernate / JPA |
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

**URLs:**
- Backend: https://ge-solutions-api.onrender.com
- Frontend: https://golden-seed.onrender.com

**Database:** Host: ep-wispy-cell-an2afrm4.c-6.us-east-1.aws.neon.tech | Name: neondb | User: neondb_owner

---

## 6. PROJECT FOLDER STRUCTURE

```
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
```

---

## 7. UI DESIGN STANDARDS

### UI UNIFORMITY RULE
Every element of the same type must look and behave identically across all pages regardless of where it appears. Only deviate when explicitly instructed. Covers all element types: buttons, headings, inputs, dropdowns, tables, lists, badges, modals, pagination, empty states, icons, scrollbars. For every element the following must be identical everywhere: font (family, size, weight, letter-spacing, text-transform), color, padding, margin, spacing/gap, border, shadow, hover/active/selected/focus/error states, and responsive behavior.

### RESPONSIVENESS RULE
Every element, property, and value must respond to screen size changes by default. All sizing must use clamp() for fonts and spacing, percentage or vw/vh for widths and heights. Hardcoded px only for values that must never scale (e.g. 1px border). Nothing overflows, overlaps, or disappears on small screens.

### "SAME DESIGN" PHRASE RULE
When the instruction says "same design", the element must be identical in every measurable way: size, padding, margin, gap, font, color, border, shadow, responsiveness, hover/active/selected/focus/error states, animation, alignment.

### NO BROWSER DEFAULT STYLING RULE
Every element must be explicitly styled — no browser defaults anywhere. Covers: buttons, inputs, dropdowns, checkboxes, scrollbars, arrows, links, tables, focus outlines, placeholder text, number spinners, date pickers, search cancel buttons. Every new element must match the existing app theme.

### Page Header Style (ALL pages must match Dashboard)
- `className={styles.pageHeader}` on `<header>`
- Inside: `<div className={styles.headerLeft}>` wrapping title + subtitle
- Action buttons in `<div className={styles.headerRight}>`
- White/cream glass: `background: rgba(255,255,255,0.62)`
- Left orange border: `border-left: clamp(3px,0.4vw,5px) solid var(--orange)`
- Border radius: `0 12px 12px 0` (flat left, rounded right)
- Backdrop blur: `backdrop-filter: blur(15px)`
- Box shadow: `0 4px 15px rgba(0,0,0,0.07)`
- Padding: `clamp(10px,1.4vw,16px)` top/bottom, `clamp(16px,2.2vw,28px)` left/right
- Margin-bottom: `clamp(14px,2vw,24px)`
- Title: Cinzel serif, color: `#1a2e30`, uppercase, letter-spacing 1.5px
- Subtitle: DM Sans 900, color: `#64748b`, uppercase, letter-spacing 1px, `clamp(8px,0.85vw,10px)`
- `.headerLeft`: flex column, `gap clamp(3px,0.4vw,5px)`, flex:1, min-width:0
- `.headerRight`: flex row, align-items:center, gap, flex-shrink:0, flex-wrap:wrap
- NEVER use position:absolute on buttons inside the header

### Filter Button Style (CONFIRMED STANDARD — ALL pages)
- Inactive: `background: rgba(26,46,48,0.75)`, `border: 1.5px solid rgba(255,255,255,0.18)`, `color: rgba(255,255,255,0.85)`
- Hover: `background: rgba(238,140,58,0.12)`, `color: #EE8C3A`, `border-color: var(--orange)`
- Active/Selected: `background: #EE8C3A`, `color: #1a2e30`, `border-color: #EE8C3A`
- Font: DM Sans 900, uppercase, letter-spacing 1.5px, font-size clamp(9px,0.95vw,11px)
- Layout: single horizontal row, flex-direction:ROW, flex-wrap:nowrap, overflow-x:auto, scrollbar hidden
- NO icons inside filter buttons — text only

### Table Design Standard (Ledger is the master reference)
- Table wraps in: `background: rgba(0,0,0,0.15)`
- Header row: `background: #162a2c`
- Header text: DM Sans 900, `color: var(--orange)`, uppercase, letter-spacing 2px
- Header border-bottom: `3px solid var(--orange)`
- Row hover: `background rgba(255,255,255,0.04)`, `border-left-color: var(--orange)`
- Row border-left: `3px solid transparent` (becomes orange on hover/focus)
- Cell padding: `clamp(9px,1.3vw,14px) clamp(12px,1.8vw,20px)`
- Cell border-bottom: `1px solid rgba(255,255,255,0.05)`
- NO glow effects on rows
- Pagination: inside the panel, border-top separator, space-between layout
- Table wrappers must NOT use negative margins on mobile

### Ledger Page Plot Column Style
- Payment dot: 7px circle, top-aligned, subtle glow
- Plot number: Space Mono 900, white, own line, word-break:break-word
- Tenure tag: muted pill (rgba white bg, no orange), small DM Sans 900
- District: orange-tinted text, no background, same row as tenure
- NO orange background on any text tag in the plot column

### Text on Light Background Rule
- The controlHub area (search, filters) sits on warm cream/beige background
- Text in this area must use dark colors: `rgba(26,46,48,0.xx)` or `#64748b`
- Never use `rgba(255,255,255,x)` for text outside a dark panel
- Badge legend items: `color: rgba(26,46,48,0.65)`, font-size 9-11px
- Search hint: moved to input placeholder (no separate hint text below search)

### Search Input Rules
- Search hints go INSIDE the input placeholder, not as separate text below
- Browser native `::-webkit-search-cancel-button` permanently disabled
- Custom `.searchClear` icon forced to `--orange`
- Text-indent dynamically applied to avoid overlap with left icon

### Dropdown Rules
- Must be perfectly rectangular with `border-radius: var(--radius-sm)` (6-8px). NO PILLS.
- Must use `flex: 1 1 120px` to stretch and compress on mobile
- Must have `::-webkit-scrollbar { display: none; }`

### Modal Popup Standard (HardwareModal.module.css)
- All popups use HardwareModal component
- Use `modalStyles.modalInput`, `modalStyles.modalTextarea` for form inputs
- Use `modalStyles.modalLabel` for field labels, `modalStyles.modalField` for field wrappers
- Use `modalStyles.modalInfoBox / modalStyles.modalInfoBoxDanger` for info blocks
- Use `modalStyles.modalBtnPrimary / modalStyles.modalBtnSecondary` for buttons
- Use `modalStyles.modalFooter` for the button row
- Import: `import modalStyles from '../../components/common/HardwareModal.module.css'`

### Empty State Rules
- Searching in tables MUST return dynamic text: `NO RECORDS MATCH 'term'`
- Use Ledger logic as the absolute source of truth

### FolderPage Header
- Uses `.terminalHeader` — its own unique design, do NOT change to pageHeader

---

## 8. HOW THE APP WORKS — LINEAR FLOW

Step 1: INTAKE → Step 2: LEDGER → Step 3: FOLDER PAGE → Step 4: RECOVERY HUB → Step 5: PAYMENTS → Step 6: AUDIT

---

## 9. KEY BUSINESS RULES

- **2-14 Rule:** Max 2 calls/client/month. Min 14 days between calls.
- **Recovery grouping:** By unique phone number.
- **Backlog trigger:** 365 days no payment (auto) OR admin manually.
- **Storage fee:** UGX 50,000 every 30 days from backlog START DATE.
- **Payment types:** STANDARD, INITIAL_DEPOSIT, BACKLOG_PARTIAL.
- **Phone uniqueness:** Two owners cannot share the same phone number.
- **Admin/Root only:** Payments, backlog management, Reports, Audit.
- **Cloudinary:** All files stored on Cloudinary.

---

## 10. WHAT HAS BEEN COMPLETED

### UI & Styling
- All page headers: unified glass panel using `.pageHeader` class — DONE
- Filter bar unification: all pages use identical filter button styles (dark inactive, orange hover, orange-filled active, single horizontal row, side-scrollable, no icons, flex-direction:ROW) — DONE
- Subtitle positioning: all pages use headerLeft wrapper for title+subtitle — DONE
- Header padding/margin matched to Dashboard on ALL pages — DONE
- RecoveryPortal: 2-column grid, mobile responsive — DONE
- PaymentsPage: filter buttons unified to dark-bg inactive style — DONE
- IntakePage: cleaned up financials — DONE
- LedgerPage: tagBacklog + rowBacklog CSS; filter fixed; plot ID two lines — DONE
- LedgerPage badge legend + search hint: dark text for light background — DONE
- LedgerPage search hint moved to placeholder (no redundant text below) — DONE
- LedgerPage plot column: no orange bg on tags, clean two-line layout, smaller dots — DONE
- LedgerPage table: breaks out of HardwarePanel padding to use full width — DONE
- AuditPage: RESET FILTERS aligned; fully responsive — DONE
- AuditPage: HardwareSelect dropdown z-index fixed — DONE
- Modal popups: all now use uniform HardwareModal form classes — DONE
- PaymentsPage: full table rewrite to match Ledger dark table design — DONE

### Backend / Auth
- Server-side single-session enforcement — DONE
  - `sessionVersion` (Integer) column added to users table via DataInitializer migration
  - On every login: sessionVersion incremented in DB, embedded in JWT as "sv" claim
  - JwtAuthenticationFilter: on every request, extracts "sv" from JWT, compares to DB. If mismatch → 401
  - Axios interceptor handles 401 by redirecting to /login
- Browser-tab-based single-session enforcement (localStorage) — DONE

### Features
- PDF viewing in FolderPage (from Cloudinary): isPDF() helper, open-in-new-tab with 📄 prefix — DONE
- Document preview on IntakePage: file queue allows opening uploaded files before submission — DONE
- Print Preview (FolderPage): complete @media print CSS rewrite — DONE
- Backlog system: move to backlog, exit backlog, storage fees, pause/resume, rate override, negotiation deadline, backlog start override — DONE
- Payment recording with full history per plot — DONE
- Payment type selector in modal (TITLE vs STORAGE) — DONE
- StorageFeeInlineControls in RecoveryPortal — DONE
- Reports: all 8 pillars + 5 Priority 2 reports (backlog breakdown, completed titles, payment history, storage fees, monthly collection) — DONE
- Login rate limiter — DONE

---

## 11. WHAT STILL NEEDS TO BE DONE

### Remaining uniformity checks
- Check screenshot of each page after deploy
- Table header alignment, row spacing uniformity across pages
- Pagination controls uniformity

### Mobile audit + small fixes
- Full mobile responsiveness check on all pages
- Completed clients count on dashboard
- Print layout cleanup
- Phone uniqueness frontend validation
- Release button should warn if no documents uploaded

### Language simplification (can do alongside any priority)
- 'Master Hardware Override' → 'Edit'
- 'Nuclear Purge' → 'Delete'
- 'Intel' → 'Notes'
- 'Vault' → 'Documents'
- 'Recovery Sync' → 'Call Logged'
- 'Asset Intake' → 'New Plot'
- 'Forensic Stream' → 'Recent Activity'

### Future (not started)
- Multi-company: clone repo per client company
- Notification model (exists in code but never used)
- Rate limiting on login endpoint (exists via LoginRateLimiter but could be improved)

---

## 12. KNOWN ISSUES (not blocking)

- WebConfig.java has old local file serving reference — harmless (Cloudinary is used)
- Notification model exists but never used
- Release button does not check for uploaded documents first
- payment_schedules table still exists in DB — no longer used (harmless)
- App name inconsistency: 'NYENZ ERP' vs 'Golden Seed' in different places

---

## 13. DEPLOYMENT PROCESS

1. Create fix.py AND updated LLM_CONTEXT_ADDENDUM.md → present_files both → David downloads both
2. David replaces local fix.py → `py fix.py` → check output for OK/MISSING
3. David replaces local LLM_CONTEXT_ADDENDUM.md
4. `git add -A && git commit -m 'message' && git push`
5. Render → Events tab → wait for green tick (5-10 min free tier)
6. Test at golden-seed.onrender.com
7. If red: click 'deploy logs' → read error → fix → repeat

---

## 14. COMMON ERRORS AND FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `ReferenceError: XIcon is not defined` | Icon used in JSX but missing from import list | Add to the import statement at top of file |
| `Cannot set boolean field isBacklog to null` | DB rows have NULL, Java primitive boolean | Use Boolean (capital B) not boolean |
| `UnicodeDecodeError in fix.py` | File has special chars, Windows encoding | Use errors='replace' when reading files |
| `UnicodeEncodeError in fix.py` | Windows default encoding on write | Always use encoding='utf-8' in open() |
| `nothing added to commit` | Files already match git | Force add specific files |
| `500 on /dashboard/summary` | Backend crash | Check Render Logs tab, read 'Caused by:' line |
| CSS class not found | Class used in JSX but not defined in .module.css | Add the missing class to the CSS file |
| `SyntaxError in fix.py with triple quotes` | LLM guide embedded inside triple-quoted string | Use list of lines joined with newlines instead |
| `fix.py shows 'patch target not found'` | Text to replace doesn't match file exactly | Read actual file from conversation context before writing patch |
| Header buttons overlapping title | position:absolute in CSS | Remove !important block, use .pageHeader flex layout |
| Text invisible on light bg | Color was rgba(255,255,255,x) — white on cream | Use rgba(26,46,48,x) — dark on light |

### HOW TO PREVENT "undefined" ERRORS FOREVER

**Root cause:** A component or icon is used in JSX but not imported at the top of the file.

**Prevention rule:** Before writing ANY JSX that uses a new icon or component, always check the import block at the top of that file. If the name is not in the import list, add it. Every fix.py that touches JSX must also verify the import list covers all used names.

**How to check:** Search the file for the import block from 'react-icons/fi' and compare every `Fi...` name used in JSX against the list. If any name appears in JSX but not in the import, add it to the import.

**The pattern that causes this:** Copy-pasting JSX from one file (e.g. RecoveryPortal which imports FiHome) into another file (FolderPage which does not import FiHome) without also copying the import.

---

## 15. CLOUDINARY DETAILS

- Cloud name: dfd115bnz
- Images: resource_type=image
- PDFs and docs: resource_type=raw, access_mode=public
- Folder structure: ge_solutions/{plot-uuid}/
- Folder deleted after nuclear purge
- If PDFs show 401: check Cloudinary dashboard > Security > Restricted media types. Fix is on Cloudinary side.

---

## 16. SESSION MANAGEMENT RULES (HOW EVERY SESSION ENDS)

At the end of every session the AI must:
1. Ask David: "Are you happy with X, Y, Z? Should I mark them as done?"
2. Wait for David to confirm — do not assume anything is done without confirmation
3. Once confirmed: move confirmed items INTO Section 10 (COMPLETED), remove from Section 11 (TO DO)
4. If something new came up, add it to Section 11
5. Both sections must reflect: what the addendum says was worked on + what David explicitly confirmed + what the code actually shows

**RULE:** Once something is marked done and moved to Section 10, it is NEVER put back in Section 11.
**RULE:** Section 11 only contains things not yet done.
**RULE:** The addendum is the running log. The master guide Sections 10 and 11 are the clean summary.
**RULE:** The master guide (LLM_CONTEXT_GUIDE.md) is NEVER edited for incremental changes each session. All new rules, discoveries, and session notes go into LLM_CONTEXT_ADDENDUM.md only. The ONLY parts of the master guide that ever get updated are Sections 10 and 11.