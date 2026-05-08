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
RULE: Never put triple-quoted strings inside triple-quoted strings in fix.py -- use a list of lines joined with newlines instead.
RULE: Never use special unicode characters in fix.py strings -- use plain ASCII only.
RULE: Before writing a patch, always verify the exact text to replace by reading the document context.
RULE: Always open files with errors='replace' when reading.

---

## 4. THE PROJECT -- WHAT IT IS

Golden Seed ERP (code name: NYENZ)
Internal staff accountability tool for GE Solutions -- a Ugandan land surveying and title processing company. Staff-only.

---

## 5. TECH STACK
Backend: Java Spring Boot 3.2.5, PostgreSQL
Frontend: React 19, Vite, CSS Modules
File Storage: Cloudinary
Deployment: Render free tier

---

## 6. UI DESIGN STANDARDS (CRITICAL -- apply consistently)
- Filter Button Style: Single row, text only, rounded corners (not pills), dark inactive, orange active.
- Table Design Standard (Ledger is master reference): Dark wrapper, orange headers, no glow on rows.
- Search inputs have text-indent to clear the search icon. No native browser 'X' clear buttons allowed.
- Dropdowns must shrink/grow responsively and have hidden scrollbars.
- Modals use HardwareModal.module.css.
- Empty States: Must say NO RECORDS MATCH 'xyz' when searching.

---

## 7. NEXT PRIORITIES
Priority 2 -- Reports overhaul
1. Add backlog report
2. Add completed titles report
3. Add payment history report
4. Add storage fees report
5. Add monthly collection report