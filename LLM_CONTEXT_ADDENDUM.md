# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# This file receives all small incremental updates each session.
# Last updated: 30 May 2026

---

## SESSION MANAGEMENT RULES (HOW EVERY SESSION ENDS)

At the end of every session the AI must do the following in order:

1. Read the addendum to identify everything worked on this session
2. Ask David: "Are you happy with X, Y, Z? Should I mark them as done?"
3. Wait for David to confirm -- do not assume anything is done without confirmation
4. Once confirmed:
   - Move confirmed items INTO Section 10 (COMPLETED) of master guide
   - Remove confirmed items FROM Section 11 (TO DO) of master guide
   - If something new came up during the session, add it to Section 11
5. Both sections must reflect 3 sources of truth:
   - What the addendum says was worked on
   - What David explicitly confirmed he is happy with
   - What the code actually shows

RULE: Once something is marked done and moved to Section 10, it is NEVER put back in Section 11.
RULE: Section 11 only contains things not yet done. Completed work lives in Section 10 only.
RULE: The addendum is the running log. The master guide Sections 10 and 11 are the clean summary.

---

## NEW UI RULES ADDED (May 2026)

### UI UNIFORMITY RULE (DEFAULT DESIGN APPROACH)
Every element of the same type must look and behave identically across all pages and sections regardless of where it appears. This includes fonts, padding, and math logic.

### 4-POCKET FINANCIAL MATH STANDARD
All financial displays must follow the unified logic: 
[PLOT VALUE] + [STORAGE FEES] - [PAID] = [AMOUNT OWED].

### TERMINOLOGY STANDARD
- 'Arrears' is DEPRECATED. Use 'AMOUNT OWED' or 'UNPAID'.
- 'Total Cost' or 'Original Debt' is DEPRECATED. Use 'PLOT VALUE'.
- 'Collected' is DEPRECATED. Use 'PAID'.

---

## SESSION: May 2026 -- THE SYSTEM HARDENING & RECOVERY REBOOT

### 1. Recovery Portal Architectural Redesign
- Grouping: Switched from 'Phone Number' grouping to 'Primary Owner (Client ID)' grouping. 
- Multi-plot Support: Clients with multiple plots now appear as one card, listing all plots inside.
- Visuals: Implemented a robust 2-line header. Line 1: ID & Owed. Line 2: Name, Phone, & Actions.
- High Contrast: Actual values (dates, money, counts) are pure white; Labels are muted grey.
- Status: DONE & PUSHED

### 2. Financial Reconciliation & Backlog Logic
- Math Fix: Repaired the bug where 'Paid' amounts were ignored in Backlog calculations.
- Exit Backlog Choice: Implemented a Decision Modal. Admin must choose to either 'WAIVE' fees or 'CAPITALIZE' (add fees to Total Value).
- Backend Sync: Logic updated in LandService and RecoveryController to ensure no "0" values are sent to frontend.
- Status: DONE & PUSHED

### 3. Professional Print Output (Asset Dossier)
- Layout: Completely overhauled @media print to look like a legal corporate document.
- Design: Recreated the provided sample PDF layout using dark navy header bars and clean white backgrounds.
- Integrity: Forced all tabs and drawers open during print and added 'break-inside: avoid' to prevent cutting data in half across pages.
- Status: DONE & PUSHED

### 4. Reporting Hub Overhaul
- Anti-Theft: Added "Operator Cash Reconciliation" report to track collection by staff member.
- UX: Added expandable "Black Drawers" (matching Audit Page) that show the CSV column schema and report descriptions before downloading.
- Cleanup: Deleted redundant P2-4 report and merged Revenue History with Payment History.
- Status: DONE & PUSHED

### 5. Security & Navigation Guards
- Unsaved Changes: Upgraded to 'Hyper-Strict' mode. One character typed triggers the guard.
- Interceptors: Updated axios.js to redirect to /login?reason=session_conflict on 401 errors.
- Popups: Replaced all native 'window.confirm' browser boxes with styled Golden Seed ConfirmModals.
- Status: DONE & PUSHED

### 6. Intake Page Polish
- Date of Survey: Added a manual field for historical accountability on backlog entries.
- Validation: Document vault now turns red and shakes if user tries to save with 0 scans.
- Phone Hint: Added UI text instructing use of '/' for dual numbers.
- Status: DONE & PUSHED

### 7. Global Scrolling & Mobile Fixes
- Sticky Headers: Search bars and table headers now stick to the top during scroll.
- Mobile Boundaries: Tables now bleed to the edges of the screen on mobile to maximize space.
- Button Scale: Increased touch target size for mobile action buttons.
- Status: DONE & PUSHED