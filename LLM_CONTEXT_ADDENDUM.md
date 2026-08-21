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

## CURRENT STATUS: STAGES 5, 6, 7 -- awaiting confirmation (run in this order)

David asked for a full read of the repo and a code-cleanup pass for naming/wording
consistency, plus a check of the app's end-to-end flow. Three fix.py scripts came out of
this session, meant to be run in order.

### Stage 5 -- app-name branding cleanup (NYENZ vs Golden Seed)
Fixed the Sidebar footer branding text/aria-label and every downloaded report CSV filename
(both said "NYENZ", rest of the app says "Golden Seed"). Normalized ~17 internal-only
"NYENZ ERP" code comments and 2 boot-log lines too. Added a code comment explaining why the
4 backlog_* DB columns were deliberately not renamed (see "still open" below).

### Stage 6 -- RECEIVABLE -> RECEIVABLES wording
David got 3 outside candidate scripts and asked for a comparison against a real clone.
Two were rejected (one was mostly a no-op with one label regression; the other conflated
the "Recovery Hub" call-tracking feature with the "Receivables" payment-status concept and
re-attempted the same unsafe DB rename Stage 5 already declined). The third correctly
spotted a real gap: per Section 17.2, RECEIVABLE (singular) and RECEIVABLES (plural) are two
different statuses, and since the new singular status isn't built anywhere yet, every
"RECEIVABLE" on screen today is really the old backlog concept and should read RECEIVABLES.
That script's coverage was incomplete though -- Stage 6 is the full 34-patch sweep across
RecoveryPortal, LedgerPage, IntakePage, FolderPage, PaymentsPage, ReportHub, and
ManagerTerminal. Tested clean against a clone: 34/34 applied, zero singular "RECEIVABLE"
left anywhere user-facing afterward.

### Stage 7 -- the 3 "still open" items, actually resolved (not deferred this time)
David pushed back on leaving these as open decisions instead of just fixing them. Checked
each properly:
- **Raw `<select>` on ExpensesPage** -- confirmed only 1 exists anywhere in the app (not 5 as
  first estimated). Did NOT swap it for the shared HardwareSelect component -- checked its
  CSS and it renders a solid white box with a stacked label, which would visibly clash with
  ExpensesPage's flat, unlabeled, dark filter row. Instead: a scoped CSS-only patch
  (`appearance: none` + a custom SVG arrow) that hides the native browser chrome and matches
  the existing dark style, with zero JS/logic change.
- **Notification model "needs a feature decision"** -- checked every .java file in the
  backend for any reference to it outside its own folder. Zero. No controller, no scheduled
  job, nothing autowires it. It isn't a half-built feature waiting on a decision, it's 3
  files (model/repository/service) that do nothing and are called from nowhere -- deleted.
  Confirmed nothing else in the backend imports those classes before removing them.
- **"No dedicated Legacy Receivables intake flow"** -- this was a mistake in the last
  version of this addendum. Re-checked IntakePage.jsx directly: the isLegacyMode toggle
  (STANDARD PROJECT vs LEGACY RECEIVABLES) already IS that flow -- there's a code comment on
  it citing Section 17.6 by name. Nothing to build. No patch, just correcting the record.

**Nothing left open from this session.** All three fix.py scripts (Stage 5, 6, 7) have been
test-run against a clean clone with zero MISSING patches. Once David confirms he's happy
with all three, they get folded into the master guide and this whole addendum clears out.