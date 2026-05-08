# GE SOLUTIONS ERP -- CONTEXT ADDENDUM V3
# Last updated: May 2026 - Final UI Polish Details

## NEW RULES ESTABLISHED THIS SESSION

### 1. SEARCH INPUTS
- Browser native `::-webkit-search-cancel-button` is permanently disabled.
- The custom `.searchClear` icon is forced to `--orange`.
- Text-indent is dynamically applied to avoid search text overlapping the left icon.

### 2. DROPDOWNS & FILTER BUTTONS
- MUST be perfectly rectangular with `border-radius: var(--radius-sm)` (6px-8px). NO PILLS.
- Dropdowns must use `flex: 1 1 120px` to stretch and compress seamlessly on mobile.
- Dropdowns must have `::-webkit-scrollbar { display: none; }`.

### 3. EMPTY STATES
- Searching in tables MUST return dynamic text: `NO RECORDS MATCH 'term'`.
- Use Ledger logic as the absolute source of truth.

### 4. MOBILE TABLES
- Table wrappers (`.tableScroll`) must NOT use negative margins on mobile.
- They must respect the standard `border-radius` to prevent bleeding off the screen edges.