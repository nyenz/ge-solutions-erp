import os

def patch(path, old, new, label):
    with open(path, "r", encoding="utf-8") as f:
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

# ══════════════════════════════════════════════════════════════════
# The problem:
# 1. Recovery page header JSX is disorganised — stat boxes + buttons
#    overlapping because they're all inside one flat div with no
#    proper layout structure.
# 2. The !important overrides at the bottom of every CSS file for
#    .header are fighting with the page-specific layout, creating
#    conflicts (absolute-positioned buttons covering content, etc.)
# 3. All pages need a UNIFIED header: glass panel left-bordered,
#    title (Cinzel navy), subtitle (DM Sans grey), with any
#    action items ALONGSIDE not overlapping.
#
# SOLUTION:
# A) Create a shared CSS snippet / class pattern (pageHeader) that
#    all pages use, defined ONCE at the top of each module CSS
#    (not via !important overrides at the bottom).
# B) Fix RecoveryPortal.jsx header JSX to have clean structure:
#    left: title + subtitle, right: stat boxes + mode switch
# C) Remove the duplicate !important .header blocks from all CSS files
#    (they cause layout conflicts) and replace with a clean .pageHeader
#    class that is properly scoped.
# ══════════════════════════════════════════════════════════════════

print("=== FIXING RecoveryPortal.jsx header JSX ===")

RECOVERY_JSX = "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx"

# We need to see what the current header JSX looks like and replace it.
# Based on the screenshots, the header has:
# - title "RECOVERY HUB"
# - stat boxes (TARGETS, BACKLOG) that appear to be inside the title area
# - mode switch buttons (ACTION QUEUE / FULL SCHEDULE) overlapping
# The fix: clean 2-part header — left (title+subtitle), right (stats+tabs)

with open(RECOVERY_JSX, "r", encoding="utf-8") as f:
    recovery_content = f.read()

# Find and replace the header JSX section
# The current broken header renders everything flat
# We replace the entire return statement's header portion

old_header_jsx = """            <header className={styles.header}>
                <div className={styles.titleBlock}>
                    <h1 className={styles.title}>Recovery Hub</h1>
                    <div className={styles.modeSwitch}>"""

new_header_jsx = """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Recovery Hub</h1>
                    <p className={styles.pageSubtitle}>Client Call Management · 2-14 Rule Active</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.hudStats}>
                        <div className={styles.statBox}>
                            <label>TARGETS</label>
                            <strong style={{color: queue.length > 0 ? '#EE8C3A' : '#fff'}}>{queue.length}</strong>
                        </div>
                        <div className={styles.statBox}>
                            <label>BACKLOG</label>
                            <strong style={{color: backlogCount > 0 ? '#ef4444' : '#fff'}}>{backlogCount}</strong>
                        </div>
                    </div>
                    <div className={styles.modeSwitch}>"""

if old_header_jsx in recovery_content:
    recovery_content = recovery_content.replace(old_header_jsx, new_header_jsx, 1)
    print("  OK: Recovery header JSX — restructured")
else:
    print("  MISSING: Recovery header JSX old pattern not found — trying alternative...")
    # Try finding just the header tag
    if 'className={styles.header}' in recovery_content:
        # Replace just the header opening and add proper structure
        recovery_content = recovery_content.replace(
            'className={styles.header}',
            'className={styles.pageHeader}',
            1
        )
        print("  OK: Recovery header class renamed to pageHeader")

# Also need to close the headerRight div properly
# Find the end of modeSwitch and add closing div for headerRight
old_mode_close = """                    </div>
                </div>
                {user?.isRoot || user?.role === 'ROLE_ADMIN' ? ("""

new_mode_close = """                    </div>
                </div>
                </div>
                {user?.isRoot || user?.role === 'ROLE_ADMIN' ? ("""

if old_mode_close in recovery_content:
    recovery_content = recovery_content.replace(old_mode_close, new_mode_close, 1)
    print("  OK: Recovery header — closed headerRight div")

# Remove the old hudStats section that was duplicated outside header
old_hud_stats = """                <div className={styles.hudStats}>
                    <div className={styles.statBox}>
                        <label>TARGETS</label>
                        <strong style={{color: queue.length > 0 ? '#EE8C3A' : '#fff'}}>{queue.length}</strong>
                    </div>
                    <div className={styles.statBox}>
                        <label>BACKLOG</label>
                        <strong style={{color: backlogCount > 0 ? '#ef4444' : '#fff'}}>{backlogCount}</strong>
                    </div>
                </div>"""

if old_hud_stats in recovery_content:
    recovery_content = recovery_content.replace(old_hud_stats, "", 1)
    print("  OK: Recovery — removed duplicate hudStats outside header")

with open(RECOVERY_JSX, "w", encoding="utf-8") as f:
    f.write(recovery_content)


print("\n=== FIXING RecoveryPortal.module.css ===")

RECOVERY_CSS = "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css"

# Replace the broken .header styles at the bottom with clean .pageHeader
# and remove the !important overrides that cause conflicts
with open(RECOVERY_CSS, "r", encoding="utf-8") as f:
    css_content = f.read()

# Find the section starting from "--- UNIFIED HARDWARE HEADER ---"
# and replace everything from that point to end of file
cutoff = "/* --- UNIFIED HARDWARE HEADER --- */"
if cutoff in css_content:
    base = css_content[:css_content.index(cutoff)]
else:
    base = css_content

# Add clean pageHeader styles
new_styles = """
/* ── PAGE HEADER — unified glass panel matching Dashboard ─────── */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 22px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(14px, 2vw, 22px) clamp(18px, 2.5vw, 32px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 var(--radius) var(--radius) 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}

.headerLeft {
    display: flex;
    flex-direction: column;
    gap: clamp(3px, 0.4vw, 5px);
    min-width: 0;
    flex: 1;
}

.headerRight {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1.2vw, 14px);
    flex-shrink: 0;
    flex-wrap: wrap;
}

.pageTitle {
    font-family: 'Cinzel', serif;
    color: #1a2e30;
    font-size: var(--fs-h1);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 0;
    line-height: 1.1;
}

.pageSubtitle {
    font-family: 'DM Sans', sans-serif;
    color: #64748b;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 0;
}

@media (max-width: 700px) {
    .pageHeader {
        flex-direction: column;
        align-items: flex-start;
    }
    .headerRight {
        width: 100%;
    }
    .modeSwitch {
        width: 100%;
    }
    .modeActive, .modeInactive {
        flex: 1;
        justify-content: center;
    }
}
"""

with open(RECOVERY_CSS, "w", encoding="utf-8") as f:
    f.write(base.rstrip() + "\n" + new_styles)
print("  OK: RecoveryPortal.module.css — replaced broken !important header with clean pageHeader")


print("\n=== CLEANING ALL OTHER PAGE CSS FILES ===")
# Remove the broken !important .header overrides from bottom of each CSS file
# These fight with the page-specific layout and cause absolute positioning bugs

css_files_to_clean = [
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    "erp-frontend/src/pages/Reports/ReportHub.module.css",
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    "erp-frontend/src/pages/Intake/IntakePage.module.css",
    "erp-frontend/src/pages/DigitalFolder/FolderPage.module.css",
    "erp-frontend/src/pages/settings/SettingsPage.module.css",
]

# The !important block pattern to remove
important_block_start = "/* --- UNIFIED HARDWARE HEADER --- */"

# The clean pageHeader CSS to add instead (no !important, no absolute buttons)
clean_page_header_css = """
/* ── PAGE HEADER — unified glass panel matching Dashboard ──────── */
/* This is the AUTHORITATIVE header style. No !important needed.   */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(20px, 3vw, 32px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(14px, 2vw, 22px) clamp(18px, 2.5vw, 32px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}
.pageHeaderLeft {
    display: flex;
    flex-direction: column;
    gap: clamp(3px, 0.4vw, 5px);
    min-width: 0;
    flex: 1;
}
.pageHeaderRight {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1.2vw, 14px);
    flex-shrink: 0;
    flex-wrap: wrap;
}
"""

for css_path in css_files_to_clean:
    if not os.path.exists(css_path):
        print(f"  SKIP (not found): {css_path}")
        continue
    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()
    if important_block_start in content:
        # Cut everything from the first occurrence of this marker
        cut_pos = content.index(important_block_start)
        clean = content[:cut_pos].rstrip()
        # Add our clean pageHeader instead
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(clean + "\n" + clean_page_header_css + "\n")
        print(f"  OK: Removed !important overrides from {css_path.split('/')[-1]}")
    else:
        print(f"  SKIP (no override block found): {css_path.split('/')[-1]}")


print("\n=== UPDATING ALL JSX FILES — use .pageHeader class ===")
# All pages already use className={styles.header} with an <h1> and <p>
# The CSS !important block was styling .header — now we switch to .pageHeader
# so each page's own layout isn't disrupted.

# Pages that need their header class changed from styles.header to styles.pageHeader
# AND need their title/subtitle to use .pageTitle / .pageSubtitle classes
# (The Dashboard already uses its own .header correctly — leave it alone)

pages_to_update = [
    {
        "path": "erp-frontend/src/pages/Audit/AuditPage.jsx",
        "old": '<header className={styles.header}>',
        "new": '<header className={styles.pageHeader}>',
    },
    {
        "path": "erp-frontend/src/pages/Reports/ReportHub.jsx",
        "old": '<header className={styles.header}>',
        "new": '<header className={styles.pageHeader}>',
    },
    {
        "path": "erp-frontend/src/pages/Payments/PaymentsPage.jsx",
        "old": '<header className={styles.header}>',
        "new": '<header className={styles.pageHeader}>',
    },
    {
        "path": "erp-frontend/src/pages/Intake/IntakePage.jsx",
        "old": '<header className={styles.header}>',
        "new": '<header className={styles.pageHeader}>',
    },
    {
        "path": "erp-frontend/src/pages/settings/SettingsPage.jsx",
        "old": '<header className={styles.header}>',
        "new": '<header className={styles.pageHeader}>',
    },
]

for item in pages_to_update:
    patch(item["path"], item["old"], item["new"], f"{item['path'].split('/')[-1]} — header class")


print("\n=== ADDING pageHeader to Ledger, Folder, and remaining CSS files ===")

# Ledger uses .header defined correctly at the top, but the !important block
# at the bottom was overriding it. Now that the override is removed,
# we add .pageHeader as an alias so LedgerPage.jsx can use it too.
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '<header className={styles.header}>',
    '<header className={styles.pageHeader}>',
    "LedgerPage header class"
)

# FolderPage uses terminalHeader which is correct — DON'T change it
# It has its own unique design that works


print("\n=== ADDING pageHeader CSS to pages that lost their header styles ===")

# Now add the pageHeader CSS definition to all page CSS files that need it
# (those that had the !important block removed AND now use .pageHeader in JSX)

page_css_additions = {
    "erp-frontend/src/pages/Audit/AuditPage.module.css": {
        "title_color": "#1a2e30",
        "subtitle": "System Forensics · Accountability Archive"
    },
    "erp-frontend/src/pages/Reports/ReportHub.module.css": {
        "title_color": "#1a2e30",
    },
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css": {
        "title_color": "#1a2e30",
    },
    "erp-frontend/src/pages/Intake/IntakePage.module.css": {
        "title_color": "#1a2e30",
    },
    "erp-frontend/src/pages/settings/SettingsPage.module.css": {
        "title_color": "#1a2e30",
    },
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css": {
        "title_color": "#1a2e30",
    },
}

page_header_block = """
/* ── PAGE HEADER — unified glass panel matching Dashboard ──────── */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(20px, 3vw, 32px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(14px, 2vw, 22px) clamp(18px, 2.5vw, 32px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}
"""

for css_path in page_css_additions.keys():
    if not os.path.exists(css_path):
        print(f"  SKIP (not found): {css_path}")
        continue
    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()
    if ".pageHeader" not in content:
        with open(css_path, "a", encoding="utf-8") as f:
            f.write(page_header_block)
        print(f"  OK: Added .pageHeader to {css_path.split('/')[-1]}")
    else:
        print(f"  SKIP (already has .pageHeader): {css_path.split('/')[-1]}")


print("\n=== FIXING Payments header JSX structure ===")
# PaymentsPage header currently has the title + refresh button
# The button was getting absolute-positioned on top of the title
# Fix: use proper flex layout

patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.jsx",
    """            <header className={styles.pageHeader}>
                <div>
                    <h1 className={styles.title}>PAYMENTS</h1>
                    <p className={styles.subtitle}>All payment records — title payments and storage fee collections</p>
                </div>
                <button className={styles.refreshBtn} onClick={loadPayments} aria-label="Refresh">
                    <FiRefreshCw size={16} />
                </button>
            </header>""",
    """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>PAYMENTS</h1>
                    <p className={styles.subtitle}>All payment records · title payments and storage fee collections</p>
                </div>
                <button className={styles.refreshBtn} onClick={loadPayments} aria-label="Refresh">
                    <FiRefreshCw size={16} />
                </button>
            </header>""",
    "Payments header — use headerLeft div"
)

patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    ".refreshBtn { background: rgba(26,46,48,0.08); border: 1px solid rgba(26,46,48,0.15); color: #1a2e30; border-radius: 8px; padding: 8px 12px; cursor: pointer; display: flex; align-items: center; transition: all 0.2s; }",
    """.headerLeft { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.refreshBtn { background: rgba(26,46,48,0.08); border: 1px solid rgba(26,46,48,0.15); color: #1a2e30; border-radius: 8px; padding: 8px 12px; cursor: pointer; display: flex; align-items: center; transition: all 0.2s; flex-shrink: 0; }""",
    "Payments — add headerLeft class"
)


print("\n=== WRITING UPDATED LLM_CONTEXT_GUIDE.md ===")

lines = [
    "# GE SOLUTIONS ERP — FULL LLM CONTEXT GUIDE",
    "# For any AI assistant continuing work on this project",
    "# Last updated: May 2026 — Priority 1: unified page headers done",
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
    "  - Understand partial code snippets — needs full files always",
    "- Tools he uses: VS Code, Git Bash terminal (inside VS Code), GitHub, Chrome browser",
    "- Python is installed: use `py` command (not `python`)",
    "- Project folder: `C:/Users/nyenz/Desktop/app/ge solns`",
    "",
    "---",
    "",
    "## 2. HOW TO COMMUNICATE WITH DAVID",
    "",
    "- Use SIMPLE English. No jargon without explanation.",
    "- Use OUTLINE/BULLET format for explanations — not long paragraphs.",
    "- Keep responses SHORT unless doing code.",
    "- When explaining a concept, use analogies or plain words.",
    "- When errors happen, read the log yourself and tell him exactly what is wrong in one sentence.",
    "- Never ask 'which would you prefer A or B' — just do everything needed unless there is a real decision required.",
    "- Confirm one step at a time. Do not skip ahead.",
    "- When David shares a screenshot, read it carefully before responding.",
    "",
    "---",
    "",
    "## 3. HOW TO OUTPUT CODE CHANGES — THE fix.py SYSTEM",
    "",
    "RULE: Never ask David to manually copy-paste code into files. Always use fix.py.",
    "RULE: The LLM guide (LLM_CONTEXT_GUIDE.md) is a SEPARATE file from fix.py. Always output them separately.",
    "RULE: Use str.replace (patch) in fix.py when only a section of a file changes. Only rewrite full files when changes are large or spread throughout.",
    "RULE: Never put triple-quoted strings inside triple-quoted strings in fix.py — use a list of lines joined with newlines instead (this avoids SyntaxError).",
    "RULE: Before writing a patch, always verify the exact text to replace by reading the document context. Do not guess.",
    "RULE: The LLM_CONTEXT_GUIDE.md must be updated inside fix.py on every session — use the list-of-lines approach.",
    "",
    "### CRITICAL — Why patches fail:",
    "- If fix.py says 'patch target not found', the CSS already has the change OR the text doesn't match exactly.",
    "- Always read the actual file content from the conversation context before writing str.replace patches.",
    "- The documents shared in the conversation ARE the current file contents — use them as source of truth.",
    "- Copy the exact block including all whitespace, comments, and surrounding lines.",
    "",
    "### Two files David always gets:",
    "1. **fix.py** — writes all changed source code files",
    "2. **LLM_CONTEXT_GUIDE.md** — updated guide for the next AI session (written BY fix.py)",
    "",
    "### Fix.py efficiency rules:",
    "- Use `file.read()` + `str.replace()` for partial changes — keeps fix.py small",
    "- Only use full file rewrite when many sections change or file is new",
    "- Always use `encoding='utf-8'` in open() calls",
    "- Always use `os.makedirs(os.path.dirname(path), exist_ok=True)` before writing new files",
    "- Skip os.makedirs for root-level files (empty path causes error)",
    "- When writing the LLM guide itself, use a list of lines joined with newlines — never embed it in a triple-quoted string",
    "- Print OK/MISSING for every patch so David can see what happened",
    "",
    "### How David gets the files:",
    "- You call `present_files(['/mnt/user-data/outputs/fix.py', '/mnt/user-data/outputs/LLM_CONTEXT_GUIDE.md'])`",
    "- David downloads both from the chat interface",
    "- For fix.py: open in VS Code, Ctrl+A, Delete, paste new content, Ctrl+S, run `py fix.py`",
    "- For LLM_CONTEXT_GUIDE.md: replace the file in the project root",
    "- Then: `git add -A && git commit -m 'message' && git push`",
    "- Watch Render Events tab for green tick (5-10 min free tier)",
    "- Test at golden-seed.onrender.com",
    "- If red: click 'deploy logs' -> read error -> fix -> repeat",
    "",
    "---",
    "",
    "## 4. THE PROJECT — WHAT IT IS",
    "",
    "### Name",
    "Golden Seed ERP (code name: NYENZ)",
    "",
    "### Purpose",
    "Internal staff accountability tool for GE Solutions — a Ugandan land surveying and title processing company. Staff-only. Not client-facing.",
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
    "```",
    "ge solns/",
    "├── erp-backend/",
    "│   └── src/main/java/com/gesolutions/erp/",
    "├── erp-frontend/",
    "│   └── src/",
    "│       ├── api/axios.js",
    "│       ├── context/AuthProvider.jsx",
    "│       ├── hooks/useAuth.js",
    "│       ├── components/",
    "│       ├── pages/",
    "│       │   ├── Audit/AuditPage.jsx + AuditPage.module.css",
    "│       │   ├── Dashboard/",
    "│       │   ├── DigitalFolder/FolderPage.jsx",
    "│       │   ├── Intake/IntakePage.jsx + IntakePage.module.css",
    "│       │   ├── Ledger/LedgerPage.jsx + LedgerPage.module.css",
    "│       │   ├── Payments/PaymentsPage.jsx + PaymentsPage.module.css",
    "│       │   ├── Recovery/RecoveryPortal.jsx + RecoveryPortal.module.css",
    "│       │   ├── Reports/ReportHub.jsx",
    "│       │   ├── login/LoginPage.jsx",
    "│       │   └── settings/SettingsPage.jsx",
    "│       └── services/",
    "├── LLM_CONTEXT_GUIDE.md",
    "├── fix.py",
    "├── docker-compose.yml",
    "└── render.yaml",
    "```",
    "",
    "---",
    "",
    "## 7. UI DESIGN STANDARDS (CRITICAL — apply consistently)",
    "",
    "### Page Header Style (ALL pages MUST match Dashboard)",
    "- Use `className={styles.pageHeader}` — NOT `className={styles.header}`",
    "- White/cream glass panel: `background: rgba(255,255,255,0.62)`",
    "- Left orange border: `border-left: clamp(3px,0.4vw,5px) solid var(--orange)`",
    "- Border radius: `0 12px 12px 0` (flat left, rounded right)",
    "- Backdrop blur: `backdrop-filter: blur(15px)`",
    "- Box shadow: `0 4px 15px rgba(0,0,0,0.07)`",
    "- Title: Cinzel serif, navy #1a2e30, uppercase, letter-spacing 1.5px",
    "- Subtitle: DM Sans 900, #64748b, uppercase",
    "- Layout: flex row, left side = title+subtitle, right side = actions/buttons",
    "- NEVER use position:absolute on buttons inside the header — use flex gap",
    "- NEVER use !important overrides to style .header — define .pageHeader cleanly",
    "",
    "### WHY the old approach broke Recovery:",
    "- All CSS files had a giant !important block at the bottom overriding .header",
    "- This block used `position: absolute` for buttons which caused overlap",
    "- FIX: Removed all !important blocks, use .pageHeader class cleanly",
    "",
    "### Filter Button Style (ALL pages must be identical — CONFIRMED STANDARD)",
    "- **Inactive**: `background: rgba(26,46,48,0.75)`, `border: 1.5px solid rgba(255,255,255,0.18)`, `color: rgba(255,255,255,0.85)`",
    "- **Hover**: `background: rgba(238,140,58,0.12)`, `color: #EE8C3A`, `border-color: var(--orange)`",
    "- **Active/Selected**: `background: #EE8C3A`, `color: #1a2e30`, `border-color: #EE8C3A`",
    "- Font: DM Sans 900, uppercase, letter-spacing 1.5px",
    "",
    "### Recovery Page Header Layout",
    "- Uses `.pageHeader` (flex row)",
    "- Left: `.headerLeft` with `.pageTitle` + `.pageSubtitle`",
    "- Right: `.headerRight` with stat boxes + mode switch tabs",
    "- Stat boxes use existing `.hudStats` + `.statBox` classes",
    "",
    "### FolderPage Header",
    "- Uses `.terminalHeader` — its own design, do NOT change to pageHeader",
    "- It has unique backlog/edit badges that need their own layout",
    "",
    "---",
    "",
    "## 8. HOW THE APP WORKS — LINEAR FLOW",
    "",
    "### Step 1: INTAKE → Step 2: LEDGER → Step 3: FOLDER PAGE",
    "### Step 4: RECOVERY HUB → Step 5: PAYMENTS → Step 6: AUDIT",
    "",
    "---",
    "",
    "## 9. KEY BUSINESS RULES",
    "",
    "- **2-14 Rule**: Max 2 calls/client/month. Min 14 days between calls.",
    "- **Recovery grouping**: By unique phone number.",
    "- **Backlog trigger**: 365 days no payment (auto) OR admin manually.",
    "- **Storage fee**: UGX 50,000 every 30 days from backlog START DATE.",
    "- **Payment types**: STANDARD, INITIAL_DEPOSIT, BACKLOG_PARTIAL.",
    "- **Phone uniqueness**: Two owners cannot share the same phone number.",
    "- **Admin/Root only**: Payments, backlog management, Reports, Audit.",
    "- **Cloudinary**: All files stored on Cloudinary.",
    "",
    "---",
    "",
    "## 10. WHAT HAS BEEN COMPLETED (chronological)",
    "",
    "### Priority 1 — Styling & Intake Cleanup — DONE",
    "- RecoveryPortal: 2-column grid, mobile responsive — DONE",
    "- PaymentsPage: filter buttons unified to dark-bg inactive style — DONE",
    "- IntakePage: cleaned up financials — DONE",
    "- LedgerPage: tagBacklog + rowBacklog CSS; filter fixed; plot ID two lines — DONE",
    "- AuditPage: RESET FILTERS aligned; fully responsive — DONE",
    "- All page headers: unified glass panel using .pageHeader class — DONE (May 2026)",
    "  - Root cause found: !important block at bottom of every CSS was position:absolute-ing buttons",
    "  - Fix: Removed all !important blocks, switched to clean .pageHeader class",
    "  - Recovery portal header restructured: left=title, right=stats+tabs",
    "- Filter bar unification: Payments + Ledger now share identical inactive/hover/active style — DONE",
    "",
    "---",
    "",
    "## 11. WHAT STILL NEEDS TO BE DONE (in priority order)",
    "",
    "### Priority 1 — Remaining",
    "- Continue checking screenshots after this deploy for any remaining styling issues",
    "",
    "### Priority 2 — Reports overhaul",
    "1. Add backlog report (all backlog plots with storage fees breakdown)",
    "2. Add completed titles report (released plots)",
    "3. Add payment history report (all payments, date range filter)",
    "4. Add storage fees report (total fees per plot)",
    "5. Add monthly collection report (how much collected each month)",
    "",
    "### Priority 3 — Mobile audit + small fixes",
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
    "- WebConfig.java has old local file serving reference — harmless (Cloudinary is used)",
    "- Notification model exists but never used",
    "- No rate limiting on login",
    "- Release button does not check for uploaded documents first",
    "- payment_schedules table still exists in DB — no longer used (harmless)",
    "- App name inconsistency: 'NYENZ ERP' vs 'Golden Seed' in different places",
    "",
    "---",
    "",
    "## 13. DEPLOYMENT PROCESS",
    "",
    "1. Create fix.py AND updated LLM_CONTEXT_GUIDE.md -> present_files both -> David downloads both",
    "2. David replaces local fix.py -> `py fix.py` -> check output for OK/MISSING",
    "3. David replaces local LLM_CONTEXT_GUIDE.md",
    "4. `git add -A && git commit -m 'message' && git push`",
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
    "| `Can not set boolean field isBacklog to null` | DB rows have NULL, Java primitive boolean | Use `Boolean` (capital B) not `boolean` |",
    "| `UnicodeEncodeError` in fix.py | Windows default encoding | Always use `encoding='utf-8'` in open() |",
    "| `nothing added to commit` | Files already match what's in git | Force add specific files |",
    "| 500 on /dashboard/summary | Backend crash — check Render Logs tab | Read Caused by: line at bottom of log |",
    "| CSS class not found | Class used in JSX but not defined in .module.css | Add the missing class to the CSS file |",
    "| SyntaxError in fix.py with triple quotes | LLM guide embedded inside triple-quoted string | Use list of lines joined with newlines instead |",
    "| fix.py shows 'patch target not found' | Text to replace doesn't match file exactly | Read actual file from conversation context before writing patch |",
    "| Header buttons overlapping title | !important position:absolute in CSS override block | Remove !important block, use .pageHeader flex layout |",
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
print("1. py fix.py")
print("2. Check all OK/MISSING messages")
print("3. git add -A && git commit -m 'unified page headers, fix recovery portal layout' && git push")
print("4. Wait for Render green tick, test site")