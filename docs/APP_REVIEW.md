# APP REVIEW -- GOLDEN SEED ERP

Written: 6 October 2026 (fix189). Last change: fix190. Written in simple English on purpose.

This is a full check of the whole app after fix183 to fix188.
It lists what is wrong, what was fixed, what is still to do, and the questions only David can answer.

---

## 0. HOW THIS REVIEW WAS DONE (READ THIS FIRST)

**What was checked**

- Every page was opened and photographed with made-up data: 20 screens x 5 ranks, on a phone size (390 wide) and a
  laptop size (1366 wide), in the 3 themes (CREAM, SLATE, LIGHT). About 180 pictures.
- Each picture was also checked by a script for: text cut off, things off the side of the screen, buttons too small
  to tap.
- All the page code (frontend) was read for workflow faults, wrong words, popups, and rank rules.
- All the server code (backend) was read for rank rules, data leaks, money rules, audit lines and unsafe settings.

**What could NOT be checked (being honest)**

| Not checked | Why | What it means |
|---|---|---|
| The real server running | This workspace cannot download the Java build tools (Maven is blocked) | Server faults below come from READING the code, not from running it. The 91 server tests were not run here. |
| The live site with real data | The live site address is blocked from this workspace | Pictures use made-up data from a small fake server. A fault that only shows with real data can be missed. |
| A real phone | Only a phone-sized browser window was used | The keyboard, the browser bars and finger scrolling still need David's phone. |
| Render settings and Cloudinary settings | They are not in the repo (correct) | Items S04 and S05 depend on them. David must look. |

**How bad** means: **high** = can lose data, show data to the wrong person, or give a wrong money number.
**medium** = a real problem in daily work. **low** = untidy, confusing, or a small risk.

**Sure?** means: **sure** = seen plainly in the code. **likely** = the code says so but it was not run.

Screenshots are in `docs/review-shots/`. "code" in the screenshot column means the fault was found by reading code
and has no picture.

---

## 1. FINDINGS

IDs: **P** = found in the pages (frontend). **S** = found in the server (backend).

### 1.1 High

| ID | Where | What is wrong | How bad | Sure? | Screenshot |
|---|---|---|---|---|---|
| S01 | Server: saving a project entry (`LandService` person rows, `PendingProjectService`) | An **Employee** who types a National ID and name that match a client already in the system gets that client's phone, email and home address back in the answer. The Employee's entry can also **replace** that client's phone, email and address. A Secretary is blocked from doing this on the client page, so the lowest rank can do more than a higher one. | high | likely | code |
| S02 | Server: file storage (`CloudinaryStorageServiceImpl`) | Every uploaded file (title scan, receipt, ID copy) is stored as a **public link**. Anyone who has the link can open the file without signing in, for ever, even after the staff account is switched off or the project is deleted. | high | sure | code |
| S03 | Server: New Project and Pending uploads | The file-type check is **skipped** for files uploaded with a new project. Any kind of file is accepted, up to 50 MB each. (The Folder upload does check.) | high | sure | code |
| S04 | Server: `application.properties` | The repo holds **fallback values** for the token secret, the database password and the first admin password. If a setting is missing on the host, the server starts quietly with those known values. (The values are not repeated here.) | high if a setting is missing | sure about code; Render not seen | code |
| S05 | Server: file storage settings | If the Cloudinary settings are missing, uploads are **thrown away silently**: the page says "saved" but nothing is stored. This includes payment receipts. These settings are not in the go-live checklist. | high if not set | sure about code; Render not seen | code |
| P01 | Reports page, the WHEN buttons | Report periods are **one day early** in Uganda. "LAST MONTH" in October gives 31 Aug to 29 Sep. "THIS MONTH" starts on 30 Sep. Money totals, CSV and PDF are all affected. Cause: the dates are changed to London time before use. **FIXED in fix190.** | high | sure | reports-phone.jpg |
| P02 | New Project page, SAVE PROJECT | After a good save the button works again for about 1 second before the page moves on. A second tap saves a **second copy** of the project. **FIXED in fix190.** | high | sure | new-project-money-phone.jpg |
| P03 | Pending project view | The office must START or REJECT an entry **without seeing its documents, notes or stages**. The Pending view shows only place, title and people. The Employee also never sees what they uploaded. | high | sure | pending-view-phone.jpg |

### 1.2 Medium

| ID | Where | What is wrong | How bad | Sure? | Screenshot |
|---|---|---|---|---|---|
| S06 | Server: Dashboard "projects by type and stage" | The count never moves. It reads a number that is only set when the project is created. Ticking stages does not change it. The demo data sets it by hand, which hides the fault. | medium | sure | dashboard-admin-desktop.jpg |
| S07 | Server: reversing a storage-fee payment | If a storage payment is reversed after the project has left Receivables, the books end up wrong (a fee that was dropped can come back as title money owed). | medium | likely | code |
| S08 | Server: Dashboard vs Payments page | The two pages split "title money" and "storage money" by different rules, so "title collected" will not match between them. | medium | sure | code |
| S09 | Server: the yearly move to Receivables | The automatic job skips every project that has no Title Details (Fresh Survey, Special Projects...). They never go to Receivables by themselves. | medium | sure about code; maybe meant | code |
| S10 | Server: Recovery "answered call" | No guard against a double tap. Two taps count as two good calls and the client is rested for 30 days. | medium | sure | code |
| S11 | Server: Expenses | A Manager is meant to see the last 24 hours. The server lets a Manager ask for any number of hours, so the whole history can be read. | medium | sure | code |
| S12 | Server: audit | Changing a client's phone, email or address through a project edit writes **no audit line**. The same change on the client page does. | medium | sure | code |
| S13 | Server: audit | A stage price change is audited **without the numbers** (no old price, no new price). A price below zero is accepted. | medium | sure | code |
| S14 | Server: New Project | The server accepts an office project with total cost 0. Only the page stops it. Such a project is not Pending and not in Recovery. | medium | sure | code |
| S15 | Server: checks on typed text | A name made of spaces is saved. Text that is too long fails with a wrong message ("Active data links found"). The National ID has no shape check. | medium | sure | code |
| S16 | Server: plot numbers | "12", "12 " and "012" count as different plots. A deleted project keeps its plot number, so typing it again fails with no hint to look in the Archive. | medium | likely | code |
| S17 | Server: double sends | No guard against the same New Project being sent twice. The payment guard is optional. | medium | sure | code |
| S18 | Server: deletes that cannot be undone | Documents, folder notes, expenses, project stages and recovery notes are deleted **for good**. They are audited, but nobody can bring them back. (Projects are safe: they go to the Archive.) | medium | sure | code |
| P04 | My Entries (Employee) | An Employee **cannot correct their own entry**. The server allows it but there is no edit screen. A typo means REJECT and type everything again. | medium | sure | my-entries-employee-phone.jpg |
| P05 | All pages, error messages | Staff see technical text: "Rank not authorized for this command", "Core error (NullPointerException). Look at Render Logs", "OVERPAYMENT_BLOCKED: ... (HTTP 400)", "SYSTEM_CRITICAL_FAULT". | medium | sure | code |
| P06 | Recovery, Expenses, New Project, Payments | When loading fails, the page looks **empty** instead of broken: "QUEUE CLEAR", "NO EXPENSES LOGGED", "Loading the stage list..." for ever. Staff will think there is no work. | medium | sure | recovery-secretary-phone.jpg |
| P07 | Dashboard tiles | A tile opens a list that shows a different number. "Ready for hand-over" opens the PAID tab (which also has handed-over and problem projects). "Title money still owed" opens CRITICAL only. | medium | sure | dashboard-admin-desktop.jpg |
| P08 | Settings > Staff, TEMPORARY KEY popup | The key is "shown once only", but one tap outside the popup closes it and the key is gone. **FIXED in fix190.** | medium | sure | settings-phone.jpg |
| P09 | Folder page and Client page, Secretary | The Secretary makes the recovery calls but cannot fix a wrong phone number on the client page, and cannot tick a stage. David's rule says the Secretary handles the Invoice/Contract stage. (The server also blocks the tick -- see S19.) | medium | sure | folder-phone.jpg |
| P10 | Settings > Staff | The power icon **suspends a person with one tap**, no question asked. CREATE can be pressed twice while the server wakes up. The three icon buttons have no words. | medium | sure | settings-phone.jpg |
| P11 | Folder page | A Fresh Survey or Special Project can **never be closed**. HAND OVER needs Title Details and these types never have them. A paid, finished project stays ACTIVE for ever. | medium | sure; maybe meant | folder-phone.jpg |
| P12 | Folder page, grey buttons on a phone | The reason a button is grey (RECORD PAYMENT, HAND OVER, EDIT) shows only when a mouse hovers. On a phone it is just grey with no reason. | medium on phones | sure | folder-phone.jpg |
| P13 | New Project, errors | Each error shows for 4 seconds, one at a time, with no red mark on the box and no jump to it. Easy to miss on a phone. | medium on phones | sure | new-project-money-phone.jpg |
| P14 | Project status words | Reports and the Folder print-out still use the old words (RECEIVABLE / RELEASED / COMPLETED). The Folder header can show two badges at once. Related Projects and the Client page cannot show PENDING. | medium | sure | reports-phone.jpg |
| P15 | Ledger, search on ALL PROJECTS | A search never finds a Pending project and gives no hint to look in the PENDING tab. | medium | sure | code |

### 1.3 Low

| ID | Where | What is wrong | How bad | Sure? | Screenshot |
|---|---|---|---|---|---|
| S19 | Server: two rank rules disagree with themselves | The "tick a stage" door says Secretary may enter, the room behind it says Manager and above. The room wins, so the Secretary gets "not allowed". Same kind of clash on one unused endpoint. | low | sure | code |
| S20 | Server: notes | Anyone who can add a note can type one that starts with `[HANDED OVER]` or `[PROBLEM]`. The system then treats it as its own note and it can never be edited or deleted. | low | sure | code |
| S21 | Server: storage fees | Fees can be changed on a deleted project. | low | sure | code |
| S22 | Server: old endpoints no page uses | Three old endpoints are still open (follow-up note, bulk stage delete, reality override). They have weaker rules. | low | sure | code |
| S23 | Server: project index numbers | A refused save still uses up an index number, so numbers get skipped. | low | sure | code |
| S24 | Server: Dashboard | The period "transactions" count includes payments of deleted projects; "revenue" does not. The Dashboard is kept for 60 seconds and is not refreshed after a payment. "New projects (7 days)" also counts Pending entries. | low | sure | code |
| S25 | Server: bad input | Some bad inputs give "Core error" with a Java word and "Look at Render Logs" instead of a clear sentence. | low | sure | code |
| S26 | Server: who sees money | The client page hides money from Manager and Secretary, but the Ledger list sends cost, paid and owed for every project to them. | low | sure about code; maybe meant | code |
| S27 | Server: settings for a real go-live | Local test addresses are still allowed (CORS). Demo data is ON by default. The app carries on if start-up seeding fails. The container runs as root. | low | sure | code |
| S28 | Server: smaller audit gaps | No audit line for: neighbours replaced on edit, old and new place names, reorder of the master stage list. | low | sure | code |
| S29 | Server: stage list | The rule "no stage above Invoice/Contract" is only in the page. The server does not refuse it. | low | sure | code |
| S30 | Server: words | Audit details, alerts and some error text written by the server still say "status" for a checklist step. | low | sure | audit-phone.jpg |
| S31 | Render / GitHub | GitHub shows a **failed deploy** for the old service `ge-solutions-api` (the one that was retired). The real backend service is not visible from here. | low | sure it shows; cause unknown | code |
| P16 | Popups | The design rule is ONE way to close plus the action buttons. These have both an X and a CANCEL-type button: Expenses (LOG EXPENSE, NEW PRESET, EDIT EXPENSE, delete), Settings (CHANGE RANK, RESET KEY, RESTORE PROJECT), SIGN OUT, FORGOT YOUR KEY. | low | sure | expenses-phone.jpg |
| P17 | Popups with typed text | Recovery CALL LOG, the Expenses popups and ADD STAFF close on a tap outside and the typed text is lost. **FIXED in fix190.** | low | sure | expenses-phone.jpg |
| P18 | New Project, Employee | The Employee sees "+ NEW CATEGORY" for documents but the server refuses it. **FIXED in fix190 (the button is hidden for the Employee).** | low | sure | code |
| P19 | Dashboard "Recent activity" | The links go to the Audit page but do not open the line that was clicked. | low | sure | dashboard-admin-desktop.jpg |
| P20 | Client page edit | No "saved" message, no phone check, no warning on leaving with unsaved changes. The button says EDIT PORTFOLIO but edits name and phone. | low | sure | code |
| P21 | Date picker | Old dates are slow: the year moves one tap at a time and cannot be typed. A 1998 title date needs about 28 taps. | low | sure | new-project-money-phone.jpg |
| P22 | Reports | Only the first 8 rows show on screen. The rest need a download. Hard on a phone. | low | sure | reports-phone.jpg |
| P23 | Dates | Five date styles are in use (05 Oct 2026, 05/10/2026, 2026-10-05, the device style on Expenses, and one more in Settings). "Today" on New Project and Folder is worked out in London time, so it is yesterday between midnight and 3 am. **"Today" FIXED in fix190; the five date styles are still to do.** | low | sure | expenses-phone.jpg |
| P24 | Money | Money boxes on New Project have no commas while typing (1500000 is easy to get wrong). Expenses accept decimals; everything else is whole shillings. The Dashboard shortens (271.7M). | low | sure | new-project-money-phone.jpg |
| P25 | Same thing, different names | Money owed is called DEBT, AMOUNT OWED, BALANCE OWED, TOTAL OWED. "Key" in most places but "PASSWORD" on the sign-in page. GOLDEN SEED on screen, GE SOLUTIONS on the print-out. "The root user can restore it" is wrong (a Director can too). | low | sure | code |
| P26 | Hard words | "COMMITTING DATA...", "LEDGER SYNC FAULT", "Recovery Cockpit", "QUEUE CLEAR", "OPERATOR ID", "PROTOCOL CLASS", "NO SIGNALS", "SCOPE", "tenure split", and the Folder phone tabs "OV / FIN / PPL / DOC / NTS". | low | sure | folder-phone.jpg |
| P27 | Small text | Some table headings are 7px and some tabs 8px on a phone. Hard to read. | low | sure | audit-phone.jpg |
| P28 | New Project vs Folder edit | New Project needs county, sub-county, parish, village, area, phone. Folder edit needs only the district and lets the rest be emptied. | low | sure | code |
| P29 | Pending view, REJECT | One tap rejects once 5 letters are typed. No "are you sure". | low | sure | pending-view-phone.jpg |
| P30 | Recovery | Opening a folder from Recovery reloads the whole app. Slow on a phone. | low | sure | code |
| P31 | Sign-in page | The "forgot key" text tells the Admin to use "owner recovery", which has no screen. | low | sure | code |
| P32 | Stage lists and expense presets | There is no screen to change the **master** stage list of a project type; it can only be changed one project at a time. Expense presets cannot be renamed or removed. | low | sure | code |
| P33 | Data entry helpers | An Employee gets no suggestions (the lists come from pages an Employee may not open). | low | sure | code |
| P34 | Leftovers | Unused files and calls, one browser "confirm" box left in the header, a second "leave page?" question after SIGN OUT, the Folder asks "unsaved changes?" when nothing changed. | low | sure | code |
| P35 | Labels for screen readers | Many boxes on New Project and popups are not tied to their label. Staff "active / suspended" is a colour dot only. | low | sure | code |

### 1.4 Checked and found fine

- Each rank can only open its own pages. The Employee is kept to New Project, My Entries, their own Pending view
  and Settings. No redirect loop. The side menu shows only pages the rank can open.
- The Dashboard sends money only to Director and Admin.
- An Employee cannot open another person's entry. Answers to an Employee never carry money.
- Payments: no zero or negative amount, whole shillings, overpayment blocked, blocked on deleted projects, receipt
  needed, guarded against a double tap on the Folder page.
- Reversing a payment: Director only, needs a reason, cannot be done twice.
- Deleting a project is a soft delete (Archive) with a reason. The data wipe needs the Admin, a phrase and the password.
- Staff changes (create, rank, suspend, key reset) are all audited. The audit list cannot be edited or deleted.
- No pages overflow sideways on a phone at 90 / 100 / 110 / 125 size. Every table scrolls sideways inside its box.
- No real password or key is written in this document or the guide.

---

## 2. WORKFLOW FAULTS

These are faults in **how the work flows**, not single bugs.

**W1. The field entry road (Employee -> office) is half built.**
The Employee types an entry and uploads papers. Then: the Employee cannot fix a typo (P04), the office cannot see
the papers before deciding (P03), REJECT has no "are you sure" (P29), and the invoice number and contract number
that David wants cannot be stored yet (see section 4, B1). This is the road David cares about most.

**W2. The Secretary's job and the Secretary's rights do not match.**
David's rule: the Secretary enters the invoice and contract numbers by clicking the Invoice/Contract stage.
Today the Secretary cannot tick any stage (P09, S19), cannot fix a client phone on the client page (P09), and the
National ID lookup on New Project quietly says "not found" for a Secretary because the server keeps it for
Manager and above.

**W3. Some projects have no end.**
Fresh Survey and Special Projects cannot be handed over (P11) and never go to Receivables by themselves (S09).
They stay ACTIVE for ever, so the lists grow and the Dashboard counts drift.

**W4. The same number can differ between two pages.**
Dashboard vs Payments (S08), Dashboard tiles vs the list they open (P07), report periods one day early (P01),
the stage chart that never moves (S06). When two screens disagree, staff stop trusting both.

**W5. A mistake cannot always be undone.**
Documents, notes, expenses, stages and call notes are deleted for good (S18). Staff suspend is one tap (P10).
The one-time key can vanish with one tap (P08).

**W6. When something fails, the app often looks fine.**
Empty lists on a failed load (P06), technical error words (P05), uploads thrown away if storage is not set (S05).

**W7. Uploaded papers are not private.**
Files are public links (S02) and the new-project upload takes any file type (S03). For land titles and ID copies
this matters before real client data goes in.

---

## 3. CORRECTIONS MADE

| Fix | What was corrected |
|---|---|
| fix183 | Phone and layout: the smudge under text boxes, the strip under the page, tables that would not slide sideways, cut-off tab bars, SIGN OUT pushed off screen at 125%, Payments table copied from the Ledger phone view. |
| fix184 | Words: STAGE = a step in the checklist. STATUS = where the whole project stands (Pending / Active / Receivables / Handed over / Deleted). Hover explainers. A project with no price no longer says FULLY PAID. |
| fix185 | The "WAITING FOR ..." line in every project folder, Pending view and My Entries. No "+" above Invoice/Contract. Ticking a stage offers a document upload (not the first stage). |
| fix186 | Photos are made smaller before upload with no visible loss (example: 11.5 MB -> 1.3 MB). PDFs and small files are left alone. |
| fix187 | Hosting cost plan with prices and sources (guide section 18.3a). The Hetzner move itself is still PENDING. Nothing was set up. |
| fix188 | Data entry helpers: the village fills the rest of the place, known clients are offered by name / National ID / phone, "Did you mean ...?" for likely typos, expense categories remembered. |
| fix189 | This review document. |
| fix190 | From this review: P01 report periods, P02 double save, P08 temporary key popup, P17 popups with typed text, P18 "+ NEW CATEGORY" for the Employee, P23 "today" in London time. |

---

## 4. CORRECTIONS STILL TO DO

Ranked: most important first. Size: **small** = under an hour, **medium** = a few hours, **big** = a day or more.

### A. Waiting for an answer from David (see section 5)

| Rank | Item | Size | Needs |
|---|---|---|---|
| 1 | Turn on checks for server changes (Q1). Nothing in group B can be merged safely before this. | small | Q1 |
| 2 | S02 private file links | big | Q2 |
| 3 | P09 / S19 / W2 Secretary rights | small | Q3 |
| 4 | P11 / S09 how Fresh Survey and Special Projects end | medium | Q4 |
| 5 | S18 deletes that can be undone | medium | Q5 |
| 6 | S26 who sees money in the Ledger | medium | Q6 |
| 7 | P04 Employee edits own entry | medium | Q7 |
| 8 | Hosting move (Hetzner or other) | big | Q8 |

### B. Server work, blocked only by Q1 (I am sure what to do)

| Rank | Item | Size |
|---|---|---|
| 1 | S01 Employee must not read or change an existing client's contacts | medium |
| 2 | S03 file-type check on new-project uploads | small |
| 3 | S04 + S05 refuse to start with fallback secrets or without storage settings (when not in demo mode) | small |
| 4 | Invoice number + contract number: stored, unique, needed together with the prices to leave Pending, correctable by every rank but Employee, audited (David's Task C) | big |
| 5 | Deep rename Stage / Status in server code, tables and endpoints, with a safe migration (David's Task B) | big |
| 6 | S29 server refuses a stage above Invoice/Contract | small |
| 7 | P03 send documents, notes and stages with a Pending entry and show them | medium |
| 8 | S06 make the stage chart move | medium |
| 9 | S08 + S24 one rule for title money vs storage money on Dashboard and Payments | medium |
| 10 | S07 reversing a storage payment after Receivables | medium |
| 11 | S10 + S17 guards against double sends (calls, new project, payments) | medium |
| 12 | S12 + S13 + S28 missing audit lines and numbers | small |
| 13 | S14 + S15 + S16 server checks: cost above 0, blank names, text length, plot number cleaning | medium |
| 14 | S11 Manager limited to 24 hours of expenses | small |
| 15 | S20 + S21 + S22 + S23 + S25 small server tidy-ups | small each |
| 16 | S27 go-live settings (CORS, demo flag) -- do at go-live | small |
| 17 | P33 place-name suggestions for the Employee (needs a small new endpoint with place names only) | small |

### C. Page work I can do without the server (next small PRs)

| Rank | Item | Size |
|---|---|---|
| 1 | P05 + P06 clear error sentences and a real "could not load -- TRY AGAIN" state | medium |
| 2 | P10 ask before suspending; busy state on CREATE and RESTORE; words on the icon buttons | small |
| 3 | P29 "are you sure" on REJECT | small |
| 4 | P13 errors stay on the box and the page jumps to it | medium |
| 5 | P12 show the reason for a grey button on a tap | medium |
| 6 | P14 + P15 one set of status words everywhere; Ledger search hints at the PENDING tab | medium |
| 7 | P07 + P19 Dashboard tiles and links open exactly what they count | medium |
| 8 | P16 one way to close each popup | small |
| 9 | P23 + P24 one date style and one money style; commas while typing money ("today" is already fixed) | medium |
| 10 | P21 type the year in the date picker | small |
| 11 | P20, P22, P25, P26, P27, P28, P30, P31, P34, P35 tidy-ups | small each |
| 12 | P32 a screen for the master stage lists | medium |

---

## 5. QUESTIONS FOR DAVID

I will not guess these. Each one changes what gets built. Answer with the letter, for example "Q1 A, Q2 B".

### Q1. How should server changes be checked before they go live?

**Why it matters:** your rule is "never merge if a check fails". This workspace cannot run the 91 server tests
(the download site for the Java tools is blocked). So no server change has been merged, and group B is waiting.

- **A.** Add "GitHub checks": GitHub runs the server tests and the page tests by itself on every change. Free for this repo size.
- **B.** You allow the address `repo.maven.apache.org` in this workspace's network settings. Then I run the tests here.
- **C.** Both A and B.

**MY SUGGESTED OPTION: A.** It costs nothing, it needs no settings from you, and it keeps protecting the app
whoever makes the change (me, another helper, or you). B only helps while this workspace is open.

### Q2. Uploaded files are public links today (S02). How private should they be?

**Why it matters:** title scans and ID copies of real clients will be in there. Anyone with a link can open it.

- **A.** Leave as it is until go-live (only demo files now), fix before real data.
- **B.** Fix now: files open only for a signed-in person, through the server. Slower to build (big), slightly slower to open a file.
- **C.** Fix when moving hosts: keep files on the new server's own disk instead of Cloudinary, private from day one.

**MY SUGGESTED OPTION: C.** You plan to move hosts anyway, and the cost plan already counts 100 GB of disk.
Doing it once, during the move, is cheaper and simpler than building it twice. But it must be done **before**
real client papers go in. If the move will take long, choose B.

### Q3. What may the Secretary do?

**Why it matters:** you said the Secretary enters the invoice and contract numbers by clicking that stage. Today
the Secretary cannot tick any stage and cannot fix a client's phone number.

- **A.** Secretary may tick **only** the Invoice/Contract stage, and may fix client phone numbers.
- **B.** Secretary may tick **any** stage, and may fix client phone numbers.
- **C.** Leave as it is (Manager and above tick stages).

**MY SUGGESTED OPTION: A.** It matches what you described, and it keeps the rest of the checklist with the
people who do the field and land-office work. The Secretary makes the calls, so fixing a phone number belongs
there. Every change stays audited.

### Q4. How does a Fresh Survey or Special Project end?

**Why it matters:** today these can never be closed (P11) and never go to Receivables by themselves (S09).

- **A.** Add a **CLOSE PROJECT** button (Director and above) for project types with no title. Status becomes "CLOSED". It needs all stages ticked and nothing owed.
- **B.** Let HAND OVER work without Title Details for these types (status "HANDED OVER").
- **C.** Leave them ACTIVE for ever.

Also: should they move to Receivables after 365 days unpaid like the others? (yes / no)

**MY SUGGESTED OPTION: A, and yes.** Nothing is "handed over" in a Fresh Survey, so a plain CLOSE is the
honest word. And a client who has not paid for a year should be chased the same way whatever the project type.

### Q5. Should deleted documents, notes and expenses be recoverable?

**Why it matters:** today they are gone for good (S18). One wrong tap by staff loses a paper.

- **A.** Yes: they go to the Archive for 90 days, a Director can restore them, then they are removed.
- **B.** Yes, kept for ever in the Archive.
- **C.** No, leave as it is (the audit line is enough).

**MY SUGGESTED OPTION: A.** Safe for non-technical staff, and 90 days keeps the disk (and the cost) from
growing for ever.

### Q6. May a Manager and a Secretary see money in the Ledger?

**Why it matters:** the client page hides money from them, but the Ledger shows cost, paid and owed for every
project (S26). One of the two is wrong.

- **A.** They see money **per project** (they need it to collect payments), but no company totals. Then the client page should show it too.
- **B.** They see no money anywhere; only Director and Admin do.
- **C.** Manager sees money, Secretary does not.

**MY SUGGESTED OPTION: A.** The Secretary makes the recovery calls and must know what each client owes.
Company totals stay with the Director and Admin, as on the Dashboard today.

### Q7. May an Employee correct their own entry while it is still Pending?

**Why it matters:** today a typo means the office rejects it and the Employee types everything again (P04).

- **A.** Yes, until the office starts it. Every change is audited.
- **B.** No, but the office can correct it for them before starting it.
- **C.** Leave as it is.

**MY SUGGESTED OPTION: A.** Less double work, and the office still checks every name and number before
starting the project.

### Q8. Hosting: Hetzner may not be selling its cheapest servers right now.

**Why it matters:** the cost plan (guide 18.3a) found reports that Hetzner's cheap CX / CAX servers could not be
ordered since September 2026. I could not confirm it from here. Nothing has been set up; the move is PENDING.

- **A.** You open hetzner.com/cloud, try to order a CX23, and tell me what it says. Then we decide.
- **B.** Go straight to the second choice (Netcup VPS 500, about EUR 7 a month).
- **C.** Stay on Render for now and move later.

**MY SUGGESTED OPTION: A.** It takes you two minutes and it is the only sure way to know. No payment is
needed just to look.

### Q9. The invoice / contract stage: may it ever be removed from a project?

**Why it matters:** you said no stage may sit above it. If a Director can still **remove** it, a project could
have no place to hold the two numbers.

- **A.** It can never be removed or renamed, on any project.
- **B.** A Director may remove it, with a reason.

**MY SUGGESTED OPTION: A.** Every project needs the two numbers to leave Pending, so the stage must always be
there. Simple rule, nothing to explain to staff.

### Q10. A failed deploy shows on GitHub for the old service `ge-solutions-api` (S31).

**Why it matters:** if that old service still exists on Render it may be costing money or holding an old copy
of the app.

- **A.** You look on the Render dashboard: if `ge-solutions-api` is still there, delete it (after checking the live site uses `ge-solutions`).
- **B.** Leave it.

**MY SUGGESTED OPTION: A.** Low running cost is one of your goals, and an old copy of the app is one more
thing that can be attacked.

---

## 6. HOW THIS DOCUMENT IS KEPT UP TO DATE

- When an item is fixed, it moves from section 4 to section 3 with its fix number.
- When David answers a question, the answer is written under the question and the work moves to section 4 group B or C.
- New faults get the next free ID. IDs are never reused.
