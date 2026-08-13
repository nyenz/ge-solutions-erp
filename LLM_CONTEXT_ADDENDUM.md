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

## CURRENT STATUS: REVAMP PHASE 5 -- FINANCIALS MODULE (COMPANY COSTS)

APPLIED (fix.py generated this session, not yet run/pushed by David). Shipped as ONE complete
fix.py per the permanent Section 3 rule -- backend (model, repository, service, controller) and
frontend (service, page, route, nav link) all in the same fix.py.

What this phase adds:
- Backend: `CompanyExpense` model (new `finance` module), repository, service, and controller
  at `/api/v1/finance/company-expenses`, restricted to ROLE_ADMIN and ROLE_DIRECTOR only
  (Manager and Secretary have no access, per Section 17.7's role table).
- Uses the same "total committed vs amount paid" pattern already used for client debt
  (LandProject.totalCost / amountPaid), so committed-but-unpaid company costs are visible
  separately from cash actually paid out.
- Category is free-form text (not an enum) with a `/categories` endpoint returning distinct
  past categories, consumed via a `<datalist>` autocomplete on the frontend -- same idea as
  predictionService's district/county suggestions on Intake, but server-backed instead of
  localStorage-backed since expense categories should be shared across staff, not per-browser.
- Frontend: new `CompanyExpensesPage` at `/financials`, new sidebar link "COMPANY COSTS"
  (visible only to Admin/Director/Root, same `hasHighLevelAccess` gate as Payments/Reports).
- Company costs are completely separate and unlinked from any LandProject -- no foreign key,
  no shared totals, per Section 17.8.
- Table is auto-created by Hibernate (`ddl-auto=update`) from the new `@Entity` -- no manual
  DataInitializer migration was needed, consistent with how prior new entities were added.

Deferred testing per the permanent rule in Section 3 -- David's test plan (sidebar visibility
by role, add a cost entry, autocomplete on repeat category, summary cards update correctly,
partial payment reduces outstanding balance correctly, Manager login redirected away from
`/financials`) will be run as part of the single end-to-end pass once Phase 7 is code-complete.

**Next phase queued: Phase 6 -- Legacy Receivables Entry Mode.** Per the permanent rule, this
will ship as ONE complete fix.py covering the full phase. Written only when David explicitly
says to proceed.

**Remaining phases after 6:** Phase 7 (Director Dashboard) -- not started yet.