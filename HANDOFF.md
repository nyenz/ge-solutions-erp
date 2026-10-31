# HANDOFF -- GE SOLUTIONS ERP ("Golden Seed")
# Written 19 Oct 2026; final state and finish line added 30 Oct 2026 (fix281). A NEW chat can carry on with no gaps.
# Read this file first, then LLM_CONTEXT_GUIDE.md (the full guide, kept up to date with every fix).

# ===== FINAL STATE AND FINISH LINE, 30 Oct 2026 (newer than everything below: read this first) =====
## Where things stand
- **REAL app:** David's own Netcup VPS (Debian 13, 4 GB, 80 GB) at **https://ges-erp.duckdns.org** (IP 62.83.77.55). Docker:
  db + backend + frontend + Caddy (HTTPS). Everything is in `infra/` and guide section 18. Fresh, empty database (David's
  choice). Root login `admin_root` (David changed its key). Secrets only in `/opt/ges/infra/.env` on the server.
- **DEMO app:** Render + Neon + Cloudinary with the old test data; shows a DEMO strip; FRESH START exists only there. It
  rebuilds by itself on every merge. It stays as the practice copy.
- **Documents** on the server disk (`GE_SOLUTIONS_STORAGE=local`, `VaultController`, login needed).
- **Backups:** nightly 02:00 on the server (14 days + documents); locked Google Drive copy once David runs `setup-offsite.sh`;
  root-only BACKUP button (ZIP or folder) in Settings; `restore-test.sh` / `restore-backup.sh`.
- **Updates (SAFE UPDATE, fix276):** merge to main (checks green), then on the server `bash /opt/ges/infra/deploy.sh`: safety copy
  first, build, health checks, automatic rollback. Undo: `bash /opt/ges/infra/rollback.sh`.
- **PERMANENT RULE (David): no update may ever break the app or lose data** (guide section 13). Never weaken deploy.sh.
  Data changes additive only; anything else needs David's yes and a trial on a copy.
- **Built this week:** fix269-275 server move, fix276 safe update, fix277 guide matches the app, fix278 cleanup + DEMO strip,
  fix279 owner key recovery by email (off until set up), fix280 MIDNIGHT theme (replaces GES NAVY; version A in the app,
  David may still pick B or C on the comparison page -- then only the colour values change: `scripts/build-gesday.mjs` with
  MIDNIGHT_HUE/SAT/BASE and the gesnavy block in index.css), fix281 payment words readable in CLASSIC/SLATE/MIDNIGHT + this list.
- **Working with David:** load the skill `nyenz-app-design` first. One server step = ONE paste, say what he should see. He types
  secrets only in the server terminal. I cannot reach the server from the cloud box (port 22 blocked).
- **Shipping a change:** section 2 below; next number **fix285**; commit trailers = the session's attribution reminder.

## THE FINISH LINE (everything left, in order). When all of A and B are ticked, the app is DONE and live.
### A. David's own steps -- STATUS 30 Oct 2026 (afternoon): DONE = 1 server updated (deploy.sh --force path found a bug, fixed in fix282), 2 upload test, 3 BACKUP ZIP saved,
### 4 Google Drive locked copy working (scope drive.file, passphrase in his password manager), 5 restore test passed (copy = live: 1 user, 1 project, 22 tables),
### 6 Netcup server panel passkey + phone code, Netcup customer panel phone code, phone app backup on (Gmail backup codes SKIPPED by David),
### 7 UptimeRobot monitor Up, 10 MIDNIGHT A kept. SKIPPED BY DAVID: 8 April reminder, 9 optional extras, Part 3 test-data clean-up.
### LEFT: 11 staff accounts and use the live app. David will go live now and report problems at the first real entry; do NOT ask him to repeat tests.
### The original list (kept for reference):
1. Update the server: `cd /opt/ges && git pull && bash infra/deploy.sh` (brings fix276-282; later just `bash /opt/ges/infra/deploy.sh`). fix282: deploy.sh now knows what is really RUNNING (`infra/.deployed-commit`), so a plain `git pull` first can no longer make it say "nothing new" (it did on 30 Oct and skipped the build).
2. Test on the real site: make a client + project, upload a PDF and a photo, open them, delete one.
3. Settings > BACKUP: save one ZIP to the computer and open START HERE.html.
4. Google Drive copy: Part A on the PC (`rclone authorize "drive"`), Part B on the server `bash /opt/ges/infra/setup-offsite.sh`.
5. Once some real data is in: `bash /opt/ges/infra/restore-test.sh` (proves the backup really restores).
6. Phone safety: Netcup passkey or second login, Gmail backup codes, authenticator backup.
7. UptimeRobot (free) alert on https://ges-erp.duckdns.org.
8. Reminder for mid-April 2027: Netcup contract renews by itself unless cancelled 31+ days before the end.
9. Optional: owner email recovery (remove "netcup Mail Block" in the Netcup panel, `bash infra/setup-mail.sh`, then
   Settings > Security > Recovery email). Optional: make the GitHub repo private (then check Render still deploys).
10. Pick MIDNIGHT A, B or C (A is already in).
11. Staff accounts on the real app, then a last walk-through by David before real data goes in.

### B. Build work still open from the old review (docs/APP_REVIEW.md section 4, checked against the code on 30 Oct)
ALL FIVE DONE in fix284 (1 Nov 2026): B1 Archive tab in Settings lists deleted documents/notes/expenses (archived_items, 90 days, nightly purge 02:45), B2 SUSPEND asks first, B3 utils/format.js, B4 utils/projectNumbers.js, B5 config/StartupSecretGuard.java.
Must do before real client data (small, safe, additive):
- B1 **Archive for deleted documents, notes and expenses, 90 days, a Director can restore** (Q5 = A; today only whole
  projects go to the Archive). medium.
- B2 **Ask before SUSPEND** on Settings > Staff (today one tap suspends; P10). small.
- B3 **One date style and one money style** everywhere (P23/P24: Expenses still shows the device style "10/30/2026, 7:18 AM"). medium.
- B4 **Invoice and contract numbers on Payments rows and the client page project table** (16b). small.
- B5 **Server refuses to start with the public fallback secrets** when demo data is off (S04/S05). The real server already has
  strong secrets, so this is a guard for the future. small.
Can wait until after go-live (only if David wants them):
- B6 Special Projects with their own goals and CLOSE PROJECT (Q4, section 5.1) -- only when the first special job comes. big.
- B7 Place-name suggestions for the Employee (P33). small.
- B8 A screen for the master stage lists (P32). medium.
- B9 The remaining server tidy-ups S06-S28 (stage chart movement, double-send guards, extra checks and audit lines) -- re-check
  each in the final walk-through; most were covered by fix190-fix241, fix only what still shows.
Dropped (recommend NOT doing): the deep Stage/Status rename in the database (users never see it, and renaming tables risks the
data -- against the permanent rule). Already done, removed from the list: hosting move, private files, Employee edits own
Pending entry, Secretary rights, date typing in the calendar, error sentences, field errors, popups with one X, explainers.

### C. Ideas only (not promised): "update tonight" banner for staff, his own domain name, SSH key login to the server.
# ===== END FINAL STATE =====

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
- **HOSTING MOVE -- DONE (30 Oct 2026), see CURRENT STATE at the top. (Old text, kept for history:)** The whole app (Render + Neon + Cloudinary) moves onto ONE rented server:
  **Netcup VPS Lite 1 G12.5s** -- 2 vCore, 4 GB RAM, 80 GB SSD, IPv4 included, **EUR 4.92 a month on a 6-month
  contract (EUR 29.52 paid at once, about EUR 59 a year)**, no setup fee, Ubuntu 24.04, free DuckDNS address first.
  Hetzner's cheap servers could not be ordered (14 Oct 2026). Move only BEFORE real client data goes in, and only when
  David says "move now". Full details, the agreed step-by-step walkthrough, costs, risks and the rejected options are in
  **LLM_CONTEXT_GUIDE.md section 18.0** -- read it before answering any hosting question.
- **IN-HOUSE MODE -- brainstorm only:** if his employer wants the app in the office, one office computer runs it for
  everyone on the Wi-Fi, with a "storage mode: Cloud or Disk" setting and a portable SSD as the backup disk.
  Guide section 18.0a. Not started.
- **Before go-live:** remove the FRESH START tick box, reset the Neon password, make the repo private.
- Waiting for David: Dashboard look notes (note 5), "D1 - I want all entries" (note 18), Secretary + Pending tile (note 2).
- Still TO DO in code: the STAGE/STATUS rename inside the code and database (fix184 note).
- **Earlier design board** (the first try at the comparison, a canvas): https://claude.ai/artifact/EvmVcSKuo5WKaGKb7Hxnht --
  replaced by the scrolling comparison page above; keep only for reference.
- **If the live site will not open for David:** the free Render app sleeps (wait one full minute, then reload). His own
  computer once had a DNS problem (Brave "Secure DNS" / Windows DNS); switching Brave's Secure DNS to another provider
  fixed it.

## 7. Other projects of David (not this repo, for context only)
GES website (`nyenz/ges-website`, the company site), a Three.js portfolio, a video-editing app (EditForge), a code-built
video kit, a CPU comparison app, an azolla farm plan. Do not touch them unless asked.
