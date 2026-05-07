import os

def patch(path, old, new, label):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING (not found): {label}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label}")

def write_file(path, content, label):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  WRITTEN: {label}")

# ==============================================================
# SECTION 1: HEADER SIZE -- match Dashboard exactly on all pages
#
# Dashboard header padding: clamp(10px, 1.4vw, 16px) top/bottom
#                           clamp(16px, 2.2vw, 28px) left/right
# Other pages used:         clamp(14px, 2vw, 22px) top/bottom
#                           clamp(18px, 2.5vw, 32px) left/right
# Fix: reduce all non-dashboard headers to match Dashboard values
# ==============================================================
print("=== SECTION 1: HEADER SIZE UNIFORMITY ===")

PAGES_WITH_LARGE_HEADER = [
    ("erp-frontend/src/pages/Intake/IntakePage.module.css",   "IntakePage"),
    ("erp-frontend/src/pages/Ledger/LedgerPage.module.css",   "LedgerPage"),
    ("erp-frontend/src/pages/Payments/PaymentsPage.module.css","PaymentsPage"),
    ("erp-frontend/src/pages/Reports/ReportHub.module.css",   "ReportHub"),
    ("erp-frontend/src/pages/Audit/AuditPage.module.css",     "AuditPage"),
]

OLD_HEADER_PAD = "    padding: clamp(14px, 2vw, 22px) clamp(18px, 2.5vw, 32px);"
NEW_HEADER_PAD = "    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);"

for css_path, label in PAGES_WITH_LARGE_HEADER:
    patch(css_path, OLD_HEADER_PAD, NEW_HEADER_PAD, f"{label} - reduce header padding to match Dashboard")

# Recovery portal uses different padding value
patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",
    "    padding: clamp(14px, 2vw, 22px) clamp(18px, 2.5vw, 32px);",
    "    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);",
    "RecoveryPortal - reduce header padding to match Dashboard"
)
# Recovery has it twice (duplicate .pageHeader block)
patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",
    "    padding: clamp(14px, 2vw, 22px) clamp(18px, 2.5vw, 32px);",
    "    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);",
    "RecoveryPortal - reduce header padding (second occurrence)"
)

# Settings page also has large padding
patch(
    "erp-frontend/src/pages/settings/SettingsPage.module.css",
    "    padding: clamp(14px, 2vw, 22px) clamp(18px, 2.5vw, 32px);",
    "    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);",
    "SettingsPage - reduce header padding to match Dashboard"
)

# Also fix margin-bottom on all pageHeaders to match dashboard clamp(14px,2vw,22px) -> clamp(14px, 2vw, 20px)
# Dashboard uses: margin-bottom: var(--gap-xl) which is clamp(14px, 2vw, 24px)
# Other pages use: margin-bottom: clamp(20px, 3vw, 32px)  -- too much!
# Fix to match Dashboard value

PAGES_WITH_LARGE_MARGIN = [
    "erp-frontend/src/pages/Intake/IntakePage.module.css",
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    "erp-frontend/src/pages/Reports/ReportHub.module.css",
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    "erp-frontend/src/pages/settings/SettingsPage.module.css",
]

for css_path in PAGES_WITH_LARGE_MARGIN:
    patch(
        css_path,
        "    margin-bottom: clamp(20px, 3vw, 32px);",
        "    margin-bottom: clamp(14px, 2vw, 24px);",
        f"{css_path} - reduce header margin-bottom to match Dashboard"
    )

# Recovery has different margin value
patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",
    "    margin-bottom: clamp(14px, 2vw, 22px);",
    "    margin-bottom: clamp(14px, 2vw, 24px);",
    "RecoveryPortal - normalize margin-bottom"
)


# ==============================================================
# SECTION 2: FILTER BUTTONS - icons inline with text, not stacked
#
# Ledger has icons in filter buttons. Fix: text-only, same row.
# The FILTERS array in LedgerPage.jsx has icon property but we
# already remove icons from the render. The issue is CSS:
# display:flex + flex-direction:column makes icons appear above.
#
# Standard (Payments page):
#   display: flex; align-items: center; gap: 8px; (row, not column)
# ==============================================================
print("\n=== SECTION 2: FILTER BUTTON ICON ALIGNMENT ===")

# LedgerPage filterBtn - was flex-direction:column, fix to row
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    """.filterBtn {
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    padding: 8px 16px;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 4px;
    gap: 8px;
    white-space: nowrap;
}""",
    """.filterBtn {
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    padding: 8px 16px;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}""",
    "LedgerPage - filterBtn flex-direction row (icons inline)"
)

# PaymentsPage filterBtn also had column (from the duplicate definition)
patch(
    "erp-frontend/src/pages/Payments/PaymentsPage.module.css",
    """.filterBtn {
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    padding: 8px 16px;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}""",
    """.filterBtn {
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    padding: 8px 16px;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}""",
    "PaymentsPage - filterBtn flex-direction row"
)

# AuditPage - resetBtn also needs to be inline row
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    """    display: flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    text-transform: uppercase;
    white-space: nowrap;""",
    """    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    text-transform: uppercase;
    white-space: nowrap;""",
    "AuditPage - resetBtn flex-direction row"
)


# ==============================================================
# SECTION 3: LEDGER PAGE - remove redundant search hint text,
# put it as placeholder in the search input instead
# ==============================================================
print("\n=== SECTION 3: LEDGER search hint -> placeholder ===")

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '''                    <input
                        type="search" id="ledger-search"
                        placeholder="Search by plot, name, phone, NIN, box, district..."
                        className={styles.searchInput}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        aria-label="Search ledger records"
                        aria-describedby="ledger-search-hint"
                        autoComplete="off"
                    />
                    {searchTerm && (
                        <button className={styles.searchClearBtn} onClick={() => setSearchTerm('')}
                            aria-label="Clear search" type="button">
                            <FiX aria-hidden="true" />
                        </button>
                    )}
                </div>
                <p id="ledger-search-hint" className={styles.searchHint}>{SEARCH_HINT}</p>''',
    '''                    <input
                        type="search" id="ledger-search"
                        placeholder="Plot ID, box, owner name, phone, NIN, email, district, county, tenure..."
                        className={styles.searchInput}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        aria-label="Search ledger records"
                        autoComplete="off"
                    />
                    {searchTerm && (
                        <button className={styles.searchClearBtn} onClick={() => setSearchTerm('')}
                            aria-label="Clear search" type="button">
                            <FiX aria-hidden="true" />
                        </button>
                    )}
                </div>''',
    "LedgerPage - remove redundant search hint, embed in placeholder"
)

# Remove SEARCH_HINT const since it's no longer used
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    "    const SEARCH_HINT = 'Plot ID \u25c6 Box \u25c6 Owner name \u25c6 Phone \u25c6 NIN \u25c6 Email \u25c6 District \u25c6 County \u25c6 Tenure';",
    "",
    "LedgerPage - remove SEARCH_HINT const"
)

# Also remove the .searchHint and .searchBlock flex-col since no hint below
# Actually keep searchBlock but remove hint styles since placeholder handles it
# Just hide the hint via CSS (it's already removed from JSX above)


# ==============================================================
# SECTION 4: LEDGER TABLE - plot column redesign
#
# Problems:
# 1. Orange bg on tenure tag looks cluttered
# 2. Everything crammed on one line
# 3. Payment dots too large (10px)
# 4. table not extending to full width (HardwarePanel has padding)
#
# Fix:
# - Make dots 8px, subtle
# - Plot number large + bold on its own line
# - Tenure as a small muted tag (not orange bg)
# - District as another small tag
# - Remove the orange bg from span inside plotCell
# ==============================================================
print("\n=== SECTION 4: LEDGER table plot column redesign ===")

# Fix plotCell CSS - remove orange bg from span, make two-line layout clean
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    """/* Plot cell -- two-line layout to avoid cramping */
.plotCell strong {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-value);
    font-weight: 900;
    color: #fff;
    letter-spacing: 0.5px;
    white-space: normal;
    word-break: break-all;
    line-height: 1.3;
}
/* Tenure on its own line -- orange tag */
.plotCell span {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    color: #1a2e30;
    background: var(--orange);
    padding: 1px 6px;
    border-radius: 3px;
    text-transform: uppercase;
    width: fit-content;
}""",
    """/* Plot cell -- clean two-line layout */
.plotCell strong {
    display: block;
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-value);
    font-weight: 900;
    color: #fff;
    letter-spacing: 0.5px;
    white-space: normal;
    word-break: break-word;
    line-height: 1.3;
    margin-bottom: 3px;
}
/* Tenure -- muted pill, no orange bg */
.plotCell .tenureTag {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    color: rgba(255,255,255,0.55);
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    padding: 1px 7px;
    border-radius: 3px;
    text-transform: uppercase;
    margin-right: 4px;
}
/* District tag */
.plotCell .districtTag {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 800;
    color: rgba(238,140,58,0.85);
    padding: 0;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}""",
    "LedgerPage CSS - plotCell redesign: no orange bg, clean layout"
)

# Fix the plotCell JSX to use new class names
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """                                        <td className={styles.plotCell}>
                                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                                <PaymentDot proj={proj} />
                                                <div>
                                                    <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                    <span>{proj.landTitle?.tenure}</span>
                                                    {proj.landTitle?.district && (
                                                        <span className={styles.districtTag}>{proj.landTitle.district}</span>
                                                    )}
                                                </div>
                                            </div>
                                        </td>""",
    """                                        <td className={styles.plotCell}>
                                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                                                <PaymentDot proj={proj} />
                                                <div>
                                                    <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                    <div>
                                                        {proj.landTitle?.tenure && (
                                                            <span className={styles.tenureTag}>{proj.landTitle.tenure}</span>
                                                        )}
                                                        {proj.landTitle?.district && (
                                                            <span className={styles.districtTag}>{proj.landTitle.district}</span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>""",
    "LedgerPage JSX - plotCell use tenureTag + districtTag classes"
)

# Make payment dots smaller (10px -> 8px) and neater
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """const PaymentDot = ({ proj }) => {
    const badge = getPaymentBadge(proj);
    return (
        <span
            title={BADGE_LABELS[badge]}
            aria-label={BADGE_LABELS[badge]}
            style={{
                display: 'inline-block',
                width: 10, height: 10,
                borderRadius: '50%',
                background: BADGE_COLORS[badge],
                boxShadow: `0 0 6px ${BADGE_COLORS[badge]}`,
                marginRight: 6,
                flexShrink: 0,
                verticalAlign: 'middle',
            }}
        />
    );
};""",
    """const PaymentDot = ({ proj }) => {
    const badge = getPaymentBadge(proj);
    return (
        <span
            title={BADGE_LABELS[badge]}
            aria-label={BADGE_LABELS[badge]}
            style={{
                display: 'inline-block',
                width: 7, height: 7,
                borderRadius: '50%',
                background: BADGE_COLORS[badge],
                boxShadow: `0 0 4px ${BADGE_COLORS[badge]}`,
                flexShrink: 0,
                marginTop: 4,
            }}
        />
    );
};""",
    "LedgerPage - PaymentDot smaller (7px) and top-aligned"
)


# ==============================================================
# SECTION 5: TABLE WIDTH -- remove HardwarePanel padding so table
# stretches edge to edge. Also ensure container max-width is used.
# The table is inside HardwarePanel which has padding: 30px.
# We need to make the table break out of that padding.
# ==============================================================
print("\n=== SECTION 5: TABLE full width inside panel ===")

# The HardwarePanel component adds padding via panelInner.
# LedgerPage renders: <HardwarePanel variant="dark"><div className={styles.tableScroll}>...
# The panelInner padding is 30px from HardwarePanel.module.css
# We need to apply negative margin to tableScroll to break out

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    """.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
}""",
    """.tableScroll {
    overflow-x: auto;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    /* Break out of HardwarePanel's 30px padding to use full width */
    margin: -30px;
    margin-bottom: 0;
}""",
    "LedgerPage - tableScroll negative margin to break out of panel padding"
)

# Also fix the pagination to have proper padding now that table breaks out
patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    """.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(10px, 1.4vw, 16px) clamp(14px, 2vw, 22px);
    border-top: 1px solid rgba(255,255,255,0.06);
}""",
    """.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(10px, 1.4vw, 16px) clamp(14px, 2vw, 22px);
    border-top: 1px solid rgba(255,255,255,0.06);
    /* Compensate for the negative margin on tableScroll */
    margin: 0 0 -30px 0;
}""",
    "LedgerPage - pagination margin compensate for tableScroll breakout"
)

# ==============================================================
# SECTION 6: LEDGER -- also remove icons from FILTERS array
# (they still exist in the data even though JSX doesn't render them)
# and tidy up the controlHub spacing
# ==============================================================
print("\n=== SECTION 6: LEDGER filter icons - clean removal from data ===")

patch(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    """    const FILTERS = [
        { key: 'ALL',      label: 'ALL ARCHIVES', icon: <FiLayers        aria-hidden="true" /> },
        { key: 'BACKLOG',  label: 'BACKLOG',       icon: <FiAlertOctagon  aria-hidden="true" /> },
        { key: 'LEGACY',   label: 'LEGACY',        icon: <FiArchive       aria-hidden="true" /> },
        { key: 'DEBTORS',  label: 'UNPAID',        icon: <FiActivity      aria-hidden="true" /> },
        { key: 'CRITICAL', label: 'CRITICAL',      icon: <FiAlertTriangle aria-hidden="true" /> },
    ];""",
    """    const FILTERS = [
        { key: 'ALL',      label: 'ALL ARCHIVES' },
        { key: 'BACKLOG',  label: 'BACKLOG'      },
        { key: 'LEGACY',   label: 'LEGACY'       },
        { key: 'DEBTORS',  label: 'UNPAID'       },
        { key: 'CRITICAL', label: 'CRITICAL'     },
    ];""",
    "LedgerPage - remove icons from FILTERS array entirely"
)

# Now remove the unused icon imports from LedgerPage since we removed icons
# Keep FiLayers (used in loading cell), FiAlertTriangle (error/critical), FiArchive, FiActivity, FiAlertOctagon
# All still used elsewhere in the component so leave imports as-is


# ==============================================================
# SECTION 7: Update LLM_CONTEXT_GUIDE.md
# ==============================================================
print("\n=== SECTION 7: Update LLM_CONTEXT_GUIDE.md ===")

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
    "- PADDING (must match Dashboard): clamp(10px,1.4vw,16px) top/bottom, clamp(16px,2.2vw,28px) left/right",
    "- MARGIN-BOTTOM (must match Dashboard): clamp(14px,2vw,24px)",
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
    "- Layout: single horizontal row, flex-direction:ROW, align-items:center, flex-wrap:nowrap, overflow-x:auto",
    "- NO icons inside filter buttons -- text only",
    "- On mobile: same single row, side-scrollable (never wraps to multiple lines)",
    "",
    "### Ledger Page Plot Column Style (CONFIRMED)",
    "- Payment dot: 7px circle, top-aligned, subtle glow",
    "- Plot number: Space Mono 900, white, own line, word-break:break-word",
    "- Tenure tag: muted pill (rgba white bg, no orange), small DM Sans 900",
    "- District: orange-tinted text, no background, same row as tenure",
    "- NO orange background on any text tag in the plot column",
    "",
    "### Text on Light Background Rule",
    "- The controlHub area (search, filters, badge legend) sits on the warm cream/beige background",
    "- Any text in this area must use dark colors: rgba(26,46,48,0.xx) or #64748b",
    "- Never use rgba(255,255,255,x) for text that appears outside a dark panel",
    "- Badge legend items: color: rgba(26,46,48,0.65), font-size 9-11px",
    "- Search hint: moved to input placeholder (no separate hint text below search)",
    "",
    "### Search Input Rule",
    "- Search hints go INSIDE the input placeholder, not as separate text below",
    "- This avoids visual clutter on the light background",
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
    "### Priority 1 -- Styling & Uniformity -- LARGELY COMPLETE",
    "- RecoveryPortal: 2-column grid, mobile responsive -- DONE",
    "- PaymentsPage: filter buttons unified to dark-bg inactive style -- DONE",
    "- IntakePage: cleaned up financials -- DONE",
    "- LedgerPage: tagBacklog + rowBacklog CSS; filter fixed; plot ID two lines -- DONE",
    "- AuditPage: RESET FILTERS aligned; fully responsive -- DONE",
    "- All page headers: unified glass panel using .pageHeader class -- DONE",
    "- Filter bar unification: all pages now use identical filter button styles -- DONE",
    "  - Single horizontal row, side-scrollable on mobile",
    "  - No icons in filter buttons -- text only",
    "  - flex-direction: ROW with align-items:center (icons inline, not stacked)",
    "  - Standard: dark inactive, orange hover, orange-filled active",
    "- Subtitle positioning: all pages now use headerLeft wrapper for title+subtitle -- DONE",
    "- Header padding/margin matched to Dashboard on ALL pages -- DONE",
    "- LedgerPage badge legend + search hint: dark text for light background -- DONE",
    "- LedgerPage search hint moved to placeholder (no redundant text below) -- DONE",
    "- LedgerPage plot column: no orange bg on tags, clean two-line layout, smaller dots -- DONE",
    "- LedgerPage table: breaks out of HardwarePanel padding to use full width -- DONE",
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
print("2. git add -A && git commit -m 'uniform header size, filter alignment, ledger plot column, table full width' && git push")
print("3. Wait Render green tick (~5-10 min), then test site")
print("4. Send screenshot of Ledger page + other pages to confirm")