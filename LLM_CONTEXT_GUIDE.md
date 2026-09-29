# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE
# Last updated: September 2026 (fix141: guide cleaned up to match the code)

> ##############################################################
> ## STANDING REMINDER -- HOSTING MOVE IS PENDING (READ FIRST) ##
> ##############################################################
> David has DECIDED to move the app onto ONE Hetzner server, but it is NOT DONE yet.
> Nothing has been bought or moved. The full plan is in SECTION 18 at the bottom.
>
> RULES FOR EVERY LLM THAT READS THIS GUIDE:
> 1. In your FIRST reply of the session, add ONE short line reminding David that the
>    hosting move (Section 18) is still pending. Then carry on with whatever he
>    asked. Do not nag more than once per session. (Do NOT nag about passwords or
>    security -- David chose to leave those for the end.)
> 2. Do NOT start the move unless David says so.
> 3. Keep this reminder until Section 18 says "STATUS: DONE". Only a fix script that
>    marks Section 18 as done may remove this block.
> 4. When he does start: ONE step at a time, exact copy-paste commands, plain
>    English. He is a beginner.

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
| File Storage | Cloudinary (details: Section 12) |
| Deployment | Render free tier |
| Repo | GitHub (currently PUBLIC -- David will switch it to private before real data goes in): github.com/nyenz/ge-solutions-erp |

**URLs:**
- Backend: https://ge-solutions-api.onrender.com (the app calls it at /api/v1)
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
- **Phone numbers (fix139):** staff can type a number any normal way (0772 123 456, +256772123456, 772123456). It is checked and saved as +256772123456. Several numbers are separated with "/" (max 3 per person). Wrong length, letters, or made-up numbers (6+ of the same digit in a row, or 7+ counting digits) are refused. A foreign number is allowed only when typed with its + country code. Checked in the browser (`utils/phone.js`) and again on the server (`PhoneUtil.java`) -- keep the two in step. Old numbers already saved are not changed.
- **Access control:** Payments, receivable management, Reports, and Audit access follow the 4-tier role hierarchy (Programmer, Director, Manager, Secretary) -- not a simple Admin/Root split anymore.
- **Files:** all uploads are stored on Cloudinary today (details: Section 12; changes when hosting moves, Section 18).
- **Project deletion:** soft-delete only -- deleting a plot hides it from Ledger/Recovery/Dashboard/Reports but keeps the row, payments, notes, and Cloudinary files intact. Root can restore it from the Settings > ARCHIVE tab.

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

### DESIGN REFERENCE PAGES (READ FIRST -- David's baseline, in priority order)
**THE CODE IS THE TRUTH.** When you change or create any element, first find the closest match in the pages below (in this order), OPEN that CSS file, and copy its pattern. If this summary and the CSS file disagree, the CSS file wins. Only if nothing matches, ask David.

**1. INTAKE PAGE -- the main baseline for most things.** Files: `pages/Intake/IntakePage.module.css`, `components/ui/CollapsibleSection.module.css`, `components/ui/CornerDecor.module.css`, `components/common/HardwareSelect.module.css`.
- Panels (`CollapsibleSection`): diagonal navy-teal gradient (`135deg, #3a5a5c -> #2a4a4c -> #213E40`), thin orange border at 20% that goes full orange on hover, 10px radius, soft deep shadow. The header bar is darker (`#162a2c`); a thin 1.5px orange line shows under it ONLY while the panel is open (no glow). Title: Cinzel 700, orange, 2px letter-spacing, uppercase, turns white on hover. The chevron turns orange when open. The body opens with a 0.2s fade-slide. `.accent` = 2px full-orange border for the focused panel. Corner brackets, the tiny glowing dot and the pins come from `CornerDecor`.
- Dropdown (`HardwareSelect`): white box, 1.5px orange-at-30% border, 6px radius, height `clamp(34px,4.3vw,40px)`, orange chevron that flips. Hover or open = full orange border plus a soft 2px orange ring. The list: white, 1.5px orange border, 6px radius, deep shadow, bold navy options with hairline separators, hover or selected = solid orange with white text, opens with a 0.2s slide, max height 220px, hidden scrollbar. Inside popups use `HardwareModalSelect`.
- Also copy from Intake: inputs (`.input`, `.textarea`: white, orange border on hover and focus), type buttons (`.typeBtn`, `.typeBtnActive`: dark, active = solid orange with navy text), `.grid2` / `.grid3`, `.dropzone` (dashed orange), `.financialsSummary`, `.noteDateChip`, `.btn` / `.btn.primary`, `.toast`.

**2. LEDGER PAGE -- second priority, especially the table.** File: `pages/Ledger/LedgerPage.module.css`.
- Table card (`.tablePanel`): gradient `160deg, #1c3335 -> #213E40`, 1.5px orange-at-28% border, 10px radius, bottom corner brackets and pins only.
- Header row (`.ledgerTable thead th`): sticky INSIDE the table's own scroll box, opaque `#162a2c`, orange text, weight 900, uppercase, 2px letter-spacing, 3px orange bottom border. Sortable headers get an orange wash and white text on hover.
- Rows: `12px 14px` padding, faint 1px white-6% lines. Hover = white 4% wash plus a 3px orange left edge, no glow. Numbers, phones and indexes are Space Mono. Status words are plain coloured text (no pills). Problem and receivable rows get a faint red tint.
- Also copy: `.searchInner` (white search box, orange focus ring), `.filterBtn` / `.activeFilter`, `.pagination` / `.pageBtn`, the stage dots (`.stageDot*`), `.legendRow`.

**3. REPORTS PAGE -- lists inside panels, and the light/dark tone play.** Files: `pages/Reports/ReportHub.module.css` (and `ReportStudio.module.css`).
- List row (`.reportRow`): a 3-column grid = icon frame, title, chevron. Hover = white 3.5% wash and the chevron turns orange. Open row = orange 6% wash plus a 3px orange left edge.
- Icon frame (`.iconFrame`): small rounded square, orange-tinted fill, thin orange border, orange icon.
- Light rows on a dark panel (`.libList`): each row is a WHITE card (6px radius) with dark navy text and an orange-tinted hover (7-9%). Small group labels (`.libLabel`): DM Sans 900, 2px letter-spacing, white 60%. The detail drawer (`.detailBox`) is near-black with a 4px orange left edge. Chips: `.libChip`.

**4. RECOVERY PAGE -- popups and the font/colour emphasis.** Files: `components/common/HardwareModal.module.css` (the popup) and `pages/Recovery/RecoveryPortal.module.css`.
- Popup (`HardwareModal`, used for the CALL LOG window): dark blurred backdrop (`rgba(10,20,25,0.8)` + 6px blur). The card has gradient `160deg, #1c3335 -> #213e40`, 2px orange-at-40% border, 14px radius, deep shadow, 0.25s slide-up. The title is Cinzel orange with a thin orange line under it. Popup inputs are white with an orange border. Use the `modalStyles.*` classes (see Modal Popup Standard below).
- Emphasis by colour and font: the client name is bold uppercase (Cinzel orange in the card head); the NIN and section labels are orange (`#ffb46b` in the final rules), in Space Mono or tiny DM Sans caps; good = `#34d399`, bad = `#fca5a5`, none = white 50%, written as plain text with a thin underline (no pills); call position = cyan `#67e8f9`; in history, dim details (white 45%) sit next to bright text (white 80%).
- WARNING: `RecoveryPortal.module.css` has many layered overrides. The LAST rule for a class wins. Read to the end before copying.

**5. SETTINGS PAGE -- section colours tied to the tabs.** File: `pages/settings/SettingsPage.module.css`.
- The tabs sit in a grey dock (`.tabDock`, `#4d5c5a`, 8px radius). Each tab has its own accent (`data-accent`): orange, cyan, violet, red, slate (variables at the top of the file) -- Appearance, Security, Staff, Danger, Archive. The active tab fills with its accent plus a soft matching glow; hover only tints the text.
- The card under the tabs recolours its head bar, focus ring and hover glow from ONE variable, `--accent`, so section and tab always match. The card chrome is shared with `ReportStudio.module.css`.
- Light groups (`.prefGroupBox`): a cream-white surface with dark navy text (65% for secondary text), orange on hover, solid orange when selected. Rank text colours: admin amber `#fbbf24`, manager cyan `#06b6d4`, secretary green `#4ade80`.

### LAW: LEDGER PAGE IS THE REFERENCE DESIGN -- **This is the master rule everything else follows.**
Ledger is the closest existing page to the target design language for the whole app. **Every** other list, table, filter bar, search box, dropdown, or empty state **must** default to Ledger's existing pattern unless a subsection below says otherwise.

**SUPERSEDED by "DESIGN REFERENCE PAGES" above:** Intake is now the first baseline and Ledger is second.

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
Any hover, active, or state-change animation **must** use consistent timing and easing across the whole app. Confirmed standard timings (from the New Project Page, the reference implementation): hover/state transitions = **0.2s**, toast slide-in = **0.3s ease-out**, whole-page entrance fade-up = **0.6s cubic-bezier(0.2, 1, 0.3, 1)**. No page gets its own custom animation speed or style without explicit instruction.

### CORE DESIGN TOKENS (confirmed from code -- use these exact values everywhere)
```
--orange:        #EE8C3A
--orange-dim:    rgba(238, 140, 58, 0.18)
--orange-border: rgba(238, 140, 58, 0.28)
--navy:          #213E40
--navy-deep:     #1a2e30
--red:           #ef4444
--green:         #10b981
--radius:        10px
--radius-sm:     6px
```
Font families: **Cinzel** (serif) for page titles, section headings, modal titles. **Inter** (sans-serif) for body text, labels, buttons, inputs. **Space Mono** for plot numbers, project index values, phone numbers and other IDs and figures. **DM Sans** (sans-serif, weight 900, small uppercase) for page-header subtitles, small labels and legends on the Reports, Recovery and Settings pages.
Font sizes and spacing use `clamp()` throughout (see Responsiveness Rule) -- do not hardcode pixel font sizes.

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

### Button Style Standard (outside modals) -- CONFIRMED FROM CODE
- Default: transparent background, `border: 1.5px solid rgba(255,255,255,0.1)`, `color: rgba(255,255,255,0.7)`, uppercase, letter-spacing 1.5px, font-weight 900
- Default hover: `background: rgba(255,255,255,0.07)`, `border-color: rgba(255,255,255,0.22)`, `color: #fff`
- Primary: `background: var(--orange)`, `color: #fff` (white text, NOT navy), `border-color: var(--orange)`
- Primary hover: `background: #d97a2b`
- Secondary/Add/Filter-style button (dark-bg variant): `background: rgba(26,46,48,0.75)`, `border: 1.5px solid rgba(255,255,255,0.18)`, `color: rgba(255,255,255,0.85)` -- same as Filter Button Style above
- Danger/Delete: transparent background, `border-color: rgba(239,68,68,0.3)`, `color: rgba(239,68,68,0.7)` -- turns solid only on hover: `background: rgba(239,68,68,0.15)`, `border-color: var(--red)`, `color: var(--red)`
- Disabled: `opacity: 0.18`, `cursor: not-allowed`
- Small variant: reduced padding, same colors/states

### Loading State Style -- CONFIRMED FROM CODE
- Every "loading...", "syncing..." and "no records" message uses the ONE shared component `components/common/LoadingState.jsx` (`tone="panel"` draws its own dark card; `tone="bare"` when already inside a dark panel; `size="page"` for a whole-page screen). Never write a custom loading message.
- Only a single small value that is not ready yet (e.g. the project index on the Intake page) shows the inline text "Loading...". No spinner graphic.
- Skeleton blocks exist only on the Folder page.

### Toast / Notification Style -- CONFIRMED FROM CODE
- Info/default: `background: #1a2e30`, `border: 1px solid rgba(238,140,58,0.28)`, white text
- Success: solid `background: #10b981` (green), matching border
- Error: solid `background: #ef4444` (red), matching border
- Position: fixed, **bottom-right** of screen (`bottom: clamp(16px,2.5vh,28px)`, `right: clamp(16px,2vw,28px)`)
- Animation: slides in from the right, `0.3s ease-out`
- Auto-dismiss after a few seconds (do not require the user to close it manually)

### Checkbox / Toggle Style -- CONFIRMED FROM CODE
- Use a normal native `<input type="checkbox">`, tinted with `accent-color: var(--orange)`, sized `15px x 15px`. Do NOT fully custom-build checkboxes from scratch -- the native element with `accent-color` is the standard here.

### Empty State Rules
- Searching in tables MUST return dynamic text: `NO RECORDS MATCH 'term'`

### Grid Field Layout Pattern (NEW -- confirmed from code, apply everywhere forms have grouped fields)
- 2-column field groups: `grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))`
- 3-column field groups (e.g. short fields like plot number, block): `repeat(auto-fit, minmax(130px, 1fr))`
- Both auto-collapse to fewer columns on narrow screens automatically -- no manual breakpoint needed for this part
- Gap between fields: use the standard `--gap-lg` spacing token

### DESIGN RULES (fix58)
1. X IS THE CLOSER: any popup/modal that shows the animated X must NOT also show a CANCEL button. X = dismiss.
2. LOADING STATES: use the shared `LoadingState` component (see Loading State Style above), never a custom message.
3. ATTENTION COLORS: green = healthy/active/paid, orange = pending/backlog, red = debt/danger, amber = paused/negotiation, cyan = released/info. Use consistently app-wide.
4. INACTIVITY: edit mode auto-saves and deactivates after 5 minutes of no interaction.
5. RELATED PROJECTS: Owners tab always lists every other project of each owner/joint owner, clickable to navigate.

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

### 8.5 PROCESSING STAGES -- UNLOCK TRIGGER
No new stage model needed. Checking the final template stage ("Registration and Title Issuance") reveals the Title Details fields. This works in two places, confirmed in code: (1) on the Folder Page, for an existing Folder-mode project as staff work through its stages over time, and (2) right on the New Project Page itself, if staff check the final stage while still creating a New Folder-mode project -- Title Details appears immediately in that same form. No separate "convert" button, modal, or wizard step in either case. Stage checklist has no per-stage notes -- notes are a single project-level field (see 8.8).

"New Title" and "Legacy Title" entry modes skip Stages entirely and show Title Details right away -- see 8.6.

### 8.6 LEGACY TITLE ENTRY MODE
Legacy Title is one of the 3 entry modes picked at the start of the New Project Page (New Folder, New Title, Legacy Title). Picking it shows the same layout as "New Title" mode -- Title Details appears, Stages is skipped entirely. Under the hood it produces the same record shape as a Folder-mode project that has completed all its stages. `isLegacy` still exists as a flag marking this entry mode was used.

**Technical note:** `isLegacy` and `isReceivable` (the Receivable/debt flag -- see Section 5) are two separate, independently-set fields in the code. Choosing Legacy Title mode does not automatically make a project Receivable, and a non-legacy project can still become Receivable on its own (e.g. via the 365-day trigger). Don't assume one implies the other when reading or writing logic that touches either flag.

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

**Confirmed against the actual codebase (August 2026): Phases A through F are all built and live.**

**PHASE A: Make LandTitle optional + move location fields up**
- What: `LandProject.landTitle` becomes optional. Location fields (subCounty/parish/village/area) added to `LandProject`. Migrate existing district/county data up from `LandTitle`.
- Status: DONE. Confirmed in code -- `LandProject.landTitle` is `nullable = true`; district/county/subCounty/parish/village/area all live on `LandProject`. `LandTitle` has gone further than planned -- district/county and other legacy fields have been fully dropped from `LandTitle` (referred to in code comments as "PHASE G").

**PHASE B: LandService.java null-safety audit**
- What: find and fix any code that assumes every project has a `LandTitle` -- it needs a safe fallback when one doesn't exist yet. Also update any code still reading/writing `district`/`county` from `LandTitle` instead of `LandProject`.
- Status: DONE. Confirmed in code -- `LandService.java` has null-safe handling for `landTitle` throughout.

**PHASE C: NIN becomes a true mandatory/unique constraint on Client**
- What: DB constraint + service-level validation, replacing the current soft/optional column.
- Status: DONE. Confirmed in code -- `Client.nationalId` is `nullable = false, unique = true`, enforced at both DB and service level.

**PHASE D: New Project Page rebuild**
- What: the mode-based layout in 8.9 (New Folder / New Title / Legacy Title), new fields wired to updated `LandEntryRequest`, stage unlock behavior (8.5), Legacy Title entry mode (8.6), separate notes field, area carry-forward logic.
- Status: DONE. Confirmed in code -- `IntakePage.jsx` implements all 3 entry modes with the correct section order and fields as described in 8.9.

**PHASE E: Folder page additive display + status tag**
- What: per 8.9.1 -- title/plot fields as an added block once present, status tag in header.
- Status: DONE. Confirmed in code -- `FolderPage.jsx` shows FOLDER/TITLED status and renders title fields conditionally once `landTitle` exists.

**PHASE F: Ledger status tag column + Ready for Titling queue**
- What: per 8.9.2 -- status tag column, filtered queue view, bulk-mark-titled action.
- Status: DONE. Confirmed in code -- `LedgerPage.jsx` has the status tag column, a "READY FOR TITLING" filter, and a working bulk-mark action.

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

1. Create fix.py -> present it -> David downloads it
2. David replaces local fix.py
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

This is the ONE place Cloudinary is described (Sections 4 and 5 point here). It changes when hosting moves (Section 18).

- Cloud name: dfd115bnz
- Images: resource_type=image
- PDFs and docs: resource_type=raw, access_mode=public
- Folder structure: ge_solutions/{project-index}/ (e.g. ge_solutions/001A/)
- Folder deleted after nuclear purge
- If PDFs show 401: check Cloudinary dashboard > Security > Restricted media types. Fix is on Cloudinary side.

---

## 13. GUIDE RULES (HOW THIS GUIDE STAYS TRUE)

**RULE (PERMANENT):** THE CODE IS THE SOURCE OF TRUTH. If this guide and the code disagree, the code wins. Fix the guide to match the code (inside a fix.py), never the other way round.

**RULE (PERMANENT):** No fact, design standard, or process step should exist in more than one place in this guide. If something needs to be referenced elsewhere, point to it by section number instead of restating it. Found duplication is a documentation bug -- fix it immediately, the same way a code bug would be fixed.

**RULE (PERMANENT):** When a later section changes a decision made in an earlier one, never delete or silently rewrite the earlier text. Leave it in place and add a short "SUPERSEDED by Section X.Y" note directly under it, pointing to the new authority. (Plain factual errors -- a wrong address, a wrong font -- are simply corrected.)

**RULE (PERMANENT):** Guide changes ship inside a fix.py, like any other file change. Section 8 only updates its own Phase Tracker (8.10) as work progresses; Section 9's process rules change only when David explicitly approves a new permanent rule.

*(There is no Section 14: the empty "what has been completed" list was removed. Section numbers were kept so other references stay valid.)*

---

## 15. WHAT STILL NEEDS TO BE DONE
- HOSTING + BACKUP MOVE (pending) -- see Section 18. Remind David once per session.
- SECURITY / JWT changes -- done at the END of the build. Until then ignore security work (the app only holds fake data). Before real client data goes in: reset the Neon password and make the GitHub repo private.
- DIRECTOR'S DASHBOARD -- David is still working on it and its code will change. Section 8.12 is only the plan.

---

## 16. KNOWN ISSUES (not blocking)
- Database columns still use the old name `is_backlog`, `backlog_start_date`, `backlog_start_override`, `backlog_months_billed` for what the code and business rules now call "Receivable" (money owed / overdue payment -- see Section 5). This is kept intentionally for migration safety (renaming risks Hibernate creating new empty columns and stranding historical data). Do not confuse this with the NEW "Backlog" business term (work not yet finished) -- same word, different meaning, only at the raw DB column level. Do not rename these columns without a manual, out-of-band migration run directly against the live DB first.
- Some code comments (for example in `Role.java`) point to guide sections "17.7" and "17.10". Those sections no longer exist in this guide. Ignore those pointers -- the code is the truth. (Section 18 is the hosting plan.)

---
## 18. HOSTING + BACKUP PLAN

**STATUS: PENDING -- decided September 2026, NOT started.** (Change to "STATUS: DONE" only when the move is finished and tested.)

### 18.1 What David decided
- Host the WHOLE app on ONE rented server (a "VPS") at **Hetzner**. Location: **Germany or Finland** (US locations have a tiny traffic allowance).
- **Backups: kept at the office for now.** The server makes a backup file every night. David copies it down to the office computer and to an external hard drive. Later, add the Hetzner backup add-on so a copy also exists off-site.
- **Domain: a FREE subdomain for now** (for example a DuckDNS address), NOT a bare IP address like http://95.216.x.x. The padlock (HTTPS) is set up for free. A paid domain (about $10-15 a year) comes later; staff will then switch to the new address.
- JWT / security changes stay at the END of the build, as before.
- David still wants to check other things before the move starts.

### 18.2 Why
- One bill instead of paying Render + Neon + Cloudinary separately. The free tiers sleep or have small limits.
- Expected size: about 4000 projects, each with several uploads. The database is small (a few GB). The UPLOADS are the big part.
- Rewriting the app in another language is NOT recommended. Java + Spring Boot is a good fit for an ERP that handles money. Use an agent/Opus only to speed up the same fix.py work.
- An office server is NOT recommended (Uganda power cuts, no fixed IP). True offline mode is NOT planned.

### 18.3 Estimated cost (check the Hetzner site before paying -- prices rose in April 2026)
- Server, 4 CPU / 8 GB (about CX33): roughly EUR 6.50 a month, plus about EUR 0.50 for the IP address.
- Upload disk: roughly EUR 0.05 per GB a month. 200 GB is about EUR 10.
- Backups: about EUR 4-10 a month.
- **Total: about $20-30 a month.**
- Disk size is a GUESS (80-400 GB, assuming 20-100 MB of uploads per project). Ask David for the real average upload size per project before choosing the disk.

### 18.4 DO THIS FIRST (open items)
- A. **Reset the Neon database password and make the GitHub repo private -- BEFORE real client data goes in.** David chose to leave this for now because the app only holds fake data. render.yaml in the repo contains the password in plain text and the repo is public; the old password stays in git history, so resetting is the only real fix. Then put the new password only in the host's environment settings, never in a file in the repo.
- B. **docker-compose.yml**: on the real server, remove the public database port (5432) and use a strong password from a private .env file, not the one written in the file.
- C. Ask David: is the average upload size per project known?
- D. Ask David: does he have a Visa/Mastercard (or virtual card) that works for international online payments? Hetzner needs one, and new accounts can get extra ID checks.

### 18.5 Setup steps (one time -- do ONE step at a time)
1. Rent the Hetzner server (Germany or Finland).
2. Set up the free subdomain and point it at the server.
3. Install Docker on the server.
4. Copy the project onto it and start it with `docker compose up`. (docker-compose.yml already runs the database, backend and frontend, and already keeps uploads in ./infra/ge_uploads.)
5. Move the data from Neon, and the old uploads from Cloudinary, onto the new server. (Upload code: CloudinaryStorageServiceImpl.java and FileStorageService.java in the land module.) Set VITE_API_BASE_URL to the new address.
6. Turn on HTTPS (free), nightly backups, and an uptime alert (a free monitor such as UptimeRobot).

### 18.6 Routine after going live
- Staff: open the web address in Chrome and work as now.
- Weekly (about 10 min): copy the backup file to the office computer and the external hard drive. Glance at free disk space.
- Monthly (about 20 min): run security updates, pay the bill, check the backup file exists and looks the right size.
- Every few months: TEST a restore, because a backup that was never restored may not work.
- Shipping a fix: run fix.py on his computer as now (it commits and pushes), then run ONE update command on the server (the LLM gives the exact command).
- If the site is down: run the restart command the LLM gave him.

### 18.7 Rules for the LLM when helping with this
- Simple English, outline format, short. Exact copy-paste commands. One step, then wait for him to confirm.
- Do not ask "A or B" unless it is a real decision.
- Never write real passwords into any file in the repo or into this guide.

