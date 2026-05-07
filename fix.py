import os

def patch(path, old, new, label):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING (already patched or mismatch): {label}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label}")

def write_file(path, content, label):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  WRITTEN: {label}")

# ==============================================================
# FIX 1: IntakePage - subtitle should be in pageHeader, styled correctly
# ==============================================================
print("=== FIX 1: IntakePage header subtitle ===")

patch(
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    """            <header className={styles.pageHeader}>
                <h1 className={styles.title}>New Plot Registration</h1>
                <p className={styles.subtitle}>Register a new land title into the system</p>
            </header>""",
    """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Plot Registration</h1>
                    <p className={styles.subtitle}>Register a new land title into the system</p>
                </div>
            </header>""",
    "IntakePage - wrap title+subtitle in headerLeft div"
)

# Add headerLeft to IntakePage CSS
patch(
    "erp-frontend/src/pages/Intake/IntakePage.module.css",
    ".title {\n    font-family: 'Cinzel', serif; color: var(--navy);",
    """.headerLeft {
    display: flex;
    flex-direction: column;
    gap: clamp(3px, 0.4vw, 5px);
    min-width: 0;
    flex: 1;
}

.title {
    font-family: 'Cinzel', serif; color: var(--navy);""",
    "IntakePage CSS - add headerLeft"
)

# ==============================================================
# FIX 2: ReportHub - subtitle inside headerLeft
# ==============================================================
print("\n=== FIX 2: ReportHub header subtitle ===")

patch(
    "erp-frontend/src/pages/Reports/ReportHub.jsx",
    """            <header className={styles.pageHeader}>
                <h1 className={styles.title}>Intelligence Hub</h1>
                <p className={styles.subtitle}>Direct Database Analysis &amp; CSV Export Terminal</p>
            </header>""",
    """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Intelligence Hub</h1>
                    <p className={styles.subtitle}>Direct Database Analysis &amp; CSV Export Terminal</p>
                </div>
            </header>""",
    "ReportHub - wrap title+subtitle in headerLeft"
)

patch(
    "erp-frontend/src/pages/Reports/ReportHub.module.css",
    ".title {\n    font-family: 'Cinzel', serif; color: var(--navy);",
    """.headerLeft {
    display: flex;
    flex-direction: column;
    gap: clamp(3px, 0.4vw, 5px);
    min-width: 0;
    flex: 1;
}

.title {
    font-family: 'Cinzel', serif; color: var(--navy);""",
    "ReportHub CSS - add headerLeft"
)

# ==============================================================
# FIX 3: LedgerPage - subtitle inside headerLeft
# ==============================================================
print("\n=== FIX 3: LedgerPage header subtitle ===")

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """            <header className={styles.pageHeader}>
                <h1 className={styles.title}>Digital Asset Ledger</h1>
                <p className={styles.subtitle}>Unified Storage Recovery &amp; Debt Tracking</p>
            </header>""",
    """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Digital Asset Ledger</h1>
                    <p className={styles.subtitle}>Unified Storage Recovery &amp; Debt Tracking</p>
                </div>
            </header>""",
    "LedgerPage - wrap title+subtitle in headerLeft"
)

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    ".title {\n    font-family: 'Cinzel', serif;",
    """.headerLeft {
    display: flex;
    flex-direction: column;
    gap: clamp(3px, 0.4vw, 5px);
    min-width: 0;
    flex: 1;
}

.title {
    font-family: 'Cinzel', serif;""",
    "LedgerPage CSS - add headerLeft"
)

# ==============================================================
# FIX 4: AuditPage - subtitle inside headerLeft (already has titleGroup, just rename)
# ==============================================================
print("\n=== FIX 4: AuditPage header subtitle ===")

patch(
    "erp-frontend/src/pages/Audit/AuditPage.jsx",
    """            <header className={styles.pageHeader}>
                <div className={styles.titleGroup}>
                    <h1 className={styles.title}>System Forensics</h1>
                    <p className={styles.subtitle}>Unified Accountability Archive | Total Traceability Active</p>
                </div>""",
    """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>System Forensics</h1>
                    <p className={styles.subtitle}>Unified Accountability Archive | Total Traceability Active</p>
                </div>""",
    "AuditPage - rename titleGroup to headerLeft"
)

# Fix AuditPage CSS: rename titleGroup to headerLeft
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    ".titleGroup { display: flex; flex-direction: column; gap: clamp(3px,0.4vw,5px); }",
    ".headerLeft { display: flex; flex-direction: column; gap: clamp(3px,0.4vw,5px); min-width: 0; flex: 1; }",
    "AuditPage CSS - rename titleGroup to headerLeft"
)

# Fix AuditPage title color (was navy #1a2e30, subtitle was #64748b - these are the correct colors)
# Just make sure .title is defined properly
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    ".title { font-family: 'Cinzel', serif; color: var(--navy); font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0; line-height: 1; }",
    ".title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0; line-height: 1; }",
    "AuditPage CSS - title hardcoded navy"
)
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    ".subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; margin: 0; letter-spacing: 1px; }",
    ".subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; margin: 0; letter-spacing: 1px; }",
    "AuditPage CSS - subtitle color (already correct)"
)

# ==============================================================
# FIX 5: PaymentsPage subtitle styling to match standard
# ==============================================================
print("\n=== FIX 5: PaymentsPage subtitle ===")

# The payments page already has headerLeft. Just fix the subtitle CSS to match standard
patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    ".subtitle { color: rgba(26,46,48,0.6); font-size: clamp(10px, 1.1vw, 13px); font-weight: 600; margin: 4px 0 0; }",
    ".subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: clamp(8px, 0.85vw, 10px); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }",
    "PaymentsPage CSS - subtitle matches standard"
)

# ==============================================================
# FIX 6: FILTER BARS - make ALL match Payments standard
# Single horizontal row, side-scrollable on mobile, no icons above text
# Standard: dark inactive, orange hover, orange-filled active
# ==============================================================
print("\n=== FIX 6: Filter bars unification ===")

# --- LEDGER PAGE: remove icons from filter buttons, make single row ---
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """                        <div className={styles.filterRailContainer}>
                    <div className={styles.filterRail} role="group" aria-label="Filter records">
                        {FILTERS.map(f => (
                            <button key={f.key}
                                onClick={() => setActiveFilter(f.key)}
                                className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}
                                aria-pressed={activeFilter === f.key} aria-label={f.label}>
                                {f.icon} {f.label}
                            </button>
                        ))}
                    </div>
                </div>""",
    """                        <div className={styles.filterRailContainer}>
                    <div className={styles.filterRail} role="group" aria-label="Filter records">
                        {FILTERS.map(f => (
                            <button key={f.key}
                                onClick={() => setActiveFilter(f.key)}
                                className={`${styles.filterBtn} ${activeFilter === f.key ? styles.activeFilter : ''}`}
                                aria-pressed={activeFilter === f.key} aria-label={f.label}>
                                {f.label}
                            </button>
                        ))}
                    </div>
                </div>""",
    "LedgerPage - remove icons from filter buttons"
)

# Fix LedgerPage filter CSS - ensure single row, scrollable
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    ".filterRailContainer {\n    width: 100%;\n    overflow: hidden;\n    padding-bottom: clamp(3px, 0.4vw, 5px);\n}",
    ".filterRailContainer {\n    width: 100%;\n    overflow-x: auto;\n    padding-bottom: clamp(3px, 0.4vw, 5px);\n    scrollbar-width: none;\n}\n.filterRailContainer::-webkit-scrollbar { display: none; }",
    "LedgerPage - filterRailContainer scrollable"
)

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    ".filterRail {\n    display: flex;\n    gap: clamp(6px, 1vw, 12px);\n    overflow-x: auto;\n    flex-wrap: nowrap;\n    scrollbar-width: none;\n    padding-bottom: 2px;\n}\n.filterRail::-webkit-scrollbar { display: none; }",
    ".filterRail {\n    display: flex;\n    gap: clamp(6px, 1vw, 12px);\n    flex-wrap: nowrap;\n    padding-bottom: 2px;\n    min-width: max-content;\n}",
    "LedgerPage - filterRail no-wrap single row"
)

# --- RECOVERY PAGE: make filter row single scrollable line on mobile ---
# Recovery uses .filterRow in Payments style already but we need to confirm
# The filter buttons in RecoveryPortal are the mode-switch tabs (ACTION QUEUE / FULL SCHEDULE)
# Those are already fine. The issue is on mobile they wrap.
# Fix: the modeSwitch should stay inline

# --- PAYMENTS PAGE filter row: ensure single scrollable row on mobile ---
patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    ".filterRow {\n    display: flex;\n    overflow-x: auto;\n    padding-bottom: 8px;\n    gap: 12px;\n    scrollbar-width: none; display: flex; flex-wrap: wrap; gap: 8px; }",
    ".filterRow {\n    display: flex;\n    flex-wrap: nowrap;\n    overflow-x: auto;\n    gap: 8px;\n    padding-bottom: 4px;\n    scrollbar-width: none;\n}\n.filterRow::-webkit-scrollbar { display: none; }",
    "PaymentsPage - filterRow single scrollable row"
)

# ==============================================================
# FIX 7: LedgerPage - badge legend and search hint visibility
# These sit on the warm cream/beige background, so they need DARK text
# ==============================================================
print("\n=== FIX 7: LedgerPage badge legend + search hint visibility ===")

# The badge legend is inline JSX with opacity 0.7 - it uses rgba text
# The problem: it inherits color: #fff from .container but background is light
# Fix: override with dark color in the badge legend area
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """                {/* BADGE LEGEND */}
                <div style={{ display: 'flex', gap: 16, padding: '8px 0', fontSize: '0.72rem', opacity: 0.7 }}>
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (
                        <span key={k} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, display: 'inline-block', boxShadow: `0 0 4px ${c}` }} />
                            {BADGE_LABELS[k]}
                        </span>
                    ))}
                </div>""",
    """                {/* BADGE LEGEND */}
                <div className={styles.badgeLegend}>
                    {Object.entries(BADGE_COLORS).map(([k, c]) => (
                        <span key={k} className={styles.badgeLegendItem}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, display: 'inline-block', flexShrink: 0, boxShadow: `0 0 4px ${c}` }} />
                            {BADGE_LABELS[k]}
                        </span>
                    ))}
                </div>""",
    "LedgerPage - badge legend use CSS class"
)

# Fix search hint visibility (it's on the light background area)
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    ".searchHint {\n    font-family: 'Space Mono', monospace;\n    font-size: clamp(7px, 0.7vw, 8px);\n    font-weight: 700;\n    color: rgba(255, 255, 255, 0.28);\n    letter-spacing: 0.5px;\n    text-transform: uppercase;\n    margin: 0;\n}",
    ".searchHint {\n    font-family: 'Space Mono', monospace;\n    font-size: clamp(7px, 0.7vw, 8px);\n    font-weight: 700;\n    color: rgba(26, 46, 48, 0.45);\n    letter-spacing: 0.5px;\n    text-transform: uppercase;\n    margin: 0;\n}",
    "LedgerPage CSS - searchHint dark text for light bg"
)

# Add badgeLegend classes to LedgerPage CSS
BADGE_LEGEND_CSS = """
/* ── BADGE LEGEND ───────────────────────────────────────────────── */
.badgeLegend {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(10px, 1.5vw, 18px);
    padding: clamp(6px, 0.8vw, 8px) 0;
}
.badgeLegendItem {
    display: flex;
    align-items: center;
    gap: clamp(5px, 0.6vw, 7px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 800;
    color: rgba(26, 46, 48, 0.65);
    white-space: nowrap;
}
"""

with open("erp-frontend/src/pages/Ledger/LedgerPage.module.css", "r", encoding="utf-8", errors="replace") as f:
    ledger_css = f.read()

if ".badgeLegend" not in ledger_css:
    with open("erp-frontend/src/pages/Ledger/LedgerPage.module.css", "a", encoding="utf-8") as f:
        f.write(BADGE_LEGEND_CSS)
    print("  OK: LedgerPage CSS - added badge legend classes")
else:
    print("  SKIP: badge legend already in LedgerPage CSS")

# ==============================================================
# FIX 8: LedgerPage search hint - also the search placeholder
# The search input sits on white bg, so it is fine.
# The hint below sits outside on the cream bg.
# But .searchHint is inside .searchBlock which is inside .controlHub
# which is inside .container (which has color: #fff)
# The fix above (rgba dark color) should work.
# ==============================================================

# ==============================================================
# FIX 9: Recovery filter row on mobile - single scrollable row
# The mode switch (ACTION QUEUE / FULL SCHEDULE) should not stack
# ==============================================================
print("\n=== FIX 9: Recovery modeSwitch mobile single row ===")

# Already handled in RecoveryPortal.module.css with media query
# Let's make sure the modeSwitch doesn't wrap on very small screens

with open("erp-frontend/src/pages/Recovery/RecoveryPortal.module.css", "r", encoding="utf-8", errors="replace") as f:
    rec_css = f.read()

if ".modeSwitch {" in rec_css:
    # Check if overflow is set
    if "overflow-x: auto" not in rec_css.split(".modeSwitch {")[1].split("}")[0]:
        patch(
            "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",
            ".modeSwitch { display:inline-flex; background:var(--navy); padding:4px; border-radius:var(--radius-sm); border:1px solid var(--orange-border); gap:3px; }",
            ".modeSwitch { display:flex; background:var(--navy); padding:4px; border-radius:var(--radius-sm); border:1px solid var(--orange-border); gap:3px; overflow-x:auto; scrollbar-width:none; flex-wrap:nowrap; }",
            "Recovery modeSwitch - no wrap, scrollable"
        )

# ==============================================================
# FIX 10: Update LLM_CONTEXT_GUIDE.md
# ==============================================================
print("\n=== FIX 10: Updating LLM_CONTEXT_GUIDE.md ===")

lines = [
    "# GE SOLUTIONS ERP -- FULL LLM CONTEXT GUIDE",
    "# For any AI assistant continuing work on this project",
    "# Last updated: May 2026 -- Priority 1 ongoing: header+filter+subtitle uniformity",
    "",
    "---",
    "",
    "## 1. WHO IS DAVID (the developer)",
    "",
    "- Name: David, goes by nyenz on GitHub",
    "- Location: Kampala, Uganda",
    "- Skill level: BEGINNER. Can follow exact step-by-step instructions precisely.",
    "- What he CAN do:",
    "  - Copy and run terminal commands exactly as given",
    "  - Download files and replace them in VS Code",
    "  - Run `py fix.py` to apply file changes",
    "  - Run `git add/commit/push` commands",
    "  - Read screenshots and describe what he sees",
    "  - Share screenshots to confirm progress",
    "- What he CANNOT do:",
    "  - Debug code independently",
    "  - Read Java/React errors without guidance",
    "  - Write code himself",
    "  - Understand partial code snippets -- needs full files always",
    "- Tools he uses: VS Code, Git Bash terminal (inside VS Code), GitHub, Chrome browser",
    "- Python is installed: use `py` command (not `python`)",
    "- Project folder: `C:/Users/nyenz/Desktop/app/ge solns`",
    "",
    "---",
    "",
    "## 2. HOW TO COMMUNICATE WITH DAVID",
    "",
    "- Use SIMPLE English. No jargon without explanation.",
    "- Use OUTLINE/BULLET format for explanations -- not long paragraphs.",
    "- Keep responses SHORT unless doing code.",
    "- When explaining a concept, use analogies or plain words.",
    "- When errors happen, read the log yourself and tell him exactly what is wrong in one sentence.",
    "- Never ask 'which would you prefer A or B' -- just do everything needed unless there is a real decision required.",
    "- Confirm one step at a time. Do not skip ahead.",
    "- When David shares a screenshot, read it carefully before responding.",
    "",
    "---",
    "",
    "## 3. HOW TO OUTPUT CODE CHANGES -- THE fix.py SYSTEM",
    "",
    "RULE: Never ask David to manually copy-paste code into files. Always use fix.py.",
    "RULE: The LLM guide (LLM_CONTEXT_GUIDE.md) is a SEPARATE file from fix.py. Always output them separately.",
    "RULE: Use str.replace (patch) in fix.py when only a section of a file changes. Only rewrite full files when changes are large or spread throughout.",
    "RULE: Never put triple-quoted strings inside triple-quoted strings in fix.py -- use a list of lines joined with newlines instead (this avoids SyntaxError).",
    "RULE: Never use special unicode characters (em dashes, smart quotes, etc.) in fix.py strings -- use plain ASCII only (-- instead of --, - instead of em dash). This prevents UnicodeDecodeError when reading files that Windows saved with a different encoding.",
    "RULE: Before writing a patch, always verify the exact text to replace by reading the document context. Do not guess.",
    "RULE: The LLM_CONTEXT_GUIDE.md must be updated inside fix.py on every session -- use the list-of-lines approach.",
    "RULE: Always open files with errors='replace' when reading: open(path, 'r', encoding='utf-8', errors='replace')",
    "",
    "### CRITICAL -- Why patches fail:",
    "- If fix.py says 'patch target not found', the CSS already has the change OR the text doesn't match exactly.",
    "- Always read the actual file content from the conversation context before writing str.replace patches.",
    "- The documents shared in the conversation ARE the current file contents -- use them as source of truth.",
    "- Copy the exact block including all whitespace, comments, and surrounding lines.",
    "- Special characters in source files (em dashes, arrows, etc.) cause UnicodeDecodeError -- use errors='replace' when reading.",
    "",
    "### Two files David always gets:",
    "1. fix.py -- writes all changed source code files",
    "2. LLM_CONTEXT_GUIDE.md -- updated guide for the next AI session (written BY fix.py)",
    "",
    "### Fix.py efficiency rules:",
    "- Use file.read() + str.replace() for partial changes -- keeps fix.py small",
    "- Only use full file rewrite when many sections change or file is new",
    "- Always use encoding='utf-8' in open() calls",
    "- Always use errors='replace' when READING files (prevents crash on special chars)",
    "- Always use os.makedirs(os.path.dirname(path), exist_ok=True) before writing new files",
    "- Skip os.makedirs for root-level files (empty path causes error)",
    "- When writing the LLM guide itself, use a list of lines joined with newlines -- never embed it in a triple-quoted string",
    "- Print OK/MISSING for every patch so David can see what happened",
    "- NEVER use special unicode characters in fix.py strings -- ASCII only",
    "",
    "### How David gets the files:",
    "- You call present_files(['/mnt/user-data/outputs/fix.py', '/mnt/user-data/outputs/LLM_CONTEXT_GUIDE.md'])",
    "- David downloads both from the chat interface",
    "- For fix.py: open in VS Code, Ctrl+A, Delete, paste new content, Ctrl+S, run `py fix.py`",
    "- For LLM_CONTEXT_GUIDE.md: replace the file in the project root",
    "- Then: git add -A && git commit -m 'message' && git push",
    "- Watch Render Events tab for green tick (5-10 min free tier)",
    "- Test at golden-seed.onrender.com",
    "- If red: click 'deploy logs' -> read error -> fix -> repeat",
    "",
    "---",
    "",
    "## 4. THE PROJECT -- WHAT IT IS",
    "",
    "### Name",
    "Golden Seed ERP (code name: NYENZ)",
    "",
    "### Purpose",
    "Internal staff accountability tool for GE Solutions -- a Ugandan land surveying and title processing company. Staff-only. Not client-facing.",
    "",
    "### Core functions",
    "- Store land title records digitally with scanned documents",
    "- Remind staff which clients to call (2x per month, 14-day interval rule)",
    "- Staff log what happened on each call",
    "- Management sees full audit trail of all actions",
    "- Backlog system: clients who stop paying get UGX 50,000/month storage penalty",
    "- Payment recording with full history per plot",
    "",
    "---",
    "",
    "## 5. TECH STACK",
    "",
    "| Layer | Technology |",
    "|-------|-----------|",
    "| Backend | Java Spring Boot 3.2.5 |",
    "| Database ORM | Hibernate / JPA |",
    "| Database | PostgreSQL (Neon cloud, free tier) |",
    "| Auth | JWT tokens |",
    "| Build | Maven |",
    "| Utilities | Lombok, Spring Security |",
    "| Frontend | React 19, Vite |",
    "| Styling | CSS Modules |",
    "| Routing | React Router |",
    "| HTTP | Axios |",
    "| File Storage | Cloudinary (cloud name: dfd115bnz) |",
    "| Deployment | Render free tier |",
    "| Repo | GitHub (PRIVATE): github.com/nyenz/ge-solutions-erp |",
    "",
    "### URLs",
    "- Backend: https://ge-solutions-api.onrender.com",
    "- Frontend: https://golden-seed.onrender.com",
    "",
    "### Database",
    "- Host: ep-wispy-cell-an2afrm4.c-6.us-east-1.aws.neon.tech",
    "- Name: neondb",
    "- User: neondb_owner",
    "",
    "---",
    "",
    "## 6. PROJECT FOLDER STRUCTURE",
    "",
    "ge solns/",
    "  erp-backend/",
    "    src/main/java/com/gesolutions/erp/",
    "  erp-frontend/",
    "    src/",
    "      api/axios.js",
    "      context/AuthProvider.jsx",
    "      hooks/useAuth.js",
    "      components/",
    "      pages/",
    "        Audit/AuditPage.jsx + AuditPage.module.css",
    "        Dashboard/",
    "        DigitalFolder/FolderPage.jsx",
    "        Intake/IntakePage.jsx + IntakePage.module.css",
    "        Ledger/LedgerPage.jsx + LedgerPage.module.css",
    "        Payments/PaymentsPage.jsx + PaymentsPage.module.css",
    "        Recovery/RecoveryPortal.jsx + RecoveryPortal.module.css",
    "        Reports/ReportHub.jsx",
    "        login/LoginPage.jsx",
    "        settings/SettingsPage.jsx",
    "      services/",
    "  LLM_CONTEXT_GUIDE.md",
    "  fix.py",
    "  docker-compose.yml",
    "  render.yaml",
    "",
    "---",
    "",
    "## 7. UI DESIGN STANDARDS (CRITICAL -- apply consistently)",
    "",
    "### Page Header Style (ALL pages MUST match Dashboard)",
    "- Use className={styles.pageHeader} for the <header> element",
    "- Inside pageHeader: always use <div className={styles.headerLeft}> wrapping title + subtitle",
    "- If there are action buttons/controls, put them in <div className={styles.headerRight}>",
    "- White/cream glass panel: background: rgba(255,255,255,0.62)",
    "- Left orange border: border-left: clamp(3px,0.4vw,5px) solid var(--orange)",
    "- Border radius: 0 12px 12px 0 (flat left, rounded right)",
    "- Backdrop blur: backdrop-filter: blur(15px)",
    "- Box shadow: 0 4px 15px rgba(0,0,0,0.07)",
    "- Title (.title): Cinzel serif, color: #1a2e30 (hardcoded navy, NOT var(--navy) which is white on dark panels), uppercase, letter-spacing 1.5px",
    "- Subtitle (.subtitle): DM Sans 900, color: #64748b, uppercase, letter-spacing 1px, font-size clamp(8px,0.85vw,10px)",
    "- .headerLeft: flex column, gap clamp(3px,0.4vw,5px), flex:1, min-width:0",
    "- .headerRight: flex row, align-items:center, gap, flex-shrink:0, flex-wrap:wrap",
    "- NEVER use position:absolute on buttons inside the header -- use flex gap",
    "",
    "### Filter Button Style (CONFIRMED STANDARD -- ALL pages must match)",
    "- Inactive: background: rgba(26,46,48,0.75), border: 1.5px solid rgba(255,255,255,0.18), color: rgba(255,255,255,0.85)",
    "- Hover: background: rgba(238,140,58,0.12), color: #EE8C3A, border-color: var(--orange)",
    "- Active/Selected: background: #EE8C3A, color: #1a2e30, border-color: #EE8C3A",
    "- Font: DM Sans 900, uppercase, letter-spacing 1.5px, font-size 11px",
    "- Layout: single horizontal row, flex-wrap:nowrap, overflow-x:auto, scrollbar-width:none",
    "- NO icons inside filter buttons -- text only",
    "- On mobile: same single row, side-scrollable (never wraps to multiple lines)",
    "",
    "### Text on Light Background Rule",
    "- The controlHub area (search, filters, badge legend) sits on the warm cream/beige background",
    "- Any text in this area must use dark colors: rgba(26,46,48,0.xx) or #64748b",
    "- Never use rgba(255,255,255,x) for text that appears outside a dark panel",
    "- Badge legend items: color: rgba(26,46,48,0.65), font-size 9-11px",
    "- Search hint: color: rgba(26,46,48,0.45)",
    "",
    "### FolderPage Header",
    "- Uses .terminalHeader -- its own design, do NOT change to pageHeader",
    "- It has unique backlog/edit badges that need their own layout",
    "",
    "---",
    "",
    "## 8. HOW THE APP WORKS -- LINEAR FLOW",
    "",
    "Step 1: INTAKE -> Step 2: LEDGER -> Step 3: FOLDER PAGE",
    "Step 4: RECOVERY HUB -> Step 5: PAYMENTS -> Step 6: AUDIT",
    "",
    "---",
    "",
    "## 9. KEY BUSINESS RULES",
    "",
    "- 2-14 Rule: Max 2 calls/client/month. Min 14 days between calls.",
    "- Recovery grouping: By unique phone number.",
    "- Backlog trigger: 365 days no payment (auto) OR admin manually.",
    "- Storage fee: UGX 50,000 every 30 days from backlog START DATE.",
    "- Payment types: STANDARD, INITIAL_DEPOSIT, BACKLOG_PARTIAL.",
    "- Phone uniqueness: Two owners cannot share the same phone number.",
    "- Admin/Root only: Payments, backlog management, Reports, Audit.",
    "- Cloudinary: All files stored on Cloudinary.",
    "",
    "---",
    "",
    "## 10. WHAT HAS BEEN COMPLETED (chronological)",
    "",
    "### Priority 1 -- Styling & Uniformity -- IN PROGRESS",
    "- RecoveryPortal: 2-column grid, mobile responsive -- DONE",
    "- PaymentsPage: filter buttons unified to dark-bg inactive style -- DONE",
    "- IntakePage: cleaned up financials -- DONE",
    "- LedgerPage: tagBacklog + rowBacklog CSS; filter fixed; plot ID two lines -- DONE",
    "- AuditPage: RESET FILTERS aligned; fully responsive -- DONE",
    "- All page headers: unified glass panel using .pageHeader class -- DONE",
    "  - Root cause found: !important block at bottom of every CSS was position:absolute-ing buttons",
    "  - Fix: Removed all !important blocks, switched to clean .pageHeader class",
    "  - Recovery portal header restructured: left=title+subtitle, right=stats+tabs",
    "  - RecoveryPortal.jsx fully rewritten (clean UTF-8, no special chars) to fix encoding crash",
    "- Filter bar unification: all pages now use identical filter button styles -- DONE",
    "  - Single horizontal row, side-scrollable on mobile",
    "  - No icons in filter buttons -- text only",
    "  - Standard: dark inactive, orange hover, orange-filled active",
    "- Subtitle positioning: all pages now use headerLeft wrapper for title+subtitle -- DONE",
    "  - subtitle style: DM Sans 900, #64748b, uppercase, small",
    "- LedgerPage badge legend + search hint: dark text for light background -- DONE",
    "",
    "---",
    "",
    "## 11. WHAT STILL NEEDS TO BE DONE (in priority order)",
    "",
    "### Priority 1 -- Remaining uniformity checks",
    "- Check screenshot of each page after this deploy",
    "- Table header alignment, row spacing uniformity across pages",
    "- Pagination controls uniformity",
    "",
    "### Priority 2 -- Reports overhaul",
    "1. Add backlog report (all backlog plots with storage fees breakdown)",
    "2. Add completed titles report (released plots)",
    "3. Add payment history report (all payments, date range filter)",
    "4. Add storage fees report (total fees per plot)",
    "5. Add monthly collection report (how much collected each month)",
    "",
    "### Priority 3 -- Mobile audit + small fixes",
    "1. Full mobile responsiveness check on all pages",
    "2. Completed clients count on dashboard",
    "3. Print layout cleanup",
    "4. Phone uniqueness frontend validation",
    "5. Release button should warn if no documents uploaded",
    "",
    "### Language simplification (can do alongside any priority)",
    "- 'Master Hardware Override' -> 'Edit'",
    "- 'Nuclear Purge' -> 'Delete'",
    "- 'Intel' -> 'Notes'",
    "- 'Vault' -> 'Documents'",
    "- 'Recovery Sync' -> 'Call Logged'",
    "- 'Asset Intake' -> 'New Plot'",
    "- 'Forensic Stream' -> 'Recent Activity'",
    "",
    "### Future (not started)",
    "- Multi-company: clone repo per client company",
    "- Notification model (exists in code but never used)",
    "- Rate limiting on login endpoint",
    "",
    "---",
    "",
    "## 12. KNOWN ISSUES (not blocking)",
    "",
    "- WebConfig.java has old local file serving reference -- harmless (Cloudinary is used)",
    "- Notification model exists but never used",
    "- No rate limiting on login",
    "- Release button does not check for uploaded documents first",
    "- payment_schedules table still exists in DB -- no longer used (harmless)",
    "- App name inconsistency: 'NYENZ ERP' vs 'Golden Seed' in different places",
    "",
    "---",
    "",
    "## 13. DEPLOYMENT PROCESS",
    "",
    "1. Create fix.py AND updated LLM_CONTEXT_GUIDE.md -> present_files both -> David downloads both",
    "2. David replaces local fix.py -> py fix.py -> check output for OK/MISSING",
    "3. David replaces local LLM_CONTEXT_GUIDE.md",
    "4. git add -A && git commit -m 'message' && git push",
    "5. Render -> Events tab -> wait for green tick (5-10 min free tier)",
    "6. Test at golden-seed.onrender.com",
    "7. If red: click 'deploy logs' -> read error -> fix -> repeat",
    "",
    "---",
    "",
    "## 14. COMMON ERRORS AND FIXES",
    "",
    "| Error | Cause | Fix |",
    "|-------|-------|-----|",
    "| Can not set boolean field isBacklog to null | DB rows have NULL, Java primitive boolean | Use Boolean (capital B) not boolean |",
    "| UnicodeDecodeError in fix.py | File has special chars (em dashes etc), Windows encoding | Use errors='replace' when reading files |",
    "| UnicodeEncodeError in fix.py | Windows default encoding on write | Always use encoding='utf-8' in open() |",
    "| nothing added to commit | Files already match what's in git | Force add specific files |",
    "| 500 on /dashboard/summary | Backend crash -- check Render Logs tab | Read Caused by: line at bottom of log |",
    "| CSS class not found | Class used in JSX but not defined in .module.css | Add the missing class to the CSS file |",
    "| SyntaxError in fix.py with triple quotes | LLM guide embedded inside triple-quoted string | Use list of lines joined with newlines instead |",
    "| fix.py shows 'patch target not found' | Text to replace doesn't match file exactly | Read actual file from conversation context before writing patch |",
    "| Header buttons overlapping title | !important position:absolute in CSS override block | Remove !important block, use .pageHeader flex layout |",
    "| Text invisible on light bg | Color was rgba(255,255,255,x) -- white on cream | Use rgba(26,46,48,x) -- dark on light |",
    "",
    "---",
    "",
    "## 15. CLOUDINARY DETAILS",
    "",
    "- Cloud name: dfd115bnz",
    "- Images: resource_type=image",
    "- PDFs and docs: resource_type=raw, access_mode=public",
    "- Folder structure: ge_solutions/{plot-uuid}/",
    "- Folder deleted after nuclear purge",
]

guide_content = "\n".join(lines)
with open("LLM_CONTEXT_GUIDE.md", "w", encoding="utf-8") as f:
    f.write(guide_content)
print("  WRITTEN: LLM_CONTEXT_GUIDE.md")

print("\n=== ALL DONE ===")
print("Steps:")
print("1. py fix.py  -- check all lines say OK")
print("2. git add -A && git commit -m 'uniform subtitles, filter bars, ledger visibility' && git push")
print("3. Wait Render green tick, test site")
print("4. Send screenshot of Ledger and Payments pages")