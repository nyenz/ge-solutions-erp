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
- Status: DONE THIS SESSION

### 2. PDF viewing in FolderPage (from Cloudinary)
- Added isPDF() helper function to detect PDF files by path/URL
- PDF files now show with 'open in new tab' behavior
- Images continue to work as before (direct link)
- Cloudinary raw PDFs are served directly via their secure_url
- Status: DONE THIS SESSION

### 3. Document preview on New Plot page (IntakePage)
- Fixed file queue to allow opening uploaded files before submission
- Images: open via object URL in new tab
- PDFs: create object URL on click, open in new tab, revoke after 5s
- Files now show emoji prefix (📄 for PDF, 🖼 for image) as visual hint
- Status: DONE THIS SESSION

### 4. Audit Page filter dropdowns (ALL STAFF / ALL ACTIONS)
- Resized hwSelectWrap to flex: 1 1 140px, max-width: 260px
- Now properly sized to match Payments page "ALL TYPES" buttons
- Status: DONE THIS SESSION

### 5. Single-session enforcement (security)
- When user logs in: generates a unique session ID stored in localStorage (gs_active_session)
- Each tab tracks its own session in sessionStorage (gs_tab_session)
- If another tab/browser logs in: storage event fires, old tab detects conflict and logs out
- Redirects to /login?reason=session_conflict
- Login page reads this param and shows security warning message
- NOTE: This works across tabs in the SAME browser. Different browsers on different computers
  cannot share localStorage -- this is a browser security feature. True cross-device single
  session enforcement requires server-side token invalidation (future enhancement).
- Status: DONE THIS SESSION

### 6. Unsaved changes warning (FolderPage)
- Already existed via beforeunload event handler
- Also has confirm dialog on ABORT button
- No changes needed -- working correctly

---

## KNOWN ISSUES / NOTES

- Cloudinary raw PDFs: The HTTP 401 error seen in screenshots is because Cloudinary
  raw files uploaded with access_mode=public should be accessible, but some accounts
  have delivery restrictions. If PDFs still show 401, check Cloudinary dashboard >
  Security > Restricted media types. The fix is on the Cloudinary side, not the app code.

- Single-session enforcement limitation: Works across tabs in same browser (via localStorage
  storage events). Does NOT work across different physical computers/browsers because
  localStorage is browser-local. Server-side JWT invalidation would be needed for that.
