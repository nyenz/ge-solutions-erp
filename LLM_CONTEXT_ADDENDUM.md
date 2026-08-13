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

## PERMANENT RULE CHANGE THIS SESSION (now moved to guide Section 3 -- not repeated here)

Two fix.py workflow rules were confirmed as permanent this session and written directly into
Section 3 of LLM_CONTEXT_GUIDE.md (per the exception process already established for Section 17):

1. Each phase ships as ONE complete fix.py covering the entire phase -- no more splitting a
   single phase into 4A/4B/4C-style sub-parts.
2. Testing happens only after ALL planned phases in the current rebuild are code-complete --
   never after each individual phase.

This replaces the old "TESTING APPROACH CHANGE (August 2026)" note that was previously here.
That note is now fully superseded and has been removed from this file -- the rule it described
is now the permanent, standing process (see guide Section 3), not a one-off session decision.

---

## CURRENT STATUS: REVAMP PHASE 1 -- PROJECT INDEX SYSTEM

APPLIED AND PUSHED. Deferred testing per the permanent rule above -- will be tested together
with all other phases once Phase 7 is code-complete, not before.

---

## CURRENT STATUS: REVAMP PHASE 2 -- NIN-BASED IDENTITY

CODE COMPLETE, APPLIED AND PUSHED. Deferred testing per the permanent rule above.

---

## CURRENT STATUS: REVAMP PHASE 3 -- 4-TIER ROLE SYSTEM (3A + 3B + 3C)

APPLIED AND PUSHED (all three sub-parts). Deferred testing per the permanent rule above.

Known limitation (flagged, not fixed): the promote/demote arrow button on each operator card
only toggles between ROLE_ADMIN and ROLE_MANAGER. If clicked on an existing ROLE_DIRECTOR
account, it will demote them to ROLE_ADMIN. A proper 3+ tier rank selector was out of scope for
that patch. Can be a small standalone fix.py later, or folded into a future governance UI pass.

---

## CURRENT STATUS: REVAMP PHASE 4 -- STAGE TEMPLATE SYSTEM (BACKEND + FRONTEND)

APPLIED AND PUSHED, including this session's correction patch (commit `be47aa1`) which
inserted the STAGES panel into IntakePage.jsx between FINANCIALS and DOCUMENTS -- the one
piece that was missing after the original patch's anchor mismatch. That patch showed OK
against the confirmed real file content, so it landed correctly.

What is now live end-to-end:
- Backend: `StageTemplate` / `ProjectStage` models, master template CRUD, per-project stage
  attach/toggle-complete/edit-cost/remove, default 6 stages seeded once on startup.
- Frontend: IntakePage STAGES panel (checkbox list + custom stage "+" add), FolderPage STAGE
  CHECKLIST panel (view/edit/add stages on an existing plot).
- The OLD hardcoded 5-stage pipeline dots on FolderPage remain untouched and working exactly
  as before -- the two systems intentionally coexist for now (see Section 17.5 / 17.10 in the
  guide for the reasoning).

Deferred testing per the permanent rule above -- David's test plan (check STAGES panel appears
on New Plot, check 2 stages + add a custom one, submit, confirm STAGE CHECKLIST shows them on
the folder page, confirm old pipeline dots still work) will be run as part of the single
end-to-end pass once Phase 7 is code-complete.

**Next phase queued: Phase 5 -- Financials Module (Company Costs).** Per the new permanent
rule, this will ship as ONE complete fix.py covering the full phase (backend models, service,
controller, and frontend page/service together) -- not split into parts. Written only when
David explicitly says to proceed.

**Remaining phases after 5:** Phase 6 (Legacy Receivables), Phase 7 (Director Dashboard) --
neither started yet.