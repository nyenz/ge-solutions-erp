# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# This file receives all small incremental updates each session.
# Last updated: May 2026

---

## SESSION MANAGEMENT RULES (HOW EVERY SESSION ENDS)

At the end of every session the AI must do the following in order:

1. Read the addendum to identify everything worked on this session
2. Ask David: "Are you happy with X, Y, Z? Should I mark them as done?"
3. Wait for David to confirm -- do not assume anything is done without confirmation
4. Once confirmed:
   - Move confirmed items INTO Section 10 (COMPLETED) of master guide
   - Remove confirmed items FROM Section 11 (TO DO) of master guide
   - If something new came up during the session, add it to Section 11
5. Both sections must reflect 3 sources of truth:
   - What the addendum says was worked on
   - What David explicitly confirmed he is happy with
   - What the code actually shows

RULE: Once something is marked done and moved to Section 10, it is NEVER put back in Section 11.
RULE: Section 11 only contains things not yet done. Completed work lives in Section 10 only.
RULE: The addendum is the running log. The master guide Sections 10 and 11 are the clean summary.

---

## NEW UI RULES ADDED (May 2026)

### UI UNIFORMITY RULE (DEFAULT DESIGN APPROACH)
Every element of the same type must look and behave identically across all pages and sections regardless of where it appears. Only deviate when explicitly instructed.

### RESPONSIVENESS RULE (DEFAULT DESIGN APPROACH)
Every element, property, and value must respond to screen size changes by default.

### "SAME DESIGN" PHRASE RULE
When the instruction says "same design", the element must be identical in every measurable way.

### NO BROWSER DEFAULT STYLING RULE (DEFAULT DESIGN APPROACH)
Every element must be explicitly styled -- no browser defaults are ever acceptable anywhere in the app.

---

## SESSION: May 2026 -- FIXES APPLIED THIS SESSION

### 1. Print Preview (FolderPage)
- Completely rewrote @media print CSS in FolderPage.module.css
- Pipeline HUD: compact horizontal row with visible stage dots
- Terminal header: white background, navy border-left
- All panels: white background, grey borders, all drawers forced open
- Read-only grid: 3 columns on print
- Owners: 2 columns on print
- Financials: all visible, no glow effects
- Notes + docs: scroll disabled, full height shown
- @page: A4 portrait, 15mm margins
- Status: DONE PREVIOUS SESSION

### 2. PDF viewing in FolderPage (from Cloudinary)
- Added isPDF() helper function to detect PDF files by path/URL
- PDF files now show with open-in-new-tab link + 📄 emoji prefix
- Cloudinary raw PDFs served directly via their secure_url
- Status: DONE PREVIOUS SESSION

### 3. Document preview on New Plot page (IntakePage)
- Fixed file queue to allow opening uploaded files before submission
- Files show emoji prefix (📄 for PDF, 🖼 for image) as visual hint
- Status: DONE PREVIOUS SESSION

### 4. Audit Page filter dropdowns (ALL STAFF / ALL ACTIONS)
- Resized hwSelectWrap to flex: 1 1 140px, max-width: 260px
- Status: DONE PREVIOUS SESSION

### 5. Single-session enforcement -- BROWSER TABS ONLY (previous)
- localStorage-based approach for same-browser tab detection
- Status: DONE PREVIOUS SESSION

### 6. Server-side single-session enforcement (previous)
- Added sessionVersion (Integer) column to users table in User.java
- On every login: sessionVersion incremented in DB, embedded in JWT as "sv" claim
- JwtAuthenticationFilter: on every request, extracts "sv" from JWT and compares
  to the current DB value. If mismatch (old token), request is rejected with 401.
- This means: logging in from computer B immediately invalidates computer A's token.
- The axios interceptor on the frontend already handles 401 by redirecting to /login.
- Status: DONE

### 7. Transparent Filter Headers, Unified Scrolling & Mobile Dropdown Clipping (THIS SESSION)
- Removed background color and backdrop blur from sticky headers on Ledger, Payments, Audit, Recovery, and Digital Folder pages.
- Consolidated vertical scrolling by removing fixed heights and list scrollbars on Ledger, Payments, and Audit pages, allowing the pages to scroll uniformly under the sticky headers.
- Restored layout scrolling on Recovery and Ledger pages by removing restricted heights (`height: 100%`, `min-height: 0`, and `overflow: hidden`) on their respective containers.
- Fixed stacking context clipping of select dropdowns on the Audit page by removing the static `z-index: 9000` rule from `.hwSelectWrap`.
- Status: DONE THIS SESSION