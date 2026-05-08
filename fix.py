import os
import re

def write_file(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"  OK: Restored {path}")

def append_css(path, css, label):
    if not os.path.exists(path):
        print(f"  MISSING FILE: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if "/* --- PRIORITY 1 FINAL POLISH --- */" not in content:
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"\n/* --- PRIORITY 1 FINAL POLISH --- */\n{css}\n")
        print(f"  OK: {label}")
    else:
        print(f"  ALREADY APPLIED: {label}")

def patch_payments_jsx():
    path = "erp-frontend/src/pages/Payments/PaymentsPage.jsx"
    if not os.path.exists(path):
        print(f"  MISSING FILE: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find what the search variable is named (usually 'searchTerm' or 'search')
    match = re.search(r'const\s+\[(search\w*)\s*,', content)
    search_var = match.group(1) if match else "searchTerm"

    # Replace the hardcoded string with the dynamic matching string
    old_str1 = '"NO PAYMENT RECORDS FOUND"'
    old_str2 = ">NO PAYMENT RECORDS FOUND<"
    new_str = f'{{{search_var} ? `NO RECORDS MATCH "${{{search_var}.toUpperCase()}}"` : "NO PAYMENT RECORDS FOUND"}}'

    modified = False
    if old_str1 in content:
        content = content.replace(old_str1, new_str)
        modified = True
    if old_str2 in content:
        content = content.replace(old_str2, f">{new_str}<")
        modified = True

    if modified:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print("  OK: Patched Payments Empty State to match Ledger")
    else:
        print("  SKIP/NOT FOUND: Payments Empty State already patched")

print("\nExecuting Priority 1 Final Polish...")

# 1. FIX SEARCH 'X' ICONS (Hide native, colorize custom)
search_css = """
/* Hide browser default search 'X' */
input[type="search"]::-webkit-search-decoration,
input[type="search"]::-webkit-search-cancel-button,
input[type="search"]::-webkit-search-results-button,
input[type="search"]::-webkit-search-results-decoration {
  -webkit-appearance: none !important;
  display: none !important;
}

/* Force custom clear button to be Golden Seed Orange */
[class*="searchClear"] {
    color: #EE8C3A !important;
    opacity: 0.9 !important;
}
[class*="searchClear"]:hover {
    background: rgba(238, 140, 58, 0.15) !important;
    opacity: 1 !important;
}
"""
append_css("erp-frontend/src/index.css", search_css, "Fixed dual 'X' issue on Search Bars")

# 2. MATCH AUDIT FILTERS TO PAYMENTS FILTERS & FIX RESPONSIVENESS
audit_css = """
/* Override previous Pill styles - strictly enforce Payments Filter Button design */
.hwSelectWrap {
    flex: 1 1 120px !important;
    min-width: 110px !important;
    max-width: none !important;
}
.hwSelectWrap [class*="selectBox"], .resetBtn {
    border-radius: var(--radius-sm, 6px) !important;
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    padding: 0 clamp(10px, 1.3vw, 16px) !important;
    height: clamp(34px, 4vw, 40px) !important;
}
.hwSelectWrap [class*="selectBox"]:hover, .resetBtn:hover {
    background: rgba(238, 140, 58, 0.12) !important;
    border-color: #EE8C3A !important;
    color: #EE8C3A !important;
}
.hwSelectWrap .active {
    background: #EE8C3A !important;
    border-color: #EE8C3A !important;
    color: #1a2e30 !important;
}
.hwSelectWrap .active [class*="currentValue"], .hwSelectWrap .active [class*="icon"] {
    color: #1a2e30 !important;
}
"""
append_css("erp-frontend/src/pages/Audit/AuditPage.module.css", audit_css, "Synced Audit filters perfectly with Payments style")

# 3. HIDE DROPDOWN SCROLLBAR
dropdown_css = """
/* Hide visible scrollbars on HardwareSelect dropdowns */
.dropdown::-webkit-scrollbar {
    display: none !important;
}
.dropdown {
    -ms-overflow-style: none !important;
    scrollbar-width: none !important;
}
"""
append_css("erp-frontend/src/components/common/HardwareSelect.module.css", dropdown_css, "Removed visible scrollbar from dropdowns")

# 4. REVERT PAYMENTS MOBILE TABLE TO MATCH LEDGER
payments_css = """
/* Revert mobile table shell to match Ledger exactly */
@media (max-width: 480px) {
    .tableScroll {
        margin: 0 !important;
        border-radius: var(--radius) !important;
        padding-bottom: 0 !important;
    }
}
"""
append_css("erp-frontend/src/pages/Payments/PaymentsPage.module.css", payments_css, "Re-aligned Payments mobile table borders to match Ledger")

# 5. PATCH PAYMENTS JSX FOR EMPTY STATE
patch_payments_jsx()

# 6. RESTORE LLM_CONTEXT_GUIDE.md
guide_lines = [
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
    "RULE: Never put triple-quoted strings inside triple-quoted strings in fix.py -- use a list of lines joined with newlines instead.",
    "RULE: Never use special unicode characters in fix.py strings -- use plain ASCII only.",
    "RULE: Before writing a patch, always verify the exact text to replace by reading the document context.",
    "RULE: Always open files with errors='replace' when reading.",
    "",
    "---",
    "",
    "## 4. THE PROJECT -- WHAT IT IS",
    "",
    "Golden Seed ERP (code name: NYENZ)",
    "Internal staff accountability tool for GE Solutions -- a Ugandan land surveying and title processing company. Staff-only.",
    "",
    "---",
    "",
    "## 5. TECH STACK",
    "Backend: Java Spring Boot 3.2.5, PostgreSQL",
    "Frontend: React 19, Vite, CSS Modules",
    "File Storage: Cloudinary",
    "Deployment: Render free tier",
    "",
    "---",
    "",
    "## 6. UI DESIGN STANDARDS (CRITICAL -- apply consistently)",
    "- Filter Button Style: Single row, text only, rounded corners (not pills), dark inactive, orange active.",
    "- Table Design Standard (Ledger is master reference): Dark wrapper, orange headers, no glow on rows.",
    "- Search inputs have text-indent to clear the search icon. No native browser 'X' clear buttons allowed.",
    "- Dropdowns must shrink/grow responsively and have hidden scrollbars.",
    "- Modals use HardwareModal.module.css.",
    "- Empty States: Must say NO RECORDS MATCH 'xyz' when searching.",
    "",
    "---",
    "",
    "## 7. NEXT PRIORITIES",
    "Priority 2 -- Reports overhaul",
    "1. Add backlog report",
    "2. Add completed titles report",
    "3. Add payment history report",
    "4. Add storage fees report",
    "5. Add monthly collection report"
]
write_file("LLM_CONTEXT_GUIDE.md", guide_lines)

# 7. UPDATE ADDENDUM
addendum_lines = [
    "# GE SOLUTIONS ERP -- CONTEXT ADDENDUM V3",
    "# Last updated: May 2026 - Final UI Polish Details",
    "",
    "## NEW RULES ESTABLISHED THIS SESSION",
    "",
    "### 1. SEARCH INPUTS",
    "- Browser native `::-webkit-search-cancel-button` is permanently disabled.",
    "- The custom `.searchClear` icon is forced to `--orange`.",
    "- Text-indent is dynamically applied to avoid search text overlapping the left icon.",
    "",
    "### 2. DROPDOWNS & FILTER BUTTONS",
    "- MUST be perfectly rectangular with `border-radius: var(--radius-sm)` (6px-8px). NO PILLS.",
    "- Dropdowns must use `flex: 1 1 120px` to stretch and compress seamlessly on mobile.",
    "- Dropdowns must have `::-webkit-scrollbar { display: none; }`.",
    "",
    "### 3. EMPTY STATES",
    "- Searching in tables MUST return dynamic text: `NO RECORDS MATCH 'term'`.",
    "- Use Ledger logic as the absolute source of truth.",
    "",
    "### 4. MOBILE TABLES",
    "- Table wrappers (`.tableScroll`) must NOT use negative margins on mobile.",
    "- They must respect the standard `border-radius` to prevent bleeding off the screen edges."
]
write_file("LLM_CONTEXT_GUIDE_ADDENDUM.md", addendum_lines)