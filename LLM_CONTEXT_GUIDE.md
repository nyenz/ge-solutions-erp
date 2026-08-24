# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE
# Last updated: August 2026 (Cleanup pass: Section 7 now leads with "Ledger is the reference
# design" as a checkable law, duplicate wording removed; fix.py now commits/pushes itself
# automatically, Section 3/13 deploy steps de-duplicated; Section 16 gained a no-duplication
# rule, a supersession-not-deletion rule, and its missing Section 18 exception. Section 18
# added: Folder-to-Title redesign, with 17.4/17.6 marked superseded. Section 10 bug-fix
# roadmap added, Sections 11/12/16 cleaned up.)

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
- Never ask A or B -- just do everything needed unless a real decision is required.
- Confirm one step at a time. Read screenshots carefully before responding.

---

## 3. THE fix.py SYSTEM -- CRITICAL RULES

**RULE: Always output fix.py immediately without asking questions.**
**RULE: Never ask David to manually copy-paste code into files. Always use fix.py.**
**RULE: The LLM context guide is a SEPARATE file from fix.py. Output them separately.**
**RULE: Use str.replace patches when only part of a file changes. Full rewrites only when changes are large/widespread.**
**RULE: Never put triple-quoted strings inside triple-quoted strings -- use joined line lists instead.**
**RULE: Never use special unicode characters (em dashes, smart quotes etc.) in fix.py strings -- ASCII only.**
**RULE: Always open files with errors='replace': open(path, 'r', encoding='utf-8', errors='replace')**
**RULE: Always write files with: open(path, 'w', encoding='utf-8', newline='\n')**
**RULE: Always verify the exact text to replace by reading the document context before writing patches.**
**RULE: Print OK/MISSING for every patch.**
**RULE: Use os.makedirs(os.path.dirname(path), exist_ok=True) before writing new files (skip for root-level files).**
**RULE (August 2026, PERMANENT -- supersedes the earlier "one phase per fix.py, split into small parts" rule): Each phase of a large multi-phase rebuild (like the ERP Revamp in Section 17) ships as ONE complete fix.py covering that entire phase from start to finish. Never split a single phase into sub-parts (no more 4A/4B/4C-style patches). If a phase touches many files, that is fine -- it still goes in one fix.py. Only split across multiple fix.py files if David explicitly asks for it for a specific reason.**
**RULE (August 2026, PERMANENT): Testing happens ONLY after ALL planned phases in the current rebuild are code-complete and deployed -- never after each individual phase in isolation. Do not propose or ask David to test a single phase on its own; keep shipping phases back-to-back until the full plan is code-complete, then run one comprehensive end-to-end test pass covering everything at once. This makes permanent the deferred-testing approach David adopted during the ERP Revamp.**
**RULE (August 2026, PERMANENT): Going forward, BUG FIXES (as opposed to new revamp phases) are tested immediately after each stage, not deferred to the end. Only the ERP REVAMP phases (Section 17) follow the deferred, test-everything-at-the-end rule. Bug-fix stages in the roadmap follow normal one-stage-then-test discipline.**
**RULE (August 2026, PERMANENT): Every fix.py must commit and push itself as its final step -- call `subprocess.run(['git','add','-A'])`, then `subprocess.run(['git','commit','-m','<descriptive message>'])`, then `subprocess.run(['git','push'])`, using a commit message specific to that fix. David should never need to type a git command by hand.**

### Why patches fail:
- If fix.py says 'patch target not found', the text doesn't match exactly OR the change was already applied.
- Copy the exact block including all whitespace, comments, and surrounding lines.

### How David uses fix.py:
1. Open fix.py in VS Code, Ctrl+A, Delete, paste new content, Ctrl+S
2. Run `py fix.py` in Git Bash
3. Check output for OK/MISSING -- the script commits and pushes automatically as its last step
   (see the PERMANENT rule above), so there is no git command to type by hand
4. See Section 13 for the full deploy-and-test flow, including replacing the addendum file first

---

## 4. THE PROJECT

**Name:** Golden Seed ERP (code name: NYENZ)
**Purpose (ORIGINAL, pre-revamp):** Internal staff accountability tool for GE Solutions -- a Ugandan land surveying and title processing company. Staff-only. Not client-facing.
**Purpose (REVAMPED -- see Section 17 for full detail):** A full project-based company ERP. Land titles remain the only project type for now, but the system now tracks detailed per-stage project costs, a real processing pipeline, company-wide expenses separate from project costs, NIN-based identity, and a 4-tier role hierarchy so the Director has full company visibility while lower roles see only what they need.
**Core functions (original, still true):** Store land title records digitally, remind staff which clients to call (2x/month, 14-day interval rule), log calls, management sees full audit trail, receivable system with UGX 50,000/month storage penalty, payment recording with full history.
**IMPORTANT:** The revamp in Section 17 is being built in phases. Until each phase ships, the ORIGINAL business rules in Section 9 remain in effect for that part of the system. Do not assume revamp rules apply to code that hasn't been touched yet -- check the Phase Tracker in Section 17 for what's actually live.

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
  ERP_REVAMP_PLAN.md   <-- NEW: plain-English revamp plan for showing the employer
  fix.py
```

---

## 7. UI DESIGN STANDARDS

### LAW: LEDGER PAGE IS THE REFERENCE DESIGN
Ledger is the closest existing page to the target design language for the whole app. Every
other list, table, filter bar, search box, dropdown, or empty state should default to Ledger's
existing pattern unless a subsection below says otherwise for that specific element. The
subsections below ARE that breakdown -- each names the exact spacing, color, font, and behavior
Ledger already uses, so "match Ledger" is a checkable rule, not something to eyeball.

### UI UNIFORMITY RULE
Every element of the same type must look and behave identically across all pages regardless of where it appears. Only deviate when explicitly instructed. Covers all element types: buttons, headings, inputs, dropdowns, tables, lists, badges, modals, pagination, empty states, icons, scrollbars. For every element the following must be identical everywhere: font (family, size, weight, letter-spacing, text-transform), color, padding, margin, spacing/gap, border, shadow, hover/active/selected/focus/error states, and responsive behavior.

### RESPONSIVENESS RULE
Every element, property, and value must respond to screen size changes by default. All sizing must use clamp() for fonts and spacing, percentage or vw/vh for widths and heights. Hardcoded px only for values that must never scale (e.g. 1px border). Nothing overflows, overlaps, or disappears on small screens.

### "SAME DESIGN" PHRASE RULE
When the instruction says "same design", the element must be identical in every measurable way: size, padding, margin, gap, font, color, border, shadow, responsiveness, hover/active/selected/focus/error states, animation, alignment.

### NO BROWSER DEFAULT STYLING RULE
Every element must be explicitly styled -- no browser defaults anywhere. Covers: buttons, inputs, dropdowns, checkboxes, scrollbars, arrows, links, tables, focus outlines, placeholder text, number spinners, date pickers, search cancel buttons. Every new element must match the existing app theme.

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

### Filter Button Style (CONFIRMED STANDARD -- ALL pages)
- Inactive: `background: rgba(26,46,48,0.75)`, `border: 1.5px solid rgba(255,255,255,0.18)`, `color: rgba(255,255,255,0.85)`
- Hover: `background: rgba(238,140,58,0.12)`, `color: #EE8C3A`, `border-color: var(--orange)`
- Active/Selected: `background: #EE8C3A`, `color: #1a2e30`, `border-color: #EE8C3A`
- Font: DM Sans 900, uppercase, letter-spacing 1.5px, font-size clamp(9px,0.95vw,11px)
- Layout: single horizontal row, flex-direction:ROW, flex-wrap:nowrap, overflow-x:auto, scrollbar hidden
- NO icons inside filter buttons -- text only

### Table Design Standard
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
- NEW (Phase 1 revamp): Project Index (e.g. "#001A") shown next to plot number, reuses districtTag styling

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

### FolderPage Header
- Uses `.terminalHeader` -- its own unique design, do NOT change to pageHeader

---

## 8. HOW THE APP WORKS -- LINEAR FLOW

**Original flow (pre-revamp, still the live behavior until Phase 4 ships):**
Step 1: INTAKE -> Step 2: LEDGER -> Step 3: FOLDER PAGE -> Step 4: RECOVERY HUB -> Step 5: PAYMENTS -> Step 6: AUDIT

**Target flow (post-revamp, see Section 17):**
Step 1: INTAKE (with NIN check + project index auto-assigned) -> Step 2: STAGE SELECTION (checkbox template, per-stage cost) -> Step 3: LEDGER (searchable by index, name, NIN) -> Step 4: FOLDER PAGE (per-stage cost/notes, processing pipeline) -> Step 5: RECOVERY HUB (RECEIVABLE = work not done; RECEIVABLES = done but unpaid) -> Step 6: PAYMENTS -> Step 7: DIRECTOR DASHBOARD (company-wide view) -> Step 8: AUDIT

---

## 9. KEY BUSINESS RULES

**NOTE: These are the ORIGINAL rules. Several are being redefined by the revamp (Section 17).
Check the Phase Tracker before assuming a rule below still applies as-is.**

- **2-14 Rule:** Max 2 calls/client/month. Min 14 days between calls. (unchanged by revamp)
- **Recovery grouping:** By unique phone number. (REVAMP: will change to NIN-based once Phase 2 ships)
- **Receivable trigger:** 365 days no payment (auto) OR admin manually. (REVAMP: "Receivable" is being redefined -- see Section 17. This old trigger describes what will become "Receivables" logic once Phase 6 ships)
- **Storage fee:** UGX 50,000 every 30 days from receivable START DATE. (applies to the old receivable/new Receivables concept, unchanged mechanically)
- **Payment types:** STANDARD, INITIAL_DEPOSIT, RECEIVABLE_PARTIAL. (naming may need to shift to RECEIVABLE_PARTIAL once Phase 6 ships -- flag this for a future session)
- **Phone uniqueness:** Two owners cannot share the same phone number. (REVAMP: NIN becomes the real uniqueness check once Phase 2 ships. Phone uniqueness will likely be dropped or downgraded to a soft warning.)
- **Admin/Root only:** Payments, receivable management, Reports, Audit. (REVAMP: this simple 2-tier check is being replaced by the 4-tier role table in Section 17 once Phase 3 ships)
- **Cloudinary:** All files stored on Cloudinary. (unchanged)
- **Project deletion:** soft-delete only (Stage 3 of the bug-fix roadmap) -- deleting a plot
  hides it from the Ledger/Recovery/Dashboard/Reports but keeps the row, payments, notes, and
  Cloudinary files intact. Root can restore it from Settings > Recently Deleted Plots.

---

## 10. WHAT HAS BEEN COMPLETED

### UI & Styling
- All page headers: unified glass panel using `.pageHeader` class -- DONE
- Filter bar unification: all pages use identical filter button styles (dark inactive, orange hover, orange-filled active, single horizontal row, side-scrollable, no icons, flex-direction:ROW) -- DONE
- Subtitle positioning: all pages use headerLeft wrapper for title+subtitle -- DONE
- Header padding/margin matched to Dashboard on ALL pages -- DONE
- RecoveryPortal: 2-column grid, mobile responsive -- DONE
- PaymentsPage: filter buttons unified to dark-bg inactive style -- DONE
- IntakePage: cleaned up financials -- DONE
- LedgerPage: tagReceivable + rowReceivable CSS; filter fixed; plot ID two lines -- DONE
- LedgerPage badge legend + search hint: dark text for light background -- DONE
- LedgerPage search hint moved to placeholder (no redundant text below) -- DONE
- LedgerPage plot column: no orange bg on tags, clean two-line layout, smaller dots -- DONE
- LedgerPage table: breaks out of HardwarePanel padding to use full width -- DONE
- AuditPage: RESET FILTERS aligned; fully responsive -- DONE
- AuditPage: HardwareSelect dropdown z-index fixed -- DONE
- Modal popups: all now use uniform HardwareModal form classes -- DONE
- PaymentsPage: full table rewrite to match Ledger dark table design -- DONE

### Backend / Auth
- Server-side single-session enforcement -- DONE
  - `sessionVersion` (Integer) column added to users table via DataInitializer migration
  - On every login: sessionVersion incremented in DB, embedded in JWT as "sv" claim
  - JwtAuthenticationFilter: on every request, extracts "sv" from JWT, compares to DB. If mismatch -> 401
  - Axios interceptor handles 401 by redirecting to /login
- Browser-tab-based single-session enforcement (localStorage) -- DONE

### Features
- PDF viewing in FolderPage (from Cloudinary): isPDF() helper, open-in-new-tab with (icon) prefix -- DONE
- Document preview on IntakePage: file queue allows opening uploaded files before submission -- DONE
- Print Preview (FolderPage): complete @media print CSS rewrite -- DONE
- Receivable system: move to receivable, exit receivable, storage fees, pause/resume, rate override, negotiation deadline, receivable start override -- DONE (note: this is the OLD receivable meaning -- payment overdue. Will be renamed/absorbed into Receivables under the revamp)
- Payment recording with full history per plot -- DONE
- Payment type selector in modal (TITLE vs STORAGE) -- DONE
- StorageFeeInlineControls in RecoveryPortal -- DONE
- Reports: all 8 pillars + 5 Priority 2 reports (receivable breakdown, completed titles, payment history, storage fees, monthly collection) -- DONE
- Login rate limiter -- DONE

### Automated Testing Infrastructure (June 2026)
- Zero-Dependency H2 Local Test Suite: full Spring context boots offline in-memory with mocked env vars -- DONE
- LoginRateLimiterTest: verifies IP blocked after 10 failed login attempts -- DONE
- SingleSessionEnforcementTest: verifies older JWT rejected with 403 after sessionVersion increments -- DONE
- StaffGovernanceTest: verifies ROLE_MANAGER blocked (403) from admin endpoints, ROLE_ADMIN allowed -- DONE (note: this test will need updating once the 4-tier role system in Phase 3 ships)
- ReceivableSchedulerTest: verifies monthly storage fee scheduler (default rate, custom rate override, negotiation deadline pause) -- DONE
- LandServiceTest: verifies atomicIntake workflow saves project, title, proprietor, and initial payment -- DONE
- LandCascadeDeleteTest + LandService.nuclearDelete() fix: verifies deleting a plot cascades to payments and notes (silent data leak patched) -- DONE
- Playwright login.spec.js: verifies successful login and redirect to /dashboard or /settings -- DONE

### Bug-Fix Roadmap (Stages 1-11) -- all applied, committed, and pushed
- Stage 1: payment endpoint fix, password reset, promote/demote, overpayment handling -- DONE
- Stage 2: Secretary role wiring, Director payment access -- DONE
- Stage 3: NIN name-mismatch guard on Intake (blocking confirm dialog, not a dismissible warning), soft-delete/restore for projects (Root can restore from Settings > Recently Deleted Plots) -- DONE
- Stage 4: label cleanup, doc/process notes -- DONE
- Stage 5: app-name branding cleanup -- Sidebar footer + every downloaded report CSV filename said "NYENZ", rest of the app said "Golden Seed"; normalized ~17 internal code comments and 2 boot-log lines too; the 4 `backlog_*` DB columns were deliberately left unrenamed (flagged as an unsafe DB rename, same call made again and declined in Stage 6) -- DONE
- Stage 6: RECEIVABLE -> RECEIVABLES wording sweep (34 patches across RecoveryPortal, LedgerPage, IntakePage, FolderPage, PaymentsPage, ReportHub, ManagerTerminal -- every on-screen "RECEIVABLE" was the old backlog concept per 17.2 and needed to read RECEIVABLES since the new singular status isn't built anywhere yet) -- DONE
- Stage 7: three previously-"open" items actually resolved instead of left as decisions -- ExpensesPage's one raw `<select>` got a scoped CSS-only patch (not swapped to HardwareSelect, which would visually clash); the unused Notification model (model/repository/service, zero references anywhere in the backend) was deleted; confirmed IntakePage's isLegacyMode toggle already IS the Legacy Receivables intake flow from 17.6, so nothing needed building there -- DONE
- Stage 8: NIN name-mismatch guard extended to the Edit screen (FolderPage) -- previously only ran on Intake, so reusing an existing NIN with a different typed name on Edit silently renamed that person's identity record everywhere they appear -- DONE
- Stage 9: Recovery joint-owner visibility -- every proprietor on a project now gets their own Recovery card entry; previously only the alphabetically-first "primary" owner did, so a co-owner's debt exposure on that project was invisible to Recovery entirely -- DONE
- Stage 10: per-owner call attribution in Recovery -- log-a-call and add-a-note merged into one action capturing project + specific owner + note in one record; backend + CSS shipped for a SOLO/JOINT badge and that owner's own last-contact date/note per plot (see Stage 12 in the addendum -- the JSX to actually render this badge/link row was still missing after this stage) -- DONE
- Stage 11: Director Dashboard's "stale call" KPI fixed to use the same per-owner eligibility rule as Recovery (it still used the old alphabetical-primary logic and could silently disagree with the Recovery page's own count); soft "co-owner recently contacted" notice added, 3-day look-back, never blocks the call -- DONE

---

## 11. WHAT STILL NEEDS TO BE DONE

### Remaining uniformity checks (pre-revamp, still open)
- Check screenshot of each page after deploy
- Table header alignment, row spacing uniformity across pages
- Pagination controls uniformity

### Mobile audit + small fixes (pre-revamp, still open)
- Full mobile responsiveness check on all pages
- Completed clients count on dashboard
- Print layout cleanup
- Phone uniqueness frontend validation (NOTE: may become moot once NIN is the real identity check in Phase 2)
- Release button should warn if no documents uploaded

### Language simplification
Checked (Aug 2026): none of the previously-flagged old terms ('Master Hardware Override',
'Nuclear Purge', 'Intel', 'Vault', 'Recovery Sync', 'Asset Intake', 'Forensic Stream') exist
anywhere in the current frontend. Nothing left to rename here.

### Future (not started)
- Multi-company: clone repo per client company

### UI Test Coverage (in progress)
- Playwright UI test for Intake Flow (/land/new -> /land/projects) -- IN PROGRESS
- Playwright UI test for Ledger -> Folder navigation
- Playwright UI test for Recovery -> Log Call flow

### MAJOR REVAMP -- SEE SECTION 17 FOR FULL DETAIL
The single biggest item in this section is the full project-based ERP revamp requested by
the employer (identity/NIN, 4-tier roles, stage templates, financials module, Director
dashboard, project index, legacy receivables). Do not try to summarize it here -- Section 17
is the authoritative source with the full architecture and Phase Tracker. This line exists
only as a pointer so nobody looking at Section 11 misses that the revamp is the current
top priority.

---

## 12. KNOWN ISSUES (not blocking)

- WebConfig.java has old local file serving reference -- harmless (Cloudinary is used)
- payment_schedules table still exists in DB -- no longer used (harmless)

---

## 13. DEPLOYMENT PROCESS

1. Create fix.py AND updated LLM_CONTEXT_ADDENDUM.md -> present_files both -> David downloads both
2. David replaces local fix.py AND local LLM_CONTEXT_ADDENDUM.md
3. `py fix.py` -> check output for OK/MISSING -- this also commits and pushes automatically
   (picking up both the code changes and the addendum replace), per the PERMANENT rule in
   Section 3. No manual git command needed.
4. Render -> Events tab -> wait for green tick (5-10 min free tier)
5. Test at golden-seed.onrender.com
6. If red: click 'deploy logs' -> read error -> fix -> repeat

---

## 14. COMMON ERRORS AND FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `ReferenceError: XIcon is not defined` | Icon used in JSX but missing from import list | Add to the import statement at top of file |
| `Cannot set boolean field isReceivable to null` | DB rows have NULL, Java primitive boolean | Use Boolean (capital B) not boolean |
| `UnicodeDecodeError in fix.py` | File has special chars, Windows encoding | Use errors='replace' when reading files |
| `UnicodeEncodeError in fix.py` | Windows default encoding on write | Always use encoding='utf-8' in open() |
| `nothing added to commit` | Files already match git | Force add specific files |
| `500 on /dashboard/summary` | Backend crash | Check Render Logs tab, read 'Caused by:' line |
| CSS class not found | Class used in JSX but not defined in .module.css | Add the missing class to the CSS file |
| `SyntaxError in fix.py with triple quotes` | LLM guide embedded inside triple-quoted string | Use list of lines joined with newlines instead |
| `fix.py shows 'patch target not found'` | Text to replace doesn't match file exactly | Read actual file from conversation context before writing patch |
| Header buttons overlapping title | position:absolute in CSS | Remove !important block, use .pageHeader flex layout |
| Text invisible on light bg | Color was rgba(255,255,255,x) -- white on cream | Use rgba(26,46,48,x) -- dark on light |

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

Full step-by-step rules live in LLM_CONTEXT_ADDENDUM.md's header -- read that file directly for
the process. Short version: work stays in the addendum until David confirms it, then moves into
Section 10 above (or Section 17/18's Phase Trackers for revamp/redesign phases) and is removed
from the addendum entirely.

**RULE:** The master guide (LLM_CONTEXT_GUIDE.md) is NEVER edited for incremental changes each session. All new rules, discoveries, and session notes go into LLM_CONTEXT_ADDENDUM.md only. The ONLY parts of the master guide that ever get updated are Sections 10 and 11.
**EXCEPTION (August 2026):** Section 17 below is a deliberate, one-time full-architecture addition requested directly by David to represent the revamp's permanent target design. It is NOT a violation of the above rule -- it is guide-level reference content, not a session note. Within Section 17 itself, only the Phase Tracker subsection updates as phases complete; the rest of Section 17 (decisions, role table, module list) is meant to stay stable once phases start shipping, the same way Section 9's business rules stay stable.
**EXCEPTION (August 2026, second instance):** The fix.py workflow rules in Section 3 (one-complete-fix.py-per-phase, and testing deferred until all phases are done) were also explicitly requested by David as permanent process rules, not one-session notes. They were written directly into Section 3 rather than the addendum for the same reason as the Section 17 exception above: they are standing process rules meant to govern every future session, not a fact about the current state of the code.
**EXCEPTION (August 2026, third instance):** Section 18 was added the same way as Section 17 -- a deliberate, one-time full-architecture addition for the Folder-to-Title redesign, not a session note. The same rule applies: only its Phase Tracker (18.10) updates going forward; the rest of Section 18 stays stable once Phase A starts shipping.

**RULE (August 2026, PERMANENT):** No fact, design standard, or process step should exist in more than one place in this guide. If something needs to be referenced elsewhere, point to it by section number instead of restating it. Found duplication is a documentation bug -- fix it immediately, the same way a code bug would be fixed.
**RULE (August 2026, PERMANENT):** When a later section changes a decision made in an earlier one (the way Section 18 overrides parts of Section 17), never delete or silently rewrite the earlier text. Leave it in place and add a short "SUPERSEDED by Section X.Y" note directly under it, pointing to the new authority. This keeps history intact and stops two sections from silently disagreeing.

---

## 17. PROJECT-BASED ERP REVAMP -- FULL TARGET ARCHITECTURE

**This section is the permanent, authoritative reference for the revamp. Do not re-litigate
these decisions in future sessions -- they are locked in. Only the Phase Tracker at the
bottom of this section should change as work progresses.**

**Companion document:** `ERP_REVAMP_PLAN.md` has the full plain-English write-up of all of
this, written for showing the employer directly. This section is the compressed version for
AI/technical context.

### 17.1 WHY THIS EXISTS
The employer wants the ERP transformed from a land-title tracking tool into a full
project-based company ERP: detailed cost breakdowns per project stage, a redefined RECEIVABLE
meaning, a searchable project index, NIN-based identity instead of phone-based, a 4-tier
role hierarchy, and a company-wide financials module separate from project costs.

### 17.2 TERMINOLOGY (redefined from the original system)
- **RECEIVABLE** = work not yet done / in progress (this is a NEW meaning -- the OLD system used
  "receivable" to mean overdue payment on a finished title. That old concept is renamed below.)
- **RECEIVABLES** = work finished, payment still owed (this is what "receivable" used to mean in
  the original system -- see Section 9 for the original mechanics, which carry over unchanged,
  just under the new name)

### 17.3 IDENTITY (NIN-based)
- NIN is mandatory for every person on every project, including foreigners. No exceptions --
  no project can be created without it.
- If a person's NIN changes, they are treated as a brand new person record. No merge/history
  needed -- old projects stay correctly linked to the old NIN, new projects link to the new one.
- Joint owners: every owner listed on a project must have their own valid NIN.
- Duplicate NIN handling: if a NIN already exists under a DIFFERENT name, BLOCK with a
  confirmation dialog (likely typo) -- staff must explicitly confirm "same person" or fix the
  NIN before the form can be saved (Stage 3 of the bug-fix roadmap upgraded this from a
  dismissible warning to a blocking confirm). If the NIN matches an EXISTING person being
  reused (second project, joint owner elsewhere), auto-fill their known details but allow
  staff to edit those details per-project (e.g. their address changed).

### 17.4 PROJECT INDEX
- Format: 001A, 002A ... 999A, then rolls to 001B, 002B ... 999B, then 001C, etc.
- Never repeats, never grows past 4 characters. Tied to the project/title itself, not the owner.
- Must be searchable in the Ledger.
- **SUPERSEDED by Section 18.3** -- the index is no longer tied to `LandTitle` creation. It is
  assigned at `LandProject` creation, before any title exists, and is permanent and universal
  across a record's whole life (folder, legacy, or titled). See Section 18 before touching any
  `ProjectIndexService` code.

### 17.5 PROCESSING STAGES
- Real stage list (confirmed by employer): Field Work, Deed Plan, LC Inspection,
  District Land Board Approval, Tax Assessment and Stamp Duty, Registration and Title Issuance.
- Model: a master "Stage Template" (checkbox list) with a default cost per stage (starts at 0,
  fully editable). Staff pick which stages apply per project via checkboxes. A "+" button lets
  staff add a custom one-off stage per project (and delete it). Every checked stage has its own
  editable cost field and its own notes field.
- Template editing rights: everyone EXCEPT Secretary can edit the master template
  (add/remove/rename stages, change default costs). Secretary can only pick from it.
- Stages can move backward (e.g. Approved -> Refused). Refused is not final -- can be resubmitted.

### 17.6 LEGACY RECEIVABLES (old titles in storage needing payment demanded)
- NOT an estimation system. Employer has real ledger totals for these, just no stage breakdown.
  Staff enter ONE lump total cost (the real number from the ledger). No "estimated" flag needed
  -- it's a real figure. Behaves exactly like normal project payment tracking once entered.
  Same duplicate-NIN check as regular projects applies.
- **SUPERSEDED by Section 18.6** -- "legacy" is no longer a structurally separate entry path or
  mode. It is a preset control on the single intake form: it auto-checks every processing stage
  and immediately unlocks the title fields, producing the exact same record shape as a
  folder-first project that has simply completed all its stages. `isLegacy` still exists as a
  flag but its meaning narrows to "this record used the preset," not "this record took a
  different code path." See Section 18 before touching intake or `atomicIntake()`.

### 17.7 ROLES (4-tier hierarchy, replacing current ROLE_ADMIN/ROLE_MANAGER)
| Role | Company Financials | Edits Costs | Changes Stages | Edits Template | Data Entry |
|---|---|---|---|---|---|
| Programmer (David, isRoot) | Yes | Yes | Yes | Yes | Setup/emergency only |
| Director | Yes -- full picture | Yes | Yes | Yes | Yes |
| Manager | No -- project-level only | Yes | Yes | Yes | Yes |
| Secretary | No | No | Yes (stage only, not cost) | No | Yes |
| Normal workers | -- | -- | -- | -- | No system access at all |

### 17.8 FINANCIALS MODULE
- Two completely separate, UNLINKED cost streams: (1) Project costs, tracked per-stage as
  above, and (2) Company/office costs (fuel, office costs, general field costs) -- NOT linked
  to any specific project, ever.
- Company cost categories are free-form: staff can add/delete categories as needed. The system
  should remember past entries and suggest them (same pattern as the existing `predictionService`
  used for district/county autocomplete in Intake -- reuse this exact mechanism).
- Cost timing: system suggests recurring vs one-off based on memory (e.g. recognizes "rent" was
  entered last month), but it's always the staff member's choice and editable at any time.
- Adopted the same "total committed vs amount paid" pattern already used for client debt,
  applied to company expenses too, so the Director can see both money owed/committed and money
  actually paid out -- not just cash that has already left the building.

### 17.9 DIRECTOR'S DASHBOARD
- Shows: company-wide cost/revenue/receivables snapshot, project pipeline overview (how many
  projects sitting at each stage), staff activity summary.
- Time period breakdown: must be possible to break down by day if needed. DEFAULT view is
  week + month (not day, not year, unless the Director changes it).

### 17.10 PHASE TRACKER (this is the only part of Section 17 that updates as work progresses)

**PHASE 1: Project Index System**
- What: `ProjectIndexService.java` (generates 001A/002A/etc), `project_index_counter` DB table,
  `project_index` column on `land_titles`, auto-assignment at intake, display + search in
  Ledger, display on Folder page header.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule and
  Section 17.11.
- Known limitation (expected, not a bug): existing/old plots will show a blank index until
  they are opened in edit mode and re-saved.

**PHASE 2: NIN-Based Identity**
- What: `nationalId` mandatory and unique-checked on the `Client` model, phone-number-based
  uniqueness assumption removed, duplicate-NIN warning + auto-fill-with-edit-allowed behavior
  per 17.3, Intake/Folder forms updated.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule.

**PHASE 3: 4-Tier Role System**
- What: `Role` enum expanded to the 4-tier system in 17.7 (Phase 3A). Phase 3B (every
  @PreAuthorize check and every frontend role check wired to the new roles) and Phase 3C
  (Settings UI updated with the Director/Secretary options and a real rank selector) were
  NOT actually finished at the time this entry originally claimed -- they were completed by
  Stage 1 and Stage 2 of the separate bug-fix roadmap instead (see LLM_CONTEXT_ADDENDUM.md).
- Status: APPLIED AND PUSHED, via the bug-fix roadmap rather than as part of the original
  Phase 3 rollout. Deferred testing -- see Section 3 permanent testing rule.

**PHASE 4: Processing Stage Template System**
- What: `StageTemplate` / `ProjectStage` models, master template CRUD, per-project stage
  attach/toggle-complete/edit-cost/remove (backend), the checkbox + "+" custom-stage UI on
  Intake, per-stage cost + notes fields, and the new STAGE CHECKLIST panel on FolderPage
  (frontend). The OLD hardcoded 5-stage `STAGE_LABELS` pipeline on FolderPage is deliberately
  left untouched and running in parallel -- see the design-decision comment in the relevant
  fix.py history for why both systems coexist for now.
- Status: APPLIED AND PUSHED (backend + frontend both landed, including the STAGES panel
  correction patch). Deferred testing -- see Section 3 permanent testing rule.

**PHASE 5: Financials Module (Company Costs)**
- What: the free-form-category `CompanyExpense`/`Expense` cash-out log (backend model, service,
  controller) plus the Expenses page (frontend), covering entry, category autocomplete, and
  analytics -- landed as several commits (Expenses rebuild, analytics + autocomplete + audit
  labels) rather than one combined fix.py, per `git log`.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule.
  (Doc correction: this entry previously said "NOT STARTED," which was stale.)

**PHASE 6: Legacy Receivables Entry Mode**
- What: the pre-existing `isLegacy` flag on `LandProject`, used at intake to mark old titles
  that skip the full stage checklist.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule.
  (Doc correction: this entry previously said "NOT STARTED," which was stale.)

**PHASE 7: Director's Dashboard**
- What: `DirectorDashboardDTO.java` and `GET /api/v1/dashboard/director` (backend, restricted
  to ROLE_ADMIN/ROLE_DIRECTOR), and `DirectorDashboardPanel.jsx` (frontend) showing day/week/
  month/year revenue, staff activity, pipeline stage counts, and the company financials
  snapshot.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule.
  (Doc correction: this entry previously said "NOT STARTED," which was stale.)

### 17.11 RECOMMENDED BUILD ORDER
Phase 1 (index) -> Phase 2 (NIN identity) -> Phase 3 (roles) -> Phase 4 (stage templates) ->
Phase 5 (financials) -> Phase 6 (legacy receivables) -> Phase 7 (Director dashboard).
Reasoning: identity and roles are foundational and everything else builds on top of them.
Stage templates and financials depend on roles existing first (permission checks need real
roles to check against). The Director dashboard comes last because it visualizes data that
only exists once the other phases are built.

Per the Section 3 permanent testing rule, Phases 1-4 above are all shipped but NOT yet
individually tested -- David will run one full end-to-end test pass covering Phases 1
through 7 together once Phase 7 is code-complete, not before.

---

## 18. FOLDER-TO-TITLE REDESIGN (RECOVERY MODULE ARCHITECTURE)

**This section is the permanent, authoritative reference for this redesign, same status as
Section 17. Do not re-litigate these decisions in future sessions -- they are locked in. Only
the Phase Tracker at 18.10 should change as work progresses. Where this section conflicts with
anything in Section 17, THIS SECTION WINS -- see the supersession notes left in 17.4 and 17.6.**

### 18.1 WHY THIS EXISTS
Today a `LandProject` cannot exist without a `LandTitle` (hard-required `@OneToOne`,
`nullable = false`). That's backwards -- in real life a client's project (owners, location,
payment history, processing stage) exists for months or years before a title is produced. This
redesign makes every project record exist from day one, growing additively as it moves through
processing, until a title exists. It is never rebuilt, converted, or replaced -- one continuous
record from creation to title issuance and beyond.

### 18.2 SINGLE-IDENTITY MODEL
One database record for the life of a project. Never transformed or swapped into a different
record when a title is produced. Fields are only ever ADDED to, never hidden, moved, or removed.
Status (Folder / Titled) is DERIVED from whether title fields are filled -- it is presentation
only, not a separate stored state machine staff toggle by hand.

### 18.3 PROJECT INDEX (overrides 17.4)
Assigned at `LandProject` creation, before any title exists. Permanent and universal across a
record's whole life -- folder, legacy, or already-titled. This is the client-facing search
handle ("this is my project index") and never changes or gets replaced by a plot number.

### 18.4 IDENTITY / LOCATION (extends 17.3)
- NIN is the true identity primary key, required per owner (including joint owners) before
  anything else can be entered. `Client.nationalId` moves from soft/optional to a true
  mandatory, unique-checked constraint -- the old guide claimed this was already enforced; it
  was not, and this redesign is where it actually becomes one.
- Location hierarchy -- District -> County -> Sub-county -> Parish -> Village, plus an optional
  Area field -- is PERMANENT, not folder-only. It lives on `LandProject` (moved up from
  `LandTitle`, which only had District/County) and stays visible for the record's entire life,
  title or no title.

### 18.5 PROCESSING STAGES -- UNLOCK TRIGGER (extends 17.5)
No new stage model needed. Checking the existing final template stage ("Registration and Title
Issuance") is what reveals the title/plot fields for data entry. No separate "convert" button,
modal, or wizard step. Stage checklist has no per-stage notes field -- notes are unified (18.8).

### 18.6 LEGACY AS PRESET (overrides 17.6)
Legacy is not a structurally separate entry mode or code path. It is a preset control on the
single intake form: it auto-checks every stage and jumps straight into the unlocked title
fields. Under the hood it produces the exact same record shape as a folder-first project that
has simply completed all its stages. `isLegacy` still exists as a flag but only marks that the
preset was used.

### 18.7 FINANCIALS
Live from day one regardless of title status -- total cost, initial payment, amount owed all
exist and are editable before a title exists. No change needed to where these fields live
(`LandProject`) -- they are already correct under this model.

### 18.8 NOTES
One notes field for the whole project, at the end of the page. Not one per stage. Any existing
per-`ProjectStage` notes field is deprecated in favor of this single project-level field.

### 18.9 TARGET DATA MODEL

**`LandProject`**
- `landTitle` relationship: `@OneToOne` changes from `nullable = false` to `nullable = true`.
  This is the core structural blocker and must land before anything else in this section.
- Gains `subCounty`, `parish`, `village`, `area` (new fields). `district`/`county` move up from
  `LandTitle` (migrate existing data, don't just duplicate the columns).
- Financials fields unchanged -- already correctly placed here.

**`LandTitle`**
- Stays optional-linked from `LandProject`. Only created/attached when the final stage is
  checked, or immediately if the legacy preset is used.
- Fields: `titleId` (new), `tenure` (unchanged, defaults to Freehold), `plotNumber` (unchanged),
  `blockRoad`/"Block" (unchanged), `physicalBoxNumber` (unchanged, still required).
- `area` lives ONLY on `LandProject` (18.4), not duplicated here -- it simply becomes
  read/write-unlocked once title fields appear, pre-filled if already entered at folder stage.

**`Client`**
- `nationalId` becomes a true mandatory, unique-checked column (see 18.4).

**`StageTemplate` / `ProjectStage`**
- No schema change. Legacy preset behavior (all applicable stages created pre-marked
  `isCompleted = true`) is service-layer only.

**`ProjectDocument`**
- Unaffected. Notes move to one `LandProject`-level field per 18.8.

### 18.9.1 SERVICE LAYER AUDIT (LandService.java)
Making `landTitle` nullable will NPE the following methods, which currently call
`project.getLandTitle().getPlotNumber()` (or similar) directly for audit logging with no null
check: `recordPayment`, `moveToReceivable`, `exitReceivable`, `updateProjectFull`,
`nuclearDelete`, `restoreProject`, `manualRealityOverride`, `authorizeRelease`,
`setStoragePaused`, `setStorageFeeOverride`, `setAccumulatedFees`, `setNegotiationDeadline`,
`setReceivableStartOverride`, `logUnlockAction`, `logFollowUp`. Every one needs a null-safe
fallback to `projectIndex` for logging when `landTitle` is null -- do all ~14 in the same pass,
not incrementally, or a deploy will break the moment a titleless project hits any of these.

`atomicIntake()` needs a bigger rewrite: today it builds `LandTitle` first (plot number,
physical box number required), then wraps it in `LandProject`. Under this redesign that
inverts -- `LandProject` (owners, location, stage) is what's created at intake; `LandTitle` is
only built and attached later, either immediately (legacy preset) or when the final stage is
checked.

### 18.9.2 DTOs
- `LandEntryRequest`: add `subCounty`, `parish`, `village`, `titleId`. `plotNumber`/`tenure`/
  `blockRoad` stop being required at submit time -- only validated as required if the legacy
  preset is used or the final stage is checked in the same submission. `isLegacy` narrows to
  "apply the legacy preset" per 18.6.
- `ProjectResponse`: add derived `status` (`"Folder"` if no `LandTitle` attached, `"Titled"` if
  one is -- legacy-originated projects are `"Titled"` immediately). Add `subCounty`, `parish`,
  `village`, `titleId` to the payload for Ledger/Folder display.

### 18.9.3 INTAKE PAGE -- TARGET LAYOUT
One form, no separate legacy route:
1. **Project index** -- auto-generated on save, permanent, shown at top.
2. **Owners** -- NIN required per owner; name, phone, email; "+ Add joint owner."
3. **Location** -- District -> County -> Sub-county -> Parish -> Village, optional Area.
   Permanent, stays visible regardless of title status.
4. **Stage checklist** -- checkboxes only, no per-stage notes. Final stage checkbox reveals
   section 5. Legacy preset control on this section auto-checks all stages and reveals section 5
   immediately.
5. **Title & Plot Details** -- hidden until unlocked. Title ID, Tenure (default Freehold), Plot
   Number, Block, Area (mandatory here, pre-filled from section 3 if already entered).
6. **Financials** -- Total cost, initial payment, amount owed. Live from first save.
7. **Documents & Notes** -- attachments, single shared notes field.

### 18.9.4 FOLDER PAGE
Same additive principle: owners, location, and stage checklist always shown. Title/plot fields
appear as an added block once they exist, never replacing anything above. Status tag
(Folder/Titled) shown next to the project index in the page header.

### 18.9.5 LEDGER PAGE
- Add a status tag column (Folder / Titled) next to project index in every row.
- Add a "Ready for Titling" filtered view: records with all prior stages complete and only the
  final stage outstanding, or final stage just checked but title fields still empty. Supports
  bulk-select -> bulk-mark-titled, after which staff fill in each record's unique Title
  ID/Plot Number/Area individually. Solves the ~200-at-once batch-return-from-land-board case
  without a manual ledger search per record.
- Any new UI added here (status tag, queue view) follows the Section 7 design standards --
  Ledger's own patterns -- exactly, per the LAW at the top of Section 7.

### 18.10 PHASE TRACKER (this is the only part of Section 18 that updates as work progresses)

**PHASE A: Make LandTitle optional + move location fields up**
- What: `LandProject.landTitle` -> `nullable = true`. Add `subCounty`/`parish`/`village`/`area`
  to `LandProject`. Migration to move existing `district`/`county` data from `LandTitle` rows up
  to their parent `LandProject` rows.
- Must land before any other phase in this section -- everything else assumes it's done.
- Status: NOT STARTED.

**PHASE B: LandService.java null-safety audit**
- What: fix the ~14 call sites in 18.9.1 to fall back to `projectIndex` for logging when
  `landTitle` is null. Rewrite `atomicIntake()` to build `LandProject` first, `LandTitle` only
  when triggered.
- Depends on: Phase A.
- Status: NOT STARTED.

**PHASE C: NIN becomes a true mandatory/unique constraint on Client**
- What: DB constraint + service-level validation, replacing the current soft/optional column.
- Depends on: nothing above, but ship before Phase D so intake doesn't need two passes on owner
  validation.
- Status: NOT STARTED.

**PHASE D: Intake page rebuild**
- What: the 7-section layout in 18.9.3 -- new fields wired to updated `LandEntryRequest`,
  final-stage-checkbox unlock behavior, legacy preset control, unified notes field, area
  carry-forward logic.
- Depends on: Phase A, B, C.
- Status: NOT STARTED.

**PHASE E: Folder page additive display + status tag**
- What: per 18.9.4 -- title/plot fields as an added block once present, status tag in header.
- Depends on: Phase A, D.
- Status: NOT STARTED.

**PHASE F: Ledger status tag column + Ready for Titling queue**
- What: per 18.9.5 -- status tag column, filtered queue view, bulk-mark-titled action.
- Depends on: Phase A, E.
- Status: NOT STARTED.

### 18.11 RECOMMENDED BUILD ORDER
Phase A (schema) -> Phase B (service null-safety) -> Phase C (NIN constraint) -> Phase D
(intake rebuild) -> Phase E (folder page) -> Phase F (ledger + queue).

Reasoning: A is the schema change everything else assumes. B must follow immediately -- the app
will NPE in production the moment any titleless project hits a payment, release, or audit-log
action otherwise. C is independent and cheap, best done early so D doesn't touch owner
validation twice. D, E, F all consume the new schema and are ordered by where data enters
(intake) before where it's displayed (folder, then ledger).

**Testing mode: TBD -- confirm with David before starting Phase A** whether this redesign runs
as its own standalone rebuild (deferred testing, one full pass after Phase F per the Section 3
rule) or gets folded into the bug-fix roadmap (tested per-stage, per the other Section 3 rule).
Do not assume either without an explicit answer.