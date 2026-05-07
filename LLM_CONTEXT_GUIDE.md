# GE SOLUTIONS ERP — FULL LLM CONTEXT GUIDE
# For any AI assistant continuing work on this project
# Last updated: May 2026 — Priority 1 complete, Priority 2 next

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
  - Understand partial code snippets — needs full files always
- Tools he uses: VS Code, Git Bash terminal (inside VS Code), GitHub, Chrome browser
- Python is installed: use `py` command (not `python`)
- Project folder: `C:/Users/nyenz/Desktop/app/ge solns`

---

## 2. HOW TO COMMUNICATE WITH DAVID

- Use SIMPLE English. No jargon without explanation.
- Use OUTLINE/BULLET format for explanations — not long paragraphs.
- Keep responses SHORT unless doing code.
- When explaining a concept, use analogies or plain words.
- When errors happen, read the log yourself and tell him exactly what is wrong in one sentence.
- Never ask "which would you prefer A or B" — just do everything needed unless there is a real decision required.
- Confirm one step at a time. Do not skip ahead.
- When David shares a screenshot, read it carefully before responding.

---

## 3. HOW TO OUTPUT CODE CHANGES — THE fix.py SYSTEM

RULE: Never ask David to manually copy-paste code into files. Always use fix.py.
RULE: The LLM guide (LLM_CONTEXT_GUIDE.md) is a SEPARATE file from fix.py. Always output them separately.

### Two files David always gets:
1. **fix.py** — writes all changed source code files
2. **LLM_CONTEXT_GUIDE.md** — updated guide for the next AI session

### How fix.py works:
1. You create a Python script called `fix.py`
2. The script writes all changed files automatically when David runs it
3. David downloads the file, replaces his local fix.py, runs `py fix.py`, then pushes

### Fix.py template:
```python
import os

files = {}

files["path/to/file.java"] = \"\"\"\
// file content here
\"\"\"

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("All done.")
```

### Critical rules for fix.py:
- ALWAYS use `encoding="utf-8"` in the open() call — Windows will fail without it
- ALWAYS use `os.makedirs(os.path.dirname(path), exist_ok=True)` before writing
- BUT if writing to the ROOT folder (no subfolder), skip os.makedirs — it fails on empty path
- Run path starts from project root — so paths start with `erp-backend/` or `erp-frontend/`
- After writing, David runs: `git add -A && git commit -m "message" && git push`
- Then watch Render Events tab for green tick

### EFFICIENCY RULE (important):
- If only a SECTION of a file needs to change, use file.read() + str.replace() or file append in fix.py
- Only rewrite full files when the changes are large or spread throughout
- This keeps fix.py files smaller and faster to verify

### Breaking changes into stages:
- For large changes, split into Stage 1, Stage 2, Stage 3
- One fix.py per stage
- Wait for Render green tick between stages
- This prevents long files that get corrupted when pasted

### How David gets the files:
- You call `present_files(["/mnt/user-data/outputs/fix.py", "/mnt/user-data/outputs/LLM_CONTEXT_GUIDE.md"])`
- David downloads both from the chat interface
- For fix.py: open in VS Code, Ctrl+A, Delete, paste new content, Ctrl+S, run `py fix.py`
- For LLM_CONTEXT_GUIDE.md: replace the file in the project root

---

## 4. THE PROJECT — WHAT IT IS

### Name
Golden Seed ERP (code name: NYENZ)

### Purpose
Internal staff accountability tool for GE Solutions — a Ugandan land surveying and title processing company. Staff-only. Not client-facing.

### Core functions
- Store land title records digitally with scanned documents
- Remind staff which clients to call (2x per month, 14-day interval rule)
- Staff log what happened on each call
- Management sees full audit trail of all actions
- Backlog system: clients who stop paying get UGX 50,000/month storage penalty
- Payment recording with full history per plot

### What it is NOT
- Not a receipt generator
- Not a client-facing portal
- Not a billing system
- Not multi-company (yet — future plan is to clone repo per client)

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

### Render Environment Variables (all already set)
- SPRING_DATASOURCE_URL, SPRING_DATASOURCE_USERNAME, SPRING_DATASOURCE_PASSWORD
- CLOUDINARY_CLOUD_NAME (dfd115bnz), CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
- JAVA_OPTS, PORT, JWT_SECRET
- MAIL_USERNAME, MAIL_PASSWORD
- ADMIN_EMAIL, ADMIN_DEFAULT_PASSWORD

---

## 6. PROJECT FOLDER STRUCTURE

```
ge solns/                          <- root, terminal starts here
├── erp-backend/
│   ├── src/main/java/com/gesolutions/erp/
│   │   ├── ErpBackendApplication.java
│   │   ├── config/
│   │   ├── common/
│   │   └── modules/
│   │       ├── auth/
│   │       ├── client/
│   │       └── land/
│   │           ├── model/
│   │           ├── repository/
│   │           ├── service/
│   │           ├── controller/
│   │           └── dto/
│   ├── src/main/resources/application.properties
│   └── pom.xml
├── erp-frontend/
│   ├── src/
│   │   ├── api/axios.js
│   │   ├── context/AuthProvider.jsx
│   │   ├── hooks/useAuth.js
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── layout/
│   │   │   └── ui/
│   │   ├── pages/
│   │   │   ├── Audit/AuditPage.jsx
│   │   │   ├── Dashboard/
│   │   │   ├── DigitalFolder/FolderPage.jsx
│   │   │   ├── Intake/IntakePage.jsx
│   │   │   ├── Ledger/LedgerPage.jsx + LedgerPage.module.css
│   │   │   ├── Payments/PaymentsPage.jsx
│   │   │   ├── Recovery/RecoveryPortal.jsx
│   │   │   ├── Reports/ReportHub.jsx
│   │   │   ├── login/LoginPage.jsx
│   │   │   └── settings/SettingsPage.jsx
│   │   └── services/
│   ├── App.jsx
│   └── vite.config.js
├── LLM_CONTEXT_GUIDE.md           <- THIS FILE (separate from fix.py)
├── fix.py                         <- code change scripts only
├── docker-compose.yml
└── render.yaml
```

---

## 7. HOW THE APP WORKS — LINEAR FLOW

### Step 1: INTAKE
- Staff fills in: Plot ID, land details, owner info
- Fills in: Total cost, initial payment already made
- Chooses: Standard (active) OR Backlog (already owing)
- Only fields: Total Cost | Initial Payment | Arrears (auto) | Backlog toggle
- Attaches documents, adds notes, clicks Commit

### Step 2: LEDGER
- Full list of all plots
- GREEN/YELLOW/RED payment health dots (GREEN=14 days, YELLOW=30 days, RED=over 30 or never)
- Filters: ALL / BACKLOG / LEGACY / UNPAID / CRITICAL
- BACKLOG rows have red tint, BACKLOG tag in status column
- Sort by: Plot ID, Owner, Amount Paid

### Step 3: FOLDER PAGE (per plot)
- All details: plot info, owners, financials, documents, notes, payment history
- Active: Total Cost | Amount Paid | Balance Remaining
- Backlog: Original Debt | Storage Fees Added | Total Now Owed (separated)
- Admin/Root: Record Payment, Move to Backlog, Exit Backlog, Edit, Delete

### Step 4: RECOVERY HUB
- Shows clients who need to be called TODAY
- Grouped by phone number — one card per unique phone
- 2-14 Rule: max 2 calls per month, min 14 days between calls
- Cards flow in 2-column grid on desktop, 1-column on mobile
- ACTION QUEUE and FULL SCHEDULE tabs

### Step 5: PAYMENTS PAGE (Admin/Root only)
- All payment records across all plots
- Summary: Total | Title Payments | Backlog Payments
- Filter by type, search, sort by date

### Step 6: BACKLOG & STORAGE FEES
- UGX 50,000 added every 30 days from backlog start date
- Total owed = Original Debt + Storage Fees - Payments Made
- Staff always sees breakdown — not just a total

### Step 7: AUDIT PAGE (Admin/Root only)
- Every action ever taken in the system

---

## 8. KEY BUSINESS RULES

- **2-14 Rule**: Max 2 calls per client per calendar month. Min 14 days between calls.
- **Recovery grouping**: By unique phone number.
- **Backlog trigger**: 365 days no payment (auto) OR admin manually flags it.
- **Storage fee**: UGX 50,000 every 30 days from backlog START DATE.
- **Payment types**: STANDARD, INITIAL_DEPOSIT, BACKLOG_PARTIAL.
- **Completed plots**: Stay in ledger with COMPLETED/RELEASED status.
- **Phone uniqueness**: Two owners cannot share the same phone number.
- **Admin/Root only**: Record payments, manage backlog, access Payments/Reports/Audit.
- **Cloudinary**: All files stored on Cloudinary.

---

## 9. WHAT HAS BEEN COMPLETED (chronological)

### Phase 1 — Security & Cleanup
- Repo made private, credentials moved to Render env vars

### Phase 2 — Cloudinary Integration
- All file uploads/deletes go through Cloudinary

### Phase 3 — Frontend Fixes
- AuditPage operator dropdown, dashboard activity stream

### Phase 4 — New Demand System (MAJOR OVERHAUL)
- Retired: weekly installment, payment plans, PaymentEngineService
- New: full balance demanded twice a month
- New: PaymentRecord model, BacklogSchedulerService

### Phase 5 — Recovery Portal Rewrite
- Grouped by phone number, two sections (active/backlog)
- Payment health badge computed server-side

### Phase 6 — Folder Page Updates
- Backlog banner, financial breakdown, payment history drawer
- Record Payment, Move to Backlog, Exit Backlog buttons

### Phase 7 — Ledger Updates
- GREEN/YELLOW/RED dots, BACKLOG filter, tagBacklog + rowBacklog CSS

### Phase 8 — Bug Fixes
- isBacklog Boolean vs boolean null crash fixed

### Phase 9 — Payments Page
- New /payments page, PaymentController, sidebar link

### Priority 1 — Styling & Intake Cleanup (COMPLETE ✓)
- RecoveryPortal.module.css: 2-column grid, contrast fixes, mobile responsive
- PaymentsPage.module.css: filter button text visibility fixed
- IntakePage.jsx: removed Payment Plan dropdown, Weekly Installment, Operational Mode toggle
- IntakePage.jsx: kept Total Cost, Initial Payment, Arrears (auto), single Backlog Status toggle
- LedgerPage.module.css: added missing tagBacklog and rowBacklog classes (appended via fix.py)
- LLM_CONTEXT_GUIDE.md: now a permanent separate file in project root

---

## 10. CURRENT STATUS (as of May 2026)

- Priority 1: COMPLETE AND DEPLOYED ✓
- LLM_CONTEXT_GUIDE.md: now in project root ✓
- Next: Priority 2 — Reports overhaul (waiting for David to confirm concerns first)

---

## 11. WHAT STILL NEEDS TO BE DONE (in priority order)

### Priority 2 — Reports overhaul
1. Add backlog report (all backlog plots with storage fees breakdown)
2. Add completed titles report (released plots)
3. Add payment history report (all payments, date range filter)
4. Add storage fees report (total fees per plot)
5. Add monthly collection report (how much collected each month)

### Priority 3 — Mobile audit + small fixes
1. Full mobile responsiveness check on all pages
2. Completed clients count on dashboard
3. Print layout cleanup
4. Phone uniqueness frontend validation (clear error if phone already exists)
5. Release button should warn if no documents uploaded

### Language simplification (can do alongside any priority)
- "Master Hardware Override" -> "Edit"
- "Nuclear Purge" -> "Delete"
- "Intel" -> "Notes"
- "Vault" -> "Documents"
- "Recovery Sync" -> "Call Logged"
- "Asset Intake" -> "New Plot"
- "Forensic Stream" -> "Recent Activity"

### Future (not started)
- Multi-company: clone repo per client company
- Notification model (exists in code but never used)
- Rate limiting on login endpoint

---

## 12. KNOWN ISSUES (not blocking)

- WebConfig.java still has old local file serving reference — harmless since Cloudinary is used
- Notification model exists but never used
- No rate limiting on login
- Release button does not check for uploaded documents first
- `payment_schedules` table still exists in DB — no longer used (harmless)
- App name inconsistency: "NYENZ ERP" vs "Golden Seed" in different places

---

## 13. DEPLOYMENT PROCESS

Every change follows this exact flow:
1. Create fix.py AND updated LLM_CONTEXT_GUIDE.md -> `present_files` both -> David downloads both
2. David replaces local fix.py -> `py fix.py` -> check "All done." output
3. David replaces local LLM_CONTEXT_GUIDE.md with downloaded version
4. `git add -A && git commit -m "message" && git push`
5. Go to Render -> ge-solutions-api -> Events tab (backend) OR golden-seed -> Events tab (frontend)
6. Wait for green tick (5-10 minutes on free tier)
7. Test in browser at golden-seed.onrender.com
8. If red (failed): click "deploy logs" -> read error -> fix -> repeat

---

## 14. COMMON ERRORS AND FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `Can not set boolean field isBacklog to null` | DB rows have NULL, Java primitive boolean can't hold null | Use `Boolean` (capital B) not `boolean` |
| `No property 'isActive' found for type 'Client'` | Client model has no isActive field | Use `@Query` instead of method name query |
| `column X contains null values` | New NOT NULL column added to table with existing rows | Remove `nullable = false` from @Column |
| `UnicodeEncodeError` in fix.py | Windows default encoding | Always use `encoding="utf-8"` in open() |
| `nothing added to commit` | Files already match what's in git | Force add specific files |
| 500 on /dashboard/summary | Backend crash — check Render Logs tab | Read Caused by: line at bottom of log |
| CSS class not found | Class used in JSX but not defined in .module.css | Add the missing class to the CSS file |
| `FileNotFoundError: [WinError 3]` in fix.py | os.makedirs called with empty string (root-level file) | Skip os.makedirs for root-level files |

---

## 15. CLOUDINARY DETAILS

- Cloud name: dfd115bnz
- Images: resource_type=image
- PDFs and docs: resource_type=raw, access_mode=public
- Folder structure: ge_solutions/{plot-uuid}/
- Folder deleted after nuclear purge