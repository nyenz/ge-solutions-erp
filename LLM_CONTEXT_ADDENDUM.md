# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# This file receives all small incremental updates each session.
# Once confirmed done by David, items are erased from here and folded
# into LLM_CONTEXT_GUIDE.md (Sections 10/11, or Section 17's Phase
# Tracker for revamp work specifically).
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

**What this is:** The first phase of the major ERP revamp. Full architecture and all future
phases are documented permanently in `LLM_CONTEXT_GUIDE.md`, Section 17. This addendum entry
only tracks the current in-progress phase.

**What was built:**
- `ProjectIndexService.java` -- generates project index codes in the format 001A, 002A ...
  999A, then rolls to 001B, 002B ... 999B, then 001C, etc.
- Database migration: new `project_index_counter` table, new `project_index` column on
  `land_titles` (unique constraint).
- `LandService.atomicIntake` now auto-assigns an index to every new project at intake.
- `LedgerPage.jsx`: index is now searchable, and displayed next to the plot number in the table.
- `FolderPage.jsx`: index is now displayed in the project header.

**Status: CODE WRITTEN AND GIVEN TO DAVID. NOT YET APPLIED.**
David has not run this fix.py yet. Nothing described above exists in the live codebase yet.
Do not treat any of it as done. Do not move anything into the guide until David confirms:
1. He ran fix.py and all patches showed OK
2. He pushed to GitHub and Render redeployed successfully
3. He created a test plot and saw a real index (e.g. "001A") appear correctly on both the
   Ledger page and the Folder page

**Known limitation to expect (not a bug):** existing/old plots will show a blank index until
they are opened in edit mode and re-saved. This is fine for Phase 1.

**Next phase queued after this one is confirmed:** Phase 2 -- NIN-Based Identity (see Section
17.10 in the guide for full detail on what that involves).