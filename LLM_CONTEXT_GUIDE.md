# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE
# Last updated: August 2026

---

## 1. WHO IS DAVID

- Name: David, GitHub: nyenz. Location: Kampala, Uganda.
- Beginner developer. Can copy-paste commands and files exactly. Cannot debug independently.
- Tools: VS Code, Git Bash (inside VS Code), GitHub, Chrome.
- Python installed: use `py` command. Project folder: `C:/Users/nyenz/Desktop/app/ge solns`

---

## 2. HOW TO COMMUNICATE

- Use simple, plain English. Avoid technical jargon -- explain things in a way a newbie won't get confused by. Bullets/outline format. Short unless doing code.
- Read errors yourself and say exactly what's wrong in one sentence.
- Never ask A or B -- just do everything needed unless a real decision is required.
- Confirm one step at a time. Read screenshots carefully before responding.

---

## 3. THE PROJECT

**Name:** Golden Seed ERP (code name: NYENZ)

**What it does:** Golden Seed ERP is a company management tool built for GE Solutions, a Ugandan land surveying and title processing company. Its job is to track every client project from the moment it starts until the title is fully issued -- and to keep tracking it even after that, since finished projects still need payment follow-up and record-keeping.

**For each project, it stores:**
- The project's current stage (where it is in the processing pipeline)
- Title details (once the title is issued or being processed)
- Owner/client information (including joint owners)
- Financials -- total cost, payments received, and money still owed
- Documents and notes tied to that specific project

**Beyond individual projects, it also:**
- Tracks the company's own expenses -- daily costs up to bigger recurring costs -- separate from project costs
- Produces reports and detailed analysis covering the whole company's activity, not just one project
- Keeps an audit trail of actions taken in the system, so management can see who did what
- Tracks calls made to clients and reminds staff which clients need to be called, to support debt recovery
- Supports detailed, precise search and filtering across all this data, so staff can quickly narrow down to exactly what they need -- by project, stage, client, date, amount owed, and more

**Who uses it:** Staff only. This is an internal tool -- clients never log in or interact with it directly.

---

## 4. TECH STACK

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
- Backend: https://ge-solutions.onrender.com
- Frontend: https://golden-seed.onrender.com

**Database:** Host: ep-wispy-cell-an2afrm4.c-6.us-east-1.aws.neon.tech | Name: neondb | User: neondb_owner

---

## 5. KEY BUSINESS RULES

- **2-14 Rule:** Max 2 calls/client/month. Min 14 days between calls.
- **Recovery grouping:** By NIN (National ID Number) -- each owner is tracked individually, not by phone number.
- **Backlog:** work not yet finished (in progress).
- **Receivables:** all debt -- money owed to the company, whether from legacy work or regular (non-legacy) work.
- **Legacy (within Receivables):** triggered after 365 days with no payment (automatic), or an admin can trigger it manually.
- **Storage fee:** UGX 50,000 every 30 days. The 30-day timer only starts once the work becomes Legacy -- not before. This amount can be changed/overridden.
- **Payment types:** STANDARD, INITIAL_DEPOSIT, RECEIVABLE_PARTIAL.
- **Identity uniqueness:** NIN is the real uniqueness check per owner. Phone number is no longer used to prevent duplicates.
- **Access control:** Payments, receivable management, Reports, and Audit access follow the 4-tier role hierarchy (Programmer, Director, Manager, Secretary) -- not a simple Admin/Root split anymore.
- **Cloudinary:** All files stored on Cloudinary.
- **Project deletion:** soft-delete only -- deleting a plot hides it from Ledger/Recovery/Dashboard/Reports but keeps the row, payments, notes, and Cloudinary files intact. Root can restore it from Settings > Recently Deleted Plots.

---

## 6. HOW THE APP WORKS

**Main flow:**
1. **New Project** -- entry point with 3 modes: New Folder, New Title, Legacy Title. Each mode collects its own specific details.
2. **Ledger Page**
3. **Folder Page**
4. **Recovery Hub**
5. **Payments**

**Runs alongside the main flow, not as a final step:**
- **Audit** -- tracks actions as they happen throughout the whole flow
- **Recovery** -- also ongoing, not a one-time last step

**Supporting subsystems (separate from the main flow):**
- Security system
- Expenses system
- Analysis & Reports system
- Dashboard system

---

## 7. UI DESIGN STANDARDS

### LAW: LEDGER PAGE IS THE REFERENCE DESIGN -- **This is the master rule everything else follows.**
Ledger is the closest existing page to the target design language for the whole app. **Every** other list, table, filter bar, search box, dropdown, or empty state **must** default to Ledger's existing pattern unless a subsection below says otherwise.

### UI UNIFORMITY RULE -- **Applies everywhere, no exceptions without explicit instruction.**
Every element of the same type **must** look and behave identically across all pages, regardless of where it appears. Covers: buttons, headings, inputs, dropdowns, tables, lists, badges, modals, pagination, empty states, icons, scrollbars. For every element, the following **must be identical everywhere**: font, color, padding, margin, spacing/gap, border, shadow, hover/active/selected/focus/error states, and responsive behavior.

### RESPONSIVENESS RULE -- **No element is allowed to break on any screen size.**
Every element, property, and value **must** respond to screen size changes by default. Use clamp() for fonts/spacing, %/vw/vh for widths/heights. Hardcoded px **only** for values that must never scale (e.g. 1px border). **Nothing** overflows, overlaps, or disappears on small screens.

### "SAME DESIGN" PHRASE RULE
When an instruction says "same design," the element **must** be identical in every measurable way: size, padding, margin, gap, font, color, border, shadow, responsiveness, hover/active/selected/focus/error states, animation, alignment.

### NO BROWSER DEFAULT STYLING RULE
Every element **must** be explicitly styled -- **no** browser defaults anywhere (buttons, inputs, dropdowns, checkboxes, scrollbars, arrows, links, tables, focus outlines, placeholder text, number spinners, date pickers, search cancel buttons). Every new element must match the existing app theme.

### ICON RULE
Icons **must** come from the same icon library already used in the app (react-icons/fi -- see Section 11's import-checking rule). Size, color, and stroke weight for icons of the same type **must** match everywhere they appear.

### ANIMATION / TRANSITION RULE
Any hover, active, or state-change animation **must** use consistent timing and easing across the whole app (match whatever Ledger already uses). No page gets its own custom animation speed or style without explicit instruction.

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
- NEW: Project Index (e.g. "#001A") shown next to plot number, reuses districtTag styling (see Section 8.3)

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

### Button Style Standard (outside modals)
- Primary: `background: var(--orange)`, `color: #1a2e30`, bold uppercase text
- Secondary: `background: rgba(26,46,48,0.75)`, `border: 1.5px solid rgba(255,255,255,0.18)`, `color: rgba(255,255,255,0.85)`
- Danger: red-tinted background, white text
- Hover/active states follow the same pattern as Filter Button Style

### Loading State Style
- Use a simple spinner or skeleton block matching the app's dark theme -- no default browser spinners, no white flash

### Toast / Notification Style
- Success: green-tinted, Error: red-tinted, both dark-glass background matching the app theme, positioned consistently (e.g. top-right), auto-dismiss after a few seconds

### Checkbox / Toggle Style
- Custom-styled to match theme -- checked state uses `var(--orange)`, unchecked uses the dark theme border color, no native browser checkbox/toggle appearance anywhere

### Empty State Rules
- Searching in tables MUST return dynamic text: `NO RECORDS MATCH 'term'`

### FolderPage Header
- Uses `.terminalHeader` -- its own unique design, do NOT change to pageHeader

---

## 8. FOLDER-TO-TITLE REDESIGN (RECOVERY MODULE ARCHITECTURE)

**This section is the permanent, authoritative reference for this redesign. Do not re-litigate these decisions in future sessions -- they are locked in. Only the Phase Tracker at 8.10 should change as work progresses.**

### 8.1 WHY THIS EXISTS
Today a `LandProject` cannot exist without a `LandTitle` (hard-required `@OneToOne`, `nullable = false`). That's backwards -- in real life a client's project (owners, location, payment history, processing stage) exists for months or years before a title is produced. This redesign makes every project record exist from day one, growing additively as it moves through processing, until a title exists. It is never rebuilt, converted, or replaced -- one continuous record from creation to title issuance and beyond.

### 8.2 SINGLE-IDENTITY MODEL
One database record for the life of a project. Never transformed or swapped into a different record when a title is produced. Fields are only ever ADDED to, never hidden, moved, or removed. Status (Folder / Titled) is DERIVED from whether title fields are filled -- it is presentation only, not a separate stored state machine staff toggle by hand.

### 8.3 PROJECT INDEX
Assigned at `LandProject` creation, before any title exists. Permanent and universal across a record's whole life -- folder, legacy, or already-titled. This is the client-facing search handle ("this is my project index") and never changes or gets replaced by a plot number.

### 8.4 IDENTITY / LOCATION
- NIN identity rule: see Section 5 ("Identity uniqueness"). Technical note: `Client.nationalId` moves from soft/optional to a true mandatory, unique-checked database constraint -- this redesign is where it actually gets enforced in code.
- Location hierarchy -- District -> County -> Sub-county -> Parish -> Village, plus an optional Area field -- is PERMANENT, not folder-only. It lives on `LandProject` (moved up from `LandTitle`, which only had District/County) and stays visible for the record's entire life, title or no title.

### 8.5 PROCESSING STAGES -- UNLOCK TRIGGER (Folder Page)
No new stage model needed. For a project started as "New Folder," checking the final template stage ("Registration and Title Issuance") on the Folder Page reveals the Title Details fields. No separate "convert" button, modal, or wizard step. Stage checklist has no per-stage notes -- notes are a single project-level field (see 8.8).

This trigger only applies to Folder-mode projects. "New Title" and "Legacy Title" projects skip Stages entirely and show Title Details right away -- see 8.6.

### 8.6 LEGACY TITLE ENTRY MODE
Legacy Title is one of the 3 entry modes picked at the start of the New Project Page (New Folder, New Title, Legacy Title). Picking it shows the same layout as "New Title" mode -- Title Details appears, Stages is skipped entirely. Under the hood it produces the same record shape as a Folder-mode project that has completed all its stages. `isLegacy` still exists as a flag marking this entry mode was used.

### 8.7 FINANCIALS
Live from day one regardless of title status -- total cost, initial payment, amount owed all exist and are editable before a title exists. No change needed to where these fields live (`LandProject`) -- they are already correct under this model.

### 8.8 NOTES
One notes field for the whole project, at the end of the page. Not one per stage. Any existing per-`ProjectStage` notes field is deprecated in favor of this single project-level field.

### 8.9 NEW PROJECT PAGE -- TARGET LAYOUT
Three entry modes chosen first: **New Folder**, **New Title**, **Legacy Title**.

**New Folder mode:**
1. Entry mode
2. Owners -- NIN, Full Name, Phone Number, Email (see Section 5 / 8.4 for NIN rule)
3. Location (see 8.4)
4. Stages -- Field Work first ... Registration and Title Issuance last (see 8.5)
5. Finance (see 8.7)
6. Documents
7. Notes (see 8.8)

**New Title / Legacy Title mode:**
1. Entry mode
2. Owners -- NIN, Full Name, Phone Number, Email
3. Title Details -- Title ID, Tenure (default Freehold), Plot Number, Block, Title Date
4. Location (see 8.4)
5. Finance (see 8.7)
6. Documents
7. Notes (see 8.8)

Legacy Title uses the exact same layout as New Title (see 8.6).

### 8.9.1 FOLDER PAGE
Owners and Location are always shown. Stage checklist is shown only for projects created in New Folder mode -- New Title and Legacy Title projects don't have one, since Title Details already exist from creation. Title/plot fields appear as an added block once they exist (either after the final stage is checked in Folder mode, or immediately for New Title/Legacy Title mode) -- never replacing anything above. Status tag (Folder/Titled) shown next to the project index in the page header.

### 8.9.2 LEDGER PAGE
- Add a status tag column (Folder / Titled) next to project index in every row.
- Add a "Ready for Titling" filtered view: records with all prior stages complete and only the final stage outstanding. Supports bulk-select -> bulk-mark-titled, after which staff fill in each record's Title Details individually. Solves the batch-return-from-land-board case without a manual search per record.
- Any new UI added here follows Ledger's own design patterns (Section 7).

### 8.10 PHASE TRACKER (this is the only part of Section 8 that updates as work progresses)

**PHASE A: Make LandTitle optional + move location fields up**
- What: `LandProject.landTitle` becomes optional. Location fields (subCounty/parish/village/area) added to `LandProject`. Migrate existing district/county data up from `LandTitle`.
- Must land before any other phase in this section.
- Status: NOT STARTED.

**PHASE B: LandService.java null-safety audit**
- What: find and fix any code that assumes every project has a `LandTitle` -- it needs a safe fallback when one doesn't exist yet. Also update any code still reading/writing `district`/`county` from `LandTitle` instead of `LandProject`.
- Depends on: Phase A.
- Status: NOT STARTED.

**PHASE C: NIN becomes a true mandatory/unique constraint on Client**
- What: DB constraint + service-level validation, replacing the current soft/optional column.
- Depends on: nothing above, but ship before Phase D so the New Project Page doesn't need two passes on owner validation.
- Status: NOT STARTED.

**PHASE D: New Project Page rebuild**
- What: the mode-based layout in 8.9 (New Folder / New Title / Legacy Title), new fields wired to updated `LandEntryRequest`, stage unlock behavior (8.5), Legacy Title entry mode (8.6), separate notes field, area carry-forward logic.
- Depends on: Phase A, B, C.
- Status: NOT STARTED.

**PHASE E: Folder page additive display + status tag**
- What: per 8.9.1 -- title/plot fields as an added block once present, status tag in header.
- Depends on: Phase A, D.
- Status: NOT STARTED.

**PHASE F: Ledger status tag column + Ready for Titling queue**
- What: per 8.9.2 -- status tag column, filtered queue view, bulk-mark-titled action.
- Depends on: Phase A, E.
- Status: NOT STARTED.

### 8.11 RECOMMENDED BUILD ORDER
Phase A (schema) -> Phase B (service null-safety) -> Phase C (NIN constraint) -> Phase D (New Project Page rebuild) -> Phase E (folder page) -> Phase F (ledger + queue).

Reasoning: A is the schema change everything else assumes. B must follow immediately -- the app will NPE in production the moment any titleless project hits a payment, release, or audit-log action otherwise. C is independent and cheap, best done early so D doesn't touch owner validation twice. D, E, F all consume the new schema and are ordered by where data enters (the New Project Page) before where it's displayed (folder, then ledger).

Dashboards come last for all users/roles, not just the Director -- dashboards visualize data that only exists once the underlying features are built.

**Testing:** per Section 9's testing rule, this redesign is tested as one batch -- one full test pass once Phase F is code-complete, not before.

### 8.12 DIRECTOR'S DASHBOARD
- Company-wide financial overview: revenue, expenses, profit, backlog, Receivables
- Project pipeline: how many projects are sitting at each stage
- Staff activity: who's doing what, call logs, recovery progress
- Trends over time: switchable between day/week/month/year (default: week + month)
- Drill-down: click from a company-wide number down into the specific projects behind it
- Alerts: things that need attention (e.g. overdue Receivables, stalled projects)
- Custom date range filtering
- Exportable reports (ties into the existing Reports system)

---

## 9. THE fix.py SYSTEM -- CRITICAL RULES

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
**RULE (PERMANENT): Each phase or batch of work ships as ONE complete fix.py, start to finish. Never split into sub-parts unless David asks.**
**RULE (PERMANENT): Both revamp phases and bug-fix batches follow deferred testing. Group related fixes/changes into a batch, ship each as its own fix.py, and test only once the whole batch is code-complete and deployed -- not after each individual item. Before running any test, ask David for permission first -- never start testing on your own. Only test sooner if David explicitly asks to check something mid-batch.**
**RULE (PERMANENT): Every fix.py auto-commits and pushes to git as its last step (add, commit, push) with a fix-specific message. David never types git by hand.**

### Why patches fail:
- If fix.py says 'patch target not found', the text doesn't match exactly OR the change was already applied.
- Copy the exact block including all whitespace, comments, and surrounding lines.

### How David uses fix.py:
See Section 10 for the full step-by-step deploy flow.

---

## 10. DEPLOYMENT PROCESS

1. Create fix.py AND updated LLM_CONTEXT_ADDENDUM.md -> present both -> David downloads both
2. David replaces local fix.py AND local LLM_CONTEXT_ADDENDUM.md
3. `py fix.py` -> check output for OK/MISSING -- this also commits and pushes automatically
4. Render -> Events tab -> wait for green tick (5-10 min free tier)
5. **Only once the full batch is code-complete, and David gives permission** -> test at golden-seed.onrender.com
6. If red: click 'deploy logs' -> read error -> fix -> repeat

---

## 11. COMMON ERRORS AND FIXES

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

## 12. CLOUDINARY DETAILS

- Cloud name: dfd115bnz
- Images: resource_type=image
- PDFs and docs: resource_type=raw, access_mode=public
- Folder structure: ge_solutions/{project-index}/ (e.g. ge_solutions/001A/)
- Folder deleted after nuclear purge
- If PDFs show 401: check Cloudinary dashboard > Security > Restricted media types. Fix is on Cloudinary side.

---

## 13. SESSION MANAGEMENT RULES (HOW EVERY SESSION ENDS)

Full step-by-step rules live in LLM_CONTEXT_ADDENDUM.md's header -- read that file directly for the process. Short version: work stays in the addendum until David confirms it, then moves into Section 14 (or Section 8's Phase Tracker for redesign phases) and is removed from the addendum entirely.

**RULE:** The master guide is NEVER edited for incremental changes each session. All new rules, discoveries, and session notes go into LLM_CONTEXT_ADDENDUM.md only. The ONLY parts of the master guide that ever get updated are Sections 14 and 15.

**EXCEPTION:** Sections 8 and 9 contain permanent reference content (standing process rules, and full architecture plans), not session notes -- so they don't follow the "only Sections 14/15 get updated" rule above. Each still only updates in one specific way: Section 9's process rules change only when David explicitly approves a new permanent rule; Section 8 only updates its own Phase Tracker subsection as work progresses. Everything else in these sections stays locked in once written.

**RULE (PERMANENT):** No fact, design standard, or process step should exist in more than one place in this guide. If something needs to be referenced elsewhere, point to it by section number instead of restating it. Found duplication is a documentation bug -- fix it immediately, the same way a code bug would be fixed.

**RULE (PERMANENT):** When a later section changes a decision made in an earlier one, never delete or silently rewrite the earlier text. Leave it in place and add a short "SUPERSEDED by Section X.Y" note directly under it, pointing to the new authority.

---

## 14. WHAT HAS BEEN COMPLETED
*(Nothing yet -- list starts fresh from this reset point forward.)*

---

## 15. WHAT STILL NEEDS TO BE DONE
*(Nothing listed yet -- starts fresh from this reset point forward.)*

---

## 16. KNOWN ISSUES (not blocking)
*(Nothing listed yet -- starts fresh from this reset point forward.)*