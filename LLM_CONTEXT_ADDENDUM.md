# PATH: LLM_CONTEXT_ADDENDUM.md
# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# Last updated: August 2026
---

## SESSION MANAGEMENT RULES (HOW EVERY SESSION ENDS)

At the end of every session the AI must do the following in order:

1. Read the addendum to identify everything worked on this session
2. Ask David: "Are you happy with X, Y, Z? Should I mark them as done?"
3. Wait for David to confirm -- do not assume anything is done without confirmation
4. Once confirmed:
   - Move confirmed items INTO the master guide (Section 10 for general work, or Section 17's
     Phase Tracker for revamp phases specifically)
   - Remove confirmed items FROM this addendum entirely
   - If something new came up during the session, add it here
5. This file must only ever reflect WORK IN PROGRESS -- not yet confirmed, not yet permanent.

RULE: Once something is marked done and moved to the guide, it is NEVER left duplicated here.
RULE: This addendum should be short. If it is getting long, that means things are overdue for
confirmation and should be cleared out at the next opportunity.

---

## CURRENT STATUS: REVAMP PHASE 7 -- DIRECTOR'S DASHBOARD

APPLIED (fix.py generated this session, not yet run/pushed by David). This is the LAST
planned phase in the ERP Revamp (Section 17). Once David runs this fix.py and confirms it
works, Phases 1 through 7 are ALL code-complete.

What this phase adds:
- Backend: `DirectorDashboardDTO.java` (new), and a new `GET /api/v1/dashboard/director`
  endpoint on `DashboardController.java`, restricted to ROLE_ADMIN and ROLE_DIRECTOR.
- The endpoint returns, for a single time window (DAY/WEEK/MONTH/YEAR): revenue collected,
  transaction count, staff activity (from the audit log), and two always-current snapshots
  that ignore the window entirely -- the project pipeline stage breakdown and the company
  financials snapshot (committed/paid/outstanding from Phase 5's CompanyExpense module).
- Frontend: new `DirectorDashboardPanel.jsx`, rendered inside `RootTerminal.jsx` below the
  existing Root/Director dashboard content. Fetches WEEK and MONTH by default (per the
  "default view is week + month, unless the Director changes it" business rule), with
  "+ TODAY" and "+ THIS YEAR" toggle buttons for DAY and YEAR as opt-in extra panels.
- New `getDirectorDashboard()` call in `landService.js`, and new CSS classes appended to
  `Dashboard.module.css` for the period toggle buttons and staff activity rows.
- No DB migration needed -- this phase only reads existing tables (audit_logs, land_projects,
  company_expenses, payment_records).

## PER SECTION 3 (PERMANENT RULE): FULL PIPELINE TEST NOW DUE

Phase 7 was the last item in the recommended build order (Section 17.11). Per the permanent
deferred-testing rule, David should now run ONE comprehensive end-to-end test pass covering
everything at once -- NOT test Phase 7 in isolation. That means:

1. Log in as Root/Admin/Director -> Dashboard -> confirm the new "DIRECTOR'S DASHBOARD"
   section appears below the existing panels, with WEEK + MONTH cards by default, the
   COMPANY FINANCIALS SNAPSHOT panel, and the +TODAY / +THIS YEAR toggles.
2. Log in as a plain Manager -> confirm the Director's Dashboard section does NOT appear.
3. Full Phase 1-7 regression pass:
   - Project index display/search (Ledger)
   - NIN identity checks and duplicate-NIN warning/auto-fill (Intake/Folder)
   - 4-tier role gates (Programmer/Director/Manager/Secretary boundaries)
   - Stage checklist panel on Intake and the Folder page
   - Company Costs page (add cost, record payment, category autocomplete)
   - Legacy Receivables toggle (if entered this session -- see note below)
   - Director's Dashboard itself

**Open question carried forward:** Phase 6 (Legacy Receivables Entry Mode) is listed as the
phase immediately before this one in the build order, but no dedicated simplified single-lump-
sum intake path was found in the current codebase snapshot -- only the pre-existing `isLegacy`
flag from before the revamp. If Phase 6 was not actually shipped yet, it should be built and
tested before (or alongside) confirming Phase 7, since Section 17.11's build order lists it as
a prerequisite in spirit (though not a hard technical dependency for Phase 7 specifically).
Flag this to David directly before closing out testing.

**Once David confirms all of the above:** move the Phase 7 (and Phase 6, if separately
confirmed) entries into Section 17.10's Phase Tracker in the master guide as "APPLIED AND
PUSHED," and clear this section of the addendum entirely, per the permanent session rule.