# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# This file receives all small incremental updates each session.
# The master LLM_CONTEXT_GUIDE.md is NEVER edited for incremental changes.
# Only Section 10 (COMPLETED) and Section 11 (TO DO) of the master guide are
# ever updated -- and only after explicit David approval at end of session.
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
Every element of the same type must look and behave identically across all pages and sections regardless of where it appears. Only deviate when explicitly instructed. This covers all element types including: buttons (primary, secondary, filter, action), headings (page titles, section titles, table headers), inputs (text fields, search boxes, number inputs), dropdowns/selects, tables (headers, rows, cells), lists, badges/tags/pills, modals/popups, pagination controls, empty states, icons, tooltips/hints, error messages, success/warning/info messages, loading states/spinners, corner decorations, dividers/separators, scrollbars, and any decorative or structural UI element. For every element the following must be identical everywhere: font (family, size, weight, letter-spacing, text-transform), color (text, background, border), padding, margin, spacing/gap, border (width, style, color, radius), shadow, hover/active/selected/focus/error states, and responsive behavior. When a new element is introduced its style must be derived from the closest existing matching element -- never invent a new style when one already exists.

### RESPONSIVENESS RULE (DEFAULT DESIGN APPROACH)
Every element, property, and value must respond to screen size changes by default. This applies to everything without exception: buttons, headings, text, inputs, dropdowns, tables, lists, badges/tags/pills, modals, icons, images, pagination, empty states, decorative elements, corner decorations, dividers, scrollbars, and all sizing properties (margin, padding, gap, border-width, border-radius, shadow size, font-size, letter-spacing, line-height, container widths, panel heights). All sizing must use clamp() for fonts and spacing, percentage or vw/vh for widths and heights. Hardcoded px is only acceptable for values that must never scale (e.g. a 1px border line). On small screens everything compresses but remains fully readable and usable -- nothing overflows, overlaps, or disappears. On normal/large screens everything returns to its designed size.

### "SAME DESIGN" PHRASE RULE
When the instruction says "same design", the element must be identical in every measurable way: size, padding, margin, spacing/gap, font (family, size, weight, letter-spacing, text-transform), color (text, background, border), border (width, style, color, radius), shadow, responsiveness, hover/active/selected/focus/error states, animation/transition, and alignment/positioning behavior.

### NO BROWSER DEFAULT STYLING RULE (DEFAULT DESIGN APPROACH)
Every element must be explicitly styled -- no browser defaults are ever acceptable anywhere in the app. This includes without exception: buttons, inputs, dropdowns/selects, checkboxes, radio buttons, file inputs, range sliders, scrollbars, arrows (dropdown, scroll, navigation), dots (pagination, bullets, list markers), links, tables, focus outlines, placeholder text, selection highlight, fieldsets/legends, number input spinners, date/time pickers, search cancel buttons, tooltips, and any other element the browser would otherwise style on its own. Every new element introduced must conform to the existing app theme -- matching established colors, fonts, spacing, borders, and interaction states. A new element must never look foreign next to existing ones. When in doubt derive the style from the closest matching existing element in the app.