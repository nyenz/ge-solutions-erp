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

## CURRENT STATUS: REVAMP PHASE 1 -- PROJECT INDEX SYSTEM

CODE WRITTEN. Status per David's last note: not yet confirmed tested. Do not
move to the guide until David confirms he ran it, deployed, and saw a real
index (e.g. "001A") appear on both Ledger and Folder page.

---

## CURRENT STATUS: REVAMP PHASE 2 -- NIN-BASED IDENTITY

CODE COMPLETE. Full review of the repo confirms all pieces are in place:
- Backend: `Client.java` (nationalId field + index), `ClientRepository.java`
  (findByNationalId), `ClientService.java` (findOrCreateClientByNin),
  `ClientController.java` (GET /api/v1/clients/lookup-nin), `LandService.java`
  (atomicIntake + updateProjectFull both require NIN and match by NIN),
  `DataInitializer.java` (unique constraint on national_id, drops old phone
  uniqueness constraint).
- Frontend: `clientService.js` (lookupNin), `IntakePage.jsx` and
  `FolderPage.jsx` (NIN required, duplicate/typo warning, auto-fill on blur).

**David has explicitly said he is NOT testing yet** -- he wants all code
ready across phases first, then a single test pass at the end. So this stays
listed here as CODE COMPLETE / NOT YET CONFIRMED rather than being moved into
Section 10 or Section 17's Phase Tracker. Do not mark Phase 2 as DONE in the
guide until David runs the test plan (blank NIN blocked, duplicate NIN
auto-fill, typo warning, edit-mode required asterisk) and confirms.

---

## CURRENT STATUS: REVAMP PHASE 3A -- ROLE ENUM FOUNDATION

**APPLIED AND PUSHED.** David ran fix.py, `Role.java` updated cleanly with
`ROLE_DIRECTOR` and `ROLE_SECRETARY` added alongside the existing
`ROLE_ADMIN` / `ROLE_MANAGER`, committed and pushed to GitHub
(commit `9f29489`). Purely additive -- no `@PreAuthorize` check anywhere
references the new values yet, so nothing that currently works changed
behavior. Not yet deploy-tested on Render, but this phase carries no runtime
risk since it only adds unused enum values.

**Known limitation (expected, not a bug):** the new roles cannot actually be
assigned to any real permission boundary yet -- that is Phase 3B.

**Next phase queued: Phase 3B -- 4-Tier Role Permission Wiring.**
Will involve: updating every backend `@PreAuthorize` check across all
controllers to use the real 4-tier logic from Section 17.7, and updating
every frontend role check (`user.role === 'ROLE_ADMIN'`, `user.isRoot`, etc.
in Sidebar.jsx, App.jsx, Dashboard.jsx, FolderPage.jsx, ReportHub.jsx, and
more). This is the highest-risk phase per Section 17.10 -- touches security
and access control everywhere. Will be its own dedicated fix.py, written
only when David explicitly says to proceed, per the guide's own rule against
bundling multiple phases into one patch.

**Remaining phases after 3B:** Phase 4 (Stage Templates), Phase 5
(Financials Module), Phase 6 (Legacy Receivables), Phase 7 (Director
Dashboard) -- none started yet.