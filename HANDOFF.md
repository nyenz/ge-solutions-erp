# HANDOFF -- GE SOLUTIONS ERP ("Golden Seed")
# Written 19 Oct 2026, at the end of a long chat, so a NEW chat can carry on with no gaps.
# Read this file first, then LLM_CONTEXT_GUIDE.md (the full guide, kept up to date with every fix).

## 1. Who you are working with
- **David (Nyenz)**, the owner of the repo `nyenz/ge-solutions-erp`. He calls himself a beginner, not a professional.
- The app is the ERP of **GE Solutions**, a Ugandan land-surveying and title-processing company (Busoga region:
  Iganga, Kamuli, ...). The app is branded **Golden Seed** on screen.
- **How he wants to be talked to:** simple English, short, plain click-by-click steps ("press X at the top right").
  No clarifying questions -- make a sensible choice and say what you chose. Do the work first, then a short report.
- **Never** show status numbers ("HTTP 400") or code words ("PLOT_TAKEN") in anything a user of the app reads.
- **No default browser styles anywhere** -- every box, list, button, scrollbar and date picker is custom-styled.
- He likes: tabs, dropdowns, fixed side bars, little scrolling, summaries first with details behind a dropdown,
  gentle animation (things slide/fade, never jump).
- He wants everything automated except data entry: YOU commit, push, open the PR, wait for the checks and MERGE,
  then report when done. He has said many times he is fine with auto-merge.

## 2. The way every change is shipped (do exactly this)
1. `cd ge-solutions-erp && git checkout main && git pull`, then a new branch `fixNNN-short-name` (the last one is **fix213**,
   so the next is **fix214**; fix214 and fix215 were done on 19 Oct afternoon (see the guide), next is **fix222** (fix221 = call-note delete made safe; see KEPT FOR LATER in the guide) (fix220 = call history came back empty) (fix219 = CALL LOG opens read only for resting clients) (fix218 = test pack shows only what is left) (fix216 = explainers, fix217 = Reports PDF + Office default + type-ahead everywhere, done)).
2. Make the change. Frontend checks: `cd erp-frontend && npx eslint src && npm test && npm run build` (57 tests pass).
   The backend cannot be built in the cloud box (no Maven internet); GitHub runs the server tests on every PR.
3. Update `LLM_CONTEXT_GUIDE.md`: add `fixNNN: ...;` at the FRONT of the "# Last updated: October 2026 (" line, and
   a bullet before the line that starts with `- **Not done, waiting for David:**`.
4. Commit message ends with the two trailer lines:
   `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: <the session URL of the new chat>`.
5. `git push -u origin <branch>`; open the PR with
   `gh api repos/nyenz/ge-solutions-erp/pulls -f title=... -f head=<branch> -f base=main -F body=@pr.md`
   (the body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)` and the session URL).
6. Wait for the check runs (`gh api repos/nyenz/ge-solutions-erp/commits/<branch>/check-runs`) to be
   completed:success, then merge: `gh api -X PUT repos/nyenz/ge-solutions-erp/pulls/<N>/merge -f merge_method=merge`.
7. `git checkout main && git pull`. Render deploys by itself in a few minutes.
- **Never wipe app data.** David's test data lives in the live database.

## 3. The app in one page (details: LLM_CONTEXT_GUIDE.md)
- Spring Boot 3.2.5 (`erp-backend`) + React 19 / Vite / CSS Modules (`erp-frontend`).
- Hosting (free plans): Render -- server `ge-solutions`, website `golden-seed` (https://golden-seed.onrender.com);
  Neon Postgres; Cloudinary for files. The free server sleeps; the pages retry while it wakes (fix210).
- Five ranks: Employee < Secretary < Manager < Director < Admin. Test logins: `test.secretary`, `test.manager`,
  `test.director` (David has the keys).
- Eight project types; Clients (who pay) + Owners (on the title) + Neighbours; Stages; Documents with types;
  Pending projects; Payments; Receivables + storage fees; Recovery calls; Reports; Audit; Settings.
- Money rights: the receivable buttons (MOVE TO RECEIVABLES, SAVE RATE, PAUSE/RESUME FEES, REDUCE FEES, SET ASIDE,
  ADD FEES TO COST, WAIVE FEES) are Director only; payments and COLLECT SET-ASIDE FEES are Manager and above.
- Recovery: LOCKED = paid in the last 30 days or 2 good calls in 30 days; SITE = 4 missed days in 30 days.
  Call tags: answered, not picking up, not going through, wrong number. Manager+ can delete a call note.

## 4. What was done in this chat (fix207 -> fix213), newest first
- **fix213:** a plot number is only taken in the SAME block + district (`PlotNumberGuard`; the old system-wide unique
  rule is dropped at start-up). No "plot ID" wording. A refused form now marks the wrong box (soft red ring, red label,
  small nudge), scrolls to it and puts the cursor in it -- `erp-frontend/src/utils/fieldError.js`
  (`flagField`, `flagId`, `flagServerError`). Used on New Project, Folder EDIT (opens the right tab), the Titled pop-up
  and the Pending page. **Any new form should use it.**
- **fix212:** PRINT button on the Client page -> a "Client File" in the same layout as the Project File
  (`components/print/ClientFilePrint.jsx`, money only for Director+). Transfer of a subdivision plot: the Client is NOT
  copied, Owners + Location are; Title Date starts empty with an "Original title: ..." line under it.
- **fix211:** the orange background no longer prints as a block at the end of the Project File.
- **fix210:** David's saved notes: boxes no longer stretch alone, lists retry while the server wakes, type-ahead in every
  pick-list, a typing box in the calendar, documents typed like a stage show under that stage, paperclip on New Project
  stages, Dashboard rows sized by panel count, the Project File print redone in his "case study" look.
- **fix208:** popup buttons spaced; the hover-help bubble readable in Light mode; toasts readable.
- **fix207:** company colours on the printed Project File.

## 5. The manual test (Round 1) -- where David is
- **Test pack page:** https://claude.ai/artifact/MvDzEYDPtWGu58GBr92HfF (version 12: only-what-is-left view, results built in via SAVED). Source copy:
  `docs/testing/round1-fresh-survey.html`. Sections **A to Q** -- **never reorder or rename the step ids**: David's
  ticks are kept in that page's browser storage by step id. To change the pack, READ the artifact first, edit, and
  publish to the SAME url.
- **Results so far (19 Oct 2026):** 99 passed, 0 failed, 31 not done:
  N2-N12, O1-O9, P1-P8, Q1-Q6. (N1 is done.)
- **19 Oct afternoon:** N passed in full; David is on **O. Recovery calls**. fix216 (next) = hover explainers on every tab, filter, column heading and small button + Settings > Appearance > Hover explainers OFF must hide the browser's own titles too.
- **He starts again at section N. "Storage fees and receivables (a Legacy Title)"**, step N2 (finishing N1's save):
  in N1 the plot number was changed from 214 to **316** (214 was already on project 001A; with fix213 a different
  block would now also be allowed).
- Test files to upload: `docs/testing/golden-seed-test-files-NOP.zip` (N1-copy-of-title.pdf, N-receipt-01.jpg,
  N-receipt-02.jpg, R1-application-form.pdf, R1-receipt-01.jpg) and `docs/testing/golden-seed-test-files.zip`
  (the earlier P1/P2/S1 files).
- When he sends results, save them in LLM_CONTEXT_GUIDE.md ("Test progress saved") and in memory.

## 6. Open items (not started unless David says so)
- **THEMES -- TABLED.** Four themes: A (today's look), **B "GES Daylight" = the new DEFAULT**, C "GES Charcoal", plus the
  current Light mode. Built from the GES website (repo `nyenz/ges-website`): orange #ea580c (hover #c2440a),
  charcoal #1f2937, body text #4b5563, cream #fdfaf4, Poppins, pill buttons, soft lifts. The printed Project File and
  Client File will then use the website colours too. Comparison page (all 9 pages x A/B/C/D, scroll + zoom + Pick):
  https://claude.ai/artifact/TZgKyTqCtANzT4pFDG6ScY (source: `docs/design/erp-design-comparison.html`).
  D (the first, lighter Daylight) is dropped. Later David wants a second theme study based on today's Settings page.
- **Hosting move** (Netcup VPS Lite 1 was the pick; Hetzner CX was not available): brainstorm only. Do NOT start until
  David says "move now". He also floated an in-house/offline mode with a portable SSD -- brainstorm only.
- **Before go-live:** remove the FRESH START tick box, reset the Neon password, make the repo private.
- Waiting for David: Dashboard look notes (note 5), "D1 - I want all entries" (note 18), Secretary + Pending tile (note 2).
- Still TO DO in code: the STAGE/STATUS rename inside the code and database (fix184 note).

## 7. Other projects of David (not this repo, for context only)
GES website (`nyenz/ges-website`, the company site), a Three.js portfolio, a video-editing app (EditForge), a code-built
video kit, a CPU comparison app, an azolla farm plan. Do not touch them unless asked.
