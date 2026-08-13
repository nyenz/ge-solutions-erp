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

## TESTING APPROACH CHANGE (August 2026)

**David has explicitly decided to defer testing of everything from Phase 3B onward until
all currently-planned phases are code-complete**, rather than testing each phase individually
before the next fix.py is written. This is a deliberate deviation from the project's own rule
in Section 3 ("Each phase must be confirmed working by David before the next phase's fix.py
is written").

Practical effect: multiple phases will show "APPLIED, NOT YET TESTED" simultaneously in this
addendum for a while. This is expected and intentional, not an oversight. Do not flag it as
a rule violation in future sessions -- David made this call knowingly, aware that it means
if something breaks, more phases will need to be checked to isolate the cause.

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

NOT YET CONFIRMED -- part of the deferred end-of-all-phases test pass.

---

## CURRENT STATUS: REVAMP PHASE 3A -- ROLE ENUM FOUNDATION

APPLIED AND PUSHED. `Role.java` updated cleanly with `ROLE_DIRECTOR` and
`ROLE_SECRETARY` added alongside `ROLE_ADMIN` / `ROLE_MANAGER`. Purely
additive -- no runtime risk, nothing that currently works changed behavior.

NOT YET CONFIRMED -- part of the deferred end-of-all-phases test pass.

---

## CURRENT STATUS: REVAMP PHASE 3B -- 4-TIER ROLE PERMISSION WIRING

APPLIED AND PUSHED (commit `6281f23`). fix.py ran clean -- every patch
showed OK, no MISSING/FAIL. Wires ROLE_DIRECTOR into every place that
currently grants ROLE_ADMIN full/financial access, at both controller and
service layer, across AuditController, DashboardController, LandController,
PaymentController, RecoveryController, ClientController, ReportController,
LandService, plus the frontend gates in App.jsx, Sidebar.jsx, Dashboard.jsx,
FolderPage.jsx, ReportHub.jsx.

ROLE_SECRETARY still intentionally not wired anywhere (see Phase 4 note
below -- the stage/cost separation Secretary needs is now partly built in
Phase 4A).

NOT YET CONFIRMED -- part of the deferred end-of-all-phases test pass.

---

## CURRENT STATUS: REVAMP PHASE 3C -- SETTINGS UI DIRECTOR OPTION

APPLIED AND PUSHED (commit `8b862b3`). Added ROLE_DIRECTOR as a selectable
option in the "INITIALIZE IDENTITY" provisioning modal's rank dropdown in
`SettingsPage.jsx`, and updated the operator card label to show
"TIER 2: DIRECTOR" instead of falling through to "TIER 3: OPERATOR".

**Known limitation (flagged, not fixed):** the promote/demote arrow button
on each operator card only toggles between ROLE_ADMIN and ROLE_MANAGER. If
clicked on an existing ROLE_DIRECTOR account, it will demote them to
ROLE_ADMIN. A proper 3+ tier rank selector was out of scope for this quick
patch. If this needs fixing before the end-of-phases test pass, flag it as
a small standalone fix.py -- otherwise it can wait and be handled as part
of a later governance UI pass.

NOT YET CONFIRMED -- part of the deferred end-of-all-phases test pass.

---

## CURRENT STATUS: REVAMP PHASE 4A -- STAGE TEMPLATE BACKEND FOUNDATION

CODE WRITTEN, NOT YET APPLIED. David has not run fix.py for this phase yet.

Adds (all additive, backend only):
- `StageTemplate.java` / `ProjectStage.java` models (new tables, created
  automatically by Hibernate ddl-auto=update, no manual SQL).
- `StageTemplateRepository.java` / `ProjectStageRepository.java`.
- `ProjectStageRequest.java` DTO.
- `StageTemplateService.java` -- master template CRUD, per-project stage
  attach/toggle-complete/edit-cost/remove. `toggleStageCompletion()` is
  deliberately kept separate from `updateStageCostAndNotes()` so a future
  Secretary rollout can be wired to the stage-only action without ever
  reaching the cost-edit method (see Section 17.7).
- `StageTemplateController.java` -- REST endpoints under `/api/v1/stage-templates`
  and `/api/v1/land/projects/{id}/stages`.
- `stageTemplateService.js` -- frontend API wrapper only, no UI yet.
- `DataInitializer.java` patched to seed the 6 default stages (Field Work,
  Deed Plan, LC Inspection, District Land Board Approval, Tax Assessment
  and Stamp Duty, Registration and Title Issuance) once, on first startup,
  if the table is empty.
- `LandEntryRequest.java` / `LandService.java` patched so intake can
  optionally attach a stage checklist -- entirely optional, existing
  intake behavior unchanged if omitted.

**Explicitly NOT touched:** IntakePage.jsx (no checkbox/"+" custom stage UI
yet), FolderPage.jsx (still uses the old hardcoded 5-stage STAGE_LABELS
pipeline, untouched, still works exactly as before). That is Phase 4B, a
separate dedicated fix.py, since it is large enough JSX restructuring that
patching it blind via text anchors carries real risk of a bad patch landing
silently -- same caution that applies to any large frontend rewrite in this
project.

ROLE_SECRETARY still not wired into any `@PreAuthorize` check anywhere,
consistent with the standing decision from Phase 3A/3B.

**Next phase queued: Phase 4B -- Stage Template UI (Intake + FolderPage).**
Will build the checkbox + "+" custom-stage picker on Intake, per-stage
cost/notes fields, and replace FolderPage's hardcoded `STAGE_LABELS` /
5-stage pipeline with a dynamic display driven by `ProjectStage` records.
Written only when David explicitly says to proceed, per the guide's own
rule against bundling multiple phases into one patch.

**Remaining phases after 4B:** Phase 5 (Financials Module), Phase 6
(Legacy Receivables), Phase 7 (Director Dashboard) -- none started yet.