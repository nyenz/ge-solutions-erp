# HANDOFF -- GE SOLUTIONS ERP ("Golden Seed")
# Written 19 Oct 2026, at the end of a long chat, so a NEW chat can carry on with no gaps.
# Read this file first, then LLM_CONTEXT_GUIDE.md (the full guide, kept up to date with every fix).

# ===== CURRENT STATE, 30 Oct 2026 (newer than everything below: read this first) =====
- **The app now runs on David's own Netcup VPS** (Debian 13, 4 GB, 80 GB) at **https://ges-erp.duckdns.org** (IP 62.83.77.55).
  Everything lives in `infra/` and the guide's section 18: `server-setup.sh` (one time), `deploy.sh` (clone/update + build +
  start), `docker-compose.prod.yml` (db, backend, frontend, Caddy = HTTPS; only ports 80 and 443 open), `nightly-backup.sh`
  + `setup-backups.sh` (02:00 copy, 14 days, plus the documents), `setup-offsite.sh` (locked nightly copy to Google Drive via
  rclone crypt, David runs it once), `restore-test.sh` (proves a copy restores), `restore-backup.sh` (EMERGENCY restore).
- **The new database is FRESH and EMPTY** (David's choice: no copy from Neon). Root login = `admin_root`; its first key was made on
  the server (`infra/.env`) and David changed it at first sign-in. Secrets live only in `/opt/ges/infra/.env` on the server.
- **Documents are saved on the server's own disk** (`GE_SOLUTIONS_STORAGE=local`, `LocalStorageServiceImpl`, `VaultController`,
  login needed to open). Render keeps Cloudinary (the default when the setting is absent).
- **Render + Neon still run as the PRACTICE copy** with the old test data. They are switched off at go-live. Render rebuilds by
  itself on every merge; the Netcup server changes only when David runs `bash /opt/ges/infra/deploy.sh` (quiet hour, tell staff).
- **I cannot reach the server from the cloud box** (port 22 is blocked). David pastes the one command each time; keep every
  server step to ONE paste and say what he should see afterwards. David types secrets only in the server terminal, never in chat.
- **Shipping a change** is the same as section 2 below, except: the next number is **fix279** (fix269-fix277 were the Netcup
  work, the safe update, the guide match and the fix278 cleanup + DEMO setting), commit trailers are whatever the session's attribution reminder says (not the Opus line in section 2), and after
  merge David updates the server.
- **David's rules for the next chat:** load the saved skill `nyenz-app-design` first (his design and working rules).
- **Open, in this order:** (1) David tests uploads + the BACKUP button on the new site; (2) David runs `setup-offsite.sh` (Google
  Drive); (3) David's own safety jobs: Netcup passkey, Gmail backup codes, UptimeRobot alert, reminder for mid-April 2027
  (the Netcup contract renews by itself, card saved); (4) repo cleanup DONE (fix278); FRESH START + DEMO strip only on the demo DONE (fix278); still open: make the repo private (David checks in Render that it can still read it). Render + Neon STAY as the demo. ASK FIRST for anything else. (5) Only if he wants: email recovery for the root key (free: Gmail or a free mail
  relay, after removing the "netcup Mail Block" policy in the Netcup panel), the "update tonight" banner, MIDNIGHT dark theme
  (replaces GES NAVY, same rules as GES DAY), his own domain. ADMIN_RESET_ONCE=true in `infra/.env` + `deploy.sh` is the
  emergency way back in for root (remove the line afterwards).
- **PERMANENT RULE (David): no update may ever break the app or lose data** (guide section 13). `deploy.sh` now takes a safety copy first, checks health and rolls back by itself; `rollback.sh` is the one-line undo. Never weaken it. Data changes: additive only, David's yes + trial on a copy.
- **The guide was matched to the live app in fix277** (current-state box at the top, section 10 deploy steps, SUPERSEDED notes on fix.py / Cloudinary / Hetzner / go-live list). Keep it true: every fix updates it, code wins.
# ===== END CURRENT STATE =====

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
